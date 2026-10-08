# Voice platform: Retell AI

*Checked against Retell's public docs on 8 Oct 2026. Dashboard labels can shift slightly; if a button name differs, look for the closest match.*

**Why Retell:** $10 free trial credit with no payment method needed; browser web-call testing needs no phone number ([quick start](https://docs.retellai.com/get-started/quick-start)). Variables use the same `{{variable}}` syntax as the assignment ([dynamic variables](https://docs.retellai.com/build/dynamic-variables)). It has a built-in **End Call** tool ([end call](https://docs.retellai.com/build/single-multi-prompt/end-call)), structured **Post Call Extraction** ([docs](https://docs.retellai.com/features/post-call-analysis-overview)), Hindi `hi-IN` support ([languages](https://docs.retellai.com/build/language-support)), and recording and log URLs that **don't expire by default** ([secure URLs](https://docs.retellai.com/accounts/signed-secure-url)).
**Alternative:** Bolna (India-first, $5 free credit, can ring your own verified +91 number, strong Hindi) if a real Indian phone call is ever needed ([pricing](https://www.bolna.ai/pricing)).
Retell-managed phone numbers are US/Canada only and need a card, so **use browser web calls**; the assignment allows them.

## 1. Agent configuration (Sam's current setup)

| Setting | Value |
|---|---|
| Agent type | Single Prompt, named `Home Credit LAP Agent` |
| Model | GPT 5.6 Terra (Retell default) |
| Voice | Nico (male), which matches `agent_gender=male`, `agent_name=Arjun` |
| Language | English (India) |
| Welcome message | **AI speaks first → Dynamic message.** The prompt's Section 6 produces the opening: greeting + "Am I speaking with {{customer_name}}?" |
| Tools | Built-in **end_call**. The prompt (Section 15) makes the agent call it right after the closing line of every terminal outcome. Suggested tool description: `End the call immediately after you have spoken the closing line for a terminal outcome: qualified handoff, any disqualification, transfer specialist, callback scheduled, wrong person, or not interested.` |
| Prompt | Paste **all** of `prompt/system_prompt.md` |
| Timezone | Set the agent timezone to **Asia/Kolkata** if the setting exists; otherwise pass `current_time` yourself (see below) |
| Security & fallback | Keep **Opt In Secure URLs OFF**; otherwise recording and log links expire (24 hours by default) |

**Optional, recommended: Post Call Extraction** (agent editor → Post Call Extraction → add fields). This gives graders a structured result per call:
- `outcome`, a Selector with these options: qualified_handoff, disqualified_property_type, disqualified_documents, disqualified_income_mode, disqualified_tenure, disqualified_loan_amount, transfer_specialist, callback_scheduled, wrong_person, not_interested
- Text fields: `property_type`, `ownership`, `original_documents`, `occupation`, `income_mode`, `market_value`, `callback_time`
- Number fields: `loan_amount_lakh`, `tenure_years`

## 2. Set the variable values for test calls

Retell replaces `{{variable}}` at call time. A variable with no value stays as raw `{{name}}` text, and an empty string blanks it ([docs](https://docs.retellai.com/build/dynamic-variables)).

**Exact steps** ([web call testing](https://docs.retellai.com/test/test-web), [LLM playground](https://docs.retellai.com/test/llm-playground)):
1. Open the agent editor, then the **Test** panel on the right.
2. Next to the **Test LLM / Test Audio** tabs, open the **Test Inputs** dropdown and go to the **Dynamic Variables** tab.
3. Enter the values below and click **Save**. They apply to both Test Audio (voice) and Test LLM (text) runs. They're saved **in your browser, not on the agent**, so re-enter them on another browser or machine.
4. Optional backup: set the same values as **Default Dynamic Variables** under *Security & fallback settings* so they also apply outside the test panel.

| Variable | Test value |
|---|---|
| company_name | Home Credit |
| customer_name | Sam |
| agent_name | Arjun |
| agent_gender | male |
| language_to_speak | English |
| current_date | the date you record, e.g. `10 October 2026` |
| current_day | the weekday, e.g. `Saturday` |
| current_time | leave blank to use Retell's built-in `{{current_time}}` (set the agent timezone to Asia/Kolkata), or type e.g. `11:30 AM IST` |
| additional_context_from_rag | `Loan Against Property pre-approved offer for existing Home Credit customers. Maximum amount 75 lakh. Tenure 3 to 15 years. Exact interest rates are shared by the senior loan expert.` |
| conversation_history | `Provided by the platform as the call transcript.` |
| customer_utterance | `The customer's latest message in the transcript.` |

Tip: before recording, run each script once in **Test LLM** (text, cheaper and faster) to catch issues, then do the voice call in **Test Audio**.

## 3. Make the test calls
1. **Test** → **Test Audio** → **Run Test**, then allow the microphone. Use headphones in a quiet room.
2. Follow `tests/live_call_scripts.md` in order. Talk naturally and interrupt once on purpose.
3. Click **End the Call** only if the agent doesn't hang up itself. It should end on its own after every terminal outcome, which is one of the things being checked.

## 4. Get public recording + transcript links (for the submission form)
Each finished call (web calls included) appears under **Data → Call History** ([docs](https://docs.retellai.com/features/session-history)).
1. Open **Call History** and click the call. The detail panel shows the **recording player**, the **Transcription** (with the end_call tool event), **Conversation Analysis** (your extraction fields) and **Detail Logs**. Check them against the script.
2. **Public links from Retell:** in Call History, open **Actions → Export**, tick the columns for transcript, **recording URL** and **public log URL**, and submit. When it's ready, go to **Actions → Export records** and download the CSV. The recording URL (`…/recording.wav`) and public log URL (`…/public_log.txt`, the turn-by-turn LLM log) are plain links that open without login while secure URLs are off ([Get Call API fields](https://docs.retellai.com/api-references/get-call)).
   - Alternative: with your Retell API key on your own laptop, run `curl -s -H "Authorization: Bearer $RETELL_API_KEY" https://api.retellai.com/v2/get-call/<call_id>`, which returns `recording_url`, `public_log_url` and `transcript`. Check the exact path on the [Get Call](https://docs.retellai.com/api-references/get-call) page; it shows `GET /v1/get-call/{call_id}` or `/v2/...` depending on the version.
3. **Recommended for the form:** make one Google Drive folder, `HomeCredit-LAP-Voice-Agent-Calls`. For each call, upload the WAV (download it from the recording player or the recording URL) plus a transcript `.txt` (use the copy button in Transcription). Name them like `01_point40_out_of_order.wav` / `01_point40_out_of_order_transcript.txt`. Then **Share → General access → Anyone with the link → Viewer**. Submit the folder link, and optionally the Retell recording and public-log URLs too.
4. **Open every link in an incognito window before submitting.**

## 5. Submission plan (prep guide point 40 + its deliverables list)
1. **Complete system prompt text:** paste `prompt/system_prompt.md` exactly as it is in Retell.
2. **Test audios:** the 12 core calls in `tests/live_call_scripts.md` (one per guide test). **Call #1 goes first** and is labelled *"Point 40: extract → validate → update → ask next missing"*: in one sentence the customer gives property type, value, ownership and amount, and the agent's very next question is original documents.
3. **Transcripts:** one `.txt` per audio, plus the Retell public log URL (it shows the end_call tool event).
4. **Approach documents (optional but recommended):** the README plus `docs/APPROACH.md`, which follows the guide's chain Requirements → Rules → State → Decision tree → Conversation rules → Edge cases → Prompt → Testing matrix. Link these only if Sam approves publishing the repo.
