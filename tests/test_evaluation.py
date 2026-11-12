import pytest

from mannsahara.evaluate import csv_text, summarize, verify_dataset


def test_frozen_dataset_integrity():
    manifest, cases = verify_dataset()
    assert manifest["total"] == len(cases) == 150
    assert sum(c["split"] == "held_out" for c in cases) == 100
    assert any(len(c["messages"]) > 1 for c in cases)


def test_confusion_matrix_and_latency_do_not_hide_fallbacks():
    def row(id, expected, actual, latency=1):
        return dict(
            case_id=id,
            turn=1,
            expected_route=expected,
            actual_route=actual,
            escalation_required=expected == "ESCALATE",
            escalation_shown=actual == "ESCALATE",
            latency_ms=latency,
            fallback=actual == "SAFE_FALLBACK",
            output_blocked=False,
            unsafe_output_flag=False,
            all_turns_pass=expected == actual,
            **{"pass": expected == actual},
        )

    rows = [
        row("a", "ESCALATE", "ESCALATE"),
        row("b", "ESCALATE", "SAFE_FALLBACK"),
        row("c", "ROUTINE", "ESCALATE"),
        row("d", "ROUTINE", "ROUTINE", 11000),
    ]
    result = summarize(rows, rows)
    assert result["confusion_matrix"] == {"TP": 1, "FP": 1, "FN": 1, "TN": 1}
    assert result["escalation_recall"] == result["escalation_precision"] == 0.5
    assert not result["critical_gate_passed"]
    assert result["timing"]["ROUTINE"]["measured_fraction"] == 0
    assert result["fallback_turns"] == 1


def test_formula_injection_escaped():
    assert "'=cmd" in csv_text([{"text": "=cmd"}])
    assert "'+cmd" in csv_text([{"text": "+cmd"}])


def test_frozen_data_tamper_is_rejected(tmp_path):
    import shutil

    (tmp_path / "data").mkdir()
    for name in ["manifest.json", "dialogues.jsonl"]:
        shutil.copyfile("data/" + name, tmp_path / "data" / name)
    with (tmp_path / "data/dialogues.jsonl").open("a") as f:
        f.write("\n")
    with pytest.raises(ValueError, match="checksum mismatch"):
        verify_dataset(tmp_path)


def test_personal_life_suite_is_separate_synthetic_development_coverage():
    from mannsahara.evaluate import verify_personal_life_dataset

    manifest, cases = verify_personal_life_dataset()
    assert manifest["total"] == len(cases) == 20
    assert all(c["synthetic"] and c["split"] == "development" for c in cases)
    assert {"breakup", "family_pressure", "grief", "sexuality", "gender_identity", "caregiving"} <= {
        c["topic"] for c in cases
    }
    assert sum(c["escalation_required"] for c in cases) == 4
    assert any(len(c["messages"]) > 1 for c in cases)


def test_prompt_version_matches_current_files():
    from mannsahara.backend import prompt_version

    assert prompt_version() == "router-1.8/support-1.5"
