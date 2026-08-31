import type {
  FindingCode,
  PurchaseOrder,
} from "../app/lib/types";
import { FINDING_TITLE, SEVERITY_BY_CODE } from "../app/lib/types";

function finding(
  code: FindingCode,
  detail: string,
  evidence: string,
  sku: string | null,
) {
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
        "LMP-200 is priced 2.8% above the current catalog price.",
        "PO: $74.00  ·  Catalog: $72.00  ·  Lệch: +2.78% (+$120.00)",
        "LMP-200",
      ),
      finding(
        "INSUFFICIENT_STOCK",
        "The order requests 60 units of LMP-200, but only 38 are available.",
        "Đặt: 60  ·  Tồn kho: 38  ·  Thiếu: 22",
        "LMP-200",
      ),
    ],
    decisions: [],
  },
  {
    id: "PO-10431",
    customer: "Bluebird Supply",
    submittedAt: "2026-08-31T09:18:00Z",
    sourceFile: "bluebird-order.txt",
    value: 6980,
    currency: "USD",
    status: "Blocked",
    owner: "Unassigned",
    lines: [
      {
        sku: "DSK-404",
        product: "Unknown product",
        quantity: 10,
        available: 0,
        unitPrice: 698,
        catalogPrice: 0,
      },
    ],
    findings: [
      finding(
        "UNKNOWN_SKU",
        "DSK-404 cannot be matched to an active product and must be corrected before approval.",
        "SKU nhận được: DSK-404  ·  Khớp catalog: 0",
        "DSK-404",
      ),
    ],
    decisions: [],
  },
  {
    id: "PO-10421",
    customer: "Acme Stores",
    submittedAt: "2026-08-30T16:36:00Z",
    sourceFile: "acme-po-10421.json",
    value: 12480,
    currency: "USD",
    status: "Ready",
    owner: "Daniel Ortiz",
    lines: [
      {
        sku: "TB-320",
        product: "Tanner meeting table",
        quantity: 8,
        available: 24,
        unitPrice: 960,
        catalogPrice: 960,
      },
      {
        sku: "CHR-110",
        product: "Morrow task chair",
        quantity: 10,
        available: 81,
        unitPrice: 480,
        catalogPrice: 480,
      },
    ],
    findings: [],
    decisions: [],
  },
  {
    id: "PO-10417",
    customer: "Atlas Hospitality",
    submittedAt: "2026-08-30T13:12:00Z",
    sourceFile: "atlas-10417.csv",
    value: 24860,
    currency: "USD",
    status: "Approved",
    owner: "Maya Chen",
    lines: [
      {
        sku: "CHR-110",
        product: "Morrow task chair",
        quantity: 55,
        available: 81,
        unitPrice: 452,
        catalogPrice: 452,
      },
    ],
    findings: [],
    decisions: [
      {
        type: "APPROVE",
        actor: "Maya Chen",
        note: "Approved after reviewing validation evidence",
        createdAt: "2026-08-31T08:00:00Z",
      },
    ],
  },
];
