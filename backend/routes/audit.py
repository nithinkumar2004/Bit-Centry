"""
Audit API routes — View audit logs and verify chain integrity.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Query

from backend.services.audit import AuditService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("")
async def list_audit_logs(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200)
):
    """List audit logs with optional filtering."""
    logs = await AuditService.get_logs(
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
        skip=skip
    )
    total = await AuditService.get_total_count(
        entity_type=entity_type,
        entity_id=entity_id
    )

    return {
        "logs": logs,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/verify")
async def verify_chain():
    """Verify the integrity of the audit log hash chain."""
    result = await AuditService.verify_chain()
    return result


@router.get("/{entity_type}/{entity_id}")
async def get_entity_logs(entity_type: str, entity_id: str):
    """Get audit logs for a specific entity."""
    logs = await AuditService.get_logs(
        entity_type=entity_type,
        entity_id=entity_id
    )
    total = await AuditService.get_total_count(
        entity_type=entity_type,
        entity_id=entity_id
    )

    return {
        "logs": logs,
        "total": total,
        "entity_type": entity_type,
        "entity_id": entity_id
    }
