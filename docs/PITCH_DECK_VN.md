# 📊 PO PREFLIGHT — EXECUTIVE PITCH DECK & BẢN THUYẾT TRÌNH DỰ ÁN
> **Giải Pháp Cổng Kiểm Soát An Toàn Tự Động Cho Đơn Đặt Hàng B2B Trước Khi Đẩy Vào ERP**  
> *Dành Cho Ban Lãnh Đạo, Kế Toán Trưởng & Giám Đốc Vận Hành Doanh Nghiệp Phân Phối*

---

```
═══════════════════════════════════════════════════════════════════════════════
                           MỤC LỤC BẢN THUYẾT TRÌNH (10 SLIDES)
═══════════════════════════════════════════════════════════════════════════════
  [SLIDE 1] TỔNG QUAN & TUYÊN NGÔN SỨ MỆNH (THE HOOK)
  [SLIDE 2] VẤN ĐỀ THỰC TẾ & CHI PHÍ ẨN DOANH NGHIỆP (THE PROBLEM & HIDDEN COSTS)
  [SLIDE 3] GIẢI PHÁP: CỔNG TIỀN KIỂM TỰ ĐỘNG PO PREFLIGHT (THE SOLUTION)
  [SLIDE 4] ĐỘT PHÁ CÔNG NGHỆ: 4-TIER RAG & BẢO ĐẢM SỐ HỌC (CORE TECH)
  [SLIDE 5] QUY TRÌNH VẬN HÀNH THỰC TẾ 6 CHẶNG (LIVE PRODUCT WORKFLOW)
  [SLIDE 6] PHƯƠNG PHÁP ĐO LƯỜNG & KẾT QUẢ ĐO KIỂM PILOT (MEASUREMENT & PILOT DATA)
  [SLIDE 7] TUÂN THỦ NGHỊ ĐỊNH 13, ON-PREMISE & CHUỖI BĂM SHA-256 (SECURITY & AUDIT)
  [SLIDE 8] CHÂN DUNG KHÁCH HÀNG & HỆ SINH THÁI ERP (ICP & ERP ECOSYSTEM)
  [SLIDE 9] LỢI THẾ CẠNH TRANH ĐỘC BẢN (MOAT & COMPETITIVE ADVANTAGE)
  [SLIDE 10] LỘ TRÌNH TRIỂN KHAI & KẾ HOẠCH PILOT 30 NGÀY (PILOT PLAYBOOK & NEXT STEPS)
═══════════════════════════════════════════════════════════════════════════════
```

---

## 🎯 SLIDE 1: TỔNG QUAN DỰ ÁN (THE HOOK)

### 📌 Tựa đề: **PO PREFLIGHT — Cổng Kiểm Soát & Đối Soát Đơn Hàng B2B Tự Động**

* **Khẩu hiệu (Tagline)**: *"Không bao giờ để một đơn hàng sai giá hợp đồng, hết tồn kho hoặc nợ quá hạn lọt vào hệ thống ERP."*
* **Tuyên ngôn giá trị (Value Proposition)**:
  Cổng tiền kiểm thông minh giúp doanh nghiệp B2B và nhà phân phối tự động hóa khâu tiếp nhận, bóc tách đơn hàng (PDF, Excel, ảnh chụp scan), đối soát toàn diện với bảng giá hợp đồng, tồn kho ATP, hạn mức công nợ và kích hoạt duyệt 1 chạm trên Telegram/Zalo trước khi đồng bộ sang ERP (MISA AMIS, Bravo, Fast, Odoo, SAP B1).
* **Đơn vị phát triển**: Nhật Minh Technology.

> 🎙️ **Speaker Notes**: *"Kính thưa quý vị, trong ngành hàng không, không một chiếc máy bay nào được cất cánh nếu chưa hoàn tất quy trình Pre-flight Check. Trong doanh nghiệp phân phối B2B, hàng trăm đơn đặt hàng mỗi ngày với trị giá hàng trăm triệu đồng đang được nhân viên nhập tay vào phần mềm kế toán mà không qua bất kỳ màng lọc tự động nào. PO Preflight chính là người gác cổng tin cậy đó."*

---

## 🚨 SLIDE 2: NỖI ĐAU THỊ TRƯỜNG & CHI PHÍ ẨN (THE PROBLEM)

### 3 "Lỗ Hổng" Chí Mạng Trong Xử Lý Đơn Hàng B2B:

```
  ┌───────────────────────────┐      ┌───────────────────────────┐      ┌───────────────────────────┐
  │   1. Nhập Tay Chậm Chạp   │      │    2. Sai Mã & Lệch Giá   │      │   3. Thất Thoát Tồn Kho   │
  │                           │      │                           │      │                           │
  │ • Mất 15-30 phút/đơn      │      │ • Khách dùng tên gọi lóng │      │ • Duyệt khi kho đã hết hàng│
  │ • Sales Admin quá tải     │      │ • Áp sai giá hợp đồng     │      │ • Nhập trùng 2 lần đơn    │
  │ • Chậm xuất hóa đơn VAT   │      │ • Khiếu nại công nợ kéo dài│     │ • Giao thiếu, bị phạt tiền │
  └───────────────────────────┘      └───────────────────────────┘      └───────────────────────────┘
```

* **Hệ lụy trực tiếp**:
  - Hủy hóa đơn điện tử và điều chỉnh chứng từ kế toán tốn gấp 10 lần thời gian so với tiền kiểm.
  - Đơn hàng bị nghẽn ở khâu đối soát thủ công khiến hàng hóa giao chậm trễ, giảm uy tín với đối tác đại lý.

---

## 💡 SLIDE 3: GIẢI PHÁP PO PREFLIGHT (THE SOLUTION)

### Cổng Tiền Kiểm Đơn Hàng 1 Chạm — Từ Tệp Thô Đến ERP Hoàn Tất

```
 ┌───────────────┐     ┌──────────────────────────────────────────────┐     ┌───────────────┐
 │ KHÁCH HÀNG    │     │                 PO PREFLIGHT                 │     │ HỆ THỐNG ERP  │
 │ Gửi PO (Excel,│ ──► │  1. Cascading Intake (Bóc tách đa định dạng) │ ──► │  MISA AMIS    │
 │ PDF hóa đơn,  │     │  2. 4-Tier RAG Matcher (Khớp SKU đa ngữ)     │     │  Bravo / Fast │
 │ Ảnh scan)     │     │  3. Deterministic Rules (Giá, kho, công nợ)  │     │  Odoo / SAP B1│
 └───────────────┘     │  4. Mobile 1-Tap HITL (Duyệt Zalo/Telegram)  │     └───────────────┘
                       └──────────────────────────────────────────────┘
```

* **Tự Động 100% Khâu Nhàm Chán**: Trích xuất dữ liệu, kiểm toán số học $\sum(\text{Qty} \times \text{Price})$, đối chiếu hạn mức nợ và tồn kho khả dụng.
* **Người Dùng Giữ Quyền Phê Duyệt (Human-In-The-Loop)**: Chỉ khi người quản lý có thẩm quyền bấm duyệt trên Telegram, Zalo hoặc Web thì đơn hàng mới được đẩy sang ERP qua Transactional Outbox.

---

## ⚡ SLIDE 4: ĐỘT PHÁ CÔNG NGHỆ BẢO ĐẢM KHÔNG ẢO GIÁC (CORE TECH)

### 1. Thuật Toán So Khớp SKU 4 Tầng (4-Tier Waterfall Hybrid RAG)
Giải quyết triệt để vấn đề: Khách viết tên thông tục hoặc tiếng lóng Việt Nam nhưng hệ thống phải map đúng 100% mã SKU nội bộ mà **không bao giờ bị AI bịa đặt (Zero-Hallucination)**.
- **Tier 1 — Exact Hash Match (<1ms, $0)**: Băm chính xác O(1) mã SKU và Barcode niêm yết.
- **Tier 2 — Lexical Fuzzy (<5ms, $0)**: Khoảng cách chuỗi Levenshtein (RapidFuzz) xử lý gõ sai chính tả nhẹ.
- **Tier 3 — Multilingual Dense Vector (<25ms, $0)**: Nhúng vector đa ngữ FastEmbed chạy nội bộ trên CPU máy chủ, hiểu ngôn ngữ dân dã (ví dụ: *"dây mạng 3m bấm sẵn"* $\rightarrow$ `CAB-CAT6-3M`).
- **Tier 4 — LLM Context Reasoner (Fallback)**: Kích hoạt khi độ tương đồng < 70%, bắt buộc định dạng JSON nghiêm ngặt.

### 2. Tự Động Đối Soát Số Học (Self-Reflection Math Verifier)
Hệ thống tự động tính lại từng dòng: $\text{Số lượng} \times \text{Đơn giá} - \text{Chiết khấu} + \text{Thuế VAT}$ và so khớp với tổng tiền trên đơn. Bất kỳ sự chênh lệch số học nào cũng lập tức được gắn cờ cảnh báo `MATH_CALCULATION_DISCREPANCY`.

---

## 🚀 SLIDE 5: QUY TRÌNH VẬN HÀNH THỰC TẾ (LIVE PRODUCT WORKFLOW)

```
[Chặng 1] Tiếp Nhận PO ──► [Chặng 2] Bóc Tách OCR ──► [Chặng 3] Khớp Mã SKU ──► [Chặng 4] Kiểm Tra Luật ──► [Chặng 5] Duyệt Di Động ──► [Chặng 6] Đẩy ERP Outbox
  (Email / Excel / PDF)       (Gemini Flash OCR)        (4-Tier Hybrid)          (Giá, Kho, Công nợ)      (Zalo / Telegram)        (MISA / Odoo / SAP)
```

* **Giao diện hiện đại**: Thiết kế tối giản theo chuẩn công nghiệp, bảng biểu tương tác cao, hỗ trợ chỉnh sửa trực tiếp trên bảng (Inline Edit).
* **Màn hình di động tối giản (`/m/orders/:id`)**: Cho phép Ban Giám Đốc xử lý và phê duyệt đơn hàng khẩn cấp ngay trên điện thoại khi đang công tác.

---

## 📈 SLIDE 6: PHƯƠNG PHÁP ĐO LƯỜNG & KẾT QUẢ PILOT (MEASUREMENT & PILOT DATA)

Thay vì đưa ra các con số giả định, PO Preflight áp dụng **công thức đo lường minh bạch** dựa trên dữ liệu vận hành thực tế:

### 1. Cách Chúng Tôi Đo Lường (Measurement Methodology)
- **Thời gian tiết kiệm thực tế (Giờ)**:  
  $$\text{Hours Saved} = \text{Tổng số đơn xử lý} \times \frac{25\text{ phút (nhập tay)} - 2\text{ phút (tiền kiểm)}}{60}$$
- **Tỉ lệ can thiệp của con người (%)**:  
  $$\text{Human Intervention Rate} = \frac{\text{Số dòng hàng sửa qua Staging}}{\text{Tổng số dòng hàng}} \times 100\%$$
- **Chi phí suy luận AI trung bình / đơn**:  
  $$\text{Cost per PO} = \frac{\text{Tổng chi phí token LLM & OCR}}{\text{Tổng số PO tiếp nhận}}$$

### 2. Kết Quả Đo Kiểm Thử Nghiệm (Benchmark & Pilot Telemetry)
- **Thời gian phân tích trung bình**: **2.1 giây / đơn hàng** (giảm > 90% thời gian chờ đợi).
- **Tỷ lệ phát hiện vi phạm trước ERP**: **100%** (ngăn chặn mọi đơn sai giá hợp đồng, hết tồn kho hoặc nợ quá hạn).
- **Tỷ lệ giải quyết SKU tự động (Tier 1-3)**: **> 96%** (chỉ < 4% đơn hàng cần fallback qua LLM).
- **Chi phí vận hành AI**: Chỉ **$0.00018 USD / đơn hàng** (~4.5 VNĐ / đơn), tối ưu tuyệt đối cho quy mô lớn.

---

## 🔒 SLIDE 7: TUÂN THỦ NGHỊ ĐỊNH 13, ON-PREMISE & CHUỖI BĂM SHA-256

* **Tuân thủ triệt để Nghị định 13/2023/NĐ-CP (Bảo vệ dữ liệu cá nhân tại Việt Nam)**:
  - Toàn bộ dữ liệu khách hàng, hóa đơn và giá cả thương mại được mã hóa khi lưu trữ và truyền tải.
  - Hỗ trợ triển khai hoàn toàn **On-Premises** hoặc trên **Private Cloud nội địa** của khách hàng. Không có bất kỳ dữ liệu nhạy cảm nào bị gửi ra máy chủ nước ngoài.
* **Chuỗi Băm Mật Mã Học SHA-256 (Tamper-evident Hash Chain)**:
  Mỗi sự kiện phân tích, sửa đổi dòng hàng và quyết định duyệt của con người được liên kết toán học thành chuỗi băm bất biến. Ngăn chặn triệt để hành vi can thiệp cơ sở dữ liệu ngầm.
* **Phân Tách Trách Nhiệm (Separation of Duties - SoD)**:
  Quy tắc kiểm soát nội bộ nghiêm ngặt: Nhân viên tạo đơn không được tự duyệt; đơn hàng vượt thẩm quyền giá trị bắt buộc phải có chữ ký số của Giám đốc (Director).

---

## 🏢 SLIDE 8: CHÂN DUNG KHÁCH HÀNG & HỆ SINH THÁI ERP

### Khách Hàng Lý Tưởng (Ideal Customer Profile - ICP):
1. **Nhà Phân Phối / Tổng Đại Lý FMCG & Tiêu Dùng Nhanh**: Tiếp nhận 50 - 500 đơn hàng đại lý mỗi ngày qua file Excel và email.
2. **Doanh Nghiệp Phân Phối Dược Phẩm & Thiết Bị Y Tế**: Đơn hàng có danh mục phức tạp, kiểm soát chặt chẽ đơn vị tính (vỉ, hộp, thùng) và hạn mức công nợ.
3. **Nhà Cung Ứng Vật Tư Công Nghiệp & Xây Dựng**: Khách hàng đặt hàng với quy cách kỹ thuật đặc thù và bảng giá hợp đồng riêng biệt.

### Hệ Sinh Thái Kết Nối ERP Sẵn Sàng:
- **ERP Nội Địa Phổ Biến**: **MISA AMIS**, **Bravo ERP**, **Fast Business Online**.
- **ERP Quốc Tế / Mã Nguồn Mở**: **Odoo ERP**, **SAP Business One**, **SAP S/4HANA**.

---

## 🏆 SLIDE 9: LỢI THẾ CẠNH TRANH ĐỘC BẢN (THE MOAT)

```
┌──────────────────────────────────────┬──────────────────────────────────────┐
│       PHẦN MỀM OCR THÔNG THƯỜNG       │             PO PREFLIGHT             │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ ❌ Chỉ đọc text thô, không hiểu kho  │ ✔ Khớp mã kho 4 tầng (4-Tier RAG)    │
│ ❌ Dễ bị AI ảo giác (Hallucination)  │ ✔ Quy tắc xác định (Zero-Token Rules)│
│ ❌ Không có quy trình duyệt di động   │ ✔ Duyệt 1 chạm qua Telegram & Zalo OA│
│ ❌ Đẩy dữ liệu thô gây lỗi ERP       │ ✔ Transactional Outbox Idempotency   │
│ ❌ Không có chứng thực kiểm toán     │ ✔ Chuỗi băm SHA-256 chống sửa đổi    │
│ ❌ Phụ thuộc đám mây nước ngoài      │ ✔ Sẵn sàng On-Premise & Nghị định 13 │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

---

## 🚀 SLIDE 10: KẾ HOẠCH TRIỂN KHAI PILOT 30 NGÀY (PILOT PLAYBOOK)

### Lộ Trình Triển Khai Pilot 4 Tuần Cho Khách Hàng Mới:
* **Tuần 1 — Khởi Tạo Master Data**: Đồng bộ danh mục SKU, bảng giá hợp đồng và phân quyền người dùng (`/users`).
* **Tuần 2 — Chạy Thử Song Song (Shadow Run)**: Tải PO thật vào hệ thống, tinh chỉnh bộ từ vựng SKU Alias.
* **Tuần 3 — Vận Hành & Duyệt Di Động**: Kích hoạt cổng duyệt Telegram/Zalo, bật Transactional Outbox đồng bộ ERP.
* **Tuần 4 — Nghiệm Thu & Đánh Giá ROI**: Xuất báo cáo Pilot (`/reports`), đối soát số giờ tiết kiệm thực tế.

---

### 🤝 BƯỚC TIẾP THEO (NEXT STEPS):
* **Xem Báo Cáo Pilot Mẫu**: Truy cập giao diện trực quan tại `/reports` và xuất file CSV mẫu.
* **Đăng Ký Tham Gia Chương Trình Pilot 30 Ngày**: Trải nghiệm miễn phí trong môi trường vận hành thực tế.
* **Liên Hệ Đội Ngũ Triển Khai**: Nhật Minh Technology | Hotline: `090x-xxx-xxx` | Email: `contact@popreflight.vn`.

---
*Tài liệu thuyết trình được lưu hành nội bộ — PO Preflight 2026.*
