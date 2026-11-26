"""Observations, not salary predictions or automatically qualified opportunities."""

from collections import Counter
from pathlib import Path

from .catalog import load_catalog
from .files import read_json


def market_report(root: Path) -> dict:
    rows, seen, urls = [], set(), set()
    for path in sorted((root / "research/market/batches").glob("*.json")):
        for row in read_json(path)["vacancies"]:
            if row["id"] in seen:
                raise ValueError(f"Повтор вакансии: {row['id']}")
            if row["url"] in urls:
                raise ValueError(f"Повтор URL вакансии: {row['url']}")
            if not row["url"].startswith("https://"):
                raise ValueError("Источник вакансии должен быть HTTPS")
            if row["verification"] not in {"verified", "partial"}:
                raise ValueError("Неизвестный статус проверки вакансии")
            if not all(
                isinstance(row[key], list) and all(isinstance(x, str) and x.strip() for x in row[key])
                for key in ["required_skills", "preferred_skills"]
            ):
                raise ValueError("Навыки вакансии должны быть массивами строк")
            urls.add(row["url"])
            seen.add(row["id"])
            rows.append(row)
    verified = [r for r in rows if r["verification"] == "verified"]
    aliases_file = root / "research/market/skill-aliases.json"
    aliases = read_json(aliases_file) if aliases_file.exists() else {}
    catalog = load_catalog(root)
    if not set(aliases) <= {s["id"] for s in catalog["skills"]}:
        raise ValueError("Алиас ссылается на неизвестный skill ID")
    if not all(
        isinstance(names, list) and all(isinstance(n, str) and n.strip() for n in names)
        for names in aliases.values()
    ):
        raise ValueError("Алиасы должны быть массивами непустых строк")
    outcome_by_skill = {
        s["id"]: [o for o in catalog["outcomes"] if s["id"] in o["skill_ids"]] for s in catalog["skills"]
    }
    matrix = []
    for row in rows:
        for importance, key in [("required", "required_skills"), ("preferred", "preferred_skills")]:
            for raw in row[key]:
                mapped = [
                    sid for sid, names in aliases.items() if raw.casefold() in {n.casefold() for n in names}
                ]
                outcomes = [o for sid in mapped for o in outcome_by_skill.get(sid, [])]
                matrix.append(
                    {
                        "vacancy_id": row["id"],
                        "company": row["company"],
                        "url": row["url"],
                        "verification": row["verification"],
                        "checked_on": row["checked_on"],
                        "requirement": raw,
                        "importance": importance,
                        "skill_ids": mapped,
                        "outcome_ids": sorted({o["id"] for o in outcomes}),
                        "project_ids": sorted({p for o in outcomes for p in o["project_ids"]}),
                        "mapping": "exact_alias" if mapped else "needs_review",
                    }
                )
    frequency = Counter()
    for row in verified:
        explicit = {x.casefold() for x in row["required_skills"]}
        for sid, names in aliases.items():
            if explicit.intersection(n.casefold() for n in names):
                frequency[sid] += 1
    return {
        "observations": len(rows),
        "verified": len(verified),
        "partial": sum(r["verification"] == "partial" for r in rows),
        "fully_remote": sum(r["remote"] == "fully_remote" for r in rows),
        "confirmed_salary_and_eligibility_fit": sum(
            r["verification"] == "verified"
            and r["remote"] == "fully_remote"
            and r.get("active") == "confirmed"
            and r["hiring_eligibility"] == "confirmed"
            and r["salary"]["currency"] == "USD"
            and r["salary"]["basis"] == "net"
            and r["salary"]["period"] == "month"
            and (r["salary"]["min"] or 0) >= 5000
            for r in rows
        ),
        "frequency_denominator": len(verified),
        "skill_frequency": dict(frequency.most_common()),
        "vacancies": rows,
        "matrix": matrix,
        "limitation": "Разведочная выборка; доступность найма из РФ/Казахстана и минимум $5000 net не подтверждены вместе",
    }
