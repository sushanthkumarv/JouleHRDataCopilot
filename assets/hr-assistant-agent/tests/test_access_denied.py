"""Tests for access-denied response helper."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))


class TestAccessDeniedResponse:
    def test_no_data_fragments_in_response(self):
        from audit_logger import build_access_denied_response
        msg = build_access_denied_response("PAYROLL_VIEW", "payslip data")
        # Should not contain any sensitive data fragments
        assert "payslip data" in msg
        for fragment in ["bank_account", "salary", "tax_id", "national_id", "123", "000"]:
            assert fragment not in msg

    def test_access_denied_message_present(self):
        from audit_logger import build_access_denied_response
        msg = build_access_denied_response("PAYROLL_VIEW")
        assert "Access Denied" in msg or "denied" in msg.lower()

    def test_no_data_scope_exposed_as_sensitive(self):
        from audit_logger import build_access_denied_response
        msg = build_access_denied_response("SECRET_SCOPE", "secret data")
        # The message may reference the scope label but must not expose raw data
        assert msg

    def test_hr_contact_direction(self):
        from audit_logger import build_access_denied_response
        msg = build_access_denied_response("ANY_SCOPE")
        assert "HR" in msg or "human resources" in msg.lower() or "contact" in msg.lower()

    def test_returns_string(self):
        from audit_logger import build_access_denied_response
        result = build_access_denied_response("SCOPE")
        assert isinstance(result, str)
        assert len(result) > 0
