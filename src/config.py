# config.py
import os
import dotenv
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data")

EMBEDDING_MODEL = "nomic-embed-text"
LANGUAGE_MODEL =  "llama3.2:3b" 
RERANKING_MODEL = "ms-marco-MiniLM-L-6-v2"

SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")