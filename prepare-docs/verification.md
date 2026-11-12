# Documentation verification

Verified on 12 November 2026 against application source commit `0774d26`.

- Existing application tests: **78 passed in 1.25 seconds**. Run from the isolated
  worktree using the existing application's virtual environment, with bytecode
  redirected into `prepare-docs/tmp/` and the pytest cache provider disabled.
- Ruff: `ruff check --no-cache .` passed, including both documentation utilities.
- PDF: successfully built with ReportLab; reopened and extracted with pypdf.
  **31 pages**, **24 outline entries**, **50 numbered answered viva questions**.
- Coverage checks found the problem, solution, code walkthrough, safety fallback,
  viva material, source revision and current evidence identifiers in extracted text.
- Rendered every page with PDFium. Reviewed all 31 pages in three contact sheets
  and checked the demonstration and dense viva pages at full size. Margins,
  contents, headers, footers, code blocks and typography are readable without
  visible clipping, overlap or unsupported glyphs.
- All new tracked files are under `prepare-docs/`. The application, dependency
  lockfile, original specifications, datasets and existing evidence remain unchanged.
- No new live-model evaluation, independent corpus validation, human quality rating,
  manual application browser audit or clinical validation is claimed.

## Reproduce the document checks

Follow `README.md` in this folder to install the isolated document tools, then:

```bash
prepare-docs/.venv/bin/python prepare-docs/build_pdf.py
prepare-docs/.venv/bin/python prepare-docs/inspect_pdf.py
```

The second command writes extracted text, check metadata, every rendered page and
contact sheets into ignored `prepare-docs/tmp/review/`. Inspect the latest render
after changes; text checks alone do not establish visual quality. Runtime-only
review artifacts are intentionally excluded from the PR.
