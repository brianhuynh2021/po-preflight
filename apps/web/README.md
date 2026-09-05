# PO Preflight Enterprise Web Application

This enterprise application provides the mission-critical operations portal for PO Preflight. It is backed by authenticated RESTful APIs, SQLite/PostgreSQL dynamic rule engines, cryptographic audit blocks, 4-tier RAG SKU waterfall matcher, and bidirectional ERP sync outbox.

## Features & Workflows

- Operations overview and real-time attention queue
- Searchable purchase-order management & multi-channel ingestion
- Staging studio with OCR extraction review & line-item correction
- Catalog, price, inventory (ATP), and unknown-SKU findings
- Controlled human-in-the-loop approval with required exception audit trails
- Dynamic hierarchical policy matrix with SQLite/Postgres persistence by scope (Branch/Region/Channel)
- 4-Tier SKU Waterfall Matcher & interactive RAG Playground
- Stateful LangGraph workflow visualizer
- ERP Outbox synchronization center with auto-retry and idempotency
- Cryptographic Merkle tree audit certificates with SHA-256 tamper-evident verification
- Multi-channel notification center (Telegram, Zalo OA, Webhooks)

## Run locally

```bash
npm install
npm run dev
```

Open the local URL printed by the development server (`http://localhost:3000`).

## Validate

```bash
npm test
```

All browser actions and policy updates communicate with the backend FastAPI services (`http://localhost:8001`) with live database persistence.
