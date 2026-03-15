import os
import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import logging
from typing import Iterable

logger = logging.getLogger(__name__)

# Initialize ChromaDB Local Client
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(PROJECT_DIR, 'chroma_db')
chroma_client = chromadb.PersistentClient(path=DB_DIR)

collection_name = "mat_collection"
DEFAULT_EMBEDDING_MODEL = os.getenv("GOOGLE_EMBEDDING_MODEL", "models/gemini-embedding-001")


def _model_candidates() -> list[str]:
    configured = DEFAULT_EMBEDDING_MODEL.strip()
    candidates = [configured]
    # Known working fallback for current Gemini API + langchain_google_genai.
    if configured != "models/gemini-embedding-001":
        candidates.append("models/gemini-embedding-001")
    return candidates


def _is_model_not_found_error(exc: Exception) -> bool:
    message = str(exc)
    return "NOT_FOUND" in message and "models/" in message


def _embed_documents_with_fallback(chunks: list[str]) -> tuple[list[list[float]], str]:
    errors: list[str] = []
    for model_name in _model_candidates():
        try:
            logger.debug("Embedding documents | model=%s | chunk_count=%s", model_name, len(chunks))
            embeddings = GoogleGenerativeAIEmbeddings(model=model_name)
            return embeddings.embed_documents(chunks), model_name
        except Exception as exc:
            errors.append(f"{model_name}: {exc}")
            if _is_model_not_found_error(exc):
                logger.warning("Embedding model unavailable, trying fallback | model=%s", model_name)
                continue
            raise
    raise RuntimeError("No compatible embedding model found. Errors: " + " | ".join(errors))


def _embed_query_with_fallback(query: str) -> tuple[list[float], str]:
    errors: list[str] = []
    for model_name in _model_candidates():
        try:
            logger.debug("Embedding query | model=%s | query_len=%s", model_name, len(query))
            embeddings = GoogleGenerativeAIEmbeddings(model=model_name)
            return embeddings.embed_query(query), model_name
        except Exception as exc:
            errors.append(f"{model_name}: {exc}")
            if _is_model_not_found_error(exc):
                logger.warning("Query embedding model unavailable, trying fallback | model=%s", model_name)
                continue
            raise
    raise RuntimeError("No compatible embedding model found. Errors: " + " | ".join(errors))

def get_or_create_collection():
    logger.debug("Using Chroma collection=%s | db_dir=%s", collection_name, DB_DIR)
    return chroma_client.get_or_create_collection(name=collection_name)

def index_mat_document(video_id: str, mat_text: str):
    """
    Chunks the MAT text and indexes it into ChromaDB.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set")
    logger.debug("index_mat_document start | video_id=%s | mat_chars=%s", video_id, len(mat_text))
        
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    
    chunks = text_splitter.split_text(mat_text)
    
    collection = get_or_create_collection()

    # Reuse existing index entries if this video was already processed.
    existing = collection.get(where={"video_id": video_id}, include=[])
    existing_ids = existing.get("ids", []) if isinstance(existing, dict) else []
    if existing_ids:
        logger.info(
            "index_mat_document cache hit | video_id=%s | existing_chunks=%s",
            video_id,
            len(existing_ids),
        )
        return len(existing_ids)
    
    # Generate embeddings and add to collection.
    embedded_docs, model_used = _embed_documents_with_fallback(chunks)
    logger.info("index_mat_document embeddings generated | video_id=%s | model=%s", video_id, model_used)
    
    ids = [f"{video_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"video_id": video_id} for _ in range(len(chunks))]
    
    collection.add(
        documents=chunks,
        embeddings=embedded_docs,
        metadatas=metadatas,
        ids=ids
    )
    logger.debug("index_mat_document complete | video_id=%s | chunks=%s", video_id, len(chunks))
    return len(chunks)

def retrieve_context(video_id: str, query: str, top_k: int = 3) -> str:
    """
    Retrieves the most relevant chunks from ChromaDB for a given query.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set")
    logger.debug("retrieve_context start | video_id=%s | top_k=%s | query_len=%s", video_id, top_k, len(query))
        
    query_embedding, model_used = _embed_query_with_fallback(query)
    logger.debug("retrieve_context query embedded | video_id=%s | model=%s", video_id, model_used)
    
    collection = get_or_create_collection()
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"video_id": video_id}
    )
    
    if not results['documents'] or not results['documents'][0]:
        logger.debug("retrieve_context empty result | video_id=%s", video_id)
        return ""

    context = "\n\n".join(results['documents'][0])
    logger.debug("retrieve_context complete | video_id=%s | context_chars=%s", video_id, len(context))
    return context
