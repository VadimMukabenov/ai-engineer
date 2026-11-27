"""Durable attempts; recording an attempt never awards mastery."""

import json
import os
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from .files import read_json, safe_path

Assistance = Literal["none", "documentation", "hint", "ai_partial", "ai_solution", "unspecified"]


class Attempt(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    id: str = Field(pattern=r"^[A-Za-z0-9._-]+$")
    lesson_id: str
    course_version: str
    answer: str = Field(min_length=1, max_length=20000)
    assistance: Assistance
    kind: Literal["answer", "self_report"] = "answer"
    recorded_by: Literal["learner", "mentor"] = "learner"
    author: Literal["learner"] = "learner"
    status: Literal["submitted"] = "submitted"
    recorded_at: AwareDatetime


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class Assessment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1]
    id: str
    attempt_id: str
    attempt_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    course_version: str
    outcome_id: str
    criterion_version: str
    decision: Literal["passed", "needs_work"]
    method: Literal["independent_task", "transfer_check", "oral_defence"]
    reviewer: str = Field(min_length=1)
    rationale: str = Field(min_length=10)
    assistance: Assistance
    recorded_at: AwareDatetime
    evidence: list[Evidence] = Field(min_length=1)


def read_records(root: Path):
    groups, errors = [], []
    for kind, model in [("attempts", Attempt), ("assessments", Assessment)]:
        rows, ids = [], set()
        folder = safe_path(root, f"learning_records/{kind}")
        for path in sorted(folder.glob("*.json")):
            try:
                safe_path(root, str(path.relative_to(root)))
                row = model.model_validate(read_json(path))
                if row.id in ids or path.stem != row.id:
                    raise ValueError("Повтор ID или имя файла не соответствует ID")
                ids.add(row.id)
                rows.append(row)
            except (OSError, ValueError) as exc:
                errors.append(f"{kind}/{path.name}: {exc}")
        groups.append(rows)
    return groups[0], groups[1], errors


def record_errors(root: Path, catalog: dict) -> list[str]:
    from .catalog import Catalog

    attempts, assessments, errors = read_records(root)
    catalogs = {catalog["course_version"]: catalog}

    def catalog_for(version):
        if version not in catalogs:
            try:
                # Historical snapshots are read only; an updated active catalog cannot replace them.
                path = safe_path(root, f"projects/learning-hub/course/versions/{version}.json")
                snapshot = Catalog.model_validate(read_json(path)).model_dump()
                if snapshot["course_version"] != version:
                    raise ValueError("Версия внутри снимка не совпадает с именем")
                catalogs[version] = snapshot
            except (OSError, ValueError) as exc:
                errors.append(f"Недоступен снимок каталога версии {version}: {exc}")
                catalogs[version] = None
        return catalogs[version]

    by_id = {a.id: a for a in attempts}
    for a in attempts:
        scoped = catalog_for(a.course_version)
        if scoped and a.lesson_id not in {x["id"] for x in scoped["lessons"]}:
            errors.append(f"Попытка {a.id}: неизвестный урок")
    for a in assessments:
        attempt = by_id.get(a.attempt_id)
        if attempt is None:
            errors.append(f"Оценка {a.id}: нет попытки")
            continue
        try:
            path = safe_path(root, f"learning_records/attempts/{attempt.id}.json")
            if sha256(path.read_bytes()).hexdigest() != a.attempt_sha256:
                errors.append(f"Оценка {a.id}: hash попытки изменён")
        except (OSError, ValueError) as exc:
            errors.append(f"Оценка {a.id}: {exc}")
        if attempt.course_version != a.course_version:
            errors.append(f"Оценка {a.id}: несовместимые версии")
        if a.decision == "passed" and attempt.kind == "self_report":
            errors.append(f"Оценка {a.id}: самоотчёт не является проверкой навыка")
        scoped = catalog_for(a.course_version)
        if scoped:
            if a.outcome_id not in {x["id"] for x in scoped["outcomes"]}:
                errors.append(f"Оценка {a.id}: нет результата в версии {a.course_version}")
            lesson = next((x for x in scoped["lessons"] if x["id"] == attempt.lesson_id), None)
            if lesson and a.outcome_id not in lesson["outcome_ids"]:
                errors.append(f"Оценка {a.id}: результат не связан с уроком")
        if a.decision == "passed" and (
            attempt.assistance not in {"none", "documentation"}
            or a.assistance not in {"none", "documentation"}
        ):
            errors.append(f"Оценка {a.id}: нет независимой попытки")
        for ev in a.evidence:
            try:
                path = safe_path(root, ev.path)
                if not path.is_file() or sha256(path.read_bytes()).hexdigest() != ev.sha256:
                    raise ValueError("Нет доказательства или hash изменён")
            except (OSError, ValueError) as exc:
                errors.append(f"Оценка {a.id}: {exc}")
    return errors


def save_attempt(
    root: Path,
    lesson_id: str,
    answer: str,
    assistance: str,
    *,
    kind: str = "answer",
    recorded_by: str = "learner",
) -> dict:
    from .catalog import load_catalog

    catalog = load_catalog(root)
    lesson = next((x for x in catalog["lessons"] if x["id"] == lesson_id), None)
    if lesson is None or lesson["state"] != "ready":
        raise ValueError("Урок не найден или ещё не подготовлен")
    row = Attempt(
        id=f"attempt-{uuid4().hex}",
        lesson_id=lesson_id,
        course_version=catalog["course_version"],
        answer=answer.strip(),
        assistance=assistance,
        kind=kind,
        recorded_by=recorded_by,
        recorded_at=datetime.now(UTC),
    )
    folder = safe_path(root, "learning_records/attempts")
    folder.mkdir(parents=True, exist_ok=True)
    destination = safe_path(root, f"learning_records/attempts/{row.id}.json")
    temp = folder / f".{row.id}.tmp"
    try:
        with temp.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(row.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temp, destination)
    finally:
        temp.unlink(missing_ok=True)
    return row.model_dump(mode="json")
