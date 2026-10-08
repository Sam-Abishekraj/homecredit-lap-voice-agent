
### v3 — openai/gpt-oss-20b: 13/19 passed (68%)

| Language | Pass |
|---|---|
| English | 13/19 |

| Category | Pass |
|---|---|
| callback | 0/1 |
| disqualify | 3/4 |
| greeting | 3/4 |
| loan_cap | 0/1 |
| not_interested | 1/1 |
| out_of_order | 1/2 |
| transfer | 2/3 |
| trust | 1/1 |
| wrong_person | 2/2 |

Failures:
- **T03** 'Who is calling?' before confirming -> no offer details, re-verify — failed `does_not_end, must_0, must_1` — reply: "" → end_call wrong_person
- **T06** Busy at greeting with relative time — failed `callback_resolved` — reply: "" → end_call callback_scheduled
- **T12** Unrelated phone EMI is not a transfer — failed `does_not_end, asks_property_type` — reply: "" → end_call transfer_specialist
- **T13** All 7 details + no loan volunteered at once -> handoff — failed `outcome, slots` ['property_type: want residential got None', 'ownership: want sole got None', 'documents: want available got None', 'loan_amount_lakh: want 50 got None', 'income_mode: want bank got None', 'occupation: want self_employed got None', 'tenure_years: want 8 got None'] — reply: "Thank you, Rahul. That's everything I needed. Your details meet the basic criteria for this offer. A senior loan expert from Home Credit will call you shortly t"
- **T17** Ambiguous 'plot' -> clarify agricultural or not — failed `does_not_end, must_0` — reply: "" → end_call disqualified_property_type
- **T24** Asks 90 lakh -> explain cap, offer 75 — failed `does_not_end, must_0, must_1` — reply: "" → end_call disqualified_loan_amount

Soft style flags (not scored): multi-question turns 0, markdown/symbols 0, digits in speech 0, mean words/turn 9.4

### v3 — qwen/qwen3.8-27b: 4/4 passed (100%)

| Language | Pass |
|---|---|
| English | 3/3 |
| Hindi | 1/1 |

| Category | Pass |
|---|---|
| disqualify | 2/2 |
| greeting | 1/1 |
| out_of_order | 1/1 |

Soft style flags (not scored): multi-question turns 0, markdown/symbols 0, digits in speech 0, mean words/turn 42.0