import os
import json
import cv2
import numpy as np
import yt_dlp
import whisper
from pydub import AudioSegment
import google.generativeai as genai
import logging
import importlib

tf = None

logger = logging.getLogger(__name__)

_FRAME_CLASSIFIER = None
_FRAME_CLASS_NAMES = None
_FRAME_IMG_SIZE = (224, 224)

_DEFAULT_CLASS_NAMES = ["text", "diagram", "formula", "code"]

_OPTIONAL_MODELS_INIT = False
_EASYOCR_READER = None
_PYTESSERACT = None
_LATEX_OCR_MODEL = None
_CAPTION_PIPELINE = None


def _build_fallback_classifier(num_classes: int):
    """Rebuilds the known training architecture to support legacy/fragile H5 loading."""
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=_FRAME_IMG_SIZE + (3,),
        include_top=False,
        weights=None,
    )
    base_model.trainable = False

    return tf.keras.Sequential([
        tf.keras.layers.Rescaling(1.0 / 255, input_shape=_FRAME_IMG_SIZE + (3,)),
        base_model,
        tf.keras.layers.GlobalAveragePooling2D(),
        tf.keras.layers.Dense(num_classes, activation='softmax'),
    ])


def _init_trained_frame_classifier():
    """Loads the trained frame classifier (.h5) and class names once per process."""
    global _FRAME_CLASSIFIER, _FRAME_CLASS_NAMES

    if _FRAME_CLASSIFIER is not None:
        return

    global tf
    if tf is None:
        try:
            tf = importlib.import_module('tensorflow')
        except Exception:
            logger.warning("Frame classifier unavailable: tensorflow not installed")
            return

    model_path = os.path.join(PROJECT_DIR, 'frame_classifier.h5')
    class_names_path = os.path.join(PROJECT_DIR, 'class_names.json')

    try:
        if os.path.exists(class_names_path):
            with open(class_names_path, 'r', encoding='utf-8') as f:
                _FRAME_CLASS_NAMES = json.load(f)
        else:
            _FRAME_CLASS_NAMES = _DEFAULT_CLASS_NAMES

        try:
            _FRAME_CLASSIFIER = tf.keras.models.load_model(model_path, compile=False)
        except Exception:
            logger.warning(
                "Direct model load failed, attempting architecture rebuild + load_weights | model=%s",
                model_path,
            )
            _FRAME_CLASSIFIER = _build_fallback_classifier(len(_FRAME_CLASS_NAMES))
            _FRAME_CLASSIFIER.load_weights(model_path)

        logger.info(
            "Trained frame classifier loaded | model=%s | classes=%s",
            model_path,
            _FRAME_CLASS_NAMES,
        )
    except Exception:
        logger.exception("Failed to load trained frame classifier | model=%s", model_path)
        _FRAME_CLASSIFIER = None
        _FRAME_CLASS_NAMES = None


def _classify_frame(frame_path: str) -> tuple[str, float]:
    """Returns (predicted_label, confidence) using trained frame classifier."""
    if _FRAME_CLASSIFIER is None:
        return 'unknown', 0.0

    try:
        img = tf.keras.utils.load_img(frame_path, target_size=_FRAME_IMG_SIZE)
        img_array = tf.keras.utils.img_to_array(img)
        batch = np.expand_dims(img_array, axis=0)

        predictions = _FRAME_CLASSIFIER.predict(batch, verbose=0)
        probs = predictions[0]
        class_idx = int(np.argmax(probs))
        confidence = float(probs[class_idx])
        class_names = _FRAME_CLASS_NAMES or _DEFAULT_CLASS_NAMES
        label = class_names[class_idx] if class_idx < len(class_names) else f'class_{class_idx}'
        return label, confidence
    except Exception:
        logger.exception("Frame classification failed | frame_path=%s", frame_path)
        return 'unknown', 0.0


def _init_optional_visual_models():
    """Initializes optional per-type extraction models with graceful fallbacks."""
    global _OPTIONAL_MODELS_INIT, _EASYOCR_READER, _PYTESSERACT, _LATEX_OCR_MODEL, _CAPTION_PIPELINE
    if _OPTIONAL_MODELS_INIT:
        return
    _OPTIONAL_MODELS_INIT = True

    try:
        easyocr_module = importlib.import_module('easyocr')
        _EASYOCR_READER = easyocr_module.Reader(['en'], gpu=False)
        logger.info("EasyOCR initialized")
    except Exception:
        logger.info("EasyOCR unavailable; will use fallback OCR")

    try:
        _PYTESSERACT = importlib.import_module('pytesseract')
        logger.info("pytesseract initialized")
    except Exception:
        logger.info("pytesseract unavailable")

    try:
        pix2tex_cli = importlib.import_module('pix2tex.cli')
        _LATEX_OCR_MODEL = pix2tex_cli.LatexOCR()
        logger.info("LaTeX OCR initialized")
    except Exception:
        logger.info("LaTeX OCR unavailable")

    try:
        transformers_module = importlib.import_module('transformers')
        _CAPTION_PIPELINE = transformers_module.pipeline(
            "image-to-text",
            model="Salesforce/blip-image-captioning-base",
        )
        logger.info("Captioning pipeline initialized")
    except Exception:
        logger.info("Captioning pipeline unavailable")


def _extract_text_from_frame(frame_path: str) -> str:
    if _EASYOCR_READER is not None:
        try:
            results = _EASYOCR_READER.readtext(frame_path)
            text = "\n".join([item[1] for item in results]).strip()
            if text:
                return text
        except Exception:
            logger.debug("EasyOCR extraction failed | frame=%s", frame_path, exc_info=True)

    if _PYTESSERACT is not None:
        try:
            frame = cv2.imread(frame_path, cv2.IMREAD_GRAYSCALE)
            if frame is None:
                return ""
            return _PYTESSERACT.image_to_string(frame).strip()
        except Exception:
            logger.debug("pytesseract extraction failed | frame=%s", frame_path, exc_info=True)

    return ""


def _extract_visual_content(frame_path: str, frame_type: str) -> str:
    if frame_type in ('text', 'code'):
        text = _extract_text_from_frame(frame_path)
        return text if text else "No text extracted"

    if frame_type == 'formula':
        if _LATEX_OCR_MODEL is not None:
            try:
                pil_image_module = importlib.import_module('PIL.Image')
                img = pil_image_module.open(frame_path)
                return str(_LATEX_OCR_MODEL(img)).strip()
            except Exception:
                logger.debug("LaTeX OCR failed | frame=%s", frame_path, exc_info=True)
        fallback = _extract_text_from_frame(frame_path)
        return fallback if fallback else "Formula frame detected"

    if frame_type == 'diagram':
        if _CAPTION_PIPELINE is not None:
            try:
                pil_image_module = importlib.import_module('PIL.Image')
                img = pil_image_module.open(frame_path).convert('RGB')
                generated = _CAPTION_PIPELINE(img)
                if generated and isinstance(generated, list):
                    caption = generated[0].get('generated_text', '').strip()
                    if caption:
                        return caption
            except Exception:
                logger.debug("Caption generation failed | frame=%s", frame_path, exc_info=True)
        return "Diagram frame detected"

    return "Visual content type not supported"


def _calculate_importance(frame_path: str, extracted_content: str) -> float:
    frame = cv2.imread(frame_path)
    if frame is None:
        return 0.0

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]
    edges = cv2.Canny(gray, 100, 200)

    complexity_score = float(np.sum(edges) / max(h * w * 255, 1))
    text_score = min(len(extracted_content) / 500.0, 1.0)
    importance = 0.7 * complexity_score + 0.3 * text_score
    return round(float(np.clip(importance, 0.0, 1.0)), 3)

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
    """Classifies sampled frames using the trained frame classifier and returns visual events."""
    _init_trained_frame_classifier()
    _init_optional_visual_models()

    visual_events = []
    logger.debug("process_visual_stream start | frame_count=%s", len(frame_paths))

    for frame_data in frame_paths:
        label, confidence = _classify_frame(frame_data['path'])
        extracted_content = _extract_visual_content(frame_data['path'], label)
        importance_score = _calculate_importance(frame_data['path'], extracted_content)
        visual_events.append({
            'timestamp': frame_data['timestamp'],
            'type': label,
            'score': importance_score,
            'content': extracted_content,
            'classification_confidence': round(confidence, 3),
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
