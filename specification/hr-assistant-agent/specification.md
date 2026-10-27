# Specification: hr-assistant-agent

> **Guidelines**: Read all applicable guidelines before executing ANY tasks below:
> - [guidelines.md](../guidelines.md) — Universal execution rules
> - [guidelines-agent.md](../guidelines-agent.md) — Universal agent patterns
> - [guidelines-agent-python.md](../guidelines-agent-python.md) — Python implementation details
> - [guidelines-agent-skills.md](../guidelines-agent-skills.md) — Runtime skills patterns
> - [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) — MCP integration patterns

---

## Basic Setup

- [ ] Read `product-requirements-document.md` and `intent.md` for full context before proceeding.
- [ ] Bootstrap agent code in `assets/hr-assistant-agent/` using the `sap-agent-bootstrap` instructions. (invoke from inside `assets/hr-assistant-agent/`, use copy commands — do NOT create files manually)
- [ ] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`

---

## Runtime Skills

- [ ] Create `assets/hr-assistant-agent/app/skills/authorization/SKILL.md` — 3-tier RBAC rules:
  - Employee: access to own data only (filter by `userId == requestingUserId`)
  - Manager: access to direct reports only (verify `managerId == requestingUserId`)
  - HR Admin: access to all employees
  - If scope validation fails → return access-denied immediately; do NOT proceed to data retrieval
- [ ] Create `assets/hr-assistant-agent/app/skills/privacy-redaction/SKILL.md` — GDPR & CCPA field-level redaction rules:
  - Define redactable fields per data domain: payroll (bank account, tax ID, NI number), personal info (national ID, DOB for managers), compensation (exact figures for non-HR roles)
  - Rule: if redaction layer throws any error → return safe error message; NEVER return unredacted data
  - Append data privacy notice to every response containing personal data
- [ ] Create `assets/hr-assistant-agent/app/skills/intent-classification/SKILL.md` — HR intent categories:
  - Categories: `payslip`, `leave_balance`, `employment_contract`, `personal_info`, `compensation`, `policy`
  - If confidence is low → ask one clarifying question before proceeding
  - Log: `M1.achieved: intent classified as [category] for user [user_id]` on success
  - Log: `M1.missed: intent classification failed or produced ambiguous result for user [user_id]` on failure

---

## Project-Specific Tasks

### REQ-01: Natural Language Request Ingestion & Intent Classification

- [ ] In `app/agent.py`, define system prompt instructing the agent to:
  - Accept natural language HR questions via the Joule interface
  - Classify intent into one of: `payslip`, `leave_balance`, `employment_contract`, `personal_info`, `compensation`, `policy`
  - If confidence is insufficient, ask exactly one clarifying question before proceeding
  - Load the `intent-classification` runtime skill via `load(path)` tool for classification rules
  - Instrument milestone M1: log `M1.achieved` / `M1.missed` based on classification outcome

### REQ-02: Authorization Validation via SAP SuccessFactors Role-Based Permissions

- [ ] Wire the `PLTRoleBasedPermissions` MCP tool (generated from `specification/hr-assistant-agent/api-specs/PLTRoleBasedPermissions.edmx`) for permission checks
- [ ] In `app/agent.py` system prompt, instruct the agent to:
  - Always call the `PLTRoleBasedPermissions` MCP tool FIRST — before any data retrieval
  - Enforce 3-tier scope: employee → own data; manager → direct reports; HR admin → all
  - Load the `authorization` runtime skill via `load(path)` for RBAC rules
  - If authorization returns denied or errors → stop immediately, return access-denied message (do NOT expose any data fragments)
  - Instrument milestone M2: log `M2.achieved: authorization [granted|denied] for user [user_id] on scope [data_scope]` or `M2.missed` on timeout/error

### REQ-03: HR Data Retrieval via SAP SuccessFactors APIs (MCP)

- [ ] Wire the following MCP tools (generated from downloaded API specs):
  - `ECEmployeeProfile` — from `specification/hr-assistant-agent/api-specs/ECEmployeeProfile.edmx`
  - `ECEmployeeCentralPayroll` — from `specification/hr-assistant-agent/api-specs/ECEmployeeCentralPayroll.edmx`
  - `Balances` (Time Off Balances) — from `specification/hr-assistant-agent/api-specs/Balances.json`
  - `ECCompensationInformation` — from `specification/hr-assistant-agent/api-specs/ECCompensationInformation.edmx`
  - `ECEmploymentInformation` — from `specification/hr-assistant-agent/api-specs/ECEmploymentInformation.edmx`
- [ ] Instruct the agent to: retrieve only the minimum data required for the specific request (least-privilege)
- [ ] On API call failure: return a graceful error message; log the failure to the audit log; do NOT surface raw stack traces

### REQ-04: External Document/PDF Retrieval via A2A Protocol

- [ ] Implement `assets/hr-assistant-agent/app/a2a_client.py` — A2A protocol client:
  - Target endpoint: `EXTERNAL_AVIATOR_AGENT_ENDPOINT` (read from environment variable)
  - Send authenticated, encrypted-in-transit requests to the external document-generation agent
  - Return document payload or structured data on success
  - On failure: return a user-friendly error, log the failure; do NOT retry indefinitely (max 2 retries with exponential backoff)
  - Instrument milestone M3: log `M3.achieved: A2A invocation successful, payload received for user [user_id]` on success; `M3.missed` on failure
- [ ] Expose A2A invocation as a tool the agent can call after successful authorization

### REQ-05: GDPR & CCPA Privacy Compliance Layer

- [ ] Implement `assets/hr-assistant-agent/app/privacy_redactor.py`:
  - Input: raw data payload + requesting user role
  - Apply field-level redaction per GDPR and CCPA rules (load rules from the `privacy-redaction` runtime skill)
  - CRITICAL: if redaction fails for any reason → return safe error message; NEVER return unredacted data
  - Append a data privacy notice to every response containing personal data
  - Instrument milestone M4: log `M4.achieved: privacy-compliant response delivered to user [user_id] for category [category]` on success; `M4.missed` on redaction failure

### REQ-06: Access-Denied Response Handling

- [ ] Implement a standardised access-denied response helper:
  - Message must: state access is denied, NOT expose any data fragments, optionally direct the user to their HR contact
  - Called by authorization layer (REQ-02) whenever authorization fails

### REQ-07: Audit Log for All Interactions

- [ ] Implement `assets/hr-assistant-agent/app/audit_logger.py`:
  - Append-only file writer — target: `audit/hr_audit_log.jsonl` (created if not exists)
  - Log entry fields: `interaction_id`, `timestamp` (ISO-8601), `user_id`, `request_summary`, `intent_category`, `authorization_result`, `data_scope`, `response_summary`, `milestone_statuses`
  - NEVER write raw data payloads — summaries only
  - Write an entry for EVERY interaction including failures and access-denied outcomes
  - Instrument milestone M5: log `M5.achieved: audit log entry written for interaction [interaction_id]`; `M5.missed: audit log write failed for interaction [interaction_id]`

### REQ-08: Conversation Context Retention

- [ ] Maintain conversation context within a session using the agent's built-in context management
- [ ] User should not need to repeat context for follow-up questions within the same session

### Agent System Prompt Configuration

- [ ] In `app/agent.py` `@prompt_section`, define the full system prompt covering:
  - Agent role: Enterprise HR Assistant Agent for Joule interface
  - Strict operation order: classify intent → validate authorization → retrieve data → apply privacy redaction → formulate response → write audit log
  - Guardrails: read-only agent; NEVER modify, create, or delete any data in SAP SuccessFactors
  - Reference the `intent-classification`, `authorization`, and `privacy-redaction` runtime skills
  - Instructions to use MCP tools for all SuccessFactors API calls (no direct HTTP)
  - Instructions to call `a2a_client` for PDF/document retrieval after authorization succeeds
  - Instructions to ALWAYS write an audit log entry at the end of every interaction

---

## Business Instrumentation

- [ ] Implement structured logging and OpenTelemetry spans for all 5 milestones:
  - **M1** — Intent Classification: `M1.achieved: intent classified as [category] for user [user_id]` / `M1.missed`
  - **M2** — Authorization Validated: `M2.achieved: authorization [granted|denied] for user [user_id] on scope [data_scope]` / `M2.missed`
  - **M3** — External Agent Invoked (A2A): `M3.achieved: A2A invocation successful, payload received for user [user_id]` / `M3.missed`
  - **M4** — Privacy-Compliant Response Delivered: `M4.achieved: privacy-compliant response delivered to user [user_id] for category [category]` / `M4.missed`
  - **M5** — Audit Log Written: `M5.achieved: audit log entry written for interaction [interaction_id]` / `M5.missed`
- [ ] Extract business logic from `stream()` into a plain `async` helper to avoid `GeneratorExit` context errors
- [ ] Verify `bootstrap(app)` is called after `app = server.build()` in `main.py`

---

## MCP Tool Integration

- [ ] Verify `specification/hr-assistant-agent/api-specs/` contains all 6 downloaded spec files:
  - `PLTRoleBasedPermissions.edmx`
  - `ECEmployeeProfile.edmx`
  - `ECEmployeeCentralPayroll.edmx`
  - `Balances.json`
  - `ECCompensationInformation.edmx`
  - `ECEmploymentInformation.edmx`
- [ ] Invoke `mcp-translation-file` skill for each of the 6 API specs to generate MCP translation files
- [ ] Invoke `setup-solution` skill to create `solution.yaml` and `asset.yaml` files and register generated MCP assets
- [ ] Wire MCP tool loading in `agent.py` using `get_mcp_tools()` from the `mcp_tools` module — NEVER import directly from `sap_cloud_sdk.agentgateway`
- [ ] Add all 6 MCP server dependencies to `asset.yaml` under `requires` (one entry per MCP server, using exact ORD IDs from generated assets)
- [ ] Generate `mcp-mock.json` using the `mcp-mock-config` skill (required before tests can run)

---

## Testing

- [ ] `conftest.py` sets only `IBD_TESTING=true`
- [ ] Write unit tests in `assets/hr-assistant-agent/tests/` — one per MCP tool and one per custom module:
  - Test: `PLTRoleBasedPermissions` authorization check (granted and denied cases)
  - Test: `ECEmployeeProfile` data retrieval
  - Test: `ECEmployeeCentralPayroll` payslip retrieval
  - Test: `Balances` leave balance retrieval
  - Test: `ECCompensationInformation` compensation data retrieval
  - Test: `ECEmploymentInformation` employment info retrieval
  - Test: `a2a_client.py` — successful A2A invocation and failure/retry logic
  - Test: `privacy_redactor.py` — redaction applied correctly; redaction failure returns safe error
  - Test: `audit_logger.py` — entry written with correct fields; never writes raw payloads
  - Test: access-denied response — no data fragments exposed
- [ ] Write one integration test executing end-to-end agent flow with mocked LLM and mocked external systems (offline)
- [ ] Run `pytest` from `assets/hr-assistant-agent/` (no args) — if coverage < 70%, add tests
- [ ] Run `pytest` again from `assets/hr-assistant-agent/` (no args) to generate final `test_report.json`
- [ ] Verify `test_report.json` exists in `assets/hr-assistant-agent/`
