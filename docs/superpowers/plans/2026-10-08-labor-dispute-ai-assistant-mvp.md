# Labor Dispute AI Assistant MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local web application that turns uploaded labor-dispute materials into a source-linked, structured case report.

**Architecture:** Use one FastAPI process with server-rendered HTML, SQLite metadata, and a local per-case file store. A sequential analysis pipeline parses documents, calls one OpenAI-compatible model client, validates JSON, and persists only successful reports.

**Tech Stack:** Python 3.11+, FastAPI, Jinja2, SQLite, httpx, pypdf, python-docx, pytest

**Spec:** `docs/superpowers/specs/2026-10-08-labor-dispute-ai-assistant-design.md`

## Global Constraints

- Support PDF, DOCX, TXT, PNG, JPG, and JPEG uploads.
- Default to localhost operation and never log document bodies, API keys, or complete personal information.
- Every reported fact must contain one or more source references; unsupported statements become verification items.
- Use a sequential pipeline, not an autonomous multi-agent framework.
- Do not add accounts, billing, collaboration, a vector database, a message queue, a standalone OCR service, or legal-database retrieval.
- Show “AI 辅助整理，不构成法律意见” on every report.
- Keep real credentials, real case materials, and runtime data out of Git.

## File Map

```text
pyproject.toml                         Dependencies and test configuration
.env.example                          Model and local storage configuration
.gitignore                            Runtime data and secret exclusions
src/legal_case_agent/app.py           FastAPI routes and app factory
src/legal_case_agent/config.py        Environment configuration
src/legal_case_agent/db.py            SQLite schema and persistence functions
src/legal_case_agent/models.py        Validated report and source models
src/legal_case_agent/storage.py       Safe case-directory and upload handling
src/legal_case_agent/parsers.py       TXT, DOCX, PDF, and image parsing dispatch
src/legal_case_agent/llm.py           OpenAI-compatible HTTP client and retry
src/legal_case_agent/pipeline.py      Sequential extraction and report workflow
src/legal_case_agent/templates/       Server-rendered upload and report pages
tests/                                Focused unit and end-to-end tests
tests/fixtures/sample_case/           Synthetic, non-personal test materials
README.md                              Setup, run, limitations, and safety notice
```

---

### Task 1: Application foundation and SQLite persistence

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `src/legal_case_agent/__init__.py`
- Create: `src/legal_case_agent/config.py`
- Create: `src/legal_case_agent/db.py`
- Create: `tests/test_db.py`

**Interfaces:**
- Produces: `Settings.from_env() -> Settings`
- Produces: `connect(database_path: Path) -> sqlite3.Connection`
- Produces: `init_db(connection) -> None`
- Produces: `create_case(connection, name: str) -> str`
- Produces: `get_case(connection, case_id: str) -> sqlite3.Row | None`

- [ ] **Step 1: Define dependencies and test configuration**

Create `pyproject.toml` with Python `>=3.11`, runtime dependencies `fastapi`, `uvicorn`, `jinja2`, `python-multipart`, `httpx`, `pypdf`, and `python-docx`, plus a `test` extra containing `pytest` and `pytest-asyncio`. Configure pytest with `pythonpath = ["src"]`.

- [ ] **Step 2: Write the failing persistence test**

```python
from legal_case_agent.db import connect, create_case, get_case, init_db


def test_create_and_read_case(tmp_path):
    connection = connect(tmp_path / "app.db")
    init_db(connection)
    case_id = create_case(connection, "张某劳动争议")

    row = get_case(connection, case_id)
    assert row["name"] == "张某劳动争议"
    assert row["status"] == "draft"
```

- [ ] **Step 3: Run the test and verify the expected failure**

Run: `python -m pytest tests/test_db.py -v`

Expected: FAIL because `legal_case_agent.db` does not exist.

- [ ] **Step 4: Implement configuration and persistence**

Implement `Settings` as a frozen dataclass reading `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`, `APP_DATA_DIR`, and `MAX_FILE_MB`. Use defaults `http://127.0.0.1:8000/v1`, empty key, empty model, `./data`, and `20` MB.

In `db.py`, open SQLite with `row_factory = sqlite3.Row`, enable foreign keys, and create the four tables specified by the design: `cases`, `documents`, `analysis_runs`, and `reports`. Generate IDs with `uuid.uuid4().hex` and store UTC ISO timestamps.

- [ ] **Step 5: Add secret and runtime exclusions**

Create `.env.example` with the five documented variables and add `.env`, `data/`, `*.db`, `__pycache__/`, `.pytest_cache/`, and virtual environments to `.gitignore`.

- [ ] **Step 6: Run the test and commit**

Run: `python -m pytest tests/test_db.py -v`

Expected: PASS.

```bash
git add pyproject.toml .env.example .gitignore src/legal_case_agent tests/test_db.py
git commit -m "feat: add application foundation and database"
```

### Task 2: Safe case uploads and document records

**Files:**
- Create: `src/legal_case_agent/storage.py`
- Modify: `src/legal_case_agent/db.py`
- Create: `tests/test_storage.py`

**Interfaces:**
- Consumes: `Settings.app_data_dir`, `Settings.max_file_mb`
- Produces: `save_upload(case_id: str, original_name: str, content: bytes, data_dir: Path, max_file_mb: int) -> StoredFile`
- Produces: `add_document(connection, case_id: str, stored: StoredFile) -> str`
- Produces: `list_documents(connection, case_id: str) -> list[sqlite3.Row]`

- [ ] **Step 1: Write upload validation tests**

```python
import pytest
from legal_case_agent.storage import UploadError, save_upload


def test_upload_uses_generated_name_and_stays_in_case_directory(tmp_path):
    stored = save_upload("case1", "../工资记录.txt", b"2026-01 工资 8000", tmp_path, 1)
    assert stored.original_name == "工资记录.txt"
    assert stored.path.parent == (tmp_path / "cases" / "case1" / "documents").resolve()
    assert stored.path.read_bytes() == b"2026-01 工资 8000"


def test_upload_rejects_unsupported_extension(tmp_path):
    with pytest.raises(UploadError, match="不支持的文件类型"):
        save_upload("case1", "script.exe", b"x", tmp_path, 1)


def test_upload_rejects_oversized_file(tmp_path):
    with pytest.raises(UploadError, match="超过 1 MB"):
        save_upload("case1", "large.txt", b"x" * (1024 * 1024 + 1), tmp_path, 1)
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/test_storage.py -v`

Expected: FAIL because `legal_case_agent.storage` does not exist.

- [ ] **Step 3: Implement safe storage**

Define `StoredFile(original_name: str, path: Path, extension: str, size_bytes: int)` and `UploadError`. Accept only `.pdf`, `.docx`, `.txt`, `.png`, `.jpg`, and `.jpeg`; normalize the original name with `Path(name).name`; reject empty content; generate the stored filename with a UUID; resolve the target directory and assert it remains below `data_dir/cases/<case_id>/documents` before writing.

- [ ] **Step 4: Add document persistence**

Add `add_document` and `list_documents` to `db.py`. Store only the path relative to `APP_DATA_DIR`, initialize `parse_status` as `pending`, and order document results by creation time.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest tests/test_storage.py tests/test_db.py -v`

Expected: PASS.

```bash
git add src/legal_case_agent/storage.py src/legal_case_agent/db.py tests/test_storage.py
git commit -m "feat: add safe case file uploads"
```

### Task 3: Document parsing and stable source chunks

**Files:**
- Create: `src/legal_case_agent/parsers.py`
- Create: `tests/test_parsers.py`
- Create: `tests/fixtures/sample_case/聊天记录.txt`
- Create: `tests/fixtures/sample_case/劳动合同.docx`
- Create: `tests/fixtures/sample_case/工资流水.pdf`

**Interfaces:**
- Produces: `SourceChunk(document_id: str, source_label: str, text: str)`
- Produces: `ParseResult(chunks: list[SourceChunk], warnings: list[str])`
- Produces: `parse_document(document_id: str, original_name: str, path: Path) -> ParseResult`

- [ ] **Step 1: Add synthetic fixtures**

Create fixtures containing only fictional parties: 张某 and 示例科技有限公司. The TXT fixture contains a dated termination chat; DOCX contains contract dates and salary; PDF contains two months of salary entries. Generate DOCX and PDF fixtures once with their native libraries and commit the resulting small binary files.

- [ ] **Step 2: Write parser tests**

```python
from legal_case_agent.parsers import parse_document


def test_txt_chunks_include_stable_source(tmp_path):
    path = tmp_path / "聊天记录.txt"
    path.write_text("2026-02-01 公司通知解除劳动合同", encoding="utf-8")
    result = parse_document("doc1", "聊天记录.txt", path)
    assert result.chunks[0].source_label == "聊天记录.txt，第 1 段"
    assert "解除劳动合同" in result.chunks[0].text


def test_image_without_vision_returns_warning(tmp_path):
    path = tmp_path / "证据.jpg"
    path.write_bytes(b"not-decoded-in-parser")
    result = parse_document("doc2", "证据.jpg", path)
    assert result.chunks == []
    assert result.warnings == ["证据.jpg：需要人工查看或视觉模型识别"]
```

- [ ] **Step 3: Run tests and verify failure**

Run: `python -m pytest tests/test_parsers.py -v`

Expected: FAIL because `legal_case_agent.parsers` does not exist.

- [ ] **Step 4: Implement parsers**

Use UTF-8 with BOM fallback for TXT, `python-docx` paragraphs for DOCX, and `pypdf.PdfReader` pages for PDF. Emit source labels as `文件名，第 N 段` or `文件名，第 N 页`. For PNG/JPG/JPEG return no chunks and the specified manual-review warning. Raise `ParseError` for unreadable files and never silently return invented text.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest tests/test_parsers.py -v`

Expected: PASS.

```bash
git add src/legal_case_agent/parsers.py tests/test_parsers.py tests/fixtures/sample_case
git commit -m "feat: parse case documents with source labels"
```

### Task 4: Report schema and OpenAI-compatible model client

**Files:**
- Create: `src/legal_case_agent/models.py`
- Create: `src/legal_case_agent/llm.py`
- Create: `tests/test_llm.py`

**Interfaces:**
- Consumes: `SourceChunk`
- Produces: `CaseReport.model_validate_json(raw: str) -> CaseReport`
- Produces: `LLMClient.generate_report(chunks: list[SourceChunk], warnings: list[str]) -> CaseReport`

- [ ] **Step 1: Write schema and retry tests**

```python
import httpx
from legal_case_agent.llm import LLMClient


def test_client_retries_once_after_invalid_json():
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        content = "not-json" if calls == 1 else '{"summary":{"case_type":"劳动争议","parties":[],"claims":[],"amounts":[],"stage":"待核实","sources":["聊天记录.txt，第 1 段"]},"timeline":[],"evidence":[],"issues":[],"missing_materials":[],"hearing_checklist":[],"manual_review":[]}'
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    client = LLMClient("key", "https://model.test/v1", "model", transport=httpx.MockTransport(handler))
    report = client.generate_report([], [])
    assert report.summary.case_type == "劳动争议"
    assert calls == 2
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/test_llm.py -v`

Expected: FAIL because report models and `LLMClient` do not exist.

- [ ] **Step 3: Define strict report models**

Use Pydantic models for `Summary`, `TimelineEvent`, `EvidenceItem`, `Issue`, and `CaseReport`. Require `sources: list[str]` on factual summary fields, timeline events, evidence items, and issue assertions. Define the six output sections plus `manual_review`. Forbid unknown fields so accidental model drift is visible.

- [ ] **Step 4: Implement the model client**

POST to `<base_url>/chat/completions` using `httpx.Client`, bearer authentication, the configured model, `temperature: 0`, and JSON response instructions. The system prompt requires Chinese output, prohibits invented facts and legal citations, and instructs the model to place unsupported claims in `manual_review`. Parse with `CaseReport.model_validate_json`; on invalid JSON send one corrective retry containing the validation error, then raise `AnalysisError`.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest tests/test_llm.py -v`

Expected: PASS with exactly two mock requests.

```bash
git add src/legal_case_agent/models.py src/legal_case_agent/llm.py tests/test_llm.py
git commit -m "feat: add validated model report generation"
```

### Task 5: Sequential analysis pipeline and report versioning

**Files:**
- Create: `src/legal_case_agent/pipeline.py`
- Modify: `src/legal_case_agent/db.py`
- Create: `tests/test_pipeline.py`

**Interfaces:**
- Consumes: `list_documents`, `parse_document`, `LLMClient.generate_report`
- Produces: `run_analysis(connection, case_id: str, data_dir: Path, client: LLMClient) -> str`
- Produces: `get_latest_report(connection, case_id: str) -> sqlite3.Row | None`

- [ ] **Step 1: Write the failure-preserves-report test**

```python
import pytest
from legal_case_agent.pipeline import run_analysis


def test_failed_run_does_not_replace_successful_report(prepared_case, failing_client):
    connection, case_id, data_dir, successful_report_id = prepared_case
    with pytest.raises(RuntimeError, match="model unavailable"):
        run_analysis(connection, case_id, data_dir, failing_client)
    latest = connection.execute(
        "SELECT reports.id FROM reports "
        "JOIN analysis_runs ON analysis_runs.id = reports.run_id "
        "WHERE analysis_runs.case_id = ? ORDER BY reports.version DESC LIMIT 1",
        (case_id,),
    ).fetchone()
    assert latest["id"] == successful_report_id
```

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/test_pipeline.py -v`

Expected: FAIL because `legal_case_agent.pipeline` does not exist.

- [ ] **Step 3: Add run and report persistence functions**

Add functions that create a running `analysis_runs` row, mark it succeeded or failed, append a monotonically increasing report version inside a transaction, update document parse states, and fetch the newest successful report. Store `CaseReport.model_dump_json()` in `reports.content_json`.

- [ ] **Step 4: Implement the pipeline**

Load all case documents, resolve stored paths below `data_dir`, parse each independently, accumulate chunks and warnings, and continue after `ParseError` by marking that document failed. Refuse to call the model when no chunks exist. Persist a new report only after schema validation succeeds. On any exception, mark the run failed with a sanitized error message and re-raise without touching prior reports.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest tests/test_pipeline.py tests/test_llm.py tests/test_parsers.py -v`

Expected: PASS.

```bash
git add src/legal_case_agent/pipeline.py src/legal_case_agent/db.py tests/test_pipeline.py
git commit -m "feat: add sequential case analysis pipeline"
```

### Task 6: Local web workflow and end-to-end acceptance

**Files:**
- Create: `src/legal_case_agent/app.py`
- Create: `src/legal_case_agent/templates/base.html`
- Create: `src/legal_case_agent/templates/index.html`
- Create: `src/legal_case_agent/templates/case.html`
- Create: `src/legal_case_agent/templates/report.html`
- Create: `tests/test_app.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: all prior persistence, storage, pipeline, and report interfaces
- Produces: `create_app(settings: Settings | None = None, client: LLMClient | None = None) -> FastAPI`
- Produces: HTTP routes `GET /`, `POST /cases`, `POST /cases/{case_id}/documents`, `POST /cases/{case_id}/analyze`, and `GET /cases/{case_id}/report`

- [ ] **Step 1: Write the end-to-end web test**

```python
from fastapi.testclient import TestClient
from legal_case_agent.app import create_app


def test_case_upload_analysis_and_report(test_settings, fixed_report_client):
    client = TestClient(create_app(test_settings, fixed_report_client))
    created = client.post("/cases", data={"name": "张某劳动争议"}, follow_redirects=False)
    case_url = created.headers["location"]
    case_id = case_url.rstrip("/").split("/")[-1]

    uploaded = client.post(
        f"/cases/{case_id}/documents",
        files=[("files", ("聊天记录.txt", "2026-02-01 公司通知解除", "text/plain"))],
        follow_redirects=False,
    )
    assert uploaded.status_code == 303

    analyzed = client.post(f"/cases/{case_id}/analyze", follow_redirects=False)
    report = client.get(analyzed.headers["location"])
    assert report.status_code == 200
    assert "案件摘要" in report.text
    assert "聊天记录.txt，第 1 段" in report.text
    assert "AI 辅助整理，不构成法律意见" in report.text
```

- [ ] **Step 2: Run the test and verify failure**

Run: `python -m pytest tests/test_app.py -v`

Expected: FAIL because `legal_case_agent.app` does not exist.

- [ ] **Step 3: Implement routes and dependency wiring**

Create the database and data directories at app startup. Render cases on `/`; create and redirect from `/cases`; save each uploaded file independently and display per-file errors on the case page; run analysis synchronously for the local MVP; redirect successful runs to the report and render sanitized failures on the case page. Return 404 for unknown cases and reports.

- [ ] **Step 4: Build accessible server-rendered pages**

Use semantic headings, labeled controls, keyboard-accessible forms, visible focus styles, and tables with headers. The report template renders the six fixed sections, source labels beside each factual item, warnings for contradictions/manual review, and the required legal disclaimer at both the top and bottom.

- [ ] **Step 5: Update the README**

Replace claims about nonexistent files and mock behavior with exact setup commands:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[test]"
Copy-Item .env.example .env
uvicorn legal_case_agent.app:create_app --factory --host 127.0.0.1 --port 8000
```

Document supported files, environment variables, local-only security posture, test command, known limitations, and the prohibition on uploading real client materials to untrusted model providers.

- [ ] **Step 6: Run full acceptance checks**

Run: `python -m pytest -v`

Expected: all tests PASS.

Run: `uvicorn legal_case_agent.app:create_app --factory --host 127.0.0.1 --port 8000`

Expected: opening `http://127.0.0.1:8000` allows the synthetic case flow, and the report shows all six sections, sources, warnings, and both disclaimers.

- [ ] **Step 7: Commit the completed MVP**

```bash
git add src/legal_case_agent/app.py src/legal_case_agent/templates tests/test_app.py README.md
git commit -m "feat: deliver local labor dispute assistant MVP"
```

## Final verification

- [ ] Run `python -m pytest -v` from a clean checkout and confirm all tests pass.
- [ ] Run `git status --short` and confirm no generated database, uploaded material, `.env`, or cache file is tracked.
- [ ] Confirm the report has six sections, source references, manual-review warnings, and the required disclaimer.
- [ ] Confirm a failed second analysis leaves the first successful report intact.
- [ ] Confirm unsupported files, oversized files, path traversal names, empty cases, invalid model JSON, and model outages produce user-visible errors without leaking document content or credentials.
