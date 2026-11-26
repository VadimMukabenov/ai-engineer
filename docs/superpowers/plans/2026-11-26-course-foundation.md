# Course Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for native execution in the current session. User authorized execution of the reviewed approach on 2026-11-26. Work is tracked in this repository's separate Beads; steps below define the implementation, not a second live task tracker.

**Goal:** A recoverable Python-first course foundation with all agreed competencies/projects, source-backed market observations, first diagnostic/lab, and an honest working progress UI.

**Architecture:** JSON course and governance contracts, independent project passports, immutable learning records, separate embedded Beads, FastAPI/Jinja dashboard, deterministic verification, GitHub CI and restore test.

**Tech Stack:** Python 3.12+, uv, FastAPI, Pydantic v2, Jinja2, pytest, HTTPX; existing Ollama; Beads 1.0.3 pinned initially.

**Spec:** `docs/superpowers/specs/2026-11-26-course-foundation-design.md`

## Global Constraints

- Preserve 6 capstones, 9 blocks, Python-first and independent learning checks.
- No paid services until a budget is explicitly set; no VPN/kernel/driver/global-bd changes.
- Zero initial learner mastery. Agent work and test fixtures never create learner achievements.
- Unknown market eligibility or net salary stays unknown. RF priority, Kazakhstan secondary.
- New repository branch `codex/course-foundation`; public remote under VadimMukabenov (user clarification 2026-11-27).

## Review Focus

- Forged/missing assessment evidence must not increment mastery.
- Unrecognised IDs, dependency cycles and missing mandatory scope must fail verification.
- Paths outside repository and HTML in learner input must not permit arbitrary file read/write or executable rendering.
- Learning records must survive app restart; simultaneous writes must not overwrite another attempt.
- GitHub/Beads sync/restore failures and unavailable server protections must be reported, never converted to success.

## Task 1: Canonical scope, market protocol and teaching material

**Files:** `governance/plan.json`, `projects/learning-hub/course/catalog.json`, six `projects/*/passport.json`, `research/market/README.md`, `docs/teaching-method.md`, `docs/CONTEXT.md`.

**Interfaces:** catalog has schema_version/course_version, skills, modules, lessons and outcomes; plan owns mandatory module/project IDs; passports reference skill/outcome IDs. Market batches share a documented observation schema. Consumers receive validated JSON objects.

- Create exact agreed scope, stage/criteria definitions, foundation content and unresolved decisions.
- Prepare diagnostic and first lab without filling the learner's answer or marking any result passed.
- Collect 30–50 unique market observations if primary sources are accessible; preserve verified/partial/unavailable separately and report shortfall instead of inventing entries.
- Verify JSON parses and the registry reconstructs the complete scope; commit the canonical baseline.

## Task 2: Validator and progress engine (test first)

**Files:** `projects/learning-hub/src/learning_hub/{catalog,records,progress,cli}.py`, `tests/test_contract.py`, `tests/test_progress.py`, `Makefile`.

**Interfaces:** `load_catalog(root: Path) -> dict`; `validate_repository(root: Path) -> list[str]`; `build_progress(root: Path) -> dict`; `save_attempt(root: Path, lesson_id: str, answer: str, assistance: str) -> dict`; CLI `verify`, `status`, `readme`.

- Write tests proving zero initial progress and rejection of deleted modules, unknown skills, cycles, missing/altered evidence, incompatible criterion versions and invalid records.
- Run tests RED with missing behavior, then implement and run full suite GREEN.
- Count unique independently demonstrated outcomes, not tasks or repeated attempts. Keep project readiness and market observations separate.
- Generate README summary from the same computed state. Commit verified behavior.

## Task 3: Learning Hub first complete interaction (test first)

**Files:** `learning_hub/app.py`, templates/static, `tests/test_app.py`, app `pyproject.toml`/`uv.lock`/Dockerfile.

**Interfaces:** `create_app(root: Path | None = None) -> FastAPI`; GET `/`, `/modules/{id}`, `/lessons/{id}`, `/history`, `/market`, `/projects`; POST `/lessons/{id}/attempts`; GET `/api/status`; bind localhost.

- Pin behavior: render actual course, reject unknown lesson and invalid/oversized input, escape learner HTML, persist attempts and recover after restart without raising mastery.
- Watch RED, implement server-rendered UI from design concept, run GREEN suite.
- Verify in Browser/IAB desktop/mobile and inspect screenshots against concept. Record explicit deviations or blockers.
- Use temporary records for automated acceptance, never manufacture actual student completion. Commit.

## Task 4: Beads, CI, remote preservation and recovery

**Files:** `scripts/bd`, `scripts/verify_restore.py`, `.github/workflows/verify.yml`, `governance/runtime-status.json`, Beads export/config and restore docs.

**Interfaces:** project wrapper selects explicit local binary and project database; no invocation of global remote wrapper. Restore procedure verifies code contract, issue IDs/dependencies and student record counts.

- Test wrapper isolation and restore comparison; run negative cases.
- Create milestone tasks in the actual separate Beads; export read model and configure supported backup/sync.
- Push public GitHub repository, inspect remote files/workflow, restore into clean disposable checkout with separate Beads data, compare inventories.
- Inspect server protection availability and record exact state; do not claim independent trust with owner/admin credentials.

## Task 5: Independent final review and handoff

**Files:** `docs/CONTEXT.md`, verification/restore reports, review findings.

- Run full platform suite, verify course and negative controls, verify public remote and complete restore evidence.
- Fresh reviewer reads actual spec/code/data and reports material defects. Fix Important defects with regression tests; retain honest limitations.
- Open learning-hub in Codex, hand over diagnostic and exact continuation command. No claim of completed learner diagnostics or job eligibility without evidence.
