"""
Audit Logger — Append-only interaction log for HR Assistant Agent.

Writes structured JSONL entries to audit/hr_audit_log.jsonl.
Each entry records: interaction_id, timestamp, user_id, request_summary,
intent_category, authorization_result, data_scope, response_summary,
and milestone_statuses.

IMPORTANT: Raw data payloads are NEVER written. Summaries only.
"""

import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Audit log location (relative to working directory or override via env var)
_AUDIT_DIR = os.environ.get("AUDIT_LOG_DIR", "audit")
_AUDIT_FILE = os.path.join(_AUDIT_DIR, "hr_audit_log.jsonl")

# Thread lock for safe concurrent writes
_write_lock = threading.Lock()


def _ensure_audit_dir() -> None:
    """Create the audit directory if it does not exist."""
    Path(_AUDIT_DIR).mkdir(parents=True, exist_ok=True)


def write_entry(
    user_id: str,
    request_summary: str,
    authorization_result: str,
    response_summary: str,
    intent_category: str = "unknown",
    data_scope: str = "unknown",
    milestone_statuses: dict[str, str] | None = None,
    interaction_id: str | None = None,
) -> str:
    """
    Append a structured audit log entry.

    Args:
        user_id: The requesting user's identifier.
        request_summary: A short (< 200 char) summary of the request. No raw data.
        authorization_result: 'granted', 'denied', or 'error'.
        response_summary: A short summary of what was returned. No raw data.
        intent_category: Classified HR intent category.
        data_scope: The data scope evaluated for authorization.
        milestone_statuses: Dict mapping milestone ID to 'achieved' or 'missed'.
        interaction_id: Correlation ID; auto-generated if not provided.

    Returns:
        The interaction_id used for this log entry.
    """
    if interaction_id is None:
        interaction_id = str(uuid.uuid4())

    entry: dict[str, Any] = {
        "interaction_id": interaction_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "request_summary": request_summary[:500],  # cap at 500 chars
        "intent_category": intent_category,
        "authorization_result": authorization_result,
        "data_scope": data_scope,
        "response_summary": response_summary[:500],  # cap at 500 chars
        "milestone_statuses": milestone_statuses or {},
    }

    try:
        _ensure_audit_dir()
        with _write_lock:
            with open(_AUDIT_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        logger.info(
            "M5.achieved: audit log entry written for interaction %s",
            interaction_id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "M5.missed: audit log write failed for interaction %s: %s",
            interaction_id,
            str(exc),
        )

    return interaction_id


def build_access_denied_response(data_scope: str, target_identifier: str = "the requested resource") -> str:
    """
    Build a standardised access-denied response message.

    No data fragments are ever included. The message directs the user to HR.

    Args:
        data_scope: The scope that was denied (e.g., 'PAYROLL_VIEW').
        target_identifier: Display label for what was requested.

    Returns:
        A safe, user-facing access-denied string.
    """
    return (
        f"Access Denied: You do not have permission to access {target_identifier}.\n\n"
        f"If you believe this is incorrect, please contact your HR representative "
        f"or raise a request through the HR portal."
    )
