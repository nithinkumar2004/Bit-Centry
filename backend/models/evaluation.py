"""
Pydantic models for Evaluation results.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class CriterionResult(BaseModel):
    """Evaluation result for a single criterion."""
    criterion_id: str = Field(..., description="ID of the evaluated criterion")
    criterion_description: str = Field(default="", description="Description of the criterion")
    criterion_type: str = Field(default="", description="Type: financial, technical, compliance")
    extracted_value: Optional[str] = Field(default=None, description="Value extracted from bidder docs")
    threshold: Optional[str] = Field(default=None, description="Required threshold")
    decision: str = Field(..., description="Eligible, Not Eligible, or Needs Manual Review")
    confidence: float = Field(default=0.0, description="Confidence score (0-1)")
    explanation: str = Field(default="", description="Human-readable explanation")
    source_document: Optional[str] = Field(default=None, description="Source document filename")
    is_ambiguous: bool = Field(default=False, description="Whether this result is flagged as ambiguous")


class EvaluationResponse(BaseModel):
    """Response model for a complete evaluation."""
    id: str
    tender_id: str
    bidder_id: str
    bidder_name: str = ""
    results: List[CriterionResult] = []
    final_status: str = "Pending"  # Eligible, Not Eligible, Needs Manual Review, Pending
    overall_confidence: float = 0.0
    ambiguous_count: int = 0
    evaluated_at: datetime
    

class EvaluationListResponse(BaseModel):
    """Response model for listing evaluations."""
    evaluations: List[EvaluationResponse]
    total: int
    tender_title: str = ""
