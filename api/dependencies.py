from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.auth import verify_token

bearer_scheme = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)) -> dict:
    token = credentials.credentials
    user = verify_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user