"""Safe file handling helpers for uploads."""
import re
import uuid
from pathlib import Path

ALLOWED_EXTENSIONS = {".pdf": "pdf", ".docx": "docx"}
ALLOWED_MIME_TYPES = {
    "pdf": {"application/pdf", "application/x-pdf"},
    "docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
        "application/octet-stream",  # some browsers send this for .docx
    },
}


def sanitize_filename(name: str | None) -> str:
    """Return a display-safe filename: no directories, no odd characters, bounded length."""
    base = Path((name or "resume").replace("\\", "/")).name
    stem, ext = Path(base).stem, Path(base).suffix.lower()
    stem = re.sub(r"[^A-Za-z0-9._ -]", "_", stem).strip(" ._") or "resume"
    return f"{stem[:80]}{ext[:10]}"


def new_stored_name(file_type: str) -> str:
    """Server-generated name; the client never controls where a file is written."""
    return f"{uuid.uuid4().hex}.{file_type}"


def resolve_upload_path(upload_dir: str, stored_name: str) -> Path:
    root = Path(upload_dir).resolve()
    path = (root / stored_name).resolve()
    if root not in path.parents:  # defence in depth against path traversal
        raise ValueError("Invalid storage path")
    return path
