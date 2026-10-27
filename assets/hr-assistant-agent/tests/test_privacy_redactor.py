"""Tests for privacy_redactor module."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from privacy_redactor import (
    REDACTION_FAILURE_MESSAGE,
    apply_redaction,
)


# ---------------------------------------------------------------------------
# Payslip redaction
# ---------------------------------------------------------------------------

class TestPayslipRedaction:
    def test_employee_sees_masked_bank_account(self):
        data = {"bank_account": "1234567890", "gross_salary": "5000", "net_salary": "4000"}
        ok, result = apply_redaction(data, "payslip", "employee")
        assert ok
        assert result["bank_account"].startswith("****")
        assert result["bank_account"].endswith("7890")

    def test_employee_tax_id_redacted(self):
        data = {"tax_id": "123-45-6789"}
        ok, result = apply_redaction(data, "payslip", "employee")
        assert ok
        assert "tax identifier" in result["tax_id"].lower()

    def test_employee_ni_number_redacted(self):
        data = {"ni_number": "AB123456C"}
        ok, result = apply_redaction(data, "payslip", "employee")
        assert ok
        assert "redacted" in result["ni_number"].lower()

    def test_manager_salary_fields_redacted(self):
        data = {"gross_salary": "5000", "net_salary": "4000", "tax_deductions": "1000"}
        ok, result = apply_redaction(data, "payslip", "manager")
        assert ok
        assert result["gross_salary"] == "***"
        assert result["net_salary"] == "***"
        assert result["tax_deductions"] == "***"

    def test_manager_bank_account_fully_masked(self):
        data = {"bank_account": "1234567890"}
        ok, result = apply_redaction(data, "payslip", "manager")
        assert ok
        assert result["bank_account"] == "****"

    def test_privacy_notice_appended(self):
        data = {"gross_salary": "5000"}
        ok, result = apply_redaction(data, "payslip", "employee")
        assert ok
        assert "_privacy_notice" in result


# ---------------------------------------------------------------------------
# Personal info redaction
# ---------------------------------------------------------------------------

class TestPersonalInfoRedaction:
    def test_manager_sees_age_range_not_dob(self):
        data = {"date_of_birth": "1985-05-15"}
        ok, result = apply_redaction(data, "personal_info", "manager")
        assert ok
        assert "–" in result["date_of_birth"]  # age range format
        assert "1985" not in result["date_of_birth"]

    def test_manager_national_id_redacted(self):
        data = {"national_id": "ABC123456"}
        ok, result = apply_redaction(data, "personal_info", "manager")
        assert ok
        assert result["national_id"] == "***"

    def test_employee_national_id_document_type_shown(self):
        data = {"national_id": "ABC123456"}
        ok, result = apply_redaction(data, "personal_info", "employee")
        assert ok
        assert "national ID" in result["national_id"]

    def test_employee_passport_document_type_shown(self):
        data = {"passport_number": "P1234567"}
        ok, result = apply_redaction(data, "personal_info", "employee")
        assert ok
        assert "passport" in result["passport_number"].lower()

    def test_privacy_notice_included(self):
        data = {"full_name": "John Doe"}
        ok, result = apply_redaction(data, "personal_info", "employee", user_name="John Doe")
        assert ok
        assert "John Doe" in result["_privacy_notice"]


# ---------------------------------------------------------------------------
# Compensation redaction
# ---------------------------------------------------------------------------

class TestCompensationRedaction:
    def test_manager_cannot_see_salary_figures(self):
        data = {"base_salary": "80000", "bonus": "10000", "total_rewards": "90000"}
        ok, result = apply_redaction(data, "compensation", "manager")
        assert ok
        assert result["base_salary"] == "***"
        assert result["bonus"] == "***"
        assert result["total_rewards"] == "***"

    def test_hr_admin_sees_compensation(self):
        data = {"base_salary": "80000", "bonus": "10000"}
        ok, result = apply_redaction(data, "compensation", "hr_admin")
        assert ok
        assert result["base_salary"] == "80000"
        assert result["bonus"] == "10000"


# ---------------------------------------------------------------------------
# Employment info redaction
# ---------------------------------------------------------------------------

class TestEmploymentInfoRedaction:
    def test_manager_cannot_see_salary_on_contract(self):
        data = {"salary_on_contract": "75000", "job_title": "Engineer"}
        ok, result = apply_redaction(data, "employment_contract", "manager")
        assert ok
        assert result["salary_on_contract"] == "***"
        assert result["job_title"] == "Engineer"

    def test_employee_sees_salary_on_contract(self):
        data = {"salary_on_contract": "75000"}
        ok, result = apply_redaction(data, "employment_contract", "employee")
        assert ok
        assert result["salary_on_contract"] == "75000"


# ---------------------------------------------------------------------------
# Leave balance redaction
# ---------------------------------------------------------------------------

class TestLeaveBalanceRedaction:
    def test_manager_medical_details_hidden(self):
        data = {"leave_history": [
            {"leave_type": "Medical", "details": "Back pain"},
            {"leave_type": "Annual", "days": 5},
        ]}
        ok, result = apply_redaction(data, "leave_balance", "manager")
        assert ok
        medical = [e for e in result["leave_history"] if e.get("leave_type") == "Medical"]
        assert medical[0]["details"] == "[redacted]"

    def test_manager_annual_leave_not_redacted(self):
        data = {"leave_history": [{"leave_type": "Annual", "days": 5}]}
        ok, result = apply_redaction(data, "leave_balance", "manager")
        assert ok
        assert result["leave_history"][0]["days"] == 5


# ---------------------------------------------------------------------------
# Policy category (no specific redactor)
# ---------------------------------------------------------------------------

class TestPolicyCategoryRedaction:
    def test_policy_category_passes_through_with_notice(self):
        data = {"policy_text": "Leave policy content..."}
        ok, result = apply_redaction(data, "policy", "employee")
        assert ok
        assert result["policy_text"] == "Leave policy content..."
        assert "_privacy_notice" in result


# ---------------------------------------------------------------------------
# Failure handling
# ---------------------------------------------------------------------------

class TestRedactionFailureSafety:
    def test_redaction_error_returns_safe_message(self, monkeypatch):
        """If redaction throws, must return safe error — never raw data."""
        import privacy_redactor as pr

        def bad_redactor(data, role):
            raise ValueError("Unexpected schema error")

        monkeypatch.setitem(pr._REDACTORS, "payslip", bad_redactor)
        ok, result = apply_redaction({"bank_account": "secret"}, "payslip", "employee")
        assert not ok
        assert result == REDACTION_FAILURE_MESSAGE
        assert "secret" not in result

    def test_redaction_failure_message_is_safe(self):
        assert "contact" in REDACTION_FAILURE_MESSAGE.lower() or "HR" in REDACTION_FAILURE_MESSAGE
