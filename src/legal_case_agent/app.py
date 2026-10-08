from pathlib import Path
import json

from fastapi import FastAPI, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .config import Settings
from .db import add_document, connect, create_case, get_case, get_latest_report, init_db, list_cases, list_documents
from .llm import LLMClient
from .models import CaseReport
from .pipeline import run_analysis
from .storage import UploadError, save_upload


def create_app(settings: Settings | None = None, client: LLMClient | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    settings.app_data_dir.mkdir(parents=True, exist_ok=True)
    connection = connect(settings.app_data_dir / "app.db")
    init_db(connection)
    model_client = client or LLMClient(settings.llm_api_key, settings.llm_base_url, settings.llm_model)
    templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
    app = FastAPI(title="劳动争议律师 AI 助理")

    def case_context(request: Request, case_id: str, errors=None):
        case = get_case(connection, case_id)
        if not case:
            return None
        return {
            "request": request,
            "case": case,
            "documents": list_documents(connection, case_id),
            "errors": errors or [],
        }

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request):
        return templates.TemplateResponse(request, "index.html", {"cases": list_cases(connection)})

    @app.post("/cases")
    def new_case(name: str = Form(...)):
        case_id = create_case(connection, name)
        return RedirectResponse(f"/cases/{case_id}", status_code=303)

    @app.get("/cases/{case_id}", response_class=HTMLResponse)
    def case_page(request: Request, case_id: str):
        context = case_context(request, case_id)
        if not context:
            return HTMLResponse("案件不存在", status_code=404)
        return templates.TemplateResponse(request, "case.html", context)

    @app.post("/cases/{case_id}/documents", response_class=HTMLResponse)
    async def upload_documents(request: Request, case_id: str, files: list[UploadFile]):
        context = case_context(request, case_id)
        if not context:
            return HTMLResponse("案件不存在", status_code=404)
        errors = []
        for upload in files:
            try:
                stored = save_upload(
                    case_id, upload.filename or "", await upload.read(),
                    settings.app_data_dir, settings.max_file_mb, upload.content_type,
                )
                add_document(connection, case_id, stored, settings.app_data_dir)
            except UploadError as exc:
                errors.append(f"{upload.filename or '未命名文件'}：{exc}")
            finally:
                await upload.close()
        if errors:
            return templates.TemplateResponse(request, "case.html", case_context(request, case_id, errors), status_code=400)
        return RedirectResponse(f"/cases/{case_id}", status_code=303)

    @app.post("/cases/{case_id}/analyze", response_class=HTMLResponse)
    def analyze(request: Request, case_id: str):
        context = case_context(request, case_id)
        if not context:
            return HTMLResponse("案件不存在", status_code=404)
        try:
            run_analysis(connection, case_id, settings.app_data_dir, model_client)
        except Exception as exc:
            context["errors"] = [str(exc)]
            return templates.TemplateResponse(request, "case.html", context, status_code=400)
        return RedirectResponse(f"/cases/{case_id}/report", status_code=303)

    @app.get("/cases/{case_id}/report", response_class=HTMLResponse)
    def report_page(request: Request, case_id: str):
        case, row = get_case(connection, case_id), get_latest_report(connection, case_id)
        if not case or not row:
            return HTMLResponse("报告不存在", status_code=404)
        report = CaseReport.model_validate(json.loads(row["content_json"]))
        return templates.TemplateResponse(
            request, "report.html", {"case": case, "report": report, "version": row["version"]}
        )

    return app


app = create_app()
