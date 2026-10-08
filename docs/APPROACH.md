# Approach: Requirements → Rules → State → Decision tree → Conversation rules → Edge cases → Prompt → Testing matrix

This follows the build order recommended in the company's prep guide. Each step produced an artifact in this repo.

| Step | Artifact | Summary |
|---|---|---|
| 1. Requirements | This file (below) | 15 requirements extracted from the assignment PDF |
| 2. Eligibility rules | `docs/RULES_TABLE.md` | Every rule explicit: eligible, disqualify, or clarify once |
| 3. State variables | `docs/RULES_TABLE.md`, prompt Section 8 | 7 checklist items (item 5 = occupation **and** income mode) plus transfer flag and callback time |
| 4. Decision tree | `docs/FLOW.md` (mermaid) | Stages A, B, C, the handoff gate, and exits at any stage |
| 5. Conversation rules | Prompt Sections 4, 5, 12 | Voice style; **extract first, validate second, update state third, ask the next missing question fourth** |
| 6. Edge cases | `docs/DESIGN_DECISIONS.md` | 30 ambiguous cases, each with the choice made and why |
| 7. System prompt | `prompt/system_prompt.md` (`prompt/versions/` keeps every version) | About 4.8K tokens, 16 sections, `{{variables}}` for Retell |
| 8. Testing matrix | `docs/TESTING_MATRIX.md`, `eval/`, `tests/live_call_scripts.md` | Turn-level golden tests, a simulated-call harness, and 12 live Retell calls |

## 1. Requirements (from the assignment)
1. Verify the customer is `{{customer_name}}` before sharing anything.
2. Busy → ask for a callback time → end.
3. Present the loyalty offer: pre-approved LAP up to 75 lakh.
4. Capture 7 items **in sequence**: property type, ownership, original documents, loan amount, occupation + income mode, market value, tenure.
5. Information given out of order is recorded and **never asked again**.
6. Disqualify **immediately**, at any point: agricultural property, no originals, cash income, tenure outside 3 to 15 years.
7. Above 75 lakh → explain the cap → offer to proceed with 75 lakh.
8. Existing loan on the property or an EMI-reduction request → loan-transfer specialist will contact them → end.
9. Hand off **only** after all 7 items are answered and pass; go back for anything skipped.
10. The handoff says a senior loan expert will call with **exact interest rates**, so the agent never quotes rates.
11. Use all variables: company_name, customer_name, agent_name, agent_gender (strict), current_date/day/time, additional_context_from_rag, language_to_speak (English or Hindi), conversation_history, customer_utterance.
12. Handle full sentences, interruptions and fillers; don't build a yes/no bot.
13. Professional, advisory, natural voice.
14. Implement on a voice platform (Retell AI) and test with multiple realistic calls.
15. Submit the prompt plus public links to recordings and transcripts.

## Point 40, applied
The guide names *"Extract first, validate second, update state third, ask the next missing question fourth"* as the strongest differentiator. In this repo:
- **Prompt:** Section 5 is titled with that sentence and spells out the 4 steps in that order, using the guide's own example (1.1 crore, joint, 60 lakh → ask original documents).
- **Eval:** test `T50` sends exactly that utterance and checks deterministically that the next question is documents and none of the 4 given items is asked again. `T13`, `T14`, `T15`, `H08` and `H10` test the same behaviour in other phrasings and in Hindi.
- **Live calls:** call #1 in `tests/live_call_scripts.md` speaks the guide's example on a real Retell call, so the grader can hear it.
- **Submission:** recording #1 is listed first and labelled "Point 40: extract → validate → update → ask next missing".
