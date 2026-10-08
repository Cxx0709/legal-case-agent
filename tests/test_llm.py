import json
import httpx

from legal_case_agent.llm import LLMClient


VALID_REPORT = {
    "summary": {"case_type": "劳动争议", "parties": [], "claims": [], "amounts": [], "stage": "待核实", "sources": []},
    "timeline": [], "evidence": [], "issues": [], "missing_materials": [],
    "hearing_checklist": [], "manual_review": []
}


def test_client_retries_once_after_invalid_json():
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        content = "not-json" if calls == 1 else json.dumps(VALID_REPORT, ensure_ascii=False)
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    client = LLMClient("key", "https://model.test/v1", "model", httpx.MockTransport(handler))
    assert client.generate_report([], []).summary.case_type == "劳动争议"
    assert calls == 2
