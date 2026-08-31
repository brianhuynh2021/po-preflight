# TÀI LIỆU ĐẶC TẢ NGHIỆP VỤ FRONTEND & DANH SÁCH TICKET TRIỂN KHAI TOÀN DIỆN (PO PREFLIGHT)

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

| Mã lỗi (`code`) | Mức độ (`severity`) | Tiêu đề lỗi hiển thị | Ý nghĩa & Bằng chứng cần hiển thị |
| :--- | :--- | :--- | :--- |
| `PRICE_MISMATCH` | `Warning` | Chênh lệch giá so với Catalog | Hiển thị: *Giá trên PO (vd: 17.6tr) vs Giá Catalog (vd: 18.5tr) - Lệch 4.86%*. |
| `INSUFFICIENT_STOCK` | `Warning` | Không đủ tồn kho đáp ứng | Hiển thị: *Khách đặt: 15 cái · Tồn kho hiện có: 8 cái · Thiếu: 7 cái*. |
| `UNKNOWN_SKU` | `Error` | Mã SKU không tồn tại | Hiển thị: *Mã hàng `DSK-404` không có trong danh mục sản phẩm của công ty*. |
| `INACTIVE_SKU` | `Error` | Sản phẩm đã ngừng kinh doanh | Hiển thị: *Mã hàng `STG-410` đã bị vô hiệu hóa, không nhận đơn mới*. |
| `DUPLICATE_PO` | `Error` | Trùng lặp mã đơn hàng | Hiển thị: *Mã PO `PO-10428` đã từng được xử lý cho khách hàng này trước đó*. |

---

## 3. ĐẶC TẢ CHI TIẾT 10 MÀN HÌNH CỦA HỆ THỐNG HOÀN CHỈNH

### 🖥️ Màn hình 1: Dashboard (Bảng điều khiển Tổng quan Preflight)
* **Vị trí:** `apps/web/src/pages/Dashboard.tsx`
* **KPIs:** *Needs Attention, Ready for Approval, Approved Today, Avg Decision Time*.
* **Charts (ECharts):** Thống kê phân loại vi phạm và lưu lượng đơn theo thời gian.
* **WorldMap:** Phân bổ đơn hàng theo khu vực địa lý / chi nhánh.

### 🖥️ Màn hình 2: Hàng đợi Đơn hàng (Orders Queue Page)
* **Vị trí:** `apps/web/src/pages/Orders.tsx`
* **Bảng DataTable:** Mã PO, Khách hàng, File gốc, Tổng tiền, Badge số lỗi Findings, Trạng thái rủi ro, Thao tác.
* **Bộ lọc:** Search PO/Khách hàng + Tabs: `All`, `Needs Attention`, `Ready`, `Approved`.

### 🖥️ Màn hình 3: Chi tiết Đơn hàng & Đối chiếu Vi phạm (Order Detail & Review)
* **Vị trí:** Drawer / Trang con `OrderDetail.tsx`
* **Nội dung:** Thông tin Header, Danh sách thẻ vi phạm Findings (có Evidence), Bảng Line Items so khớp giá và kho, Action Bar (**Approve**, **Request Changes**, **Reject**).

### 🖥️ Màn hình 4: Modal Upload Đơn hàng (Upload PO Modal)
* **Vị trí:** `apps/web/src/components/UploadModal.tsx`
* **Nội dung:** Kéo thả file PDF, Excel, Ảnh, JSON $\rightarrow$ Animation bóc tách $\rightarrow$ Thêm đơn mới vào đầu bảng.

### 🖥️ Màn hình 5: Danh mục Sản phẩm & Bảng giá (Catalog & Stock)
* **Vị trí:** `apps/web/src/pages/Products.tsx`
* **Nội dung:** Mã SKU, Tên sản phẩm, Giá niêm yết, Tồn kho khả dụng, Trạng thái Active/Inactive.

### 🖥️ Màn hình 6: Nhật ký Kiểm toán (Audit Trail Timeline)
* **Vị trí:** `apps/web/src/pages/Reports.tsx` hoặc `AuditLog.tsx`
* **Nội dung:** Dòng thời gian bất biến ghi nhận ai duyệt đơn nào, lúc mấy giờ, kèm ghi chú quyết định.

### 🖥️ Màn hình 7: So sánh Trực quan File Gốc (Side-by-side Document Viewer)
* **Vị trí:** `apps/web/src/components/DocumentSplitViewer.tsx`
* **Nội dung:** Chế độ xem chia đôi (Split-view): Nửa bên trái là Viewer hiển thị file PDF/Ảnh gốc, nửa bên phải là form dữ liệu AI bóc tách để đối chiếu trực quan.

### 🖥️ Màn hình 8: Cấu hình Luật Nghiệp vụ & Dung sai (Rules & Policy Engine Settings)
* **Vị trí:** `apps/web/src/pages/RulesConfig.tsx`
* **Nội dung:** Bật/tắt từng luật kiểm tra, chỉnh % dung sai giá cho phép, ngưỡng tự động duyệt đơn giá trị nhỏ, cửa sổ kiểm tra trùng mã đơn.

### 🖥️ Màn hình 9: Cài đặt Kết nối Đa kênh (Multi-Channel Integration Settings)
* **Vị trí:** `apps/web/src/pages/ChannelSettings.tsx`
* **Nội dung:** Cấu hình Token Telegram Bot, Zalo OA OpenAPI Key, Slack Webhook URL, WeChat Work, phân luồng gửi thông báo duyệt theo giá trị đơn.

### 🖥️ Màn hình 10: Quản lý Đồng bộ ERP & Xuất dữ liệu (ERP Sync & Export Center)
* **Vị trí:** `apps/web/src/pages/ErpSync.tsx`
* **Nội dung:** Bảng theo dõi trạng thái đồng bộ đơn sang ERP (Odoo, SAP, MISA), nút bấm Retry khi lỗi mạng, và công cụ xuất file Excel/CSV/JSON chuẩn ERP.

---

## 4. DANH SÁCH 8 TICKET GITHUB CHO FRONTEND TEAM (BACKLOG)

Dưới đây là 8 Ticket chi tiết từ giai đoạn Core MVP đến Enterprise:

---

### 🎫 [FE-1] Issue #2: Core Data Models & Seed Data for PO Preflight Domain
* **Mô tả:** Định nghĩa TypeScript types (`PurchaseOrder`, `LineItem`, `Finding`, `OrderStatus`) và cập nhật dữ liệu `seed.ts`.
* **Ưu tiên:** `Highest` | **Trạng thái:** `Đã tạo trên GitHub`

---

### 🎫 [FE-2] Issue #3: Rebuild Orders Queue with Risk Status & Findings Badges
* **Mô tả:** Tái cấu trúc bảng `Orders.tsx` thành Bảng hàng đợi duyệt đơn PO (Mã PO, Khách hàng, File gốc, Badge lỗi, Trạng thái rủi ro, Bộ lọc).
* **Ưu tiên:** `High` | **Trạng thái:** `Đã tạo trên GitHub`

---

### 🎫 [FE-3] Issue #4: Build Order Detail Review Screen & Decision Actions (Approve/Reject)
* **Mô tả:** Màn hình Chi tiết Đơn: danh sách thẻ lỗi Findings, bảng Line Items so khớp giá Catalog, Action Bar và Modal nhập lý do duyệt.
* **Ưu tiên:** `High` | **Trạng thái:** `Đã tạo trên GitHub`

---

### 🎫 [FE-4] Issue #5: Update Dashboard Preflight Metrics & Build Upload PO Modal
* **Mô tả:** Điều chỉnh KPI và biểu đồ ECharts trên Dashboard theo tiền kiểm; xây dựng Modal kéo thả Upload PO.
* **Ưu tiên:** `Medium` | **Trạng thái:** `Đã tạo trên GitHub`

---

### 🎫 [FE-5] Issue #6: Build Side-by-Side Document Viewer for Visual Evidence Matching
* **Mô tả:** Xây dựng chế độ xem chia đôi (Split-view) cho màn hình chi tiết đơn: nửa trái hiển thị PDF/Ảnh scan gốc, nửa phải hiển thị bảng bóc tách.
* **Ưu tiên:** `Medium` | **Trạng thái:** `Đang tạo trên GitHub`

---

### 🎫 [FE-6] Issue #7: Build Rules & Policy Engine Configuration Screen
* **Mô tả:** Xây dựng màn hình cài đặt quy tắc tiền kiểm: điều chỉnh % dung sai giá lệch, bật/tắt luật kiểm tra tồn kho, cài ngưỡng tự động duyệt đơn nhỏ.
* **Ưu tiên:** `Medium` | **Trạng thái:** `Đang tạo trên GitHub`

---

### 🎫 [FE-7] Issue #8: Build Multi-Channel Integration & Notification Settings (Telegram/Zalo/Slack)
* **Mô tả:** Xây dựng trang cài đặt kết nối Telegram Bot, Zalo OA, Slack Webhook và phân quyền nhận thông báo duyệt theo mức độ rủi ro.
* **Ưu tiên:** `Low` | **Trạng thái:** `Đang tạo trên GitHub`

---

### 🎫 [FE-8] Issue #9: Build ERP Synchronization Dashboard & Export Center
* **Mô tả:** Xây dựng màn hình theo dõi trạng thái đồng bộ đơn sang ERP (SAP/Odoo), nút Retry khi lỗi kết nối và nút xuất file Excel/CSV/JSON.
* **Ưu tiên:** `Low` | **Trạng thái:** `Đang tạo trên GitHub`
