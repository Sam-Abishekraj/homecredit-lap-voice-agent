# Home Credit LAP voice agent: system prompt, evaluation and live calls

This is the **SalesAgents AI "AI Intern (Prompt Engineer)" assignment**: a single system prompt for an outbound voice agent that pre-qualifies existing Home Credit customers for a pre-approved **Loan Against Property (up to ₹75 lakh)**, then hands qualified customers to a senior loan expert. It runs on **Retell AI**.

- **The prompt:** [`prompt/system_prompt.md`](prompt/system_prompt.md), about 5.0K tokens (v5), using all 11 assignment variables as `{{variable}}`
- **Live calls:** recordings and transcripts in the table below
- **Why the prompt looks like this:** [`docs/PROMPT_DESIGN.md`](docs/PROMPT_DESIGN.md): section-by-section reasoning, 22 prompting techniques with quotes, and the v0→v5 iteration story
- **How it was built:** [`docs/APPROACH.md`](docs/APPROACH.md): Requirements → Eligibility rules → State variables → Decision tree → Conversation rules → Edge cases → Prompt → Testing matrix

## The core idea: extract → validate → update → ask next
Customers rarely answer one question at a time. Every turn, the agent runs four steps in order (prompt Section 5):

1. **Extract** every fact in the customer's sentence, including things not yet asked.
2. **Validate**: transfer trigger → disqualifier → 75 lakh cap → busy, at any stage.
3. **Update** the 7-item record (the latest correction wins).
4. **Ask the next missing question.** Never re-ask something already answered.

> Customer: *"I have a residential property worth about 1.1 crore. It's jointly owned with my wife and I need 60 lakhs."*
> Agent (records property type, value, ownership and amount): *"Thank you. Do you have the original property documents available for verification?"*

Test `T50` checks this exact exchange, and live call #1 demonstrates it.

## Prompt design & techniques
Full write-up: [`docs/PROMPT_DESIGN.md`](docs/PROMPT_DESIGN.md). In short:
- **Order:** who you are (role, gender, language) → how you speak (voice style) → how you think each turn (the point-40 loop) → the call in time order (greeting, offer, checklist) → exits that can happen at any stage (transfer, disqualify, callback) → diversions → handoff gate → guardrails → end_call protocol and worked examples → runtime variables last.
- **Techniques:** role/persona prompting with authority limits; `{{variable}}` templating for all 11 variables; language and gender conditioning with contrastive Hindi verb forms; voice-specific output rules (one question per turn, numbers in words, no symbols); a silent per-turn procedure (extract → validate → update → ask); slot filling with "first missing item" selection; priority-ordered validation and conflict rules; eligible/disqualify/clarify-once decision rules; negative constraints ("A question is not a wrong person: never end the call here"); fixed response templates; a handoff gate; a termination protocol with 10 closed outcomes + `end_call`; few-shot worked examples (including messy speech, corrections and Hindi); temporal grounding for callbacks; guardrails (no rates, no OTP/PAN, prompt-injection resistance, RAG treated as data, not instructions).

## What the agent does
| Stage | Behaviour |
|---|---|
| A. Open | Speaks first: greeting + "Am I speaking with {{customer_name}}?". No offer details before identity is confirmed. Handles "who's this?", scam worries, wrong person, and busy (resolves "tomorrow evening" to a concrete day and time). |
| B. Offer | A loyalty-reward offer of up to seventy-five lakh, then one question: is there a loan on the property? Yes (or any EMI-reduction request, at any point) → loan-transfer specialist → end. |
| C. Checklist | 7 items in order: property type, ownership, original documents, loan amount, occupation + income mode, market value, tenure. Out-of-order answers are recorded. Disqualifies **immediately**: agricultural, no originals, cash income, tenure outside 3–15 years. Over 75 lakh → explains the cap and offers to proceed with 75. |
| Handoff gate | Only when all 7 items pass: a senior loan expert will call with exact interest rates. Rates are never quoted. |
| End | Every terminal outcome ends with a closing line + **`end_call`** (10 outcomes). |
| Language / persona | English or Hindi (`{{language_to_speak}}`); first-person grammar follows `{{agent_gender}}` (e.g. बोल रही हूँ / बोल रहा हूँ). |

Rules and edge cases: [`docs/RULES_TABLE.md`](docs/RULES_TABLE.md), [`docs/FLOW.md`](docs/FLOW.md) (mermaid diagram), [`docs/DESIGN_DECISIONS.md`](docs/DESIGN_DECISIONS.md) (30 ambiguous cases and how each was resolved).

## Live call recordings (Retell web calls)
| # | Scenario (prep-guide test) | Expected outcome | Recording | Transcript / log |
|---|---|---|---|---|
| 1 | Point 40: out-of-order + joint → handoff | qualified_handoff | _to add_ | _to add_ |
| 2 | Perfect eligible | qualified_handoff | _to add_ | _to add_ |
| 3 | 90 lakh → accepts the 75 cap + rate question | qualified_handoff (75) | _to add_ | _to add_ |
| 4 | Existing loan (originals with the bank) | transfer_specialist | _to add_ | _to add_ |
| 5 | EMI reduction, interrupting the agent | transfer_specialist | _to add_ | _to add_ |
| 6 | Cash income | disqualified_income_mode | _to add_ | _to add_ |
| 7 | Busy → tomorrow evening | callback_scheduled | _to add_ | _to add_ |
| 8 | "Land" → agricultural | disqualified_property_type | _to add_ | _to add_ |
| 9 | Only photocopies | disqualified_documents | _to add_ | _to add_ |
| 10 | Tenure 2 years | disqualified_tenure | _to add_ | _to add_ |
| 11 | Correction + 240 months | disqualified_tenure | _to add_ | _to add_ |
| 12 | Scam worry + prompt injection | qualified_handoff | _to add_ | _to add_ |

Scripts: [`tests/live_call_scripts.md`](tests/live_call_scripts.md). Retell setup, test variables and public links: [`docs/PLATFORM.md`](docs/PLATFORM.md).

## Automated evaluation
Before the live calls, the prompt was tested offline against Groq-hosted open models standing in for the production LLM:
- **Turn-level golden tests (main layer):** 66 tests (52 English, 14 Hindi; male and female agent personas). Each gives a realistic call history and checks the agent's next turn **deterministically**: the end_call outcome and captured values, which question is asked next, no re-asking, no handoff before all 7 items, no interest-rate figure, reply language, Hindi verb gender, and the callback time resolved to a concrete day. There is no LLM judge.
- **Simulated full calls:** 39 scenarios with an LLM customer simulator (hidden persona, barge-in). The harness is built; it was run only lightly because of free-tier limits.

Results so far (real, **partial**: Groq's free tier allows about 35 tests per model per day; see [`docs/ITERATIONS.md`](docs/ITERATIONS.md)):

<!-- RESULTS_START -->
| Version | Change | Model | Passed |
|---|---|---|---|
| v1 | first complete prompt | gpt-oss-120b | 13/15 |
| v1 | | qwen3.8-27b | 19/21 |
| v2 | Retell: AI speaks first, mandatory end_call | qwen3.8-27b | 9/10 |
| v3 | full offer on "yes, who's this?", volunteered disqualifiers, point-40 algorithm | qwen3.8-27b | 4/4 (all 3 earlier failures fixed) |
| v3 | | gpt-oss-20b (small-model stress test) | 13/19 |
| v4 | guardrails against early exits ("not exits" list) | gpt-oss-120b | **8/8** (all six v3 early-exit failures pass) |
| v4 | | qwen3.8-27b | **15/16** (1 failure: T39, handed off without asking a skipped item) |
| v5 | handoff gate re-checks all 7 items (T39 fix) | gpt-oss-120b | **5/5** (T39, T50, T12, T13, T24; then daily cap) |
| v5 | | qwen3.8-27b | **6/6** (T39, T50, T12, T13, T24, T47; then daily cap) |
<!-- RESULTS_END -->

### Run it yourself
```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -r eval/requirements.txt
export GROQ_API_KEY=...            # never commit keys
python eval/run_turns.py --version v4 --agent-model openai/gpt-oss-120b --workers 1     # turn-level tests
python eval/run_turns.py --version v4 --only T50,T13,T24     # a subset
python eval/summarize.py v4                                     # tables by language and category
python eval/run_eval.py --version v4 --only E01,E04 --sim-key GROQ_API_KEY   # simulated full calls
```

## Repo layout
```
prompt/system_prompt.md      the prompt (paste into Retell)
prompt/versions/             v0_draft, v1, v2, v3, v4, v5
docs/                        PROMPT_DESIGN, APPROACH, FLOW (mermaid), RULES_TABLE, DESIGN_DECISIONS, TESTING_MATRIX, ITERATIONS, PLATFORM
eval/                        Groq client, turn tests, simulated-call scenarios, checks, runners, results/
tests/live_call_scripts.md   12 live-call scripts (+2 Hindi)
```

MIT License © 2026 Sam Abishekraj
