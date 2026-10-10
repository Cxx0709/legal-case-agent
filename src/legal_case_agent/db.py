from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import uuid


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS cases (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, status TEXT NOT NULL,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id),
            original_name TEXT NOT NULL, stored_path TEXT NOT NULL,
            extension TEXT NOT NULL, size_bytes INTEGER NOT NULL,
            parse_status TEXT NOT NULL, warning TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS analysis_runs (
            id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id),
            status TEXT NOT NULL, model TEXT NOT NULL, error TEXT,
            started_at TEXT NOT NULL, finished_at TEXT
        );
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY, run_id TEXT NOT NULL UNIQUE REFERENCES analysis_runs(id),
            version INTEGER NOT NULL, content_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_documents_case_created
            ON documents(case_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_analysis_runs_case_status
            ON analysis_runs(case_id, status);
        CREATE INDEX IF NOT EXISTS idx_reports_run_version
            ON reports(run_id, version);
        """
    )
    # A process restart cannot leave an analysis falsely claiming to run.
    connection.execute(
        "UPDATE analysis_runs SET status = 'failed', error = ?, finished_at = ? WHERE status = 'running'",
        ("服务重启，分析任务已终止", _now()),
    )
    connection.commit()


def create_case(connection: sqlite3.Connection, name: str) -> str:
    name = name.strip()
    if not name:
        raise ValueError("案件名称不能为空")
    case_id, now = uuid.uuid4().hex, _now()
    connection.execute(
        "INSERT INTO cases VALUES (?, ?, 'draft', ?, ?)",
        (case_id, name, now, now),
    )
    connection.commit()
    return case_id


def get_case(connection: sqlite3.Connection, case_id: str):
    return connection.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()


def list_cases(connection: sqlite3.Connection):
    return connection.execute("SELECT * FROM cases ORDER BY created_at DESC").fetchall()


def add_document(connection, case_id: str, stored, data_dir: Path) -> str:
    document_id = uuid.uuid4().hex
    relative = stored.path.relative_to(data_dir.resolve()).as_posix()
    connection.execute(
        "INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, 'pending', NULL, ?)",
        (document_id, case_id, stored.original_name, relative, stored.extension, stored.size_bytes, _now()),
    )
    connection.commit()
    return document_id


def list_documents(connection: sqlite3.Connection, case_id: str):
    return connection.execute(
        "SELECT * FROM documents WHERE case_id = ? ORDER BY created_at", (case_id,)
    ).fetchall()


def get_latest_report(connection: sqlite3.Connection, case_id: str):
    return connection.execute(
        """SELECT reports.* FROM reports
        JOIN analysis_runs ON analysis_runs.id = reports.run_id
        WHERE analysis_runs.case_id = ? AND analysis_runs.status = 'succeeded'
        ORDER BY reports.version DESC LIMIT 1""",
        (case_id,),
    ).fetchone()
