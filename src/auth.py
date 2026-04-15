from supabase import create_client
from src.config import SUPABASE_URL, SUPABASE_KEY
import logging

_supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def verify_token(token: str) -> dict | None:
    try:
        response = _supabase.auth.get_user(token)
        return response.user
    except Exception as e:
        logging.warning(f"Token verification failed: {e}")
        return None

def sign_up(email: str, password: str) -> dict:
    try:
        response = _supabase.auth.sign_up({"email": email, "password": password})
        return {"success": True, "user": response.user}
    except Exception as e:
        return {"success": False, "error": str(e)}

def sign_in(email: str, password: str) -> dict:
    try:
        response = _supabase.auth.sign_in_with_password({"email": email, "password": password})
        return {"success": True, "access_token": response.session.access_token, "user_id": str(response.user.id)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def sign_out(token: str) -> None:
    try:
        _supabase.auth.sign_out()
    except Exception as e:
        logging.warning(f"Sign out failed: {e}")