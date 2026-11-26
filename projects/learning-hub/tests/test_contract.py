import json

import pytest

from learning_hub.catalog import validate_repository


def mutate(root, transform):
    p = root / "projects/learning-hub/course/catalog.json"
    value = json.loads(p.read_text())
    transform(value)
    p.write_text(json.dumps(value))


def test_complete_contract_is_valid(course_root):
    assert validate_repository(course_root) == []


@pytest.mark.parametrize(
    "case", ["missing_module", "unknown_skill", "cycle", "duplicate", "unsafe_path", "missing_material"]
)
def test_invalid_contract_is_rejected(course_root, case):
    def change(c):
        if case == "missing_module":
            c["modules"].pop()
        elif case == "unknown_skill":
            c["outcomes"][0]["skill_ids"] = ["SK-NONEXISTENT"]
        elif case == "cycle":
            c["modules"][0]["prerequisites"] = ["M01"]
        elif case == "duplicate":
            c["skills"].append(c["skills"][0])
        elif case == "unsafe_path":
            c["lessons"][0]["material_path"] = "../../outside.md"
        elif case == "missing_material":
            c["lessons"][0]["material_path"] = "missing.md"

    mutate(course_root, change)
    assert validate_repository(course_root), case


def test_unreferenced_outcome_cannot_disappear_from_module(course_root):
    mutate(course_root, lambda c: c["modules"][0].update(outcome_ids=[]))
    assert validate_repository(course_root)


def test_ready_lesson_cannot_reference_outcome_from_another_module(course_root):
    mutate(course_root, lambda c: c["lessons"][0].update(outcome_ids=["O-API"]))
    assert validate_repository(course_root)
