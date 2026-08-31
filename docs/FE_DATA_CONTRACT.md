# PO Preflight — Data Contract & Schema cho Frontend

> **Nguồn chân lý (source of truth):** file này. Khi có mâu thuẫn với issue GitHub hoặc
> `docs/ui-specification.md`, contract này thắng.
>
> Contract được chốt bằng cách đối chiếu 3 nguồn:
> 1. Backend rules engine — `src/preflight/rules.py`, `src/preflight/models.py`
> 2. Backend audit store — `src/preflight/store.py`
> 3. Prototype UI hiện có — `apps/web/app/preflight-prototype.tsx` (branch `dev`)

---

## 0. CẢNH BÁO QUAN TRỌNG VỀ ĐƯỜNG DẪN FILE

Bốn issue #2–#5 mô tả đường dẫn theo cấu trúc **Vite + React** (`apps/web/src/pages/`,
`apps/web/src/data/`, `apps/web/src/components/`).

**Cấu trúc đó KHÔNG tồn tại trên branch `dev`.** Branch `dev` hiện tại là:

```
apps/web/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                  ← chỉ render <PreflightPrototype/>
│   ├── preflight-prototype.tsx   ← TOÀN BỘ UI nằm trong 1 file 333 dòng
│   └── globals.css
├── db/  drizzle/  worker/        ← Cloudflare Workers + Drizzle ORM
└── package.json                  ← Next.js 16, React 19, Tailwind 4, vinext
```

Stack thật: **Next.js 16 + React 19 + Tailwind 4 + Cloudflare Workers**, không phải
Vite + React + ECharts.

**Hệ quả cho FE team:** mọi đường dẫn trong issue #2–#5 phải map lại theo Mục 8 bên dưới
trước khi bắt tay code. Các thành phần mà issue giả định đã tồn tại (`DataTable`, `Kpi`,
`Seg`, `Panel`, `WorldMap`, `EChart`) **đều không có** trên `dev`.

---

## 1. Enum trạng thái đơn hàng (`OrderStatus`)

Đây là bảng enum **duy nhất**. Ba nguồn đang dùng ba cách viết khác nhau; bảng này chốt lại.

| Giá trị FE (dùng trong code) | Nhãn hiển thị | Backend `rules.py` trả về | Tone màu | Ý nghĩa |
| :--- | :--- | :--- | :--- | :--- |
| `Ready` | Ready | `ready_for_approval` | 🟢 `#19704c` | Không có finding nào. Đủ điều kiện duyệt. |
| `Review required` | Review required | `review_required` | 🟡 `#a76418` | Chỉ có finding severity `Warning`. |
| `Blocked` | Blocked | `blocked` | 🔴 `#a5453c` | Có ít nhất 1 finding severity `Error`. |
| `Approved` | Approved | *(do người dùng quyết định)* | 🔵 `#386b8e` | Đã được duyệt, ghi vào audit log. |
| `Changes requested` | Changes requested | *(do người dùng quyết định)* | 🟠 `#b45309` | Đã yêu cầu khách sửa file. |
| `Rejected` | Rejected | *(do người dùng quyết định)* | ⚫ `#57534e` | Từ chối dứt điểm. |

```ts
export type OrderStatus =
  | "Ready"
  | "Review required"
  | "Blocked"
  | "Approved"
  | "Changes requested"
  | "Rejected";
```

### 1.1. Ba trạng thái đầu là DẪN XUẤT, không được set tay

`Ready` / `Review required` / `Blocked` được **tính ra từ findings**, đúng theo
`rules.py:74-79`. FE phải dùng hàm dưới đây thay vì gán cứng, nếu không UI sẽ lệch backend:

```ts
export function deriveStatus(findings: Finding[]): OrderStatus {
  if (findings.some((f) => f.severity === "Error")) return "Blocked";
  if (findings.length > 0) return "Review required";
  return "Ready";
}
```

Chỉ 3 trạng thái cuối (`Approved`, `Changes requested`, `Rejected`) mới được set trực tiếp,
và chỉ thông qua hành động của người dùng ở Mục 6.

### 1.2. Chênh lệch cần biết với prototype hiện tại

Prototype `dev` mới có **4** giá trị (`Ready | Review required | Blocked | Approved`).
FE-1 phải mở rộng thành **6** bằng cách thêm `Changes requested` và `Rejected`.

### 1.3. Hai trạng thái đã loại bỏ (đã chốt)

`docs/ui-specification.md` trước đây còn liệt kê `PROCESSING` và `EXTRACTION_REVIEW`. Cả hai
**đã bị xoá khỏi phạm vi demo** và khỏi `ui-specification.md`. Enum đúng **6** giá trị.

Xem §7.2 và §7.3 để biết lý do và nợ kỹ thuật đi kèm.

---

## 2. Finding — 5 mã lỗi

Năm mã này khớp **chính xác 100%** với `rules.py`. Không được thêm/bớt/đổi tên.

| `code` | `severity` | `title` (hiển thị) | Sinh ra khi |
| :--- | :--- | :--- | :--- |
| `PRICE_MISMATCH` | `Warning` | Chênh lệch giá so với Catalog | `\|poPrice − catalogPrice\| / catalogPrice × 100 > tolerance` |
| `INSUFFICIENT_STOCK` | `Warning` | Không đủ tồn kho đáp ứng | `quantity > available` |
| `UNKNOWN_SKU` | `Error` | Mã SKU không tồn tại | SKU không có trong catalog |
| `INACTIVE_SKU` | `Error` | Sản phẩm đã ngừng kinh doanh | `product.active === false` |
| `DUPLICATE_PO` | `Error` | Trùng lặp mã đơn hàng | PO number đã có trong audit store |

```ts
export type FindingCode =
  | "PRICE_MISMATCH"
  | "INSUFFICIENT_STOCK"
  | "UNKNOWN_SKU"
  | "INACTIVE_SKU"
  | "DUPLICATE_PO";

export type FindingSeverity = "Warning" | "Error";

export interface Finding {
  /** Mã lỗi máy đọc. Dùng cái này để nhóm/lọc/thống kê — KHÔNG dùng title. */
  code: FindingCode;
  /** Warning → tone amber. Error → tone red. Error luôn kéo status về Blocked. */
  severity: FindingSeverity;
  /** Tiêu đề ngắn hiển thị trên thẻ finding. */
  title: string;
  /** Câu giải thích đầy đủ, 1–2 dòng. */
  detail: string;
  /** Dòng bằng chứng đối chiếu. Xem Mục 2.2 để biết định dạng bắt buộc. */
  evidence: string;
  /** SKU liên quan. `null` với DUPLICATE_PO vì lỗi này thuộc về cả đơn. */
  sku: string | null;
}
```

### 2.1. Quy tắc severity bất biến

`severity` **bị ràng buộc cứng theo `code`**, không phải trường tự do:

```ts
export const SEVERITY_BY_CODE: Record<FindingCode, FindingSeverity> = {
  PRICE_MISMATCH:     "Warning",
  INSUFFICIENT_STOCK: "Warning",
  UNKNOWN_SKU:        "Error",
  INACTIVE_SKU:       "Error",
  DUPLICATE_PO:       "Error",
};
```

Seed data nào vi phạm bảng này là sai. Nên thêm 1 test khẳng định điều đó.

### 2.2. Định dạng `evidence` bắt buộc theo từng mã

Đây là phần khiến màn hình Order Detail có giá trị. Dùng đúng khuôn, phân tách bằng ` · `:

| `code` | Khuôn `evidence` | Ví dụ thật |
| :--- | :--- | :--- |
| `PRICE_MISMATCH` | `PO: {poPrice} · Catalog: {catalogPrice} · Lệch: {±%} ({±tiền})` | `PO: $74.00 · Catalog: $72.00 · Lệch: +2.78% (+$120.00)` |
| `INSUFFICIENT_STOCK` | `Đặt: {qty} · Tồn kho: {available} · Thiếu: {qty−available}` | `Đặt: 60 · Tồn kho: 38 · Thiếu: 22` |
| `UNKNOWN_SKU` | `SKU nhận được: {sku} · Khớp catalog: 0` | `SKU nhận được: DSK-404 · Khớp catalog: 0` |
| `INACTIVE_SKU` | `SKU: {sku} · Trạng thái: Inactive · Ngừng bán từ: {date}` | `SKU: STG-410 · Trạng thái: Inactive · Ngừng bán từ: 2026-06-01` |
| `DUPLICATE_PO` | `PO: {id} · Đã xử lý: {date} · Khách hàng: {customer}` | `PO: PO-10428 · Đã xử lý: 2026-08-14 · Khách hàng: Northstar Retail` |

**Lưu ý phần trăm:** `rules.py:60` tính trên **giá catalog làm mẫu số**, và dùng
`abs()` nên backend ra số dương. FE cần **dấu ±** để người duyệt biết đắt hay rẻ hơn:

```ts
export function priceDeltaPercent(poPrice: number, catalogPrice: number): number {
  if (catalogPrice <= 0) return 0;                   // khớp rules.py: bỏ qua khi giá catalog = 0
  return ((poPrice - catalogPrice) / catalogPrice) * 100;  // giữ dấu, KHÔNG abs()
}
```

---

## 3. LineItem

```ts
export interface LineItem {
  sku: string;
  /** Tên sản phẩm từ catalog. Với UNKNOWN_SKU dùng chuỗi "Unknown product". */
  product: string;
  /** Số lượng khách đặt trên PO. */
  quantity: number;
  /** Tồn kho khả dụng tại thời điểm phân tích. UNKNOWN_SKU → 0. */
  available: number;
  /** Đơn giá ghi trên PO của khách. */
  unitPrice: number;
  /** Đơn giá trong catalog công ty. UNKNOWN_SKU → 0 (không có gì để đối chiếu). */
  catalogPrice: number;
}
```

**Thành tiền (`lineTotal`) là trường dẫn xuất, không lưu:**

```ts
export const lineTotal = (l: LineItem) => l.quantity * l.unitPrice;
```

Dùng `unitPrice` (giá trên PO), **không** dùng `catalogPrice` — tổng tiền phải phản ánh
đúng cái khách đã gửi, đó chính là điều đang được đem ra soát.

### 3.1. Quy tắc highlight ô trong bảng Line Items (FE-3)

| Điều kiện | Ô cần tô | Tone |
| :--- | :--- | :--- |
| `unitPrice !== catalogPrice && catalogPrice > 0` | ô `unitPrice` | 🟡 amber |
| `quantity > available` | ô `quantity` | 🟡 amber |
| `catalogPrice === 0` (SKU lạ) | cả dòng | 🔴 red |

---

## 4. PurchaseOrder

```ts
export interface PurchaseOrder {
  /** Mã PO, vd "PO-10428". Là khoá nghiệp vụ dùng để phát hiện DUPLICATE_PO. */
  id: string;
  customer: string;
  /** ISO 8601 UTC, vd "2026-08-31T10:42:00Z". Xem Mục 4.1. */
  submittedAt: string;
  /** Tên file gốc khách gửi, vd "northstar-po-10428.pdf". */
  sourceFile: string;
  /** Tổng tiền = Σ lineTotal. Xem Mục 4.2. */
  value: number;
  /** ISO 4217. Đa tiền tệ — luôn format qua money(value, currency). Xem §7.1. */
  currency: string;
  status: OrderStatus;
  /** Danh sách vi phạm đầy đủ. Badge số lỗi = findings.length. Xem Mục 4.3. */
  findings: Finding[];
  lines: LineItem[];
  /** Người phụ trách. "Unassigned" nếu chưa gán. */
  owner: string;
  /** Lịch sử quyết định, mới nhất trước. Rỗng nếu chưa ai quyết định. */
  decisions: Decision[];
}
```

### 4.1. `submittedAt` phải là ISO, không phải chuỗi người đọc

Prototype hiện lưu `submitted: "Today, 10:42 AM"` — **chuỗi này không sort được và sẽ sai
ngay hôm sau**. Issue #3 yêu cầu "sort theo ngày gửi", nên FE-1 **bắt buộc** đổi sang ISO
và format lúc render:

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

### 4.2. `value` là trường dẫn xuất — đừng để nó trôi khỏi `lines`

```ts
export const orderValue = (o: PurchaseOrder) => o.lines.reduce((s, l) => s + lineTotal(l), 0);
```

Seed data phải thoả `orderValue(o) === o.value`. **Prototype hiện tại đang vi phạm:**
`PO-10428` khai `value: 18420` nhưng `60×74 + 30×466 = 4440 + 13980 = 18420` ✅ đúng;
còn `PO-10417` khai `24860` trong khi `55×452 = 24860` ✅ đúng. Kiểm lại toàn bộ khi seed
lại, và thêm test cho bất biến này.

### 4.3. `findings` là mảng, KHÔNG phải số đếm

Prototype hiện tách làm hai trường rời rạc: `findings: number` (số đếm) và `issues: [...]`
(danh sách). Đây là **nguồn lỗi lệch dữ liệu** — hai trường có thể mâu thuẫn nhau.

Contract gộp lại thành **một** mảng `findings: Finding[]`. Badge trên Orders Queue lấy
`findings.length`. Trường `issues` bị **loại bỏ**.

Đồng thời `issues[].severity` cũ dùng `"Review" | "Blocked"` — đó là tên *trạng thái*, không
phải tên *mức độ*. Contract dùng `"Warning" | "Error"` cho khớp `rules.py`.

---

## 5. Product (Catalog)

```ts
export interface Product {
  sku: string;
  name: string;
  /** Số, KHÔNG phải chuỗi đã format. Xem cảnh báo bên dưới. */
  unitPrice: number;
  stock: number;
  active: boolean;
}
```

**Prototype đang lưu `price: "$466.00"` dạng chuỗi** — không so sánh số học được, nên không
thể dùng để tính `PRICE_MISMATCH`. FE-1 phải đổi sang `number` và format lúc render.

Tương tự, `state: "Active" | "Inactive"` đổi thành `active: boolean` cho khớp
`models.py:Product.active`.

---

## 6. Decision — quyết định của người duyệt

Khớp bảng `decisions` trong `store.py` (`decision`, `actor`, `note`, `created_at`).

```ts
export type DecisionType = "APPROVE" | "REQUEST_CHANGES" | "REJECT";

export interface Decision {
  type: DecisionType;
  /** Người thực hiện. */
  actor: string;
  /** Ghi chú. Bắt buộc hay không: xem ma trận Mục 6.2. */
  note: string;
  /** ISO 8601 UTC. */
  createdAt: string;
}
```

### 6.1. Ma trận hành động — nút nào bật ở trạng thái nào

Đây là phần issue #4 còn thiếu. **Không được render cả 3 nút vô điều kiện.**

| Status hiện tại | Approve | Request Changes | Reject |
| :--- | :---: | :---: | :---: |
| `Ready` | ✅ bật | ✅ bật | ✅ bật |
| `Review required` | ✅ bật | ✅ bật | ✅ bật |
| `Blocked` | ❌ **tắt** | ✅ bật | ✅ bật |
| `Approved` | ❌ tắt | ❌ tắt | ❌ tắt |
| `Changes requested` | ❌ tắt | ❌ tắt | ✅ bật |
| `Rejected` | ❌ tắt | ❌ tắt | ❌ tắt |

**Vì sao `Blocked` không cho Approve:** `Blocked` nghĩa là có `Error` — SKU không tồn tại,
sản phẩm ngừng bán, hoặc trùng mã đơn. Không có ghi chú nào làm cho một SKU không tồn tại
trở nên tồn tại. Đây là ràng buộc nghiệp vụ, không phải lựa chọn giao diện.

Nút bị tắt phải có tooltip nêu lý do, ví dụ:
*"Không thể duyệt: đơn có 1 lỗi nghiêm trọng cần sửa trước."*

```ts
export function canDecide(status: OrderStatus, type: DecisionType): boolean {
  switch (type) {
    case "APPROVE":         return status === "Ready" || status === "Review required";
    case "REQUEST_CHANGES": return status === "Ready" || status === "Review required" || status === "Blocked";
    case "REJECT":          return status !== "Approved" && status !== "Rejected";
  }
}
```

### 6.2. Khi nào ghi chú là BẮT BUỘC

| Hành động | Ghi chú | Lý do |
| :--- | :--- | :--- |
| Approve đơn `Ready` | tuỳ chọn | Không có vi phạm nào để giải trình. |
| Approve đơn `Review required` | **bắt buộc**, ≥ 10 ký tự | Đây là "exceptional approval" — duyệt đè lên cảnh báo, phải ghi lý do vào audit log. |
| Request Changes | **bắt buộc**, ≥ 10 ký tự | Nội dung này gửi cho khách hàng. |
| Reject | **bắt buộc**, ≥ 10 ký tự | Quyết định không đảo ngược được. |

### 6.3. Chuyển trạng thái sau quyết định

```
APPROVE          → Approved
REQUEST_CHANGES  → Changes requested
REJECT           → Rejected
```

Mỗi quyết định **thêm** một bản ghi vào đầu `order.decisions` — không ghi đè bản ghi cũ.

---

## 7. BA QUYẾT ĐỊNH ĐÃ CHỐT

> Ba điểm dưới đây trước đây là câu hỏi mở. Đã được chốt ngày 2026-08-31. FE code theo đây.

### 7.1. ✅ Tiền tệ: ĐA TIỀN TỆ (multi-currency)

**Quyết định:** giữ field `currency` trên từng đơn, format theo đúng field đó.

Xung đột gốc:

| Nguồn | Giá trị |
| :--- | :--- |
| `models.py:27` | `currency: str = "VND"` |
| Prototype `dev` | toàn bộ seed dùng `"USD"`, `money()` hardcode `currency: "USD"` |
| Issue #3 | "Định dạng tiền tệ VND / USD" (cả hai) |

**Lý do chọn đa tiền tệ:** field `currency` đã tồn tại sẵn trong **cả hai** model (backend
`models.py:27` và prototype). Không phải thêm gì mới — chỉ là dùng cho đúng thay vì bỏ qua nó.
Đây cũng là cách duy nhất thoả mãn issue #3 ("VND / USD").

Đã implement trong `derive.ts`:

```ts
export const money = (value: number, currency: string) =>
  new Intl.NumberFormat(currency === "VND" ? "vi-VN" : "en-US",
    { style: "currency", currency, maximumFractionDigits: 0 }).format(value);
```

**Hệ quả cho FE:**
- ❌ Không dùng `money(value)` một tham số. Hàm cũ trong prototype hardcode USD — phải bỏ.
- ❌ Không hardcode ký hiệu `$` ở bất kỳ đâu. Prototype đang có `${line.unitPrice.toFixed(2)}` trong bảng line items và `catalog[].price: "$466.00"` — cả hai phải sửa.
- ✅ Luôn truyền `order.currency`: `money(o.value, o.currency)`.
- ✅ Với `LineItem`, tiền tệ **kế thừa từ đơn cha** — `LineItem` không có field `currency` riêng, vì một PO không thể trộn nhiều loại tiền.
- ✅ Seed nên có **ít nhất 1 đơn VND** để lộ ngay lỗi hardcode USD.

**`maximumFractionDigits: 0`** là cố ý: VND không dùng số lẻ, và với USD thì đơn PO thường
là số tròn nghìn — số lẻ chỉ làm bảng khó đọc. Chênh lệch giá vẫn hiển thị chính xác qua
`evidence` của finding.

### 7.2. ✅ `EXTRACTION_REVIEW`: BỎ khỏi bản demo

**Quyết định:** không đưa `Extraction review` vào `OrderStatus`. Enum giữ đúng **6** giá trị.

Kèm theo: **xoá `PROCESSING` và `EXTRACTION_REVIEW` khỏi `docs/ui-specification.md`** để hai
tài liệu hết mâu thuẫn. Đã làm trong cùng PR này.

**⚠️ Đây là nợ kỹ thuật có chủ đích, không phải thiếu sót.**

Rủi ro được chấp nhận: bóc tách PDF/ảnh có thể sai. Nếu OCR đọc `quantity: 60` thành `600`,
hệ thống sẽ chạy rules trên số rác rồi kết luận "Insufficient stock" một cách rất tự tin.
Người duyệt không có bước nào để phát hiện.

**Điều kiện để chấp nhận rủi ro này:**
- Chỉ áp dụng cho **bản demo/prototype**, nơi dữ liệu là seed tĩnh chứ không phải OCR thật.
- Modal upload **phải** giữ dòng cảnh báo đang có trong prototype:
  *"Preflight will extract the order and run company validation rules. You will review the
  result before any approval."*
- Trước khi nối OCR thật vào, **phải** mở lại quyết định này.

Đã ghi vào backlog: xem issue "Tech debt: khôi phục bước Extraction Review trước khi nối OCR thật".

**Lưu ý `architecture.md`:** state machine ở `docs/architecture.md:133-144` vẫn mô tả
`PROCESSING → EXTRACTION_REVIEW`. File đó mô tả **kiến trúc đích của hệ thống hoàn chỉnh**,
không phải phạm vi demo — nên giữ nguyên, không sửa. Contract này chỉ chi phối phạm vi FE demo.

### 7.3. ✅ `PROCESSING`: giữ trong component state

**Quyết định:** không thêm vào `OrderStatus`.

Với demo dùng `setTimeout` giả lập animation bóc tách, trạng thái "đang xử lý" chỉ tồn tại
trong vòng đời của `UploadModal`. Nó không phải trạng thái nghiệp vụ của đơn hàng — không ai
lọc queue theo nó, không ai ra quyết định trên nó.

```tsx
type UploadPhase = "idle" | "extracting" | "validating" | "done";
const [phase, setPhase] = useState<UploadPhase>("idle");
```

Đơn chỉ xuất hiện trong `orders[]` **sau khi** `phase === "done"`, và khi đó nó đã có
`status` dẫn xuất từ `deriveStatus(findings)`.

---

## 8. MAP ĐƯỜNG DẪN — Issue nói gì → Thực tế làm ở đâu

Cấu trúc đề xuất, tách dần khỏi file 333 dòng hiện tại:

| Issue nói | Không tồn tại trên `dev` | Đường dẫn thực tế nên dùng |
| :--- | :--- | :--- |
| `src/data/seed.ts`, `src/data/orders.ts` | ✗ | `apps/web/app/lib/types.ts` + `apps/web/app/lib/seed.ts` |
| `src/pages/Orders.tsx` | ✗ | `apps/web/app/components/OrdersQueue.tsx` |
| `src/pages/Dashboard.tsx` | ✗ | `apps/web/app/components/Overview.tsx` |
| `src/pages/Products.tsx` | ✗ | `apps/web/app/components/CatalogView.tsx` |
| `OrderDetail.tsx` | ✗ | `apps/web/app/components/OrderDetail.tsx` |
| `components/UploadModal.tsx` | ✗ | `apps/web/app/components/UploadModal.tsx` |
| `DataTable`, `Kpi`, `Seg`, `Panel` | ✗ | Phải tự viết, hoặc dùng bảng Tailwind thuần |
| `WorldMap`, `EChart` (ECharts) | ✗ | Xem Mục 9 |

Ba hàm dẫn xuất `deriveStatus`, `lineTotal`, `orderValue` và các helper format nên nằm ở
`apps/web/app/lib/derive.ts` để cả bốn issue dùng chung.

---

## 9. WORLDMAP VÀ ECHARTS — cần cắt phạm vi

Đặc tả 10 màn hình (Mục 3, màn 1) yêu cầu **WorldMap phân bổ đơn theo khu vực/chi nhánh**.

**Vấn đề:** không model nào có trường địa lý. `models.py:Order` chỉ có `po_number`,
`customer`, `items`, `currency`. Prototype cũng không có. Thêm WorldMap nghĩa là **thêm field
mới vào cả backend lẫn frontend** — đó là việc của backend, không phải FE-4.

Ngoài ra `dev` **không cài ECharts** (kiểm `package.json`: chỉ có next, react, react-dom).

Khuyến nghị cho FE-4:
- **Bỏ WorldMap** khỏi phạm vi. Nó là di sản của template e-commerce cũ, không phục vụ nghiệp vụ duyệt PO.
- **Thay biểu đồ ECharts bằng thống kê có dữ liệu thật:** đếm findings theo `code`. Dữ liệu này đã có sẵn, và trả lời đúng câu hỏi vận hành *"loại vi phạm nào đang xảy ra nhiều nhất?"*

```ts
export function findingsByCode(orders: PurchaseOrder[]): Record<FindingCode, number> {
  const acc = { PRICE_MISMATCH: 0, INSUFFICIENT_STOCK: 0,
                UNKNOWN_SKU: 0, INACTIVE_SKU: 0, DUPLICATE_PO: 0 };
  for (const o of orders) for (const f of o.findings) acc[f.code]++;
  return acc;
}
```

Một dãy thanh ngang bằng `div` + Tailwind là đủ, không cần thêm thư viện biểu đồ.

---

## 10. KPI Dashboard (FE-4) — công thức chính xác

```ts
export const needsAttention = (o: PurchaseOrder[]) =>
  o.filter((x) => x.status === "Review required" || x.status === "Blocked").length;

export const readyForApproval = (o: PurchaseOrder[]) =>
  o.filter((x) => x.status === "Ready").length;

export const approvedToday = (o: PurchaseOrder[], now = new Date()) =>
  o.filter((x) => x.decisions.some(
    (d) => d.type === "APPROVE" && isSameDay(new Date(d.createdAt), now))).length;
```

### 10.1. ⚠️ `Avg decision time` cần dữ liệu chưa có

KPI này = trung bình `decision.createdAt − order.submittedAt` trên các đơn đã quyết định.

Tính được **chỉ khi** `submittedAt` là ISO (Mục 4.1) và `decisions[]` có `createdAt`. Nếu
FE-1 giữ nguyên chuỗi `"Today, 10:42 AM"` thì **KPI này không thể tính** và sẽ phải hardcode
— tức là một con số giả trên dashboard.

```ts
export function avgDecisionTimeMinutes(orders: PurchaseOrder[]): number | null {
  const spans = orders.flatMap((o) => {
    const d = o.decisions.at(-1);           // quyết định đầu tiên theo thời gian
    return d ? [(+new Date(d.createdAt) - +new Date(o.submittedAt)) / 60_000] : [];
  });
  return spans.length ? spans.reduce((a, b) => a + b, 0) / spans.length : null;
}
```

Trả `null` khi chưa có quyết định nào → UI hiển thị `—`, **không hiển thị `0m`**.

---

## 11. Bộ lọc Orders Queue (FE-2)

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

### 11.1. ⚠️ Bốn tab không phủ hết sáu trạng thái

`Changes requested` và `Rejected` **không xuất hiện ở bất kỳ tab nào ngoài `All`**. Đơn bị
từ chối sẽ biến mất khỏi mọi tab lọc — người dùng không có cách nào lọc ra chúng.

Ba lựa chọn: thêm tab `Closed` (gộp 2 trạng thái này); hoặc thêm 2 tab riêng; hoặc chấp nhận
chỉ tìm thấy chúng ở `All`. **Khuyến nghị: thêm tab `Closed`.**

### 11.2. Search

Tìm theo **mã PO** và **tên khách hàng**, không phân biệt hoa thường:

```ts
export function searchOrders(orders: PurchaseOrder[], q: string): PurchaseOrder[] {
  const s = q.trim().toLowerCase();
  if (!s) return orders;
  return orders.filter((o) =>
    o.id.toLowerCase().includes(s) || o.customer.toLowerCase().includes(s));
}
```

**Đừng** dùng `JSON.stringify(o).includes(...)` như code cũ — cách đó sẽ khớp nhầm vào tên
file, ghi chú, tên người phụ trách, và cả nội dung finding.

---

## 12. Seed data — bốn ca bắt buộc phải có

Tiêu chí hoàn thành của FE-1 yêu cầu seed phủ hết các ca. Tối thiểu:

| PO | Status | Currency | Findings | Ca kiểm thử |
| :--- | :--- | :--- | :--- | :--- |
| `PO-10421` | `Ready` | USD | — | Khớp 100%: giá đúng, đủ kho |
| `PO-10428` | `Review required` | USD | `PRICE_MISMATCH` + `INSUFFICIENT_STOCK` | Hai cảnh báo cùng lúc |
| `PO-10431` | `Blocked` | USD | `UNKNOWN_SKU` | SKU không tồn tại |
| `PO-10433` | `Blocked` | **VND** | `INACTIVE_SKU` | SKU ngừng bán **+ ca đa tiền tệ** |
| `PO-10428-B` | `Blocked` | USD | `DUPLICATE_PO` | Trùng mã với đơn đã xử lý |
| `PO-10417` | `Approved` | USD | — | Đã duyệt, có `decisions[]` |
| `PO-10402` | `Changes requested` | **VND** | `PRICE_MISMATCH` | Đã yêu cầu sửa **+ ca đa tiền tệ** |
| `PO-10399` | `Rejected` | USD | `UNKNOWN_SKU` | Đã từ chối |

**Bắt buộc có ít nhất 2 đơn VND.** Nếu seed toàn USD, mọi chỗ hardcode `$` sẽ trông vẫn
đúng và lỗi chỉ lộ ra ở production. Hai đơn VND ở trên tồn tại để phá vỡ điều đó ngay tại
màn hình đầu tiên.

Ba bất biến mà seed phải thoả (nên viết thành test):

```ts
orders.every((o) => o.value === orderValue(o));
orders.every((o) => o.findings.every((f) => f.severity === SEVERITY_BY_CODE[f.code]));
orders.filter((o) => !["Approved","Changes requested","Rejected"].includes(o.status))
      .every((o) => o.status === deriveStatus(o.findings));
new Set(orders.map((o) => o.currency)).size >= 2;  // §7.1: phải có ít nhất 2 loại tiền
```

---

## 13. Thứ tự triển khai

FE-1 **chặn cứng** cả ba issue còn lại — không thể làm song song:

```
FE-1 (#2) types + seed
   ├──→ FE-2 (#3) Orders Queue
   ├──→ FE-3 (#4) Order Detail   ← nặng nhất, làm sau FE-2
   └──→ FE-4 (#5) Dashboard + Upload
```

FE-4 phụ thuộc FE-2 (upload phải chèn được đơn mới vào queue), nên làm cuối.
