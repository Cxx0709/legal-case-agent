import pytest

from legal_case_agent.db import add_document, connect, create_case, get_latest_report, init_db
from legal_case_agent.models import CaseReport
from legal_case_agent.pipeline import run_analysis
from legal_case_agent.storage import save_upload


REPORT = {
    "summary": {"case_type": "劳动争议", "parties": [], "claims": [], "amounts": [], "stage": "待核实", "sources": ["材料.txt，第 1 段"]},
    "timeline": [], "evidence": [], "issues": [], "missing_materials": [],
    "hearing_checklist": [], "manual_review": []
}


class SuccessfulClient:
    model = "test-model"

    def generate_report(self, chunks, warnings):
        return CaseReport.model_validate(REPORT)


class FailingClient:
    model = "test-model"

    def generate_report(self, chunks, warnings):
        raise RuntimeError("model unavailable")


def test_failed_run_keeps_previous_successful_report(tmp_path):
    connection = connect(tmp_path / "app.db")
    init_db(connection)
    case_id = create_case(connection, "测试案件")
    stored = save_upload(case_id, "材料.txt", "事实".encode(), tmp_path, 1)
    add_document(connection, case_id, stored, tmp_path)
    run_analysis(connection, case_id, tmp_path, SuccessfulClient())
    first_report = get_latest_report(connection, case_id)["id"]

    with pytest.raises(RuntimeError, match="model unavailable"):
        run_analysis(connection, case_id, tmp_path, FailingClient())

    assert get_latest_report(connection, case_id)["id"] == first_report
