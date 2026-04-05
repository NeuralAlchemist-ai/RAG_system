import os
import shutil
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma 
from langchain_ollama import OllamaEmbeddings

DATA_PATH = "../data/"
CHROMA_DB_PATH = "../db/chroma_db"
EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'

def main():
    generate_data()

def generate_data():
    docs=load_document(DATA_PATH)
    chunks=split_documents(docs)
    save_to_db(chunks)

def load_document(DATA_PATH):
    loader = DirectoryLoader(DATA_PATH, glob="*.pdf", loader_cls=PyPDFLoader)
    docs = loader.load()
    return docs

def split_documents(docs):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=100,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(docs)
    print(f"Split {len(docs)} documents into {len(chunks)} chunks.")

    return chunks
def save_to_db(chunks):
    if os.path.exists(CHROMA_DB_PATH):
        shutil.rmtree(CHROMA_DB_PATH)

    embedding = OllamaEmbeddings(model=EMBEDDING_MODEL)
    db=Chroma.from_documents(chunks,embedding=embedding,persist_directory=CHROMA_DB_PATH)
    print(f"Saved {len(chunks)} chunks to ChromaDB at {CHROMA_DB_PATH}.")


if __name__ == "__main__":
    main()