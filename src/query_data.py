from langchain_ollama import OllamaEmbeddings
import ollama
import logging
from config import EMBEDDING_MODEL, LANGUAGE_MODEL, SUPABASE_DB_URL, RERANKING_MODEL
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
        self.embedding_model = OllamaEmbeddings(model=embedding_model)
        self.vx=vecs.create_client(SUPABASE_DB_URL)
        self.collection=self.vx.get_or_create_collection(
            name="rag_collection",
            dimension=768
        )
        self.chat_history: list[dict] = []
        self.ranker=Ranker(model_name=RERANKING_MODEL, cache_dir="opt/flashrank")

    def _build_messages(self, query: str, context: str) -> list[dict]:
        system = {
            "role": "system",
            "content": RAG_PROMPT_TEMPLATE.format(context=context, question=query)
        }
        return [system, *self.chat_history, {"role": "user", "content": query}]

    def _retrieve_context(self, query: str, k: int = 3):

        emb_query=self.embedding_model.embed_query(query)
        results=self.collection.query(
            data=emb_query,
            limit=k*3,
            include_metadata=True,
            include_value=False
        )        
        passages = [
        {"id": i, "text": meta["content"], "meta": meta}
        for i, (_, meta) in enumerate(results)
        ]
        
        rerank_request = RerankRequest(query=query, passages=passages)
        results = self.ranker.rerank(rerank_request)
        
        top_3 = results[:3]
        
        context = "\n\n---\n\n".join([r['text'] for r in top_3])
        sources = list({
            f"{r['meta'].get('source', 'unknown')} (page {r['meta'].get('page', '?')})"
            for r in top_3
        })
        
        return context, sources

    def ask(self, query, k=3):
        context, sources = self._retrieve_context(query,k)
        messages = self._build_messages(query, context) 

        response = ollama.chat(model=LANGUAGE_MODEL, messages=messages, stream=True)

        answer = ""
        for chunk in response:
            token = chunk["message"]["content"]
            answer += token
            print(token, end="", flush=True)
        print()

        self.chat_history.append({"role": "user", "content": query})
        self.chat_history.append({"role": "assistant", "content": answer})
        return answer, sources
    
    def clear_history(self):
        self.chat_history.clear()

def main():

    chatbot = RAGChatBot()
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

            answer, sources = chatbot.ask(query_text, k=3)
            print(f"\nAnswer:\n{answer}")
            print(f"Sources: {', '.join(sources)}")
    finally:
        chatbot.vx.disconnect()
if __name__ == "__main__":
    main()