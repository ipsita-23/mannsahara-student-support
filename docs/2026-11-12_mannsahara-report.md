# MannSahara implementation and evaluation report

CSE473 CA1 · Group 9 · SIH25092 · 12 November 2026  
Ipsita Umang, 12309971 · Annamneendi Suresh Kumar, 12317960

> Historical implementation/evaluation report. The app has since gained explicit personal-life coverage and revised prompts; see the [scope update](personal-life-scope-update.md). Results below remain attributed to their original versions.

## Outcome and scope

The project now contains a runnable Streamlit chatbot, a local instruction-tuned LLM adapter, four-state safety workflow, 150 frozen original fictional dialogues, automated tests, exported case/turn logs and setup instructions. All development and evaluation content is synthetic. No real students, clinical records, DAIC-WOZ, scraped disclosures or live trials were used. The original editable and PDF specifications remain byte-for-byte unchanged.

This prototype is functional, but **not all acceptance targets are met**. The final live regression escalated every labeled critical turn, while escalation precision was 72.7%, below the 90% target. Independent human quality scoring is pending. An outage miss was found and fixed; the subsequent checks are regression evidence, not fresh independent validation. No clinical safety or effectiveness claim is supported.

## Implementation

The flow is input validation → explicit rules and persistent state → constrained classifier → fixed clarification/escalation or supportive generation → deterministic output guard → display. `ROUTINE`, `CLARIFY`, `ESCALATE` and `SAFE_FALLBACK` are operational routes, never clinical risk scores. Explicit danger and an already-latched escalation bypass the model entirely. A fresh-session control is the only way to clear escalation. The last eight messages inform the model; both model and display history are bounded in memory.

Qwen2.5 1.5B Q4_K_M runs locally through Ollama 0.40.16. The exact model digest is `65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b`. Settings: temperature 0, seed 47309, context 2048, classifier maximum 24 tokens, support maximum 140 tokens. Final versions: `safety-1.3`, `router-1.2`, `support-1.0`. Classifier and generation read timeouts are three and six seconds. The backend is replaceable; no fine-tuning or vector database is used.

The demo environment was an Apple M2 MacBook Air with 8 GB memory, macOS arm64 and Python 3.11.16. The locked package versions and OS build are recorded in `uv.lock` and per-run configuration. A fictional hello preflight loaded the model before recorded runs. Timings are warm/mixed engine timings, not cold-start or browser display guarantees.

Generated responses are screened for medical/diagnostic language, harmful patterns, unsupported promises, invented contacts, numbers/URLs and malformed output. Rejected text is replaced by a fixed safety check. Exceptions are sanitized. These pattern checks are limited and cannot certify that arbitrary generated text is safe. The crisis template encourages urgent local emergency help, a trusted nearby person and campus staff; it never claims to contact anyone. No verified regional contact is configured, so no telephone number or inferred location is displayed.

## Dataset and execution

`data/dialogues.jsonl` has 50 development cases (20 routine, 10 ambiguous, 15 crisis, 5 adversarial/indirect) and 100 held-out cases (40, 20, 30, 10). Every case includes messages, per-turn and final expected routes, escalation requirement, rationale, split and scenario group. The manifest freezes SHA-256 `927bbb57f285784d2319eff1f0b6fcd6c0aacc554a29f7d62b306dd255466d22`.

The author assigned specific scenario groups within a single split and checked exact dialogue uniqueness. Broad assignment categories appear in both splits as required. **Semantic paraphrase independence is not established:** direct safety phrases overlap across splits, and one implementation agent authored both data and labels. Independent student label adjudication has not occurred. This is a limitation against the specification's leakage-reduction intent, not proof of independent held-out generalization.

Development runs 001–004 were retained. Prompt revisions used development outputs only: adding explicit ordinary/ambiguous examples improved final route matches from 25/50 to 44/50 and then 49/50. Unit tests added third-person and contextual safety handling. The first held-out live run used the frozen prompt. Its output was not used to tune the classifier prompt further.

The first outage check missed `TEST-129:1` (“My roommate wants to die tonight…”). A development outage check also missed `DEV-033:1` (“ending my life”). The final rule revision recognizes grammatical forms such as wants, ending, taking, hurting, and third-person references. Original failed logs remain intact. Because held-out failure evidence was inspected before this fix, **both final runs are labeled regression checks**. The specification's requirement for a newly independently prepared validation set after a critical miss remains pending; retesting the same corpus does not satisfy it.

## Measured results and targets

Positive means the final user turn is labeled as requiring immediate escalation. A separate gate checks **every** critical turn, including intermediate and follow-up turns. There are 32 positive dialogues and 35 critical turns in the 100-case/111-turn held-out corpus.

| Run | TP | FP | FN | TN | Recall | Precision | Missed critical turns |
|---|---:|---:|---:|---:|---:|---:|---:|
| First live held-out (`heldout-001`) | 32 | 12 | 0 | 56 | 100% | 72.7% | 0 |
| First outage (`outage-001`) | 31 | 1 | 1 | 67 | 96.9% | 96.9% | 1 |
| Final live regression (`regression-002`) | 32 | 12 | 0 | 56 | 100% | 72.7% | 0 |
| Final outage regression (`outage-regression-002`) | 32 | 1 | 0 | 67 | 100% | 97.0% | 0 |

| Acceptance item | Target | Final measured evidence | Status |
|---|---|---|---|
| Critical gate | Zero missed critical turns | 0/35 in both final regression runs | Regression passes; fresh independent validation pending |
| Live escalation precision | ≥90% | 72.7% | Not met |
| Exact routing | Report outcomes, no specified percentage target | 84/100 final routes; 80/100 dialogues correct on every turn | Measured |
| Unsafe output | Zero unsafe outputs | Zero delivered ROUTINE outputs flagged by the automated guard; one generation blocked | Human safety review pending; guard is not independent evidence |
| Crisis engine response | ≤2 s for ≥95% | 35/35 on intended path; p95 0.026 ms, maximum 0.238 ms | Engine-level timing met; full display timing unmeasured |
| Routine engine response | ≤10 s for ≥95% | 42/46 expected-routine turns delivered as ROUTINE on time (91.3%); cohort p95 1,079.306 ms | Delivery fraction not met; all cohort replies were below the time limit |
| Human quality | Mean ≥4/5 in empathy, relevance, safety | No independent student ratings | Pending, not a measured result |

The live regression had one fallback and one blocked generation. The outage regression had 75 fallback turns; ordinary support is deliberately unavailable during an outage. Fast fallbacks are not counted as successful routine delivery. Timing uses sequential engine wall-clock, including relevant model calls, excluding browser rendering, metadata collection and network transport to a browser. Submillisecond crisis timings reflect the fixed local code path.

All live exact-route failures are enumerated in `summary.json` and retained in CSV/JSON. Examples include conservative escalation of ambiguous hopelessness and a fictional-quotation case, a routine message receiving clarification, and an output guard rejection producing SAFE_FALLBACK. These false positives explain why precision remains below target. A broad guard's rejection is not automatically a proven major safety failure; rejected text is not retained, and independent output review is pending.

## Checks, evidence and remaining work

`evidence/checks/pytest-final.txt` records the complete passing test suite, including Streamlit AppTest for the notice gate, chat, outage, escalation persistence, reset and invalid backend configuration. Earlier UI-test failures were test harness path/button-selection mistakes; their raw logs are preserved. `evidence/checks/ruff.txt` records static checks. The live server returned `ok` on its health endpoint. No browser screenshot or manual visual/keyboard audit is claimed.

Evidence → finding → path:

- **E1:** frozen data/specification hashes and dataset-integrity tests → **F1:** originals preserved and evaluation inputs frozen → validation runs check these hashes before accepting cases.
- **E2:** original and final live/outage CSV, JSONL and summaries → **F2:** fixed crisis routing survives the tested outage after the rule fix, with over-referral still present → input → explicit rules/latch → fixed template; other cases use classifier → generator/guard or fallback.
- **E3:** final pytest/AppTest and static-check logs → **F3:** the tested integration and failure paths work → opening notice → fictional chat → safety routing → fresh-session reset. This does not establish clinical safety or screen-reader/browser behavior.

Reproduce from the project root using the README, then run `uv run pytest -q`, `uv run ruff check .` and `uv run python -m mannsahara.evaluate --split held_out --run-id your-new-run`. Add `--backend outage` for the outage path. Existing run directories cannot be overwritten. The final regression configurations include exact code/prompt/dependency hashes and source snapshots. Early development runs 001–002 predate source snapshots; their raw results and hashes are preserved, but their old source is not packaged as a runnable snapshot.

Both named students must independently complete their blank rating CSVs, resolve label disagreements and document any major failures. A separately prepared validation corpus is required after the outage fix; it must not be derived by tuning to these held-out outputs. Manual opening-screen capture and visual/keyboard checks remain on the demo checklist. These pending items and unmet precision/delivery targets prevent claiming full acceptance of the specification. The project remains suitable for demonstrating the implemented workflow and its measured synthetic limitations.

Sources: unchanged [approved specification](../output/pdf/group-09-mannsahara-specification.md); original assignment page 3 row 9; [Ollama chat API](https://docs.ollama.com/api/chat); [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest); [NIMH support principles](https://www.nimh.nih.gov/health/publications/5-action-steps-to-help-someone-having-thoughts-of-suicide). Implementation details are in [the operational policy](safety-policy.md) and [review/demo guide](review-guide.md).
