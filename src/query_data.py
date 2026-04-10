from groq import Groq
from fastembed import TextEmbedding
import logging
import json
from src.config import EMBEDDING_MODEL, SUPABASE_DB_URL, GROQ_API_KEY, COLLECTION_NAME , LANGUAGE_MODEL
import vecs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RAG_PROMPT_TEMPLATE = """
You are a specialized AI assistant. Your answer must be based STRICTLY on the provided context.

CONTEXT (most relevant excerpts):
{context}

QUESTION:
{question}

RULES:
1. Use ONLY the context provided above. Do not add any external knowledge.
2. If the context contains the answer, you MUST provide it. Only say you don't know 
   if after careful reading the answer is truly absent.
3. Be concise and precise. If asked for a number or date, state it directly.
4. Never contradict yourself — do not say information is missing if you then quote it.
5. Always respond in the same language the question was asked in.

ANSWER:"""

RERANK_PROMPT = """You are a relevance ranking assistant.
Given a question and a list of text passages, return a JSON array of passage indices 
sorted from MOST to LEAST relevant to the question.
Return ONLY a valid JSON array of integers like [2, 0, 4, 1, 3]. Nothing else.

Question: {question}

Passages:
{passages}

JSON array:"""

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
            dimension=self.embedding_model.get_sentence_embedding_dimension()
        )

    def _rerank(self, query: str, passages: list[dict], k: int) -> list[dict]:
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
            return reranked[:k]

        except Exception as e:
            logger.warning(f"Groq reranking failed: {e}. Using original order.")
            return passages[:k]  

    def _build_messages(self, query: str, context: str) -> list[dict]:
        system = {
            "role": "system",
            "content": RAG_PROMPT_TEMPLATE.format(context=context, question=query)
        }
        return [system, *self.chat_history, {"role": "user", "content": query}]

    def _retrieve_context(self, query: str, user_id: str, k: int = 3):
        emb_query = self.embedding_model.encode(query)

        results = self.collection.query(
            data=emb_query,
            limit=k * 5,
            filters={"user_id": {"$eq": user_id}},
            include_metadata=True,
            include_value=False
        )

        passages = [
            {"id": i, "text": meta["content"], "meta": meta}
            for i, (_, meta) in enumerate(results)
        ]

        top_k = self._rerank(query, passages, k)

        context = "\n\n---\n\n".join([r["text"] for r in top_k])
        sources = list({
            f"{r['meta'].get('source', 'unknown')} (page {r['meta'].get('page', '?')})"
            for r in top_k
        })

        return context, sources

    def ask(self, query: str, user_id: str, k: int = 3) -> tuple[str, list]:
        context, sources = self._retrieve_context(query, user_id, k)
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
        return answer, sources

    def clear_history(self):
        self.chat_history.clear()