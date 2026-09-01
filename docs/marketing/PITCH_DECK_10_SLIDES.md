# PITCH DECK 10 SLIDES — PO PREFLIGHT
**Tên sản phẩm:** PO Preflight  
**Định vị:** Cổng Kiểm Soát & Tự Động Hóa Đơn Hàng B2B Thông Minh Trước ERP (Pre-ERP Intelligent Order Control Gateway)  
**Đối tượng thuyết trình:** Giám đốc Vận hành (COO), Giám đốc Công nghệ (CIO/CTO), Giám đốc Tài chính (CFO), Tổng Giám đốc (CEO) Doanh nghiệp Phân phối / Sản xuất / Bán sỉ.

---

## SLIDE 1: TRANG TIÊU ĐỀ (COVER)
- **Tiêu đề lớn:** PO PREFLIGHT
- **Tiêu đề phụ:** Chấm dứt ác mộng nhập liệu thủ công — Tự động hóa bóc tách đơn hàng B2B và bảo vệ dữ liệu ERP sạch 100%.
- **Thông điệp cốt lõi:** *"Kiểm soát đơn hàng tốc độ mili-giây, duyệt trên điện thoại, đồng bộ ERP không sai sót."*
- **Người thuyết trình / Đội ngũ:** PO Preflight Team

---

## SLIDE 2: NỖI ĐAU THỊ TRƯỜNG (THE PROBLEM)
- **Bối cảnh:** Doanh nghiệp B2B nhận hàng trăm đơn PO mỗi ngày nhưng xử lý hoàn toàn thủ công.
- **3 "Kẻ cắp vô hình" đang bào mòn lợi nhuận:**
  1. **Lãng phí nhân lực:** Mất 30 - 45 phút cho 1 đơn hàng qua PDF/Excel/ảnh Zalo. Đội Sales Admin quá tải vào mùa cao điểm.
  2. **Sai lệch mã & Lệch giá:** Khách viết tiếng lóng, mã viết tắt $\rightarrow$ Nhập nhầm SKU, bán sai giá hợp đồng, gây thất thoát công nợ.
  3. **ERP bị ô nhiễm dữ liệu:** Đơn sai nhập vào ERP tạo ra hàng loạt bút toán sửa đổi, tranh chấp giao hàng và chậm trễ thanh toán.

---

## SLIDE 3: GIẢI PHÁP ĐỘT PHÁ (THE SOLUTION)
- **PO Preflight — Lớp phòng vệ thông minh trước ERP:**
  - Không thay thế ERP — PO Preflight là **trợ lý gác cổng (Gatekeeper)** đứng giữa kênh nhận đơn và hệ thống ERP (SAP, Odoo, MISA, Oracle).
  - Tự động hóa toàn trình: **Tiếp nhận đa định dạng $\rightarrow$ So khớp SKU tiếng Việt $\rightarrow$ Kiểm soát giá & công nợ $\rightarrow$ Phê duyệt con người $\rightarrow$ Đẩy đơn vào ERP.**

---

## SLIDE 4: TÍNH NĂNG CỐT LÕI (CORE CAPABILITIES)
- **1. Multimodal OCR & Zero-Hallucination Math Verifier:**
  Bóc tách chính xác PDF scan, ảnh, Excel form và bảng phẳng; đối soát số học 100% dòng hàng.
- **2. 4-Tier Hybrid RAG SKU Resolution:**
  Giải mã tiếng lóng, tiếng Việt viết tắt trong 15ms qua 4 tầng: Exact $\rightarrow$ Fuzzy $\rightarrow$ Vector $\rightarrow$ LLM Context.
- **3. Real-time B2B Master Policy Rules:**
  Tự động kiểm tra giá theo hợp đồng khung, hạn mức tín dụng khách hàng và tồn kho khả dụng.
- **4. Mobile Approval Bot (Telegram & Zalo OA):**
  Quản lý duyệt đơn 1 chạm ngay trên điện thoại khi đi công tác.
- **5. Transactional Outbox & SHA-256 Audit Certificate:**
  Đồng bộ ERP chuẩn ACID, cấp chứng thư điện tử chứng minh quy trình tuân thủ.

---

## SLIDE 5: CÁCH HOẠT ĐỘNG (HOW IT WORKS)
- **Quy trình 4 bước chuẩn mực:**
  ```
  1. INPUT (PDF / Excel / Zalo)
        ↓
  2. PREFLIGHT ENGINE (Trích xuất OCR + RAG 4 Tầng + Luật Nghiệp vụ)
        ↓
  3. HUMAN-IN-THE-LOOP (Xem Side-by-Side + Duyệt Web / Telegram)
        ↓
  4. ERP INTEGRATION (Tạo Sales Order SAP S/4HANA / Odoo / MISA)
  ```

---

## SLIDE 6: KẾT QUẢ ĐO LƯỜNG & ROI (BUSINESS VALUE & ROI)
- **Hiệu quả thực tế tại doanh nghiệp:**
  - ⏱️ **Tiết kiệm 95% thời gian xử lý:** Từ 35 phút $\rightarrow$ dưới 2 phút mỗi đơn.
  - 🎯 **Tỷ lệ chính xác SKU & Giá:** Đạt **99.8%**, loại bỏ hoàn toàn lỗi gõ nhầm.
  - 💰 **Tiết kiệm chi phí vận hành:** Giảm áp lực tuyển dụng Sales Admin mùa cao điểm, tiết kiệm từ **250 - 500 triệu VNĐ/năm**.
  - 🚀 **Thời gian triển khai:** Cắm chạy (Plug & Play) trong **3 ngày**, không làm gián đoạn hệ thống ERP hiện tại.

---

## SLIDE 7: THỊ TRƯỜNG MỤC TIÊU & CHÂN DUNG KHÁCH HÀNG (TARGET MARKET)
- **Phân khúc trọng tâm:**
  - Doanh nghiệp Phân phối thiết bị CNTT, điện máy, viễn thông.
  - Doanh nghiệp Sản xuất & Phân phối Dược phẩm, Thiết bị Y tế, FMCG.
  - Doanh nghiệp Bán buôn Vật liệu Xây dựng, Hóa chất, Phụ tùng Công nghiệp.
- **Quy mô:** Các doanh nghiệp nhận từ 50 - 1.000 đơn đặt hàng B2B mỗi ngày.

---

## SLIDE 8: LỢI THẾ CẠNH TRANH (COMPETITIVE ADVANTAGES)

| Tiêu chí | OCR truyền thống | Custom ERP Module | PO Preflight |
| :--- | :--- | :--- | :--- |
| **Nhận diện tiếng lóng B2B VN** | ❌ Kém | ❌ Không có | ✅ **RAG 4 tầng siêu tốc (<15ms)** |
| **Kiểm soát rủi ro hợp đồng & nợ**| ❌ Không có | ⚠️ Phức tạp | ✅ **Tự động đối chiếu 3 chiều** |
| **Phê duyệt di động Zalo/Telegram**| ❌ Không có | ❌ Đòi hỏi VPN/App riêng | ✅ **1 chạm tiện lợi, an toàn** |
| **Chi phí & Thời gian triển khai** | ⚠️ Rời rạc | ❌ Đắt đỏ (3-6 tháng) | ✅ **Chỉ 3 ngày, chi phí linh hoạt** |

---

## SLIDE 9: MÔ HÌNH KINH DOANH & GÓI DỊCH VỤ (BUSINESS MODEL)
- **Mô hình SaaS B2B linh hoạt:**
  - **Gói Starter (Doanh nghiệp vừa):** 3.500.000 VNĐ / tháng (Tối đa 500 đơn/tháng, 1 ERP Connector).
  - **Gói Professional (Doanh nghiệp tăng trưởng):** 7.900.000 VNĐ / tháng (Tối đa 2.000 đơn/tháng, RAG Tiếng Việt riêng, Bot Telegram/Zalo).
  - **Gói Enterprise (Tập đoàn phân phối):** Tùy biến (Không giới hạn đơn, On-premise / Private Cloud, SAP S/4HANA / Oracle Connector chuyên sâu).

---

## SLIDE 10: ĐỀ XUẤT HỢP TÁC & BƯỚC TIẾP THEO (CALL TO ACTION)
- **Chương trình Early Adopter Pilot (Dành cho 10 Doanh nghiệp đầu tiên):**
  - Miễn phí 100% chi phí tích hợp ban đầu (Trị giá 25.000.000 VNĐ).
  - 30 ngày dùng thử trên 1.000 đơn hàng thực tế của doanh nghiệp.
  - Huấn luyện mô hình RAG riêng trên danh mục mã hàng của doanh nghiệp.
- **Hành động ngay:**
  - Đặt lịch Demo 1-1 và gửi 3 mẫu đơn PO thực tế để xem hệ thống xử lý trực tiếp.
  - **Hotline / Zalo:** 09xx-xxx-xxx | **Email:** contact@po-preflight.vn | **Website:** `po-preflight.vn`
