"""Curriculum integrity independent of model judgments."""

from hashlib import sha256
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .files import read_json, safe_path


class Row(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[A-Za-z0-9._-]+$")
    title: str = Field(min_length=1)


class Skill(Row):
    category: str


class Module(Row):
    description: str
    prerequisites: list[str]
    outcome_ids: list[str] = Field(min_length=1)
    lesson_ids: list[str]


class Outcome(Row):
    module_id: str
    skill_ids: list[str] = Field(min_length=1)
    criterion_version: str
    criteria: list[str] = Field(min_length=1)
    project_ids: list[str]


class Lesson(Row):
    module_id: str
    kind: Literal["diagnostic", "lesson", "lab", "assessment"]
    state: Literal["ready", "planned"]
    material_path: str | None
    outcome_ids: list[str]


class Catalog(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1]
    course_version: str
    title: str
    skills: list[Skill] = Field(min_length=1)
    modules: list[Module] = Field(min_length=1)
    outcomes: list[Outcome] = Field(min_length=1)
    lessons: list[Lesson] = Field(min_length=1)


def load_catalog(root: Path) -> dict:
    return Catalog.model_validate(read_json(root / "projects/learning-hub/course/catalog.json")).model_dump()


def project_passports(root: Path) -> list[dict]:
    plan = read_json(root / "governance/plan.json")
    return [
        read_json(safe_path(root, f"projects/{pid}/passport.json")) for pid in plan["mandatory_project_ids"]
    ]


def validate_repository(root: Path) -> list[str]:
    root, errors = root.resolve(), []
    try:
        plan, c = read_json(root / "governance/plan.json"), load_catalog(root)
        if plan.get("schema_version") != 1:
            raise ValueError("Неизвестная версия схемы плана")
        groups = {key: {r["id"]: r for r in c[key]} for key in ["skills", "modules", "outcomes", "lessons"]}
        for key, index in groups.items():
            if len(index) != len(c[key]):
                errors.append(f"Повтор ID: {key}")
        for mid in plan["mandatory_module_ids"]:
            if mid not in groups["modules"]:
                errors.append(f"Отсутствует обязательный модуль {mid}")
        project_ids = set(plan["mandatory_project_ids"])
        if len(project_ids) != len(plan["mandatory_project_ids"]):
            errors.append("Повтор project ID")
        for pid in project_ids:
            p = read_json(safe_path(root, f"projects/{pid}/passport.json"))
            if p.get("id") != pid or not p.get("acceptance") or not p.get("baseline"):
                errors.append(f"Неполный паспорт {pid}")
            if not set(p.get("skill_ids", [])) <= groups["skills"].keys():
                errors.append(f"Неизвестный skill в {pid}")
            if p.get("implementation_status") not in {"planned", "in_progress", "implemented"}:
                errors.append(f"Проект {pid}: статус требует отдельной проверки demo/evidence")
        for m in c["modules"]:
            if not set(m["prerequisites"]) <= groups["modules"].keys():
                errors.append(f"Неизвестная предпосылка {m['id']}")
            actual = {o["id"] for o in c["outcomes"] if o["module_id"] == m["id"]}
            if set(m["outcome_ids"]) != actual:
                errors.append(f"Нарушен состав результатов {m['id']}")
            actual_lessons = {x["id"] for x in c["lessons"] if x["module_id"] == m["id"]}
            if set(m["lesson_ids"]) != actual_lessons:
                errors.append(f"Нарушен состав уроков {m['id']}")
        visiting, visited = set(), set()

        def visit(mid):
            if mid in visiting:
                raise ValueError(f"Цикл предпосылок: {mid}")
            if mid not in visited and mid in groups["modules"]:
                visiting.add(mid)
                for dep in groups["modules"][mid]["prerequisites"]:
                    visit(dep)
                visiting.remove(mid)
                visited.add(mid)

        for mid in groups["modules"]:
            visit(mid)
        for o in c["outcomes"]:
            if o["module_id"] not in groups["modules"] or not set(o["skill_ids"]) <= groups["skills"].keys():
                errors.append(f"Неизвестная связь результата {o['id']}")
            if not set(o["project_ids"]) <= project_ids:
                errors.append(f"Неизвестный проект результата {o['id']}")
        for lesson in c["lessons"]:
            if lesson["module_id"] not in groups["modules"]:
                errors.append(f"Неизвестный модуль {lesson['id']}")
            for oid in lesson["outcome_ids"]:
                if (
                    oid not in groups["outcomes"]
                    or groups["outcomes"][oid]["module_id"] != lesson["module_id"]
                ):
                    errors.append(f"Неверная связь урока {lesson['id']} → {oid}")
            if lesson["state"] == "ready" and not lesson["material_path"]:
                errors.append(f"Нет материала готового урока {lesson['id']}")
            if lesson["material_path"] and not safe_path(root, lesson["material_path"]).is_file():
                errors.append(f"Нет файла урока {lesson['id']}")
        if plan["next_learning_step"] not in groups["lessons"]:
            errors.append("Нет следующего учебного шага")
        from .records import record_errors

        errors.extend(record_errors(root, c))
        lock = root / "governance/content-lock.json"
        if not lock.is_file():
            errors.append("Отсутствует governance/content-lock.json")
        else:
            for name, expected in read_json(lock)["files"].items():
                path = safe_path(root, name)
                if not path.is_file() or sha256(path.read_bytes()).hexdigest() != expected:
                    errors.append(f"Изменён утверждённый контракт: {name}; нужен пересмотр")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(str(exc))
    return errors
