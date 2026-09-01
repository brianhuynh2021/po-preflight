import type { ValidationRule } from "../app/lib/types";

/** Deterministic controls applied to every normalized order. */
export const rules: ValidationRule[] = [
  { name: "Unknown SKU", description: "Block line items that do not match the company catalog.", severity: "Block", owner: "Operations" },
  { name: "Inactive product", description: "Block products that are not available for new orders.", severity: "Block", owner: "Operations" },
  { name: "Catalog price mismatch", description: "Require review when the received price differs from the active catalog.", severity: "Review", owner: "Sales" },
  { name: "Insufficient stock", description: "Require review when requested quantity exceeds available inventory.", severity: "Review", owner: "Operations" },
  { name: "Duplicate PO number", description: "Block a PO number already recorded for the same customer.", severity: "Block", owner: "Finance" },
];
