# Project preparation guide

Open [the topic-wise PDF](mannsahara-project-guide.pdf) for the problem statement, solution,
code walkthrough, demo preparation and answered viva questions.

The guide describes application source commit `0774d26`. It is study material, not new
clinical validation. Every added file in this PR lives in `prepare-docs/`; application
code, existing specifications, datasets and evaluation evidence are unchanged.

## Editable sources

- `01-project-and-code.md`: problem, approach, architecture and code explanation.
- `02-viva-and-demo.md`: setup, demonstration, viva answers and revision material.
- `03-evidence-and-references.md`: evidence interpretation, source index and verification.
- `build_pdf.py`: creates the PDF with clickable contents, bookmarks and page numbers.

## Rebuild

From the repository root, using Python 3.11 or newer and `uv`:

```bash
uv venv --python 3.11 prepare-docs/.venv
uv pip install --python prepare-docs/.venv/bin/python -r prepare-docs/requirements.txt
prepare-docs/.venv/bin/python prepare-docs/build_pdf.py
```

The PDF tools have their own environment and do not change the application's dependency
lockfile. Rendered review pages and temporary artifacts belong in ignored `prepare-docs/tmp/`.

## Writing checks

The source code and frozen evidence take precedence over older narrative reports.
Keep model/prompt versions attached to any reported score. A development regression,
an automated output check and independent clinical validation are different claims.
Do not fill the original student review forms on anyone's behalf.
