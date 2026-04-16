"""
Audit Service — Tamper-evident audit logging with SHA-256 hash chain.
Every action creates an immutable log entry linked to the previous entry.
"""
import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from bson import ObjectId

logger = logging.getLogger(__name__)


class AuditService:
    """Service for creating and verifying immutable audit logs."""

    @staticmethod
    def _compute_hash(data: Any) -> str:
        """Compute SHA-256 hash of any serializable data."""
        if isinstance(data, (dict, list)):
            serialized = json.dumps(data, sort_keys=True, default=str)
        else:
            serialized = str(data)
        return hashlib.sha256(serialized.encode()).hexdigest()

    @staticmethod
    def _compute_entry_hash(entry: Dict[str, Any]) -> str:
        """Compute the hash for an audit log entry (used for chain integrity)."""
        hash_input = f"{entry['action']}:{entry['entity_type']}:{entry['entity_id']}:" \
                     f"{entry['input_hash']}:{entry['output_hash']}:{entry['prev_hash']}:" \
                     f"{entry['timestamp']}"
        return hashlib.sha256(hash_input.encode()).hexdigest()

    @staticmethod
    async def _get_last_hash() -> str:
        """Get the hash of the most recent audit log entry."""
        try:
            from backend.db.mongodb import Database
            collection = Database.get_collection("audit_logs")
            last_entry = await collection.find_one(
                sort=[("timestamp", -1)]
            )
            if last_entry:
                return AuditService._compute_entry_hash({
                    "action": last_entry["action"],
                    "entity_type": last_entry["entity_type"],
                    "entity_id": last_entry["entity_id"],
                    "input_hash": last_entry["input_hash"],
                    "output_hash": last_entry["output_hash"],
                    "prev_hash": last_entry["prev_hash"],
                    "timestamp": last_entry["timestamp"]
                })
        except Exception as e:
            logger.debug(f"Could not get last hash: {e}")
        return "GENESIS"

    @staticmethod
    async def log_action(
        action: str,
        entity_type: str,
        entity_id: str,
        input_data: Any = None,
        output_data: Any = None,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create an immutable audit log entry.
        
        Args:
            action: Action type (UPLOAD, EXTRACT, PARSE, EVALUATE, EXPORT, DELETE)
            entity_type: Entity type (tender, bidder, evaluation)
            entity_id: ID of the affected entity
            input_data: Input data to hash
            output_data: Output data to hash
            details: Additional details to store
            
        Returns:
            ID of the created audit log entry
        """
        try:
            from backend.db.mongodb import Database
            collection = Database.get_collection("audit_logs")

            input_hash = AuditService._compute_hash(input_data) if input_data else "none"
            output_hash = AuditService._compute_hash(output_data) if output_data else "none"
            prev_hash = await AuditService._get_last_hash()

            entry = {
                "action": action,
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "input_hash": input_hash,
                "output_hash": output_hash,
                "prev_hash": prev_hash,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat()
            }

            # Compute this entry's hash for the chain
            entry["entry_hash"] = AuditService._compute_entry_hash(entry)

            result = await collection.insert_one(entry)
            logger.info(f"📝 Audit log: {action} on {entity_type}/{entity_id}")
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            return ""

    @staticmethod
    async def get_logs(
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Retrieve audit logs with optional filtering."""
        try:
            from backend.db.mongodb import Database
            collection = Database.get_collection("audit_logs")

            query = {}
            if entity_type:
                query["entity_type"] = entity_type
            if entity_id:
                query["entity_id"] = entity_id

            cursor = collection.find(query).sort("timestamp", -1).skip(skip).limit(limit)
            logs = []
            async for doc in cursor:
                doc["id"] = str(doc.pop("_id"))
                logs.append(doc)

            return logs

        except Exception as e:
            logger.error(f"Failed to retrieve audit logs: {e}")
            return []

    @staticmethod
    async def get_total_count(
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> int:
        """Get total count of audit logs matching the filter."""
        try:
            from backend.db.mongodb import Database
            collection = Database.get_collection("audit_logs")
            
            query = {}
            if entity_type:
                query["entity_type"] = entity_type
            if entity_id:
                query["entity_id"] = entity_id

            return await collection.count_documents(query)
        except Exception as e:
            logger.error(f"Failed to count audit logs: {e}")
            return 0

    @staticmethod
    async def verify_chain() -> Dict[str, Any]:
        """
        Verify the integrity of the audit log hash chain.
        
        Returns:
            Dict with is_valid, total_entries, and any broken_at info
        """
        try:
            from backend.db.mongodb import Database
            collection = Database.get_collection("audit_logs")

            cursor = collection.find().sort("timestamp", 1)
            
            prev_hash = "GENESIS"
            total = 0
            broken_at = None

            async for doc in cursor:
                total += 1
                
                # Verify this entry's prev_hash matches expected
                if doc.get("prev_hash") != prev_hash and total > 1:
                    broken_at = {
                        "entry_number": total,
                        "entry_id": str(doc["_id"]),
                        "expected_prev_hash": prev_hash,
                        "actual_prev_hash": doc.get("prev_hash")
                    }
                    break

                # Compute this entry's hash for next comparison
                prev_hash = AuditService._compute_entry_hash({
                    "action": doc["action"],
                    "entity_type": doc["entity_type"],
                    "entity_id": doc["entity_id"],
                    "input_hash": doc["input_hash"],
                    "output_hash": doc["output_hash"],
                    "prev_hash": doc["prev_hash"],
                    "timestamp": doc["timestamp"]
                })

            return {
                "is_valid": broken_at is None,
                "total_entries": total,
                "broken_at": broken_at
            }

        except Exception as e:
            logger.error(f"Chain verification failed: {e}")
            return {
                "is_valid": False,
                "total_entries": 0,
                "error": str(e)
            }
