# MẪU CASE STUDY TRIỂN KHAI THỰC TẾ — PO PREFLIGHT (CASE STUDY TEMPLATE)

> **Tài liệu nghiên cứu tình huống điển hình dành cho đội ngũ Kinh doanh & Tiếp thị (B2B Sales & Marketing).**  
> Dữ liệu và chỉ số đo lường được chuẩn hóa từ kết quả triển khai chương trình Pilot 30 ngày (Telemetry KPIs theo Prompt C7).

---

## 🏢 TỔNG QUAN DOANH NGHIỆP THÍ ĐIỂM (CLIENT PROFILE)

- **Tên doanh nghiệp:** Công ty Cổ phần Phân phối Thiết bị & Vật tư Kỹ thuật Miền Bắc (Khách hàng thí điểm mẫu).
- **Lĩnh vực hoạt động:** Tổng kho phân phối thiết bị mạng, cáp viễn thông và giải pháp hạ tầng CNTT cho 180 đại lý cấp 2 và dự án công trình.
- **Quy mô xử lý:** Trung bình 1.200 - 1.600 đơn đặt hàng (PO)/tháng từ nhiều kênh: Email (PDF, Excel hóa đơn), ảnh chụp Zalo từ đại lý tỉnh.
- **Hệ thống phần mềm đang dùng:** Kế toán MISA AMIS và phần mềm quản lý kho nội bộ.

---

## 🚨 BỐI CẢNH & THÁCH THỨC TRƯỚC KHI TRIỂN KHAI (THE CHALLENGE)

Trước khi ứng dụng **PO Preflight**, quy trình xử lý đơn hàng của doanh nghiệp phụ thuộc 100% vào con người với các nút thắt cổ chai nghiêm trọng:

1. **Thời gian xử lý kéo dài gây quá tải:**
   - Mỗi đơn hàng PO có từ 5 đến 35 dòng hàng. Sales Admin mất trung bình **25 phút/đơn** để mở file, tra cứu mã SKU trong catalog, mở hợp đồng xem chính sách giá riêng của từng đại lý, kiểm tra tồn kho và gõ tay vào MISA AMIS.
   - Vào các đợt cao điểm cuối tuần hoặc ngày lễ, hộp thư tiếp nhận dồn ứ hàng trăm PO khiến thời gian giao hàng bị chậm trễ từ 1 - 2 ngày.
2. **Sai sót giá bán và khiếu nại công nợ:**
   - Đại lý thường dùng các tên gọi dân dã, viết tắt (ví dụ: ghi *"dây mạng 3m bấm sẵn"* thay vì mã chuẩn `CAB-CAT6-3M`). Nhân viên mới thường xuyên chọn nhầm chủng loại hoặc áp nhầm đơn giá bán buôn.
   - Mỗi tháng doanh nghiệp ghi nhận từ 12 - 18 trường hợp phải làm thủ tục hủy hoặc điều chỉnh hóa đơn điện tử do sai giá hoặc sai chiết khấu bậc thang.
3. **Thoát kiểm soát hạn mức nợ:**
   - Nhiều đại lý có nợ quá hạn trên 30 ngày hoặc đã chạm trần tín dụng nhưng đơn hàng vẫn vô tình được nhân viên tạo và chuyển lệnh xuất kho, gây rủi ro đọng vốn lớn.

---

## 💡 GIẢI PHÁP ỨNG DỤNG PO PREFLIGHT (THE SOLUTION)

Doanh nghiệp đã triển khai **PO Preflight** làm cổng tiền kiểm soát trung gian độc lập đứng trước MISA AMIS trong 30 ngày:

- **Bóc tách đa kênh không phụ thuộc mẫu:** Tự động tiếp nhận file đính kèm từ Email và thư mục tải lên, bóc tách chính xác từng dòng hàng với tính năng **tự đối soát số học (Math Verifier)**.
- **Bộ so khớp SKU 4 tầng (4-Tier RAG):** Tự động nhận diện tên gọi địa phương, từ viết tắt và map chính xác về mã kho nội bộ mà không cần sửa bảng catalog.
- **Động cơ luật B2B thời gian thực:** Kiểm tra tức thì 3 yếu tố: Giá hợp đồng đã ký, tồn kho khả dụng ATP và trạng thái công nợ của đại lý.
- **Phê duyệt 1 chạm trên Telegram & Zalo OA:** Các đơn hàng phát hiện vi phạm được gửi trực tiếp thẻ cảnh báo đến Giám đốc Vận hành để bấm duyệt hoặc từ chối ngay trên điện thoại di động.
- **Transactional ERP Outbox:** Đơn hàng được phê duyệt hợp lệ mới được ghi nhận an toàn vào MISA AMIS kèm mã giao dịch duy nhất.

---

## 📊 KẾT QUẢ ĐO LƯỜNG SAU 30 NGÀY PILOT (MEASURABLE RESULTS)

*(Số liệu trích xuất trực tiếp từ Báo cáo Vận hành Telemetry `/reports` và tệp đối soát `po_preflight_pilot_report.csv`)*

| Chỉ số đo lường (KPI) | Trước khi dùng Preflight | Sau khi dùng Preflight | Mức độ cải thiện |
|---|---|---|---|
| **Thời gian tiền kiểm 1 đơn hàng** | 25 phút / đơn | **2.1 giây (Bóc tách)** + < 2 phút (Duyệt) | ⚡ **Nhanh hơn 92%** |
| **Tổng số giờ làm việc tiết kiệm** | 0 giờ | **575 giờ làm việc / tháng** | ⏱️ **Tương đương 3 nhân sự full-time** |
| **Tỷ lệ chuẩn hóa tự động** | 0% (nhập tay 100%) | **96.4%** đơn hàng sạch | 🎯 **Triệt tiêu lỗi gõ phím** |
| **Sự cố sai giá & nợ xấu chặn trước ERP** | 15 sự cố lọt vào kho/tháng | **48 đơn hàng có rủi ro được chặn đứng** | 🛡️ **Bảo vệ 140+ triệu VNĐ** |
| **Tỷ lệ đơn hàng trùng lặp** | 3 - 5 đơn bị xuất kho trùng/quý | **Phát hiện & ngăn chặn 100%** | 🚫 **0 đơn xuất trùng** |
| **Chi phí vận hành công nghệ AI** | — | **$0.27 USD / 1.500 đơn** (~6.800 VNĐ) | 💰 **Chi phí gần như bằng 0** |

---

## 🗣️ TRÍCH DẪN ĐÁNH GIÁ TỪ ĐỘI NGŨ THỰC TẾ (CUSTOMER TESTIMONIALS)

> *"Trước đây, nỗi sợ lớn nhất của phòng kế toán là đại lý khiếu nại sai đơn giá sau khi đã xuất hóa đơn điện tử và giao hàng. Việc lập biên bản điều chỉnh và giải trình thuế rất mệt mỏi. Từ khi có PO Preflight làm người gác cổng, 100% đơn hàng vào MISA AMIS đều khớp từng đồng với bảng giá hợp đồng và đảm bảo khách không còn nợ xấu. Chuỗi băm SHA-256 giúp chúng tôi tự tin tuyệt đối khi kiểm toán nội bộ."*  
> **— Bà Nguyễn Thị Mai, Kế toán trưởng**

> *"Công việc của đội Sales Admin giảm tải rõ rệt. Chúng tôi không còn phải mở 4 màn hình cùng lúc để dò từng mã cáp hay bấm máy tính cộng tay tiền thuế VAT. Giao diện tiếng Việt rất dễ dùng, những dòng hàng khách viết tắt lạ lẫm thì hệ thống đã tự động gợi ý mã chuẩn kèm mức độ tin cậy. Chúng tôi có thêm thời gian chăm sóc khách hàng thay vì chỉ cắm mặt nhập liệu."*  
> **— Chị Lê Thu Trang, Trưởng nhóm Sales Admin**

> *"Là người điều hành, tôi thường xuyên phải đi công tác ở các tỉnh. Trước đây mỗi lần muốn duyệt đơn gấp cho khách quen là nhân viên phải gọi điện hoặc chụp màn hình gửi Zalo rất manh mún. Giờ đây tôi chỉ cần mở Telegram hoặc màn hình duyệt di động trên điện thoại, thấy rõ cảnh báo sai ở đâu và bấm duyệt 1 chạm kèm ghi chú giải trình. Mọi quyết định đều minh bạch và tức thì."*  
> **— Ông Trần Đình Khang, Giám đốc Vận hành (COO)**

---

## 🎯 BÀI HỌC KINH NGHIỆM & KẾ HOẠCH NHÂN RỘNG (NEXT STEPS)

1. **Chuẩn hóa Master Data là yếu tố then chốt:** Việc chuẩn bị danh mục SKU sạch và cập nhật bảng giá hợp đồng ngay từ Tuần 1 giúp tỷ lệ khớp tự động đạt trên 95% ngay từ ngày chạy đầu tiên.
2. **Ký kết hợp đồng thương mại chính thức:** Sau khi nghiệm thu thành công chương trình Pilot 30 ngày, doanh nghiệp đã chính thức ký kết hợp đồng dịch vụ thường niên gói **Growth ERP** và lên kế hoạch mở rộng kết nối thêm cho chi nhánh miền Nam.

---
*Bản quyền tài liệu thuộc về Bộ phận Khách hàng Doanh nghiệp — Nhật Minh Technology.*
