import json

from fastapi.testclient import TestClient

from legal_case_agent.app import create_app
from legal_case_agent.config import Settings
from legal_case_agent.models import CaseReport


REPORT = {
    "summary": {"case_type": "劳动争议", "parties": ["张某", "示例公司"], "claims": [], "amounts": [], "stage": "仲裁", "sources": ["聊天记录.txt，第 1 段"]},
    "timeline": [], "evidence": [], "issues": [], "missing_materials": [],
    "hearing_checklist": [], "manual_review": []
}


class FixedClient:
    model = "fixed-test-model"

    def generate_report(self, chunks, warnings):
        return CaseReport.model_validate(REPORT)


def test_complete_local_workflow(tmp_path):
    settings = Settings(app_data_dir=tmp_path)
    client = TestClient(create_app(settings, FixedClient()))
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
    exported = client.get(f"/cases/{case_id}/report.md")
    assert exported.status_code == 200
    assert "案件资料包" in exported.text
