/**
 * PO Preflight — derived values, formatting and business rules.
 *
 * Source of truth: docs/FE_DATA_CONTRACT.md
 * Every function here mirrors a rule in src/preflight/rules.py. Keep them in step.
 */

import {
  type Decision,
  type DecisionType,
  type FindingCode,
  type LineItem,
  type OrderStatus,
  type PurchaseOrder,
} from "./types";

// ------------------------------------------------------- derived status

/** Mirrors rules.py:74-79. Never assign these three statuses by hand. */
export function deriveStatus(findings: { severity: string }[]): OrderStatus {
  if (findings.some((f) => f.severity === "Error")) return "Blocked";
  if (findings.length > 0) return "Review required";
  return "Ready";
}

/** Statuses set by a human decision rather than by the rules engine. */
export const DECIDED_STATUSES: OrderStatus[] = [
  "Approved",
  "Changes requested",
  "Rejected",
];

export const isDecided = (s: OrderStatus) => DECIDED_STATUSES.includes(s);

// -------------------------------------------------------- derived money

export const lineTotal = (l: LineItem) => l.quantity * l.unitPrice;

export const orderValue = (o: Pick<PurchaseOrder, "lines">) =>
  o.lines.reduce((sum, l) => sum + lineTotal(l), 0);

/**
 * Signed price delta as a percentage of the catalog price.
 * rules.py uses abs(); we keep the sign so a reviewer can see over- vs under-charging.
 * Returns 0 when catalogPrice <= 0, matching rules.py's `if product.unit_price > 0` guard.
 */
export function priceDeltaPercent(poPrice: number, catalogPrice: number): number {
  if (catalogPrice <= 0) return 0;
  return ((poPrice - catalogPrice) / catalogPrice) * 100;
}

export const money = (value: number, currency: string) =>
  new Intl.NumberFormat(currency === "VND" ? "vi-VN" : "en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);

// ------------------------------------------------------------ line flags

export type CellFlag = "none" | "warn" | "error";

/** Which cells to highlight in the line-item table — contract §3.1. */
export function lineFlags(l: LineItem): {
  row: CellFlag;
  unitPrice: CellFlag;
  quantity: CellFlag;
} {
  if (l.catalogPrice === 0) {
    return { row: "error", unitPrice: "error", quantity: "error" };
  }
  return {
    row: "none",
    unitPrice: l.unitPrice !== l.catalogPrice ? "warn" : "none",
    quantity: l.quantity > l.available ? "warn" : "none",
  };
}

// --------------------------------------------------------------- dates

const startOfDay = (d: Date) =>
  new Date(d.getFullYear(), d.getMonth(), d.getDate());

export const isSameDay = (a: Date, b: Date) =>
  +startOfDay(a) === +startOfDay(b);

export function formatSubmitted(iso: string, now = new Date()): string {
  const d = new Date(iso);
  const time = d.toLocaleTimeString("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
  });
  const days = Math.round((+startOfDay(now) - +startOfDay(d)) / 86_400_000);
  if (days === 0) return `Hôm nay, ${time}`;
  if (days === 1) return `Hôm qua, ${time}`;
  return d.toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

// ------------------------------------------------------------ decisions

/** Contract §6.1. A Blocked order can never be approved. */
export function canDecide(status: OrderStatus, type: DecisionType): boolean {
  switch (type) {
    case "APPROVE":
      return status === "Ready" || status === "Review required";
    case "REQUEST_CHANGES":
      return (
        status === "Ready" ||
        status === "Review required" ||
        status === "Blocked"
      );
    case "REJECT":
      return status !== "Approved" && status !== "Rejected";
  }
}

/** Tooltip explaining why an action is unavailable. null when it is available. */
export function decisionBlockedReason(
  status: OrderStatus,
  type: DecisionType,
  errorCount: number,
): string | null {
  if (canDecide(status, type)) return null;
  if (type === "APPROVE" && status === "Blocked") {
    return `Không thể duyệt: đơn có ${errorCount} lỗi nghiêm trọng cần sửa trước.`;
  }
  if (isDecided(status)) {
    return `Đơn đã ở trạng thái "${status}", không thể thực hiện thao tác này.`;
  }
  return "Thao tác không khả dụng ở trạng thái hiện tại.";
}

/** Contract §6.2. Approving over warnings is an exceptional approval and needs a reason. */
export function isNoteRequired(status: OrderStatus, type: DecisionType): boolean {
  if (type === "REQUEST_CHANGES" || type === "REJECT") return true;
  return type === "APPROVE" && status === "Review required";
}

export const MIN_NOTE_LENGTH = 10;

export function validateNote(
  status: OrderStatus,
  type: DecisionType,
  note: string,
): string | null {
  if (!isNoteRequired(status, type)) return null;
  if (note.trim().length < MIN_NOTE_LENGTH) {
    return `Vui lòng nhập ghi chú tối thiểu ${MIN_NOTE_LENGTH} ký tự.`;
  }
  return null;
}

export const STATUS_AFTER_DECISION: Record<DecisionType, OrderStatus> = {
  APPROVE: "Approved",
  REQUEST_CHANGES: "Changes requested",
  REJECT: "Rejected",
};

/** Applies a decision immutably: new status, decision prepended to the log. */
export function applyDecision(
  order: PurchaseOrder,
  decision: Decision,
): PurchaseOrder {
  return {
    ...order,
    status: STATUS_AFTER_DECISION[decision.type],
    decisions: [decision, ...order.decisions],
  };
}

// ------------------------------------------------------------ dashboard

export const needsAttention = (orders: PurchaseOrder[]) =>
  orders.filter(
    (o) => o.status === "Review required" || o.status === "Blocked",
  ).length;

export const readyForApproval = (orders: PurchaseOrder[]) =>
  orders.filter((o) => o.status === "Ready").length;

export const approvedToday = (orders: PurchaseOrder[], now = new Date()) =>
  orders.filter((o) =>
    o.decisions.some(
      (d) => d.type === "APPROVE" && isSameDay(new Date(d.createdAt), now),
    ),
  ).length;

/** null when nothing has been decided yet — render "—", never "0m". */
export function avgDecisionTimeMinutes(orders: PurchaseOrder[]): number | null {
  const spans = orders.flatMap((o) => {
    const first = o.decisions.at(-1);
    if (!first) return [];
    return [(+new Date(first.createdAt) - +new Date(o.submittedAt)) / 60_000];
  });
  if (!spans.length) return null;
  return spans.reduce((a, b) => a + b, 0) / spans.length;
}

export function findingsByCode(
  orders: PurchaseOrder[],
): Record<FindingCode, number> {
  const acc: Record<FindingCode, number> = {
    PRICE_MISMATCH: 0,
    INSUFFICIENT_STOCK: 0,
    UNKNOWN_SKU: 0,
    INACTIVE_SKU: 0,
    DUPLICATE_PO: 0,
  };
  for (const o of orders) for (const f of o.findings) acc[f.code]++;
  return acc;
}

// --------------------------------------------------------------- queue

export type QueueTab =
  | "All"
  | "Needs Attention"
  | "Ready"
  | "Approved"
  | "Closed";

export function filterByTab(
  orders: PurchaseOrder[],
  tab: QueueTab,
): PurchaseOrder[] {
  switch (tab) {
    case "All":
      return orders;
    case "Needs Attention":
      return orders.filter(
        (o) => o.status === "Review required" || o.status === "Blocked",
      );
    case "Ready":
      return orders.filter((o) => o.status === "Ready");
    case "Approved":
      return orders.filter((o) => o.status === "Approved");
    case "Closed":
      return orders.filter(
        (o) => o.status === "Changes requested" || o.status === "Rejected",
      );
  }
}

/** Search PO id and customer only — not the whole serialised object. */
export function searchOrders(
  orders: PurchaseOrder[],
  query: string,
): PurchaseOrder[] {
  const s = query.trim().toLowerCase();
  if (!s) return orders;
  return orders.filter(
    (o) =>
      o.id.toLowerCase().includes(s) || o.customer.toLowerCase().includes(s),
  );
}

export const errorCount = (o: PurchaseOrder) =>
  o.findings.filter((f) => f.severity === "Error").length;

export const warningCount = (o: PurchaseOrder) =>
  o.findings.filter((f) => f.severity === "Warning").length;
