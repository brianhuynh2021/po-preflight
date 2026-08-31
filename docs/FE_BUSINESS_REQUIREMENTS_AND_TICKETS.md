# TÀI LIỆU ĐẶC TẢ NGHIỆP VỤ FRONTEND & DANH SÁCH TICKET TRIỂN KHAI (PO PREFLIGHT)

> **Dành cho:** Đội ngũ phát triển Frontend (FE Team)  
> **Dự án:** PO Preflight (Hệ thống AI Tiền kiểm toán & Phê duyệt Đơn hàng B2B)  
> **Nền tảng UI hiện tại:** Vite + React 19 + TypeScript + Tailwind CSS (`apps/web`)

---

## 1. TỔNG QUAN BÀI TOÁN KINH DOANH CHO FRONTEND TEAM

### 1.1. Ứng dụng này KHÔNG PHẢI là gì?
- **Không phải** là sàn thương mại điện tử / E-commerce bán lẻ thông thường (không có giỏ hàng, không có trạng thái `Paid / Refunded` cho người tiêu dùng cá nhân).

### 1.2. Ứng dụng này LÀ GÌ?
- **PO Preflight** là hệ thống **Bảng điều khiển Tiền kiểm toán Đơn đặt hàng B2B (Order Operations & Preflight Gatekeeper)** dành cho nhân viên kinh doanh (Sales Admin) và Quản lý vận hành (Operations Manager) của các công ty sản xuất/phân phối.
- **Nhiệm vụ của ứng dụng:**
  1. Tiếp nhận file đơn đặt hàng (**Purchase Orders - PO**) gửi về từ khách hàng (PDF, Excel, Ảnh, JSON).
  2. Bóc tách dữ liệu và **tự động chạy các quy tắc kiểm tra (Validation Rules)** để phát hiện lỗi: *Sai giá so với bảng giá niêm yết, thiếu tồn kho, mã hàng lạ, đơn trùng lặp*.
  3. Cung cấp giao diện trực quan cho Quản lý **xem bằng chứng sai lệch và bấm nút Phê duyệt / Từ chối (Human-In-The-Loop)** trước khi đơn được đồng bộ vào phần mềm ERP (SAP / Odoo).

---

## 2. CÁC TRẠNG THÁI ĐƠN HÀNG & MÃ LỖI NGHIỆP VỤ (CORE DOMAIN)

### 2.1. Vòng đời Trạng thái Đơn hàng (Order Lifecycle Status)

```
[Mới tiếp nhận (File Upload)]
              │
              ▼
   [TỰ ĐỘNG CHẠY PREFLIGHT RULES]
              │
    ┌─────────┼─────────────────────────┐
    │ (Không có lỗi)                    │ (Có cảnh báo nhẹ)       │ (Có lỗi nghiêm trọng)
    ▼                                   ▼                         ▼
🟢 READY_FOR_APPROVAL               🟡 REVIEW_REQUIRED         🔴 BLOCKED
(Sẵn sàng duyệt)                    (Cần người xem xét)        (Bị chặn, bắt buộc sửa)
    │                                   │                         │
    └─────────────────┬─────────────────┘                         │
                      ▼                                           ▼
             [QUẢN LÝ PHÊ DUYỆT]                         [YÊU CẦU ĐIỀU CHỈNH]
                      │                                           │
         ┌────────────┴────────────┐                              ▼
         ▼                         ▼                     🟠 CHANGES_REQUESTED
    🔵 APPROVED               ❌ REJECTED                (Gửi thông báo cho khách)
  (Ghi nhận vào ERP)       (Hủy đơn hàng)
```

| Mã trạng thái (`status`) | Nhãn hiển thị | Màu sắc Tone | Ý nghĩa nghiệp vụ |
| :--- | :--- | :--- | :--- |
| `READY` | Ready for approval | 🟢 Green (`#19704c`) | Đơn hàng hoàn toàn hợp lệ, khớp giá 100%, đủ tồn kho. |
| `REVIEW_REQUIRED` | Review required | 🟡 Amber (`#a76418`) | Có cảnh báo thương mại: Chênh lệch giá nhẹ hoặc tồn kho không đủ. |
| `BLOCKED` | Blocked | 🔴 Red (`#a5453c`) | Bị chặn do lỗi nghiêm trọng: SKU không tồn tại, SKU đã ngừng bán hoặc trùng mã đơn. |
| `APPROVED` | Approved | 🔵 Blue (`#386b8e`) | Quản lý đã bấm nút duyệt chính thức, ghi nhận vào Audit Log. |
| `CHANGES_REQUESTED` | Changes requested | 🟠 Orange | Quản lý yêu cầu gửi thông báo cho khách điều chỉnh lại file đơn. |
| `REJECTED` | Rejected | ⚫ Gray/Dark Red | Đơn hàng bị từ chối dứt điểm. |

---

### 2.2. Danh mục 5 Mã lỗi Vi phạm (Validation Finding Codes)

FE cần hiển thị các thẻ lỗi (Issue Card) dựa trên các mã lỗi trả về từ hệ thống:

| Mã lỗi (`code`) | Mức độ (`severity`) | Tiêu đề lỗi hiển thị | Ý nghĩa & Bằng chứng cần hiển thị |
| :--- | :--- | :--- | :--- |
| `PRICE_MISMATCH` | `Warning` | Chênh lệch giá so với Catalog | Hiển thị: *Giá trên PO (vd: 17.6tr) vs Giá Catalog (vd: 18.5tr) - Lệch 4.86%*. |
| `INSUFFICIENT_STOCK` | `Warning` | Không đủ tồn kho đáp ứng | Hiển thị: *Khách đặt: 15 cái · Tồn kho hiện có: 8 cái · Thiếu: 7 cái*. |
| `UNKNOWN_SKU` | `Error` | Mã SKU không tồn tại | Hiển thị: *Mã hàng `DSK-404` không có trong danh mục sản phẩm của công ty*. |
| `INACTIVE_SKU` | `Error` | Sản phẩm đã ngừng kinh doanh | Hiển thị: *Mã hàng `STG-410` đã bị vô hiệu hóa, không nhận đơn mới*. |
| `DUPLICATE_PO` | `Error` | Trùng lặp mã đơn hàng | Hiển thị: *Mã PO `PO-10428` đã từng được xử lý cho khách hàng này trước đó*. |

---

## 3. ĐẶC TẢ CHI TIẾT TỪNG MÀN HÌNH (SCREEN SPECIFICATIONS)

### 🖥️ Màn hình 1: Dashboard (Bảng điều khiển Tổng quan Preflight)
* **Vị trí file:** `apps/web/src/pages/Dashboard.tsx`
* **Nhiệm vụ:** Hiển thị bức tranh toàn cảnh về tình hình xử lý đơn PO trong ngày/tháng.
* **Các thành phần cần có:**
  1. **Hàng chỉ số KPI (KPI Cards):**
     - *Cần xử lý (Needs Attention):* Tổng số đơn `Review required` + `Blocked`.
     - *Sẵn sàng duyệt (Ready for Approval):* Số đơn `Ready`.
     - *Đã duyệt hôm nay (Approved Today):* Số đơn `Approved`.
     - *Thời gian duyệt trung bình (Avg Decision Time):* ví dụ: `5.8 phút`.
  2. **Biểu đồ ECharts:**
     - Biểu đồ phân bổ loại lỗi vi phạm (Price Mismatch, Stock Shortfall, Unknown SKU).
     - Biểu đồ xu hướng xử lý đơn hàng theo tuần/tháng.
  3. **Bản đồ WorldMap / Regional Map:** Hiển thị khối lượng đơn hàng phân bổ theo khu vực địa lý / chi nhánh khách hàng.
  4. **Nút tác vụ nhanh:** `Upload Purchase Order` (mở modal tải file).

---

### 🖥️ Màn hình 2: Danh sách Đơn hàng (Orders Queue Page)
* **Vị trí file:** `apps/web/src/pages/Orders.tsx`
* **Nhiệm vụ:** Hàng đợi đơn hàng giúp Sales Admin tìm kiếm, lọc và chọn đơn để duyệt.
* **Cột của Bảng DataTable:**
  1. **Mã PO (`id`):** vd `PO-10428` (click vào để mở Drawer / Chi tiết đơn).
  2. **Khách hàng (`customer`):** Tên công ty đặt hàng + Avatar chữ cái đầu.
  3. **File gốc (`source_file`):** vd `northstar-order.pdf` (có icon PDF/Excel).
  4. **Tổng giá trị (`value`):** Định dạng tiền tệ VND / USD.
  5. **Số lỗi vi phạm (`findings`):** Badge số lượng (vd: `2 findings` màu vàng/đỏ).
  6. **Trạng thái (`status`):** Badge màu chuẩn `Ready / Review required / Blocked / Approved`.
  7. **Người phụ trách (`owner`):** Tên nhân viên xử lý.
* **Bộ lọc (Filter Toolbar):**
  - Search Input: Tìm theo Mã PO hoặc Tên khách hàng.
  - Segment Tabs: `All`, `Needs Attention` (gồm Review+Blocked), `Ready`, `Approved`.

---

### 🖥️ Màn hình 3: Chi tiết Đơn hàng & Đối chiếu Vi phạm (Order Detail & Review)
* **Vị trí:** Drawer trượt từ bên phải hoặc Trang con `OrderDetail.tsx`.
* **Nhiệm vụ:** Màn hình quan trọng nhất giúp Quản lý đối chiếu bằng chứng và ra quyết định.
* **Giao diện chia làm 3 phần:**
  1. **Header:** Mã PO, Tên khách hàng, Ngày gửi, Trạng thái hiện tại.
  2. **Danh sách Cảnh báo Vi phạm (Validation Findings Panel):**
     - Render từng thẻ Finding với màu sắc tương ứng (Vàng cho Warning, Đỏ cho Error).
     - Hiển thị rõ: *Tiêu đề lỗi*, *Mô tả chi tiết*, *Bằng chứng đối chiếu (Evidence)*.
  3. **Bảng chi tiết từng dòng hàng (Line Items Table):**
     - Cột: `SKU`, `Tên sản phẩm`, `Số lượng đặt`, `Tồn kho khả dụng`, `Đơn giá trên PO`, `Đơn giá Catalog`, `Thành tiền`.
     - Highlight màu đỏ/vàng ở các ô bị lệch giá hoặc thiếu kho.
  4. **Thanh hành động Quyết định (Decision Action Bar):**
     - Nút 🔵 **[Phê duyệt đơn (Approve Order)]**: Mở Modal nhập ghi chú xác nhận $\rightarrow$ Chuyển trạng thái sang `Approved`.
     - Nút 🟠 **[Yêu cầu điều chỉnh (Request Changes)]**: Mở Modal nhập lý do gửi lại cho khách $\rightarrow$ Chuyển sang `Changes Requested`.
     - Nút ❌ **[Từ chối đơn (Reject)]**: Chuyển sang `Rejected`.

---

### 🖥️ Màn hình 4: Modal Upload Đơn hàng (Upload PO Modal)
* **Vị trí component:** `apps/web/src/components/UploadModal.tsx`
* **Nhiệm vụ:** Cho phép người dùng kéo thả file PO (PDF, Excel, Ảnh, JSON) vào hệ thống.
* **Trạng thái tương tác:**
  - Kéo thả file $\rightarrow$ Hiển thị thanh tiến trình bóc tách:
    `Đang đọc tài liệu...` $\rightarrow$ `Kiểm tra quy tắc Catalog & Tồn kho...` $\rightarrow$ `Hoàn tất! Tìm thấy 2 cảnh báo`.
  - Tự động thêm đơn mới vào đầu danh sách Orders.

---

### 🖥️ Màn hình 5: Danh mục Sản phẩm & Tồn kho (Products / Catalog Page)
* **Vị trí file:** `apps/web/src/pages/Products.tsx`
* **Nhiệm vụ:** Hiển thị danh mục sản phẩm dùng để đối soát.
* **Cột:** `Mã SKU`, `Tên sản phẩm`, `Giá niêm yết (Catalog Price)`, `Số lượng tồn kho (Available Stock)`, `Trạng thái (Active / Inactive)`.

---

### 🖥️ Màn hình 6: Nhật ký Kiểm toán (Audit Log Timeline)
* **Vị trí file:** `apps/web/src/pages/Reports.tsx` hoặc `AuditLog.tsx`
* **Nhiệm vụ:** Hiển thị lịch sử minh bạch: Ai đã duyệt đơn nào, lúc mấy giờ, lý do ghi chú là gì.

---

## 4. DANH SÁCH TICKET CÔNG VIỆC CHO FRONTEND (BACKLOG TICKETS)

Dưới đây là danh sách Ticket được chia nhỏ, chuẩn định dạng để bạn copy tạo trên Jira / Trello / GitHub Issues:

---

### 🎫 TICKET FE-01: Cập nhật Data Models & Types chuẩn nghiệp vụ PO Preflight
* **Loại:** `Task` | **Độ ưu tiên:** `Highest`
* **Mô tả:** Cập nhật lại các Interface/Type trong `apps/web/src/data/` để đúng với thực thể PO Preflight.
* **Chi tiết công việc:**
  - Định nghĩa Type:
    ```typescript
    export type OrderStatus = 'Ready' | 'Review required' | 'Blocked' | 'Approved' | 'Changes requested' | 'Rejected';
    export type FindingSeverity = 'Warning' | 'Error';
    export interface Finding {
      code: 'PRICE_MISMATCH' | 'INSUFFICIENT_STOCK' | 'UNKNOWN_SKU' | 'INACTIVE_SKU' | 'DUPLICATE_PO';
      severity: FindingSeverity;
      title: string;
      detail: string;
      evidence: string;
      sku?: string;
    }
    export interface LineItem {
      sku: string;
      product: string;
      quantity: number;
      available: number;
      unitPrice: number;
      catalogPrice: number;
    }
    export interface PurchaseOrder {
      id: string;
      customer: string;
      submitted: string;
      source_file: string;
      value: number;
      currency: string;
      status: OrderStatus;
      findings: Finding[];
      lines: LineItem[];
      owner: string;
    }
    ```
  - Cập nhật dữ liệu mẫu `seed.ts` theo đúng cấu trúc trên.

---

### 🎫 TICKET FE-02: Chuyển đổi trang `Orders.tsx` thành PO Approval Queue
* **Loại:** `Feature` | **Độ ưu tiên:** `High`
* **Mô tả:** Tái cấu trúc bảng `OrdersPage` để hiển thị hàng đợi đơn PO cần duyệt thay vì đơn hàng e-commerce bán lẻ.
* **Chi tiết công việc:**
  - Đổi các cột: `Mã PO`, `Khách hàng`, `Nguồn file`, `Tổng tiền`, `Số lỗi vi phạm (Findings badge)`, `Trạng thái rủi ro`, `Thao tác`.
  - Thêm bộ lọc trạng thái: Tab `All`, `Needs Attention`, `Ready`, `Approved`.
  - Click vào dòng sẽ mở Drawer / Modal xem chi tiết đơn PO.

---

### 🎫 TICKET FE-03: Xây dựng Component Chi tiết Đơn hàng & Đối chiếu Vi phạm (Order Review Drawer)
* **Loại:** `Feature` | **Độ ưu tiên:** `High`
* **Mô tả:** Tạo component xem chi tiết đơn PO, hiển thị danh sách thẻ vi phạm Findings và bảng đối chiếu line items.
* **Chi tiết công việc:**
  - Tạo Panel hiển thị các thẻ Finding (màu Amber cho Warning, Red cho Error kèm dòng Evidence).
  - Tạo bảng Line Items highlight các ô sai giá và thiếu kho.
  - Thêm nút thao tác: **Approve**, **Request Changes**, **Reject**.

---

### 🎫 TICKET FE-04: Xây dựng Modal Phê duyệt & Ghi nhận Quyết định (Decision Modal)
* **Loại:** `Feature` | **Độ ưu tiên:** `High`
* **Mô tả:** Khi bấm nút Approve hoặc Request Changes, hiển thị modal cho phép Quản lý nhập ghi chú quyết định (`decision_note`).
* **Chi tiết công việc:**
  - Form gồm: Textarea nhập lý do phê duyệt / yêu cầu điều chỉnh.
  - Khi submit: Cập nhật trạng thái đơn sang `Approved` hoặc `Changes requested`, thêm một bản ghi vào dòng thời gian Audit Trail.
  - Hiển thị Toast thông báo thành công.

---

### 🎫 TICKET FE-05: Xây dựng Modal Upload File PO (Kéo thả & Bóc tách)
* **Loại:** `Feature` | **Độ ưu tiên:** `Medium`
* **Mô tả:** Tạo nút `Upload purchase order` ở Topbar/Header để mở modal kéo thả file.
* **Chi tiết công việc:**
  - Hỗ trợ kéo thả các file `.pdf`, `.csv`, `.json`, `.xlsx`, `.png`, `.jpg`.
  - Hiển thị hiệu ứng loading phân tích trong 1.5 giây $\rightarrow$ Tạo một đơn mới đưa vào hàng đợi `Orders`.

---

### 🎫 TICKET FE-06: Điều chỉnh trang `Dashboard.tsx` theo số liệu Tiền kiểm
* **Loại:** `Improvement` | **Độ ưu tiên:** `Medium`
* **Mô tả:** Cập nhật các thẻ KPI và biểu đồ ECharts trên Dashboard phản ánh đúng số liệu tiền kiểm toán.
* **Chi tiết công việc:**
  - KPI 1: `Needs attention` (Đơn có lỗi cần xử lý).
  - KPI 2: `Ready for approval` (Đơn chuẩn sạch sẵn sàng duyệt).
  - KPI 3: `Approved today` (Đơn đã duyệt trong ngày).
  - KPI 4: `Avg decision time` (Thời gian xử lý trung bình).
  - Đổi biểu đồ tròn/cột thành thống kê tỷ lệ vi phạm theo mã lỗi (`Price Mismatch`, `Insufficient Stock`, `Unknown SKU`).

---

### 🎫 TICKET FE-07: Cập nhật trang `Products.tsx` (Catalog) và `Reports.tsx` (Audit Trail)
* **Loại:** `Improvement` | **Độ ưu tiên:** `Low`
* **Mô tả:** Đảm bảo trang Catalog hiển thị đúng danh mục sản phẩm đối soát và trang Audit Trail hiển thị lịch sử phê duyệt minh bạch.
