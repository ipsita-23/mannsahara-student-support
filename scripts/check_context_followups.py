"""Exercise short replies and explicit recall with fictional content against the local model."""

import argparse
import json
from pathlib import Path

from mannsahara.backend import ROOT, OllamaBackend, prompt_version
from mannsahara.engine import Chatbot, Session
from mannsahara.evaluate import sha
from mannsahara.policy import POLICY_VERSION, Route, normalize


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--cold", action="store_true", help="Unload the selected local model before testing")
    args = parser.parse_args()
    if not args.run_id or any(
        c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in args.run_id
    ):
        parser.error("Use an alphanumeric run ID with hyphens or underscores")
    out = ROOT / "evidence" / args.run_id
    out.mkdir(exist_ok=False)
    backend = OllamaBackend()
    if args.cold:
        response = backend.client.post(
            backend.url + "/api/generate", json={"model": backend.model, "keep_alive": 0}, timeout=30
        )
        response.raise_for_status()
    initial = [
        {
            "role": "user",
            "content": "I want a manageable morning study routine because I get distracted thinking about dating.",
        },
        {"role": "assistant", "content": "What time in the morning would work for a short study session?"},
    ]
    session = Session(messages=[dict(message) for message in initial])
    rows = []
    for number, message in enumerate(
        [
            "Around 7am would work.",
            "Would a short break afterwards make sense?",
            "Could you remind me what time I chose?",
        ],
        1,
    ):
        reply = Chatbot(backend).respond(session, message)
        recall_correct = None
        if number == 3:
            recall_correct = any(
                token in normalize(reply.response) for token in ["7am", "7 am", "7:00", "seven"]
            )
        rows.append(
            {
                "synthetic": True,
                "turn": number,
                "input": message,
                **reply.record(),
                "expected_route": "ROUTINE",
                "recall_correct": recall_correct,
                "pass": reply.route == Route.ROUTINE and not reply.fallback and recall_correct is not False,
            }
        )
        print(json.dumps(rows[-1]), flush=True)
    (out / "turns.json").write_text(json.dumps(rows, indent=2) + "\n")
    (out / "initial-context.json").write_text(json.dumps(initial, indent=2) + "\n")
    files = [
        *sorted((ROOT / "mannsahara").glob("*.py")),
        *sorted((ROOT / "prompts").glob("*.txt")),
        Path(__file__).resolve(),
    ]
    (out / "config.json").write_text(
        json.dumps(
            {
                "prompt_version": prompt_version(),
                "policy_version": POLICY_VERSION,
                "backend": backend.metadata(),
                "cold_start": args.cold,
                "synthetic_only": True,
                "source_hashes": {str(p.relative_to(ROOT)): sha(p) for p in files},
                "command": f"uv run python scripts/check_context_followups.py --run-id your-new-id{' --cold' if args.cold else ''}",
                "scope": "Three-turn development regression, not independent validation or a clinical assessment",
                "passed": all(row["pass"] for row in rows),
            },
            indent=2,
        )
        + "\n"
    )
    if not all(row["pass"] for row in rows):
        raise SystemExit("One or more context checks failed; see retained evidence")


if __name__ == "__main__":
    main()
