import json
from hashlib import sha256

import pytest
from conftest import write_json

from learning_hub.catalog import validate_repository
from learning_hub.progress import build_progress
from learning_hub.records import save_attempt


def assessment(root, attempt, **changes):
    evidence = root / "evidence/answer.txt"
    evidence.parent.mkdir(exist_ok=True)
    evidence.write_text("Observed independent explanation and changed example")
    attempt_path = root / "learning_records/attempts" / f"{attempt['id']}.json"
    record = {
        "schema_version": 1,
        "id": "ASSESS-1",
        "attempt_id": attempt["id"],
        "attempt_sha256": sha256(attempt_path.read_bytes()).hexdigest()
        if attempt_path.exists()
        else "0" * 64,
        "course_version": "1.0.0",
        "outcome_id": "O-PY",
        "criterion_version": "1.0.0",
        "decision": "passed",
        "method": "independent_task",
        "reviewer": "mentor",
        "rationale": "Explained and applied in a new example",
        "assistance": "none",
        "recorded_at": "2026-11-26T20:00:00+00:00",
        "evidence": [{"path": "evidence/answer.txt", "sha256": sha256(evidence.read_bytes()).hexdigest()}],
    }
    record.update(changes)
    write_json(root / "learning_records/assessments/ASSESS-1.json", record)


def test_initial_progress_is_zero_and_next_is_diagnostic(course_root):
    report = build_progress(course_root)
    assert report["mastered_outcomes"] == 0
    assert report["total_outcomes"] == 2
    assert report["next_lesson_id"] == "D00"
    assert report["ready_projects"] == 0


def test_attempt_persists_without_automatic_mastery(course_root):
    row = save_attempt(course_root, "D00", "Моя попытка", "none")
    assert (course_root / "learning_records/attempts" / f"{row['id']}.json").exists()
    report = build_progress(course_root)
    assert report["attempt_count"] == 1
    assert report["mastered_outcomes"] == 0


def test_verified_independent_evidence_counts_outcome_once(course_root):
    row = save_attempt(course_root, "D00", "Моя попытка", "none")
    assessment(course_root, row)
    assert validate_repository(course_root) == []
    assert build_progress(course_root)["mastered_outcomes"] == 1
    data = json.loads((course_root / "learning_records/assessments/ASSESS-1.json").read_text())
    data["id"] = "ASSESS-2"
    write_json(course_root / "learning_records/assessments/ASSESS-2.json", data)
    assert build_progress(course_root)["mastered_outcomes"] == 1


def test_assisted_attempt_does_not_prove_independence(course_root):
    row = save_attempt(course_root, "D00", "С подсказкой", "ai_solution")
    assessment(course_root, row)
    assert validate_repository(course_root)
    assert build_progress(course_root)["mastered_outcomes"] == 0


def test_tampered_or_missing_evidence_is_not_mastery(course_root):
    row = save_attempt(course_root, "D00", "Моя попытка", "none")
    assessment(course_root, row)
    (course_root / "evidence/answer.txt").write_text("changed")
    assert validate_repository(course_root)
    assert build_progress(course_root)["mastered_outcomes"] == 0


def test_old_criterion_does_not_automatically_transfer(course_root):
    row = save_attempt(course_root, "D00", "Моя попытка", "none")
    assessment(course_root, row, criterion_version="0.9.0")
    assert build_progress(course_root)["mastered_outcomes"] == 0


def test_missing_attempt_cannot_be_graded(course_root):
    assessment(course_root, {"id": "nonexistent"})
    assert validate_repository(course_root)
    assert build_progress(course_root)["mastered_outcomes"] == 0


def test_assessment_binds_the_exact_attempt_content(course_root):
    row = save_attempt(course_root, "D00", "Original independent answer", "none")
    assessment(course_root, row)
    assert build_progress(course_root)["mastered_outcomes"] == 1
    path = course_root / "learning_records/attempts" / f"{row['id']}.json"
    changed = json.loads(path.read_text())
    changed["answer"] = "Unrelated replacement"
    write_json(path, changed)
    assert any("hash" in error for error in validate_repository(course_root))
    assert build_progress(course_root)["mastered_outcomes"] == 0


@pytest.mark.parametrize("kind", ["attempts", "assessments"])
def test_naive_timestamps_are_reported_without_crashing_progress(course_root, kind):
    row = save_attempt(course_root, "D00", "Independent answer", "none")
    assessment(course_root, row)
    original = (
        course_root
        / "learning_records"
        / kind
        / (f"{row['id']}.json" if kind == "attempts" else "ASSESS-1.json")
    )
    invalid = json.loads(original.read_text())
    invalid.update(id="NAIVE", recorded_at="2026-11-26T21:00:00")
    write_json(original.parent / "NAIVE.json", invalid)
    errors = validate_repository(course_root)
    assert any("recorded_at" in error for error in errors)
    report = build_progress(course_root)
    assert not report["integrity"]["valid"]
    assert report["mastered_outcomes"] == 0


def test_later_old_criterion_does_not_replace_current_criterion_pass(course_root):
    row = save_attempt(course_root, "D00", "Independent answer", "none")
    assessment(course_root, row)
    path = course_root / "learning_records/assessments/ASSESS-1.json"
    old = json.loads(path.read_text())
    old.update(
        id="OLD", criterion_version="0.9.0", decision="needs_work", recorded_at="2026-11-26T21:00:00+00:00"
    )
    write_json(path.parent / "OLD.json", old)
    assert validate_repository(course_root) == []
    assert build_progress(course_root)["mastered_outcomes"] == 1


def upgrade_course(root, *, archive=True):
    path = root / "projects/learning-hub/course/catalog.json"
    catalog = json.loads(path.read_text())
    if archive:
        write_json(path.parent / "versions/1.0.0.json", catalog)
    catalog["course_version"] = "2.0.0"
    catalog["lessons"][0]["id"] = "D02"
    catalog["lessons"][0]["outcome_ids"] = ["O-PY-V2"]
    catalog["outcomes"][0]["id"] = "O-PY-V2"
    catalog["modules"][0].update(lesson_ids=["D02"], outcome_ids=["O-PY-V2"])
    write_json(path, catalog)
    plan_path = root / "governance/plan.json"
    plan = json.loads(plan_path.read_text())
    plan["next_learning_step"] = "D02"
    write_json(plan_path, plan)


def test_archived_catalog_validates_history_without_transferring_mastery(course_root):
    row = save_attempt(course_root, "D00", "Historical independent answer", "none")
    assessment(course_root, row)
    upgrade_course(course_root)
    assert validate_repository(course_root) == []
    report = build_progress(course_root)
    assert report["attempt_count"] == 1
    assert report["mastered_outcomes"] == 0
    assert not report["modules"][0]["attempted"]


def test_missing_historical_snapshot_is_an_explicit_integrity_error(course_root):
    row = save_attempt(course_root, "D00", "Historical independent answer", "none")
    assessment(course_root, row)
    upgrade_course(course_root, archive=False)
    report = build_progress(course_root)
    assert not report["integrity"]["valid"]
    assert any("снимок" in error and "1.0.0" in error for error in report["integrity"]["errors"])
    assert report["mastered_outcomes"] == 0


def test_historical_links_are_checked_against_the_snapshot(course_root):
    row = save_attempt(course_root, "D00", "Historical independent answer", "none")
    assessment(course_root, row)
    path = course_root / "learning_records/assessments/ASSESS-1.json"
    bad = json.loads(path.read_text())
    bad["outcome_id"] = "O-NONEXISTENT"
    write_json(path, bad)
    upgrade_course(course_root)
    assert any("результат" in error for error in validate_repository(course_root))


def test_snapshot_version_must_match_the_requested_version(course_root):
    save_attempt(course_root, "D00", "Historical answer", "none")
    upgrade_course(course_root)
    path = course_root / "projects/learning-hub/course/versions/1.0.0.json"
    wrong = json.loads(path.read_text())
    wrong["course_version"] = "0.9.0"
    write_json(path, wrong)
    assert any("снимок" in error and "1.0.0" in error for error in validate_repository(course_root))


@pytest.mark.parametrize("target", ["attempt", "evidence"])
def test_historical_records_still_require_unchanged_provenance(course_root, target):
    row = save_attempt(course_root, "D00", "Historical independent answer", "none")
    assessment(course_root, row)
    upgrade_course(course_root)
    assert validate_repository(course_root) == []
    path = (
        course_root / "learning_records/attempts" / f"{row['id']}.json"
        if target == "attempt"
        else course_root / "evidence/answer.txt"
    )
    path.unlink()
    report = build_progress(course_root)
    assert not report["integrity"]["valid"]
    assert report["mastered_outcomes"] == 0


def test_self_report_survives_read_without_counting_as_answer_or_mastery(course_root):
    from learning_hub.records import read_records

    row = save_attempt(
        course_root,
        "D00",
        "Не смог решить без помощи",
        "unspecified",
        kind="self_report",
        recorded_by="mentor",
    )
    attempts, _, errors = read_records(course_root)
    assert not errors
    assert attempts[0].kind == "self_report"
    assert attempts[0].recorded_by == "mentor"
    assert attempts[0].answer == "Не смог решить без помощи"
    report = build_progress(course_root)
    assert report["attempt_count"] == 0
    assert report["self_report_count"] == 1
    assert report["mastered_outcomes"] == 0
    assert not report["modules"][0]["attempted"]
    assert report["modules"][0]["reported"]
    assessment(course_root, row)
    errors = validate_repository(course_root)
    assert any("самоотчёт" in error for error in errors)
    assert build_progress(course_root)["mastered_outcomes"] == 0


def test_legacy_attempt_keeps_meaning_without_rewriting(course_root):
    from learning_hub.records import read_records

    row = save_attempt(course_root, "D00", "Independent answer", "none")
    path = course_root / "learning_records/attempts" / f"{row['id']}.json"
    old = json.loads(path.read_text())
    old.pop("kind", None)
    old.pop("recorded_by", None)
    write_json(path, old)
    original = path.read_bytes()
    attempts, _, errors = read_records(course_root)
    assert not errors
    assert attempts[0].kind == "answer"
    assert attempts[0].recorded_by == "learner"
    assessment(course_root, row)
    assert build_progress(course_root)["mastered_outcomes"] == 1
    assert path.read_bytes() == original
