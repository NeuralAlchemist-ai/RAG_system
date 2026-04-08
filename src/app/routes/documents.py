import os
import uuid
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from create_database import RAGDatabase

router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_FILE_TYPES = ["application/pdf", "text/plain", "text/markdown"]
MAX_FILE_SIZE = 10 * 1024 * 1024 

@router.post("/document/")
async def upload_document(file: UploadFile = File(...),user_id: str = None):
    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    contents = await file.read()                  

    if len(contents) > MAX_FILE_SIZE:             
        raise HTTPException(status_code=413, detail="File size exceeds 10MB.")

    user_id = user_id or str(uuid.uuid4()) 

    ext = "." + file.filename.split(".")[-1]      
    tmp_path = None                               

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        rag_db = RAGDatabase()
        chunks = rag_db.build(tmp_path, user_id) 

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return {
        "message": f"File '{file.filename}' uploaded and processed successfully.",
        "user_id": user_id,        
        "chunks_created": chunks
    }


@router.get("/documents/")
async def list_documents(user_id: str):
    db = RAGDatabase()
    results = db.collection.query(
        data=[0.0] * 768,
        limit=1000,
        filters={"user_id": {"$eq": user_id}},
        include_metadata=True,
        include_value=False
    )
    sources = list({meta.get("source", "unknown") for _, meta in results})
    db.vx.disconnect()
    return {"user_id": user_id, "documents": sources}


@router.delete("/documents/{user_id}")
async def delete_documents(user_id: str):
    db = RAGDatabase()
    db.collection.delete(filters={"user_id": {"$eq": user_id}})
    db.vx.disconnect()
    return {"message": f"All documents deleted for user {user_id}"}