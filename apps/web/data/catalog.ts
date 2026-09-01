import type { Product } from "../app/lib/types";

/** Company product catalog — the reference used by order validation rules. */
export const catalog: Product[] = [
  { sku: "CHR-110", name: "Morrow task chair", unitPrice: 466, stock: 81, active: true },
  { sku: "LMP-200", name: "Arc desk lamp", unitPrice: 72, stock: 38, active: true },
  { sku: "TB-320", name: "Tanner meeting table", unitPrice: 960, stock: 24, active: true },
  { sku: "STG-410", name: "Rowan storage unit", unitPrice: 1240, stock: 0, active: false },
];
