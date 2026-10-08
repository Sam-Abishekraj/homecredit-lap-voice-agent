"""Simulated-call evaluation of the LAP voice-agent system prompt on Groq.

Agent under test : the real prompt/system_prompt.md with variables filled in (openai/gpt-oss-120b by default).
Customer         : an LLM role-playing a hidden persona (openai/gpt-oss-20b by default, different API key).
Scoring          : deterministic checks in checks.py (outcome via the end_call tool, slots, re-asks, gate,
                   rates, language, Hindi gender forms, callback resolution, exit latency).

Usage:
  python eval/run_eval.py --version v1                 # all scenarios
  python eval/run_eval.py --version v2 --only E04,H08  # subset
Keys come from env vars (GROQ_API_KEY / FARM_GROQ_API_KEY by default) and are never printed.
"""
import argparse, json, os, re, sys, time, traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(__file__))
import groq_client as gc
from scenarios import SCENARIOS, COMBOS, RAG_DEFAULT
from checks import run_checks, asked_slots

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CTX = dict(current_date="8 October 2026", current_day="Thursday", current_time="11:30 AM IST")

END_CALL_TOOL = [{"type": "function", "function": {
    "name": "end_call",
    "description": "Hang up the phone call. Use only after speaking your closing line in the same turn. Record the call outcome and everything captured.",
    "parameters": {"type": "object", "properties": {
        "outcome": {"type": "string", "enum": ["qualified_handoff", "disqualified_property_type", "disqualified_documents",
                    "disqualified_income_mode", "disqualified_tenure", "disqualified_loan_amount", "transfer_specialist",
                    "callback_scheduled", "wrong_person", "not_interested"]},
        "property_type": {"type": "string", "description": "residential / commercial / industrial / agricultural / unknown"},
        "ownership": {"type": "string", "description": "sole / joint / other / unknown"},
        "original_documents": {"type": "string", "description": "available / not_available / unknown"},
        "loan_amount_lakh": {"type": "number", "description": "final loan amount in lakh (e.g. 75)"},
        "occupation": {"type": "string", "description": "salaried / self_employed / other / unknown"},
        "income_mode": {"type": "string", "description": "bank / cash / unknown"},
        "market_value": {"type": "string", "description": "customer's estimate, e.g. '1.2 crore', or unknown"},
        "tenure_years": {"type": "number"},
        "callback_time": {"type": "string", "description": "resolved day, date and time for a callback, if any"},
        "notes": {"type": "string"}},
        "required": ["outcome"]}}}]

SIM_SYSTEM = """You are role-playing a CUSTOMER who has just picked up a phone call from a loan company. You are NOT an assistant.
Today is Thursday, 8 October 2026, 11:30 AM.

YOUR PERSONA AND HIDDEN SCRIPT:
{persona}

HOW TO SPEAK:
- Talk like a real Indian person on the phone: natural full sentences, sometimes fillers ("umm", "haan", "see", "actually"), never robotic one-word answers.
- {lang_rule}
- Reply to what the caller just said. Reveal facts only when asked, unless your script tells you to volunteer them. Never invent facts beyond your script; if asked something not in your script, answer plausibly and consistently with it.
- Keep each reply short (1-3 sentences) unless your script says to say a long sentence.
- If the caller says goodbye / ends the conversation, reply with a short goodbye.

OUTPUT: return ONLY ONE JSON object for your NEXT reply (never write the caller's lines or future turns): {{"say": "<your spoken words>", "revealed": [..], "trigger": true/false}}
- "revealed": the checklist facts you stated CLEARLY and DEFINITIVELY in THIS reply, from: property_type, ownership, documents, loan_amount, occupation, income_mode, market_value, tenure, existing_loan. Do not list vague or partial answers, and do not list facts you only asked about.
- "trigger": true only if THIS reply clearly states a disqualifying fact (agricultural property, no original documents, cash income, tenure under 3 or over 15 years, refusing the 75 lakh cap) or an existing loan on the property / wish to reduce an EMI. Otherwise false."""


def render_prompt(template, sc):
    agent_name, gender, lang, cust, _ = COMBOS[sc["combo"]]
    vals = dict(company_name="Home Credit", customer_name=cust, agent_name=agent_name, agent_gender=gender,
                language_to_speak=lang, additional_context_from_rag=sc.get("rag", RAG_DEFAULT),
                conversation_history="(provided as the chat messages of this call)",
                customer_utterance="(the latest customer message in the chat)", **CTX)
    out = template
    for k, v in vals.items():
        out = out.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{\w+\}\}", out)
    assert not left, f"unfilled variables: {left}"
    return out


def parse_sim(content):
    try:
        d, _ = json.JSONDecoder().raw_decode(content[content.index("{"):])  # first JSON object only
        return str(d.get("say", "")).strip(), list(d.get("revealed", []) or []), bool(d.get("trigger", False))
    except Exception:
        return content.strip()[:400], [], False


def simulate(sc, prompt_tpl, args):
    agent_name, gender, lang, cust, cust_gender = COMBOS[sc["combo"]]
    sc["_lang"], sc["_gender"] = lang, gender
    system = render_prompt(prompt_tpl, sc)
    if lang == "Hindi":
        lang_rule = ("Speak Hindi written in Devanagari (Hinglish words are fine), unless your persona says otherwise."
                     f" You are {'a woman' if cust_gender == 'female' else 'a man'}; use matching Hindi verb forms.")
    else:
        lang_rule = "Speak Indian English."
    sim_sys = SIM_SYSTEM.format(persona=sc["persona"], lang_rule=lang_rule)
    agent_msgs = [{"role": "system", "content": system}]
    sim_msgs = [{"role": "system", "content": sim_sys}]
    turns, end_args, ended = [], None, False
    if sc.get("opening", "Hello?") == "Hello?":
        # Retell "AI speaks first": the agent opens; a silent placeholder user turn is needed by the chat API
        agent_msgs.append({"role": "user", "content": "(call connected: the customer has picked up and is silent)"})
    else:
        cust_text = sc["opening"]
        turns.append({"role": "customer", "text": cust_text, "revealed": [], "trigger": False})
        agent_msgs.append({"role": "user", "content": cust_text})
        sim_msgs.append({"role": "assistant", "content": json.dumps({"say": cust_text, "revealed": [], "trigger": False})})
    seen_prompt = False
    for step in range(args.max_turns):
        hist_tokens = sum(len(m["content"]) for m in agent_msgs[1:]) // 2.5
        msg, usage = gc.chat(agent_msgs, args.agent_model, key_env=args.agent_key, tools=END_CALL_TOOL,
                             temperature=args.temperature, max_tokens=700, reasoning_effort=args.reasoning,
                             est_tokens=(6000 if step == 0 else 900), tpm=7600)
        text = (msg.get("content") or "").strip()
        calls = msg.get("tool_calls") or []
        turns.append({"role": "agent", "text": text})
        if calls:
            fn = calls[0]["function"]
            try:
                end_args = json.loads(fn.get("arguments") or "{}")
            except Exception:
                end_args = {"raw": fn.get("arguments")}
            ended = fn.get("name") == "end_call"
            turns[-1]["end_call"] = end_args
            break
        agent_msgs.append({"role": "assistant", "content": text})
        # simulate barge-in: customer interrupts while the agent is asking a given item
        interrupted = False
        if sc.get("interrupt_on") and not sc.get("_interrupted") and sc["interrupt_on"] in asked_slots(text):
            words = text.split()
            cut = " ".join(words[: max(3, int(len(words) * 0.55))]) + "—"
            agent_msgs[-1]["content"] = cut
            turns[-1]["text"] = cut
            turns[-1]["interrupted"] = True
            sc["_interrupted"] = interrupted = True
        sim_msgs.append({"role": "user", "content": turns[-1]["text"] + ("  [you cut the caller off mid-sentence]" if interrupted else "")})
        smsg, _ = gc.chat(sim_msgs, args.sim_model, key_env=args.sim_key, temperature=0.7, max_tokens=500,
                          reasoning_effort="low", est_tokens=900, tpm=7600)
        say, revealed, trigger = parse_sim(smsg.get("content") or "")
        if not say:
            say = "Hello?"
        turns.append({"role": "customer", "text": say, "revealed": revealed, "trigger": trigger})
        sim_msgs.append({"role": "assistant", "content": json.dumps({"say": say, "revealed": revealed, "trigger": trigger}, ensure_ascii=False)})
        agent_msgs.append({"role": "user", "content": say})
    return turns, end_args, ended


def to_md(sc, turns, end_args, res):
    passed, hard, soft, det = res
    lines = [f"# {sc['id']} — {sc['title']}", f"combo={sc['combo']} category={sc['category']} expected={sc['expect']} -> got={det['got_outcome']}  **{'PASS' if passed else 'FAIL'}**", ""]
    for t in turns:
        who = "AGENT" if t["role"] == "agent" else "CUSTOMER"
        extra = ""
        if t.get("revealed"):
            extra = f"  _(revealed: {', '.join(t['revealed'])}{'; TRIGGER' if t.get('trigger') else ''})_"
        lines.append(f"**{who}:** {t['text']}{extra}")
        if t.get("end_call") is not None:
            lines.append(f"`end_call {json.dumps(t['end_call'], ensure_ascii=False)}`")
    lines += ["", "## Checks", "```", json.dumps({"hard": hard, "soft": soft, "details": det}, ensure_ascii=False, indent=1), "```"]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    ap.add_argument("--prompt", default=os.path.join(ROOT, "prompt", "system_prompt.md"))
    ap.add_argument("--only", default="")
    ap.add_argument("--agent-model", default="openai/gpt-oss-120b")
    ap.add_argument("--agent-key", default="GROQ_API_KEY")
    ap.add_argument("--sim-model", default="openai/gpt-oss-20b")
    ap.add_argument("--sim-key", default="FARM_GROQ_API_KEY")
    ap.add_argument("--reasoning", default="low")
    ap.add_argument("--temperature", type=float, default=0.3)
    ap.add_argument("--max-turns", type=int, default=22)
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()
    tpl = open(args.prompt, encoding="utf-8").read()
    ids = [i.strip() for i in args.only.split(",") if i.strip()] or list(SCENARIOS)
    outdir = os.path.join(ROOT, "eval", "results", args.version)
    os.makedirs(os.path.join(outdir, "transcripts"), exist_ok=True)
    results = {}
    t0 = time.time()

    def one(i):
        sc = dict(SCENARIOS[i])
        turns, end_args, ended = simulate(sc, tpl, args)
        res = run_checks(sc, turns, end_args, ended)
        open(os.path.join(outdir, "transcripts", f"{i}.md"), "w", encoding="utf-8").write(to_md(sc, turns, end_args, res))
        json.dump({"scenario": {k: v for k, v in sc.items() if not k.startswith('_')}, "turns": turns, "end_call": end_args,
                   "passed": res[0], "hard": res[1], "soft": res[2], "details": res[3]},
                  open(os.path.join(outdir, "transcripts", f"{i}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        return i, sc, res

    # warm the prompt cache: run one scenario per combo first, sequentially
    first = {}
    for i in ids:
        first.setdefault(SCENARIOS[i]["combo"], i)
    order = list(first.values()) + [i for i in ids if i not in first.values()]
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {}
        for n, i in enumerate(order):
            if n < len(first):
                try:
                    i2, sc, res = one(i)
                    results[i2] = (sc, res)
                    print(f"{i2} {'PASS' if res[0] else 'FAIL'} {res[3]['got_outcome']} {[k for k, v in res[1].items() if not v]}", flush=True)
                except Exception as e:
                    print(f"{i} ERROR {e}", flush=True)
                    results[i] = (dict(SCENARIOS[i]), None)
                continue
            futs[ex.submit(one, i)] = i
        for f in as_completed(futs):
            i = futs[f]
            try:
                i2, sc, res = f.result()
                results[i2] = (sc, res)
                print(f"{i2} {'PASS' if res[0] else 'FAIL'} {res[3]['got_outcome']} {[k for k, v in res[1].items() if not v]}", flush=True)
            except Exception as e:
                traceback.print_exc()
                print(f"{i} ERROR {e}", flush=True)
                results[i] = (dict(SCENARIOS[i]), None)

    # summary
    rows = []
    for i in ids:
        sc, res = results.get(i, (SCENARIOS[i], None))
        lang = COMBOS[SCENARIOS[i]["combo"]][2]
        if res is None:
            rows.append(dict(id=i, category=SCENARIOS[i]["category"], language=lang, status="ERROR"))
            continue
        rows.append(dict(id=i, category=SCENARIOS[i]["category"], language=lang, status="PASS" if res[0] else "FAIL",
                         expected=SCENARIOS[i]["expect"], got=res[3]["got_outcome"],
                         failed_checks=[k for k, v in res[1].items() if not v], soft=res[2]))
    done = [r for r in rows if r["status"] != "ERROR"]
    summ = {"version": args.version, "agent_model": args.agent_model, "sim_model": args.sim_model,
            "reasoning": args.reasoning, "n": len(rows), "completed": len(done),
            "passed": sum(r["status"] == "PASS" for r in rows), "elapsed_s": round(time.time() - t0),
            "token_usage": gc.USAGE, "rows": rows}
    json.dump(summ, open(os.path.join(outdir, "summary.json"), "w"), indent=1, ensure_ascii=False)
    print(f"\n{args.version}: {summ['passed']}/{summ['n']} passed ({summ['completed']} completed) in {summ['elapsed_s']}s")
    print(json.dumps(gc.USAGE))


if __name__ == "__main__":
    main()
