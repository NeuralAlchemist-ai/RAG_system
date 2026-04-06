# config.py
import os
import dotenv
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data")

EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'
LANGUAGE_MODEL = 'hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF'
RERANKING_MODEL = "ms-marco-MiniLM-L-12-v2"


SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")