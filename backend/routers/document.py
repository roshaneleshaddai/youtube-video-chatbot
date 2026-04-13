import os
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from services.document import document_to_mat
from services.rag import index_mat_document
from services.llm import generate_final_summary, generate_quiz, generate_title

router = APIRouter(prefix="/api/document", tags=["Document Processing"])
logger = logging.getLogger(__name__)


class DocumentResponse(BaseModel):
    message: str
    video_id: str
    title: str
    summary: str
    quiz: str


@router.post("/process", response_model=DocumentResponse)
async def process_document(file: UploadFile = File(...)):
    try:
        logger.info("[document] /api/document/process called | filename=%s", file.filename)
        raw = await file.read()
        if not raw:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        doc_id, mat_text, extension = document_to_mat(file.filename or "uploaded_document", raw)
        logger.info(
            "[document] Parsed document | doc_id=%s | filename=%s | extension=%s | chars=%s",
            doc_id,
            file.filename,
            extension,
            len(mat_text),
        )

        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail="GOOGLE_API_KEY environment variable is not set. Document text was parsed but cannot be analyzed yet.",
            )

        chunks_indexed = index_mat_document(doc_id, mat_text)
        summary = generate_final_summary(mat_text)
        quiz = generate_quiz(mat_text)
        title = generate_title(mat_text)

        return DocumentResponse(
            message=f"Document processed successfully and indexed into {chunks_indexed} chunks.",
            video_id=doc_id,
            title=title,
            summary=summary,
            quiz=quiz,
        )
    except HTTPException:
        raise
    except ValueError as exc:
        logger.warning("[document] Validation error | filename=%s | error=%s", file.filename, str(exc))
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        error_text = str(exc)
        if "RESOURCE_EXHAUSTED" in error_text or "429" in error_text:
            logger.warning("[document] Quota/rate limit hit | filename=%s | error=%s", file.filename, error_text)
            raise HTTPException(status_code=429, detail=error_text)
        logger.exception("[document] Processing failed | filename=%s | error=%s", file.filename, str(exc))
        raise HTTPException(status_code=500, detail=str(exc))
