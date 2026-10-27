---
name: intent-classification
description: |
  [WHAT] Classifies incoming natural language HR requests into a known category.
  [WHEN] Use at the very start of every HR request processing cycle to determine what the employee is asking for.
  [NOT] Do not use for authorization checks — use the authorization skill instead.
  Key terms: payslip, leave balance, employment contract, personal info, compensation, policy.
allowed-tools:
  - Read
metadata:
  version: 1.0.0
  tags:
    - intent
    - classification
    - hr
---

# HR Intent Classification Skill

## Purpose

Classifies the user's natural language HR request into one of the defined HR intent categories. This classification drives the subsequent authorization scope and data retrieval path.

## When to use

- At the start of every request, before authorization or data retrieval
- When the agent receives a natural language message via the Joule interface

## When NOT to use

- Do not use for follow-up questions that continue a classified session — the classification persists for the session
- Do not use to check permissions — that is the authorization skill's job

---

## Instructions

### Step 1 — Read the user message

Analyse the full user message text. Look for keywords, intent signals, and context clues.

### Step 2 — Classify into one of these categories

| Category | Trigger keywords / intent signals |
|---|---|
| `payslip` | payslip, pay slip, salary slip, earnings statement, paycheck, pay stub, payroll summary |
| `leave_balance` | leave balance, annual leave, vacation days, time off, PTO, sick leave quota, remaining leave |
| `employment_contract` | employment contract, contract, offer letter, terms of employment, job agreement |
| `personal_info` | personal details, my profile, contact info, address, bank details, national ID |
| `compensation` | compensation, salary, benefits, bonus, pay grade, total rewards, remuneration |
| `policy` | policy, HR policy, leave policy, company policy, rules, guidelines, handbook |

**Confidence threshold**: If the intent maps clearly to ONE category → proceed to Step 3.

**Ambiguous input**: If the request could match two or more categories with similar likelihood, ask exactly ONE clarifying question:
> "Could you clarify what you need — are you asking about your [category A] or your [category B]?"

Do NOT proceed to authorization until the category is unambiguous.

### Step 3 — Log the classification result

On success:
```
M1.achieved: intent classified as [category] for user [user_id]
```

On failure (ambiguous after clarification, or completely unrecognisable):
```
M1.missed: intent classification failed or produced ambiguous result for user [user_id]
```

### Step 4 — Return the classified category

Return the category string (e.g., `payslip`, `leave_balance`) to the agent orchestration layer so it can proceed to the authorization step.

---

## Examples

### Example 1 — Clear intent

**Input:** "Can you summarise my payslip for last month?"
**Output:** `payslip` — M1.achieved logged

### Example 2 — Ambiguous

**Input:** "What are my details?"
**Output:** Clarifying question: "Could you clarify what you need — are you asking about your personal profile details or your compensation details?"

---

## Gotchas

- **"What is our leave policy?"** maps to `policy`, not `leave_balance`. Policy questions ask about rules; balance questions ask about the user's specific remaining quota.
- **Mixed-intent messages** (e.g., "Show me my payslip and leave balance") — classify the PRIMARY intent first, then handle the secondary intent in a follow-up turn within the same session.
