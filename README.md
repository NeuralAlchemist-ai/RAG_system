# 📄 RAG System — AI-Powered Document Q&A

> A production-ready Retrieval-Augmented Generation (RAG) system that lets users upload documents and chat with them using state-of-the-art AI. Built with a full cloud stack: FastAPI backend, Streamlit frontend, Supabase vector database, and Groq LLM inference.

🔗 **Live Demo:** [rag-system.streamlit.app](https://ragsystem-hcnze3owqbpdydx8jmpwlx.streamlit.app)  
🔗 **API Docs:** [rag-system.onrender.com/docs](https://rag-system.onrender.com/docs)

---

## 🏗️ Architecture

```
User → Streamlit Cloud (Frontend)
              ↓
       Render (FastAPI Backend)
         ↙           ↘
Supabase pgvector    Groq API
(Vector Store)       (LLM Inference)
```

**Why this architecture matters:**
- Stateless backend — horizontally scalable
- Vector DB separated from application logic
- LLM inference offloaded to specialized hardware (Groq)
- Frontend and backend independently deployable

---

## 🧠 How It Works

### 1. Document Ingestion Pipeline
```
PDF/TXT/MD upload
      ↓
Text extraction (PDFMiner)
      ↓
Recursive chunking (700 tokens, 100 overlap)
      ↓
Embedding generation (BAAI/bge-small-en-v1.5 via FastEmbed)
      ↓
Vector storage (Supabase pgvector) with user_id metadata
```

### 2. Retrieval Pipeline
```
User question
      ↓
Embed query (same model as ingestion)
      ↓
ANN search — top 15 candidates (Supabase ivfflat index)
      ↓
LLM Reranking (Groq llama-3.1-8b-instant)
      ↓
Top 3 most relevant chunks → context window
      ↓
Answer generation (Groq) with source citations
```

---

## 🔑 Key Technical Decisions

| Decision | Choice | Why |
|---|---|---|
| Vector DB | Supabase pgvector | Free tier, SQL filtering, no extra infra |
| Embeddings | FastEmbed bge-small | No PyTorch dependency, runs on 512MB RAM |
| LLM | Groq llama-3.1-8b | 10x faster than local inference, free tier |
| Reranking | Groq LLM | Eliminates heavy cross-encoder model |
| Backend | FastAPI | Async, auto-docs, production-ready |
| Frontend | Streamlit | Fast iteration, AI-native UI |

---

## 🚀 Features

- **Multi-document support** — upload multiple files, all searchable together
- **Conversational memory** — chat history maintained per session
- **Source citations** — every answer shows which document and page it came from
- **Per-user isolation** — each user's documents are stored separately via `user_id` filtering
- **Multi-format support** — PDF, TXT, Markdown
- **Groq-powered reranking** — two-stage retrieval for higher answer accuracy
- **Streaming responses** — token-by-token output for better UX
- **RESTful API** — fully documented at `/docs`, ready for integration

---

## 📁 Project Structure

```
RAG_system/
├── api/                      # FastAPI application
│   ├── main.py               # App entrypoint, lifespan, CORS
│   ├── schemas.py            # Pydantic request/response models
│   └── routes/
│       ├── chat.py           # POST /chat, DELETE /chat/{session_id}
│       └── documents.py      # POST /upload, GET/DELETE /documents
├── src/                      # Core RAG logic
│   ├── config.py             # Centralized configuration
│   ├── create_database.py    # Document ingestion pipeline
│   └── query_data.py         # RAGChatBot — retrieval + generation
├── streamlit_app.py          # Frontend
├── render.yaml               # Render deployment config
├── pyproject.toml            # Dependencies (uv)
└── requirements.txt          # Streamlit Cloud dependencies
```

---

## 🛠️ Tech Stack

**Backend**
- Python 3.13
- FastAPI + Uvicorn
- LangChain (document loading, text splitting)
- FastEmbed (lightweight embeddings, no PyTorch)
- Vecs (Supabase vector client)
- Groq SDK

**Infrastructure**
- Render (FastAPI backend)
- Streamlit Cloud (frontend)
- Supabase (PostgreSQL + pgvector)
- Groq (LLM inference — llama-3.1-8b-instant)

**Package Management**
- uv (10x faster than pip)

---

## ⚙️ API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/upload/document/` | Upload single document |
| `POST` | `/api/v1/upload/documents/` | Upload multiple documents |
| `GET` | `/api/v1/upload/documents/` | List user's documents |
| `DELETE` | `/api/v1/upload/documents/{user_id}` | Delete user's documents |
| `POST` | `/api/v1/chat/` | Ask a question |
| `DELETE` | `/api/v1/chat/{session_id}` | Clear conversation history |

Full interactive documentation: `https://your-api.onrender.com/docs`

---

## 🏃 Run Locally

### Prerequisites
- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com/) (optional — for local LLM)
- Supabase account (free)
- Groq API key (free)

### Setup

```bash
# clone
git clone https://github.com/NeuralAlchemist-ai/RAG_system.git
cd RAG_system

# install dependencies
uv sync

# create .env
cp .env.example .env
# fill in your keys
```

### `.env` file
```env
GROQ_API_KEY=your_groq_key
SUPABASE_DB_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
COLLECTION_NAME=rag_collection
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
LANGUAGE_MODEL=llama-3.1-8b-instant
```

### Run

```bash
# start backend
uvicorn api.main:app --reload

# start frontend (new terminal)
streamlit run streamlit_app.py
```

### Supabase Setup

Run this in Supabase SQL Editor:

```sql
create extension if not exists vector;

create table documents (
    id         bigserial primary key,
    content    text,
    metadata   jsonb,
    embedding  vector(384),
    user_id    text not null,
    created_at timestamp default now()
);

create index on documents using ivfflat (embedding vector_cosine_ops) with (lists = 100);
create index on documents (user_id);
```

---

## 🧪 What I Learned Building This

- **RAG pipeline design** — chunking strategy, embedding model selection, retrieval quality tradeoffs
- **Vector databases** — pgvector indexing, ANN search, metadata filtering
- **Reranking** — two-stage retrieval (ANN → LLM rerank) for higher accuracy
- **Cloud deployment** — stateless API design, cold start optimization, memory constraints on free tier
- **Production tradeoffs** — replaced PyTorch-based models with FastEmbed to fit 512MB RAM limit
- **Multi-user isolation** — per-user vector filtering with metadata

---

## 📈 Future Improvements

- [done] Conversation history persistence in database
- [done] Evaluation dashboard with semantic similarity scores
- [ ] Highlighting document sources
- [ ] Docker containerization

---

## 👤 Author

**Tsimur** — AI Engineering student, Year 2  
[GitHub](https://github.com/NeuralAlchemist-ai)
