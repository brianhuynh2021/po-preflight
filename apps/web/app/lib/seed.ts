import type {
  AuditEntry,
  Finding,
  FindingCode,
  Product,
  PurchaseOrder,
  ValidationRule,
} from "./types";
import { FINDING_TITLE, SEVERITY_BY_CODE } from "./types";

function finding(
  code: FindingCode,
  detail: string,
  evidence: string,
  sku: string | null,
): Finding {
  return {
    code,
    severity: SEVERITY_BY_CODE[code],
    title: FINDING_TITLE[code],
    detail,
    evidence,
    sku,
  };
}

/**
 * Synthetic purchase orders used to demo the frontend workflow.
 * Shapes conform to the FE data contract (PurchaseOrder): ISO submittedAt,
 * a single findings array with Warning/Error severity, and a decisions log.
 */
export const seedOrders: PurchaseOrder[] = [
  {
    id: "PO-10428",
    customer: "Northstar Retail",
    submittedAt: "2026-08-31T10:42:00Z",
    sourceFile: "northstar-po-10428.pdf",
    value: 18420,
    currency: "USD",
    status: "Review required",
    owner: "Maya Chen",
    lines: [
      {
        sku: "LMP-200",
        product: "Arc desk lamp",
        quantity: 60,
        available: 38,
        unitPrice: 74,
        catalogPrice: 72,
      },
      {
        sku: "CHR-110",
        product: "Morrow task chair",
        quantity: 30,
        available: 81,
        unitPrice: 466,
        catalogPrice: 466,
      },
    ],
    findings: [
      finding(
        "PRICE_MISMATCH",
        "PO lists $74.00, catalog is $72.00 (+2.8% difference)",
        "Line 1 (LMP-200): PO $74.00 vs Catalog $72.00 (+2.8%)",
        "LMP-200",
      ),
      finding(
        "INSUFFICIENT_STOCK",
        "Ordered 60 units, available stock is 38 (short 22)",
        "Line 1 (LMP-200): requested 60, available 38",
        "LMP-200",
      ),
    ],
    decisions: [],
  },
  {
    id: "PO-10431",
    customer: "Beacon Logistics",
    submittedAt: "2026-08-31T09:18:00Z",
    sourceFile: "beacon-august-batch.pdf",
    value: 9600,
    currency: "USD",
    status: "Blocked",
    owner: "Alex Rivera",
    lines: [
      {
        sku: "DSK-404",
        product: "Unknown item",
        quantity: 10,
        available: 0,
        unitPrice: 960,
        catalogPrice: 0,
      },
    ],
    findings: [
      finding(
        "UNKNOWN_SKU",
        "SKU DSK-404 was not found in the active catalog",
        "Line 1: SKU DSK-404 not in catalog",
        "DSK-404",
      ),
    ],
    decisions: [],
  },
  {
    id: "PO-10417",
    customer: "Cascade Health",
    submittedAt: "2026-08-30T16:05:00Z",
    sourceFile: "cascade-q3-po.pdf",
    value: 32620,
    currency: "USD",
    status: "Ready",
    owner: "Maya Chen",
    lines: [
      {
        sku: "CHR-110",
        product: "Morrow task chair",
        quantity: 70,
        available: 81,
        unitPrice: 466,
        catalogPrice: 466,
      },
    ],
    findings: [],
    decisions: [],
  },
  {
    id: "PO-10402",
    customer: "Vanguard Studio",
    submittedAt: "2026-08-29T14:22:00Z",
    sourceFile: "vanguard-expansion.pdf",
    value: 14880,
    currency: "USD",
    status: "Approved",
    owner: "Samira Patel",
    lines: [
      {
        sku: "TB-320",
        product: "Tanner meeting table",
        quantity: 12,
        available: 24,
        unitPrice: 960,
        catalogPrice: 960,
      },
      {
        sku: "CHR-110",
        product: "Morrow task chair",
        quantity: 8,
        available: 81,
        unitPrice: 466,
        catalogPrice: 466,
      },
    ],
    findings: [],
    decisions: [
      {
        type: "APPROVE",
        actor: "Samira Patel",
        note: "Approved without exception",
        createdAt: "2026-08-29T15:00:00Z",
      },
    ],
  },
  {
    id: "PO-10398",
    customer: "Harbor & Pine",
    submittedAt: "2026-08-29T11:04:00Z",
    sourceFile: "harbor-refit-0829.pdf",
    value: 24800,
    currency: "USD",
    status: "Changes requested",
    owner: "Alex Rivera",
    lines: [
      {
        sku: "STG-410",
        product: "Rowan storage unit",
        quantity: 20,
        available: 0,
        unitPrice: 1240,
        catalogPrice: 1240,
      },
    ],
    findings: [
      finding(
        "INACTIVE_SKU",
        "STG-410 is discontinued as of 2026-08-01",
        "Line 1 (STG-410): product is inactive in catalog",
        "STG-410",
      ),
    ],
    decisions: [
      {
        type: "REQUEST_CHANGES",
        actor: "Alex Rivera",
        note: "Customer notified of discontinued item; waiting on replacement SKU.",
        createdAt: "2026-08-29T11:40:00Z",
      },
    ],
  },
  {
    id: "PO-10385",
    customer: "Apex Design Co",
    submittedAt: "2026-08-28T08:50:00Z",
    sourceFile: "apex-po-8812.pdf",
    value: 8640,
    currency: "USD",
    status: "Rejected",
    owner: "Samira Patel",
    lines: [
      {
        sku: "LMP-200",
        product: "Arc desk lamp",
        quantity: 120,
        available: 38,
        unitPrice: 72,
        catalogPrice: 72,
      },
    ],
    findings: [
      finding(
        "INSUFFICIENT_STOCK",
        "Requested 120 units, warehouse holds 38",
        "Line 1 (LMP-200): requested 120, available 38",
        "LMP-200",
      ),
    ],
    decisions: [
      {
        type: "REJECT",
        actor: "Samira Patel",
        note: "Capacity cannot meet requested lead time. Customer will re-order in Q4.",
        createdAt: "2026-08-28T09:30:00Z",
      },
    ],
  },
];

/** Company product catalog — the reference used by order validation rules. */
export const catalog: Product[] = [
  { sku: "CHR-110", name: "Morrow task chair", unitPrice: 466, stock: 81, active: true },
  { sku: "LMP-200", name: "Arc desk lamp", unitPrice: 72, stock: 38, active: true },
  { sku: "TB-320", name: "Tanner meeting table", unitPrice: 960, stock: 24, active: true },
  { sku: "STG-410", name: "Rowan storage unit", unitPrice: 1240, stock: 0, active: false },
];

/** Deterministic controls applied to every normalized order. */
export const rules: ValidationRule[] = [
  { name: "Unknown SKU", description: "Block line items that do not match the company catalog.", severity: "Block", owner: "Operations" },
  { name: "Inactive product", description: "Block products that are not available for new orders.", severity: "Block", owner: "Operations" },
  { name: "Catalog price mismatch", description: "Require review when the received price differs from the active catalog.", severity: "Review", owner: "Sales" },
  { name: "Insufficient stock", description: "Require review when requested quantity exceeds available inventory.", severity: "Review", owner: "Operations" },
  { name: "Duplicate PO number", description: "Block a PO number already recorded for the same customer.", severity: "Block", owner: "Finance" },
];

/** Audit entries list for Audit log view. */
export const auditEntries: AuditEntry[] = [
  {
    id: "a1",
    time: "10:43 AM",
    event: "Validation completed",
    actor: "Preflight Rules",
    order: "PO-10428",
    detail: "2 findings generated",
    type: "system",
  },
  {
    id: "a2",
    time: "10:42 AM",
    event: "Order submitted",
    actor: "Olivia Park",
    order: "PO-10428",
    detail: "Web portal upload",
    type: "human",
  },
  {
    id: "a3",
    time: "9:19 AM",
    event: "Order blocked",
    actor: "Preflight Rules",
    order: "PO-10431",
    detail: "Unknown SKU DSK-404",
    type: "system",
  },
  {
    id: "a4",
    time: "Yesterday",
    event: "Order approved",
    actor: "Maya Chen",
    order: "PO-10417",
    detail: "No exceptions",
    type: "human",
  },
];
