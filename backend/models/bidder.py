"""
Pydantic models for Bidder documents.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ExtractedData(BaseModel):
    """Data extracted from bidder documents via OCR + parsing."""
    turnover: Optional[float] = Field(default=None, description="Annual turnover in crores")
    certifications: List[str] = Field(default_factory=list, description="List of certifications (GST, ISO, PAN, etc.)")
    project_count: Optional[int] = Field(default=None, description="Number of completed projects")
    raw_text: Optional[str] = Field(default=None, description="Full extracted text")
    confidence: float = Field(default=0.0, description="OCR confidence score (0-1)")
    additional: Dict[str, Any] = Field(default_factory=dict, description="Additional extracted fields")


class BidderDocument(BaseModel):
    """Metadata for a single uploaded bidder document."""
    filename: str
    file_path: str
    file_hash: str
    file_type: str  # pdf, image
    ocr_confidence: float = 0.0
    extracted_text: Optional[str] = None


class BidderCreate(BaseModel):
    """Request model for creating a bidder."""
    name: str = Field(..., description="Bidder company name")
    tender_id: str = Field(..., description="Associated tender ID")


class BidderResponse(BaseModel):
    """Response model for bidder data."""
    id: str
    name: str
    tender_id: str
    documents: List[BidderDocument] = []
    extracted_data: Optional[ExtractedData] = None
    status: str = "uploaded"  # uploaded, parsing, parsed, error
    created_at: datetime
    updated_at: Optional[datetime] = None


class BidderListResponse(BaseModel):
    """Response model for listing bidders."""
    bidders: List[BidderResponse]
    total: int
