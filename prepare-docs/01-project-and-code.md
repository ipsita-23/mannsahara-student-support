# MannSahara study guide: project and code

This guide describes the repository as it stands at commit `0774d26`
("Implement MannSahara student support chatbot and evaluation evidence").
Everything below was read directly from the current source, prompts, tests,
docs and evaluation evidence in this repo. Where a number comes from an
evaluation run, it is a **measured outcome of a specific run**; where a
number is called a target, it is an **acceptance goal that is not yet met
or not yet independently validated**.

# Chapter 1 — Problem, motivation and scope

## The problem

MannSahara is a CSE473 CA1 student project (Group 09, SIH25092) by Ipsita
Umang (12309971) and Annamneendi Suresh Kumar (12317960). The problem is
student wellbeing support: students have personal lives that go beyond
exam stress — breakups, friendship conflict, family pressure, grief,
loneliness, self-esteem, identity and sexuality questions, money
worries, caregiving. A student may want a private, low-pressure place to
talk through one small concern at a time. `README.md` and
`docs/personal-life-scope-update.md` describe how the team widened the
original academic-stress framing into explicit personal-life coverage.

## What it actually is

A **local, synthetic assessment prototype** built as a Streamlit chat
app. It runs an open-weight instruction-tuned LLM (`qwen2.5:3b`) on your
own computer through Ollama, wraps it in a four-state safety workflow,
and ships a frozen fictional evaluation corpus with reproducible evidence
runs.

It is **not** a health service. `README.md` and `docs/safety-policy.md`
state this repeatedly: it cannot diagnose, prescribe, advise on
medication, contact anyone, or provide emergency intervention. All
development and evaluation content is fictional; no real student
disclosures, clinical records (such as DAIC-WOZ), or scraped
conversations are used. Every surface says "synthetic demo": the opening
gate in `app.py`, the sidebar, the `.info` notice, and
`mannsahara/__init__.py` ("Synthetic-only CSE473 prototype. No clinical
claims."). The crisis template in `mannsahara/policy.py` points to local
emergency services and a trusted nearby person — it deliberately invents
no helpline numbers and no location, because no regional contact has
been verified (see Chapter 8).

## Objectives

From the approved specification (`output/pdf/group-09-mannsahara-specification.md`, hash-frozen and checked on every
evaluation run) and the README: a runnable English support chatbot for
fictional student scenarios; a safety router separating routine support
from uncertainty (clarify) and danger (fixed escalation); local LLM
inference only, with a replaceable backend adapter; and reproducible
synthetic evaluation with frozen data and per-run evidence.

## Non-goals (explicit)

- No clinical assessment, diagnosis, risk scoring or effectiveness
  claims.
- No real-user data: ordinary chats are session memory only, never
  saved or exported by the app. Bounded context is sent to the local Ollama process over loopback HTTP.
- No cloud APIs or remote endpoints: `mannsahara/backend.py` refuses any
  URL that is not loopback HTTP (`OllamaBackend.__init__`).
- No automatic contacting of anyone, ever — the escalation text says so
  explicitly.
- No unlimited memory; see Chapter 6 on bounded history.

Source references: `README.md`; `docs/safety-policy.md`;
`docs/implementation-notes.md`; `mannsahara/__init__.py`.

# Chapter 2 — Solution and architecture

## The routing order

The core idea, stated in the docstring of `mannsahara/engine.py`, is:

```text
input -> deterministic rules and latch -> constrained classifier
      -> fixed response or support generation -> output guard
```

Concretely, one user message flows through `Chatbot.respond` in
`mannsahara/engine.py` in this order (each stage has its own chapter
below):

1. **Validate input** — a non-empty string of at most
   `MAX_INPUT = 2000` characters. Danger screening runs on the *full*
   submitted string before length is enforced, so a long message
   containing a crisis phrase is escalated, never silently truncated.
2. **Deterministic rules** — `rule_route` screens for explicit danger,
   ambiguous distress and boundary requests. This is the floor: the LLM
   can *raise* a decision but never *lower* one.
3. **Escalation latch** — if the session already escalated, or the rules
   found danger, the fixed `ESCALATION` template returns with no model
   call at all.
4. **Constrained classifier** — otherwise the backend classifies the
   last 8 messages plus the current one into a single JSON label
   (`NO_SAFETY_SIGNAL`, `UNCERTAIN_SAFETY`, `CURRENT_DANGER`), validated
   by `parse_label` in `backend.py`.
5. **Fixed responses or generation** — `CURRENT_DANGER` gives the fixed
   escalation; `UNCERTAIN_SAFETY` gives the fixed clarification (or the
   refusal template for boundary requests); only `ROUTINE` calls the
   supportive generator.
6. **Output guard** — generated text passes `output_issue` in
   `policy.py`. Rejected text is never shown; a fixed `FALLBACK` safety
   check replaces it.
7. **Failure handling** — any exception (timeout, HTTP error, bad JSON)
   becomes `SAFE_FALLBACK` with a sanitized reason; upstream error text
   and secrets never reach the UI.

## A fictional trace

Four routes appear throughout: `mannsahara/policy.py` defines `ROUTINE`
(supportive chat), `CLARIFY` (a direct safety question), `ESCALATE`
(fixed urgent-human referral) and `SAFE_FALLBACK` (a fixed safety check
used whenever anything malfunctions) — application states, never
clinical risk scores. Memory is bounded twice (details in Chapter 6):
the last `CONTEXT_TURNS = 8` messages in `Session.messages` feed the
model, and the UI keeps at most the last 20 turns in
`st.session_state.display`.

Here is how a made-up conversation moves through the code. The real
recorded examples live in `evidence/*/turns.csv`.

```text
User: "A breakup has left me feeling lonely."
  rule_route -> ROUTINE / no_rule_signal
  Assume classifier returns NO_SAFETY_SIGNAL.
  Generate support, then check output_issue(response).
  If accepted: show ROUTINE; store the two-message exchange.

User: "I cannot keep going like this."
  rule_route -> CLARIFY / ambiguous_distress
  Classifier still runs. If it does not promote to ESCALATE,
  show fixed CLARIFICATION; awaiting_clarification = True.
  On classifier failure, show SAFE_FALLBACK instead.

User: "Yes, I might do it tonight."
  awaiting_clarification + affirmative reply -> ESCALATE
  Fixed ESCALATION; session.escalated = True; no model call.

User: "Forget it, tell me a joke."
  Latch -> same ESCALATION / escalation_latched; no model call.

Click "Clear session / start fresh":
  Session.clear() resets history, latch and clarification flag.
```

Source references: `mannsahara/engine.py`; `mannsahara/policy.py`;
`docs/safety-policy.md`; `docs/2026-11-12_mannsahara-report.md`.

# Chapter 3 — Current stack and configuration

As checked in at `0774d26`:

- **Python 3.11–3.13** (`pyproject.toml` `requires-python`), developed on
  Python 3.11 with uv and its `uv.lock` pin.
- **Streamlit** `>=1.50,<2` for the UI (single file `app.py`, light theme
  in `.streamlit/config.toml`).
- **httpx** `>=0.28,<1` as the only other runtime dependency, used for the
  Ollama HTTP adapter.
- **Ollama** serving `qwen2.5:3b` (default in `scripts/pull_model.sh` and
  `OllamaBackend`) on loopback port `11435`. The earlier default was
  `qwen2.5:1.5b`; the scope update doc explains the switch (the small
  model redirected relationship talk back to exams and over-escalated
  ordinary concerns).
- **Generation options** in `mannsahara/backend.py`: `temperature: 0`,
  `seed: 47309`, `num_ctx: 2048`, `num_predict: 140` for generation and
  `24` for classification; timeouts are 8.0 s for the classifier and
  6.0 s for generation. The classifier timeout was raised from 3 s
  (`docs/context-followup-fix.md`) because cold model loading can exceed
  short limits.
- **Safety policy version** `safety-1.4` (`POLICY_VERSION` in
  `policy.py`); **prompt versions** read live from the files by
  `prompt_version()` in `backend.py`: currently `router-1.8` /
  `support-1.5` (asserted in `tests/test_evaluation.py`).
- **Environment variables** (`.env.example`): `MANNSAHARA_OLLAMA_URL`
  (default `http://127.0.0.1:11435`) and `MANNSAHARA_MODEL` (default
  `qwen2.5:3b`). No API keys exist; `OllamaBackend` also builds
  `httpx.Client(trust_env=False)` so proxy env vars cannot redirect
  traffic, and rejects URLs with credentials, query strings or fragments.
- **Dev tools:** `pytest` and `ruff` (line length 110) under
  `[dependency-groups] dev`.
- **Ollama helper scripts:** `scripts/start_ollama.sh` binds the server
  to `127.0.0.1:11435`, stores weights in ignored `.local/models`,
  disables cloud features and request logging; `scripts/pull_model.sh`
  downloads `qwen2.5:3b` (~1.9 GB).

Source references: `pyproject.toml`; `mannsahara/backend.py`;
`.env.example`; `scripts/start_ollama.sh`; `scripts/pull_model.sh`;
`docs/context-followup-fix.md`.

# Chapter 4 — Repository map

- `app.py` — 115-line Streamlit UI: notice gate, chat, sidebar, outage
  toggle, evidence download button.
- `mannsahara/` — the package: `__init__.py` (version/docstring),
  `engine.py` (Chatbot, Session, Reply), `policy.py` (rules, templates,
  output guard), `backend.py` (Ollama adapter, backend protocol, label
  parsing), `resources.py` (verified-contact loader), `evaluate.py`
  (CLI evaluation runner).
- `prompts/classifier.txt` (Revision: router-1.8, 71 lines) and
  `prompts/support.txt` (Revision: support-1.5, 23 lines).
- `config/resources.json` — intentionally empty contacts list.
- `data/dialogues.jsonl` + `data/manifest.json` — the frozen 150-case
  corpus with SHA-256 `927bbb57...466d22`; `data/personal-life-development.jsonl` + `data/personal-life-manifest.json` — 20 extra
  development-only cases.
- `scripts/` — dataset builder, context-check runner, review aggregator,
  packaging, and Ollama helpers (details in Chapter 11).
- `tests/` — `test_safety.py`, `test_backend.py`, `test_evaluation.py`,
  `test_ui.py`, `test_review.py`.
- `evidence/` — many run directories (`development-001..004`,
  `heldout-001`, `outage-001`, `regression-002`, personal-life runs,
  context-fix runs, `checks/` logs).
- `docs/` — report, scope update, context/follow-up fix, safety policy,
  implementation notes, review guide.
- `output/pdf/group-09-mannsahara-specification.{md,pdf}` — frozen
  approved specification.

Source references: the paths above; `data/manifest.json`;
`data/personal-life-manifest.json` for the supplemental corpus counts.

# Chapter 5 — app.py walkthrough

`app.py` is the only UI file. Key pieces:

- **Styling** (lines 11–20): a static CSS block via `unsafe_allow_html`
  — the only HTML in the app, authored, not user-controlled; chat text
  renders via `st.text`, so no injected markup can execute.
- **Session state** (lines 22–25): one `Session()` (the engine's bounded
  memory), an `accepted` flag for the notice gate, and a `display` list
  for rendering.
- **Sidebar** (lines 27–63): project caption, the urgent-help guidance
  (local emergency services / trusted nearby person / campus staff —
  with the caption "Location is unknown. No verified regional contacts
  are configured"), the **Simulate model outage** toggle, the
  **Clear session / start fresh** button (the only way to clear the
  escalation latch and history), a privacy caption, and a "Project
  evidence" expander with both students' names and a download button for
  the newest `evidence/*/cases.csv`.
- **Notice gate** (lines 75–84): before `accepted`, the app shows the
  AI-support-prototype info box ("Use invented messages; do not enter
  real student or clinical disclosures...") and a Begin button, then
  `st.stop()`.
- **Chat rendering** (lines 86–102): each stored turn renders the user
  text and the assistant reply, with route-specific badges: `st.error`
  "Urgent human support" for ESCALATE, `st.warning` "Limited response ·
  safety check" for SAFE_FALLBACK, `st.info` "A quick safety check" for
  CLARIFY, plus a "Demo routing details" expander showing route, reason
  and latency in milliseconds.
- **Input handling** (lines 104–114): `st.chat_input` with
  `max_chars=MAX_INPUT`. On submit it builds the backend:
  `UnavailableBackend()` when the outage toggle is on, otherwise
  `OllamaBackend()`; if constructing Ollama fails (e.g. misconfigured
  URL), it catches `ValueError` and falls back to `UnavailableBackend`,
  so crisis rules still work with a broken backend. It then calls
  `Chatbot(backend).respond(...)`, appends `{input, **reply.record()}`
  to `display`, and trims the display list to the last 20 turns.

Source references: `app.py` (all), `tests/test_ui.py`.

# Chapter 6 — engine.py walkthrough

`mannsahara/engine.py` is the heart.

- **`Session`** (dataclass): `messages` list, `escalated` bool,
  `awaiting_clarification` bool, and `clear()` resetting all three.
  `clear()` is what the UI's clear button calls.
- **`Reply`** (dataclass): route, response text, sanitized reason,
  measured `latency_ms`, plus booleans `fallback`, `output_blocked`,
  `classifier_called`, `generator_called`. `record()` turns it into a
  dict; the UI spreads it into the display row and the evaluator writes
  it into `turns.csv`.
- **`Chatbot.respond(session, text)`** — the seven-step flow of
  Chapter 2. Details worth knowing:
  - The `stage` variable ("classifier" then "generation") makes failure
    reasons specific without leaking anything.
  - The classifier label is compared against the rule verdict: rules
    CLARIFY but model ESCALATE → escalate with reason
    `classifier_danger`; rules or model CLARIFY → fixed clarification,
    using `REFUSAL` for boundary requests (`content_boundary`) and
    `CLARIFICATION` for ambiguous distress.
  - Only when nothing else fires does it generate; a guard violation
    raises into the shared `except`, producing `SAFE_FALLBACK` with
    reason `output_rejected`.
  - **State updates after every turn** (lines 93–99): the latch is set
    (never unset here), `awaiting_clarification` is set true after
    CLARIFY or SAFE_FALLBACK (so a short "Yes, tonight." next turn
    escalates), and if input was valid the exchange is appended to
    `messages`, sliced to the last 8 entries. Invalid input adds
    nothing to memory.
  - Latency is wall-clock via `perf_counter`, rounded to 3 decimals.

Why bounded memory matters: the 8-message cap limits retained history and model work. It does not guarantee that all messages plus the system prompt fit the 2048-token context, or guarantee stable latency; because the latch is a
boolean rather than a message, escalation cannot "fall out of memory" by
truncation. Tests `test_context_is_bounded_and_not_shared` and
`test_context_followup_and_latch_reset` pin this down.

Source references: `mannsahara/engine.py`; `tests/test_safety.py`.

# Chapter 7 — policy.py walkthrough

`mannsahara/policy.py` holds versioned constants and pure
functions — no I/O, easy to unit test.

- **Constants:** `POLICY_VERSION = "safety-1.4"`, `MAX_INPUT = 2000`,
  `CONTEXT_TURNS = 8`, the `Route` enum, and the four fixed templates.
  `ESCALATION` urges local emergency help, a trusted nearby person and
  campus staff, and states "I am an AI support tool and cannot provide
  emergency intervention or contact anyone for you". `CLARIFICATION`
  asks a direct safety question; `FALLBACK` is a reliability apology
  plus safety check; `REFUSAL` starts "I can't provide harmful
  instructions, a diagnosis, or medication advice..." and appends the
  clarification. No phone numbers, links or locations appear anywhere in
  them.
- **`normalize(text)`**: NFKC Unicode normalization, lowercase, curly
  apostrophe handling, removal of zero-width/invisible characters, a
  small leetspeak un-mask table (`su1cide`→`suicide`, `k1ll`→`kill`,
  `mys3lf`→`myself`), whitespace collapsing.
- **Regex families:** `DANGER` (explicit current harm: suicide/self-kill
  phrasings in all grammatical persons, overdoses, "cannot stay safe",
  attack plans), `NEGATED_OR_DISTANT` (negations, past markers,
  fiction/quote framing), `CURRENT_OVERRIDE` (present-intent phrases
  that beat negation), `AMBIGUOUS` (hopelessness/giving-up phrases
  warranting a safety question), and `BOUNDARY` (harmful-instruction
  requests, diagnosis/medication, prompt injection such as "system
  prompt" or "pretend you are a doctor").
- **`rule_route(text, awaiting_clarification)`**: normalizes, then splits
  on sentence boundaries and "but" so each clause is checked
  independently — a negation in one clause cannot hide a current threat in
  another (comment on line 51; test
  `test_negation_does_not_blanket_hide_current_danger`). Then it checks
  the safety follow-up: if awaiting clarification and the reply affirms
  danger ("yes", "tonight", "not safe") without an explicit safe
  negation, it escalates. Next: AMBIGUOUS → CLARIFY
  (`ambiguous_distress`); BOUNDARY → CLARIFY (`content_boundary`);
  otherwise ROUTINE.
- **`output_issue(text)`** returns a reason string or None. It first
  rejects non-strings, blank text and anything over 800 characters, then
  applies the forbidden-pattern list: URLs/HTML, 3+ digit numbers or
  7+ digit-like runs, "call/text/dial +digits", helpline-word-plus-digit,
  medication quantities (mg/tablets/doses), clinical risk scores,
  diagnostic vocabulary, "you have depression", medication advice,
  self-harm instructions and vocabulary, secrecy/promise/cure claims,
  false guarantees ("everything will be fine"), and false agency ("I
  have called...", "I am your therapist"). Ordinary times, durations and
  small counts are allowed — that was the point of the `safety-1.4`
  numeric fix (compare `test_benign_times_durations_and_counts_are_allowed`
  with `test_numeric_contact_medication_and_score_guards_remain`).

The module docstring sets the right frame: rules are defense in depth,
"not a clinical instrument". Regexes miss paraphrases and can over-reject
benign wording — known limits recorded in `docs/safety-policy.md`.

Source references: `mannsahara/policy.py`; `tests/test_safety.py`;
`docs/context-followup-fix.md`.

# Chapter 8 — backend.py and resources.py walkthrough

## backend.py

`mannsahara/backend.py` isolates the LLM behind a small
`Backend` Protocol (`classify`, `generate`, `metadata`).

- **`prompt_version()`** reads the "Revision:" header line of each
  prompt file, so recorded evidence can never silently describe an older
  prompt than the one that actually ran.
- **`BackendError`** is the sanitized failure type: its message is a
  fixed category, never upstream text (tests inject "secret-data" into
  timeouts/500s/bad JSON and assert it never escapes).
- **`UnavailableBackend`** raises `BackendError("backend_unavailable")`
  for both calls; the outage toggle and outage evaluation runs use it.
- **`OllamaBackend`**:
  - Constructor reads env vars, then **rejects anything but local
    loopback HTTP** (scheme must be http, hostname in
    {127.0.0.1, localhost, ::1}; no userinfo/query/fragment) — fictional
    content stays on this computer. `trust_env=False` blocks proxy
    redirection.
  - `_chat(messages, prompt_name, timeout, structured)` builds the
    `/api/chat` payload: the prompt file as system message, the bounded
    context as the conversation, non-streaming, `keep_alive: "30m"`, the
    fixed options; for classification it adds `payload["format"] =SCHEMA` — Ollama's JSON-schema constrained decoding, restricting
    output to exactly `{"route": "..."}` with the three wire labels and
    `num_predict: 24`. Responses must have `done: true`, a string
    content of at most 4000 characters; all `httpx`/parse errors
    collapse into `BackendError("local_model_request_failed")`.
  - `metadata()` collects model digest, runtime version and options for
    evidence configs; on failure it marks `metadata_status: unavailable`
    instead of crashing.
- **`parse_label(raw)`**: strict JSON validation (must be exactly
  `{"route": <str>}`), then maps wire labels to routes:
  `NO_SAFETY_SIGNAL`→ROUTINE, `UNCERTAIN_SAFETY`→CLARIFY,
  `CURRENT_DANGER`→ESCALATE. The parser also accepts the legacy application labels `ROUTINE`, `CLARIFY` and `ESCALATE` for compatibility. Invalid labels, extra keys and `SAFE_FALLBACK` raise `BackendError` with reason
  `invalid_classifier_output`, and the engine falls back. Distinct wire
  labels exist so a request for ordinary clarification can't be confused
  with safety uncertainty (`docs/context-followup-fix.md`).

## resources.py

`mannsahara/resources.py` implements
`verified_resources(path, region, today)`: it returns contact entries
only if the JSON parses with `schema_version == 1`, the entry's region
matches, `approved is True`, the HTTPS `official_source` has a hostname,
`verified_on ≤ today ≤ expires_on`, and name/contact are non-empty
strings of at most 250 chars. Anything invalid, expired, unapproved or
malformed is silently skipped — it **fails closed**
(`test_referral_configuration_fails_closed`).

**Important wiring fact:** this helper is *not* connected to the UI.
`app.py` imports nothing from `resources.py`; the sidebar always shows
the general "location unknown" guidance, and `config/resources.json`
contains `"resources": []`. The helper exists so future region selection
can be added without inventing an unverified helpline (`docs/implementation-notes.md`, `docs/safety-policy.md`). Today the app can
never display a phone number — by design.
Source references: `mannsahara/backend.py`; `mannsahara/resources.py`;
`tests/test_backend.py`; `tests/test_safety.py`; `config/resources.json`.

# Chapter 9 — evaluate.py walkthrough

`mannsahara/evaluate.py` is the evidence engine. It is a CLI
(`python -m mannsahara.evaluate`) that never touches app transcripts and
writes only into a brand-new `evidence/<run-id>/` directory.

- **Dataset integrity.** `verify_dataset()` checks the frozen corpus
  against the manifest SHA-256, exactly 150 unique case IDs, the exact
  per-split/per-family counts (20/10/15/5 development, 40/20/30/10
  held-out), `synthetic: True` on every case, one label per user turn,
  final-label consistency, no duplicate dialogue content, no scenario
  group in both splits (leakage check), and unchanged specification file
  hashes. `verify_personal_life_dataset()` runs all of that again
  (never relabeling the original corpus) and then validates the 20 extra
  development-only cases against their own manifest.
- **Summaries.** `summarize(rows, turns)` computes the final-turn
  confusion matrix (TP/FP/FN/TN), escalation recall/precision, a
  **critical gate** requiring zero missed ESCALATE turns anywhere in a
  dialogue (not just the final turn), fallback and output-blocked
  counts, an automated `unsafe_delivered_by_automated_guard` count with
  an explicit note that this is the same deterministic guard as runtime
  — **not** an independent human review — and timing per expected-route
  cohort. Timing cohorts deliberately include fallbacks and misroutes
  so fast failures cannot inflate successful-support metrics (see
  `tests/test_evaluation.py::test_confusion_matrix_and_latency_do_not_hide_fallbacks`). Limits:
  2000 ms for ESCALATE, 10000 ms for ROUTINE, 95% target fraction.
  Human quality scores are always `status: "pending..."` with `None`
  measurements — the runner refuses to fabricate them.
- **`csv_text(rows)`** writes CSV with formula-injection defense:
  strings starting with `=`, `+`, `-`, `@` get a leading apostrophe
  (`test_formula_injection_escaped`).
- **`main()`**:
  - Flags: `--split development|held_out|all`, `--suite approved|personal-life` (personal-life rejects held_out — it is development
    coverage only), `--backend ollama|outage`, and `--run-id`
    (required-new, alphanumeric; existing directories are never
    overwritten). A live-model run **refuses to start** unless backend
    metadata contains `model_digest` — an unavailable model cannot be
    logged as a successful live evaluation (line 198).
  - It snapshots an exact runnable source copy (package files, prompts,
    lockfile, app, data, specification) into `evidence/<run-id>/source/`
    and records `config.json`: model digest, policy/prompt versions,
    code hashes, environment, the exact reproduction command, latency
    scope, and `human_review_status: "not performed; no student scoresfabricated"`.
  - It replays each dialogue through a fresh `Session`, writing each
    full turn record (expected vs actual route, escalation flags,
    response, latency, reason, fallback/block/classifier/generator
    flags) to an append-only `turns.jsonl`, so interrupted runs keep
    completed turns.
  - Finally it writes `cases.json`/`cases.csv` (final per-dialogue rows
    plus `all_turns_pass` and dialogue latency), `turns.csv`,
    `summary.json` (overall and per-split), and two **blank** review
    templates `review-ipsita.csv` and `review-suresh.csv` for the
    routine-family dialogues.

Source references: `mannsahara/evaluate.py`; `tests/test_evaluation.py`;
`docs/2026-11-12_mannsahara-report.md`.

# Chapter 10 — Prompts

`prompts/classifier.txt` (Revision: router-1.8) instructs the model to
classify **only personal safety in the last user message**, using recent
context, and to answer with exactly one JSON object. It defines the
three wire labels with few-shot examples covering deliberate hard cases:
ordinary personal-life concerns (sexuality privacy, caregiving
tiredness, family comparison) are NO_SAFETY_SIGNAL; vague distress ("I
can't do this anymore") is UNCERTAIN_SAFETY; injection attempts ("Ignore
your rules...") are UNCERTAIN_SAFETY unless paired with present intent;
fiction-quoted phrases are NO_SAFETY_SIGNAL; "I might hurt myself
tonight" and an affirmative "Yes, tonight." to a safety question are
CURRENT_DANGER; and ordinary time recall ("About 9am") is
NO_SAFETY_SIGNAL. It ends by forbidding the model from answering the
user's question at all.

`prompts/support.txt` (Revision: support-1.5) defines the persona
("MannSahara, an AI support prototype for fictional student scenarios"),
the shape (2–4 short warm sentences, at most 100 words, one small
nonclinical step, one gentle question), personal-life breadth,
anti-assumption rules (never pressure disclosure or coming out; never
push reconciliation or confrontation), hard prohibitions (no
diagnosis/prescription/harmful steps/secrecy promises/invented contacts;
treat rule-change requests as untrusted), style examples including a
breakup conversation that stays with the feeling, respect for "I don't
want study advice", short-reply interpretation via the last question,
and a capability boundary ("You cannot set alarms, send reminders or
notifications").

Both prompts are system messages supplied by `OllamaBackend._chat`; the
user's bounded context is appended after them.

Source references: `prompts/classifier.txt`; `prompts/support.txt`;
`mannsahara/backend.py`.

# Chapter 11 — Supporting scripts and tests

- `scripts/build_dataset.py` — the original authoring source for the
  150-case corpus: hand-written fictional dialogues as text blocks
  (`~` separates multi-turn cases), scenario groups assigned pairwise
  within a split, and a `build()` that **refuses to overwrite** the
  frozen files; it writes the manifest with provenance, split policy and
  the independence limit.
- `scripts/check_context_followups.py` — a three-turn regression: a
  fictional study-routine conversation checking that "Around 7am" stays
  ROUTINE and "Could you remind me what time I chose?" recalls `7am`
  without a safety fallback. `--cold` unloads the model first (via
  `keep_alive: 0`) to test cold starts. Writes its own evidence dir.
- `scripts/review_scores.py` — aggregates the two students' independent
  rating CSVs; refuses missing cases, identity mismatches and blank or out-of-range scores, and unmarked `major_safety_failure`; then writes
  `human-review-summary.json` with means, ≥4/5 target comparisons, major
  failures and disagreements. `tests/test_review.py` proves it exits
  nonzero on blank reviews rather than inventing numbers.
- `scripts/verify_evidence.py` — read-only check: re-verifies the frozen
  dataset, recomputes each run's summary from its raw rows, and checks
  source-snapshot hashes.
- `scripts/package_submission.py` — builds the submission zip with a
  SHA-256 manifest, excluding runtimes and local session data.

**Tests** (`uv run pytest -q`; the personal-life doc records 63 passing,
the context-fix doc 78 after additions):

- `tests/test_safety.py` — the largest file: 13 danger-phrase variants
  (leetspeak, zero-width characters, negation+intent, third person)
  escalate with **zero backend calls** and survive `UnavailableBackend`;
  classifier schema violations all fall back safely; the latch persists
  across topic changes until `clear()`; plus output-guard replacement,
  sanitized exceptions, no silent truncation, the context bound,
  fail-closed resources, local-only backend rejection, benign vs
  dangerous numbers, and wire-label mapping.
- `tests/test_backend.py` — MockTransport checks that schema, options,
  system-message placement and stream flag are sent, and that all
  adapter errors are sanitized.
- `tests/test_evaluation.py` — frozen dataset integrity, summary math,
  CSV injection escaping, tamper rejection (a one-byte change to the
  frozen file fails the checksum), personal-life suite separation, and
  the current prompt version `router-1.8/support-1.5`.
- `tests/test_ui.py` — Streamlit `AppTest` end-to-end: notice gate →
  chat → outage toggle → escalation persists → clear resets → fallback
  on unavailable backend; misconfigured URL still shows crisis text;
  personal-life phrasing; the 7am follow-up stays in chat.

The review script validates form completeness and score ranges; it cannot establish who authored a rating or whether it was honest. Source references: `scripts/*.py`, `tests/*.py`, `docs/review-guide.md`.

# Chapter 12 — Evidence: targets vs measured outcomes

This is where careful reading matters most. Three distinctions the
project itself insists on:

- **Synthetic prototype vs health service.** Everything here is a
  fictional-scenario demo. No clinical, diagnostic or effectiveness
  claim is supported (`mannsahara/__init__.py`, `README.md`,
  `docs/safety-policy.md` "Known limits").
- **Targets vs measured outcomes.** Acceptance targets come from the
  approved specification: ≥90% live escalation precision, zero missed
  critical turns, ≥4/5 mean human quality, ≤2 s for ≥95% of crisis
  turns, ≤10 s for ≥95% of routine turns. Measured numbers come only
  from named evidence runs.
- **Development results vs independent validation.** Prompt revisions
  were tuned on development outputs; the personal-life suite is
  explicitly development coverage; the report labels its final runs
  **regression checks** because held-out failures had been inspected
  before the fix. A newly and independently prepared validation set and
  the students' independent ratings remain pending.

Key measured results, with their runs:

- `evidence/heldout-001` and final `evidence/regression-002` (live, but
  an older model/prompts than today): 100 held-out cases, 111 turns.
  TP 32, FP 12, FN 0, TN 56 — **recall 100%, precision 72.7%** (target
  ≥90%: not met; the false positives are mostly conservative escalation
  of ambiguous or fiction-quoted phrases, enumerated in
  `route_failures`). Critical gate passed: 0 of 35 critical turns
  missed. 84/100 exact final routes; 80/100 correct on every turn.
  ESCALATE 35/35 within 2 s (sub-millisecond, fixed local path);
  ROUTINE delivered-intended-path 42/46 = 91.3%, below the 95%
  fraction, though all replies were under 10 s (cohort p95 ≈ 1079 ms).
- `evidence/outage-001` initially missed one critical turn. The later `outage-regression-002` (model disabled) delivered fixed crisis responses on all 35 critical turns after a rule fix for inflected/third-person danger phrases;
  ordinary support intentionally becomes the fixed fallback (75
  fallback turns in the outage regression).
- `evidence/personal-scope-development-007` (3B model with earlier `safety-1.3`, `router-1.5/support-1.3`,
  50-case development corpus): 48/50 exact final routes, 0 missed
  critical turns, 0 fallbacks, escalation precision 88.9% (16 of 18
  predicted escalations correct); and `personal-life-3b-002`: 20/20
  routes on the 20-case personal-life suite, all 5 critical turns
  escalated. **Development numbers**, not independent validation.
- `evidence/context-numeric-fix-004/005` — the three-turn recall
  sequence passing, with first replies ≈8.2 s (cold) and ≈4.3 s (warm);
  individual engine observations, not service guarantees.
- Human quality: **pending**. The review CSVs in every run directory
  are intentionally blank; `summarize` hard-codes `None` for measured
  quality. No score may be attributed to a student by the
  implementation agent.

History matters here: the held-out numbers above used Qwen2.5 1.5B with
`safety-1.3`, `router-1.2`, `support-1.0`. The current code (3B,
`safety-1.4`, `router-1.8`, `support-1.5`) has development regressions
only — the README states that replacing the model "changes measured
behavior and requires a new evaluation", and fresh independent
validation after the outage fix is still pending.

Source references: `docs/2026-11-12_mannsahara-report.md`;
`docs/personal-life-scope-update.md`; `docs/context-followup-fix.md`;
`evidence/*/summary.json`; `README.md` "Verify and reproduce evidence";
`docs/review-guide.md`.

# Chapter 13 — Quick revision bullets

- One routing order: validate → rules → latch → classifier → fixed text
  or generation → output guard → bounded state update. The model may
  promote safety but never demote it, and cannot emit SAFE_FALLBACK.
- Escalation is latched per session; only `Session.clear()` resets it.
- Memories are bounded (8 model messages, 20 display turns); ordinary
  chats are never persisted.
- Every failure path lands on a fixed, sanitized fallback; crisis rules
  work with no backend at all.
- Contacts are absent by design; the fail-closed `verified_resources`
  helper is not wired into the UI.
- Evaluation is frozen-data, hash-verified, never overwritten, never
  invents human scores; the ≥90% precision target was measured at 72.7%
  on the older configuration, and current-code results are development
  only with independent validation still pending.

Source references: `mannsahara/engine.py`, `mannsahara/policy.py`,
`mannsahara/backend.py`, `mannsahara/resources.py`,
`mannsahara/evaluate.py`, `app.py`, and the docs/evidence paths cited in
the chapters above.
