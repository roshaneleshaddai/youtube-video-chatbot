from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.rag import retrieve_context
from services.llm import generate_rag_response

router = APIRouter(prefix="/api/chat", tags=["RAG Chat"])

class ChatRequest(BaseModel):
    video_id: str
    query: str

class ChatResponse(BaseModel):
    answer: str

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # 1. Retrieve Context from ChromaDB using Video ID
        context = retrieve_context(request.video_id, request.query)
        
        # 2. Generate final response based on context + query
        answer = generate_rag_response(request.query, context)
        
        return ChatResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
