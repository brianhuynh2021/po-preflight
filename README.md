# PO Preflight

> 🇻🇳 **Tài liệu tiếng Việt đầy đủ:** Xem chi tiết kiến trúc Agentic AI, RAG và phê duyệt đa kênh tại [Mô tả dự án PO Preflight (Tiếng Việt)](docs/MO_TA_DU_AN.md).

PO Preflight ingests purchase orders from files, validates them with deterministic business rules and intelligent RAG-assisted reasoning, and delivers review-ready results for instant approval through **Telegram, Zalo, Slack, WeChat, or WebChat**.

## MVP capabilities

- Read JSON, CSV, text, and text-based PDF purchase orders.
- Validate SKUs, catalog prices, product status, and inventory.
- Detect duplicate PO numbers using SQLite.
- Generate concise approval reports.
- Store every analysis and human decision in an audit log.
- Never create an ERP order without explicit human approval.

## Quick demo

```bash
./scripts/demo.sh
```

Or run it directly:

```bash
PYTHONPATH=src python3 -m preflight \
  --catalog examples/catalog.csv \
  --db runtime/preflight.db \
  analyze examples/orders/po-review.json
```

## PDF

Text-based PDFs require `pypdf`:

```bash
python3 -m pip install '.[pdf]'
```

Scanned PDFs require an OCR stage (Gemini Flash / Vision) handled by the ingestion agent.

## Architecture

```text
Telegram / Zalo / Slack / Web -> FastAPI & LangGraph -> Preflight Engine
                                                        |-- parser & vision OCR
                                                        |-- hybrid SKU RAG
                                                        |-- rule engine
                                                        `-- SQLite / Postgres audit log
```

See the [Vietnamese Specification (Mô tả chi tiết)](docs/MO_TA_DU_AN.md), [Frontend Backlog Tickets](docs/FE_BUSINESS_REQUIREMENTS_AND_TICKETS.md), [Agentic Roadmap](docs/ROADMAP.md), [Product Requirements Document](docs/PRD.md), and [architecture diagrams](docs/architecture.md).

## Web Dashboard

The customer-facing web dashboard lives in `apps/web`.

```bash
npm run dev
```

The terminal prints the local URL (e.g. `http://localhost:5173/`). Open it in a browser to run the interactive dashboard.

## CI/CD and Cloud

- Pull requests and pushes to `dev` run the test and policy suite.
- Terraform provisions an encrypted deployment topology on AWS.

See [AWS deployment](docs/aws-deployment.md).
