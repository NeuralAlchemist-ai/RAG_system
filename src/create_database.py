from langchain_community.document_loaders import DirectoryLoader, PDFMinerLoader, TextLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import vecs
from src.config import EMBEDDING_MODEL, DATA_PATH, SUPABASE_DB_URL, COLLECTION_NAME
import logging
import os
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_embedding_model = SentenceTransformer(EMBEDDING_MODEL)

class RAGDatabase:
    def __init__(self, data_path=DATA_PATH, embedding_model=EMBEDDING_MODEL,format="pdf"):
        self.data_path = data_path
        self.embedding_model = _embedding_model        
        test_embedding = self.embedding_model.encode("test")
        embedding_dimension = len(test_embedding)
        
        self.vx=vecs.create_client(SUPABASE_DB_URL)
        self.collection=self.vx.get_or_create_collection(
            name=COLLECTION_NAME,
            dimension=embedding_dimension
        )
        self.format = format
        self.loaders={
            "pdf": PDFMinerLoader,
            "txt": TextLoader,
            "md": UnstructuredMarkdownLoader
        }

    def build(self, file_path: str | None = None, user_id: str | None = None, original_file_name: str | None = None):
        if file_path:
            self.data_path = file_path
            self.format = os.path.splitext(file_path)[1].lstrip(".").lower()

        docs = self._load_document()
        chunks = self._split_documents(docs)
        self._save_to_db(chunks, user_id=user_id,original_file_name=original_file_name)
        self.vx.disconnect()
        return len(chunks)

    def _load_document(self):
        if os.path.isfile(self.data_path):
            loader_cls = self.loaders.get(self.format)
            if loader_cls is None:
                raise ValueError(f"Unsupported file format: {self.format}")
            loader = loader_cls(self.data_path)
        else:
            loader = DirectoryLoader(self.data_path, glob=f"*.{self.format}", loader_cls=self.loaders.get(self.format))
        docs = loader.load()
        return docs

    def _split_documents(self, docs):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size = 500,
            chunk_overlap=100,
            length_function=len,
            add_start_index=True,
        )
        chunks = text_splitter.split_documents(docs)
        logger.info(f"Split {len(docs)} documents into {len(chunks)} chunks.")
        return chunks
    
    def _save_to_db(self, chunks, user_id: str | None = None, original_file_name: str | None = None):
        records=[]
        for chunk in chunks:
            embedding = self.embedding_model.encode(chunk.page_content)
            records.append((
                f"chunk_{uuid.uuid4()}",      
                embedding,          
                {
                    "content":  chunk.page_content,
                    "source":   original_file_name or chunk.metadata.get("source", "unknown"),
                    "page":     chunk.metadata.get("page", 0),
                    "user_id":  user_id,
                }
            ))
        batch_size=100
        for i in range(0, len(records), batch_size):
            batch=records[i:i+batch_size]
            self.collection.upsert(records=batch)
            logger.info(f"Uploaded {min(i + batch_size, len(records))}/{len(chunks)} chunks")
        
        logger.info(f"Saved {len(chunks)} chunks to the database.")
        try:
            self.collection.create_index()
        except Exception:
            pass
    
if __name__ == "__main__":
    RAGDatabase().build()