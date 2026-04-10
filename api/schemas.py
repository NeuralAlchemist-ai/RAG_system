from pydantic import BaseModel
from typing import List

class ChatRequest(BaseModel):
    query: str
    user_id: str
    session_id: str
    k: int = 3

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    session_id: str