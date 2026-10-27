"""Tests for audit_logger module."""
import json
import os
import sys
import tempfile
import uuid
from pathlib import Path

import pytest

# Add app/ to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))


@pytest.fixture(autouse=True)
def temp_audit_dir(tmp_path, monkeypatch):
    """Redirect audit log to a temp dir for each test."""
    monkeypatch.setenv("AUDIT_LOG_DIR", str(tmp_path / "audit"))
    # Force reload so the module picks up the new env var
    import importlib
    import audit_logger
    audit_logger._AUDIT_DIR = os.environ.get("AUDIT_LOG_DIR", "audit")
    audit_logger._AUDIT_FILE = os.path.join(audit_logger._AUDIT_DIR, "hr_audit_log.jsonl")
    yield tmp_path / "audit"


def test_write_entry_creates_file(temp_audit_dir):
    """write_entry should create the audit file if it does not exist."""
    import audit_logger
    interaction_id = audit_logger.write_entry(
        user_id="user1",
        request_summary="Test request",
        authorization_result="granted",
        response_summary="Test response",
    )
    log_file = temp_audit_dir / "hr_audit_log.jsonl"
    assert log_file.exists()
    lines = log_file.read_text().strip().splitlines()
    assert len(lines) == 1


def test_write_entry_returns_interaction_id():
    """write_entry should return the interaction_id used."""
    import audit_logger
    custom_id = str(uuid.uuid4())
    returned = audit_logger.write_entry(
        user_id="user1",
        request_summary="Request",
        authorization_result="granted",
        response_summary="Response",
        interaction_id=custom_id,
    )
    assert returned == custom_id


def test_write_entry_auto_generates_interaction_id():
    """write_entry should auto-generate interaction_id if not provided."""
    import audit_logger
    returned = audit_logger.write_entry(
        user_id="user1",
        request_summary="Request",
        authorization_result="denied",
        response_summary="Access denied",
    )
    assert returned  # non-empty UUID string


def test_write_entry_correct_fields(temp_audit_dir):
    """write_entry should write all required fields to the log."""
    import audit_logger
    iid = audit_logger.write_entry(
        user_id="emp123",
        request_summary="Show my payslip",
        authorization_result="granted",
        response_summary="Payslip summary provided",
        intent_category="payslip",
        data_scope="PAYROLL_VIEW",
        milestone_statuses={"M1": "achieved", "M2": "achieved"},
    )
    log_file = temp_audit_dir / "hr_audit_log.jsonl"
    entry = json.loads(log_file.read_text().strip())
    assert entry["interaction_id"] == iid
    assert entry["user_id"] == "emp123"
    assert entry["request_summary"] == "Show my payslip"
    assert entry["authorization_result"] == "granted"
    assert entry["intent_category"] == "payslip"
    assert entry["data_scope"] == "PAYROLL_VIEW"
    assert entry["milestone_statuses"] == {"M1": "achieved", "M2": "achieved"}
    assert "timestamp" in entry


def test_write_entry_caps_long_summaries(temp_audit_dir):
    """write_entry must cap request and response summaries to 500 chars."""
    import audit_logger
    long_text = "X" * 600
    audit_logger.write_entry(
        user_id="u",
        request_summary=long_text,
        authorization_result="granted",
        response_summary=long_text,
    )
    log_file = temp_audit_dir / "hr_audit_log.jsonl"
    entry = json.loads(log_file.read_text().strip())
    assert len(entry["request_summary"]) <= 500
    assert len(entry["response_summary"]) <= 500


def test_write_entry_never_writes_raw_payloads(temp_audit_dir):
    """Entries must not contain raw data payloads."""
    import audit_logger
    audit_logger.write_entry(
        user_id="u",
        request_summary="salary request",
        authorization_result="granted",
        response_summary="salary summary",
    )
    log_file = temp_audit_dir / "hr_audit_log.jsonl"
    content = log_file.read_text()
    # No raw numeric salary data or sensitive raw payload markers
    assert "bank_account" not in content
    assert "tax_id" not in content


def test_write_entry_appends(temp_audit_dir):
    """Multiple write_entry calls should append, not overwrite."""
    import audit_logger
    for i in range(3):
        audit_logger.write_entry(
            user_id=f"user{i}",
            request_summary=f"Request {i}",
            authorization_result="granted",
            response_summary=f"Response {i}",
        )
    log_file = temp_audit_dir / "hr_audit_log.jsonl"
    lines = log_file.read_text().strip().splitlines()
    assert len(lines) == 3


def test_build_access_denied_response_no_data():
    """Access-denied response must not expose data fragments."""
    import audit_logger
    msg = audit_logger.build_access_denied_response("PAYROLL_VIEW", "payslip")
    assert "Access Denied" in msg
    assert "payslip" in msg
    # Ensure no data fragments
    for dangerous in ["salary", "account", "tax", "national_id"]:
        assert dangerous not in msg.lower()


def test_build_access_denied_response_mentions_hr():
    """Access-denied response should direct user to HR contact."""
    import audit_logger
    msg = audit_logger.build_access_denied_response("PAYROLL_VIEW")
    assert "HR" in msg or "human resources" in msg.lower()
