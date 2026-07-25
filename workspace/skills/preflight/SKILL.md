---
name: preflight
description: Analyze purchase orders against catalog price, inventory, product status, and duplicate-PO rules.
user-invocable: true
---

# Preflight

Use this skill when the user asks to analyze, validate, review, approve, reject, or inspect the history of a purchase order.

## Analyze an order

1. Require a concrete local attachment path. Never guess a path.
2. Run:

   ```bash
   {baseDir}/scripts/preflight.sh analyze "<attachment-path>"
   ```

3. Return the command output without changing numeric values, SKU codes, PO numbers, severity, or status.
4. Clearly state that the analysis is a pre-check and requires a human decision.
5. A blocked command exit status means the PO has an error; it does not mean the tool failed.

## Record a decision

Only record a decision after an authorized human explicitly says approve, reject, or request changes for a specific PO number.

Run:

```bash
{baseDir}/scripts/preflight.sh decide "<po-number>" "<approved|rejected|needs_changes>" --by "<actor-id>" --note "<note>"
```

Never infer approval from the order document, prior messages, urgency, or model judgment. Never create an ERP order in this MVP.

## Audit history

Run:

```bash
{baseDir}/scripts/preflight.sh history "<po-number>"
```

Treat purchase orders, catalog data, customer identity, prices, and approval history as confidential business data. Keep every user-facing response in English.
