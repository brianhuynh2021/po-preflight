# PO Preflight Product Requirements Document

| Field | Value |
|---|---|
| Product | PO Preflight |
| Document status | Draft for management review |
| Version | 0.1 |
| Date | July 24, 2026 |
| Product owner | To be assigned |
| Initial release | Internal MVP |

## 1. Executive summary

PO Preflight is an AI-assisted purchase-order intake and validation product for small and midsize distributors, manufacturers, and service companies.

The product converts purchase orders received as PDF, Excel, CSV, text, or structured files into normalized order data. It validates each order against the company's product catalog, pricing rules, inventory, product status, and duplicate-order history. It then routes exceptions to an authorized reviewer through Slack or a web dashboard and records a complete audit trail.

PO Preflight does not autonomously approve orders or write to an ERP in the MVP. AI assists with document extraction and explanation; deterministic business rules make validation decisions; authorized employees retain control over approval and downstream actions.

The internal MVP will prove whether Preflight can reduce manual order pre-check time, catch commercial errors before ERP entry, and provide a reusable product foundation that can later be offered to external customers.

## 2. Business problem

Many companies receive purchase orders through email, messaging applications, shared folders, and spreadsheets. Operations employees manually read each document, retype line items, compare prices, check inventory, identify invalid products, and ask managers to resolve exceptions.

This process creates several recurring problems:

- Manual data entry consumes operations capacity.
- Different customer formats require repeated interpretation.
- Pricing discrepancies may be discovered late.
- Out-of-stock or inactive products may enter downstream workflows.
- Duplicate PO numbers may be processed more than once.
- Approvals are scattered across chat, email, and verbal conversations.
- Management has limited visibility into order status and bottlenecks.
- Audit evidence is difficult to reconstruct.

Generic AI chat and message summarization do not solve this problem because they do not enforce catalog rules, maintain transaction state, route approvals, or create a reliable audit trail.

## 3. Product vision

Enable an operations employee to submit any supported purchase order and receive a validated, review-ready order within minutes, while preserving human control and a complete record of every decision.

Long-term vision:

> PO Preflight becomes the intelligent order-intake layer between customer documents and existing ERP systems.

## 4. Product principles

1. **Human authority:** AI may recommend; authorized employees decide.
2. **Deterministic validation:** Prices, SKUs, inventory, duplicates, and approval thresholds are evaluated by explicit rules.
3. **Evidence before action:** Every finding must reference extracted order data and the applicable business rule.
4. **No silent mutation:** The product must not modify an ERP, catalog, or order without an explicit authorized action.
5. **Auditability:** Every extraction, rule result, correction, approval, and integration action must be recorded.
6. **Channel flexibility:** Slack and web are interfaces to one product, not separate sources of truth.
7. **Secure by default:** Credentials and customer data remain outside source control and access is restricted by role.
8. **English-only product:** Source code, documentation, UI, logs, and generated reports use English in the initial release.

## 5. Goals

### 5.1 MVP goals

- Accept purchase orders through a web upload and Slack workflow.
- Extract order header and line-item data from supported documents.
- Validate orders against catalog, price, inventory, product status, and duplicate rules.
- Show findings with severity and recommended next action.
- Allow authorized reviewers to approve, reject, or request changes.
- Store analyses and decisions in an auditable database.
- Demonstrate an end-to-end workflow using realistic synthetic data.
- Deploy through repeatable CI/CD to an AWS-hosted environment after local validation.

### 5.2 Business goals

- Reduce time spent on manual order pre-checks.
- Catch order errors before ERP entry.
- Improve approval turnaround and visibility.
- Establish a reusable product that can be configured for multiple customers.
- Validate willingness to pay through internal adoption and external demonstrations.

## 6. Non-goals for the MVP

- Autonomous ERP order creation.
- Reliable OCR for low-quality scanned documents.
- Tax, legal, or regulatory compliance certification.
- Customer credit decisions.
- Demand forecasting.
- Inventory reservation.
- Payment processing.
- Automatic price correction.
- Full contract management.
- Native mobile applications.
- Support for every ERP or messaging platform.

## 7. Target customers

### 7.1 Primary segment

Small and midsize distributors and manufacturers that:

- Process recurring customer purchase orders.
- Receive orders in multiple file formats.
- Use manual or semi-manual ERP entry.
- Maintain a product catalog and inventory data.
- Need manager approval for commercial exceptions.
- Prefer a lightweight product over a large order-management replacement.

### 7.2 Secondary segment

Service companies that receive structured work orders, equipment requests, or procurement requests and need validation and approval before internal processing.

## 8. Personas

### 8.1 Order operations specialist

**Objective:** Convert incoming customer POs into correct internal orders quickly.

**Pain points:** Repetitive typing, inconsistent document formats, missing information, price checking, and status follow-up.

**Primary actions:** Submit orders, review extraction, correct data, request clarification, and monitor status.

### 8.2 Sales manager

**Objective:** Resolve commercial exceptions without delaying customers.

**Pain points:** Incomplete context, approvals hidden in messages, and no consistent record of decisions.

**Primary actions:** Review price exceptions, approve, reject, or request changes.

### 8.3 Finance or operations manager

**Objective:** Maintain policy control and process visibility.

**Pain points:** Duplicate orders, inconsistent approvals, weak audit evidence, and unclear bottlenecks.

**Primary actions:** Configure thresholds, inspect audit history, and review process metrics.

### 8.4 System administrator

**Objective:** Operate the service securely and reliably.

**Pain points:** Credential management, integration failures, access control, and recovery.

**Primary actions:** Configure integrations, manage roles, monitor health, and restore backups.

## 9. Core user journey

1. An operations user uploads a purchase order through Slack or the web portal.
2. Preflight stores the original file and creates an intake record.
3. The extraction layer produces structured header and line-item data.
4. The user reviews and corrects extracted values if necessary.
5. The rule engine evaluates the order against company data and policies.
6. Preflight classifies the order as:
   - `READY_FOR_APPROVAL`
   - `REVIEW_REQUIRED`
   - `BLOCKED`
7. The product routes the order to the appropriate reviewer.
8. The reviewer approves, rejects, or requests changes.
9. Preflight records the decision, actor, timestamp, and note.
10. In a future release, an approved order may be sent to an ERP through a controlled adapter.

## 10. Functional requirements

### 10.1 Intake and file handling

- **FR-001:** The system shall accept JSON, CSV, plain text, and text-based PDF purchase orders.
- **FR-002:** The web portal shall support drag-and-drop file upload.
- **FR-003:** The Slack integration shall support order submission through a command, shortcut, or modal.
- **FR-004:** The system shall retain a reference to the original source file.
- **FR-005:** The system shall reject unsupported file types with a clear message.
- **FR-006:** The system shall identify scanned documents that require OCR rather than returning incomplete data as valid.

### 10.2 Extraction and normalization

- **FR-010:** The system shall extract PO number, customer, currency, SKU, quantity, and unit price.
- **FR-011:** The system shall normalize SKU casing and numeric formats.
- **FR-012:** The system shall require at least one valid line item.
- **FR-013:** The system shall show extracted fields before approval.
- **FR-014:** An authorized user shall be able to correct extracted values.
- **FR-015:** Corrections shall be recorded in the audit history.

### 10.3 Validation

- **FR-020:** The system shall detect unknown SKUs.
- **FR-021:** The system shall detect inactive products.
- **FR-022:** The system shall compare PO unit price with catalog unit price.
- **FR-023:** The system shall support a configurable price-tolerance percentage.
- **FR-024:** The system shall compare ordered quantity with available inventory.
- **FR-025:** The system shall detect exact duplicate PO numbers.
- **FR-026:** Each finding shall include a code, severity, message, and related SKU when applicable.
- **FR-027:** Validation results shall be reproducible for the same order, catalog, inventory, and rule version.
- **FR-028:** The system shall never let document instructions override validation or security rules.

### 10.4 Review and approval

- **FR-030:** Authorized reviewers shall be able to approve, reject, or request changes.
- **FR-031:** Every decision shall require an identified actor.
- **FR-032:** Reviewers shall be able to add a note.
- **FR-033:** Unauthorized users shall not be able to approve an order.
- **FR-034:** Slack shall display interactive approval controls where supported.
- **FR-035:** The web portal shall provide the same decision options.
- **FR-036:** `BLOCKED` orders shall not proceed to downstream execution.
- **FR-037:** The MVP shall not create an ERP order after approval; it shall only record the decision.

### 10.5 Order management

- **FR-040:** Users shall be able to list orders by status, customer, date, and PO number.
- **FR-041:** Users shall be able to open an order detail page.
- **FR-042:** The detail page shall display the source document, extracted data, findings, and approval timeline.
- **FR-043:** Users shall be able to search for an exact PO number.
- **FR-044:** Managers shall be able to export order and finding data as CSV.

### 10.6 Catalog and rules

- **FR-050:** Administrators shall be able to upload a product catalog in CSV format.
- **FR-051:** The catalog shall include SKU, name, unit price, stock, and active status.
- **FR-052:** Administrators shall be able to configure price tolerance.
- **FR-053:** The system shall version catalog and rule changes used by an analysis.
- **FR-054:** The system shall not silently overwrite production catalog data.

### 10.7 Audit and observability

- **FR-060:** The system shall record intake, extraction, validation, correction, decision, and integration events.
- **FR-061:** Audit events shall include actor, timestamp, action, entity identifier, and relevant metadata.
- **FR-062:** Audit records shall not be editable through the normal product UI.
- **FR-063:** Administrators shall be able to inspect processing errors.
- **FR-064:** The service shall expose health and readiness checks.

## 11. User experience requirements

### 11.1 Slack experience

The Slack application shall provide:

- A `Submit Purchase Order` modal.
- A review card containing PO number, customer, total, item count, and findings.
- `View Details`, `Approve`, `Reject`, and `Request Changes` actions.
- Thread-based conversation for each order.
- Permission-aware approval actions.
- A clear statement that no ERP order was created.

### 11.2 Web dashboard

The web application shall provide:

1. **Orders list** with search and filters.
2. **Order detail** with source preview and extracted data side by side.
3. **Validation panel** grouped by error and warning severity.
4. **Approval timeline** showing each actor and event.
5. **Catalog management** for upload and inspection.
6. **Rules settings** for price tolerance and approval thresholds.
7. **Audit log** for authorized managers and administrators.

### 11.3 Accessibility and clarity

- Status must never depend on color alone.
- Error and warning messages must identify the affected field or SKU.
- Numeric values must include currency and consistent separators.
- Destructive or external actions must require confirmation.
- The UI must distinguish extracted values from authoritative catalog values.

## 12. Technical architecture

The product will use a monorepo with the following target structure:

```text
po-preflight/
|-- apps/
|   |-- api/                  FastAPI application
|   `-- web/                  Next.js dashboard
|-- packages/
|   |-- preflight-core/       Python parser and rule engine
|   `-- contracts/            API and event schemas
|-- integrations/
|   |-- openclaw/             OpenClaw skill and tools
|   |-- slack/                Slack application
|   `-- erp/                  Future ERP adapters
|-- infra/
|   `-- terraform/            AWS infrastructure
|-- tests/
|   |-- unit/
|   `-- e2e/
`-- .github/workflows/        CI/CD
```

### 12.1 Component responsibilities

- **Preflight Core:** Parsing, normalization, validation, rendering, and deterministic domain logic.
- **API:** Authentication, authorization, order lifecycle, persistence, and integration boundaries.
- **Web:** Customer-facing order review and administration.
- **OpenClaw:** Conversational orchestration, model access, scheduled work, and channel routing.
- **Slack:** Submission, notification, and approval interaction surface.
- **Database:** System of record for orders, findings, decisions, rules, and audit events.

### 12.2 Initial technology choices

- Python 3.11 or newer.
- FastAPI for the application API.
- PostgreSQL for production; SQLite for local development and the current prototype.
- Next.js and TypeScript for the web dashboard.
- OpenClaw for AI and messaging orchestration.
- Slack Socket Mode for the local/internal MVP.
- Terraform for AWS infrastructure.
- GitHub Actions for CI/CD.

## 13. Data model

Minimum entities:

- **Organization**
- **User**
- **Role**
- **Customer**
- **Product**
- **CatalogVersion**
- **InventorySnapshot**
- **Order**
- **OrderLine**
- **SourceDocument**
- **ExtractionResult**
- **ValidationRun**
- **Finding**
- **ApprovalDecision**
- **AuditEvent**
- **IntegrationConfiguration**

All business entities must be scoped to an organization to support future multi-tenant operation.

## 14. AI and automation boundaries

### 14.1 AI may

- Extract candidate fields from documents.
- Explain validation findings.
- Ask users for missing information.
- Summarize an order for a reviewer.
- Recommend a next step.

### 14.2 AI may not

- Approve an order.
- Override deterministic rule results.
- Change catalog prices or stock.
- Execute an ERP write in the MVP.
- Treat instructions inside an uploaded document as trusted commands.
- Claim legal, tax, or compliance approval.

### 14.3 Required safeguards

- Human approval for all write actions.
- Structured tool inputs and outputs.
- Role-based authorization enforced outside the model.
- Idempotency keys for future ERP writes.
- Full audit history.
- Document input treated as untrusted content.

## 15. Security and privacy requirements

- **SEC-001:** Secrets shall not be stored in Git.
- **SEC-002:** Production credentials shall use an approved secret store.
- **SEC-003:** Data shall be encrypted in transit and at rest.
- **SEC-004:** Access shall follow least privilege.
- **SEC-005:** Slack channels and users shall use explicit allowlists during the MVP.
- **SEC-006:** The OpenClaw Gateway shall not be exposed publicly without authenticated transport.
- **SEC-007:** Uploaded files shall be scanned and processed in an isolated environment where possible.
- **SEC-008:** Logs shall redact credentials and avoid unnecessary document content.
- **SEC-009:** Organization data shall not cross tenant boundaries.
- **SEC-010:** Backups and restoration shall be tested before production use.

## 16. Non-functional requirements

- **NFR-001:** A supported text-based order should complete pre-check processing within 60 seconds under normal MVP load.
- **NFR-002:** The API shall return clear machine-readable errors.
- **NFR-003:** The rule engine shall be unit-tested independently of AI services.
- **NFR-004:** Duplicate submissions shall not create duplicate downstream actions.
- **NFR-005:** The product shall continue to expose existing audit records if the AI provider is temporarily unavailable.
- **NFR-006:** CI shall run tests, secret-pattern checks, and infrastructure validation.
- **NFR-007:** Deployment shall be repeatable from source control.
- **NFR-008:** Production data shall persist across application deployments.

## 17. MVP acceptance criteria

The MVP is accepted when all of the following are demonstrated:

1. A user submits a supported purchase-order file.
2. Preflight extracts PO number, customer, currency, SKU, quantity, and unit price.
3. The user can inspect extracted data.
4. The system detects at least:
   - one price discrepancy,
   - one inventory shortage,
   - one unknown or inactive SKU,
   - one duplicate PO number.
5. A reviewer can approve, reject, or request changes.
6. Unauthorized approval is denied.
7. The decision appears in the audit timeline.
8. No ERP order is created.
9. Unit and end-to-end tests pass in CI.
10. The application can be deployed to a controlled AWS environment through the documented pipeline.

## 18. Success metrics

### 18.1 Product metrics

- Median time from upload to review-ready result.
- Percentage of supported orders successfully normalized.
- Percentage of extractions corrected by a human.
- Number of issues found before ERP entry.
- Approval turnaround time.
- Percentage of orders blocked, reviewed, approved, and rejected.
- Duplicate POs detected.
- Processing cost per order.

### 18.2 Initial target outcomes

Targets must be validated during the pilot rather than treated as guaranteed performance:

- Reduce manual pre-check time by at least 70% for supported formats.
- Produce a review-ready result within 60 seconds for normal text-based orders.
- Record 100% of approval decisions with actor and timestamp.
- Prevent 100% of unauthorized or unapproved ERP writes in the MVP.
- Detect 100% of exact duplicate PO numbers already present in the Preflight database.

## 19. Delivery plan

### Phase 0: Working prototype - complete

- Python parser and rule engine.
- JSON, CSV, text, and optional text-based PDF support.
- Catalog and inventory validation.
- Duplicate detection.
- SQLite audit history.
- OpenClaw skill.
- Automated tests.
- Initial CI/CD and Terraform files.

### Phase 1: Internal web MVP

- Monorepo restructuring.
- FastAPI service.
- PostgreSQL schema and migrations.
- Order upload and list APIs.
- Minimal Next.js dashboard.
- Order detail, findings, and audit timeline.
- Authentication and role-based access.

### Phase 2: Slack workflow

- Slack application setup.
- Submit-order modal.
- Review cards and notifications.
- Approval buttons.
- User and channel allowlists.
- Slack-to-web deep links.

### Phase 3: Pilot hardening

- Text-based PDF extraction quality evaluation.
- OCR proof of concept for scanned orders.
- Catalog import workflow.
- Metrics and monitoring.
- Backup and recovery test.
- Security review.
- Internal pilot with a limited user group.

### Phase 4: External customer readiness

- Organization isolation.
- Configurable branding and rules.
- Customer onboarding workflow.
- Billing and usage metering.
- ERP adapter framework.
- Support runbooks and service-level objectives.

## 20. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Poor document extraction | Incorrect order data | Require human review, confidence indicators, and field correction |
| Scanned or low-quality PDFs | Failed extraction | Detect missing text layer and route to OCR/manual entry |
| Prompt injection in documents | Unauthorized behavior | Treat documents as untrusted, use structured tools, enforce policy outside AI |
| Stale catalog or inventory | Misleading findings | Version data sources and display last-updated timestamps |
| Unauthorized approval | Commercial or compliance risk | Enforce role checks in the API, not in prompts |
| Duplicate downstream actions | Duplicate ERP orders | Use idempotency keys and transaction records |
| Over-expansion of MVP scope | Delayed delivery | Keep ERP writes, advanced OCR, and multi-tenancy out of initial MVP |
| Vendor dependence | Cost or availability risk | Keep rule engine and system of record provider-independent |
| Sensitive data exposure | Customer and legal risk | Encryption, least privilege, redaction, isolation, and explicit retention policy |

## 21. Commercial packaging hypothesis

Preflight should be sold as an operational outcome, not as an OpenClaw installation or generic AI assistant.

Proposed positioning:

> Validate incoming customer purchase orders before ERP entry, reduce manual checks, and keep every exception and approval auditable.

Potential packaging:

- One-time implementation and workflow configuration fee.
- Monthly subscription based on order volume or active users.
- Private-cloud or customer-hosted deployment option.
- Additional fees for ERP connectors, OCR volume, and custom business rules.

Commercial assumptions require customer interviews and should not be treated as finalized pricing.

## 22. Demo scenario

The management demo should take no more than five minutes:

1. Open the Preflight dashboard.
2. Upload synthetic PO `PO-2026-1002`.
3. Show extracted customer, currency, SKUs, quantities, and prices.
4. Show a 4.86% price discrepancy.
5. Show two inventory shortages.
6. Display the Slack review notification.
7. Select `Request Changes` as an authorized reviewer.
8. Return to the dashboard and show the decision in the audit timeline.
9. State clearly that no ERP order was created.

## 23. Decisions requested from management

Management approval is requested for:

1. The PO Preflight product direction.
2. The initial internal department and pilot users.
3. Access to representative, sanitized purchase-order samples.
4. Access to a non-production catalog and inventory export.
5. Approval to create a restricted Slack application.
6. An MVP owner from operations or sales administration.
7. The target ERP for a future read-only integration assessment.
8. The success metrics and pilot review date.

## 24. Open questions

- Which department currently performs manual order entry?
- How many orders are processed per day and per month?
- What document formats are most common?
- Which fields are mandatory for an order to proceed?
- What is the authoritative source for catalog price and inventory?
- What price tolerances and approval thresholds apply?
- Who may approve commercial exceptions?
- Which ERP is currently used?
- What data-retention and hosting requirements apply?
- Is Slack available to all pilot users?

