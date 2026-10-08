from dataclasses import dataclass
from pathlib import Path
import uuid


ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg"}
ALLOWED_MIME_TYPES = {
    ".pdf": {"application/pdf"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    ".txt": {"text/plain", "application/octet-stream"},
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
}


class UploadError(ValueError):
    pass


@dataclass(frozen=True)
class StoredFile:
    original_name: str
    path: Path
    extension: str
    size_bytes: int


def save_upload(
    case_id: str, original_name: str, content: bytes, data_dir: Path, max_file_mb: int,
    content_type: str | None = None,
) -> StoredFile:
    clean_name = Path(original_name).name
    extension = Path(clean_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise UploadError(f"不支持的文件类型：{extension or '无扩展名'}")
    mime = (content_type or "").split(";", 1)[0].strip().lower()
    if mime and mime not in ALLOWED_MIME_TYPES[extension]:
        raise UploadError("文件类型与内容类型不匹配")
    if not content:
        raise UploadError("文件为空")
    limit = max_file_mb * 1024 * 1024
    if len(content) > limit:
        raise UploadError(f"文件超过 {max_file_mb} MB")

    root = (data_dir / "cases" / case_id / "documents").resolve()
    root.mkdir(parents=True, exist_ok=True)
    target = (root / f"{uuid.uuid4().hex}{extension}").resolve()
    if target.parent != root:
        raise UploadError("文件路径无效")
    target.write_bytes(content)
    return StoredFile(clean_name, target, extension, len(content))
