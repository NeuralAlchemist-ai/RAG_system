from fastapi import APIRouter, Depends
from api.schemas import ChatRequest, ChatResponse
from api.dependencies import get_current_user
from src.query_data import RAGChatBot
from src.history import load_history

router = APIRouter(prefix="/api/v1")

sessions: dict[str, RAGChatBot] = {}


@router.post("/chat/", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    real_user_id = str(current_user.id)

    if real_user_id not in sessions:
        sessions[real_user_id] = RAGChatBot()
        history = load_history(user_id=real_user_id)
        sessions[real_user_id].chat_history = history or []

    chatbot = sessions[real_user_id]
    answer, sources = chatbot.ask(
        request.question,
        user_id=real_user_id,
    )
    return ChatResponse(
        answer=answer,
        sources=sources
    )


@router.get("/chat/history") 
async def get_history(current_user: dict = Depends(get_current_user)):
    messages = load_history(user_id=str(current_user.id))
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


@router.delete("/chat/history")
async def clear_history(current_user: dict = Depends(get_current_user)):
    real_user_id = str(current_user.id)
    if real_user_id in sessions:
        sessions[real_user_id].clear_history(user_id=real_user_id)
    from src.history import clear_history as clear_db_history
    clear_db_history(user_id=real_user_id)
    return {"message": "History cleared"}