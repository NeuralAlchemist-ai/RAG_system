from supabase import create_client
from src.config import SUPABASE_URL, SUPABASE_KEY, MAX_HISTORY
import logging

logger = logging.getLogger(__name__)

_supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_supabase():
    return _supabase

def save_message(
    user_id: str,
    role: str,
    content: str,
    sources: list[str] | None = None
) -> None:
    try:
        supabase = get_supabase()
        supabase.table("chat_history").insert({
            "user_id":    user_id,
            "role":       role,
            "content":    content,
            "sources":    sources or [],
        }).execute()
        logger.info(f"Saved {role} message for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to save message: {e}")

def load_history(user_id: str) -> list[dict]:
    try:
        supabase = get_supabase()
        response = (
        supabase.table("chat_history")
        .select("role, content")
        .eq("user_id", user_id)
        .order("created_at", desc=False)
        .limit(MAX_HISTORY)           
        .execute()
    )
        if response.data:
            logger.info(f"Loaded {len(response.data)} messages for session {user_id}")
            return [{"role": r["role"], "content": r["content"]} for r in response.data]
        else:
            logger.warning(f"Failed to load history")
            return []
    except Exception as e:
        logger.error(f"Error loading history: {e}")
        return []
    
def clear_history(user_id: str) -> None:
    try:
        supabase = get_supabase()
        supabase.table("chat_history").delete().eq("user_id", user_id).execute()
        logger.info(f"Cleared history for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to clear history: {e}")