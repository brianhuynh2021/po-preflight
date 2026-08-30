# PO Preflight Architecture

This document describes the target architecture for PO Preflight and the path from a local demonstration to an enterprise multi-agent & multi-channel deployment.

## 1. System context

```mermaid
flowchart LR
    Customer["Customer or Operations User"]
    Reviewer["Sales or Operations Manager"]
    Admin["System Administrator"]
    MultiChannels["Channels: Telegram / Zalo / Slack / WeChat"]
    Web["Preflight Web Portal"]
    Preflight["PO Preflight (Agentic Brain + RAG)"]
    Catalog["Product Catalog & Vector Index"]
    ERP["ERP Adapter (Odoo / SAP)"]

    Customer -->|Submit purchase order| MultiChannels
    Customer -->|Upload and review| Web
    Reviewer -->|Instant Approve / Reject / Request Info| MultiChannels
    Reviewer -->|Review exceptions & audit| Web
    MultiChannels --> Preflight
    Web --> Preflight
    Admin -->|Configure rules and access| Preflight
    Catalog -->|SKU, price, status, vector search| Preflight
    Preflight -.->|Approved orders only| ERP
```

Preflight is the controlled intake layer between incoming purchase-order documents and downstream business systems. Multi-channel bots (Telegram, Zalo, Slack, WeChat) and the web portal are interfaces to the same workflow and audit trail.

## 2. Application containers

```mermaid
flowchart TB
    subgraph Channels["User Channels & Messaging"]
        TelegramBot["Telegram Bot"]
        ZaloOA["Zalo OA / ZNS"]
        SlackApp["Slack Application"]
        WeChatBot["WeChat Work Bot"]
        WebApp["Next.js Web Portal"]
    end

    subgraph Platform["Preflight Platform (MIT Outer + Stanford Inner Loop)"]
        API["FastAPI Gateway & Webhook Router"]
        Worker["Document Processing Worker"]
        AgentEngine["LangGraph Agentic Engine"]
        RAGService["SKU & Contract RAG (ChromaDB)"]
        Rules["Deterministic Zero-Token Rule Engine"]
        Audit["Audit Trail Service"]
    end

    subgraph Data["Data services"]
        DB[("PostgreSQL / SQLite")]
        VectorStore[("ChromaDB Vector Store")]
        Files[("S3 / Local Document Store")]
        Secrets["AWS Secrets Manager"]
    end

    subgraph External["Company systems"]
        CatalogAPI["Catalog and Inventory Source"]
        ERPAPI["ERP Adapter — Human Approved Only"]
    end

    TelegramBot --> API
    ZaloOA --> API
    SlackApp --> API
    WeChatBot --> API
    WebApp --> API
    API --> Worker
    Worker --> AgentEngine
    AgentEngine --> RAGService
    AgentEngine --> Rules
    RAGService --> VectorStore
    Rules --> CatalogAPI
    API --> Audit
    Worker --> Audit
    API --> DB
    Audit --> DB
    Worker --> Files
    API --> Secrets
    API -.-> ERPAPI
```

### Component responsibilities

| Component | Responsibility | MVP status |
|---|---|---|
| Next.js web portal | Upload, review, approval, search, and audit experience | Interactive prototype |
| Slack application | Submit orders and act on exception notifications | Planned |
| FastAPI application | Authentication, workflow state, business API, and integration boundary | Planned |
| Document worker | Extraction, normalization, validation orchestration, and retries | Local core available |
| Preflight core | Parsers, deterministic rules, reports, and audit decisions | Implemented |
| OpenClaw | AI-assisted extraction, explanation, channel orchestration, and skills | Local skill implemented |
| PostgreSQL | Durable orders, findings, decisions, rules, and tenant data | Planned; SQLite used locally |
| S3 | Original documents and generated artifacts | Planned for AWS |

## 3. Order processing sequence

```mermaid
sequenceDiagram
    autonumber
    actor User as Operations User
    participant UI as Slack or Web Portal
    participant API as Preflight API
    participant Store as Document Store
    participant Extract as Extraction Worker
    participant Rules as Rule Engine
    participant Data as Catalog and Inventory
    actor Manager as Authorized Reviewer

    User->>UI: Submit purchase order
    UI->>API: Create intake record
    API->>Store: Save original document
    API-->>UI: Return processing status
    API->>Extract: Queue extraction
    Extract->>Extract: Normalize header and line items
    Extract->>Rules: Validate normalized order
    Rules->>Data: Read SKUs, prices, status, and stock
    Data-->>Rules: Return current company data
    Rules-->>API: Findings and recommended status
    API-->>UI: Show review-ready order
    UI->>Manager: Notify when approval is required
    Manager->>UI: Approve, reject, or request changes
    UI->>API: Record decision with note
    API-->>UI: Update status and audit timeline
```

## 4. Workflow state model

```mermaid
stateDiagram-v2
    [*] --> RECEIVED
    RECEIVED --> PROCESSING
    PROCESSING --> EXTRACTION_REVIEW: Extraction needs confirmation
    EXTRACTION_REVIEW --> PROCESSING: User corrects fields
    PROCESSING --> READY_FOR_APPROVAL: No blocking findings
    PROCESSING --> REVIEW_REQUIRED: Commercial exception
    PROCESSING --> BLOCKED: Invalid or unsafe order
    REVIEW_REQUIRED --> APPROVED: Authorized approval
    REVIEW_REQUIRED --> CHANGES_REQUESTED
    READY_FOR_APPROVAL --> APPROVED: Authorized approval
    READY_FOR_APPROVAL --> REJECTED
    CHANGES_REQUESTED --> PROCESSING: Corrected order submitted
    BLOCKED --> PROCESSING: Blocking issue resolved
    APPROVED --> EXPORT_READY
    REJECTED --> [*]
    EXPORT_READY --> [*]
```

Only explicit actions by authorized users can move an order into `APPROVED`. AI output never bypasses workflow policy.

## 5. AWS deployment topology

```mermaid
flowchart TB
    Users["Company Users"] --> CloudFront["CloudFront"]
    CloudFront --> Web["Web Application"]
    Slack["Slack Platform"] --> ALB["Application Load Balancer"]
    Web --> ALB

    subgraph VPC["Private AWS VPC"]
        ALB --> API["Preflight API Service"]
        API --> Worker["Processing Worker"]
        API --> RDS[("Encrypted PostgreSQL")]
        Worker --> RDS
        Worker --> S3[("Encrypted S3 Documents")]
        API --> Secrets["Secrets Manager"]
        Worker --> Secrets
    end

    CI["GitHub Actions with OIDC"] -->|Deploy reviewed main branch| Web
    CI -->|Deploy containers and migrations| API
```

The first internal deployment may use one private EC2 instance for cost and speed. The target topology separates the web application, API, worker, database, and document storage so the system can scale and meet customer security requirements.

## 6. Trust boundaries and controls

- Original purchase orders are untrusted input and must be scanned, size-limited, and parsed in an isolated worker.
- AI extraction produces a proposal, not an authoritative transaction.
- Deterministic rules own SKU, pricing, inventory, duplicate, and policy outcomes.
- All decisions require an authenticated actor and append-only audit event.
- Customer data is isolated by tenant in every business record and storage path.
- Secrets are injected at runtime and never stored in Git or browser code.
- ERP writes remain disabled until an adapter has idempotency, authorization, reconciliation, and rollback controls.

## 7. Monorepo target

```text
po-preflight/
├── apps/
│   ├── api/                 # FastAPI product API
│   └── web/                 # Next.js customer portal and prototype
├── packages/
│   ├── preflight-core/      # Parsing and deterministic validation
│   └── contracts/           # Shared API and event schemas
├── integrations/
│   ├── openclaw/
│   ├── slack/
│   └── erp/
├── infra/terraform/
├── docs/
└── tests/
```

The repository can migrate toward this layout incrementally. The current Python core remains the working validation engine while the web portal and API boundaries are added.
