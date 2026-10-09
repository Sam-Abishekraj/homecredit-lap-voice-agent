
### v4 — openai/gpt-oss-120b: 8/8 passed (100%)

| Language | Pass |
|---|---|
| English | 8/8 |

| Category | Pass |
|---|---|
| callback | 1/1 |
| disqualify | 1/1 |
| greeting | 2/2 |
| loan_cap | 1/1 |
| out_of_order | 2/2 |
| transfer | 1/1 |

Soft style flags (not scored): multi-question turns 1, markdown/symbols 0, digits in speech 0, mean words/turn 28.9

### v4 — qwen/qwen3.8-27b: 15/16 passed (94%)

| Language | Pass |
|---|---|
| English | 13/14 |
| Hindi | 2/2 |

| Category | Pass |
|---|---|
| callback | 1/1 |
| disqualify | 4/4 |
| greeting | 4/4 |
| handoff_gate | 0/1 |
| loan_cap | 1/1 |
| out_of_order | 4/4 |
| transfer | 1/1 |

Failures:
- **T39** Skipped item (market value) must be asked before handoff — failed `does_not_end, asks_market_value` — reply: "Thank you, that's everything I needed. Your details meet the basic criteria for this offer. A senior loan expert from Home Credit will call you shortly to share" → end_call qualified_handoff

Soft style flags (not scored): multi-question turns 0, markdown/symbols 0, digits in speech 0, mean words/turn 26.7