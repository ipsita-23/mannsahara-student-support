import subprocess
import sys


def test_review_script_does_not_invent_scores(tmp_path):
    import csv
    import json

    (tmp_path / "cases.json").write_text(json.dumps([{"case_id": "TEST-X", "scenario_family": "routine"}]))
    for name in ["ipsita", "suresh"]:
        with (tmp_path / f"review-{name}.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=[
                    "case_id",
                    "reviewer",
                    "empathy_1_to_5",
                    "relevance_1_to_5",
                    "safety_1_to_5",
                    "major_safety_failure",
                ],
            )
            writer.writeheader()
            writer.writerow({"case_id": "TEST-X", "reviewer": name})
    result = subprocess.run(
        [sys.executable, "scripts/review_scores.py", str(tmp_path)], capture_output=True, text=True
    )
    assert result.returncode != 0 and "Incomplete review" in result.stderr
    assert not (tmp_path / "human-review-summary.json").exists()
