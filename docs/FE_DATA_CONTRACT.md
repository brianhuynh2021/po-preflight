# PO Preflight — Data Contract & Schema for the Frontend

## Banking pilot extension

The `/banking` flow is independent of `PurchaseOrder`, per [BANKING_PILOT.md](BANKING_PILOT.md).
`DisbursementCase`, `BankingInvoice`, and `DisbursementAnalysis` in `app/lib/types.ts`
must match the Pydantic schema in `src/preflight/banking.py`.

- `POST /api/v1/banking/analyze` accepts manually entered VND case files; monetary fields are
  decimal integer strings, dates are `YYYY-MM-DD`; it requires authentication with at least
  the VIEWER role.
- The backend is the sole source for computing amounts and status. The FE uses `money()` for display.
- It returns only `Ready`, `Review required`, `Blocked`; there is no approval decision.
- The result contains `case_id`, `evaluated_on`, `policy_version`, `mode: pilot_manual_input`,
  `available_limit`, `eligible_invoice_amount`, `findings`.
- Findings have `code`, `severity`, `fields` (data paths), `evidence` (string map).
  Codes, formulas, and limits are described in the pilot document.
- The FE clears the result when the data is edited and never replaces an API error with a sample result.
- The checklist/source documents are all supplied by the user and are not independently verified.
- No case file is stored and no transaction is generated. `Ready` does not mean the funds are disbursed.

---

> **Source of truth:** this file. When it conflicts with a GitHub issue or
> `docs/ui-specification.md`, this contract wins.
>
> The contract was finalized by cross-checking 3 sources:
> 1. Backend rules engine — `src/preflight/rules.py`, `src/preflight/models.py`
> 2. Backend audit store — `src/preflight/store.py`
> 3. The existing prototype UI — `apps/web/app/preflight-prototype.tsx` (branch `dev`)

---

## 0. IMPORTANT WARNING ABOUT FILE PATHS

The four issues #2–#5 describe paths using a **Vite + React** structure (`apps/web/src/pages/`,
`apps/web/src/data/`, `apps/web/src/components/`).

**That structure does NOT exist on the `dev` branch.** The current `dev` branch is:

```
apps/web/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                  ← only renders <PreflightPrototype/>
│   ├── preflight-prototype.tsx   ← the ENTIRE UI lives in a single 333-line file
│   └── globals.css
├── db/  drizzle/  worker/        ← Cloudflare Workers + Drizzle ORM
└── package.json                  ← Next.js 16, React 19, Tailwind 4, vinext
```

The real stack: **Next.js 16 + React 19 + Tailwind 4 + Cloudflare Workers**, not
Vite + React + ECharts.

**Consequence for the FE team:** every path in issues #2–#5 must be remapped according to Section 8 below
before starting to code. The components the issues assume already exist (`DataTable`, `Kpi`,
`Seg`, `Panel`, `WorldMap`, `EChart`) **do not exist at all** on `dev`.

---

## 1. Order status enum (`OrderStatus`)

This is the **only** enum table. The three sources use three different spellings; this table settles them.

| FE value (used in code) | Display label | Backend `rules.py` returns | Color tone | Meaning |
| :--- | :--- | :--- | :--- | :--- |
| `Ready` | Ready | `ready_for_approval` | 🟢 `#19704c` | No findings. Eligible for approval. |
| `Review required` | Review required | `review_required` | 🟡 `#a76418` | Only findings with severity `Warning`. |
| `Blocked` | Blocked | `blocked` | 🔴 `#a5453c` | At least 1 finding with severity `Error`. |
| `Approved` | Approved | *(decided by the user)* | 🔵 `#386b8e` | Approved; recorded in the audit log. |
| `Changes requested` | Changes requested | *(decided by the user)* | 🟠 `#b45309` | The customer has been asked to fix the file. |
| `Rejected` | Rejected | *(decided by the user)* | ⚫ `#57534e` | Rejected outright. |

```ts
export type OrderStatus =
  | "Ready"
  | "Review required"
  | "Blocked"
  | "Approved"
  | "Changes requested"
  | "Rejected";
```

### 1.1. The first three statuses are DERIVED and must not be set by hand

`Ready` / `Review required` / `Blocked` are **computed from the findings**, exactly per
`rules.py:74-79`. The FE must use the function below instead of hardcoding them, otherwise the UI will drift from the backend:

```ts
export function deriveStatus(findings: Finding[]): OrderStatus {
  if (findings.some((f) => f.severity === "Error")) return "Blocked";
  if (findings.length > 0) return "Review required";
  return "Ready";
}
```

Only the last 3 statuses (`Approved`, `Changes requested`, `Rejected`) may be set directly,
and only through user actions as described in Section 6.

### 1.2. Differences from the current prototype to be aware of

The `dev` prototype has only **4** values (`Ready | Review required | Blocked | Approved`).
FE-1 must extend this to **6** by adding `Changes requested` and `Rejected`.

### 1.3. Two removed statuses (settled)

`docs/ui-specification.md` previously still listed `PROCESSING` and `EXTRACTION_REVIEW`. Both
**have been removed from the demo scope** and from `ui-specification.md`. The correct enum has **6** values.

See §7.2 and §7.3 for the reasons and the accompanying technical debt.

---

## 2. Finding — 5 error codes

These five codes match `rules.py` **exactly, 100%**. Do not add, remove, or rename any.

| `code` | `severity` | `title` (displayed) | Raised when |
| :--- | :--- | :--- | :--- |
| `PRICE_MISMATCH` | `Warning` | `Chênh lệch giá so với Catalog` (Price difference vs. catalog) | `\|poPrice − catalogPrice\| / catalogPrice × 100 > tolerance` |
| `INSUFFICIENT_STOCK` | `Warning` | `Không đủ tồn kho đáp ứng` (Insufficient stock to fulfil) | `quantity > available` |
| `UNKNOWN_SKU` | `Error` | `Mã SKU không tồn tại` (SKU does not exist) | The SKU is not in the catalog |
| `INACTIVE_SKU` | `Error` | `Sản phẩm đã ngừng kinh doanh` (Product has been discontinued) | `product.active === false` |
| `DUPLICATE_PO` | `Error` | `Trùng lặp mã đơn hàng` (Duplicate order number) | The PO number already exists in the audit store |

```ts
export type FindingCode =
  | "PRICE_MISMATCH"
  | "INSUFFICIENT_STOCK"
  | "UNKNOWN_SKU"
  | "INACTIVE_SKU"
  | "DUPLICATE_PO";

export type FindingSeverity = "Warning" | "Error";

export interface Finding {
  /** Machine-readable error code. Use this to group/filter/aggregate — do NOT use title. */
  code: FindingCode;
  /** Warning → amber tone. Error → red tone. An Error always pulls the status down to Blocked. */
  severity: FindingSeverity;
  /** Short title shown on the finding card. */
  title: string;
  /** Full explanatory sentence, 1–2 lines. */
  detail: string;
  /** Evidence line for cross-checking. See Section 2.2 for the required format. */
  evidence: string;
  /** Related SKU. `null` for DUPLICATE_PO because this error belongs to the whole order. */
  sku: string | null;
}
```

### 2.1. Immutable severity rule

`severity` is **hard-bound to `code`**; it is not a free-form field:

```ts
export const SEVERITY_BY_CODE: Record<FindingCode, FindingSeverity> = {
  PRICE_MISMATCH:     "Warning",
  INSUFFICIENT_STOCK: "Warning",
  UNKNOWN_SKU:        "Error",
  INACTIVE_SKU:       "Error",
  DUPLICATE_PO:       "Error",
};
```

Any seed data that violates this table is wrong. Add a test asserting this.

### 2.2. Mandatory `evidence` format per code

This is what makes the Order Detail screen valuable. Use the exact template, separated by ` · `:

| `code` | `evidence` template | Real example |
| :--- | :--- | :--- |
| `PRICE_MISMATCH` | `PO: {poPrice} · Catalog: {catalogPrice} · Lệch: {±%} ({±amount})` (`Lệch` = Difference) | `PO: $74.00 · Catalog: $72.00 · Lệch: +2.78% (+$120.00)` |
| `INSUFFICIENT_STOCK` | `Đặt: {qty} · Tồn kho: {available} · Thiếu: {qty−available}` (`Đặt` = Ordered, `Tồn kho` = In stock, `Thiếu` = Short) | `Đặt: 60 · Tồn kho: 38 · Thiếu: 22` |
| `UNKNOWN_SKU` | `SKU nhận được: {sku} · Khớp catalog: 0` (`SKU nhận được` = SKU received, `Khớp catalog` = Catalog matches) | `SKU nhận được: DSK-404 · Khớp catalog: 0` |
| `INACTIVE_SKU` | `SKU: {sku} · Trạng thái: Inactive · Ngừng bán từ: {date}` (`Trạng thái` = Status, `Ngừng bán từ` = Discontinued since) | `SKU: STG-410 · Trạng thái: Inactive · Ngừng bán từ: 2026-06-01` |
| `DUPLICATE_PO` | `PO: {id} · Đã xử lý: {date} · Khách hàng: {customer}` (`Đã xử lý` = Processed on, `Khách hàng` = Customer) | `PO: PO-10428 · Đã xử lý: 2026-08-14 · Khách hàng: Northstar Retail` |

**Note on percentages:** `rules.py:60` computes against the **catalog price as the denominator**, and uses
`abs()`, so the backend yields a positive number. The FE needs the **± sign** so the reviewer can tell whether the PO price is higher or lower:

```ts
export function priceDeltaPercent(poPrice: number, catalogPrice: number): number {
  if (catalogPrice <= 0) return 0;                   // matches rules.py: skip when catalog price = 0
  return ((poPrice - catalogPrice) / catalogPrice) * 100;  // keep the sign, do NOT use abs()
}
```

---

## 3. LineItem

```ts
export interface LineItem {
  sku: string;
  /** Product name from the catalog. For UNKNOWN_SKU use the string "Unknown product". */
  product: string;
  /** Quantity the customer ordered on the PO. */
  quantity: number;
  /** Available stock at the time of analysis. UNKNOWN_SKU → 0. */
  available: number;
  /** Unit price stated on the customer's PO. */
  unitPrice: number;
  /** Unit price in the company catalog. UNKNOWN_SKU → 0 (nothing to compare against). */
  catalogPrice: number;
}
```

**The line amount (`lineTotal`) is a derived field and is not stored:**

```ts
export const lineTotal = (l: LineItem) => l.quantity * l.unitPrice;
```

Use `unitPrice` (the price on the PO), **not** `catalogPrice` — the total must reflect
exactly what the customer sent, which is precisely what is being checked.

### 3.1. Cell highlight rules in the Line Items table (FE-3)

| Condition | Cell to highlight | Tone |
| :--- | :--- | :--- |
| `unitPrice !== catalogPrice && catalogPrice > 0` | the `unitPrice` cell | 🟡 amber |
| `quantity > available` | the `quantity` cell | 🟡 amber |
| `catalogPrice === 0` (unknown SKU) | the entire row | 🔴 red |

---

## 4. PurchaseOrder

```ts
export interface PurchaseOrder {
  /** PO number, e.g. "PO-10428". The business key used to detect DUPLICATE_PO. */
  id: string;
  customer: string;
  /** ISO 8601 UTC, e.g. "2026-08-31T10:42:00Z". See Section 4.1. */
  submittedAt: string;
  /** Original file name the customer sent, e.g. "northstar-po-10428.pdf". */
  sourceFile: string;
  /** Total amount = Σ lineTotal. See Section 4.2. */
  value: number;
  /** ISO 4217. Multi-currency — always format via money(value, currency). See §7.1. */
  currency: string;
  status: OrderStatus;
  /** Full list of violations. The error-count badge = findings.length. See Section 4.3. */
  findings: Finding[];
  lines: LineItem[];
  /** Person in charge. "Unassigned" if not yet assigned. */
  owner: string;
  /** Decision history, newest first. Empty if no one has decided yet. */
  decisions: Decision[];
}
```

### 4.1. `submittedAt` must be ISO, not a human-readable string

The prototype currently stores `submitted: "Today, 10:42 AM"` — **this string cannot be sorted and will be wrong
as early as the next day**. Issue #3 requires "sort by submission date", so FE-1 **must** switch to ISO
and format at render time:

```ts
export function formatSubmitted(iso: string, now = new Date()): string {
  const d = new Date(iso);
  const time = d.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
  const days = Math.floor((+startOfDay(now) - +startOfDay(d)) / 86_400_000);
  if (days === 0) return `Hôm nay, ${time}`;
  if (days === 1) return `Hôm qua, ${time}`;
  return d.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" });
}
```

The literal strings `Hôm nay` ("Today") and `Hôm qua` ("Yesterday") are the displayed UI labels.

### 4.2. `value` is a derived field — do not let it drift from `lines`

```ts
export const orderValue = (o: PurchaseOrder) => o.lines.reduce((s, l) => s + lineTotal(l), 0);
```

Seed data must satisfy `orderValue(o) === o.value`. **The current prototype violates this:**
`PO-10428` declares `value: 18420` but `60×74 + 30×466 = 4440 + 13980 = 18420` ✅ correct;
and `PO-10417` declares `24860` while `55×452 = 24860` ✅ correct. Re-check everything when
re-seeding, and add a test for this invariant.

### 4.3. `findings` is an array, NOT a count

The prototype currently splits this into two separate fields: `findings: number` (a count) and `issues: [...]`
(the list). This is a **source of data-drift bugs** — the two fields can contradict each other.

The contract merges them into **one** array `findings: Finding[]`. The badge on the Orders Queue uses
`findings.length`. The `issues` field is **removed**.

In addition, the old `issues[].severity` used `"Review" | "Blocked"` — those are *status* names, not
*severity* names. The contract uses `"Warning" | "Error"` to match `rules.py`.

---

## 5. Product (Catalog)

```ts
export interface Product {
  sku: string;
  name: string;
  /** A number, NOT a formatted string. See the warning below. */
  unitPrice: number;
  stock: number;
  active: boolean;
}
```

**The prototype currently stores `price: "$466.00"` as a string** — it cannot be compared numerically, so it
cannot be used to compute `PRICE_MISMATCH`. FE-1 must change it to `number` and format at render time.

Likewise, `state: "Active" | "Inactive"` becomes `active: boolean` to match
`models.py:Product.active`.

---

## 6. Decision — the reviewer's decision

Matches the `decisions` table in `store.py` (`decision`, `actor`, `note`, `created_at`).

```ts
export type DecisionType = "APPROVE" | "REQUEST_CHANGES" | "REJECT";

export interface Decision {
  type: DecisionType;
  /** The person who performed the action. */
  actor: string;
  /** Note. Whether it is required: see the matrix in Section 6.2. */
  note: string;
  /** ISO 8601 UTC. */
  createdAt: string;
}
```

### 6.1. Action matrix — which button is enabled in which status

This is the part issue #4 is missing. **Do not render all 3 buttons unconditionally.**

| Current status | Approve | Request Changes | Reject |
| :--- | :---: | :---: | :---: |
| `Ready` | ✅ enabled | ✅ enabled | ✅ enabled |
| `Review required` | ✅ enabled | ✅ enabled | ✅ enabled |
| `Blocked` | ❌ **disabled** | ✅ enabled | ✅ enabled |
| `Approved` | ❌ disabled | ❌ disabled | ❌ disabled |
| `Changes requested` | ❌ disabled | ❌ disabled | ✅ enabled |
| `Rejected` | ❌ disabled | ❌ disabled | ❌ disabled |

**Why `Blocked` does not allow Approve:** `Blocked` means there is an `Error` — the SKU does not exist,
the product is discontinued, or the order number is a duplicate. No note can make a nonexistent SKU
exist. This is a business constraint, not a UI choice.

A disabled button must have a tooltip stating the reason, for example:
*"Không thể duyệt: đơn có 1 lỗi nghiêm trọng cần sửa trước."* (Cannot approve: the order has 1 serious error that must be fixed first.)

```ts
export function canDecide(status: OrderStatus, type: DecisionType): boolean {
  switch (type) {
    case "APPROVE":         return status === "Ready" || status === "Review required";
    case "REQUEST_CHANGES": return status === "Ready" || status === "Review required" || status === "Blocked";
    case "REJECT":          return status !== "Approved" && status !== "Rejected";
  }
}
```

### 6.2. When a note is REQUIRED

| Action | Note | Reason |
| :--- | :--- | :--- |
| Approve an order in `Ready` | optional | There are no violations to explain. |
| Approve an order in `Review required` | **required**, ≥ 10 characters | This is an "exceptional approval" — approving over warnings; the reason must be recorded in the audit log. |
| Request Changes | **required**, ≥ 10 characters | This content is sent to the customer. |
| Reject | **required**, ≥ 10 characters | The decision is irreversible. |

### 6.3. Status transition after a decision

```
APPROVE          → Approved
REQUEST_CHANGES  → Changes requested
REJECT           → Rejected
```

Each decision **prepends** a record to the head of `order.decisions` — it does not overwrite earlier records.

---

## 7. THREE DECISIONS SETTLED

> The three points below were previously open questions. They were settled on 2026-08-31. FE code follows this.

### 7.1. ✅ Currency: MULTI-CURRENCY

**Decision:** keep the `currency` field on each order and format according to that field.

Original conflict:

| Source | Value |
| :--- | :--- |
| `models.py:27` | `currency: str = "VND"` |
| `dev` prototype | all seed data uses `"USD"`, and `money()` hardcodes `currency: "USD"` |
| Issue #3 | "Currency formatting VND / USD" (both) |

**Reason for choosing multi-currency:** the `currency` field already exists in **both** models (backend
`models.py:27` and the prototype). Nothing new needs to be added — it is only a matter of using it properly instead of ignoring it.
It is also the only way to satisfy issue #3 ("VND / USD").

Implemented in `derive.ts`:

```ts
export const money = (value: number, currency: string) =>
  new Intl.NumberFormat(currency === "VND" ? "vi-VN" : "en-US",
    { style: "currency", currency, maximumFractionDigits: 0 }).format(value);
```

**Consequences for the FE:**
- ❌ Do not use the single-argument `money(value)`. The old prototype function hardcodes USD — it must be removed.
- ❌ Do not hardcode the `$` symbol anywhere. The prototype currently has `${line.unitPrice.toFixed(2)}` in the line items table and `catalog[].price: "$466.00"` — both must be fixed.
- ✅ Always pass `order.currency`: `money(o.value, o.currency)`.
- ✅ For `LineItem`, the currency is **inherited from the parent order** — `LineItem` has no `currency` field of its own, because a single PO cannot mix multiple currencies.
- ✅ The seed should include **at least 1 VND order** to expose any USD hardcoding right away.

**`maximumFractionDigits: 0`** is deliberate: VND does not use fractional amounts, and for USD, POs are typically
round thousands — decimals only make the table harder to read. Price differences are still displayed precisely via the finding's
`evidence`.

### 7.2. ✅ `EXTRACTION_REVIEW`: DROPPED from the demo

**Decision:** do not put `Extraction review` into `OrderStatus`. The enum keeps exactly **6** values.

Accompanying change: **remove `PROCESSING` and `EXTRACTION_REVIEW` from `docs/ui-specification.md`** so the two
documents no longer contradict each other. Done in this same PR.

**⚠️ This is deliberate technical debt, not an oversight.**

The accepted risk: PDF/image extraction can be wrong. If OCR reads `quantity: 60` as `600`,
the system will run the rules on garbage numbers and then conclude "Insufficient stock" with great confidence.
The reviewer has no step at which to catch it.

**Conditions for accepting this risk:**
- It applies only to the **demo/prototype**, where the data is static seed data rather than real OCR.
- The upload modal **must** keep the warning line already in the prototype:
  *"Preflight will extract the order and run company validation rules. You will review the
  result before any approval."*
- Before real OCR is wired in, this decision **must** be reopened.

Logged in the backlog: see the issue "Tech debt: restore the Extraction Review step before wiring in real OCR" (original title: "Tech debt: khôi phục bước Extraction Review trước khi nối OCR thật").

**Note on `architecture.md`:** the state machine at `docs/architecture.md:133-144` still describes
`PROCESSING → EXTRACTION_REVIEW`. That file describes the **target architecture of the complete system**,
not the demo scope — so leave it as is and do not edit it. This contract governs only the FE demo scope.

### 7.3. ✅ `PROCESSING`: keep in component state

**Decision:** do not add it to `OrderStatus`.

With a demo that uses `setTimeout` to simulate the extraction animation, the "processing" state exists only
within the lifetime of `UploadModal`. It is not a business status of the order — no one
filters the queue by it, and no one makes a decision on it.

```tsx
type UploadPhase = "idle" | "extracting" | "validating" | "done";
const [phase, setPhase] = useState<UploadPhase>("idle");
```

An order appears in `orders[]` only **after** `phase === "done"`, and by then it already has a
`status` derived from `deriveStatus(findings)`.

---

## 8. PATH MAP — What the issue says → Where the work actually goes

Proposed structure, gradually splitting out of the current 333-line file:

| What the issue says | Does not exist on `dev` | Actual path to use |
| :--- | :--- | :--- |
| `src/data/seed.ts`, `src/data/orders.ts` | ✗ | `apps/web/app/lib/types.ts` + `apps/web/app/lib/seed.ts` |
| `src/pages/Orders.tsx` | ✗ | `apps/web/app/components/OrdersQueue.tsx` |
| `src/pages/Dashboard.tsx` | ✗ | `apps/web/app/components/Overview.tsx` |
| `src/pages/Products.tsx` | ✗ | `apps/web/app/components/CatalogView.tsx` |
| `OrderDetail.tsx` | ✗ | `apps/web/app/components/OrderDetail.tsx` |
| `components/UploadModal.tsx` | ✗ | `apps/web/app/components/UploadModal.tsx` |
| `DataTable`, `Kpi`, `Seg`, `Panel` | ✗ | Must be written by hand, or use a plain Tailwind table |
| `WorldMap`, `EChart` (ECharts) | ✗ | See Section 9 |

The three derived functions `deriveStatus`, `lineTotal`, `orderValue` and the format helpers should live in
`apps/web/app/lib/derive.ts` so that all four issues share them.

---

## 9. WORLDMAP AND ECHARTS — scope must be cut

The 10-screen specification (Section 3, screen 1) requires a **WorldMap showing order distribution by region/branch**.

**The problem:** no model has a geographic field. `models.py:Order` has only `po_number`,
`customer`, `items`, `currency`. The prototype has none either. Adding a WorldMap means **adding a new
field to both the backend and the frontend** — that is backend work, not FE-4.

In addition, `dev` **does not install ECharts** (check `package.json`: only next, react, react-dom).

Recommendation for FE-4:
- **Drop the WorldMap** from scope. It is a leftover from the old e-commerce template and does not serve the PO approval workflow.
- **Replace the ECharts chart with statistics backed by real data:** count findings by `code`. This data is already available, and it answers exactly the operational question *"which type of violation occurs most often?"*

```ts
export function findingsByCode(orders: PurchaseOrder[]): Record<FindingCode, number> {
  const acc = { PRICE_MISMATCH: 0, INSUFFICIENT_STOCK: 0,
                UNKNOWN_SKU: 0, INACTIVE_SKU: 0, DUPLICATE_PO: 0 };
  for (const o of orders) for (const f of o.findings) acc[f.code]++;
  return acc;
}
```

A series of horizontal bars made with `div` + Tailwind is enough; no additional charting library is needed.

---

## 10. KPI Dashboard (FE-4) — exact formulas

```ts
export const needsAttention = (o: PurchaseOrder[]) =>
  o.filter((x) => x.status === "Review required" || x.status === "Blocked").length;

export const readyForApproval = (o: PurchaseOrder[]) =>
  o.filter((x) => x.status === "Ready").length;

export const approvedToday = (o: PurchaseOrder[], now = new Date()) =>
  o.filter((x) => x.decisions.some(
    (d) => d.type === "APPROVE" && isSameDay(new Date(d.createdAt), now))).length;
```

### 10.1. ⚠️ `Avg decision time` needs data that does not exist yet

This KPI = the average of `decision.createdAt − order.submittedAt` across decided orders.

It can be computed **only if** `submittedAt` is ISO (Section 4.1) and `decisions[]` has `createdAt`. If
FE-1 keeps the string `"Today, 10:42 AM"`, then **this KPI cannot be computed** and would have to be hardcoded
— in other words, a fake number on the dashboard.

```ts
export function avgDecisionTimeMinutes(orders: PurchaseOrder[]): number | null {
  const spans = orders.flatMap((o) => {
    const d = o.decisions.at(-1);           // the chronologically first decision
    return d ? [(+new Date(d.createdAt) - +new Date(o.submittedAt)) / 60_000] : [];
  });
  return spans.length ? spans.reduce((a, b) => a + b, 0) / spans.length : null;
}
```

Return `null` when there are no decisions yet → the UI displays `—`, **not `0m`**.

---

## 11. Orders Queue filters (FE-2)

```ts
export type QueueTab = "All" | "Needs Attention" | "Ready" | "Approved";

export function filterByTab(orders: PurchaseOrder[], tab: QueueTab): PurchaseOrder[] {
  switch (tab) {
    case "All":             return orders;
    case "Needs Attention": return orders.filter((o) => o.status === "Review required" || o.status === "Blocked");
    case "Ready":           return orders.filter((o) => o.status === "Ready");
    case "Approved":        return orders.filter((o) => o.status === "Approved");
  }
}
```

### 11.1. ⚠️ The four tabs do not cover all six statuses

`Changes requested` and `Rejected` **do not appear in any tab other than `All`**. A rejected
order will disappear from every filter tab — users have no way to filter them out.

Three options: add a `Closed` tab (merging these 2 statuses); or add 2 separate tabs; or accept
that they can only be found under `All`. **Recommendation: add a `Closed` tab.**

### 11.2. Search

Search by **PO number** and **customer name**, case-insensitive:

```ts
export function searchOrders(orders: PurchaseOrder[], q: string): PurchaseOrder[] {
  const s = q.trim().toLowerCase();
  if (!s) return orders;
  return orders.filter((o) =>
    o.id.toLowerCase().includes(s) || o.customer.toLowerCase().includes(s));
}
```

**Do not** use `JSON.stringify(o).includes(...)` as the old code did — that would produce false matches on file
names, notes, owner names, and even finding content.

---

## 12. Seed data — four required cases

FE-1's completion criteria require the seed to cover all the cases. At a minimum:

| PO | Status | Currency | Findings | Test case |
| :--- | :--- | :--- | :--- | :--- |
| `PO-10421` | `Ready` | USD | — | 100% match: correct prices, sufficient stock |
| `PO-10428` | `Review required` | USD | `PRICE_MISMATCH` + `INSUFFICIENT_STOCK` | Two warnings at once |
| `PO-10431` | `Blocked` | USD | `UNKNOWN_SKU` | Nonexistent SKU |
| `PO-10433` | `Blocked` | **VND** | `INACTIVE_SKU` | Discontinued SKU **+ multi-currency case** |
| `PO-10428-B` | `Blocked` | USD | `DUPLICATE_PO` | Same number as an already-processed order |
| `PO-10417` | `Approved` | USD | — | Approved, has `decisions[]` |
| `PO-10402` | `Changes requested` | **VND** | `PRICE_MISMATCH` | Changes requested **+ multi-currency case** |
| `PO-10399` | `Rejected` | USD | `UNKNOWN_SKU` | Rejected |

**At least 2 VND orders are required.** If the seed is all USD, every place that hardcodes `$` will still look
correct and the bug will only surface in production. The two VND orders above exist to break that assumption on the
very first screen.

Three invariants the seed must satisfy (these should be written as tests):

```ts
orders.every((o) => o.value === orderValue(o));
orders.every((o) => o.findings.every((f) => f.severity === SEVERITY_BY_CODE[f.code]));
orders.filter((o) => !["Approved","Changes requested","Rejected"].includes(o.status))
      .every((o) => o.status === deriveStatus(o.findings));
new Set(orders.map((o) => o.currency)).size >= 2;  // §7.1: there must be at least 2 currencies
```

---

## 13. Implementation order

FE-1 **hard-blocks** all three remaining issues — they cannot be done in parallel:

```
FE-1 (#2) types + seed
   ├──→ FE-2 (#3) Orders Queue
   ├──→ FE-3 (#4) Order Detail   ← heaviest, do after FE-2
   └──→ FE-4 (#5) Dashboard + Upload
```

FE-4 depends on FE-2 (upload must be able to insert the new order into the queue), so it is done last.
