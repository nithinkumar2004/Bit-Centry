"""
Pydantic models for Audit logging.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class AuditLog(BaseModel):
    """Immutable audit log entry with hash chain."""
    id: str
    action: str = Field(..., description="Action performed: UPLOAD, EXTRACT, PARSE, EVALUATE, EXPORT")
    entity_type: str = Field(..., description="Entity type: tender, bidder, evaluation")
    entity_id: str = Field(..., description="ID of the affected entity")
    input_hash: str = Field(..., description="SHA-256 hash of input data")
    output_hash: str = Field(..., description="SHA-256 hash of output data")
    prev_hash: str = Field(default="GENESIS", description="Hash of the previous audit log entry")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AuditLogResponse(BaseModel):
    """Response model for audit log entries."""
    logs: list[AuditLog]
    total: int
    chain_valid: Optional[bool] = None
