from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.auth import sign_up, sign_in

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

class AuthRequest(BaseModel):
    email: str
    password: str

@router.post("/signup/")
def signup(request: AuthRequest):
    result = sign_up(request.email, request.password)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"message": "Account created successfully"}

@router.post("/login/")
def login(request: AuthRequest):
    result = sign_in(request.email, request.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    return {"access_token": result["access_token"], "user_id": result["user_id"], "token_type": "bearer"}