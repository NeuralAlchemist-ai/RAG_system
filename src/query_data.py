import argparse
from httpcore import stream
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
import ollama

CHROMA_DB_PATH = "../db/chroma_db"
EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'
LANGUAGE_MODEL = 'hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF'

PROMPT_TEMPLATE = """You are a helpful chatbot.
Use only the following pieces of context to answer the question and stay within the bounds of the provided information. Don't make up any new information:
{context}
If you don't know the answer, say you don't know. Always use all the relevant information from the provided context to answer the question."""

def main():
    query_text = input("\nAsk a question about the file: ")
    
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    db = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=embeddings)
    
    results = db.similarity_search(query_text, k=3)
    context_text = "\n\n---\n\n".join([doc.page_content for doc in results])
    
    full_prompt = PROMPT_TEMPLATE.format(context=context_text)

    print("\nResponse:")
    response = ollama.chat(
        model=LANGUAGE_MODEL,
        messages=[
            {"role": "system", "content": full_prompt},
            {"role": "user", "content": query_text},
        ],
        stream=True,
    )

    for chunk in response:
        print(chunk["message"]["content"], end="", flush=True)
    print()

if __name__ == "__main__":
    main()