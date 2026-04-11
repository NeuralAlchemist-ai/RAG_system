from supabase import create_client, Client
from src.config import SUPABASE_URL, SUPABASE_KEY, MAX_HISTORY
import logging

logger = logging.getLogger(__name__)

_supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_supabase():
    return _supabase

def save_message(
    session_id: str,
    user_id: str,
    role: str,
    content: str,
    sources: list[str] | None = None
) -> None:
    try:
        supabase = get_supabase()
        supabase.table("chat_history").insert({
            "session_id": session_id,
            "user_id":    user_id,
            "role":       role,
            "content":    content,
            "sources":    sources or [],
        }).execute()
        logger.info(f"Saved {role} message for session {session_id}")
    except Exception as e:
        logger.error(f"Failed to save message: {e}")

def load_history(session_id: str) -> list[dict]:
    try:
        supabase = get_supabase()
        response = (
        supabase.table("chat_history")
        .select("role, content")
        .eq("session_id", session_id)
        .order("created_at", desc=False)
        .limit(MAX_HISTORY)           
        .execute()
    )
        if response.data:
            logger.info(f"Loaded {len(response.data)} messages for session {session_id}")
            return [{"role": r["role"], "content": r["content"]} for r in response.data]
        else:
            logger.warning(f"Failed to load history: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error loading history: {e}")
        return []
    
def clear_history(session_id: str) -> None:
    try:
        supabase = get_supabase()
        supabase.table("chat_history").delete().eq("session_id", session_id).execute()
        logger.info(f"Cleared history for session {session_id}")
    except Exception as e:
        logger.error(f"Failed to clear history: {e}")