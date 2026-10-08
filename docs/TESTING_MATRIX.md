# Testing matrix

Three layers. Each guide scenario is covered by at least one automated test and, where it matters, a live call.

| Prep-guide scenario | Turn-level golden tests (`eval/turn_tests.py`) | Simulated call (`eval/scenarios.py`) | Live Retell call (`tests/live_call_scripts.md`) |
|---|---|---|---|
| Point 40: extract → validate → update → ask next | T50, T13, T14, T15, H08, H10 | E04, E05, H08 | #1 |
| Test 1: perfect eligible | T34, T35, T40, H11 | E01 | #2 |
| Test 2: agricultural | T16, T19, T43, H03 | E10, E11, E17, H03 | #8 |
| Test 3: cash income | T28, T30, T47, H04 | E13, E14, E18, H04 | #6, #14 |
| Test 4: missing originals | T20, T23 | E12 | #9 |
| Test 5: tenure too short | T32, T46 | E15 | #10 |
| Test 6: tenure too long | T33, H13 | E16 | #11 |
| Test 7: 90 lakh | T24, T25, T26, T27, T40, H07 | E20, E21, E22, H07 | #3 |
| Test 8: joint ownership | T48, T50 | E02, E03, H01 | #1 |
| Test 9: existing loan | T10, T11, T22 | E30, E31 | #4 |
| Test 10: EMI reduction | T42, H05 | E32, H05 | #5 |
| Test 11: out-of-order | T13, T14, T15, T50, H08, H10 | E04, E05 | #1 |
| Test 12: busy | T06, T07, T41, H06 | E40, E41, H06 | #7 |
| Contradiction / correction | T35, T43 | E06, E17 | #11 |
| Interruption / line drop | T44 ("hello? are you there?") | E07 (simulated barge-in truncates the agent mid-sentence) | #5 |
| Ambiguous answer | T17, T18, T23, T29, T46 | E11, E14 | #8 |
| Diversion: interest rate, branch, documents | T36, T37, T45, H14 | E07 | #3 |
| Verification, wrong person, scam | T00, T00F, T01 to T05, T09 | E42, E44 | #12 |
| Prompt injection | T38 | E45 | #12 |
| Handoff gate (skipped item) | T39 | E04 | #1 |
| Privacy (third party, Aadhaar) | T04, T49 | E42 | n/a |
| Unrelated loan is not a transfer | T12 | E33 | n/a |
| Hindi + agent gender | H01 to H14 (female and male agents) | H01 to H09 | #13, #14 |
| AI speaks first (Retell) | T00 (male Arjun), T00F (female Priya) | all simulated calls start agent-first | all |

**Deterministic checks** (no LLM judge): outcome from the `end_call` arguments, captured slot values, the next question asked, no re-ask, no handoff before all 7 items, no interest-rate pattern, language (Devanagari ratio), Hindi first-person verb gender, callback time resolved to a concrete day, no offer details disclosed to a third party, no prompt leak.
