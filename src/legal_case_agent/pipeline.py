from pathlib import Path
import sqlite3
import uuid

from .db import _now, list_documents
from .llm import LLMClient
from .parsers import ParseError, parse_document


def _safe_error(exc: Exception) -> str:
    return str(exc)[:300] or exc.__class__.__name__


def run_analysis(
    connection: sqlite3.Connection, case_id: str, data_dir: Path, client: LLMClient
) -> str:
    run_id = uuid.uuid4().hex
    connection.execute(
        "INSERT INTO analysis_runs VALUES (?, ?, 'running', ?, NULL, ?, NULL)",
        (run_id, case_id, client.model, _now()),
    )
    connection.commit()
    chunks, warnings = [], []
    try:
        root = data_dir.resolve()
        for document in list_documents(connection, case_id):
            path = (root / document["stored_path"]).resolve()
            if root not in path.parents:
                raise RuntimeError("文档路径无效")
            try:
                result = parse_document(document["id"], document["original_name"], path)
                chunks.extend(result.chunks)
                warnings.extend(result.warnings)
                status, warning = "parsed", "；".join(result.warnings) or None
            except ParseError as exc:
                status, warning = "failed", _safe_error(exc)
                warnings.append(warning)
            connection.execute(
                "UPDATE documents SET parse_status = ?, warning = ? WHERE id = ?",
                (status, warning, document["id"]),
            )
        if not chunks:
            raise RuntimeError("没有可分析的文本，请检查文件或补充可读取材料")

        report = client.generate_report(chunks, warnings)
        version = connection.execute(
            """SELECT COALESCE(MAX(reports.version), 0) + 1 FROM reports
            JOIN analysis_runs ON analysis_runs.id = reports.run_id
            WHERE analysis_runs.case_id = ?""",
            (case_id,),
        ).fetchone()[0]
        report_id = uuid.uuid4().hex
        with connection:
            connection.execute(
                "INSERT INTO reports VALUES (?, ?, ?, ?, ?)",
                (report_id, run_id, version, report.model_dump_json(), _now()),
            )
            connection.execute(
                "UPDATE analysis_runs SET status = 'succeeded', finished_at = ? WHERE id = ?",
                (_now(), run_id),
            )
            connection.execute(
                "UPDATE cases SET status = 'analyzed', updated_at = ? WHERE id = ?",
                (_now(), case_id),
            )
        return report_id
    except Exception as exc:
        connection.execute(
            "UPDATE analysis_runs SET status = 'failed', error = ?, finished_at = ? WHERE id = ?",
            (_safe_error(exc), _now(), run_id),
        )
        connection.commit()
        raise
