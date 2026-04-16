"""
Tender API routes — Upload, extract criteria, list, and manage tenders.
"""
import logging
from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from backend.db.mongodb import Database
from backend.services.ocr import OCRService
from backend.services.llm import LLMService
from backend.services.audit import AuditService
from backend.utils.file_handler import save_uploaded_file, detect_file_type

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tenders", tags=["tenders"])


@router.post("/upload")
async def upload_tender(
    title: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload a tender document (PDF or image) and extract text via OCR."""
    # Validate file type
    file_type = detect_file_type(file.filename)
    if file_type == "unknown":
        raise HTTPException(400, "Unsupported file type. Use PDF or image files.")

    # Read and save file
    content = await file.read()
    file_path, file_hash = save_uploaded_file(content, file.filename, "tenders")

    # Extract text via OCR
    raw_text, ocr_confidence = OCRService.extract_text(file_path)

    # Create tender document
    tender_doc = {
        "title": title,
        "raw_text": raw_text,
        "criteria": [],
        "file_path": file_path,
        "file_hash": file_hash,
        "file_type": file_type,
        "original_filename": file.filename,
        "status": "uploaded",
        "ocr_confidence": round(ocr_confidence, 3),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    collection = Database.get_collection("tenders")
    result = await collection.insert_one(tender_doc)
    tender_id = str(result.inserted_id)

    # Audit log
    await AuditService.log_action(
        action="UPLOAD",
        entity_type="tender",
        entity_id=tender_id,
        input_data={"filename": file.filename, "file_hash": file_hash},
        output_data={"tender_id": tender_id, "text_length": len(raw_text)},
        details={"ocr_confidence": ocr_confidence}
    )

    return {
        "id": tender_id,
        "title": title,
        "status": "uploaded",
        "ocr_confidence": round(ocr_confidence, 3),
        "text_preview": raw_text[:300] if raw_text else "",
        "message": "Tender uploaded successfully. Use /extract to extract criteria."
    }


@router.post("/{tender_id}/extract")
async def extract_criteria(tender_id: str):
    """Extract eligibility criteria from tender text using LLM."""
    collection = Database.get_collection("tenders")
    
    try:
        tender = await collection.find_one({"_id": ObjectId(tender_id)})
    except Exception:
        raise HTTPException(400, "Invalid tender ID")

    if not tender:
        raise HTTPException(404, "Tender not found")

    raw_text = tender.get("raw_text", "")
    if not raw_text:
        raise HTTPException(400, "No text available. The document may not have been processed correctly.")

    # Update status
    await collection.update_one(
        {"_id": ObjectId(tender_id)},
        {"$set": {"status": "extracting", "updated_at": datetime.utcnow()}}
    )

    # Extract criteria via LLM
    try:
        criteria = await LLMService.extract_criteria(raw_text)
    except Exception as e:
        await collection.update_one(
            {"_id": ObjectId(tender_id)},
            {"$set": {"status": "error", "updated_at": datetime.utcnow()}}
        )
        raise HTTPException(500, f"Criteria extraction failed: {str(e)}")

    # Update tender with criteria
    await collection.update_one(
        {"_id": ObjectId(tender_id)},
        {"$set": {
            "criteria": criteria,
            "status": "ready",
            "updated_at": datetime.utcnow()
        }}
    )

    # Audit log
    await AuditService.log_action(
        action="EXTRACT",
        entity_type="tender",
        entity_id=tender_id,
        input_data={"text_length": len(raw_text)},
        output_data={"criteria_count": len(criteria), "criteria": criteria}
    )

    return {
        "id": tender_id,
        "criteria": criteria,
        "count": len(criteria),
        "status": "ready"
    }


@router.get("")
async def list_tenders(skip: int = 0, limit: int = 50):
    """List all tenders."""
    collection = Database.get_collection("tenders")
    
    cursor = collection.find().sort("created_at", -1).skip(skip).limit(limit)
    tenders = []
    async for doc in cursor:
        tenders.append({
            "id": str(doc["_id"]),
            "title": doc.get("title", ""),
            "status": doc.get("status", "unknown"),
            "criteria_count": len(doc.get("criteria", [])),
            "ocr_confidence": doc.get("ocr_confidence", 0),
            "created_at": doc.get("created_at", "").isoformat() if doc.get("created_at") else "",
        })

    total = await collection.count_documents({})
    return {"tenders": tenders, "total": total}


@router.get("/{tender_id}")
async def get_tender(tender_id: str):
    """Get full tender details including criteria."""
    collection = Database.get_collection("tenders")
    
    try:
        tender = await collection.find_one({"_id": ObjectId(tender_id)})
    except Exception:
        raise HTTPException(400, "Invalid tender ID")

    if not tender:
        raise HTTPException(404, "Tender not found")

    # Get associated bidders count
    bidder_count = await Database.get_collection("bidders").count_documents(
        {"tender_id": tender_id}
    )

    return {
        "id": str(tender["_id"]),
        "title": tender.get("title", ""),
        "raw_text": tender.get("raw_text", ""),
        "criteria": tender.get("criteria", []),
        "status": tender.get("status", "unknown"),
        "ocr_confidence": tender.get("ocr_confidence", 0),
        "file_hash": tender.get("file_hash", ""),
        "original_filename": tender.get("original_filename", ""),
        "bidder_count": bidder_count,
        "created_at": tender.get("created_at", "").isoformat() if tender.get("created_at") else "",
        "updated_at": tender.get("updated_at", "").isoformat() if tender.get("updated_at") else "",
    }


@router.delete("/{tender_id}")
async def delete_tender(tender_id: str):
    """Delete a tender and its associated data."""
    collection = Database.get_collection("tenders")
    
    try:
        result = await collection.delete_one({"_id": ObjectId(tender_id)})
    except Exception:
        raise HTTPException(400, "Invalid tender ID")

    if result.deleted_count == 0:
        raise HTTPException(404, "Tender not found")

    # Audit log
    await AuditService.log_action(
        action="DELETE",
        entity_type="tender",
        entity_id=tender_id,
        details={"deleted": True}
    )

    return {"message": "Tender deleted", "id": tender_id}
