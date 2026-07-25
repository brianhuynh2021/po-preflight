# PO Preflight

PO Preflight ingests purchase orders from files, validates them with deterministic business rules, and delivers review-ready results through OpenClaw, WebChat, or Slack.

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

## Install into local OpenClaw

```bash
./scripts/install-openclaw.sh
openclaw gateway restart
```

Then open WebChat and send:

```text
/preflight analyze this purchase order
```

## PDF

Text-based PDFs require `pypdf`:

```bash
python3 -m pip install '.[pdf]'
```

Scanned PDFs require an OCR stage that is outside the current MVP. The MVP does not claim reliable extraction from scanned images.

## Architecture

```text
Slack/WebChat -> OpenClaw skill -> Preflight CLI
                                    |-- parser
                                    |-- catalog
                                    |-- rule engine
                                    `-- SQLite audit log
```

See the [Product Requirements Document](docs/PRD.md), [architecture diagrams](docs/architecture.md), [UI specification](docs/ui-specification.md), [demo guide](docs/demo-guide.md), [product scope](docs/product-scope.md), and [security model](docs/security.md).

## Local web prototype

The customer-facing prototype lives in `apps/web` and uses realistic synthetic order data. It demonstrates the order queue, validation findings, approval actions, upload flow, and audit timeline without requiring access to the raw OpenClaw dashboard.

```bash
cd apps/web
npm install
npm run dev
```

The terminal prints the local URL. Open it in a browser to run the interactive demo.

## CI/CD and AWS

- Pull requests and pushes to `main` run the test and policy suite.
- Pushes to `main` can deploy the OpenClaw skill to a bootstrapped EC2 instance.
- Terraform provisions an encrypted Ubuntu EC2 host without exposing the Gateway port.

See [AWS deployment](docs/aws-deployment.md).
