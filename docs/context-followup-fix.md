# Context and numeric follow-up fix

A synthetic reproduction showed that the model received the earlier conversation and generated an appropriate short study duration. The output guard rejected it because the earlier policy rejected every digit. That replaced the reply with a safety fallback and made the conversation appear to lose context.

The fix permits ordinary short times, durations and counts such as `7am`, `9:30 am` and `20 minutes`. Unverified contact-like numeric strings, numeric medication doses, clinical scores, unsafe advice and URLs remain blocked. This is a targeted pattern guard, not a clinical safety guarantee. The policy version is now `safety-1.4`.

Testing also exposed two separate issues. First, initial local model loading could exceed the old three-second classifier read timeout. The classifier now allows eight seconds; generation keeps its six-second limit. Explicit crisis rules still bypass the model. These are separate per-request read limits, so routine wall-clock latency can exceed the original ten-second target during cold starts or congestion.

Second, the model treated an ordinary request to recall a chosen time as a generic need for clarification. The classifier now uses explicit safety-specific wire labels: `NO_SAFETY_SIGNAL`, `UNCERTAIN_SAFETY` and `CURRENT_DANGER`. These map to the existing ROUTINE, CLARIFY and ESCALATE application states. The prompt distinguishes a normal question from uncertain personal safety. Invalid labels still fail closed, and deterministic safety rules cannot be downgraded. Current prompt revisions are `router-1.8/support-1.5`.

Failure details distinguish classifier failure, generation failure and output rejection without showing raw upstream errors. No real chat transcripts were stored or inspected; reproduction uses an invented study-planning conversation. The original 150-case dataset, personal-life development corpus, approved specifications and earlier evaluation runs remain unchanged.

## Executed checks

- `evidence/checks/pytest-context-fix.txt` records 78 passing tests. Added coverage checks harmless times and durations, blocked numeric contacts/doses/scores, model wire-label validation, short-reply context, and the Streamlit follow-up path.
- `evidence/context-numeric-fix-001` retains the initial short-timeout failure with the numeric guard already fixed.
- `evidence/context-numeric-fix-002` and `003` retain failures where the reminder request was misclassified.
- `evidence/context-numeric-fix-004` passes the full three-turn sequence from a deliberate cold model start, including correct recall of 7 am. The first full reply took approximately 8.2 seconds in that one observed cold run.
- `evidence/context-numeric-fix-005` passes the same sequence with the final support prompt. Its first reply took approximately 4.3 seconds; the model continued the study plan and recalled 7 am. These are individual engine observations, not service guarantees.
- `evidence/context-fix-personal-life-001` and `context-fix-outage-001` contain fresh personal-life development regressions for the current versions. These do not replace independent held-out validation or student quality ratings.

Reproduce with a fresh run ID:

```bash
uv run pytest -q
uv run python scripts/check_context_followups.py --run-id your-context-check --cold
uv run python -m mannsahara.evaluate --suite personal-life --split development --run-id your-personal-check
```

The `--cold` option deliberately unloads the selected local model before testing. The context check logs invented content only and fails if a route is incorrect, a fallback occurs, or the final response fails to recall the chosen time. Session memory remains bounded to the last eight messages (four user/assistant exchanges); this fix does not add unlimited history or persistent memory. Refresh and start a fresh session if the previous conversation already contains safety fallbacks.
