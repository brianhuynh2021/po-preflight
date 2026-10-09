# PO Preflight Architecture

This document describes the concrete system architecture for PO Preflight and the path from single-tenant pilot to enterprise multi-tenant deployment.

## 1. System context

```mermaid
flowchart LR
    Customer["Customer or Operations User"]
    Reviewer["Sales or Operations Manager"]
    Admin["System Administrator"]
    MultiChannels["Channels: Telegram / Zalo OA / Mobile Web"]
    Web["Preflight Web Portal"]
    Preflight["PO Preflight Core (LangGraph + 4-Tier RAG)"]
    Catalog["Product Catalog & Vector Embeddings"]
    ERP["ERP Adapter (MISA AMIS / Odoo / SAP)"]

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

Preflight is the controlled intake layer between incoming purchase-order documents and downstream business systems. Multi-channel bots (Telegram, Zalo Official Account) and the web portal are unified interfaces to the same workflow and cryptographic audit trail.

### 1.1 AI-Native Design Philosophy

PO Preflight applies 5 core principles of modern AI-assisted systems to B2B order operations:

1. **High-Trust Grounding Evidence:** AI is never an opaque black box. Every validation finding provides explicit lineage and evidence (e.g., matching line 3 of the PO against Clause 2 of Customer Contract #2026-04).
2. **Proactive Background Processing (Zero-Wait):** Documents sent via email or portal are ingested and analyzed asynchronously in the background. Reviewers see instant results.
3. **Frictionless 1-Click Correction:** 98% of clean data is prepared automatically. For ambiguous lines, AI provides 1-click suggested corrections instead of forcing manual data re-entry.
4. **Context-Centric Reasoning:** Orders are evaluated in the holistic context of customer historical orders, custom pricing agreements, and past nickname resolutions.
5. **Human in Full Control:** AI acts as a tireless pre-flight co-pilot. Only an authenticated human decision triggers ERP synchronization.

## 2. Application containers

```mermaid
flowchart TB
    subgraph Channels["User Channels & Messaging"]
        TelegramBot["Telegram Bot (Inline Keyboards)"]
        ZaloOA["Zalo OA (Interactive Cards)"]
        MobileWeb["Minimal Mobile View (/m/orders/:id)"]
        WebApp["Next.js Web Portal"]
    end

    subgraph Platform["Preflight Platform Core Engine"]
        API["FastAPI Gateway & Webhook Router"]
        Worker["Document Processing Worker & Queue"]
        AgentEngine["LangGraph Stateful Workflow (Checkpointed)"]
        RAGService["4-Tier Hybrid SKU RAG (Exact/Fuzzy/Vector/LLM)"]
        Rules["Deterministic Zero-Token Rule Engine"]
        Audit["Cryptographic SHA-256 Audit Chain"]
    end

    subgraph Data["Data services"]
        DB[("PostgreSQL (Cloud) / SQLite WAL (Edge)")]
        VectorStore[("FastEmbed Multilingual Embeddings")]
        Files[("S3 / Local Document Store")]
        Secrets["Environment & Secret Management"]
    end

    subgraph External["Company systems"]
        CatalogAPI["Master Catalog and ATP Stock"]
        ERPAPI["ERP Transactional Outbox (MISA / Odoo / SAP)"]
    end

    TelegramBot --> API
    ZaloOA --> API
    MobileWeb --> API
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

### Component status & implementation reality

| Component | Responsibility | Current status |
|---|---|---|
| **FastAPI Gateway** | Session/API-Key authentication, RBAC, B2B rule analysis, order management | **Live (Production Ready)** |
| **Next.js Web Portal** | React 19 / Next 16 interface on Vite: extraction, inline edit, audit log | **Live (Production Ready)** |
| **Telegram & Zalo OA Bots** | Push rich-card alert messages, webhook callbacks for 1-tap approval from mobile | **Live (Production Ready)** |
| **LangGraph Stateful Graph** | Workflow graph that interrupts to wait for Human-In-The-Loop approval, with SQLite/Postgres checkpointing | **Live (Production Ready)** |
| **4-Tier SKU Matcher** | Tier 1 Exact → Tier 2 Fuzzy → Tier 3 Vector (FastEmbed) → Tier 4 LLM fallback | **Live (Production Ready)** |
| **B2B Rule Engine** | Reconciliation of list price, contract, ATP stock, overdue receivables, and UOM specifications | **Live (Production Ready)** |
| **ERP Transactional Outbox** | Idempotent ERP export queue supporting MISA AMIS, Odoo, SAP S/4HANA | **Live (Production Ready)** |
| **SHA-256 Hash Chain** | Tamper-evident cryptographic log attesting to the immutability of decisions | **Live (Production Ready)** |
| **Email Intake Worker** | Periodic IMAP worker that ingests PO attachments, with a lock to prevent duplicate processing | **Live (Production Ready)** |
| **Slack & WeChat Auxiliary Channels** | Extended integrations for Slack Block Kit and WeChat Work | **Planned expansion (Roadmap)** |

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
│   ├── telegram/
│   ├── zalo/
│   ├── slack/
│   └── erp/
├── infra/terraform/
├── docs/
└── tests/
```

The repository can migrate toward this layout incrementally. The current Python core remains the working validation engine while the web portal and API boundaries are added.
