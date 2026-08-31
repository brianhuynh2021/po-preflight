# PO Preflight UI Specification

This specification defines the initial customer-facing experience and can be used as the source for a future Figma design file.

## Product experience

Preflight should feel like an operations workspace: calm, precise, trustworthy, and fast. It should not look like a generic AI chat application. Users work with orders, findings, decisions, and evidence; AI remains a supporting capability.

## Information architecture

| Area | Purpose |
|---|---|
| Overview | Operational metrics, attention queue, recent activity, and processing health |
| Orders | Searchable order queue with status, customer, value, findings, and owner |
| Order detail | Header, line items, findings, source evidence, decisions, and audit timeline |
| Catalog | Product status, catalog price, currency, and available inventory |
| Rules | Validation policies, thresholds, severity, and ownership |
| Audit log | Searchable record of system and human events |
| Settings | Company profile, roles, channels, integrations, and retention |

## Primary prototype screens

### Operations overview

- Page title and concise operating context
- “Upload purchase order” primary action
- Ready, review-required, and blocked counts
- Order queue prioritized by required attention
- Processing activity summary

### Order review

- Order identity, customer, value, source, status, and submission metadata
- Normalized line-item table
- Findings grouped by severity
- Evidence and expected-versus-received values
- Approve, request changes, and reject actions
- Required decision note for exceptional approvals
- Chronological audit timeline

### Upload flow

- Drag-and-drop area and file picker
- Supported format guidance
- Processing and extraction states
- Clear explanation that the user reviews extracted data before approval

## Reusable components

- Application shell and workspace navigation
- Status badge
- Metric card
- Order queue row
- Finding card
- Evidence comparison
- Decision composer
- Audit event
- Empty, loading, error, and permission states
- Confirmation dialog
- Toast notification

## Status language

> **Source of truth: [`FE_DATA_CONTRACT.md`](./FE_DATA_CONTRACT.md) §1.** The frontend uses
> the display labels below as the literal `OrderStatus` values. Where this file and the
> contract disagree, the contract wins.

| `OrderStatus` (frontend) | Backend `rules.py` | Meaning |
|---|---|---|
| `Ready` | `ready_for_approval` | No validation findings |
| `Review required` | `review_required` | Warning-level findings only |
| `Blocked` | `blocked` | At least one error-level finding |
| `Approved` | *(human decision)* | An authorized reviewer approved the order |
| `Changes requested` | *(human decision)* | The submitter must provide or correct information |
| `Rejected` | *(human decision)* | The order will not continue |

The first three are **derived from findings** — never assigned by hand. See
`deriveStatus()` in `apps/web/app/lib/derive.ts`.

### Removed from scope

`PROCESSING` and `EXTRACTION_REVIEW` previously appeared here. Both were **removed** from the
demo scope — see contract §7.2 and §7.3.

- `EXTRACTION_REVIEW` is deliberate technical debt: the demo runs on static seed data, not
  real OCR. It must be restored before real extraction is wired in.
- `PROCESSING` lives in `UploadModal` component state. It is not an order status — nobody
  filters a queue by it or makes a decision on it.

The target-state machine in [`architecture.md`](./architecture.md) still models both; that
file describes the complete system rather than the demo scope.

## Visual direction

- Dense enough for operations work, with generous spacing around decision areas.
- Neutral warm background and dark navy navigation create a dependable business tone.
- Amber identifies review work; red identifies blocked actions; green identifies completed or ready work.
- Color always appears with text or an icon so status is never color-only.
- Use tabular numerals for order values and quantities.
- Use short labels and direct action copy; avoid AI marketing language inside the workflow.

## Responsive behavior

- Desktop: persistent navigation, two-column order detail, and full line-item table.
- Tablet: compact navigation and stacked review panels.
- Mobile: single-column queue and detail; secondary metadata collapses; decision actions remain visible in document flow.

## Accessibility requirements

- All actions must be keyboard accessible.
- Focus indicators must remain visible.
- Text and interactive controls must meet WCAG AA contrast.
- Status and validation severity must not rely on color alone.
- Dialogs must provide clear titles, labels, and close actions.
- Tables must preserve meaningful headers at every supported width.

## Figma handoff plan

When Figma work begins, create the following pages:

1. `00 Cover and Product Story`
2. `01 Foundations`
3. `02 Components`
4. `03 Desktop Screens`
5. `04 Responsive Screens`
6. `05 Prototype Flow`
7. `06 Handoff Notes`

The first clickable flow should cover: overview → open exception order → inspect evidence → add approval note → approve → confirm audit entry.
