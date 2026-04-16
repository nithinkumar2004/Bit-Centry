"""
Bidder API routes — Upload documents, parse via OCR, extract structured data.
"""
import logging
from datetime import datetime
from typing import List

from bson import ObjectId
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from backend.db.mongodb import Database
from backend.services.ocr import OCRService
from backend.services.audit import AuditService
from backend.utils.file_handler import save_uploaded_file, detect_file_type
from backend.utils.extractors import extract_all_data

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/bidders", tags=["bidders"])


@router.post("/upload")
async def upload_bidder(
    name: str = Form(...),
    tender_id: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """Upload bidder documents (multiple files), parse via OCR, extract structured data."""

    # Verify tender exists
    tender_col = Database.get_collection("tenders")
    try:
        tender = await tender_col.find_one({"_id": ObjectId(tender_id)})
    except Exception:
        raise HTTPException(400, "Invalid tender ID")

    if not tender:
        raise HTTPException(404, "Tender not found")

    # Process all files
    documents = []
    all_text = []
    total_confidence = 0.0

    for file in files:
        file_type = detect_file_type(file.filename)
        if file_type == "unknown":
            continue

        content = await file.read()
        file_path, file_hash = save_uploaded_file(content, file.filename, "bidders")

        # OCR extraction
        text, confidence = OCRService.extract_text(file_path)
        
        documents.append({
            "filename": file.filename,
            "file_path": file_path,
            "file_hash": file_hash,
            "file_type": file_type,
            "ocr_confidence": round(confidence, 3),
            "extracted_text": text[:5000] if text else ""  # Store first 5000 chars per doc
        })

        if text:
            all_text.append(text)
            total_confidence += confidence

    if not documents:
        raise HTTPException(400, "No valid files uploaded. Use PDF or image files.")

    # Combine all text and extract structured data
    combined_text = "\n\n".join(all_text)
    extracted_data = extract_all_data(combined_text)
    avg_confidence = total_confidence / len(documents) if documents else 0.0

    extracted_data["raw_text"] = combined_text[:10000]  # Store first 10k chars
    extracted_data["confidence"] = round(avg_confidence, 3)

    # Create bidder document
    bidder_doc = {
        "name": name,
        "tender_id": tender_id,
        "documents": documents,
        "extracted_data": extracted_data,
        "status": "parsed",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    collection = Database.get_collection("bidders")
    result = await collection.insert_one(bidder_doc)
    bidder_id = str(result.inserted_id)

    # Audit log
    await AuditService.log_action(
        action="UPLOAD",
        entity_type="bidder",
        entity_id=bidder_id,
        input_data={
            "name": name,
            "tender_id": tender_id,
            "file_count": len(documents),
            "file_hashes": [d["file_hash"] for d in documents]
        },
        output_data={
            "bidder_id": bidder_id,
            "extracted_data": {
                "turnover": extracted_data.get("turnover"),
                "certifications": extracted_data.get("certifications"),
                "project_count": extracted_data.get("project_count"),
                "confidence": extracted_data.get("confidence")
            }
        }
    )

    return {
        "id": bidder_id,
        "name": name,
        "tender_id": tender_id,
        "documents_count": len(documents),
        "extracted_data": {
            "turnover": extracted_data.get("turnover"),
            "certifications": extracted_data.get("certifications", []),
            "project_count": extracted_data.get("project_count"),
            "confidence": extracted_data.get("confidence", 0)
        },
        "status": "parsed",
        "low_confidence": avg_confidence < 0.7,
        "message": "Bidder documents uploaded and parsed successfully."
    }


@router.get("")
async def list_bidders(tender_id: str = None, skip: int = 0, limit: int = 50):
    """List all bidders, optionally filtered by tender."""
    collection = Database.get_collection("bidders")
    
    query = {}
    if tender_id:
        query["tender_id"] = tender_id

    cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
    bidders = []
    async for doc in cursor:
        ed = doc.get("extracted_data", {})
        bidders.append({
            "id": str(doc["_id"]),
            "name": doc.get("name", ""),
            "tender_id": doc.get("tender_id", ""),
            "documents_count": len(doc.get("documents", [])),
            "turnover": ed.get("turnover"),
            "certifications": ed.get("certifications", []),
            "project_count": ed.get("project_count"),
            "confidence": ed.get("confidence", 0),
            "status": doc.get("status", "unknown"),
            "created_at": doc.get("created_at", "").isoformat() if doc.get("created_at") else "",
        })

    total = await collection.count_documents(query)
    return {"bidders": bidders, "total": total}


@router.get("/{bidder_id}")
async def get_bidder(bidder_id: str):
    """Get full bidder details including extracted data."""
    collection = Database.get_collection("bidders")
    
    try:
        bidder = await collection.find_one({"_id": ObjectId(bidder_id)})
    except Exception:
        raise HTTPException(400, "Invalid bidder ID")

    if not bidder:
        raise HTTPException(404, "Bidder not found")

    docs = []
    for d in bidder.get("documents", []):
        docs.append({
            "filename": d.get("filename", ""),
            "file_type": d.get("file_type", ""),
            "ocr_confidence": d.get("ocr_confidence", 0),
            "file_hash": d.get("file_hash", "")
        })

    return {
        "id": str(bidder["_id"]),
        "name": bidder.get("name", ""),
        "tender_id": bidder.get("tender_id", ""),
        "documents": docs,
        "extracted_data": bidder.get("extracted_data", {}),
        "status": bidder.get("status", "unknown"),
        "created_at": bidder.get("created_at", "").isoformat() if bidder.get("created_at") else "",
        "updated_at": bidder.get("updated_at", "").isoformat() if bidder.get("updated_at") else "",
    }


@router.delete("/{bidder_id}")
async def delete_bidder(bidder_id: str):
    """Delete a bidder."""
    collection = Database.get_collection("bidders")
    
    try:
        result = await collection.delete_one({"_id": ObjectId(bidder_id)})
    except Exception:
        raise HTTPException(400, "Invalid bidder ID")

    if result.deleted_count == 0:
        raise HTTPException(404, "Bidder not found")

    await AuditService.log_action(
        action="DELETE",
        entity_type="bidder",
        entity_id=bidder_id,
        details={"deleted": True}
    )

    return {"message": "Bidder deleted", "id": bidder_id}
