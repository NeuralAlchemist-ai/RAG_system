# config.py
import os
import dotenv
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data")

EMBEDDING_MODEL  = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "rag_collection_v2"
LANGUAGE_MODEL   = "llama-3.1-8b-instant"
GROQ_API_KEY     = os.getenv("GROQ_API_KEY")

SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")