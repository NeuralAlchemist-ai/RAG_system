from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.documents import router as upload_router
from api.routes.chat import router as chat_router
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Pre-loading models...")
    from src.query_data import _embedding_model
    print("Models ready.")
    yield
    print("Shutting down.")

app = FastAPI(title="RAG API", version="1.0.0", lifespan=lifespan)

app.include_router(upload_router)
app.include_router(chat_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
