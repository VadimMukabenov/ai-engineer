import json

import pytest
from conftest import write_json

from learning_hub.market import market_report


def batch(root, **changes):
    row = {
        "id": "job-1",
        "company": "Example",
        "title": "AI Engineer",
        "url": "https://example.com/jobs/1",
        "verification": "verified",
        "checked_on": "2026-11-26",
        "remote": "fully_remote",
        "active": "confirmed",
        "hiring_eligibility": "unknown",
        "salary": {
            "currency": "USD",
            "min": 100000,
            "max": 150000,
            "period": "year",
            "basis": "gross",
            "kind": "base",
        },
        "required_skills": ["Python"],
        "preferred_skills": [],
    }
    row.update(changes)
    write_json(root / "research/market/batches/test.json", {"vacancies": [row]})
    write_json(root / "research/market/skill-aliases.json", {"SK-PY": ["Python"]})


def test_gross_and_unknown_eligibility_never_count_as_fit(course_root):
    batch(course_root)
    report = market_report(course_root)
    assert report["confirmed_salary_and_eligibility_fit"] == 0
    assert report["skill_frequency"]["SK-PY"] == 1
    assert report["matrix"][0]["outcome_ids"] == ["O-API", "O-PY"]


def test_aliases_must_reference_real_skills(course_root):
    batch(course_root)
    write_json(course_root / "research/market/skill-aliases.json", {"SK-FAKE": ["Python"]})
    with pytest.raises(ValueError):
        market_report(course_root)


def test_duplicate_source_url_is_rejected(course_root):
    batch(course_root)
    path = course_root / "research/market/batches/test.json"
    data = json.loads(path.read_text())
    data["vacancies"].append({**data["vacancies"][0], "id": "different-id"})
    write_json(path, data)
    with pytest.raises(ValueError):
        market_report(course_root)
