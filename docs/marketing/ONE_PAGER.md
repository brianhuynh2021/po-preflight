# PO PREFLIGHT — ONE-PAGER GIẢI PHÁP TỰ ĐỘNG HÓA & KIỂM SOÁT ĐƠN HÀNG B2B

---

## 1. NỖI ĐAU THỰC TẾ CỦA DOANH NGHIỆP PHÂN PHỐI & BÁN BUÔN B2B

Tại các doanh nghiệp phân phối, sản xuất và bán sỉ tại Việt Nam, đội ngũ Sales Admin (CS/Nhập liệu) đang mất **30 - 45 phút cho mỗi đơn hàng** và doanh nghiệp đối mặt với 4 rủi ro lớn:

1. **Đa định dạng, xử lý thủ công mệt mỏi:** Đơn PO gửi qua Zalo, Email bằng đủ loại: PDF scan mờ, Excel form tùy chỉnh, bảng phẳng CSV, ảnh chụp từ điện thoại. Nhập tay vừa chậm vừa dễ sót dòng.
2. **Sai sót SKU & Tên gọi địa phương:** Khách viết tắt (*"dây mạng 3m bấm sẵn"*, *"màn 27 inch 4k"*, mã cũ đã đổi). Tra cứu bảng giá mất hàng chục phút, nhập nhầm mã gây giao sai hàng, bị phạt vi phạm hợp đồng.
3. **Lệch giá hợp đồng & Thất thoát công nợ:** Không kịp đối chiếu giá theo hợp đồng khung và hạn mức tín dụng khách hàng, dẫn đến bán dưới giá sàn hoặc cho nợ vượt trần.
4. **ERP rác (Garbage-In, Garbage-Out):** Nhập trực tiếp đơn sai vào SAP / Odoo / MISA tạo ra hàng loạt chứng từ điều chỉnh (Credit/Debit Note), kế toán và kho bãi xung đột liên tục.

---

## 2. GIẢI PHÁP: PO PREFLIGHT — TRỢ LÝ KIỂM SOÁT ĐƠN HÀNG TỰ ĐỘNG B2B

**PO Preflight** là cổng kiểm soát trung gian thông minh (B2B Pre-ERP Control Gateway) tự động hóa 100% quy trình từ lúc nhận file PO đến khi đẩy đơn sạch vào ERP:

- 📑 **Trích xuất đa định dạng siêu chuẩn:** Đọc tức thì PDF scan, ảnh, file Excel form hoặc bảng phẳng với cơ chế tự kiểm toán số học (Self-Reflection Math Verifier) chống ảo giác 100%.
- 🧠 **RAG 4 tầng giải mã SKU thuần Việt:** Tìm đúng mã ERP trong 15ms qua 4 tầng (Chính xác $\rightarrow$ Fuzzy $\rightarrow$ Vector ngữ nghĩa tiếng Việt $\rightarrow$ LLM Context), tự động nhận diện tiếng lóng ngành.
- 🛡️ **Bộ quy tắc nghiệp vụ thời gian thực:** Kiểm tra tự động 3 chiều: Bảng giá theo khách (B2B Price Agreement), Hạn mức công nợ & nợ quá hạn (Credit Profile), Tồn kho an toàn & Quy đổi ĐVT (Thùng $\leftrightarrow$ Cái).
- 📱 **Phê duyệt 1 chạm trên Telegram & Zalo:** Trưởng phòng duyệt ngoại lệ ngay trên điện thoại khi đi công tác mà không cần mở máy tính hay đăng nhập ERP cồng kềnh.
- ⚡ **Đồng bộ ERP chuẩn ACID với Transactional Outbox:** Đơn duyệt xong tự động tạo Sales Order trên SAP S/4HANA, Odoo, MISA AMIS kèm mã băm chứng thực (SHA-256 Audit Certificate).

---

## 3. CÁCH HOẠT ĐỘNG (WORKFLOW 4 BƯỚC KHÉP KÍN)

```
[1. Nhận PO] ──▶ [2. Phân tích & So khớp] ──▶ [3. Kiểm soát & Duyệt] ──▶ [4. Đồng bộ ERP]
(PDF, Excel,      (OCR + RAG 4 Tầng          (Kiểm tra Giá, Tồn,      (Tạo Sales Order SAP/
 Zalo/Email)       chống ảo giác)             Công nợ + Mobile HITL)   Odoo/MISA + Audit Log)
```

1. **Tiếp nhận & Bóc tách (3s):** Nhân viên kéo thả PO hoặc nhận tự động qua Webhook Zalo/Email. Hệ thống chuẩn hóa thông tin ngay lập tức.
2. **So khớp & Đánh giá Rủi ro (5s):** Phân loại rủi ro theo 3 mức `Ready` (Đủ chuẩn), `Review required` (Cần xem xét), `Blocked` (Bị chặn do nợ xấu / hết hàng).
3. **Phê duyệt con người kiểm soát (Human-In-The-Loop):** Quản lý xem đối chiếu song song (Side-by-Side) giữa file gốc và dữ liệu trích xuất; duyệt nhanh qua Telegram/Zalo.
4. **Đẩy đơn sạch vào ERP (2s):** Transactional Outbox tự động tạo đơn trên ERP, ghi sổ nhật ký tuân thủ không thể sửa xóa.

---

## 4. HIỆU QUẢ ĐO LƯỜNG NGAY (ROI)

| Chỉ số | Trước khi dùng PO Preflight | Sau khi dùng PO Preflight | Mức cải thiện |
| :--- | :--- | :--- | :--- |
| **Thời gian xử lý đơn** | 30 - 45 phút / đơn | **1 - 2 phút / đơn** | **Giảm 95%** |
| **Tỷ lệ sai sót SKU/Giá** | 3 - 5% tổng số đơn | **< 0.1%** | **Giảm 98%** |
| **Chi phí nhân sự Admin** | 3 - 5 nhân sự CS/nhập liệu | 1 nhân sự phụ trách ngoại lệ | **Tiết kiệm ~300tr/năm** |
| **Thời gian Go-Live** | Tùy biến ERP mất 3 - 6 tháng | **Cắm chạy trong 3 ngày** | **Nhanh gấp 30 lần** |

---

## 5. CHƯƠNG TRÌNH PILOT & ƯU ĐÃI ĐẶC QUYỀN CHO 10 DOANH NGHIỆP ĐẦU TIÊN

Dành riêng cho **10 Doanh nghiệp Phân phối / Bán buôn B2B đầu tiên**:

- 🎁 **Miễn phí 100% chi phí khảo sát & tích hợp kết nối ban đầu** (Trị giá 25.000.000 VNĐ).
- 🎁 **30 ngày dùng thử toàn diện (Full-feature Pilot)** với 1.000 đơn hàng thực tế của doanh nghiệp.
- 🎁 **Huấn luyện RAG nhận diện bộ từ khóa / SKU riêng** của doanh nghiệp với độ chính xác >98%.
- 🛡️ **Cam kết không rủi ro:** Không can thiệp sửa đổi Core ERP, dữ liệu lưu trữ hoàn toàn tại máy chủ doanh nghiệp (On-premise / Private Cloud).

**Liên hệ đăng ký Pilot ngay:**  
- **Website:** https://po-preflight.vn  
- **Hotline / Zalo:** 09xx-xxx-xxx  
- **Email:** pilot@po-preflight.vn
