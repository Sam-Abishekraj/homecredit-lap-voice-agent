
### v1 — openai/gpt-oss-120b: 13/15 passed (87%)

| Language | Pass |
|---|---|
| English | 11/12 |
| Hindi | 2/3 |

| Category | Pass |
|---|---|
| callback | 2/2 |
| disqualify | 0/1 |
| greeting | 4/5 |
| not_interested | 1/1 |
| transfer | 3/3 |
| trust | 1/1 |
| wrong_person | 2/2 |

Failures:
- **H04** Hindi: cash income — failed `outcome` — reply: "जानकारी देने के लिए धन्यवाद, सुनीता शर्मा जी। क्योंकि आपका मुख्य आय कैश में आती है, आप अभी इस ख़ास ऑफ़र के क्राइटेरिया में नहीं आते। धन्यवाद, आपका दिन शुभ हो!"
- **T02** Verified + asks who it is -> presents the offer — failed `must_0` — reply: "I’m Priya from Home Credit, calling about a special benefit for our existing customers. May I confirm I’m speaking with Rahul Verma?"

Soft style flags (not scored): multi-question turns 1, markdown/symbols 0, digits in speech 0, mean words/turn 24.9

### v1 — qwen/qwen3.8-27b: 19/21 passed (90%)

| Language | Pass |
|---|---|
| English | 16/18 |
| Hindi | 3/3 |

| Category | Pass |
|---|---|
| adversarial | 1/1 |
| boundary | 1/1 |
| callback | 1/1 |
| disqualify | 2/3 |
| diversion | 3/3 |
| greeting | 2/3 |
| handoff_gate | 1/1 |
| language | 1/1 |
| loan_cap | 1/1 |
| natural_speech | 1/1 |
| ownership | 1/1 |
| privacy | 1/1 |
| transfer | 1/1 |
| wrong_person | 2/2 |

Failures:
- **T02** Verified + asks who it is -> presents the offer — failed `must_0` — reply: "This is Priya from Home Credit. I'm calling about a special benefit for our existing customers. Am I speaking with Rahul Verma?"
- **T47** Cash income volunteered before checklist — failed `outcome` — reply: "Thank you for sharing that, Rahul. Since your income is received in cash rather than a bank account, you don't meet the criteria for this specific offer at this"

Soft style flags (not scored): multi-question turns 0, markdown/symbols 0, digits in speech 0, mean words/turn 27.3