# Enterprise HR Assistant Agent

## Business challenge

Employees, managers, HR business partners, and HR admins spend excessive time waiting for HR responses or manually retrieving HR documents such as payslips, leave balance statements, employment contracts, personal information, and compensation summaries. There is no intelligent, self-service channel available via the Joule interface to handle these routine Tier-1 requests automatically, with proper authorization enforcement, data privacy compliance, and audit traceability.

The solution must capture natural language HR requests via Joule, validate authorization against SAP SuccessFactors Role-Based Permissions, securely invoke an external document-generation agent (A2A protocol) to fetch the relevant data or PDF documents, apply GDPR and CCPA privacy compliance rules before responding, and log all interactions to an audit file.

## Business Goals & Success Criteria

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| HR response wait time | 2 days | < 1 hour | 3 months | Employee HR inquiry handling | user |
| Routine Tier-1 HR ticket volume (payslip, leave, policy) | — | Measurable reduction | 3 months | Payslip, leave balance, policy clarification | user |
| Agent response time per user prompt | — | < 45 seconds | 3 months | All HR agent interactions | user |
| Agent self-service rate (no human escalation) | — | > 75% of all HR inquiries | 3 months | End-to-end HR self-service | user |

## Key Milestones

1. **Request Ingestion** — User submits a natural language HR request via the Joule interface and the agent classifies the intent (payslip, leave, contract, personal info, compensation).
2. **Authorization Validated** — Agent queries SAP SuccessFactors Role-Based Permissions via MCP to confirm the requesting user has access to the requested data; access-denied message returned on failure.
3. **External Agent Invoked (A2A)** — Agent communicates via A2A protocol with the external document-generation agent ([EXTERNAL_AVIATOR_AGENT_ENDPOINT]) to retrieve the relevant PDF or data payload.
4. **Privacy-Compliant Response Delivered** — Agent applies GDPR and CCPA redaction rules, summarizes or extracts the requested information, and returns a clear, governed response to the user.
5. **Audit Log Written** — Interaction (request, authorization result, response summary, timestamp, user context) is appended to a local audit log file for traceability.

## Business Architecture (RBA)

### End-to-End Process

Recruit to Retire

### Process Hierarchy

```
Recruit to Retire (E2E)
└── Manage Workforce (generic)
    └── Manage employee information and reporting (BPS-385)
        └── Manage HR reports
    └── Manage payroll and reimbursements (BPS-394)
        └── Process payroll
        └── Manage payroll taxes and legal deductions
        └── Process expense reimbursements
    └── Manage time and attendance (BPS-393)
        └── Manage attendance and absence quotas
        └── Record absences
```

### Summary

An enterprise HR AI assistant enabling employees to retrieve payslip summaries, leave balances, employment contracts, personal information, and compensation statements maps to the Recruit to Retire E2E — specifically the Manage Workforce sub-processes for employee information & reporting, payroll & reimbursements, and time & attendance, with authorization validation and GDPR/CCPA data privacy compliance embedded across all interactions.

## Fit Gap Analysis

| Requirement (business) | Standard asset(s) found | API ORD ID | MCP Server ORD ID | MCP Server Version | Webhook API ORD ID | Data Product ORD ID | Gap? | Notes / assumptions |
|------------------------|------------------------|------------|-------------------|-------------------|-------------------|---------------------|------|---------------------|
| Authorization & permission check (Role-Based Permissions) | SAP SuccessFactors Employee Central | `sap.sf:apiResource:PLTRoleBasedPermissions:v1` | — | — | — | — | Yes | No MCP server found; MCP translation file must be generated |
| Employee profile & personal information retrieval | SAP SuccessFactors Employee Central | `sap.sf:apiResource:ECEmployeeProfile:v1` | — | — | — | — | Yes | No MCP server found; MCP translation file must be generated |
| Payslip / payroll data retrieval | SAP SuccessFactors Employee Central Payroll | `sap.sf:apiResource:ECEmployeeCentralPayroll:v1` | — | — | — | — | Yes | No MCP server found; MCP translation file must be generated |
| Leave balance & time-off retrieval | SAP SuccessFactors Employee Central | `sap.sf:apiResource:Balances:v1` | — | — | — | — | Yes | No MCP server found; MCP translation file must be generated |
| Compensation & benefits data retrieval | SAP SuccessFactors Employee Central | `sap.sf:apiResource:ECCompensationInformation:v1` | — | — | — | — | Yes | No MCP server found; MCP translation file must be generated |
| Employment contract / information retrieval | SAP SuccessFactors Employee Central | `sap.sf:apiResource:ECEmploymentInformation:v1` | — | — | — | — | Yes | No MCP server found; MCP translation file must be generated |
| External document/PDF generation (A2A) | None (external agent) | — | — | — | — | — | Yes | Custom A2A call to [EXTERNAL_AVIATOR_AGENT_ENDPOINT]; placeholder endpoint |
| GDPR & CCPA data privacy enforcement | None (custom build) | — | — | — | — | — | Yes | Custom privacy redaction/masking layer within agent logic |
| Audit log for conversation tracking | None (file-based placeholder) | — | — | — | — | — | Yes | File-based audit log; to be replaced with persistent storage |

### Key findings

- SAP SuccessFactors Employee Central covers all three identified sub-processes (employee info, payroll, time & attendance) as a mandatory product.
- 19 relevant SAP SuccessFactors APIs were discovered; no pre-built MCP servers exist — MCP translation files must be generated for each API used.
- The external document-generation agent integration requires a custom A2A protocol implementation against a placeholder endpoint.
- Data privacy compliance (GDPR and CCPA) is a custom layer — no standard SAP product covers automated response redaction for conversational agents.
- Role-based access follows three tiers: employees (own data only), managers (direct reports), HR admins (all employees).
- File-based audit logging is a temporary placeholder; the architecture should be designed for easy migration to a persistent store.

## Recommendations

### Enterprise HR Assistant Agent — Python AI Agent with SAP SuccessFactors MCP Integration

#### Executive Summary

Pro-code Python A2A agent integrating SuccessFactors via MCP

#### Recommended Solution

Build a Python-based AI agent (A2A protocol) deployed on SAP BTP that:
1. Accepts natural language HR requests via the Joule interface.
2. Validates authorization by calling SAP SuccessFactors Role-Based Permissions API via a generated MCP translation file.
3. Retrieves relevant HR data (payslip, leave balance, employment info, compensation, personal info) from SuccessFactors APIs via MCP tool calls.
4. Invokes the external document-generation agent via A2A protocol ([EXTERNAL_AVIATOR_AGENT_ENDPOINT]) to fetch generated PDF documents or structured data payloads.
5. Applies GDPR and CCPA privacy compliance rules (redacting sensitive fields based on requester role and regulation).
6. Returns a clear, governed natural language response to the user.
7. Appends all interactions to a local audit log file (to be replaced by persistent storage).

#### Affected User Roles

- Employees (self-service: own payslips, leave balances, personal info, contracts)
- Managers (team view: direct reports' employment data where permitted)
- HR Business Partners (broader data access per SuccessFactors RBP configuration)
- HR Admins (full access across all employees)

#### Recommended solution category

AI Agent

#### Intent fit
85%
