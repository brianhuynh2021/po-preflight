# OrderFlow AI

OrderFlow AI ingests purchase orders from files, validates them with deterministic business rules, and delivers review-ready results through OpenClaw, WebChat, or Slack.

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
PYTHONPATH=src python3 -m orderflow \
  --catalog examples/catalog.csv \
  --db runtime/orderflow.db \
  analyze examples/orders/po-price-and-stock.json
```

## Install into local OpenClaw

```bash
./scripts/install-openclaw.sh
openclaw gateway restart
```

Then open WebChat and send:

```text
/orderflow analyze this purchase order
```

## PDF

Text-based PDFs require `pypdf`:

```bash
python3 -m pip install '.[pdf]'
```

Scanned PDFs require an OCR stage that is outside the current MVP. The MVP does not claim reliable extraction from scanned images.

## Architecture

```text
Slack/WebChat -> OpenClaw skill -> OrderFlow CLI
                                    |-- parser
                                    |-- catalog
                                    |-- rule engine
                                    `-- SQLite audit log
```

See [product scope](docs/product-scope.md) and [security](docs/security.md).

## CI/CD and AWS

- Pull requests and pushes to `main` run the test and policy suite.
- Pushes to `main` can deploy the OpenClaw skill to a bootstrapped EC2 instance.
- Terraform provisions an encrypted Ubuntu EC2 host without exposing the Gateway port.

See [AWS deployment](docs/aws-deployment.md).
