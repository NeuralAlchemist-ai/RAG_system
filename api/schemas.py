from pydantic import BaseModel
from typing import List

class ChatRequest(BaseModel):
    question: str
    user_id: str
    session_id: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    session_id: str