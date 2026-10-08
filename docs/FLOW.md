# Call flow

The diagram is the state machine that `prompt/system_prompt.md` implements in natural language.
Exits on the right (busy, transfer, disqualification) can fire at any stage, not only where they are drawn.

```mermaid
flowchart TD
    S([Call connects]) --> G["Stage A: greet + 'Am I speaking with {{customer_name}}?'"]
    G -->|"Who is this? / Is this a scam?"| G1["Name + company, no offer details;<br/>never asks OTP/PIN; re-verify"] --> G
    G -->|"Not the customer / wrong number"| WP["Share nothing, ask when to reach them"] --> E1(["end_call: wrong_person"])
    G -->|Busy| CB
    G -->|Confirmed| B["Stage B: loyalty offer, up to 75 lakh"]
    B -->|Not interested| NI(["end_call: not_interested"])
    B -->|Interested| TC{"Any loan running<br/>on this property?"}
    TC -->|"Yes / wants lower EMI"| TR["Transfer specialist message"] --> E2(["end_call: transfer_specialist"])
    TC -->|"No (or only an unrelated personal/phone loan)"| C

    subgraph C ["Stage C: 7-point checklist, run every customer turn"]
      direction TB
      X["1. EXTRACT every fact in the utterance (asked or not)"] --> Y["2. CHECK exits: transfer > disqualifier > busy/not interested"]
      Y --> Z["3. UPDATE record (latest clear correction wins)"]
      Z --> W["4. ANSWER any side question briefly (no rates)"]
      W --> V["5. ASK the earliest unknown item, 1 to 7"]
    end

    C -->|"Agricultural / photocopies only / cash income /<br/>tenure outside 3 to 15 yrs"| DQ["Polite 'not eligible for this offer' + short reason"] --> E3(["end_call: disqualified_reason"])
    C -->|"Amount > 75 lakh"| CAP{"'Max is 75 lakh.<br/>Proceed with 75?'"}
    CAP -->|Yes| C
    CAP -->|No| E4(["end_call: disqualified_loan_amount"])
    C -->|"Existing loan on property / EMI reduction<br/>(e.g. originals are with the bank)"| TR
    C -->|"Busy mid-way"| CB["Callback: resolve 'tomorrow evening' using<br/>current_date / day / time, read it back"] --> E5(["end_call: callback_scheduled<br/>(keeps captured items)"])
    C --> GATE{"Handoff gate:<br/>all 7 answered (5 = occupation AND income mode),<br/>no rule failed, no transfer?"}
    GATE -->|"No: something skipped"| C
    GATE -->|Yes| H["'Senior loan expert will call shortly<br/>with exact interest rates'"] --> E6(["end_call: qualified_handoff"])
```

## Per-turn algorithm (Section 5 of the prompt)

```
on customer utterance:
    facts   = extract_all(utterance)              # property, ownership, docs, amount, occupation, income, value, tenure, loans
    if transfer_trigger(facts):   say(transfer_script);  end_call("transfer_specialist")
    elif disqualifier(facts):     say(disqualify_script); end_call("disqualified_<reason>")
    elif busy / not interested / wrong person: handle exit
    record.update(facts)                           # a clear later correction overwrites
    answer_side_question_if_any()                  # never quote rates; RAG only for product facts
    if amount > 75 lakh and cap not answered: ask_cap()
    elif all_7_answered(record): handoff()         # gate
    else: ask(first_unknown_item(record))          # never re-ask a known item
```
