import re
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from learning_hub.app import create_app
from learning_hub.progress import build_progress
from learning_hub.records import save_attempt


def submit(client, text="Мой самостоятельный ответ", **extra):
    page = client.get("/lessons/D00")
    token = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
    return client.post(
        "/lessons/D00/attempts", data={"answer": text, "assistance": "none", "csrf_token": token, **extra}
    )


def test_dashboard_and_diagnostic_show_actual_course(course_root):
    client = TestClient(create_app(course_root))
    page = client.get("/")
    assert page.status_code == 200
    assert "Обучение AI Engineer" in page.text
    assert "Начать диагностику" in page.text
    assert "Объясните свой ответ" in client.get("/lessons/D00").text
    assert client.get("/lessons/unknown").status_code == 404
    assert client.get("/lessons/L00").status_code == 404


def test_attempt_survives_restart_and_is_escaped(course_root):
    client = TestClient(create_app(course_root))
    assert submit(client, "<script>alert(1)</script>").status_code == 200
    restarted = TestClient(create_app(course_root))
    history = restarted.get("/history").text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in history
    assert "<script>alert(1)</script>" not in history
    assert restarted.get("/api/status").json()["attempt_count"] == 1
    assert build_progress(course_root)["mastered_outcomes"] == 0


def test_invalid_or_cross_origin_attempt_rejected(course_root):
    client = TestClient(create_app(course_root))
    assert (
        client.post("/lessons/D00/attempts", data={"answer": "Bad", "assistance": "none"}).status_code == 403
    )
    assert submit(client, "  ").status_code == 422
    assert submit(client, "x" * 20001).status_code == 422
    assert submit(client, assistance="fabricated").status_code == 422
    assert build_progress(course_root)["attempt_count"] == 0


def test_concurrent_attempts_never_overwrite(course_root):
    with ThreadPoolExecutor(max_workers=4) as executor:
        rows = list(
            executor.map(lambda n: save_attempt(course_root, "D00", f"Answer {n}", "none"), range(12))
        )
    assert len({r["id"] for r in rows}) == 12
    assert build_progress(course_root)["attempt_count"] == 12


def test_api_is_read_only_and_does_not_grant_passes(course_root):
    client = TestClient(create_app(course_root))
    assert client.post("/api/status", json={"mastered_outcomes": 2}).status_code == 405
    assert client.get("/api/status").json()["mastered_outcomes"] == 0


def test_untrusted_host_cannot_access_local_course(course_root):
    from fastapi.testclient import TestClient

    from learning_hub.app import create_app

    with TestClient(create_app(course_root)) as client:
        assert client.get("/", headers={"host": "attacker.example"}).status_code == 400


def test_material_links_are_rewritten_to_canonical_lesson_urls(course_root):
    import json

    from conftest import write_json
    from fastapi.testclient import TestClient

    from learning_hub.app import create_app

    path = course_root / "projects/learning-hub/course/catalog.json"
    catalog = json.loads(path.read_text())
    catalog["lessons"][1].update(state="ready", material_path="materials/L00.md")
    write_json(path, catalog)
    (course_root / "materials/L00.md").write_text("[Back](D00.md)")
    with TestClient(create_app(course_root)) as client:
        assert 'href="/lessons/D00"' in client.get("/lessons/L00").text


def test_history_shows_assessment_reason_and_evidence(course_root):
    from fastapi.testclient import TestClient
    from test_progress import assessment

    from learning_hub.app import create_app
    from learning_hub.records import save_attempt

    row = save_attempt(course_root, "D00", "Independent answer", "none")
    assessment(course_root, row)
    with TestClient(create_app(course_root)) as client:
        page = client.get("/history").text
    assert "ASSESS-1" in page
    assert "Explained and applied in a new example" in page
    assert "evidence/answer.txt" in page
    assert "Ожидает проверки" not in page
