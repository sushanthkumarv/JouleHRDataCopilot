---
name: authorization
description: |
  [WHAT] Validates that the requesting user is authorized to access the requested HR data scope using SAP SuccessFactors Role-Based Permissions.
  [WHEN] Use immediately after intent classification, before any data retrieval. This MUST be the first action taken after classification.
  [NOT] Do not skip this step under any circumstance. Authorization is mandatory for every request.
  Key terms: RBAC, role-based permissions, authorization, access control, employee, manager, HR admin.
allowed-tools:
  - Read
metadata:
  version: 1.0.0
  tags:
    - authorization
    - rbac
    - security
    - successfactors
---

# HR Authorization Skill

## Purpose

Enforces 3-tier role-based access control (RBAC) for all HR data requests. This skill defines the rules used to validate whether the requesting user may access the requested data scope before any retrieval occurs.

## When to use

- After intent classification, before every data retrieval call
- On every request — there are no exceptions

## When NOT to use

- Do not use this skill for intent classification
- Do not use this skill to retrieve data — it only validates access rights

---

## Instructions

### Step 1 — Identify the requesting user's role

Determine the user's role from the security context propagated from the Joule interface:
- `employee` — standard employee
- `manager` — team lead or people manager with direct reports
- `hr_admin` — HR business partner or HR administrator

### Step 2 — Call the PLTRoleBasedPermissions MCP tool

Call the `PLTRoleBasedPermissions` MCP tool with:
- Requesting user ID
- Target user ID (may differ for manager queries)
- Requested data scope (maps to the classified intent category)

| Intent Category | Data Scope |
|---|---|
| `payslip` | `PAYROLL_VIEW` |
| `leave_balance` | `TIME_OFF_VIEW` |
| `employment_contract` | `EMPLOYMENT_INFO_VIEW` |
| `personal_info` | `PERSONAL_INFO_VIEW` |
| `compensation` | `COMPENSATION_VIEW` |
| `policy` | `PUBLIC_POLICY_VIEW` |

### Step 3 — Apply 3-tier RBAC rules

| User Role | Allowed Scope |
|---|---|
| `employee` | Own data only — `requestingUserId == targetUserId` must be true |
| `manager` | Direct reports only — verify `managerId == requestingUserId` for the target employee |
| `hr_admin` | All employees within their configured business unit scope |

**If scope validation FAILS:**
- Stop immediately
- Return the access-denied message (see Step 4)
- Do NOT call any data retrieval tool
- Log `M2.achieved: authorization denied for user [user_id] on scope [data_scope]`

**If scope validation SUCCEEDS:**
- Proceed to data retrieval
- Log `M2.achieved: authorization granted for user [user_id] on scope [data_scope]`

**If the MCP call times out or errors:**
- Stop immediately
- Return a safe error message: "Authorization check is temporarily unavailable. Please try again or contact HR."
- Log `M2.missed: authorization check failed or timed out for user [user_id]`

### Step 4 — Access-denied message format

When authorization is denied, return EXACTLY this format — do NOT include any data fragments:

```
Access Denied: You do not have permission to access [data_scope] for [target_user_name_or_id].

If you believe this is incorrect, please contact your HR representative.
```

---

## Gotchas

- **NEVER skip authorization** — even for `policy` requests (public policies still go through the check to confirm the user is an authenticated employee).
- **Manager scope creep** — a manager may only access direct reports, NOT the entire organizational hierarchy below them. Always check the direct report relationship, not just the reporting line.
- **MCP timeout ≠ authorization granted** — if the MCP call fails, treat it as a hard stop, not a pass-through.
