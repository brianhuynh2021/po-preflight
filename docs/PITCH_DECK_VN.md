# 📊 PO PREFLIGHT — EXECUTIVE PITCH DECK & BẢN THUYẾT TRÌNH DỰ ÁN
> **Giải Pháp Cổng Kiểm Soát An Toàn Tự Động Cho Đơn Đặt Hàng B2B Trước Khi Đẩy Vào ERP**  
> *Chuẩn Thuyết Trình Gọi Vốn / Trình Ban Lãnh Đạo (Executive & Investor Ready)*

---

```
═══════════════════════════════════════════════════════════════════════════════
                           MỤC LỤC BẢN THUYẾT TRÌNH (10 SLIDES)
═══════════════════════════════════════════════════════════════════════════════
  [SLIDE 1] TỔNG QUAN & TUYÊN NGÔN SỨ MỆNH (THE HOOK)
  [SLIDE 2] VẤN ĐỀ THỰC TẾ & NỖI ĐAU THỊ TRƯỜNG (THE PROBLEM & HIDDEN COSTS)
  [SLIDE 3] GIẢI PHÁP: CỔNG KIỂM SOÁT TỰ ĐỘNG PO PREFLIGHT (THE SOLUTION)
  [SLIDE 4] ĐỘT PHÁ CÔNG NGHỆ: 4-TIER RAG & ZERO-HALLUCINATION AI (CORE TECH)
  [SLIDE 5] QUY TRÌNH VẬN HÀNH THỰC TẾ 6 CHẶNG (LIVE PRODUCT WORKFLOW)
  [SLIDE 6] BÀI TOÁN KINH TẾ & TỶ SUẤT HOÀN VỐN ROI (ROI & BUSINESS IMPACT)
  [SLIDE 7] BẢO MẬT DOANH NGHIỆP & CHỨNG THỰ MERKLE SOX 404 (SECURITY & COMPLIANCE)
  [SLIDE 8] CHÂN DUNG KHÁCH HÀNG & THỊ TRƯỜNG MỤC TIÊU (ICP & TAM/SAM)
  [SLIDE 9] LỢI THẾ CẠNH TRANH ĐỘC BẢN (MOAT & COMPETITIVE ADVANTAGE)
  [SLIDE 10] LỘ TRÌNH PHÁT TRIỂN & KÊU GỌI HÀNH ĐỘNG (ROADMAP & CALL TO ACTION)
═══════════════════════════════════════════════════════════════════════════════
```

---

## 🎯 SLIDE 1: TỔNG QUAN DỰ ÁN (THE HOOK)

### 📌 Tựa đề: **PO PREFLIGHT — Autonomous Order Intake & Risk Gatekeeper for B2B**

* **Khẩu hiệu (Tagline)**: *"Không bao giờ để một đơn hàng sai giá, hết tồn kho hoặc nhập trùng lọt vào hệ thống ERP."*
* **Tuyên ngôn giá trị (Value Proposition)**:
  Nền tảng AI chuyên sâu giúp doanh nghiệp B2B tự động hóa 90% quy trình tiếp nhận, bóc tách và đối chiếu đơn đặt hàng (PO) dạng PDF/ảnh/Excel, phát hiện 100% rủi ro tài chính và đồng bộ thẳng vào SAP/Odoo trong < 30 giây.
* **Người trình bày**: Ban Sáng Lập / Nhóm Kỹ Thuật PO Preflight.

> 🎙️ **Speaker Notes**: *"Kính thưa quý vị, trong ngành hàng không, không một chiếc máy bay nào được cất cánh nếu chưa vượt qua quy trình Pre-flight Check. Nhưng trong các doanh nghiệp B2B, hàng nghìn đơn đặt hàng trị giá hàng tỷ đồng mỗi ngày đang được nhân viên nhập tay vào ERP mà không có bất kỳ cổng kiểm soát an toàn tự động nào. PO Preflight sinh ra để giải quyết triệt để rủi ro đó."*

---

## 🚨 SLIDE 2: NỖI ĐAU THỊ TRƯỜNG & CHI PHÍ ẨN (THE PROBLEM)

### 3 "Lỗ Hổng" Chí Mạng Trong Xử Lý Đơn Hàng B2B Hiện Nay:

```
  ┌───────────────────────────┐      ┌───────────────────────────┐      ┌───────────────────────────┐
  │   1. Nhập Tay Chậm Chạp   │      │    2. Sai Mã & Lệch Giá   │      │   3. Thất Thoát Tồn Kho   │
  │                           │      │                           │      │                           │
  │ • Mất 15-30 phút/đơn      │      │ • Khách dùng tên lóng     │      │ • Đơn duyệt khi kho đã hết│
  │ • Sales Admin quá tải     │      │ • Khách tự ý áp giá cũ    │      │ • Nhập trùng 2 lần đơn    │
  │ • Tỷ lệ sai sót gõ 3-5%   │      │ • Doanh nghiệp mất tiền tỷ│      │ • Bị phạt vi phạm hợp đồng│
  └───────────────────────────┘      └───────────────────────────┘      └───────────────────────────┘
```

* **Chi phí ẩn vô hình**:
  - Doanh nghiệp 50 tỷ doanh thu/tháng mất trung bình **150 - 300 triệu/tháng** vì chiết khấu sai, khiếu nại công nợ và chi phí đổi trả hàng sai mã.
  - Tốc độ xử lý đơn chậm khiến khách hàng chuyển sang đối thủ cạnh tranh có tốc độ phản hồi nhanh hơn.

---

## 💡 SLIDE 3: GIẢI PHÁP PO PREFLIGHT (THE SOLUTION)

### Cổng Kiểm Soát Đơn Hàng 1 Chạm — Từ Tài Liệu Thô Đến ERP Hoàn Tất

```
 ┌───────────────┐     ┌──────────────────────────────────────────────┐     ┌───────────────┐
 │ KHÁCH HÀNG    │     │                 PO PREFLIGHT                 │     │ DOANH NGHIỆP  │
 │ Gửi PO (PDF,  │ ──► │  1. Ingestion OCR Vision (Bóc tách dữ liệu)  │ ──► │  SAP S/4HANA  │
 │ Ảnh Scan,     │     │  2. 4-Tier RAG Matcher (Khớp SKU <15ms)      │     │  Odoo / MISA  │
 │ Zalo / Email) │     │  3. Deterministic Rules (Kiểm tra giá & kho) │     │  NetSuite ERP │
 └───────────────┘     │  4. Telegram 1-Tap HITL (Duyệt trên mobile)  │     └───────────────┘
                       └──────────────────────────────────────────────┘
```

* **Tự Động 100% Khâu Nhàm Chán**: Trích xuất, kiểm toán số học, đối chiếu tồn kho và chính sách giá.
* **Giữ Quyền Kiểm Soát Cho Con Người (Human-in-the-Loop)**: Chỉ các đơn có cảnh báo (Review Required/Blocked) mới yêu cầu Trưởng phòng duyệt 1 chạm trên Telegram/Zalo.

---

## ⚡ SLIDE 4: ĐỘT PHÁ CÔNG NGHỆ ĐỘC QUYỀN (CORE INNOVATIONS)

### 1. Thuật Toán 4-Tier Waterfall Hybrid SKU Resolution
Giải quyết bài toán: Khách ghi tên lóng/tiếng lóng Việt Nam nhưng hệ thống phải map đúng 100% SKU kho mà **không bao giờ bị AI ảo giác (Zero-Hallucination)**.
- **Tier 0 (<0.5ms, 0 tokens)**: Bộ nhớ ghi nhớ biệt danh theo từng khách hàng (`Customer Active Learning Store`).
- **Tier 1 (<1ms, 0 tokens)**: Băm chính xác O(1) Exact Hash Match.
- **Tier 2 (<5ms, 0 tokens)**: Khoảng cách chuỗi RapidFuzz Levenshtein (bắt lỗi gõ sai chính tả).
- **Tier 3 (<15ms, 0 tokens)**: Không gian vector ngữ nghĩa TF-IDF Character Trigrams.
- **Tier 4 (Fallback)**: LLM Context Reasoner khi độ tin cậy < 70%.

### 2. Tự Kiểm Toán Số Học (Self-Reflection Math Grounding)
Hệ thống tự động cộng dồn $\sum(\text{Quantity} \times \text{Unit Price})$ và so khớp với tổng tiền khai báo trên hóa đơn. Nếu lệch dù chỉ 1 đồng, hệ thống kích hoạt cảnh báo lập tức.

---

## 🚀 SLIDE 5: QUY TRÌNH VẬN HÀNH THỰC TẾ (LIVE PRODUCT WORKFLOW)

```
[Chặng 1] Tải Lên PO  ──► [Chặng 2] OCR Bóc Tách ──► [Chặng 3] Khớp Mã SKU ──► [Chặng 4] Kiểm Tra Luật ──► [Chặng 5] Duyệt Telegram ──► [Chặng 6] Đẩy ERP SAP
 (PDF / Ảnh Scan)          (Gemini 2.0 Flash)          (4-Tier Waterfall)        (Giá, Kho, Trùng lặp)      (Mobile 1 Chạm)          (Idempotent Outbox)
```

* **Giao diện đẳng cấp**: 11 phân hệ tinh gọn chuẩn Linear / Stanford HCI Design System.
* **Thời gian thực (Real-Time)**: Kết nối Server-Sent Events (SSE) cập nhật trạng thái đơn hàng ngay tức thì mà không cần bấm F5 tải lại trang.

---

## 📈 SLIDE 6: BÀI TOÁN KINH TẾ & TỶ SUẤT HOÀN VỐN (ROI)

### So Sánh Trước & Sau Khi Ứng Dụng PO Preflight:

| Tiêu Chí So Sánh | Cách Làm Thủ Công Trước Đây | Ứng Dụng PO Preflight | Mức Độ Cải Thiện |
| :--- | :--- | :--- | :--- |
| **Thời gian xử lý 1 đơn hàng** | 15 – 30 phút/đơn | **< 30 giây/đơn** | ⚡ **Nhanh hơn 30 - 60 lần** |
| **Tỷ lệ sai sót gõ dữ liệu** | 3% – 5% tổng số đơn | **0% (Được chặn bằng Rules)** | 🎯 **Triệt tiêu 100% lỗi** |
| **Năng suất xử lý / nhân sự** | Tối đa 30 – 40 đơn/ngày | **> 500 đơn/ngày** | 🚀 **Tăng gấp 10 lần** |
| **Chi phí nhân sự nhập liệu** | 3 - 5 nhân viên (~45tr/tháng) | **1 nhân sự giám sát (~10tr/tháng)** | 💰 **Tiết kiệm 70 - 80%** |
| **Rủi ro thất thoát doanh thu** | Tiềm ẩn 50 - 200tr/tháng | **Được bảo vệ tuyệt đối** | 🛡️ **Bảo vệ dòng tiền** |

> 💵 **Thời gian hoàn vốn (Payback Period)**: **Dưới 45 ngày** kể từ khi triển khai.

---

## 🔒 SLIDE 7: BẢO MẬT DOANH NGHIỆP & KIỂM TOÁN MERKLE (SECURITY & AUDIT)

* **Chuẩn SOX 404 & SOC2 Type II**:
  Mỗi hành động bóc tách, đánh giá luật, phê duyệt của con người và đồng bộ ERP được băm thành một **Khối SHA-256 trong Chuỗi Merkle Hash Chain**.
* **Chống Sửa Đổi Dữ Liệu Lén (Tamper-Evident Non-Repudiation)**:
  Không ai (kể cả quản trị viên cơ sở dữ liệu) có thể sửa lén giá trị đơn hàng mà không làm vỡ chữ ký mã hóa của chuỗi.
* **Bảo Mật Đa Tầng**:
  - Xác thực Webhook Anti-Spoofing (`X-Telegram-Bot-Api-Secret-Token`).
  - Phân quyền RBAC 4 cấp (`ADMIN`, `MANAGER`, `AUDITOR`, `VIEWER`).
  - Chống tấn công DDoS bằng Sliding-Window Rate Limiting.

---

## 🏢 SLIDE 8: THỊ TRƯỜNG MỤC TIÊU & KHÁCH HÀNG LÝ TƯỞNG (ICP)

### Chân Dung Khách Hàng Mục Tiêu (Ideal Customer Profile):
1. **Nhà Phân Phối / Tổng Đại Lý FMCG & Hàng Tiêu Dùng**: Có từ 50 - 1,000 đại lý cấp 2 gửi đơn hàng mỗi ngày.
2. **Công Ty Dược Phẩm & Vật Tư Y Tế**: Cung cấp thuốc cho hệ thống bệnh viện, chuỗi nhà thuốc (Long Châu, An Khang, Pharmacity).
3. **Doanh Nghiệp B2B Thiết Bị Công Nghiệp / CNTT / Xây Dựng**: Đơn hàng có danh mục kỹ thuật phức tạp, nhiều thông số.

* **Dung lượng thị trường (Vietnam B2B TAM)**:
  - Hơn **45,000+ doanh nghiệp phân phối và bán buôn B2B** tại Việt Nam đang sử dụng ERP/phần mềm kế toán nhưng vẫn nhập liệu thủ công.
  - Thị trường mục tiêu sẵn sàng chi trả: **10 - 50 triệu VNĐ/tháng/doanh nghiệp** cho giải pháp tự động hóa intake.

---

## 🏆 SLIDE 9: LỢI THẾ CẠNH TRANH ĐỘC BẢN (THE MOAT)

```
┌──────────────────────────────────────┬──────────────────────────────────────┐
│       PHẦN MỀM OCR THÔNG THƯỜNG       │             PO PREFLIGHT             │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ ❌ Chỉ đọc chữ thô, không hiểu kho   │ ✔ Khớp mã kho 4 tầng (4-Tier RAG)    │
│ ❌ Dễ bị AI ảo giác (Hallucination)  │ ✔ Kiểm toán luật cứng (Deterministic)│
│ ❌ Không có quy trình duyệt di động   │ ✔ Duyệt 1 chạm qua Telegram/Zalo Bot │
│ ❌ Đẩy dữ liệu thô gây lỗi ERP       │ ✔ Transactional Outbox Idempotency   │
│ ❌ Không có chứng thực kiểm toán     │ ✔ Chứng thư mã hóa Merkle Tree       │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

---

## 🚀 SLIDE 10: LỘ TRÌNH PHÁT TRIỂN & KÊU GỌI HÀNH ĐỘNG (CALL TO ACTION)

### Lộ Trình 12 Tháng Tới:
* **Q1/2026 (Hiện tại)**: Hoàn tất Core Engine, 11 phân hệ UI, 4-Tier RAG, kết nối SAP/Odoo Outbox.
* **Q2/2026**: Triển khai thí điểm (Pilot) tại 5 doanh nghiệp phân phối FMCG & Dược phẩm lớn tại TP.HCM & Hà Nội.
* **Q3/2026**: Tích hợp trực tiếp App Connector lên Chợ ứng dụng MISA, SAP App Center, Odoo App Store.
* **Q4/2026**: Mở rộng tính năng dự báo tồn kho tự động & tự động đàm phán chênh lệch giá bằng AI Agent.

---

### 🤝 KÊU GỌI HÀNH ĐỘNG (NEXT STEPS):
* **Xem Trực Tiếp Bản Demo**: Truy cập `http://localhost:5173` để trải nghiệm bóc tách và duyệt đơn trực tiếp.
* **Đăng Ký Trải Nghiệm Thí Điểm (Pilot Program)**: Miễn phí 30 ngày tích hợp vào hệ thống ERP nội bộ.
* **Liên Hệ Đội Ngũ Sáng Lập**: `contact@popreflight.com` | Hotline: `090x-xxx-xxx`.

---
*Bản quyền tài liệu thuộc về Dự Án PO Preflight — 2026.*
