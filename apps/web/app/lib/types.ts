/**
 * PO Preflight — Core domain types.
 *
 * Source of truth: docs/FE_DATA_CONTRACT.md
 * Mirrors the backend rules engine in src/preflight/rules.py and src/preflight/models.py.
 * Changing anything here without updating the contract doc will drift the UI from the engine.
 */

// ---------------------------------------------------------------- status

export type OrderStatus =
  | "Ready"
  | "Review required"
  | "Blocked"
  | "Approved"
  | "Changes requested"
  | "Rejected";

/** Tone tokens per status. Colour never carries meaning alone — always pair with the label. */
export const STATUS_TONE: Record<OrderStatus, string> = {
  Ready: "#19704c",
  "Review required": "#a76418",
  Blocked: "#a5453c",
  Approved: "#386b8e",
  "Changes requested": "#b45309",
  Rejected: "#57534e",
};

// --------------------------------------------------------------- findings

export type FindingCode =
  | "PRICE_MISMATCH"
  | "INSUFFICIENT_STOCK"
  | "UNKNOWN_SKU"
  | "INACTIVE_SKU"
  | "DUPLICATE_PO"
  | "UOM_CONVERSION_MISSING";

export type FindingSeverity = "Warning" | "Error";

/** Severity is fixed by code, not a free field. Seed data violating this is a bug. */
export const SEVERITY_BY_CODE: Record<FindingCode, FindingSeverity> = {
  PRICE_MISMATCH: "Warning",
  INSUFFICIENT_STOCK: "Warning",
  UNKNOWN_SKU: "Error",
  INACTIVE_SKU: "Error",
  DUPLICATE_PO: "Error",
  UOM_CONVERSION_MISSING: "Warning",
};

export const FINDING_TITLE: Record<FindingCode, string> = {
  PRICE_MISMATCH: "Chênh lệch giá so với Catalog",
  INSUFFICIENT_STOCK: "Không đủ tồn kho đáp ứng",
  UNKNOWN_SKU: "Mã SKU không tồn tại",
  INACTIVE_SKU: "Sản phẩm đã ngừng kinh doanh",
  DUPLICATE_PO: "Trùng lặp mã đơn hàng",
  UOM_CONVERSION_MISSING: "Thiếu cấu hình quy đổi đơn vị (UOM)",
};

export interface Finding {
  code: FindingCode;
  severity: FindingSeverity;
  title: string;
  detail: string;
  /** Comparison line. Format is fixed per code — see contract §2.2. */
  evidence: string;
  /** null for DUPLICATE_PO, which belongs to the order rather than a line. */
  sku: string | null;
}

// -------------------------------------------------------------- line items

export interface LineItem {
  sku: string;
  product: string;
  quantity: number;
  available: number;
  /** Price as stated on the customer's PO, in the parent order's currency. */
  unitPrice: number;
  /** Company catalog price. 0 when the SKU is unknown. */
  catalogPrice: number;
}
// Note: LineItem has no `currency` of its own — it inherits the parent order's.
// A single PO cannot mix currencies. Always format with money(value, order.currency).

// --------------------------------------------------------------- decisions

export type DecisionType = "APPROVE" | "REQUEST_CHANGES" | "REJECT";

export interface Decision {
  type: DecisionType;
  actor: string;
  note: string;
  /** ISO 8601 UTC. */
  createdAt: string;
}

// ------------------------------------------------------------------ order

export interface PurchaseOrder {
  id: string;
  customer: string;
  /** ISO 8601 UTC — never a display string, or sorting breaks. */
  submittedAt: string;
  sourceFile: string;
  /** Derived: must equal orderValue(order). */
  value: number;
  /** ISO 4217. Multi-currency: always format via money(value, currency). Contract §7.1. */
  currency: string;
  status: OrderStatus;
  findings: Finding[];
  lines: LineItem[];
  owner: string;
  /** Newest first. Empty until someone decides. */
  decisions: Decision[];
}

// ---------------------------------------------------------------- catalog

export interface Product {
  sku: string;
  name: string;
  /** Number, not a formatted string — it has to be comparable. */
  unitPrice: number;
  stock: number;
  active: boolean;
  baseUom?: string;
  moq?: number;
  packSize?: number;
  category?: string | null;
  barcode?: string | null;
}

// ------------------------------------------------------------- prototype UI

/* UI-only types used by the prototype. Not part of the backend data contract —
   they describe navigation and display-only surfaces. */

/** A validation-rule control shown on the Rules screen. */
export interface ValidationRule {
  name: string;
  description: string;
  severity: "Block" | "Review";
  owner: string;
}

export type ActivityEventType = "system" | "human";

/** A single timeline entry on the Order Detail "Activity" panel. */
export interface ActivityEvent {
  title: string;
  detail: string;
  time: string;
  type: ActivityEventType;
}

/** A single row on the Audit log screen. */
export interface AuditEntry {
  id: string;
  time: string;
  event: string;
  actor: string;
  order: string;
  detail: string;
  type: ActivityEventType;
}

