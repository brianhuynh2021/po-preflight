# Product scope

## Target user

The MVP targets operations and sales-order teams at small and midsize distributors or manufacturers that receive purchase orders as files and manually retype them into internal systems.

## In scope

- File-based purchase-order intake.
- Deterministic SKU, price, inventory, active-product, and duplicate checks.
- Human-readable review output.
- Explicit human decisions.
- SQLite audit history.
- OpenClaw WebChat and Slack as interaction surfaces.

## Out of scope for the MVP

- Automatic ERP writes.
- Reliable OCR for scanned documents.
- Credit-limit decisions.
- Tax or legal compliance claims.
- Customer identity verification.
- Automatic price corrections.
- Autonomous approval.

## Success metrics

- Median order pre-check time.
- Percentage of orders requiring manual correction.
- Number of price, stock, and duplicate issues found before ERP entry.
- Human approval turnaround time.
- Cost per analyzed order.
