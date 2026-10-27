# Product Requirements Document (PRD)

**Title:** Enterprise HR Assistant Agent  
**Date:** 2026-10-07  
**Owner:** HR Digital Transformation Team  
**Solution Category:** AI Agent

---

## Product Purpose & Value Proposition

**Elevator Pitch:**  
Employees, managers, and HR staff currently wait up to two days to receive routine HR information — payslips, leave balances, employment contracts, or compensation summaries. This agent eliminates that wait by providing instant, governed, natural language access to HR data directly through the Joule interface, with authorization and privacy enforced automatically on every interaction.

**Business Need:**  
There is no intelligent self-service channel for routine Tier-1 HR inquiries. Employees raise tickets or contact HR representatives for information they are entitled to access independently. This creates avoidable workload for HR teams and frustrating delays for employees. The solution must handle these requests autonomously while strictly enforcing access rights and data privacy regulations.

**Expected Value:**  
- HR response wait time reduced from 2 days to under 1 hour.
- Measurable reduction in Tier-1 HR support tickets (payslip, leave, policy inquiries).
- Agent response time under 45 seconds per user prompt.
- More than 75% of HR inquiries resolved without human escalation.

**Product Objectives (Prioritized):**
1. Provide employees with instant, self-service access to their own HR documents and data via natural language.
2. Enforce role-based authorization against SAP SuccessFactors permissions on every request.
3. Apply GDPR and CCPA privacy compliance rules before any response is delivered.
4. Integrate securely with the external document-generation agent via A2A protocol.
5. Maintain a complete audit trail of all interactions for compliance and traceability.

---

## Business Metrics

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| HR response wait time | 2 days | < 1 hour | 3 months | Employee HR inquiry handling | user |
| Routine Tier-1 HR ticket volume (payslip, leave, policy) | — | Measurable reduction | 3 months | Payslip, leave balance, policy clarification | user |
| Agent response time per user prompt | — | < 45 seconds | 3 months | All HR agent interactions | user |
| Agent self-service rate (no human escalation) | — | > 75% of all HR inquiries | 3 months | End-to-end HR self-service | user |

---

## User Profiles & Personas

### Primary Persona: Employee (Self-Service User)

Alex is a 34-year-old software engineer who needs quick access to their payslip, leave balance, and employment contract. Alex is comfortable with conversational interfaces and expects instant answers. The frustration: every HR data request currently requires opening a ticket and waiting one to two days for a response. Alex just wants to type a question and get an accurate answer in seconds, without navigating multiple HR portals.

### Secondary Persona: Manager

Jordan is a 42-year-old team lead managing 12 direct reports. Jordan frequently needs to check team members' leave balances or verify employment details when planning project resourcing. Currently, this requires contacting HR or asking the employee directly. Jordan expects to be able to ask the agent on behalf of a direct report and receive accurate, permission-gated results.

### Other User Types

- **HR Business Partner**: Broader data access; handles inquiries on behalf of a business unit. Needs to retrieve records across multiple employees within their scope.
- **HR Admin**: Full access to all employee data. Uses the agent to quickly retrieve records during audit or compliance activities.

---

## User Goals & Tasks

### For Employees:
**Goals:**
- Access own payslips, leave balances, contracts, personal information, and compensation summaries without raising a ticket.
- Receive clear, privacy-compliant answers within 45 seconds.

**Key Tasks:**
- Ask the agent natural language questions ("What is my current leave balance?", "Summarise my latest payslip").
- Receive summarised or extracted information, not raw data dumps.
- Be notified clearly if access is denied.

### For Managers:
**Goals:**
- Check direct reports' relevant HR data within permitted scope.

**Key Tasks:**
- Query the agent about a direct report's leave balance or employment status.
- Receive permission-gated responses that respect the employee's privacy.

---

## Product Principles

1. **Authorization First**: Every request must be validated against SAP SuccessFactors Role-Based Permissions before any data is retrieved or returned.
2. **Privacy by Design**: GDPR and CCPA compliance rules are applied as a mandatory layer before any response is delivered — not as an afterthought.
3. **Least Privilege**: The agent retrieves only the minimum data required to answer the specific request.
4. **Auditability**: Every interaction — request, authorization outcome, response summary — is recorded for compliance traceability.
5. **Graceful Failure**: When authorization fails or data is unavailable, the agent returns a clear, actionable message rather than an error dump.

---

## Goals and Non-Goals

### Goals (In Scope)
- Natural language HR request ingestion and intent classification via the Joule interface.
- Authorization validation against SAP SuccessFactors Role-Based Permissions (3-tier: employee, manager, HR admin).
- Data retrieval for: payslips, leave balances, employment contracts, personal information, compensation summaries.
- Secure A2A invocation of the external document-generation agent to fetch PDF documents or structured data.
- GDPR and CCPA field-level privacy redaction applied before every response.
- Clear access-denied messaging when authorization fails.
- Append-only audit log capturing all interactions (file-based, Phase 1).

### Non-Goals (Out of Scope)
- Modification of any HR data in SAP SuccessFactors (read-only agent).
- Configuration or administration of SAP SuccessFactors Role-Based Permissions.
- Payroll calculations or tax computations.
- Persistent database storage for audit logs (file-based placeholder in Phase 1; migration out of scope).
- Support for HR processes outside document and data retrieval (e.g., leave requests, onboarding workflows).

---

## Requirements

### Must-Have Requirements

**REQ-01**: Natural Language Request Ingestion & Intent Classification

- **Problem to Solve**: Employees have no way to ask HR questions in plain language without navigating multiple portals or raising tickets.
- **User Story**: As an employee, I need to type a natural language HR question so that the agent understands what I need and routes it correctly.
- **Acceptance Criteria**:
  - Given the user submits a message via Joule, when the agent receives it, then it classifies the intent into one of the defined categories: payslip, leave balance, employment contract, personal information, compensation.
  - Given an ambiguous request, when the agent cannot classify intent with confidence, then it asks a single clarifying question before proceeding.
- **Maps to Objective**: Objective 1
- **Priority Rank**: 1

**REQ-02**: Authorization Validation via SAP SuccessFactors Role-Based Permissions

- **Problem to Solve**: HR data is sensitive and must only be accessible to users with the appropriate rights; there is currently no automated check in the self-service flow.
- **User Story**: As an HR admin, I need the agent to verify permissions before returning any data so that employees cannot access records they are not entitled to see.
- **Acceptance Criteria**:
  - Given a request for HR data, when the agent queries the SuccessFactors Role-Based Permissions API, then it proceeds only if the requester is authorized for that data type and scope.
  - Given an unauthorized request, when the authorization check fails, then the agent returns a clear access-denied message without exposing any underlying data.
  - Given an employee query, when the scope is validated, then the agent enforces: employees see own data only; managers see direct reports; HR admins see all.
- **Maps to Objective**: Objective 2
- **Priority Rank**: 2

**REQ-03**: HR Data Retrieval via SAP SuccessFactors APIs (MCP)

- **Problem to Solve**: HR data is locked in SAP SuccessFactors with no conversational retrieval interface.
- **User Story**: As an employee, I need the agent to fetch my payslip, leave balance, personal information, employment contract, or compensation data so that I can get the information I need without logging into separate systems.
- **Acceptance Criteria**:
  - Given a successful authorization check, when the agent calls the relevant SuccessFactors API via MCP, then it returns the requested data payload.
  - Given a failed API call, when SuccessFactors is unavailable, then the agent returns a graceful error message and logs the failure.
  - The following data types must be supported: payslip/payroll, leave balances, employee profile, personal information, compensation information, employment information.
- **Maps to Objective**: Objective 1
- **Priority Rank**: 3

**REQ-04**: External Document/PDF Retrieval via A2A Protocol

- **Problem to Solve**: Generated HR documents (e.g., payslip PDFs) are produced by an external agent and are not directly accessible via SuccessFactors APIs.
- **User Story**: As an employee, I need the agent to securely retrieve generated PDF documents from the external document-generation service so that I can receive the actual document or a summary of it.
- **Acceptance Criteria**:
  - Given a request that requires a generated document, when the agent invokes the external agent at [EXTERNAL_AVIATOR_AGENT_ENDPOINT] via A2A protocol, then it receives the document or data payload.
  - Given a failure in A2A communication, when the external agent is unreachable, then the agent notifies the user and logs the error.
- **Maps to Objective**: Objective 4
- **Priority Rank**: 4

**REQ-05**: GDPR & CCPA Privacy Compliance Layer

- **Problem to Solve**: HR data contains highly sensitive personal information; returning raw data without redaction could violate data privacy regulations.
- **User Story**: As an HR admin, I need all agent responses to have sensitive fields redacted or masked according to GDPR and CCPA rules so that the organization remains compliant with data privacy regulations.
- **Acceptance Criteria**:
  - Given a data payload is ready for response, when the privacy layer processes it, then fields not permitted for the requesting role under GDPR and CCPA are redacted before the response is returned.
  - Given any response containing personal data, when delivered to the user, then it is accompanied by a data privacy notice.
- **Maps to Objective**: Objective 3
- **Priority Rank**: 5

**REQ-06**: Access-Denied Response Handling

- **Problem to Solve**: When a user requests data they are not authorized to access, the system must communicate this clearly without leaking information.
- **User Story**: As an employee, I need a clear message when I am not authorized to access requested data so that I understand the limitation and know what to do next.
- **Acceptance Criteria**:
  - Given an authorization failure, when the agent responds, then the message states that access is denied, does not expose any data fragments, and optionally directs the user to their HR contact.
- **Maps to Objective**: Objective 2
- **Priority Rank**: 6

**REQ-07**: Audit Log for All Interactions

- **Problem to Solve**: There is no traceability mechanism for HR data access requests, creating a compliance gap.
- **User Story**: As an HR admin, I need every agent interaction to be logged so that we can audit who requested what data and when, and what was returned.
- **Acceptance Criteria**:
  - Given any interaction (successful or failed), when the agent completes processing, then it appends a structured log entry to the audit file containing: timestamp, user identity, request summary, authorization result, and response summary.
  - The audit log file must be append-only and must not contain full raw data payloads (summaries only).
- **Maps to Objective**: Objective 5
- **Priority Rank**: 7

---

### High-Want Requirements

**REQ-08**: Conversation Context Retention Within a Session

- **Problem to Solve**: Users asking follow-up questions within the same session currently need to repeat context.
- **User Story**: As an employee, I need the agent to remember context within a conversation session so that I can ask follow-up questions without repeating myself.
- **Priority Rank**: 1

**REQ-09**: Multilingual Support

- **Problem to Solve**: Global organizations have employees who communicate in languages other than English.
- **User Story**: As an employee, I need to interact with the agent in my preferred language so that language is not a barrier to accessing my HR information.
- **Priority Rank**: 2

---

### Nice-to-Have Requirements

**REQ-10**: Proactive Leave Balance Notifications

- **Problem to Solve**: Employees are often unaware of expiring leave balances until it is too late.
- **Priority Rank**: 1

**REQ-11**: Persistent Audit Log Storage

- **Problem to Solve**: File-based audit logging is a temporary solution that does not scale.
- **Priority Rank**: 2

---

## Non-Functional Requirements

### Performance
- **Latency**: Agent must return a response within 45 seconds for 95% of requests.
- **Throughput**: Must support concurrent requests from multiple users without degradation.

### Reliability
- **Availability**: Agent should follow SAP BTP platform SLA.
- **Fallback**: If SuccessFactors API or external agent is unavailable, return a user-friendly message and log the failure; do not surface raw errors.

### Security
- All SuccessFactors API calls must use the current user's security context (OAuth 2.0 / SAML propagation).
- A2A communication to the external agent must be authenticated and encrypted in transit.
- The audit log file must be access-controlled at the file system level.

### Explainability
- **Traceability**: Each response must be traceable to the specific API call and data payload that produced it via the milestone log.
- **Decision Logging**: Authorization decisions (granted/denied) must be logged with the role scope evaluated.
- **Uncertainty Communication**: If the agent cannot classify intent with sufficient confidence, it must communicate this to the user rather than guessing.

---

## Solution Architecture

**Architecture Overview:**  
A Python-based AI agent deployed on SAP BTP, exposed via the Joule interface using the A2A protocol. The agent uses generated MCP translation files to call SAP SuccessFactors APIs for authorization and data retrieval, invokes an external document-generation agent via A2A, applies a privacy redaction layer, and writes to a file-based audit log.

**Key Components:**

- **HR Assistant Agent** (Python, A2A): Core reasoning agent; orchestrates all steps.
- **MCP Translation Files** (×6): Interface layer between the agent and SAP SuccessFactors APIs (Role-Based Permissions, Employee Profile, Payroll, Leave Balances, Compensation, Employment Information).
- **A2A Client**: Secure communication module for invoking the external document-generation agent.
- **Privacy Redaction Layer**: Custom module applying GDPR and CCPA field-level redaction rules per user role.
- **Audit Logger**: Append-only file writer capturing structured interaction records.

**Integration Points:**

- **SAP SuccessFactors** (via MCP): Read-only data retrieval across 6 API domains; user security context propagated.
- **External Document-Generation Agent** (via A2A): Retrieval of generated PDF documents and structured data payloads; placeholder endpoint [EXTERNAL_AVIATOR_AGENT_ENDPOINT].
- **Joule Interface**: User-facing entry point for natural language requests.

**Deployment Environments:**

- **Dev**: Local agent development and unit testing with mocked MCP responses.
- **QA**: Integration testing against a SuccessFactors sandbox tenant; A2A endpoint stubbed.
- **Prod**: Full deployment on SAP BTP with live SuccessFactors APIs and external agent endpoint.

---

### Agent Extensibility & Instrumentation

**Agent Extensibility:**
The agent must be designed with clear extension points to allow future HR capabilities to be added without rearchitecting the core:
- New HR data domains (e.g., performance reviews, training records) should be addable by registering new MCP tools.
- The privacy redaction rules should be configurable externally to accommodate new regulations or jurisdictions.
- The A2A client should support multiple external agent endpoints for future multi-agent scenarios.

**Business Step Instrumentation:**
All five business milestones must be instrumented with structured log statements. Log format: `[MILESTONE_ID].[achieved|missed]: [description]`. This enables production monitoring, debugging, and SLA measurement against the < 45-second response target.

---

### Automation & Agent Behaviour

**Automation Level:** Autonomous agent with authorization guardrails

**Actions the system performs without human approval:**
- Intent classification of natural language HR requests.
- Authorization validation against SuccessFactors Role-Based Permissions.
- Data retrieval from SuccessFactors APIs.
- A2A invocation of the external document-generation agent.
- Privacy redaction and response formulation.
- Audit log entry writing.

**Actions that require human review or approval:**
- None in the standard flow; all actions are read-only.
- Any unresolvable authorization ambiguity escalates to an access-denied response directing the user to HR.

**Model or engine used:** Large language model via SAP Generative AI Hub (model selection per deployment configuration).

**Knowledge & data sources accessed:**
- SAP SuccessFactors Employee Central (employee profile, payroll, leave, compensation, employment information): live API calls per request.
- SAP SuccessFactors Role-Based Permissions API: per-request authorization check.
- External document-generation agent (A2A): on-demand PDF and data retrieval.

**Tools or connectors invoked:**
- `PLTRoleBasedPermissions` MCP tool: check user authorization (read-only)
- `ECEmployeeProfile` MCP tool: retrieve employee profile data (read-only)
- `ECEmployeeCentralPayroll` MCP tool: retrieve payslip and payroll data (read-only)
- `Balances` MCP tool: retrieve leave balances and time-off data (read-only)
- `ECCompensationInformation` MCP tool: retrieve compensation and benefits data (read-only)
- `ECEmploymentInformation` MCP tool: retrieve employment contract data (read-only)
- External document-generation agent (via A2A call): fetch generated PDF documents or data payloads (read-only)

**Guardrails & fail-safes:**
- The agent must never modify, create, or delete any data in SAP SuccessFactors.
- Authorization check must always complete before any data retrieval call is made; no exceptions.
- If authorization returns denied or errors, the agent must stop processing and return an access-denied message immediately.
- If the privacy redaction step fails for any reason, the agent must not return the unredacted data — it must return a safe error message instead.
- If A2A communication fails, the agent must return a graceful error and log the failure; it must not retry indefinitely.
- All responses must be scoped to data the user is explicitly entitled to see.

---

## Governance, Risk & Compliance

**Data Handling:**
- All data retrieved from SAP SuccessFactors is processed in-memory only; no raw data is persisted.
- PII and sensitive payroll data must be redacted to the applicable GDPR and CCPA standards before inclusion in any response.
- Audit log entries contain summaries only — no raw personal data payloads.
- Data residency: all processing must occur within the SAP BTP region configured for the tenant.

**Compliance Frameworks:**
- GDPR (EU Regulation 2016/679): Right of access, data minimization, purpose limitation.
- CCPA (California Consumer Privacy Act): Disclosure and access rights for California residents.
- SAP SuccessFactors Role-Based Permissions: governs data access authorization at the source.

**Approval Flows:**
- The agent operates in read-only mode; no approval flows are required for data retrieval.
- Any future write-capable extensions must include a human-in-the-loop approval step.

---

## Release Criteria

- **Performance**: 95% of agent responses delivered within 45 seconds under normal load.
- **Authorization**: 100% of requests validated against SuccessFactors Role-Based Permissions before data retrieval.
- **Privacy**: 100% of responses pass the GDPR/CCPA redaction check before delivery; verified by automated test suite.
- **Audit**: 100% of interactions (successful and failed) produce an audit log entry.
- **Reliability**: Access-denied and error states return user-friendly messages in 100% of cases — no raw stack traces exposed.
- **Security**: A2A communication encrypted in transit; SuccessFactors API calls use the requesting user's security context.

---

## Schedule & Timeline Context

**Target Timeline:** 3 months from project kick-off.

**Business Drivers:**
- HR team capacity is constrained by the volume of routine Tier-1 inquiries; every month of delay represents continued avoidable workload.
- Employee satisfaction with HR responsiveness is a tracked metric; the current 2-day response time is an identified pain point.

---

## Milestones

### M1: Request Ingestion & Intent Classification

- **Description**: The agent receives a natural language HR request via Joule and successfully classifies the intent into a known category (payslip, leave balance, employment contract, personal information, compensation).
- **Achieved when**: Intent category is assigned with sufficient confidence and the request is ready for authorization.
- **Log on achievement**: `M1.achieved: intent classified as [category] for user [user_id]`
- **Log on miss**: `M1.missed: intent classification failed or produced ambiguous result for user [user_id]`

### M2: Authorization Validated

- **Description**: The agent has queried SAP SuccessFactors Role-Based Permissions and received a definitive authorization outcome (granted or denied) for the requesting user and requested data scope.
- **Achieved when**: Authorization result is received and is either granted (proceed) or denied (return access-denied message).
- **Log on achievement**: `M2.achieved: authorization [granted|denied] for user [user_id] on scope [data_scope]`
- **Log on miss**: `M2.missed: authorization check failed or timed out for user [user_id]`

### M3: External Agent Invoked via A2A

- **Description**: The agent has successfully communicated with the external document-generation agent at [EXTERNAL_AVIATOR_AGENT_ENDPOINT] and received the requested document or data payload.
- **Achieved when**: A2A call completes and a valid payload or document reference is returned.
- **Log on achievement**: `M3.achieved: A2A invocation successful, payload received for user [user_id]`
- **Log on miss**: `M3.missed: A2A invocation failed or returned no payload for user [user_id]`

### M4: Privacy-Compliant Response Delivered

- **Description**: The agent has applied GDPR and CCPA redaction rules to the retrieved data and delivered a clear, governed natural language response to the user.
- **Achieved when**: Privacy layer completes successfully and response is sent to the user via Joule.
- **Log on achievement**: `M4.achieved: privacy-compliant response delivered to user [user_id] for category [category]`
- **Log on miss**: `M4.missed: privacy redaction failed or response delivery error for user [user_id]`

### M5: Audit Log Written

- **Description**: A structured audit log entry has been appended to the audit file capturing the full interaction record.
- **Achieved when**: Audit log entry is written without error after every interaction (successful or failed).
- **Log on achievement**: `M5.achieved: audit log entry written for interaction [interaction_id]`
- **Log on miss**: `M5.missed: audit log write failed for interaction [interaction_id]`

---

## Risks, Assumptions, and Dependencies

### Risks
- **External agent endpoint availability**: [EXTERNAL_AVIATOR_AGENT_ENDPOINT] is a placeholder; until the real endpoint is confirmed, A2A integration cannot be fully tested.
- **MCP translation file coverage**: No pre-built MCP servers exist for the required SuccessFactors APIs; all 6 translation files must be generated and validated, which may surface API schema gaps.
- **Privacy redaction completeness**: GDPR/CCPA field mapping must be defined for each of the 6 data domains; incomplete mapping could result in non-compliant responses.

### Assumptions
- SAP SuccessFactors Role-Based Permissions API accurately reflects the organization's configured access policies.
- The requesting user's identity is propagated correctly from the Joule interface to the agent's security context.
- The external document-generation agent supports the A2A protocol and returns structured payloads.
- The file-based audit log is acceptable for Phase 1; persistent storage migration is a separate workstream.

### Dependencies
- SAP SuccessFactors tenant with Role-Based Permissions configured for the 3-tier access model.
- External document-generation agent endpoint confirmed and accessible from SAP BTP.
- SAP Generative AI Hub model availability and quota.
- Joule interface configured to route HR assistant requests to this agent.

---

## Open Questions

- What is the confirmed endpoint URL for the external document-generation agent (replacing [EXTERNAL_AVIATOR_AGENT_ENDPOINT])?
- Which specific fields in each SuccessFactors data domain must be redacted under GDPR and CCPA?
- Is there a maximum data retention period for the file-based audit log before entries must be purged?
- Should the agent support document download links or only inline summaries for PDF documents?

---

## Appendix

### Glossary

- **A2A (Agent-to-Agent)**: A protocol for structured, authenticated communication between AI agents.
- **MCP (Model Context Protocol)**: A standardized interface that exposes API capabilities as tools callable by AI agents.
- **RBP (Role-Based Permissions)**: SAP SuccessFactors' authorization framework controlling which users can access which data.
- **GDPR**: General Data Protection Regulation — EU data privacy law.
- **CCPA**: California Consumer Privacy Act — California data privacy law.
- **Tier-1 HR Inquiry**: A routine, self-service HR request that does not require HR specialist judgment (e.g., "What is my leave balance?").

### References
- SAP SuccessFactors Role-Based Permissions API: `sap.sf:apiResource:PLTRoleBasedPermissions:v1`
- SAP SuccessFactors Employee Profile API: `sap.sf:apiResource:ECEmployeeProfile:v1`
- SAP SuccessFactors Payroll API: `sap.sf:apiResource:ECEmployeeCentralPayroll:v1`
- SAP SuccessFactors Time Off Balances API: `sap.sf:apiResource:Balances:v1`
- SAP SuccessFactors Compensation Information API: `sap.sf:apiResource:ECCompensationInformation:v1`
- SAP SuccessFactors Employment Information API: `sap.sf:apiResource:ECEmploymentInformation:v1`
- SAP BTP AI Agent Development Guidelines
- GDPR Official Text: https://gdpr-info.eu
- CCPA Official Text: https://oag.ca.gov/privacy/ccpa
