# PO Preflight — Automated B2B Order Preflight System

> 🇻🇳 **Full documentation:** See the detailed architecture and business analysis in the [PO Preflight Project Description](docs/MO_TA_DU_AN.md) and the [Pilot Playbook](docs/PILOT_PLAYBOOK.md).

**PO Preflight** is a pre-control and standardization gateway for Purchase Orders, built for B2B businesses and distributors in Vietnam. The system automatically extracts orders from multiple formats, checks business rules in real time (contract price, credit limit, ATP available stock, packaging specifications), and triggers instant one-tap approval via **Telegram, Zalo Official Account, or the Web Portal** before safely syncing to the ERP system (MISA AMIS, Bravo, Fast, Odoo, SAP B1).

---

## 📊 System Capability Status

**Banking extension (pilot):** the `/banking` screen and the API for preflight checks on corporate
disbursement dossiers already support manual entry, checklists, limit/invoice reconciliation, and result export.
Scope, limitations, and usage: [Banking Pilot](docs/BANKING_PILOT.md).
This is an illustrative rule set; it does not yet include dossier storage, disbursement approval, or core banking connectivity.

| Technical Component | Technology & Mechanism | Current Status |
|---|---|---|
| **Multi-format Intake** | JSON, CSV, and text-table parsers + Gemini Flash Vision OCR for scanned images/PDFs | **Live (Production Ready)** |
| **Math Grounding** | Self-Reflection Math Verifier (reconciles totals, VAT, and line discounts) | **Live (Production Ready)** |
| **4-Tier Hybrid SKU Matcher** | Tier 1 Exact Hash → Tier 2 Fuzzy → Tier 3 FastEmbed Vector → Tier 4 LLM | **Live (Production Ready)** |
| **Stateful Workflow Orchestration Graph** | LangGraph StateGraph with SQLite/Postgres Checkpointer & HITL approval-wait interrupt | **Live (Production Ready)** |
| **B2B Rules Engine** | Checks contract price, credit limit, ATP stock, MOQ, and UOM packaging specifications | **Live (Production Ready)** |
| **Multi-channel Mobile Approval** | Telegram Bot Webhook + Zalo OA Rich Interactive Cards + Web `/m/orders/:id` | **Live (Production Ready)** |
| **ERP Connectivity Gateway (ERP Outbox)** | Transactional Outbox Pattern with MISA AMIS Live, Odoo, SAP S/4HANA (Dry-run supported) | **Live (Production Ready)** |
| **Dual-backend Storage** | SQLite (WAL mode) for Edge/On-premise and PostgreSQL for Cloud with Alembic | **Live (Production Ready)** |
| **Cryptographic Audit Log (Audit Hash Chain)** | Sequential SHA-256 hash chain against tampering (Tamper-evident Cryptographic Hash Chain) | **Live (Production Ready)** |
| **Email Intake Worker** | IMAP Poller with a distributed lock preventing duplicate processing, plus idempotency | **Live (Production Ready)** |
| **Auxiliary Slack & WeChat Channels** | Slack App Block Kit & WeChat Work Webhook | **Planned expansion (Roadmap)** |

---

## 🚀 Quick Start Guide

### 1. Start the Backend API & Run the Full Test Suite
```bash
# Activate the Python environment (>= 3.12)
source .venv/bin/activate

# Run the full automated test suite (270+ tests)
./scripts/test.sh

# Run the 6-stage E2E Demo scenario
PYTHONPATH=src python3 -m preflight.cli demo
```

### 2. Start the Customer Web Dashboard (Next.js 16 + React 19 on Vite)
```bash
cd apps/web
npm install
npm run dev
```
Visit `http://localhost:5173/` to view the operations Portal interface.

---

## 🏗 Technical Architecture

```text
[ Email (IMAP) / Excel / PDF / JSON ]
                  │
                  ▼
   ┌──────────────────────────────┐
   │ Cascading Ingestion Pipeline │ ── (Gemini Vision OCR fallback)
   └──────────────┬───────────────┘
                  │
                  ▼
   ┌──────────────────────────────┐
   │ 4-Tier Hybrid SKU Matcher    │ ── (Exact -> Fuzzy -> FastEmbed Vector -> LLM)
   └──────────────┬───────────────┘
                  │
                  ▼
   ┌──────────────────────────────┐
   │ LangGraph Stateful Graph     │ ── [Human Approval Checkpoint]
   │ Deterministic Rules Engine   │        │
   └──────────────┬───────────────┘        ├─► Telegram Bot (Inline Buttons)
                  │                        ├─► Zalo Official Account Card
                  │                        └─► Minimal Mobile Screen (/m/orders/:id)
                  ▼
   ┌──────────────────────────────┐
   │ Transactional ERP Outbox     │ ──► [ MISA AMIS / Odoo / SAP S/4HANA ]
   └──────────────┬───────────────┘
                  │
                  ▼
   ┌──────────────────────────────┐
   │ SHA-256 Audit Hash Chain     │ ──► [ Tamper-evident Audit Certificate ]
   └──────────────────────────────┘
```

---

## 🔒 Security & Compliance

- **Decree 13/2023/ND-CP**: All customer data is anonymized, stored encrypted, and supports fully On-Premise or Private Cloud installation in Vietnam.
- **Segregation of Duties (SoD)**: Thoroughly prevents conflicts of interest — Sales Admin staff cannot approve orders they submitted themselves; orders exceeding the limit require confirmation from a Director.
- **Data integrity**: The SHA-256 hash chain is tightly bound to every action and automatically detects if data in the database has been modified directly.

---

## 📚 Technical & Business Documentation
- [30-Day Pilot Deployment Handbook (Pilot Playbook)](docs/PILOT_PLAYBOOK.md)
- [Detailed System Architecture Description](docs/MO_TA_DU_AN.md)
- [Security Q&A Handbook for Accounting & IT](docs/SECURITY_QA.md)
- [Customer Deployment Case Study Template](docs/marketing/CASE_STUDY_TEMPLATE.md)
- [Frontend Data Contract (FE Data Contract)](docs/FE_DATA_CONTRACT.md)
- [Operations & Incident Recovery Guide (Runbook)](docs/RUNBOOK.md)
