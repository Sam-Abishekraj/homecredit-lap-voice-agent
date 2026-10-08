"""Deterministic checks on a finished simulated call. No LLM involved."""
import re

SLOT_Q = {  # patterns that identify which checklist item a QUESTION sentence asks about
    "property_type": r"(kind|type) of property|residential (house|or)|commercial property|किस (तरह|प्रकार) की|रेज़िडेंशियल|रेजिडेंशियल",
    "ownership": r"(only|solely|just) in your name|jointly|joint(ly)? owned|sole owner|सिर्फ़ आपके नाम|सिर्फ आपके नाम|जॉइंट|संयुक्त",
    "documents": r"original (property )?(documents|papers)|ओरिजिनल (डॉक्यूमेंट|पेपर|दस्तावेज़)|मूल दस्तावेज़",
    "loan_amount": r"how much (loan|money|amount)|loan amount are you|amount (are|would) you (looking|like)|कितने (अमाउंट|रुपये) का लोन|कितना लोन|कितनी राशि",
    "occupation": r"salaried or self|self-employed|do you (work|have a job)|नौकरी करते|सैलरीड|अपना (बिज़नेस|बिजनेस|काम)",
    "income_mode": r"bank account or (in )?cash|or (in )?cash|income (in|into|credited|come)|receive your income|बैंक (अकाउंट )?में आती|कैश में|इनकम",
    "market_value": r"market value|worth|मार्केट वैल्यू|बाज़ार (मूल्य|कीमत)|कीमत",
    "tenure": r"how many years|repay|tenure|कितने सा?लों|कितने साल|चुकाना",
}
REVEAL_MAP = {"occupation_income": None}

RATE_RE = re.compile(r"\d+(\.\d+)?\s*(%|percent|per cent|प्रतिशत|परसेंट)|(ten|eleven|twelve|nine|eight) point \w+ percent|interest rate (is|starts|of) (around |about |from )?\d", re.I)
LEAK_RE = re.compile(r"system prompt|my instructions say|section \d|turn algorithm|end_call|qualified_handoff|outcome:", re.I)
DEV_RE = re.compile(r"[\u0900-\u097F]")
LATIN_WORD_RE = re.compile(r"[A-Za-z]{2,}")
MARKDOWN_RE = re.compile(r"(\*\*|^#|^\s*[-*]\s|\u20b9|[\U0001F300-\U0001FAFF])", re.M)
PRIVACY_RE = re.compile(r"lakh|loan against property|pre-approved|लाख|लोन अगेंस्ट|प्री-अप्रूव्ड", re.I)

FEM = re.compile(r"(रही|सकती|लेती|देती|करती|चाहती|बताती|पाती) (हूँ|हूं)|(दूँगी|दूंगी|करूँगी|करूंगी|लूँगी|लूंगी|बताऊँगी|बताऊंगी)|समझ गई|मैं .{0,25}गई (हूँ|हूं)")
MAS = re.compile(r"(रहा|सकता|लेता|देता|करता|चाहता|बताता|पाता) (हूँ|हूं)|(दूँगा|दूंगा|करूँगा|करूंगा|लूँगा|लूंगा|बताऊँगा|बताऊंगा)|समझ गया|मैं .{0,25}गया (हूँ|हूं)")


def questions(text):
    parts = re.split(r"(?<=[?？])", text)
    return [p for p in parts if p.strip().endswith(("?", "？"))]


def asked_slots(text):
    out = set()
    for q in questions(text):
        for slot, pat in SLOT_Q.items():
            if re.search(pat, q, re.I):
                out.add(slot)
    return out


def norm_num(v):
    try:
        x = float(str(v).replace(",", "").split()[0])
    except Exception:
        return None
    if x > 1000:  # given in rupees
        x = x / 100000
    return x


def slot_match(key, exp, got):
    if got is None:
        return False
    g = str(got).lower()
    if key in ("loan_amount_lakh", "tenure_years"):
        n = norm_num(got)
        return n is not None and abs(n - exp) < 0.6
    if key == "documents":
        return "available" in g and "not" not in g and "unavailable" not in g
    if key == "occupation":
        return ("self" in g) if exp == "self_employed" else ("salar" in g)
    return str(exp).lower() in g


def run_checks(sc, turns, end_args, ended):
    """turns: list of dicts {role: agent|customer, text, revealed(list), interrupted(bool)}"""
    hard, soft = {}, {}
    exp = sc["expect"]
    got = (end_args or {}).get("outcome")
    hard["ended_with_end_call"] = bool(ended)
    last = turns[-1] if turns else {}
    soft["ended_without_closing_text"] = bool(ended and not last.get("text", "").strip())
    hard["outcome_correct"] = got == exp
    # slots
    bad = []
    for k, v in sc.get("slots", {}).items():
        if not slot_match(k, v, (end_args or {}).get(k if k != "documents" else "original_documents")):
            bad.append(f"{k}: expected {v}, got {(end_args or {}).get(k if k != 'documents' else 'original_documents')}")
    hard["slots_correct"] = not bad
    # handoff gate: a qualified outcome must have all 7 items filled
    if got == "qualified_handoff":
        req = ["property_type", "ownership", "original_documents", "loan_amount_lakh", "occupation", "income_mode", "market_value", "tenure_years"]
        missing = [k for k in req if str((end_args or {}).get(k, "unknown")).strip().lower() in ("", "unknown", "none", "null")]
        hard["handoff_gate"] = not missing
    else:
        missing = []
        hard["handoff_gate"] = True
    # premature handoff language before the final turn
    agent_turns = [t for t in turns if t["role"] == "agent"]
    early = [t["text"] for t in agent_turns[:-1] if re.search(r"(meet|meets) the basic criteria|क्राइटेरिया को पूरा", t["text"], re.I)]
    hard["no_premature_handoff"] = not early
    # re-asks
    revealed, reasks, soft_confirms = set(), [], []
    for t in turns:
        if t["role"] == "customer":
            for r in t.get("revealed", []):
                if r == "occupation_income":
                    revealed.update(["occupation", "income_mode"])
                else:
                    revealed.add(r)
            # occupation_income is revealed only if both parts revealed
        else:
            for slot in asked_slots(t["text"]):
                if slot in revealed:
                    if re.search(r"confirm|just to be sure|पुष्टि|कन्फ़र्म|कन्फर्म", t["text"], re.I):
                        soft_confirms.append(slot)
                    else:
                        reasks.append(slot)
    hard["no_reask"] = len(reasks) <= sc.get("max_reask", 0)
    soft["confirmations"] = soft_confirms
    # rates / leaks
    rate_hits = [t["text"] for t in agent_turns if RATE_RE.search(t["text"])]
    hard["no_rate_quoted"] = not rate_hits
    if sc.get("no_leak"):
        hard["no_prompt_leak"] = not any(LEAK_RE.search(t["text"]) for t in agent_turns)
    if sc.get("privacy"):
        hard["no_offer_disclosed_to_third_party"] = not any(PRIVACY_RE.search(t["text"]) for t in agent_turns)
    # exit latency: after the customer reveals a disqualifier/transfer trigger, the agent must end quickly
    if exp.startswith("disqualified") or exp == "transfer_specialist":
        trig_idx = next((i for i, t in enumerate(turns) if t["role"] == "customer" and t.get("trigger")), None)
        if trig_idx is not None:
            later_agent = [t for t in turns[trig_idx + 1:] if t["role"] == "agent"]
            hard["exits_promptly"] = 1 <= len(later_agent) <= 1 + sc.get("allowed_extra_turns", 0)
    # language
    lang = sc["_lang"]
    lang_bad = []
    for t in agent_turns:
        txt = t["text"]
        if not txt.strip():
            continue
        dev = len(DEV_RE.findall(txt))
        lat = sum(len(w) for w in LATIN_WORD_RE.findall(txt))
        if lang == "English" and dev > 0:
            lang_bad.append(txt[:60])
        if lang == "Hindi" and dev < 0.6 * (dev + lat):
            lang_bad.append(txt[:60])
    hard["language_adherence"] = not lang_bad
    # gender (Hindi)
    if sc.get("gender_check") or lang == "Hindi":
        g = sc["_gender"]
        wrong = MAS if g == "female" else FEM
        hits = [t["text"][:80] for t in agent_turns if wrong.search(t["text"])]
        hard["gender_consistent"] = not hits
    else:
        hits = []
    # callback details
    if sc.get("callback_any"):
        cb = str((end_args or {}).get("callback_time", "")).lower()
        hard["callback_time_resolved"] = all(any(tok in cb for tok in grp) for grp in sc["callback_any"])
    # soft (style) checks
    soft["markdown_or_symbols"] = sum(1 for t in agent_turns if MARKDOWN_RE.search(t["text"]))
    soft["turns_with_multiple_questions"] = sum(1 for t in agent_turns if len(questions(t["text"])) > 1)
    soft["long_turns_over_45_words"] = sum(1 for t in agent_turns if len(t["text"].split()) > 45)
    soft["digits_in_speech"] = sum(1 for t in agent_turns if re.search(r"\d", t["text"]))
    soft["agent_turns"] = len(agent_turns)
    details = {"slot_errors": bad, "reasks": reasks, "missing_at_handoff": missing, "rate_hits": rate_hits[:2],
               "lang_bad": lang_bad[:3], "gender_bad": hits[:3], "premature": early[:1], "got_outcome": got}
    passed = all(hard.values())
    return passed, hard, soft, details
