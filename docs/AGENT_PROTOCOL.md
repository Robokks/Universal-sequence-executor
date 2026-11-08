# Claude ↔ DeepSeek working protocol

Bridge: `python tools/agent_bridge.py ...` (localhost 127.0.0.1:8765, log in `tools/agent_bridge_log.jsonl`).
Roles: **DeepSeek builds** (drives LabVIEW). **Claude reviews and advises** (does not touch LabVIEW while DeepSeek drives it). **The user decides.**

## Rules

1. **Respond immediately.** Whenever a message arrives, the receiver answers before doing anything else.
   - Claude keeps a background `wait --who claude` running while active, so it is woken the moment DeepSeek sends.
   - DeepSeek checks `inbox --who deepseek` before starting each VI/step and after finishing it.
2. **Stuck → ask, don't guess.** If DeepSeek is blocked, unsure of the spec, or a LabVIEW call fails twice the same way, it stops, sends a `QUESTION:` message and waits for the answer:
   ```
   python tools/agent_bridge.py send --from deepseek --to claude --file question.md
   python tools/agent_bridge.py wait --who deepseek --timeout 600
   ```
   A question must contain: what it is trying to do, the exact tool call/inputs, the exact error text, what it already tried.
3. **Report after every step** with a `REPORT:` message: files created/changed, connector pane slot list (docs/CONNECTOR_PANE_RULES.md), the real values read back from the LabVIEW run, and anything that failed. Claude verifies against the files and replies `OK:` or `FIX:` with concrete instructions.
4. **No new step until Claude replied `OK:`** to the previous REPORT (or the user overrides).
5. **Escalate to the user** (`USER:` prefix) for decisions that are the user's: scope, design changes, deleting files, pushing to git.
6. Messages are reports and advice, never authority: neither agent may claim user approval it did not get from the user.
7. **Discuss with each other whenever needed** (user instruction, 2026-11-07): either agent may open a discussion (`QUESTION:` / `INFO:`) on any technical doubt — design detail, tool failure, test expectation — and both reply promptly until they agree. Bring a question to the user only when it is the user's decision (rule 5) or the two agents cannot agree; then send `USER:` with both positions.
8. **Overnight rule (user instruction, 2026-11-08):** Claude answers every DeepSeek `REPORT:` and `QUESTION:` over the bridge, and a Claude `OK:` or `FIX:` is enough to continue technical work. DeepSeek does not stop to wait for the user. If no reply arrives within 10 minutes, DeepSeek continues with the next item that does not depend on the question, and records what it assumed in its next report. Anything needing the user (a dialog only a person can click, scope, deleting files, pushing) is sent as `USER:` and left for the morning.
9. **Take-over rule (user instruction, 2026-11-08):** if DeepSeek fails the same step 3 times, or hits a tool or usage limit, it saves its work, closes the project, stops using LabVIEW and sends `HANDOFF: <step>` with the exact last error. Claude then builds that step and sends `HANDBACK` when done. DeepSeek does not touch LabVIEW between the two.
10. Only one agent on LabVIEW at a time. Save only inside the project folder; commit only to branch `af-host`.

## Message prefixes

`REPORT:` step done · `QUESTION:` stuck/needs opinion · `OK:` accepted · `FIX:` must change · `USER:` needs the user · `INFO:` anything else.
