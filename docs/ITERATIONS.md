# Iterations: what failed, what changed, what the numbers were

Every number below comes from `eval/results/<version>/turns_*.jsonl`, re-scored by `eval/summarize.py` with the current checker. The runs are **partial**: Groq's free tier allows 200K tokens per day per model, **shared across both keys because they belong to one Groq organisation**, and each test costs about 5–6K tokens because prompt caching isn't active on this account. So each version ran a targeted subset, not the full 66-test suite. Different subsets mean the percentages are **not directly comparable** between versions; the per-test fixes are the useful signal.

## v0 → v1: compression (6.9K → 4.4K tokens)
- v0 (`prompt/versions/v0_draft.md`) followed the guide's long recommended structure, at 6,920 tokens. On Groq, prompt + history + output went over the 8K-tokens-per-request limit (HTTP 413) on longer calls.
- v1 merged overlapping sections and moved scripts into one-line forms, bringing it to 4,424 tokens. That's also better for voice latency on Retell. (Design decision 30.)

## v1: first eval round
| Model (Groq) | Passed | English | Hindi |
|---|---|---|---|
| gpt-oss-120b | 13/15 (87%) | 11/12 | 2/3 |
| qwen3.8-27b | 19/21 (90%) | 16/18 | 3/3 |

Failures (real):
1. **T02, both models:** "Yes, this is Rahul. Who's this?" → the agent re-asked identity instead of treating it as confirmed, and never presented the offer.
2. **T47 (qwen) and H04 (120b, Hindi):** the agent said the cash-income disqualification line but **did not call end_call**, so the call would stay open.
3. gpt-oss-20b as the agent: it called end_call (`wrong_person`) on the very first turn, so it was dropped as an agent model for v1 (`results/v1/dropped_gpt-oss-20b.jsonl.txt`).

## v2: Retell alignment (4,592 tokens)
Changes:
- **AI speaks first:** the prompt now writes the opening line itself (greeting + "Am I speaking with {{customer_name}}?"), matching Sam's Retell setting of a dynamic welcome message.
- **Mandatory `end_call`:** Section 15 lists all 10 terminal outcomes and requires the closing line and the end_call function in the same turn.
- **"Yes, who's this?" counts as verified.**
- Defaults set to Arjun / male. The eval keeps a female persona (Priya) for both English and Hindi.

Result: qwen 9/10. **T02 still failed in a new way:** the agent introduced itself ("This is Priya from Home Credit, calling about a special offer…") but left out the actual offer (75 lakh, "Shall we go ahead?").

## v3: full offer, volunteered disqualifiers, prep-guide point 40 (4,806 tokens)
Changes:
- T02 fix: "in ONE turn give your name and company AND the full offer turn from Section 7".
- Disqualification applies "even if it is volunteered before you asked" (T47/H04 pattern).
- **Section 5 rewritten as the guide's point-40 algorithm:** *Extract first, validate second, update state third, ask the next missing question fourth*, using the guide's own example (1.1 crore, joint, 60 lakh → ask original documents).
- New test **T50** uses the point-40 example word for word (male agent Arjun).
- Checker fix (not a prompt change): a model wrote "seventy‑five" with a Unicode non-breaking hyphen (U+2011), which the regex missed. Typographic hyphens are now normalised before checks. Re-scoring v1/v2 with this fix changed none of their numbers.

| Model | Passed | Notes |
|---|---|---|
| qwen3.8-27b | **4/4** | The 3 earlier failures **T02, T47, H04 now pass**, plus T13 (all 7 details in one breath → handoff). Then the daily cap was hit. |
| gpt-oss-120b | n/a | Daily cap still exhausted from the v1 run |
| gpt-oss-20b (small-model stress test) | 13/19 (68%) | **T50 (point 40) passes**: "Thank you. Do you have the original property documents available for verification?" Also passes T00/T00F (opening for both genders), T02, T47, T04/T05, T08, T09, T11, T16, T20, T22. Fails because it **ends the call too eagerly**: T03 "Who's calling?" → wrong_person; T12 unrelated phone EMI → transfer; T17 "plot" → disqualified without clarifying; T24 90 lakh → disqualified instead of offering the cap; T06 "around six" → 8 PM; T13 handoff line without end_call. |

## v4: guardrails against early exits (4,920 tokens)
These target the v3 small-model failures; a stronger model shouldn't need them, but they cost very few tokens:
- Section 5, VALIDATE step: lists what is **not** an exit: over 75 lakh (ask the cap question), ambiguous "plot/land/papers" (clarify once), a question, or a loan not on the property.
- Section 6: "Who's calling, what is it about?" is not a wrong person; never end the call there.
- Section 7: an unrelated loan "never ends the call"; ask property type next.
- Section 11: keep the customer's exact hour and put the same day/time in callback_time.

Results: see the v4 table in the README (filled in from `eval/results/v4/` as the slow runner finishes; see below).

## Eval-infrastructure findings (honest notes)
- **Groq limits are per organisation**, not per key. Running two keys in parallel just splits the same 200K/day budget.
- **No prompt caching** on this account (`cached_tokens` is always 0), so each turn re-pays the full ~4.9K prompt. That's why the main layer is **turn-level golden tests** (one API call per test) rather than full simulated calls (~15 calls each). The simulated-call harness (`eval/run_eval.py`, 39 scenarios, customer simulator on gpt-oss-20b) is built and working, but it wasn't run at scale for budget reasons.
- **gpt-oss on Groq can't return spoken text and a tool call in the same message**, so when it calls end_call its closing line isn't visible in the eval. `closing_line_spoken` is therefore a soft flag for gpt-oss. On Retell, GPT 5.6 Terra speaks first and then calls end_call. **Verify this on the live calls.**
- `eval/slow_runner.sh` keeps running a test list at the rate the free tier allows (run → hit the cap → wait 40 min → resume).
