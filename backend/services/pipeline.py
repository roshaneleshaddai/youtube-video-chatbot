import os
import json
import cv2
import numpy as np
import yt_dlp
import whisper
from pydub import AudioSegment
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)

# Setup directories
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'outputs')
CACHE_DIR = os.path.join(OUTPUT_DIR, 'cache')
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_path(video_id: str) -> str:
    return os.path.join(CACHE_DIR, f"{video_id}.json")


def load_cached_mat(video_id: str):
    cache_file = _cache_path(video_id)
    if not os.path.exists(cache_file):
        return None, None
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            payload = json.load(f)
        mat_text = payload.get('mat_text')
        spoken_transcript = payload.get('spoken_transcript')
        if not mat_text or spoken_transcript is None:
            logger.warning("Ignoring invalid MAT cache | video_id=%s | cache_file=%s", video_id, cache_file)
            return None, None
        logger.info(
            "Loaded MAT cache | video_id=%s | transcript_segments=%s | mat_chars=%s",
            video_id,
            len(spoken_transcript),
            len(mat_text),
        )
        return mat_text, spoken_transcript
    except Exception:
        logger.exception("Failed to load MAT cache | video_id=%s | cache_file=%s", video_id, cache_file)
        return None, None


def save_cached_mat(video_id: str, video_source: str, video_path: str, mat_text: str, spoken_transcript: list):
    cache_file = _cache_path(video_id)
    payload = {
        'video_id': video_id,
        'video_source': video_source,
        'video_path': video_path,
        'mat_text': mat_text,
        'spoken_transcript': spoken_transcript,
    }
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=True)
        logger.info(
            "Saved MAT cache | video_id=%s | cache_file=%s | transcript_segments=%s | mat_chars=%s",
            video_id,
            cache_file,
            len(spoken_transcript) if spoken_transcript else 0,
            len(mat_text) if mat_text else 0,
        )
    except Exception:
        logger.exception("Failed to save MAT cache | video_id=%s | cache_file=%s", video_id, cache_file)

def download_video(url: str, output_dir: str = OUTPUT_DIR) -> str:
    logger.debug("download_video start | url=%s", url)
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'restrictfilenames': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)
            logger.debug("download_video complete | path=%s", video_path)
            return video_path
    except Exception:
        logger.exception("download_video failed | url=%s", url)
        raise

def decompose_video(video_path: str, output_dir: str = OUTPUT_DIR):
    logger.debug("decompose_video start | video_path=%s", video_path)
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    audio_path = os.path.join(output_dir, f"{base_name}.wav")
    frames_dir = os.path.join(output_dir, f"{base_name}_frames")
    os.makedirs(frames_dir, exist_ok=True)

    logger.debug("Extracting audio | source=%s | target=%s", video_path, audio_path)
    audio = AudioSegment.from_file(video_path)
    audio.export(audio_path, format="wav")

    logger.debug("Extracting frames | video_path=%s", video_path)
    frame_paths = []
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        logger.warning("Video FPS is invalid (%s). Falling back to interval=1 frame.", fps)
    frame_interval = max(int((fps or 0) * 20), 1)  # Every 20 seconds
    frame_count = 0

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
        if frame_count % frame_interval == 0:
            timestamp_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))
            frame_path = os.path.join(frames_dir, f"frame_{timestamp_ms}.jpg")
            cv2.imwrite(frame_path, frame)
            frame_paths.append({'path': frame_path, 'timestamp': timestamp_ms})
        frame_count += 1
    cap.release()
    logger.debug(
        "decompose_video complete | audio_path=%s | frames_dir=%s | frames_extracted=%s",
        audio_path,
        frames_dir,
        len(frame_paths),
    )
    return audio_path, frame_paths

def process_audio_stream(audio_path: str):
    logger.debug("process_audio_stream start | audio_path=%s", audio_path)
    # NOTE: In a real backend this might be too slow to do synchronously.
    model = whisper.load_model("base.en") 
    logger.debug("Whisper model loaded | model=base.en")
    logger.debug("Transcribing audio")
    result = model.transcribe(audio_path, word_timestamps=True)
    logger.debug("Transcription complete | segments=%s", len(result.get('segments', [])))
    return result['segments']

def process_visual_stream(frame_paths: list):
    # Stubbed visual processing to avoid heavy CV models on quick backend setup.
    # In a full deployment, OCR/LaTeX-OCR would be integrated here.
    visual_events = []
    logger.debug("process_visual_stream start | frame_count=%s", len(frame_paths))
    for frame_data in frame_paths:
        visual_events.append({
            'timestamp': frame_data['timestamp'],
            'type': 'unknown',
            'score': 0.5,
            'content': 'Visual content placeholder'
        })
    logger.debug("process_visual_stream complete | visual_events=%s", len(visual_events))
    return visual_events

def synthesize_mat(spoken_transcript: list, visual_events: list) -> str:
    logger.debug(
        "synthesize_mat start | transcript_segments=%s | visual_events=%s",
        len(spoken_transcript),
        len(visual_events),
    )
    mat_string = ""
    visual_event_idx = 0
    for segment in spoken_transcript:
        segment_start_ms = segment['start'] * 1000
        
        while visual_event_idx < len(visual_events) and visual_events[visual_event_idx]['timestamp'] < segment_start_ms:
            event = visual_events[visual_event_idx]
            mat_string += f"\n[VISUAL_EVENT @ {int(event['timestamp']/1000)}s]\n"
            mat_string += f"[FRAME_TYPE: {event['type']}]\n"
            mat_string += f"[IMPORTANCE_SCORE: {event['score']}]\n"
            mat_string += f"[CONTENT: {event['content']}]\n\n"
            visual_event_idx += 1
            
        mat_string += segment['text'].strip() + " "
        logger.debug("synthesize_mat complete | mat_chars=%s", len(mat_string))
    return mat_string

def process_video_to_mat(video_source: str, video_id: str | None = None, prefer_cache: bool = True) -> tuple[str, list, bool]:
    logger.info("process_video_to_mat called | source=%s", video_source)

    if video_id and prefer_cache:
        cached_mat_text, cached_spoken_transcript = load_cached_mat(video_id)
        if cached_mat_text and cached_spoken_transcript is not None:
            return cached_mat_text, cached_spoken_transcript, True

    if video_source.startswith('http'):
        video_path = download_video(video_source)
    else:
        video_path = video_source

    if not video_path or not os.path.exists(video_path):
        logger.error("process_video_to_mat failed | video path missing | path=%s", video_path)
        return None, None, False

    audio_path, frame_paths = decompose_video(video_path)
    spoken_transcript = process_audio_stream(audio_path)
    visual_events = process_visual_stream(frame_paths)
    mat_text = synthesize_mat(spoken_transcript, visual_events)
    logger.info(
        "process_video_to_mat complete | video_path=%s | transcript_segments=%s | frames=%s | mat_chars=%s",
        video_path,
        len(spoken_transcript) if spoken_transcript else 0,
        len(frame_paths),
        len(mat_text) if mat_text else 0,
    )
    if video_id and mat_text:
        save_cached_mat(video_id, video_source, video_path, mat_text, spoken_transcript)
    return mat_text, spoken_transcript, False
