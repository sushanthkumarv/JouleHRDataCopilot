---
name: privacy-redaction
description: |
  [WHAT] Applies GDPR and CCPA field-level data redaction to HR data payloads before they are included in any agent response.
  [WHEN] Use after data retrieval and before formulating the user response. This MUST run on every data payload.
  [NOT] Do not skip this step. If redaction fails for any reason, return a safe error — never return unredacted data.
  Key terms: GDPR, CCPA, redaction, PII, privacy, data minimisation, masking.
allowed-tools:
  - Read
metadata:
  version: 1.0.0
  tags:
    - privacy
    - gdpr
    - ccpa
    - redaction
    - compliance
---

# Privacy Redaction Skill

## Purpose

Applies field-level privacy redaction to HR data payloads in compliance with GDPR (EU Regulation 2016/679) and CCPA (California Consumer Privacy Act). Ensures that sensitive personal data is redacted or masked before inclusion in any agent response.

## When to use

- After every data retrieval call, before formulating the response
- On every response containing personal or payroll data — no exceptions

## When NOT to use

- Do not use this skill to retrieve data
- Do not apply redaction to access-denied or error messages (no data is present)

---

## Instructions

### Step 1 — Identify the requesting user's role and data category

The redaction rules vary by the requester's role and the data category being returned.

### Step 2 — Apply field-level redaction rules

#### Payslip / Payroll data

| Field | Employee | Manager | HR Admin |
|---|---|---|---|
| Gross salary amount | SHOW | REDACT (`***`) | SHOW |
| Net salary amount | SHOW | REDACT (`***`) | SHOW |
| Bank account number | REDACT (last 4 digits only: `****1234`) | REDACT (full) | REDACT (last 4 digits only) |
| Tax ID / NI number | REDACT (show category only) | REDACT (full) | REDACT (show category only) |
| Tax deduction amounts | SHOW (own) | REDACT (`***`) | SHOW |
| Payroll period | SHOW | SHOW | SHOW |

#### Personal Information

| Field | Employee | Manager | HR Admin |
|---|---|---|---|
| Full name | SHOW | SHOW | SHOW |
| Date of birth | SHOW (own) | REDACT (age range only, e.g., "30–40") | SHOW |
| National ID / passport number | REDACT (document type only) | REDACT (full) | REDACT (document type only) |
| Home address | SHOW (own) | REDACT (city only) | SHOW |
| Personal email | SHOW (own) | REDACT (full) | SHOW |
| Emergency contact | SHOW (own) | REDACT (full) | SHOW |

#### Compensation

| Field | Employee | Manager | HR Admin |
|---|---|---|---|
| Base salary | SHOW (own) | REDACT (`***`) | SHOW |
| Bonus amounts | SHOW (own) | REDACT (`***`) | SHOW |
| Pay grade / band | SHOW | SHOW | SHOW |
| Total rewards value | SHOW (own) | REDACT (`***`) | SHOW |

#### Employment Information

| Field | Employee | Manager | HR Admin |
|---|---|---|---|
| Job title | SHOW | SHOW | SHOW |
| Start date | SHOW | SHOW | SHOW |
| Contract type | SHOW | SHOW | SHOW |
| Salary on contract | SHOW (own) | REDACT (`***`) | SHOW |

#### Leave Balances

| Field | Employee | Manager | HR Admin |
|---|---|---|---|
| Leave balance (own) | SHOW | SHOW | SHOW |
| Leave history | SHOW (own) | SHOW (direct reports) | SHOW |
| Medical leave details | SHOW (own) | REDACT (type only: "Medical") | REDACT (type only) |

### Step 3 — Privacy notice

Append the following notice to EVERY response containing personal data:

```
---
🔒 Data Privacy Notice: This information is provided in accordance with GDPR and CCPA regulations. It is intended solely for [user_name] and must not be shared with unauthorised parties.
```

### Step 4 — Log and return

On success:
```
M4.achieved: privacy-compliant response delivered to user [user_id] for category [category]
```

On ANY redaction failure (exception, missing rule, data format mismatch):
```
M4.missed: privacy redaction failed or response delivery error for user [user_id]
```
Then return: "We are unable to process your request at this time due to a data privacy compliance check. Please contact HR directly."

---

## Gotchas

- **Redaction failure = safe error, not passthrough** — if the redaction module throws any exception, NEVER return the unredacted payload. Return the safe error message instead.
- **Summaries, not raw dumps** — always summarise the data in natural language. Never paste raw JSON or API responses into the user-facing reply.
- **CCPA "right to know"** — employees viewing their own data under CCPA have the right to see it; do not over-redact for self-service requests.
