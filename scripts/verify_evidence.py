"""Read-only verification of frozen data, run source snapshots and summary counts."""

import json

from mannsahara.evaluate import ROOT, sha, summarize, verify_dataset


def main():
    verify_dataset()
    runs = 0
    for path in sorted((ROOT / "evidence").glob("*/summary.json")):
        directory = path.parent
        config = json.loads((directory / "config.json").read_text())
        rows = json.loads((directory / "cases.json").read_text())
        turns = [json.loads(line) for line in (directory / "turns.jsonl").read_text().splitlines()]
        summary = json.loads(path.read_text())
        computed = summarize(rows, turns)
        assert all(summary[key] == value for key, value in computed.items()), directory
        for name, expected_hash in config["code_hashes"].items():
            snapshot = directory / "source" / name
            if snapshot.exists():
                assert sha(snapshot) == expected_hash, snapshot
        if (directory / "source").exists():
            assert all((directory / "source" / name).exists() for name in config["code_hashes"]), directory
        print(f"Verified {directory.name}: {len(rows)} cases, {len(turns)} turns")
        runs += 1
    assert runs > 0
    print(f"Verified {runs} complete runs and unchanged approved specifications.")


if __name__ == "__main__":
    main()
