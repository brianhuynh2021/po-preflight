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

export const STATUS_LABEL_VI: Record<OrderStatus, string> = {
  Ready: "Sẵn sàng duyệt",
  "Review required": "Cần xem xét",
  Blocked: "Bị chặn",
  Approved: "Đã duyệt",
  "Changes requested": "Yêu cầu sửa",
  Rejected: "Đã từ chối",
};

// --------------------------------------------------------------- findings

import type {
  FindingCode,
  FindingSeverity,
  FindingCategory,
  FindingMetadata,
} from "./findings.generated";

export type {
  FindingCode,
  FindingSeverity,
  FindingCategory,
  FindingMetadata,
};
export {
  FINDINGS_REGISTRY,
  FINDING_TITLE,
  SEVERITY_BY_CODE,
} from "./findings.generated";

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
  discountPercent?: number;
  discountAmount?: number;
  taxRate?: number;
  isPromo?: boolean;
  description?: string | null;
  uom?: string;
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
  revision?: number;
  supersedesOrderId?: string | number | null;
  requestedChanges?: string | null;
  revisions?: { id: string | number; revision: number; status: string; createdAt: string }[];
  subtotal?: number;
  taxAmount?: number;
  grandTotal?: number;
  shippingFee?: number;
  headerDiscountAmount?: number;
  declaredTotal?: number | null;
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

// ------------------------------------------------------------- customer master

export interface CustomerMaster {
  id?: number | null;
  code: string;
  name: string;
  normalized_name?: string;
  normalizedName?: string;
  tax_code?: string | null;
  taxCode?: string | null;
  tier?: "VIP" | "PLATINUM" | "GOLD" | "STANDARD" | string;
  aliases?: string[];
  created_at?: string | null;
  createdAt?: string | null;
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

// ------------------------------------------------------------- users & auth

export type UserRole = "viewer" | "auditor" | "sales_admin" | "manager" | "director" | "admin";

export interface UserAccount {
  id?: number | null;
  org_id?: string;
  username: string;
  display_name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  failed_attempts?: number;
  locked_until?: string | null;
  created_at?: string;
}

export const ROLE_LABEL_VI: Record<UserRole, string> = {
  viewer: "Người xem",
  auditor: "Kiểm toán viên",
  sales_admin: "Sales Admin",
  manager: "Trưởng phòng (Quản lý)",
  director: "Giám đốc phê duyệt",
  admin: "Quản trị hệ thống",
};
