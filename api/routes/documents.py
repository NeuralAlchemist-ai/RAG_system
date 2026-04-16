import os
import uuid
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
from api.dependencies import get_current_user
from src.create_database import RAGDatabase

router = APIRouter(prefix="/api/v1/upload", tags=["upload"])

ALLOWED_FILE_TYPES = ["application/pdf", "text/plain", "text/markdown"]
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/document/")
async def upload_document(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    user_id = str(current_user.id)
    return await _process_file(file, user_id)


@router.post("/documents/")
async def upload_documents(files: List[UploadFile] = File(...), current_user: dict = Depends(get_current_user)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    user_id = str(current_user.id)

    results = []
    errors  = []

    for file in files:
        try:
            result = await _process_file(file, user_id)
            results.append(result)
        except HTTPException as e:
            errors.append({
                "filename": file.filename,
                "error": e.detail
            })

    return {
        "user_id":        user_id,
        "uploaded":       len(results),
        "failed":         len(errors),
        "files":          results,
        "errors":         errors
    }


async def _process_file(file: UploadFile, user_id: str | None) -> dict:
    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=400, detail=f"{file.filename}: Unsupported file type.")

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"{file.filename}: Exceeds 10MB limit.")

    ext     = "." + file.filename.split(".")[-1]
    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        rag_db = RAGDatabase()
        chunks = rag_db.build(tmp_path, user_id, original_file_name=file.filename)

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return {
        "message":       f"'{file.filename}' uploaded successfully.",
        "filename":      file.filename,
        "user_id":       user_id,
        "chunks_created": chunks
    }


@router.get("/documents/")
async def list_documents(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user.id)
    db = RAGDatabase()
    results = db.collection.query(
        data=[0.0] * 384,
        limit=1000,
        filters={"user_id": {"$eq": user_id}},
        include_metadata=True,
        include_value=False
    )
    sources = list({meta.get("source", "unknown") for _, meta in results})
    db.vx.disconnect()
    return {"user_id": user_id, "documents": sources}


@router.delete("/documents/")
async def delete_documents(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user.id)
    db = RAGDatabase()
    db.collection.delete(filters={"user_id": {"$eq": user_id}})
    db.vx.disconnect()
    return {"message": f"All documents deleted for user {user_id}"}
