# MannSahara · Student mental health support

CSE473 CA1 · Group 9 · SIH25092. Ipsita Umang (12309971) and Annamneendi Suresh Kumar (12317960).

Support covers students’ personal lives as well as academics: relationships and breakups, friendship conflict, family pressure, grief, loneliness, self-esteem, identity, sexuality, money worries and caregiving. A concern does not need an academic connection.

A runnable English support chatbot with a separate safety router, fixed crisis referrals, local LLM support, and reproducible synthetic evaluation. **Use invented scenarios only.** It cannot diagnose, prescribe, provide emergency intervention or contact anyone. No clinical datasets, scraped conversations or real student disclosures are used. This is a local assessment prototype, not a health service.

## Run the demo

Requires Python 3.11–3.13, [uv](https://docs.astral.sh/uv/), and [Ollama](https://ollama.com/download). The current setup uses Python 3.11, Ollama 0.40.16 and `qwen2.5:3b` (approximately 1.9 GB model download). Allow about 4 GB for runtime, model and Python dependencies. Installation/model pull need internet; inference stays on loopback. The checked-in `uv.lock` pins Python dependencies.

```bash
uv sync --frozen
bash scripts/start_ollama.sh
```

Leave that terminal running. In another terminal:

```bash
bash scripts/pull_model.sh
uv run streamlit run app.py
```

Open the Streamlit URL printed in the terminal (normally `http://127.0.0.1:8501`). Read the scope notice and choose **Begin fictional conversation**. The sidebar includes clear-session and model-outage controls. Stop each server with Ctrl+C when finished.

The helper scripts use a project-local `.local/ollama` if present, otherwise your installed `ollama`. They bind the model server to `127.0.0.1:11435`, store model files in ignored `.local/models`, and disable Ollama cloud features. This separate port avoids changing another Ollama instance. Runtime binaries and model weights are not committed. Do not expose the demo or Ollama publicly.

For a different **local** Ollama model/port, set these environment variables in the app/evaluation terminal:

```bash
export MANNSAHARA_OLLAMA_URL=http://127.0.0.1:11435
export MANNSAHARA_MODEL=qwen2.5:3b
```

`.env.example` documents settings; no `.env` loader or API credentials are needed. Replacing the model changes measured behavior and requires a new evaluation. The adapter permits only local HTTP endpoints. Prompts, inference options, timeouts and model digest are recorded per run. The implementation uses [Ollama's chat API](https://docs.ollama.com/api/chat), including JSON-schema constrained classification.

## Verify and reproduce evidence

```bash
uv run pytest -q
uv run ruff check .
uv run python scripts/verify_evidence.py
uv run python -m mannsahara.evaluate --suite personal-life --split development --run-id my-personal-life-run
uv run python -m mannsahara.evaluate --split development --run-id my-development-run
uv run python -m mannsahara.evaluate --split held_out --run-id my-heldout-run
uv run python -m mannsahara.evaluate --split held_out --backend outage --run-id my-outage-run
```

Every run ID must be new. Existing evidence is never overwritten. A stopped run may have partial `turns.jsonl`; only runs with `summary.json` are complete. A live-model run refuses to start without model metadata. No per-run warm-up is performed. A synthetic hello preflight loaded the model before the recorded runs, so timings are warm or mixed, not cold-start guarantees. Compare model digests and code/prompt hashes to reproduce a specific run; floating model tags can change. Local hardware/load and runtime kernels may affect timings or outputs even with fixed seed and temperature zero.

The 150 dialogues are frozen in `data/dialogues.jsonl` with a SHA-256 manifest. There are 50 development and 100 held-out cases in the specified category proportions. `scripts/build_dataset.py` is the original authoring source and refuses to overwrite frozen files. Specific scenario groups are split-disjoint. One agent authored cases/labels; independent student label review is pending and wording patterns limit diversity. The runner checks dataset integrity and the preserved specification hashes.

Each evidence directory contains:

- `config.json`: exact model digest/runtime, seed/options, prompt and source hashes, environment and reproduction command.
- `cases.csv` / `cases.json`: final per-dialogue expected/actual route, response, pass/fail, escalation flags, timing and reviewer notes.
- `turns.csv` / append-only `turns.jsonl`: every turn, including critical intermediate turns, fallbacks and blocked-output flags.
- `summary.json`: confusion matrix, recall/precision, all critical misses, exact route failures, fallbacks, guard flags and expected-cohort timing.
- Separate blank `review-ipsita.csv` and `review-suresh.csv`: independent student scores, never fabricated by the agent.

**Validation limits:** the earlier model/prompt regression measured 72.7% precision (target ≥90%); this is not a measurement of the revised app. Fresh independent validation after the outage fix and both students’ quality ratings remain pending. Those historical metrics use the earlier prompts; see the [personal-life scope update](docs/personal-life-scope-update.md) for current prompt versions and additional development checks. The held-out measured results and limitations are in [the short report](docs/2026-11-12_mannsahara-report.md). The ≥90% escalation precision, zero critical misses, ≥4/5 human quality and latency thresholds are **acceptance targets**, not assumed results. Automated unsafe-output flags are not an independent safety review. [Complete the review and demo checklist](docs/review-guide.md) before claiming human-rated quality.

The [context/follow-up fix](docs/context-followup-fix.md) documents current numeric filtering, safety-specific classifier labels, timeout settings and executable short-reply/recall checks.

## How safety and privacy work

`mannsahara/engine.py` validates input, applies explicit safety rules, validates a constrained classifier label, selects a fixed response or calls the routine-support generator, then checks generated text. Explicit danger and latched escalation bypass all model calls. Classification/generation failures produce a conservative fixed safety check. Escalation persists until the visible clear-session control starts a fresh session. [Read the operational policy and limitations](docs/safety-policy.md).

No ordinary chat transcripts are written to disk or downloadable. Model context uses the last eight messages; the UI displays at most twenty turns. Each browser session has separate in-memory state. The app does not cache conversations, use a database, load external fonts, or send inference requests to cloud APIs. Evaluation exports only the fixed fictional corpus. Local runtime infrastructure may emit technical logs; request logging is disabled by the start script. Do not enter private data into this prototype.

No regional contact has been independently verified. `config/resources.json` intentionally contains no numbers; the app gives general local emergency/campus guidance and never assumes location. Its resource-validation helper fails closed on invalid/expired entries. Adding contacts and region selection needs actual source verification and another validation run.

## Troubleshoot

If routine chat shows **Limited response · safety check**, confirm the server is running on port 11435, the model pull completed, and **Simulate model outage** is off. Cold loading or a busy machine may exceed the classifier's three-second or generator's six-second read timeout. Known crisis rules still work during an outage. The UI intentionally does not show raw exception details.

If `uv sync --frozen` rejects your Python, use `uv python install 3.11` then `uv sync --frozen --python 3.11`. If port 11435 is busy, choose a free local port in both the server's `OLLAMA_HOST` and the app's `MANNSAHARA_OLLAMA_URL`; the supplied script sets the default explicitly. If dataset checks fail, restore the frozen files; do not silently regenerate them. See the report for remaining assessment/review limitations.

## Approved source artifacts

The [editable specification](output/pdf/group-09-mannsahara-specification.md) and [PDF specification](output/pdf/group-09-mannsahara-specification.pdf) are preserved unchanged. The original assignment's page 3 row 9 supplies the title, membership, synthetic-only requirement and core deliverables. Architecture, case counts and acceptance targets come from the approved project specification.
