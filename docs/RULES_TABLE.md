# State and rules table

| # | Item (internal record) | Natural question (EN) | Eligible | Not eligible: immediate polite close | Needs one clarifying question |
|---|---|---|---|---|---|
| 1 | `property_type` | What kind of property is it: residential, commercial or industrial? | House, flat, bungalow, villa; shop, office, showroom, godown; factory, industrial shed; mixed use | Agricultural: farmland, khet, खेती की ज़मीन, orchard, farmhouse | "plot", "land", "ज़मीन": agricultural or a residential/commercial plot? |
| 2 | `ownership` | Only in your name, or jointly owned? | Sole; joint with spouse, parents, siblings or partner | *(none)* | Only in a family member's name: record it, continue, the expert reviews |
| 3 | `original_documents` | Original documents available for verification? | At home, in a bank locker, with a parent or co-owner | Only photocopies, lost, not issued, still with the builder | "Probably somewhere": confirm once. **With a bank for a loan: transfer flow** |
| 4 | `loan_amount` | How much loan are you looking for? | Up to 75 lakh | More than 75 lakh **and the customer declines 75 lakh** | More than 75 lakh (including 1 crore, or 70 to 80 lakh): "Max is 75 lakh, proceed with 75?" "The maximum" means 75 |
| 5 | `occupation` + `income_mode` | Salaried or self-employed, and is income in the bank or in cash? | Salaried or self-employed **and** income into a bank account | Income in cash | Mixed cash and bank: is the main income bank or cash? Retired or homemaker: record, continue |
| 6 | `market_value` | Roughly what's the current market value? | Any estimate (no minimum, no loan-to-value rule) | *(none, never invented)* | "Don't know": ask once for a rough guess, else record "unsure" |
| 7 | `tenure_years` | Over how many years, from three to fifteen? | 3 to 15 years inclusive (36 to 180 months) | Under 3 or over 15 years | Range crossing the limit ("two or three years"): ask for the exact number |
| – | `existing_loan_on_property` / `emi_reduction` | Asked once before item 1 | No | **Transfer flow** at any stage (not a disqualification) | Unrelated personal, car or phone loan: not a trigger |
| – | `callback_time` | When should we call back? | Resolved to day, date and time from `current_date/day/time` | – | Only "later": ask once for a rough time |

**Priority when several things happen in one utterance:** transfer > disqualification > cap question > busy > next missing item.

**Handoff gate:** all 7 items answered (item 5 needs both parts), no rule failed, no transfer trigger. Anything skipped gets asked before the handoff. The words "eligible", "qualified" and "approved" are never used before the gate passes.

**Outcomes** (one per call, emitted with `end_call` / Retell Post-Call Extraction):
`qualified_handoff`, `disqualified_property_type`, `disqualified_documents`, `disqualified_income_mode`, `disqualified_tenure`, `disqualified_loan_amount`, `transfer_specialist`, `callback_scheduled`, `wrong_person`, `not_interested`.
