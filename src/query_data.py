import argparse
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
import ollama
import logging
from config import CHROMA_DB_PATH, EMBEDDING_MODEL, LANGUAGE_MODEL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """You are a helpful assistant. Answer using ONLY the context below.
If the answer isn't in the context, say you don't know. Do not make anything up.

Context:
{context}
"""
class RAGChatBot:
    def __init__(self, db_path=CHROMA_DB_PATH, embedding_model=EMBEDDING_MODEL, language_model=LANGUAGE_MODEL):
        self.embedding_model = OllamaEmbeddings(model=embedding_model)
        self.language_model = language_model
        self.db = Chroma(persist_directory=db_path, embedding_function=self.embedding_model)
        self.chat_history: list[dict] = []

    def _retrieve_context(self, query, k=3):
        results = self.db.similarity_search(query, k=k)
        context_text = "\n\n---\n\n".join([doc.page_content for doc in results])
        sources = list({
            f"{doc.metadata.get('source', 'unknown')} (page {doc.metadata.get('page', '?')})"
            for doc in results
        })
        return context_text, sources

    def _build_messages(self, query: str, context: str) -> list[dict]:
        system = {"role": "system", "content": PROMPT_TEMPLATE.format(context=context)}
        return [system, *self.chat_history, {"role": "user", "content": query}]

    def ask(self, query, k):
        context, sources = self._retrieve_context(query)
        messages = self._build_messages(query, context) 

        response = ollama.chat(model=self.language_model, messages=messages, stream=True)

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
    parser = argparse.ArgumentParser(description="RAG Chatbot")
    parser.add_argument("--k", type=int, default=3)
    args = parser.parse_args()

    chatbot = RAGChatBot()
    print("RAG Chatbot ready. Type 'quit' to exit, 'clear' to reset memory.\n")

    while True:
        query_text = input("\nAsk a question about the file: ")
        if query_text.lower() == "quit":
            print("Goodbye!")
            break
        elif query_text.lower() == "clear":
            chatbot.clear_history()
            print("Chat history cleared.")
            continue

        answer, sources = chatbot.ask(query_text, k=args.k)
        print(f"\nAnswer:\n{answer}")
        print(f"Sources: {', '.join(sources)}")

if __name__ == "__main__":
    main()