# Evidence index

All messages and responses in these logs belong to the frozen fictional corpus. Run directories are never overwritten. `turns.jsonl` preserves every executed turn; `cases.csv` summarizes final turns. Summaries also check intermediate critical turns. Read exact settings, hashes and timing scope in each `config.json`.

| Run | Purpose |
|---|---|
| `development-001` | Original prompt; over-referral identified |
| `development-002` | Development-only prompt revision and third-person rule |
| `development-003` | Additional development examples; exact source snapshots start here |
| `development-004` | Unit-driven context/negation fixes before first held-out execution |
| `heldout-001` | First frozen live-model held-out run; no critical misses, precision target failed |
| `outage-001` | First outage run; one critical miss, retained unchanged |
| `development-outage-001` | Development outage check; grammatical danger wording miss reproduced |
| `regression-002` | Final live regression on the reused frozen set; no fresh validation claim |
| `outage-regression-002` | Final outage regression; zero missed critical turns |
| `checks` | Passing final pytest/static/integrity logs, original test-harness failures and app health |

The first outage miss triggered a rule fix, so independent validation after that fix remains pending. The classifier prompt was not tuned on held-out outputs. Exact labels were not changed after freezing. Case IDs are unique globally, so held-out IDs begin at TEST-051.

Every complete run includes two blank rating CSVs. No scores or approvals are attributed to either student. Use the review guide and scoring script for real independent reviews. Early development runs 001–002 have hashes but no runnable source snapshot. Later snapshots include application/engine source, prompts, dependency lock, data and approved specifications; restore them into a separate directory and use the top-level setup instructions to recreate the environment.

`summary.json`'s unsafe-delivered metric reuses the runtime guard and must not be presented as independent human assessment. Outage exact-route failures are expected for ordinary inputs, which deliberately receive SAFE_FALLBACK; crisis gate results must be read separately.

The first personal-life scope runs use `router-1.3/support-1.1`: `personal-life-001` (twenty additional fictional development dialogues), `personal-life-outage-001` (same suite with the model disabled), and `personal-scope-development-005` (the original fifty development cases). These are development/regression evidence, not a new independent held-out validation. Original run contents and prompt snapshots remain unchanged.

Subsequent prompt-refinement runs (`personal-life-002`, `personal-life-003`) and original-development reruns retain their exact versions in each config. `personal-life-3b-001` includes two cold-start classification timeouts; `personal-life-3b-002` is the completed loaded-model check with Qwen2.5 3B and `router-1.5/support-1.3`. `personal-life-outage-002` is the current scope outage check, and `personal-scope-development-007` checks the original fifty development cases with the new default. These remain development/regression results; none replaces fresh independent validation. See `docs/personal-life-scope-update.md`.
