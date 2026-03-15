from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
import time
import os
import hashlib
from services.pipeline import process_video_to_mat
from services.rag import index_mat_document
from services.llm import generate_final_summary, generate_quiz

router = APIRouter(prefix="/api/video", tags=["Video Processing"])
logger = logging.getLogger(__name__)


def emit(message: str):
    logger.info(message)
    print(message, flush=True)


def build_video_id(url: str) -> str:
    # Deterministic ID enables cross-request cache and index reuse.
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]

class VideoRequest(BaseModel):
    url: str

class VideoResponse(BaseModel):
    message: str
    video_id: str
    summary: str
    quiz: str

@router.post("/process", response_model=VideoResponse)
async def process_video(request: VideoRequest):
    start_time = time.perf_counter()
    try:
        emit(f"[video] /api/video/process called | url={request.url}")
        video_id = build_video_id(request.url)
        emit(f"[video] Generated video_id={video_id}")
        
        # 1. Process Video -> MAT
        stage_start = time.perf_counter()
        mat_text, spoken_transcript, used_cache = process_video_to_mat(request.url, video_id=video_id, prefer_cache=True)
        logger.debug(
            "Pipeline complete | video_id=%s | mat_len=%s | transcript_segments=%s | elapsed=%.2fs",
            video_id,
            len(mat_text) if mat_text else 0,
            len(spoken_transcript) if spoken_transcript else 0,
            time.perf_counter() - stage_start,
        )
        if not mat_text:
            logger.error("MAT generation failed | video_id=%s", video_id)
            raise HTTPException(status_code=400, detail="Failed to process video source.")
        if used_cache:
            emit(f"[video] MAT cache hit | video_id={video_id} | elapsed={time.perf_counter() - stage_start:.2f}s")
        else:
            emit(f"[video] MAT generated | video_id={video_id} | elapsed={time.perf_counter() - stage_start:.2f}s")

        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail="GOOGLE_API_KEY environment variable is not set. MAT has been prepared and cached; set the key and retry.",
            )
            
        # 2. Index MAT in ChromaDB for RAG Chatbot
        stage_start = time.perf_counter()
        chunks_indexed = index_mat_document(video_id, mat_text)
        logger.debug(
            "Indexing complete | video_id=%s | chunks_indexed=%s | elapsed=%.2fs",
            video_id,
            chunks_indexed,
            time.perf_counter() - stage_start,
        )
        emit(f"[video] Indexed chunks={chunks_indexed} | video_id={video_id} | elapsed={time.perf_counter() - stage_start:.2f}s")
        
        # 3. Generate Summary & Quiz
        stage_start = time.perf_counter()
        summary = generate_final_summary(mat_text)
        logger.debug("Summary generated | video_id=%s | chars=%s", video_id, len(summary) if summary else 0)
        quiz = generate_quiz(mat_text)
        logger.debug(
            "Quiz generated | video_id=%s | chars=%s | elapsed=%.2fs",
            video_id,
            len(quiz) if quiz else 0,
            time.perf_counter() - stage_start,
        )
        emit(f"[video] Summary+Quiz generated | video_id={video_id} | elapsed={time.perf_counter() - stage_start:.2f}s")

        logger.info(
            "Video processing success | video_id=%s | total_elapsed=%.2fs",
            video_id,
            time.perf_counter() - start_time,
        )
        emit(f"[video] Success | video_id={video_id} | total_elapsed={time.perf_counter() - start_time:.2f}s")
        
        return VideoResponse(
            message=f"Video processed successfully and indexed into {chunks_indexed} chunks.",
            video_id=video_id,
            summary=summary,
            quiz=quiz
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Video processing failed | url=%s | elapsed=%.2fs | error=%s",
            request.url,
            time.perf_counter() - start_time,
            str(e),
        )
        print(f"[video] Failed | url={request.url} | error={str(e)}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))
