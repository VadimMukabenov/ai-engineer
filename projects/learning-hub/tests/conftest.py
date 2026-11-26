import json
from pathlib import Path

import pytest


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


@pytest.fixture
def course_root(tmp_path):
    root = tmp_path / "course"
    plan = {
        "schema_version": 1,
        "plan_version": "1.0.0",
        "mandatory_module_ids": ["M00", "M01"],
        "mandatory_project_ids": ["support-agent"],
        "next_learning_step": "D00",
    }
    catalog = {
        "schema_version": 1,
        "course_version": "1.0.0",
        "title": "AI Engineer",
        "skills": [{"id": "SK-PY", "title": "Python", "category": "Python"}],
        "modules": [
            {
                "id": "M00",
                "title": "Python для инженера",
                "description": "Основа",
                "prerequisites": [],
                "outcome_ids": ["O-PY"],
                "lesson_ids": ["D00"],
            },
            {
                "id": "M01",
                "title": "Direct LLM API",
                "description": "API",
                "prerequisites": ["M00"],
                "outcome_ids": ["O-API"],
                "lesson_ids": ["L00"],
            },
        ],
        "outcomes": [
            {
                "id": "O-PY",
                "module_id": "M00",
                "title": "Объяснить Python",
                "skill_ids": ["SK-PY"],
                "criterion_version": "1.0.0",
                "criteria": ["Самостоятельно объясняет"],
                "project_ids": ["support-agent"],
            },
            {
                "id": "O-API",
                "module_id": "M01",
                "title": "Вызвать API",
                "skill_ids": ["SK-PY"],
                "criterion_version": "1.0.0",
                "criteria": ["Проверяет ответ"],
                "project_ids": ["support-agent"],
            },
        ],
        "lessons": [
            {
                "id": "D00",
                "module_id": "M00",
                "title": "Диагностика",
                "kind": "diagnostic",
                "state": "ready",
                "material_path": "materials/D00.md",
                "outcome_ids": ["O-PY"],
            },
            {
                "id": "L00",
                "module_id": "M01",
                "title": "API",
                "kind": "lesson",
                "state": "planned",
                "material_path": None,
                "outcome_ids": ["O-API"],
            },
        ],
    }
    write_json(root / "governance/plan.json", plan)
    write_json(root / "projects/learning-hub/course/catalog.json", catalog)
    write_json(
        root / "projects/support-agent/passport.json",
        {
            "id": "support-agent",
            "title": "Поддержка",
            "summary": "Agent",
            "user": "Оператор",
            "workflow": ["Вопрос"],
            "data": "Synthetic",
            "baseline": "Manual",
            "unique_outcomes": ["Идемпотентность"],
            "skill_ids": ["SK-PY"],
            "acceptance": ["Нет двойного возврата"],
            "demo_command": "planned",
            "implementation_status": "planned",
        },
    )
    (root / "materials").mkdir()
    (root / "materials/D00.md").write_text("# Диагностика\nОбъясните свой ответ.")
    write_json(root / "governance/content-lock.json", {"schema_version": 1, "files": {}})
    return root
