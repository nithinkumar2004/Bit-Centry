"""
Pydantic models for Tender documents.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Criterion(BaseModel):
    """A single eligibility criterion extracted from a tender."""
    id: str = Field(..., description="Unique criterion identifier (e.g., C1, C2)")
    type: str = Field(..., description="Category: financial, technical, or compliance")
    description: str = Field(..., description="Human-readable criterion description")
    mandatory: bool = Field(default=True, description="Whether this criterion is mandatory")
    threshold: Optional[float] = Field(default=None, description="Numeric threshold if applicable")
    unit: Optional[str] = Field(default=None, description="Unit of measurement (e.g., crore, count)")


class TenderCreate(BaseModel):
    """Request model for creating a tender (used with file upload)."""
    title: str = Field(..., description="Tender title")


class TenderResponse(BaseModel):
    """Response model for tender data."""
    id: str
    title: str
    raw_text: Optional[str] = None
    criteria: List[Criterion] = []
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    status: str = "uploaded"  # uploaded, extracting, ready, error
    ocr_confidence: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class TenderListResponse(BaseModel):
    """Response model for listing tenders."""
    tenders: List[TenderResponse]
    total: int
