from groq import Groq
from fastembed import TextEmbedding
import logging
import json
from src.config import EMBEDDING_MODEL, SUPABASE_DB_URL, GROQ_API_KEY, COLLECTION_NAME , LANGUAGE_MODEL, MAX_RERANK, MAX_RETRIEVE
import vecs
from src.history import clear_history,save_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RAG_PROMPT_TEMPLATE = """
You are a highly accurate AI assistant.

Answer the question using ONLY the provided context.

CONTEXT:
{context}

QUESTION:
{question}

INSTRUCTIONS:
1. Base your answer strictly on the context.
2. If the answer is partially available, provide the available information.
3. If the answer is completely missing, say: "I don't know based on the provided context."
4. Do NOT use external knowledge.
5. Be concise, factual, and direct.
6. If possible, quote or reference relevant parts of the context.
7. If multiple answers exist, list them clearly.
8. Always respond in the same language as the question.

ANSWER:
"""



RERANK_PROMPT = """You are a ranking system.

Task:
Rank the passages by relevance to the question.

Rules:
- Return ONLY a JSON array of indices
- No explanation, no text
- Must be valid JSON
- Highest relevance first

Question:
{question}

Passages:
{passages}

Output:
"""

_embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL)

class RAGChatBot:
    def __init__(self, language_model=LANGUAGE_MODEL):
        self.embedding_model = _embedding_model
        self.groq = Groq(api_key=GROQ_API_KEY)
        self.language_model = language_model
        self.chat_history: list[dict] = []

        self.vx = vecs.create_client(SUPABASE_DB_URL)
        self.collection = self.vx.get_or_create_collection(
            name=COLLECTION_NAME,
            dimension=len(list(self.embedding_model.embed(["test"]))[0])
        )

    def _rerank(self, query: str, passages: list[dict]):
        formatted = "\n\n".join([
            f"[{i}]: {p['text'][:300]}" 
            for i, p in enumerate(passages)
        ])

        try:
            response = self.groq.chat.completions.create(
                model=self.language_model,
                messages=[{
                    "role": "user",
                    "content": RERANK_PROMPT.format(
                        question=query,
                        passages=formatted
                    )
                }],
                max_tokens=100,  
                temperature=0.0   
            )

            raw = response.choices[0].message.content.strip()
            indices = json.loads(raw)

            reranked = [passages[i] for i in indices if i < len(passages)]
            return reranked[:MAX_RERANK]

        except Exception as e:
            logger.warning(f"Groq reranking failed: {e}. Using original order.")
            return passages[:MAX_RERANK]  

    def _build_messages(self, query: str, context: str) -> list[dict]:
        system = {
            "role": "system",
            "content": RAG_PROMPT_TEMPLATE.format(context=context, question=query)
        }
        return [system, *self.chat_history, {"role": "user", "content": query}]

    def _retrieve_context(self, query: str, user_id: str):
        emb_query = list(self.embedding_model.embed([query]))[0]

        results = self.collection.query(
            data=emb_query,
            limit=MAX_RETRIEVE,
            filters={"user_id": {"$eq": user_id}},
            include_metadata=True,
            include_value=True
        )

        passages = [
            {"id": i, "text": meta["content"], "score": score, "meta": meta}
            for i, (_, score, meta) in enumerate(results)
        ]

        top_k = self._rerank(query, passages)

        context = "\n\n---\n\n".join([r["text"] for r in top_k])
        sources = list({
            f"{r['meta'].get('source', 'unknown')} (page {r['meta'].get('page', '?')})"
            for r in top_k
        })

        return context, sources
    
    

    def ask(self, query: str, user_id: str):
        context, sources = self._retrieve_context(query, user_id)
        messages = self._build_messages(query, context)

        response = self.groq.chat.completions.create(
            model=self.language_model,
            messages=messages,
            max_tokens=1024,
            temperature=0.1
        )

        answer = response.choices[0].message.content

        self.chat_history.append({"role": "user", "content": query})
        self.chat_history.append({"role": "assistant", "content": answer})

        save_message(user_id=user_id, role="user", content=query)
        save_message(user_id=user_id, role="assistant", content=answer, sources=sources)

        return answer, sources

    def clear_history(self, user_id: str):
        self.chat_history.clear()
        clear_history(user_id=user_id)
