"""Run the turn-level golden tests against the system prompt.

  python eval/run_turns.py --version v1 --agent-model openai/gpt-oss-120b --agent-key GROQ_API_KEY
"""
import argparse, json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.insert(0, os.path.dirname(__file__))
import groq_client as gc
from turn_tests import TESTS
from run_eval import render_prompt, END_CALL_TOOL, ROOT
from checks import asked_slots, slot_match, questions, RATE_RE, DEV_RE, LATIN_WORD_RE, MARKDOWN_RE, FEM, MAS
from scenarios import COMBOS


def check(tc, text, args_, model=""):
    e = tc["expect"]
    # normalise typographic hyphens/apostrophes (U+2010-2015, U+2019) so "seventy\u2011five" matches "seventy-five"
    text = re.sub("[\u2010-\u2015]", "-", text or "").replace("\u2019", "'")
    lang, gender = COMBOS[tc["combo"]][2], COMBOS[tc["combo"]][1]
    got = (args_ or {}).get("outcome") if args_ is not None else None
    ended = args_ is not None
    asked = asked_slots(text)
    h = {}
    if "end" in e:
        h["outcome"] = got == e["end"]
    if "end_in" in e:
        h["outcome"] = got in e["end_in"]
    if e.get("no_end"):
        h["does_not_end"] = not ended
    # gpt-oss on Groq cannot return text and a tool call in one message (harmony format), so for those
    # models a missing closing line is an API artifact -> reported as a soft flag, not a failure.
    closing_ok = (not ended) or bool(text.strip())
    if not model.startswith("openai/gpt-oss"):
        h["closing_line_spoken"] = closing_ok
    if "ask" in e:
        h["asks_" + e["ask"]] = e["ask"] in asked
    if "not_ask" in e:
        h["no_reask"] = not (asked & set(e["not_ask"]))
    for i, pat in enumerate(e.get("must", [])):
        h[f"must_{i}"] = bool(re.search(pat, text, re.I))
    for i, pat in enumerate(e.get("must_not", [])):
        h[f"must_not_{i}"] = not re.search(pat, text, re.I)
    bad = []
    for k, v in e.get("slots", {}).items():
        kk = "original_documents" if k == "documents" else k
        if k == "market_value":
            ok = v in str((args_ or {}).get(kk, ""))
        else:
            ok = slot_match(k, v, (args_ or {}).get(kk))
        if not ok:
            bad.append(f"{k}: want {v} got {(args_ or {}).get(kk)}")
    if e.get("slots"):
        h["slots"] = not bad
    if e.get("callback_any"):
        cb = str((args_ or {}).get("callback_time", "")).lower()
        h["callback_resolved"] = all(any(tok in cb for tok in g) for g in e["callback_any"])
    h["no_rate_quoted"] = not RATE_RE.search(text)
    dev = len(DEV_RE.findall(text)); lat = sum(len(w) for w in LATIN_WORD_RE.findall(text))
    if text.strip():
        h["language"] = (dev == 0) if lang == "English" else (dev >= 0.6 * (dev + lat))
    if lang == "Hindi":
        h["gender_forms"] = not (MAS if gender == "female" else FEM).search(text)
    soft = {"multi_question": len(questions(text)) > 1, "markdown": bool(MARKDOWN_RE.search(text)),
            "words": len(text.split()), "digits": bool(re.search(r"\d", text)), "ended_without_closing_text": not closing_ok}
    return all(h.values()), h, soft, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    ap.add_argument("--prompt", default=os.path.join(ROOT, "prompt", "system_prompt.md"))
    ap.add_argument("--only", default="")
    ap.add_argument("--agent-model", default="openai/gpt-oss-120b")
    ap.add_argument("--agent-key", default="GROQ_API_KEY")
    ap.add_argument("--reasoning", default="low")
    ap.add_argument("--tag", default="")
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    tpl = open(a.prompt, encoding="utf-8").read()
    ids = [i.strip() for i in a.only.split(",") if i.strip()] or list(TESTS)
    tag = a.tag or a.agent_model.split("/")[-1]
    outdir = os.path.join(ROOT, "eval", "results", a.version)
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, f"turns_{tag}.jsonl")
    done = {}
    if os.path.exists(outpath):  # resume
        for line in open(outpath, encoding="utf-8"):
            r = json.loads(line); done[r["id"]] = r
    todo = [i for i in ids if i not in done]
    lock = __import__("threading").Lock()

    def one(i):
        tc = TESTS[i]
        sc = {"combo": tc["combo"]}
        msgs = [{"role": "system", "content": render_prompt(tpl, sc)}]
        for r, txt in tc["history"]:
            msgs.append({"role": "user" if r == "c" else "assistant", "content": txt})
        m, u = gc.chat(msgs, a.agent_model, key_env=a.agent_key, tools=END_CALL_TOOL, temperature=0.3,
                       max_tokens=700, reasoning_effort=a.reasoning, est_tokens=6200, tpm=8000)
        text = (m.get("content") or "").strip()
        calls = m.get("tool_calls") or []
        args_ = None
        if calls:
            try:
                args_ = json.loads(calls[0]["function"].get("arguments") or "{}")
            except Exception:
                args_ = {"raw": calls[0]["function"].get("arguments")}
        ok, h, soft, bad = check(tc, text, args_, a.agent_model)
        rec = {"id": i, "category": tc["category"], "combo": tc["combo"], "language": COMBOS[tc["combo"]][2],
               "title": tc["title"], "pass": ok, "failed": [k for k, v in h.items() if not v], "checks": h, "soft": soft,
               "slot_errors": bad, "reply": text, "end_call": args_, "last_customer": tc["history"][-1][1],
               "model": a.agent_model, "tokens": u.get("total_tokens")}
        with lock:
            with open(outpath, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for f in as_completed([ex.submit(one, i) for i in todo]):
            try:
                r = f.result()
                print(f"{r['id']} {'PASS' if r['pass'] else 'FAIL'} {r['failed']} | {r['reply'][:110]!r} {('-> ' + str(r['end_call'].get('outcome'))) if r['end_call'] else ''}", flush=True)
            except Exception as e:
                print("ERROR", str(e)[:300], flush=True)
                if "DAILY_LIMIT" in str(e):
                    os._exit(3)
    print(json.dumps(gc.USAGE))


if __name__ == "__main__":
    main()
