from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
import vecs
from config import EMBEDDING_MODEL, DATA_PATH, SUPABASE_DB_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGDatabase:
    def __init__(self, data_path=DATA_PATH, embedding_model=EMBEDDING_MODEL,format="pdf"):
        self.data_path = data_path
        self.vx=vecs.create_client(SUPABASE_DB_URL)
        self.collection=self.vx.get_or_create_collection(
            name="rag_collection",
            dimension=768
        )
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
        self.vx.disconnect()

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
        records=[]
        for i, chunk in enumerate(chunks):
            embedding = self.embedding_model.embed_query(chunk.page_content)
            records.append((
                f"chunk_{i}",      
                embedding,          
                {                   
                    "content":  chunk.page_content,
                    "source":   chunk.metadata.get("source", "unknown"),
                    "page":     chunk.metadata.get("page", 0),
                }
            ))
        batch_size=100
        for i in range(0, len(records), batch_size):
            batch=records[i:i+batch_size]
            self.collection.upsert(records=batch)
            logger.info(f"Uploaded {min(i + batch_size, len(records))}/{len(chunks)} chunks")
        
        logger.info(f"Saved {len(chunks)} chunks to the database.")
        self.collection.create_index()
    
if __name__ == "__main__":
    RAGDatabase().build()