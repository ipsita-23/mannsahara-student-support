# Personal-life support update

A later [context/follow-up fix](context-followup-fix.md) updates the numeric guard, classifier labels and prompt versions. Results below retain their original versions.

The assignment targets higher-education students; it does not restrict their concerns to academic stress. The demo now explicitly supports relationships and breakups, friendships, family expectations, grief, loneliness, self-esteem and body image, identity and sexuality, money worries, caregiving and other everyday personal concerns alongside studies. The approved specification files and original 150-case dataset remain unchanged.

## What changed

The opening screen, sidebar and example messages now welcome personal concerns. The support prompt asks the model to follow the concern actually raised and respect requests to discuss feelings rather than offer study advice. It also avoids assumptions about identity, pressure to disclose sexuality, appearance-rating advice, or risky confrontation. These are prompt instructions, not guarantees about every generated response.

The default local model is now **Qwen2.5 3B Q4_K_M**, through the same Ollama backend. Testing the smaller model exposed unwanted academic redirection in a relationship follow-up and false escalation for ordinary personal concerns. The larger model handled the checked follow-up on topic. Current prompt revisions are `router-1.5/support-1.3`; the explicit safety policy remains `safety-1.3`. Crisis routing, the persistent escalation latch, output safety checks, privacy limits and synthetic-only notice remain active.

Setup uses the updated `scripts/pull_model.sh`; model download is approximately 1.9 GB. An existing installation can run that helper while Ollama is running. `MANNSAHARA_MODEL=qwen2.5:1.5b` still selects the older model, but its recorded behavior should not be confused with the new default. Runtime/model digests and actual prompt revisions are recorded in every new evaluation configuration. The evaluated 3B digest is `357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b`.

## Additional synthetic checks

`data/personal-life-development.jsonl` adds twenty original fictional development dialogues, with a separate checksum manifest: twelve routine personal concerns, three ambiguous-distress cases, four crisis dialogues and one medical-boundary request. It includes a multi-turn breakup conversation that explicitly declines exam advice, third-person danger, danger at home and a topic change after escalation. These cases were used to refine prompts; they are **development coverage, not independent held-out validation**. No human quality scores are inferred from route correctness.

The first three scope runs with the smaller model and the first 3B run are retained in `evidence/`. The first 3B run had two classifier timeouts during initial loading. Its failures are not removed from the record. Cold starts or a busy local machine can still produce a fixed safety fallback; a warm-model result is not a cold-start reliability guarantee.

The final loaded-model run, `evidence/personal-life-3b-002`, measured:

- Twenty of twenty final routes and twenty of twenty complete dialogue routes matched their development labels, across twenty-three turns.
- All five labeled critical turns received the fixed escalation template.
- No fallback or blocked generation occurred in that run. This is an automated observation, not independent human safety assessment.
- The checked breakup follow-up stayed with missing the relationship rather than recommending study goals. This was an author spot-check of a fictional output, not a student or clinical rating.

`evidence/personal-life-outage-002` separately records the same fictional suite with the model disabled. Noncritical turns intentionally return the fixed safety-check fallback; critical-turn correctness is measured separately. The final pytest log is `evidence/checks/pytest-personal-life-final.txt`: **63 passing tests**, including the opening personal-life scope text, chat context, reset, model outages and crisis behavior. Static checks and source/data integrity checks are recorded alongside it.

Reproduce with new run IDs:

```bash
uv run pytest -q
uv run python -m mannsahara.evaluate --suite personal-life --split development --run-id your-personal-life-run
uv run python -m mannsahara.evaluate --suite personal-life --split development --backend outage --run-id your-personal-life-outage
uv run python scripts/verify_evidence.py
```

The original report and results visualization describe their original model/prompt snapshots. Their held-out metrics are not measurements of this updated model. A fresh independent validation set, the two students' independent quality ratings and manual UI review remain pending. The application still accepts fictional scenarios only and makes no clinical effectiveness claim.

The original fifty-case development regression with the new default is retained in `evidence/personal-scope-development-007`: 48/50 exact final routes, 0 missed critical turns and 0 fallback turns. Its remaining route failures, if any, are enumerated in that run's summary; it is not a new held-out result.
