# KỊCH BẢN VIDEO DEMO 60 GIÂY — PO PREFLIGHT (DỮ LIỆU THẬT)

> **Định dạng:** Video màn hình thực tế (Screencast) trên hệ thống chạy thật + Giọng đọc voice-over tiếng Việt chuẩn + Hiệu ứng âm thanh  
> **Căn cứ kịch bản:** Luồng nghiệp vụ kiểm thử tích hợp thực tế A7 / C6 / C7 (Bóc tách file thật → Staging inline edit → Phân quyền SoD → Duyệt di động Telegram/Zalo → Transactional ERP Outbox → Báo cáo Pilot).

---

## 🎬 BẢNG PHÂN CẢNH CHI TIẾT (STORYBOARD & TIMELINE)

| Thời lượng | Hình ảnh & Thao tác màn hình thực tế (Visual) | Lời thoại Voice-Over (Audio) | Âm thanh & Ghi chú |
| :---: | :--- | :--- | :--- |
| **00:00 - 00:09** *(9s)* | **Cảnh 1: Nỗi đau đối soát thủ công**<br>- Mở màn hình hộp thư email và tin nhắn Zalo gửi các file PO chụp nghiêng, file Excel lệch cột.<br>- Sales Admin mở nhiều cửa sổ đối soát thủ công từng dòng với bảng giá và phần mềm ERP. | *"Mỗi ngày, doanh nghiệp phân phối nhận hàng trăm đơn đặt hàng qua Email, Zalo: file Excel lệch cột, ảnh scan, viết sai tên mã hàng. Sales Admin mất 25 phút rà soát thủ công từng đơn — chỉ cần một lần nhầm giá hoặc sót nợ quá hạn, doanh nghiệp chịu tổn thất lớn."* | Tiếng gõ phím dồn dập, tiếng chuông thông báo Zalo liên tục. |
| **00:09 - 00:22** *(13s)* | **Cảnh 2: Tiếp nhận & Bóc tách tự phản ánh số học**<br>- Chuyển sang giao diện `/orders` của PO Preflight.<br>- Kéo thả tệp Excel `PO-FPT-7788.xlsx` vào vùng tải lên.<br>- Trong 2 giây, hệ thống hoàn tất bóc tách, bảng Staging hiện ra với trạng thái tự động tính lại $\sum(\text{Qty} \times \text{Price})$ không lệch 1 đồng. | *"Hãy để **PO Preflight** làm việc đó chỉ trong 2 giây. Kéo thả tệp Excel hoặc PDF scan. Động cơ tự động bóc tách từng dòng hàng và tự kiểm toán số học chống ảo giác 100%."* | Tiếng *Whoosh* mượt mà, icon thành công màu xanh lá bừng sáng. |
| **00:22 - 00:36** *(14s)* | **Cảnh 3: So khớp SKU 4 tầng & Cảnh báo luật 3 chiều**<br>- Quay cận cảnh dòng hàng có tên lóng *"dây mạng 3m bấm sẵn"*, hệ thống map chính xác sang `CAB-CAT6-3M` với độ tin cậy 100% nhờ FastEmbed vector.<br>- Dòng hàng bị lệch giá hợp đồng hoặc tồn kho ATP thiếu hụt lập tức bị gắn thẻ cảnh báo viền vàng cam `PRICE_MISMATCH` và `INSUFFICIENT_STOCK`. | *"Khách gọi tên sản phẩm theo ngôn ngữ dân dã? Bộ so khớp 4 tầng nhận diện chính xác mã kho nội bộ. Hệ thống đối soát 3 chiều: Bảng giá hợp đồng, tồn kho thực tế và hạn mức công nợ để chặn đứng mọi rủi ro trước khi vào ERP."* | Tiếng quét radar điện tử (*Scan beep*), highlight thẻ cảnh báo màu hổ phách rõ ràng. |
| **00:36 - 00:48** *(12s)* | **Cảnh 4: Phê duyệt di động 1 chạm & Đồng bộ ERP Outbox**<br>- Màn hình điện thoại iPhone nhận tin nhắn Telegram / Zalo OA tóm tắt rủi ro đơn hàng kèm nút tương tác (hoặc mở `/m/orders/PO-10428`).<br>- Giám đốc chạm nút **[✅ Duyệt Đơn]**.<br>- Ngay lập tức trên web, đơn chuyển sang **Approved**, Transactional Outbox gửi gói tin sang MISA AMIS / SAP S/4HANA có Transaction ID bất biến. | *"Quản lý có thể phê duyệt ngoại lệ 1 chạm ngay trên Telegram, Zalo hoặc màn hình di động khi đang công tác. Đơn duyệt hợp lệ được đẩy tức thì vào MISA AMIS hoặc SAP với chữ ký mật mã học SHA-256 chống làm giả."* | Tiếng thông báo *Ping*, tiếng chạm nút bấm, tiếng đóng dấu chứng nhận thành công. |
| **00:48 - 01:00** *(12s)* | **Cảnh 5: Báo cáo đo lường Pilot & Kêu gọi hành động**<br>- Mở trang `/reports`: Hiện biểu đồ SVG thời gian tiết kiệm, tỷ lệ tự động hóa 96%, nút xuất `po_preflight_pilot_report.csv`.<br>- Hiện thông điệp kêu gọi hành động (Call To Action). | *"Giảm 90% thời gian tiền kiểm, bảo vệ dòng tiền và giữ sạch dữ liệu kế toán. Đăng ký chương trình trải nghiệm Pilot 30 ngày cho doanh nghiệp của bạn ngay hôm nay tại po-preflight.vn!"* | Nhạc nền công nghệ dồn dập, hào hứng, kết thúc chuyên nghiệp. |

---

## 🛠 HƯỚNG DẪN QUAY MÀN HÌNH TRÊN DỮ LIỆU THẬT (RECORDING GUIDE)

1. **Chuẩn bị môi trường:**
   - Chạy máy chủ backend: `PYTHONPATH=src ./.venv/bin/python -m preflight.cli run`
   - Chạy giao diện web: `cd apps/web && npm run dev`
   - Đặt trình duyệt ở độ phân giải tiêu chuẩn `1920x1080` (100% zoom).
2. **Các màn hình quay thực tế:**
   - **Đoạn 1 (0:10):** Tải file tại `http://localhost:5173/orders` (hoặc `/staging`).
   - **Đoạn 2 (0:24):** Mở `/staging` và click vào dòng hàng để thấy tính năng chỉnh sửa nhanh (Inline Edit) và gợi ý mã SKU từ RAG.
   - **Đoạn 3 (0:38):** Mở màn hình phê duyệt di động tại `http://localhost:5173/m/orders/PO-10428`, xem các cảnh báo và bấm **[Phê Duyệt]** kèm lý do ngoại lệ.
   - **Đoạn 4 (0:45):** Mở `/erp-sync` để thấy sự kiện Transactional Outbox chuyển sang `EXPORTED` với mã đối soát MISA/SAP.
   - **Đoạn 5 (0:52):** Mở `/reports` quay cận cảnh 4 thẻ KPI chỉ số tiết kiệm giờ làm việc và bấm nút **"Xuất CSV Báo cáo"**.
