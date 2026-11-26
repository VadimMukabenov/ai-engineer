from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .catalog import load_catalog, project_passports, validate_repository
from .files import read_json
from .records import read_records


def build_progress(root: Path) -> dict:
    catalog = load_catalog(root)
    plan = read_json(root / "governance/plan.json")
    errors = validate_repository(root)
    attempts, assessments, _ = read_records(root)
    outcomes = {o["id"]: o for o in catalog["outcomes"]}
    latest = {}
    for a in sorted(assessments, key=lambda x: x.recorded_at):
        outcome = outcomes.get(a.outcome_id)
        if (
            a.course_version == catalog["course_version"]
            and outcome
            and a.criterion_version == outcome["criterion_version"]
        ):
            latest[a.outcome_id] = a
    mastered = set()
    if not errors:
        mastered = {
            oid
            for oid, a in latest.items()
            if oid in outcomes
            and a.decision == "passed"
            and a.criterion_version == outcomes[oid]["criterion_version"]
        }
    modules = []
    for m in catalog["modules"]:
        done, total = len(mastered.intersection(m["outcome_ids"])), len(m["outcome_ids"])
        modules.append(
            {
                **m,
                "mastered": done,
                "total": total,
                "percent": round(100 * done / total),
                "attempted": any(
                    a.course_version == catalog["course_version"] and a.lesson_id in m["lesson_ids"]
                    for a in attempts
                ),
            }
        )
    return {
        "course_version": catalog["course_version"],
        "plan_version": plan["plan_version"],
        "checked_at": datetime.now(ZoneInfo("Europe/Moscow")).isoformat(),
        "mastered_outcomes": len(mastered),
        "total_outcomes": len(outcomes),
        "percent": round(100 * len(mastered) / len(outcomes)),
        "attempt_count": len(attempts),
        "modules": modules,
        "projects": project_passports(root),
        "ready_projects": 0,
        "next_lesson_id": plan["next_learning_step"],
        "mastered_ids": sorted(mastered),
        "integrity": {"valid": not errors, "errors": errors},
        "limitations": [
            "Проверки структуры не доказывают знания",
            "Готовность demo не выводится из паспорта",
        ],
    }
