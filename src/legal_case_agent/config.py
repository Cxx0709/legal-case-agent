from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"
    app_data_dir: Path = Path("data")
    max_file_mb: int = 20
    max_case_mb: int = 200
    max_material_chars: int = 200_000

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            llm_api_key=os.getenv("LLM_API_KEY", ""),
            llm_base_url=os.getenv("LLM_BASE_URL", cls.llm_base_url),
            llm_model=os.getenv("LLM_MODEL", cls.llm_model),
            app_data_dir=Path(os.getenv("APP_DATA_DIR", "data")),
            max_file_mb=int(os.getenv("MAX_FILE_MB", "20")),
            max_case_mb=int(os.getenv("MAX_CASE_MB", "200")),
            max_material_chars=int(os.getenv("MAX_MATERIAL_CHARS", "200000")),
        )
