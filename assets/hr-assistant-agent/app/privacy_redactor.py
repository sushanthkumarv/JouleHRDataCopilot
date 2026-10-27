"""
GDPR & CCPA Privacy Redaction Layer.

Applies field-level redaction to HR data payloads before they are included in
any agent response. If redaction fails for any reason, a safe error message is
returned — unredacted data is NEVER passed through.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Safe error message returned on redaction failure
REDACTION_FAILURE_MESSAGE = (
    "We are unable to process your request at this time due to a data privacy "
    "compliance check. Please contact your HR representative directly."
)

# Privacy notice appended to all personal data responses
_PRIVACY_NOTICE_TEMPLATE = (
    "\n\n---\n"
    "🔒 Data Privacy Notice: This information is provided in accordance with "
    "GDPR and CCPA regulations. It is intended solely for {user_name} and must "
    "not be shared with unauthorised parties."
)


def _mask_bank_account(value: str) -> str:
    """Keep last 4 digits, mask the rest."""
    if not value or len(value) < 4:
        return "****"
    return "****" + value[-4:]


def _redact_field(value: Any) -> str:
    """Replace any value with the standard redaction marker."""
    return "***"


def _age_range(dob_year: int | None) -> str:
    """Convert year of birth to a decade range string."""
    if dob_year is None:
        return "[age range unavailable]"
    from datetime import date
    age = date.today().year - dob_year
    lower = (age // 10) * 10
    return f"{lower}–{lower + 9}"


# ---------------------------------------------------------------------------
# Per-category redaction functions
# ---------------------------------------------------------------------------

def _redact_payslip(data: dict, role: str) -> dict:
    redacted = dict(data)
    if role == "manager":
        for field in ("gross_salary", "net_salary", "tax_deductions"):
            if field in redacted:
                redacted[field] = _redact_field(redacted[field])
    if "bank_account" in redacted:
        if role == "manager":
            redacted["bank_account"] = "****"
        else:
            redacted["bank_account"] = _mask_bank_account(str(redacted["bank_account"]))
    if "tax_id" in redacted:
        redacted["tax_id"] = "[tax identifier — type: " + str(redacted.get("tax_id_type", "standard")) + "]"
    if "ni_number" in redacted:
        redacted["ni_number"] = "[NI number — redacted]"
    return redacted


def _redact_personal_info(data: dict, role: str) -> dict:
    redacted = dict(data)
    if role in ("manager", "hr_admin"):
        if "date_of_birth" in redacted and role == "manager":
            year = None
            dob = redacted["date_of_birth"]
            if isinstance(dob, str):
                m = re.search(r"\d{4}", dob)
                year = int(m.group()) if m else None
            redacted["date_of_birth"] = _age_range(year)
        if role == "manager":
            for field in ("national_id", "passport_number", "home_address", "personal_email", "emergency_contact"):
                if field in redacted:
                    redacted[field] = _redact_field(redacted[field])
    if "national_id" in redacted and role != "manager":
        redacted["national_id"] = "[document type: national ID — number redacted]"
    if "passport_number" in redacted and role != "manager":
        redacted["passport_number"] = "[document type: passport — number redacted]"
    return redacted


def _redact_compensation(data: dict, role: str) -> dict:
    redacted = dict(data)
    if role == "manager":
        for field in ("base_salary", "bonus", "total_rewards"):
            if field in redacted:
                redacted[field] = _redact_field(redacted[field])
    return redacted


def _redact_employment_info(data: dict, role: str) -> dict:
    redacted = dict(data)
    if role == "manager":
        if "salary_on_contract" in redacted:
            redacted["salary_on_contract"] = _redact_field(redacted["salary_on_contract"])
    return redacted


def _redact_leave_balance(data: dict, role: str) -> dict:
    redacted = dict(data)
    # Medical leave type is visible but details are redacted for non-employees
    if role in ("manager", "hr_admin"):
        entries = redacted.get("leave_history", [])
        sanitised = []
        for entry in entries:
            if isinstance(entry, dict) and entry.get("leave_type", "").lower() == "medical":
                sanitised.append({"leave_type": "Medical", "details": "[redacted]"})
            else:
                sanitised.append(entry)
        redacted["leave_history"] = sanitised
    return redacted


_REDACTORS = {
    "payslip": _redact_payslip,
    "personal_info": _redact_personal_info,
    "compensation": _redact_compensation,
    "employment_contract": _redact_employment_info,
    "leave_balance": _redact_leave_balance,
}


def apply_redaction(
    data: dict[str, Any],
    intent_category: str,
    requesting_role: str,
    user_name: str = "the requesting user",
) -> tuple[bool, dict[str, Any] | str]:
    """
    Apply GDPR and CCPA field-level redaction to a data payload.

    Args:
        data: Raw HR data payload to redact.
        intent_category: The classified HR intent (e.g., 'payslip').
        requesting_role: The requester's role ('employee', 'manager', 'hr_admin').
        user_name: Display name of the requesting user for the privacy notice.

    Returns:
        Tuple of (success: bool, result: dict | str).
        On success: (True, redacted_dict_with_privacy_notice).
        On failure: (False, safe_error_message_string).
    """
    try:
        redactor = _REDACTORS.get(intent_category)
        if redactor is None:
            # No specific redactor for this category (e.g., 'policy') — pass through with notice
            redacted = dict(data)
        else:
            redacted = redactor(data, requesting_role)

        # Attach privacy notice
        redacted["_privacy_notice"] = _PRIVACY_NOTICE_TEMPLATE.format(user_name=user_name)
        logger.info(
            "M4.achieved: privacy-compliant response delivered for category %s (role: %s)",
            intent_category,
            requesting_role,
        )
        return True, redacted

    except Exception as exc:  # noqa: BLE001
        logger.error(
            "M4.missed: privacy redaction failed for category %s (role: %s): %s",
            intent_category,
            requesting_role,
            str(exc),
        )
        return False, REDACTION_FAILURE_MESSAGE
