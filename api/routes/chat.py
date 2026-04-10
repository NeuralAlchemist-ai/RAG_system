from fastapi import APIRouter
from api.schemas import ChatRequest, ChatResponse
from src.query_data import RAGChatBot

router = APIRouter(prefix="/api/v1")

sessions: dict[str, RAGChatBot] = {}

@router.post("/chat/",response_model=ChatResponse)
async def chat(request: ChatRequest):

    if request.session_id not in sessions:
        sessions[request.session_id] = RAGChatBot()

    chatbot = sessions[request.session_id]

    answer,source=chatbot.ask(request.query,user_id=request.user_id,k=request.k)

    return ChatResponse(answer=answer, sources=source, session_id=request.session_id)

@router.delete("/chat/{session_id}")
async def clear_history(session_id: str):

    if session_id in sessions:
        sessions[session_id].clear_history() 
        return {"message": "History cleared"}
    return {"message": "Session not found"}