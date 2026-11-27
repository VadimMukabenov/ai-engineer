import os
import secrets
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .catalog import load_catalog
from .files import read_json, safe_path
from .market import market_report
from .materials import render_material
from .progress import build_progress
from .records import read_records, save_attempt


def discover_root() -> Path:
    if os.getenv("AI_ENGINEER_ROOT"):
        return Path(os.environ["AI_ENGINEER_ROOT"]).resolve()
    for path in [Path.cwd(), *Path.cwd().parents]:
        if (path / "governance/plan.json").exists():
            return path
    raise ValueError("Запустите из монорепо или задайте AI_ENGINEER_ROOT")


def create_app(root: Path | None = None) -> FastAPI:
    root = (root or discover_root()).resolve()
    app = FastAPI(title="Learning Hub", docs_url=None, redoc_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "[::1]", "testserver"])
    assets = Path(__file__).parent
    templates = Jinja2Templates(directory=assets / "templates")
    app.mount("/static", StaticFiles(directory=assets / "static"), name="static")
    csrf = secrets.token_urlsafe(32)

    def render(request: Request, template: str, **context):
        report = build_progress(root)
        return templates.TemplateResponse(
            request=request,
            name=template,
            context={"report": report, "csrf_token": csrf, "path": request.url.path, **context},
        )

    def lesson_by_id(lid):
        lesson = next((x for x in load_catalog(root)["lessons"] if x["id"] == lid), None)
        if lesson is None or lesson["state"] != "ready":
            raise HTTPException(404, "Материал не подготовлен или урок не найден")
        return lesson

    @app.get("/")
    def dashboard(request: Request):
        return render(request, "dashboard.html")

    @app.get("/modules/{module_id}")
    def module(request: Request, module_id: str):
        c = load_catalog(root)
        row = next((x for x in c["modules"] if x["id"] == module_id), None)
        if not row:
            raise HTTPException(404)
        return render(
            request,
            "module.html",
            module=row,
            lessons=[x for x in c["lessons"] if x["module_id"] == module_id],
            outcomes=[x for x in c["outcomes"] if x["module_id"] == module_id],
        )

    @app.get("/lessons/{lesson_id}")
    def lesson(request: Request, lesson_id: str):
        row = lesson_by_id(lesson_id)
        # Course Markdown is trusted versioned repository content. Learner answers are never rendered as HTML.
        material = safe_path(root, row["material_path"])
        return render(
            request, "lesson.html", lesson=row, material=render_material(root, material, load_catalog(root))
        )

    @app.post("/lessons/{lesson_id}/attempts")
    def attempt(
        request: Request,
        lesson_id: str,
        answer: str = Form(""),
        assistance: str = Form("none"),
        kind: str = Form("answer"),
        csrf_token: str = Form(""),
    ):
        lesson_by_id(lesson_id)
        origin = request.headers.get("origin")
        if not secrets.compare_digest(csrf_token, csrf) or (
            origin and origin != str(request.base_url).rstrip("/")
        ):
            raise HTTPException(403, "Откройте урок заново перед отправкой")
        try:
            save_attempt(root, lesson_id, answer, assistance, kind=kind)
        except ValueError:
            raise HTTPException(422, "Нужен ответ до 20 000 символов и корректная отметка помощи")
        return RedirectResponse("/history?saved=1", status_code=303)

    @app.get("/history")
    def history(request: Request):
        attempts, assessments, errors = read_records(root)
        return render(
            request,
            "history.html",
            attempts=sorted(attempts, key=lambda x: x.recorded_at, reverse=True),
            assessments=assessments,
            record_errors=errors,
        )

    @app.get("/market")
    def market(request: Request):
        return render(request, "market.html", market=market_report(root))

    @app.get("/projects")
    def projects(request: Request):
        return render(request, "projects.html")

    @app.get("/api/status")
    def status():
        return build_progress(root)

    @app.get("/api/market")
    def market_json():
        return market_report(root)

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "course_version": read_json(root / "projects/learning-hub/course/catalog.json")["course_version"],
        }

    return app
