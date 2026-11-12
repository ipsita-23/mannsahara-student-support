# Evidence and source reference appendix

## What this guide verifies

This guide explains source commit `0774d26` from `origin/main`. It adds study material only. Source inspection establishes implementation details; existing evaluation artifacts establish observations for their recorded version and corpus. Neither establishes effectiveness for real students. No new live-model evaluation or human quality rating was performed while creating this guide.

## Current development observations

The run `evidence/context-fix-personal-life-001` uses the revised context/numeric handling. Its `config.json` records the model, prompt versions and source hashes; its `summary.json` reports 20 dialogues and 23 turns, 20/20 final-route matches, and 20/20 dialogues matching on every turn. The final-turn confusion matrix is TP=4, FP=0, FN=0, TN=16. All five expected-critical turns received the escalation response. No fallback or output block occurred in that run. These are observations on a small development suite used during refinement.

The companion `evidence/context-fix-outage-001` also delivered the fixed referral on all five critical turns, while producing 18 fallback turns. Only 4/20 final routes and 3/20 complete dialogues matched their ordinary expected labels. All 13 expected-routine turns failed to deliver routine support. Its final-turn escalation precision and recall are still both 100%: this demonstrates why escalation metrics alone do not measure overall chatbot usefulness. A fast fallback is not successful routine support.

The earlier `evidence/regression-002` run belongs to the older 1.5B model and older prompts. Its final-turn matrix is TP=32, FP=12, FN=0, TN=56, giving precision 32/(32+12)=72.7% and recall 32/(32+0)=100%. It matched 84/100 final routes and 80/100 complete dialogues. Those historical figures must not be presented as current 3B-model held-out results. Conversely, 20/20 current development matches must not be presented as proof of independent held-out performance.

The historical specification targets include at least 90% escalation precision, zero missed critical turns, mean human ratings of at least 4/5 per quality dimension, and intended-path timing thresholds. Current independent validation and both students' quality ratings remain pending. After inspection and repair of a held-out critical miss, rerunning the same corpus is a regression check; a separately prepared validation set is still needed.

## Evidence to explanation to code path

- E1: `mannsahara/engine.py`, `policy.py` and `tests/test_safety.py`. Finding: explicit rule danger and a latched escalation are handled before model calls. Path: input -> rule/latch -> fixed escalation -> session latch. Reproduce the deterministic assertions with `pytest tests/test_safety.py` using the documented application environment.
- E2: `mannsahara/backend.py`, both prompt files and `docs/context-followup-fix.md`. Finding: the current classifier has safety-specific wire labels and an eight-second request timeout; routine generation has a six-second timeout. Path: bounded context -> schema-constrained local classification -> parsed application route -> optional support generation.
- E3: the two current development run directories named above. Finding: critical-turn referral survived the recorded outage, but ordinary generative support did not. Path: explicit rules bypass the backend; other attempted model calls raise and produce the fixed fallback. Reproduce using a new run ID with the same model digest and source snapshot; exact timings and generated wording may differ.
- E4: `app.py` and `tests/test_ui.py`. Finding: the UI has an opening fictional-use gate, outage control, bounded display history and explicit reset. Path: accept -> input -> engine -> stored display -> rerun. AppTest checks widgets and state; it is not a manual browser or accessibility review.
- E5: `data/manifest.json`, `data/personal-life-manifest.json` and `verify_dataset()` / `verify_personal_life_dataset()`. Finding: corpus and specification digests are checked. Path: load manifest -> hash files -> validate counts/labels/groups -> select split. Checksums detect changes; they do not establish label quality or semantic independence.

## Recommended reading order in the repository

1. `README.md`: purpose, setup, operating limits and evidence commands. For the classifier timeout, prefer current `backend.py`; the README troubleshooting paragraph still mentions the older three-second value.
2. `app.py`: notice gate, controls, rendering and in-memory state.
3. `mannsahara/engine.py`: `Session`, `Reply` and `Chatbot.respond()`.
4. `mannsahara/policy.py`: route definitions, fixed text, normalization, rules and generated-output guard.
5. `mannsahara/backend.py`: adapter protocol, local endpoint validation, request schema, failure handling, metadata and label parser.
6. `prompts/classifier.txt` and `prompts/support.txt`: current first-line revisions and model instructions.
7. `mannsahara/evaluate.py`: integrity checks, scoring and append-only run artifacts.
8. `tests/test_safety.py`, `test_backend.py`, `test_evaluation.py`, `test_ui.py` and `test_review.py`: executable examples and failure paths.
9. `docs/context-followup-fix.md`, then `docs/personal-life-scope-update.md`: chronology and version differences.
10. `docs/2026-11-12_mannsahara-report.md` and the matching evidence run configurations: historical metrics and their limits.
11. `docs/review-guide.md`: independent scoring and the manual demo checklist.
12. `output/pdf/group-09-mannsahara-specification.md`: preserved requirements and acceptance targets, rather than assumed achievements.

## Useful supporting scripts

`scripts/verify_evidence.py` checks recorded source snapshots/hashes and consistency of retained evidence. `scripts/check_context_followups.py` exercises an invented multi-turn time-planning conversation; its optional cold flag unloads the chosen model. `scripts/review_scores.py` requires complete human reviews rather than fabricating ratings. `scripts/package_submission.py` builds submission archives. `scripts/build_dataset.py` is the original fictional-corpus authoring source and refuses to overwrite the frozen originals. Read their argument parsers before running them; these utilities may write outside this documentation folder when used for application work.

## Document verification

The accompanying `verification.md` records checks performed for this documentation PR. PDF text extraction checks chapter coverage and page count; rendered pages are reviewed for readable type, margins, headers, code blocks and contents. The application test suite is run without a live LLM, and the application source remains unchanged. This confirms the documentation build and existing deterministic tests, not a new model evaluation.
