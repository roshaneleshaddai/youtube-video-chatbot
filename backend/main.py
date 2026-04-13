from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
import time
import uuid
from pathlib import Path
from dotenv import load_dotenv, dotenv_values

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

# Force .env values to be applied even when empty env vars already exist in the shell.
load_dotenv(ENV_PATH, override=True)

# Recover GOOGLE_API_KEY when .env was saved with UTF-8 BOM in the first key name.
if not os.getenv("GOOGLE_API_KEY"):
    env_values = dotenv_values(ENV_PATH)
    os.environ["GOOGLE_API_KEY"] = (
        env_values.get("GOOGLE_API_KEY")
        or env_values.get("\ufeffGOOGLE_API_KEY")
        or ""
    )

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
THIRD_PARTY_LOG_LEVEL = os.getenv("THIRD_PARTY_LOG_LEVEL", "WARNING").upper()
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "server.log"

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.DEBUG),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
    force=True,
)

logger = logging.getLogger(__name__)

# Keep noisy internals (Numba/JIT/compiler logs) out of normal app output.
for noisy_logger_name in (
    "numba",
    "numba.core",
    "numba.core.ssa",
    "numba.core.byteflow",
    "numba.core.interpreter",
    "llvmlite",
):
    logging.getLogger(noisy_logger_name).setLevel(
        getattr(logging, THIRD_PARTY_LOG_LEVEL, logging.WARNING)
    )

app = FastAPI(title="RAG Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers import video, chat, document

app.include_router(video.router)
app.include_router(chat.router)
app.include_router(document.router)

logger.info(
    "FastAPI app initialized with log level=%s | third_party_log_level=%s | log_file=%s | google_api_key_set=%s",
    LOG_LEVEL,
    THIRD_PARTY_LOG_LEVEL,
    LOG_FILE,
    bool(os.getenv("GOOGLE_API_KEY")),
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()
    logger.info(
        "REQ START | id=%s | method=%s | path=%s | query=%s",
        request_id,
        request.method,
        request.url.path,
        request.url.query,
    )
    try:
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "REQ END   | id=%s | status=%s | elapsed_ms=%.2f",
            request_id,
            response.status_code,
            elapsed_ms,
        )
        return response
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "REQ FAIL  | id=%s | elapsed_ms=%.2f | error=%s",
            request_id,
            elapsed_ms,
            str(exc),
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "request_id": request_id},
        )

@app.get("/")
def read_root():
    logger.debug("Root health endpoint called")
    return {"message": "Welcome to the RAG Chatbot API"}
