from groq import Groq
from sentence_transformers import SentenceTransformer
import logging
from config import EMBEDDING_MODEL, LANGUAGE_MODEL, SUPABASE_DB_URL, RERANKING_MODEL , GROQ_API_KEY, COLLECTION_NAME
from flashrank import Ranker, RerankRequest
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

class RAGChatBot:
    def __init__(self, embedding_model=EMBEDDING_MODEL, language_model=LANGUAGE_MODEL):
        self.embedding_model = SentenceTransformer(embedding_model)
        
        test_embedding = self.embedding_model.encode("test")
        embedding_dimension = len(test_embedding)
        
        self.vx=vecs.create_client(SUPABASE_DB_URL)
        self.collection=self.vx.get_or_create_collection(
            name=COLLECTION_NAME,
            dimension=embedding_dimension
        )
        self.groq=Groq(api_key=GROQ_API_KEY)
        self.language_model = language_model
        self.chat_history: list[dict] = []
        self.ranker=Ranker(model_name=RERANKING_MODEL, cache_dir="/tmp/flashrank")

    def _build_messages(self, query: str, context: str) -> list[dict]:
        system = {
            "role": "system",
            "content": RAG_PROMPT_TEMPLATE.format(context=context, question=query)
        }
        return [system, *self.chat_history, {"role": "user", "content": query}]

    def _retrieve_context(self, query: str, user_id: str, k: int = 3):

        emb_query=self.embedding_model.encode(query)
        results=self.collection.query(
            data=emb_query,
            limit=k*3,
            filters={"user_id": {"$eq": user_id}},
            include_metadata=True,
            include_value=False
        )        
        passages = [
        {"id": i, "text": meta["content"], "meta": meta}
        for i, (_, meta) in enumerate(results)
        ]
        
        rerank_request = RerankRequest(query=query, passages=passages)
        try:
            results = self.ranker.rerank(rerank_request)
        except Exception as e:
            logger.warning(f"Reranking failed: {e}. Using original order.")
            results = passages[:k*3] 
        
        top_k = results[:k]
        
        context = "\n\n---\n\n".join([r['text'] for r in top_k])
        sources = list({
            f"{r['meta'].get('source', 'unknown')} (page {r['meta'].get('page', '?')})"
            for r in top_k
        })
        
        return context, sources

    def ask(self, query: str, user_id: str, k: int = 3):
        context, sources = self._retrieve_context(query, user_id, k)
        messages = self._build_messages(query, context)

        response = self.groq.chat.completions.create(
            model=self.language_model,
            messages=messages,
            stream=True,
            max_tokens=1024
        )

        answer = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                answer += token
            

        self.chat_history.append({"role": "user", "content": query})
        self.chat_history.append({"role": "assistant", "content": answer})
        return answer, sources
    
    def clear_history(self):
        self.chat_history.clear()

def main():

    chatbot = RAGChatBot()
    user_id = "test_user"  
    print("RAG Chatbot ready. Type 'quit' to exit, 'clear' to reset memory.\n")
    try:
        while True:
            query_text = input("\nAsk a question about the file: ")
            if query_text.lower() == "quit":
                print("Goodbye!")
                break
            elif query_text.lower() == "clear":
                chatbot.clear_history()
                print("Chat history cleared.")
                continue

            answer, sources = chatbot.ask(query_text, user_id=user_id, k=3)
            print(f"\nAnswer:\n{answer}")
            print(f"Sources: {', '.join(sources)}")
    finally:
        chatbot.vx.disconnect()
if __name__ == "__main__":
    main()