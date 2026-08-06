import logging
from typing import Dict, Any

logger = logging.getLogger("authority_review.audit")

class AuditLogger:
    """Audit logging utility for Authority Review events."""

    @staticmethod
    def log_event(event_name: str, submission_id: int, reviewer_id: int = None, details: Dict[str, Any] = None) -> None:
        payload = {
            "event": event_name,
            "submission_id": submission_id,
            "reviewer_id": reviewer_id,
            "details": details or {},
        }
        logger.info(f"AUDIT_EVENT: {payload}")
