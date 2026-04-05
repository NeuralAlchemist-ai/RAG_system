import os
import shutil
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from config import CHROMA_DB_PATH, EMBEDDING_MODEL, DATA_PATH
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGDatabase:
    def __init__(self, data_path=DATA_PATH, db_path=CHROMA_DB_PATH, embedding_model=EMBEDDING_MODEL,format="pdf"):
        self.data_path = data_path
        self.db_path = db_path
        self.embedding_model = OllamaEmbeddings(model=embedding_model)
        self.format = format
        self.loaders={
            "pdf": PyPDFLoader,
            "txt": TextLoader,
            "md": UnstructuredMarkdownLoader
        }

    def build(self):
        docs=self._load_document()
        chunks=self._split_documents(docs)
        self._save_to_db(chunks)

    def _load_document(self):
        loader = DirectoryLoader(self.data_path, glob=f"*.{self.format}", loader_cls=self.loaders.get(self.format))
        docs = loader.load()
        return docs

    def _split_documents(self, docs):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=100,
            length_function=len,
            add_start_index=True,
        )
        chunks = text_splitter.split_documents(docs)
        logger.info(f"Split {len(docs)} documents into {len(chunks)} chunks.")
        return chunks
    
    def _save_to_db(self, chunks):
        if os.path.exists(self.db_path):
            shutil.rmtree(self.db_path)

        db=Chroma.from_documents(chunks,embedding=self.embedding_model,persist_directory=self.db_path)
        logger.info(f"Saved {len(chunks)} chunks to ChromaDB at {self.db_path}.")


if __name__ == "__main__":
    RAGDatabase().build()