import json

import httpx
from pydantic import ValidationError

from .models import CaseReport
from .parsers import SourceChunk


class AnalysisError(RuntimeError):
    pass


SYSTEM_PROMPT = """你是中国劳动争议律师的材料整理助理。只依据提供的材料输出中文 JSON。
不得补造事实、法条或案例；无法确认的内容放入 manual_review。每项事实必须引用输入中的完整 source_label。
输出字段必须严格符合给定 JSON Schema。你的工作是整理材料，不是提供法律意见。"""


class LLMClient:
    def __init__(self, api_key: str, base_url: str, model: str, transport=None):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.transport = transport

    def generate_report(self, chunks: list[SourceChunk], warnings: list[str]) -> CaseReport:
        if not self.api_key:
            raise AnalysisError("未配置 LLM_API_KEY")
        material = [{"source_label": c.source_label, "text": c.text} for c in chunks]
        prompt = json.dumps({"materials": material, "parser_warnings": warnings}, ensure_ascii=False)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]

        with httpx.Client(transport=self.transport, timeout=120) as client:
            for attempt in range(2):
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "temperature": 0,
                        "response_format": {"type": "json_object"},
                        "messages": messages,
                    },
                )
                try:
                    response.raise_for_status()
                    raw = response.json()["choices"][0]["message"]["content"]
                    return CaseReport.model_validate_json(raw)
                except (httpx.HTTPError, KeyError, ValueError, ValidationError) as exc:
                    if attempt:
                        raise AnalysisError("模型返回无法验证") from exc
                    messages.append({"role": "assistant", "content": response.text[:2000]})
                    messages.append({"role": "user", "content": "上次输出不符合 Schema。请仅返回合法 JSON。"})
        raise AnalysisError("模型调用失败")
