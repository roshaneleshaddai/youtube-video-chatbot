import hashlib
import json
import logging
from pathlib import Path
from typing import Tuple

try:
    from pypdf import PdfReader  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - optional dependency
    PdfReader = None

logger = logging.getLogger(__name__)

TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".log", ".py", ".js", ".ts"}


def build_document_id(filename: str, content: bytes) -> str:
    # Deterministic id allows reusing embeddings for the same file content.
    digest = hashlib.sha256()
    digest.update(filename.encode("utf-8", errors="ignore"))
    digest.update(content)
    return digest.hexdigest()[:24]


def _extract_pdf_text(content: bytes) -> str:
    if PdfReader is None:
        raise ValueError("PDF support requires pypdf package")

    import io

    reader = PdfReader(io.BytesIO(content))
    parts: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            parts.append(page_text.strip())

    return "\n\n".join(parts)


def extract_document_text(filename: str, content: bytes) -> Tuple[str, str]:
    extension = Path(filename).suffix.lower()

    if extension in TEXT_EXTENSIONS:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1", errors="ignore")
        return text, extension

    if extension == ".pdf":
        return _extract_pdf_text(content), extension

    raise ValueError("Unsupported file type. Upload txt, md, csv, json, log, code text files, or pdf.")


def document_to_mat(filename: str, content: bytes) -> tuple[str, str, str]:
    doc_text, extension = extract_document_text(filename, content)
    if not doc_text.strip():
        raise ValueError("Uploaded document has no readable text content")

    doc_id = build_document_id(filename, content)
    mat_text = (
        f"[DOCUMENT_ANALYSIS]\n"
        f"[FILENAME: {filename}]\n"
        f"[FILE_TYPE: {extension or 'unknown'}]\n\n"
        f"{doc_text.strip()}"
    )
    logger.info(
        "document_to_mat complete | doc_id=%s | filename=%s | file_type=%s | chars=%s",
        doc_id,
        filename,
        extension,
        len(mat_text),
    )
    return doc_id, mat_text, extension
