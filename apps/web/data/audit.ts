import type { ActivityEventType } from "../app/lib/types";

/** A single row on the Audit log screen. UI-only; not part of the data contract. */
export interface AuditEntry {
  id: string;
  time: string;
  event: string;
  actor: string;
  order: string;
  detail: string;
  type: ActivityEventType;
}

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