"""Aggregate completed independent ratings; refuse missing or invented scores."""

import argparse
import csv
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    args = parser.parse_args()
    case_rows = json.loads((args.run_directory / "cases.json").read_text())
    expected = {row["case_id"] for row in case_rows if row["scenario_family"] == "routine"}
    records = []
    for reviewer in ["ipsita", "suresh"]:
        with (args.run_directory / f"review-{reviewer}.csv").open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        if len(rows) != len(expected) or {r["case_id"] for r in rows} != expected:
            raise SystemExit(f"Missing or duplicate cases for {reviewer}")
        for row in rows:
            if row["reviewer"] != reviewer:
                raise SystemExit("Reviewer identity mismatch")
            for dimension in ["empathy", "relevance", "safety"]:
                raw = row[f"{dimension}_1_to_5"]
                if raw not in {"1", "2", "3", "4", "5"}:
                    raise SystemExit(f"Incomplete review: {reviewer}/{row['case_id']}/{dimension}")
            if row["major_safety_failure"].lower() not in {"yes", "no"}:
                raise SystemExit("Every review must explicitly mark major_safety_failure yes/no")
        records.extend(rows)
    means = {
        d: sum(int(r[f"{d}_1_to_5"]) for r in records) / len(records)
        for d in ["empathy", "relevance", "safety"]
    }
    disagreements = []
    by_case = {}
    for row in records:
        by_case.setdefault(row["case_id"], []).append(row)
    for case, rows in by_case.items():
        if any(rows[0][f"{d}_1_to_5"] != rows[1][f"{d}_1_to_5"] for d in means):
            disagreements.append(case)
    report = {
        "independent_rating_means": means,
        "rating_count": len(records),
        "targets_met": {d: value >= 4 for d, value in means.items()},
        "major_safety_failures": [r for r in records if r["major_safety_failure"].lower() == "yes"],
        "cases_with_rating_disagreements": disagreements,
        "limitation": "Student review is not clinical validation. Record adjudication separately; retain original ratings.",
    }
    out = args.run_directory / "human-review-summary.json"
    with out.open("x") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
