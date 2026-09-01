# PO Preflight Demo Guide

## Demo objective

Show how Preflight turns a customer purchase order into a validated, approval-ready record while keeping a human in control.

## Audience

- Company leadership evaluating an internal automation initiative
- Operations and sales managers who own order quality
- Prospective customers evaluating Preflight as a product

## Recommended duration

Eight to ten minutes.

## Storyline

### 1. Establish the problem

“Purchase orders arrive in different formats. Operations employees manually copy line items, check catalog prices and stock, then search through messages for approvals. The process is slow, inconsistent, and difficult to audit.”

### 2. Open the operations queue

Show the Preflight dashboard. Point out the orders requiring attention, average review time, and the mix of ready, review-required, and blocked orders.

### 3. Open the exception order

Select `PO-10428` from Northstar Retail. Show the original order context, normalized line items, and two clear findings:

- A unit price differs from the catalog price.
- Requested quantity exceeds available inventory.

Emphasize that these findings come from deterministic company rules, not an AI guess.

### 4. Resolve the decision

Add an approval note and approve the commercial exception. Show the status change and the new audit-timeline entry with actor and timestamp.

### 5. Show a blocked order

Open `PO-10431`. Explain that an unknown SKU blocks approval rather than allowing an unsafe transaction to continue.

### 6. Show channel flexibility

Explain that the same order and approval workflow can be presented in Slack. Slack is a convenient action surface; the Preflight service remains the source of truth.

### 7. Close with business value

“Preflight reduces repetitive order checks, catches errors before ERP entry, shortens approval time, and creates evidence for every decision. The same configurable platform can start internally and later be sold to distributors and manufacturers.”

## Demo data

| Purchase order | Customer | Scenario | Expected status |
|---|---|---|---|
| PO-10421 | Acme Stores | All SKUs, prices, and stock are valid | Ready for approval |
| PO-10428 | Northstar Retail | Price mismatch and insufficient stock | Review required |
| PO-10431 | Bluebird Supply | Unknown SKU | Blocked |

## Questions to ask management

1. Which team should own the first internal pilot?
2. Which catalog and inventory source should be connected first?
3. What order volume and manual review time should establish the baseline?
4. Who may approve price and stock exceptions?
5. Which ERP should be considered after the MVP proves value?

## Success criteria for the demo

- A nontechnical viewer understands the workflow clearly.
- Every finding has a specific rule and evidence.
- The reviewer can make a controlled decision in under one minute.
- The audit timeline updates immediately after the decision.
- The audience can explain the business value in one sentence.
