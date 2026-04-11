from fastapi import APIRouter
from api.schemas import ChatRequest, ChatResponse
from src.query_data import RAGChatBot
from src.history import load_history

router = APIRouter(prefix="/api/v1")

sessions: dict[str, RAGChatBot] = {}


@router.post("/chat/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if request.session_id not in sessions:
        sessions[request.session_id] = RAGChatBot()
        history = load_history(request.session_id)
        if history:
            sessions[request.session_id].chat_history = history
        else:
            sessions[request.session_id].chat_history = []

    chatbot = sessions[request.session_id]
    answer, sources = chatbot.ask(
        request.question,             
        user_id=request.user_id,
        session_id=request.session_id
    )
    return ChatResponse(
        answer=answer,
        sources=sources,
        session_id=request.session_id
    )


@router.get("/chat/{session_id}/history") 
async def get_history(session_id: str):
    messages = load_history(session_id)
    return {
        "messages": [
            {
                "role":    m["role"],
                "content": m["content"],
                "sources": []
            }
            for m in messages
        ]
    }


@router.delete("/chat/{session_id}")
async def clear_history(session_id: str):
    if session_id in sessions:
        sessions[session_id].clear_history(session_id=session_id)
        return {"message": "History cleared"}
    return {"message": "Session not found"}