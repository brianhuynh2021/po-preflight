# TÀI LIỆU GIẢI ĐÁP AN NINH & KỸ THUẬT — PO PREFLIGHT (SECURITY & TECHNICAL Q&A)

> **Dành cho:** Kế toán trưởng, Giám đốc CNTT (CIO/CTO), Trưởng ban Kiểm soát nội bộ và Chuyên viên An toàn thông tin.  
> **Mục tiêu:** Trả lời trung thực, minh bạch 20 câu hỏi trọng yếu về an ninh, bảo mật, tính toàn vẹn dữ liệu và kết nối ERP của hệ thống **PO Preflight**.

---

## 🔒 NHÓM 1: BẢO MẬT, QUYỀN RIÊNG TƯ & PHÁP LÝ (NGHỊ ĐỊNH 13 & ON-PREMISE)

### Câu 1: Dữ liệu đơn hàng, thông tin khách hàng và bảng giá của chúng tôi có bị gửi ra máy chủ nước ngoài (OpenAI/Google Cloud) không?
**Trả lời thật:**  
**Không.** Hệ thống PO Preflight được thiết kế theo nguyên tắc ưu tiên xử lý nội bộ (Local-first):
- Toàn bộ khâu đối soát quy tắc nghiệp vụ B2B (giá hợp đồng, tồn kho ATP, hạn mức nợ, quy cách đóng gói) chạy bằng mã Python xác định (Deterministic Zero-Token) trên máy chủ nội bộ.
- Bộ tìm kiếm ngữ nghĩa SKU đa ngữ (Tier 3 Semantic Vector) sử dụng thư viện `FastEmbed` với mô hình nhúng cục bộ `paraphrase-multilingual-MiniLM-L12-v2` chạy trực tiếp trên CPU của máy chủ, không gọi bất kỳ API bên ngoài nào.
- Chỉ duy nhất trong trường hợp tài liệu là ảnh scan chất lượng thấp cần OCR hoặc tên sản phẩm quá phức tạp (Tier 4 LLM fallback, chiếm < 4% đơn hàng), hệ thống mới gửi trích đoạn văn bản ẩn danh đến API Gemini với thỏa thuận Enterprise không lưu trữ dữ liệu huấn luyện (Zero Data Retention). Đối với gói Doanh nghiệp On-Premise, toàn bộ mô hình OCR được thay thế bằng engine nội bộ, đảm bảo 100% dữ liệu không rời khỏi mạng LAN.

### Câu 2: Hệ thống tuân thủ Nghị định 13/2023/NĐ-CP về Bảo vệ dữ liệu cá nhân tại Việt Nam như thế nào?
**Trả lời thật:**  
Hệ thống tuân thủ nghiêm ngặt các quy định của Nghị định 13/2023/NĐ-CP:
1. **Phân loại và thu nhỏ dữ liệu (Data Minimization):** Hệ thống chỉ trích xuất các trường dữ liệu cần thiết phục vụ đơn đặt hàng thương mại (Tên công ty, Mã số thuế, Địa chỉ giao hàng, Mã SKU, Đơn giá, Số lượng). Không lưu trữ thông tin nhạy cảm không liên quan.
2. **Kiểm soát truy cập dựa trên vai trò (RBAC):** Dữ liệu đơn hàng chỉ được hiển thị cho người dùng có thẩm quyền phân công (`SALES_ADMIN`, `MANAGER`, `DIRECTOR`, `AUDITOR`).
3. **Quyền được lãng quên & Ẩn danh hóa:** Hỗ trợ quy trình ẩn danh hóa thông tin định danh cá nhân (PII Scrubber) khi đơn hàng hết thời hạn lưu trữ theo luật kế toán.

### Câu 3: Doanh nghiệp chúng tôi có thể triển khai giải pháp hoàn toàn On-Premises trên máy chủ riêng không?
**Trả lời thật:**  
**Có.** PO Preflight hỗ trợ đóng gói đầy đủ dưới dạng Docker Compose hoặc Kubernetes Helm Chart để triển khai độc lập trong mạng nội bộ (On-Premises) hoặc Private Cloud (Viettel IDC, VNPT, FPT Cloud):
- Hỗ trợ cơ sở dữ liệu SQLite (WAL mode) nhẹ nhàng cho Edge deployment hoặc PostgreSQL cluster cho tải lớn.
- Không yêu cầu kết nối Internet liên tục ngoại trừ trường hợp muốn nhận thông báo qua Telegram/Zalo Bot (có thể thay thế bằng Webhook nội bộ hoặc Email nội bộ).

### Câu 4: Dữ liệu đơn hàng khi lưu trữ (At-Rest) và khi truyền tải (In-Transit) được mã hóa bằng thuật toán gì?
**Trả lời thật:**  
- **Khi truyền tải (In-Transit):** Toàn bộ giao tiếp giữa trình duyệt, ứng dụng di động và API Gateway bắt buộc qua giao thức **TLS 1.3** với bộ mã hóa mạnh (ECDHE-RSA-AES128-GCM-SHA256).
- **Khi lưu trữ (At-Rest):** Cơ sở dữ liệu và tệp đính kèm được mã hóa ở cấp độ lưu trữ bằng chuẩn **AES-256**. Mật khẩu người dùng được băm một chiều bằng thuật toán chống bẻ khóa tiên tiến nhất hiện nay là **Argon2id** kèm muối ngẫu nhiên (Salt).

### Câu 5: Nhà cung cấp phần mềm có quyền truy cập vào đơn hàng của chúng tôi sau khi bàn giao không?
**Trả lời thật:**  
**Hoàn toàn không.** Trong mô hình On-Premise hoặc Dedicated Cloud bàn giao cho khách hàng:
- Toàn bộ thông tin tài khoản quản trị cao nhất (`admin`) do khách hàng nắm giữ và có thể đổi mật khẩu ngay sau khi bàn giao.
- Khóa bí mật JWT (`SECRET_KEY`), chuỗi kết nối cơ sở dữ liệu nằm trong biến môi trường của máy chủ khách hàng. Đội ngũ kỹ thuật của chúng tôi chỉ truy cập hỗ trợ khi có sự đồng ý bằng văn bản và giám sát trực tiếp qua phiên kết nối bảo mật (SSH/AnyDesk có ghi hình).

---

## 📜 NHÓM 2: TÍNH TOÀN VẸN DỮ LIỆU & KIỂM TOÁN KẾ TOÁN (AUDIT TRAIL & SOD)

### Câu 6: Chuỗi băm SHA-256 (Cryptographic Hash Chain) hoạt động như thế nào để chứng minh dữ liệu không bị sửa lén?
**Trả lời thật:**  
Mỗi khi có một sự kiện quan trọng xảy ra (tiếp nhận đơn, bóc tách dòng hàng, quyết định duyệt của quản lý, lệnh xuất sang ERP), hệ thống tính toán một giá trị băm theo công thức:
$$\text{Block\_Hash}_n = \text{SHA256}(\text{Block\_Hash}_{n-1} + \text{Timestamp} + \text{Actor\_ID} + \text{Payload\_Content})$$
Mỗi khối dữ liệu được xích chặt với khối liền trước đó. Điều này tạo nên một chuỗi chứng thư mật mã học bất biến: Bất kỳ hành vi chỉnh sửa lén nội dung của bất kỳ đơn hàng nào trong quá khứ cũng sẽ làm sai lệch toàn bộ mã băm của các khối tiếp theo, lập tức bị phát hiện khi hệ thống quét kiểm tra tính toàn vẹn (`verify_chain`).

### Câu 7: Nếu một quản trị viên IT nội bộ can thiệp thẳng vào cơ sở dữ liệu SQL để sửa số tiền, hệ thống phát hiện ra sao?
**Trả lời thật:**  
Khi kiểm toán viên hoặc kế toán trưởng truy cập trang **Chứng thư nhật ký kiểm toán** (`/audit-certificate` hoặc gọi API `GET /api/v1/audit/verify`), hệ thống sẽ duyệt tuần tự từ khối đầu tiên đến khối mới nhất:
- Nếu ai đó dùng lệnh `UPDATE analyses SET total = ...` trực tiếp trong SQL, mã băm SHA-256 của khối đó sẽ không khớp với dữ liệu thực tế.
- Hệ thống lập tức báo đỏ cảnh báo: `"Dữ liệu bị can thiệp trái phép tại khối #ID!"` và chỉ đích danh dòng dữ liệu đã bị sửa đổi.

### Câu 8: Cơ chế Phân tách trách nhiệm (Separation of Duties - SoD) ngăn chặn gian lận nội bộ như thế nào?
**Trả lời thật:**  
Hệ thống cài đặt quy tắc SoD nghiêm ngặt ở mức tầng API (`src/preflight/security/rbac.py`):
- **Quy tắc 1 (Tự phê duyệt):** Nhân viên tạo đơn hàng (`sales_admin`) tuyệt đối không thể tự phê duyệt đơn hàng do chính mình tạo ra (`403 Forbidden: Creator cannot approve their own submission`).
- **Quy tắc 2 (Hạn mức thẩm quyền):** Đơn hàng có giá trị dưới 50 triệu VND do `MANAGER` phê duyệt. Đơn hàng từ 50 triệu VND trở lên hoặc có ngoại lệ nợ xấu bắt buộc phải do cấp `DIRECTOR` phê duyệt.
- **Quy tắc 3 (Đơn bị Blocked):** Đơn hàng bị xếp loại `Blocked` (vi phạm nghiêm trọng) bị khóa cứng, không một vai trò nào có thể bấm duyệt trực tiếp nếu chưa qua khâu chỉnh sửa dòng hàng hợp lệ tại Staging.

### Câu 9: Nhân viên Sales Admin có thể "qua mặt" hệ thống để duyệt đơn hàng cho đại lý quen không?
**Trả lời thật:**  
**Không thể.** Mọi hành động duyệt đều phải đi qua cổng API `/api/v1/orders/{id}/decide`. Cổng này kiểm tra phiên đăng nhập, vai trò RBAC và ghi nhận định danh người duyệt vào chuỗi băm SHA-256. Nếu tài khoản không đủ thẩm quyền, hệ thống trả về lỗi `403 Forbidden` và ghi lại nhật ký an ninh.

### Câu 10: Làm thế nào để kế toán trưởng hoặc kiểm toán viên độc lập xuất hồ sơ giải trình cho một đơn hàng cụ thể?
**Trả lời thật:**  
Tại bất kỳ thời điểm nào, kế toán có thể:
1. Truy cập chi tiết đơn hàng trên Web Portal và bấm nút **"Xuất Chứng Thư Kiểm Toán"**.
2. Tải về chứng thư số chứa: Toàn bộ lịch sử từ file PO gốc, ảnh chụp bóc tách, danh sách cảnh báo vi phạm, danh tính người duyệt kèm chữ ký băm SHA-256.
3. Hoặc tải file đối soát tổng hợp `po_preflight_pilot_report.csv` từ trang `/reports` phục vụ kiểm toán thuế.

---

## ⚙️ NHÓM 3: KẾT NỐI ERP & TÍNH ỔN ĐỊNH VẬN HÀNH (INTEGRATION & RELIABILITY)

### Câu 11: Nếu đường truyền Internet hoặc máy chủ ERP (MISA/Odoo/SAP) bị mất kết nối đột ngột thì đơn hàng có bị mất không?
**Trả lời thật:**  
**Không bao giờ.** PO Preflight áp dụng mô hình kiến trúc chuẩn doanh nghiệp **Transactional Outbox Pattern**:
- Khi đơn hàng được duyệt, một sự kiện xuất kho được lưu vào bảng `erp_outbox` trong cùng một giao dịch cơ sở dữ liệu cục bộ với trạng thái `PENDING`.
- Một tiến trình nền định kỳ quét hàng đợi và gửi sang ERP. Nếu ERP tạm thời không thể kết nối, hệ thống kích hoạt cơ chế thử lại tự động theo hàm mũ (Exponential Backoff with Jitter) lên đến 5 lần.
- Dữ liệu luôn an toàn trên hệ thống Preflight cho đến khi nhận được mã xác nhận giao dịch thành công từ ERP.

### Câu 12: Làm thế nào để bảo đảm không bao giờ xảy ra tình trạng ghi nhận trùng 2 lần đơn hàng vào ERP?
**Trả lời thật:**  
Hệ thống sử dụng cơ chế **Khóa phân tán & Khóa chống trùng lặp (Idempotency Key)**:
- Mỗi sự kiện đồng bộ ERP mang một mã khóa duy nhất được sinh ra từ mã đơn hàng và chu kỳ phê duyệt: `hash(po_number + approval_timestamp)`.
- Phía ERP Adapter kiểm tra nếu mã khóa này đã từng được ghi nhận trong bảng `erp_sync_history`, hệ thống sẽ lập tức trả về kết quả thành công của giao dịch trước đó mà không tạo thêm chứng từ mới.

### Câu 13: Phần mềm có can thiệp trực tiếp vào cấu trúc cơ sở dữ liệu gốc của ERP (như viết lệnh SQL trực tiếp) không?
**Trả lời thật:**  
**Tuyệt đối không.** Chúng tôi tuân thủ nguyên tắc an toàn phần mềm: Không bao giờ can thiệp trực tiếp (Direct DB Write) vào bảng SQL của các phần mềm kế toán như MISA AMIS, Bravo, Fast hay SAP.
- Mọi tương tác đều đi qua **Cổng giao tiếp chính thức (OpenAPI / REST API / SDK)** được các hãng ERP cung cấp và cấp quyền riêng biệt.
- Điều này loại bỏ hoàn toàn nguy cơ làm sai lệch dữ liệu tài chính, hỏng khóa ngoại (Foreign Key) hoặc vi phạm chính sách bảo hành của hãng ERP.

### Câu 14: Nếu khách hàng gửi 2 email trùng lặp cùng một file PO trong vòng 5 phút, hệ thống xử lý như thế nào?
**Trả lời thật:**  
Động cơ tiền kiểm có 2 tầng chặn trùng lặp:
1. **Tầng 1 (Exact PO Match):** Nếu mã số PO đã tồn tại trong cơ sở dữ liệu, hệ thống tự động gán cờ vi phạm mức nghiêm trọng `DUPLICATE_PO` và chuyển trạng thái sang `Blocked`.
2. **Tầng 2 (Fuzzy Duplicate):** Nếu mã đơn khác nhau nhưng trùng khớp khách hàng, ngày đặt và tổng số tiền trong vòng 24 giờ, hệ thống gắn cờ cảnh báo `POSSIBLE_DUPLICATE` để người quản lý lưu ý trước khi bấm duyệt.

### Câu 15: Tốc độ xử lý bóc tách và đối soát luật trung bình là bao lâu? Có bị nghẽn khi tiếp nhận hàng loạt không?
**Trả lời thật:**  
- Đối với file Excel hoặc JSON/CSV: Thời gian xử lý từ **0.5 đến 2.1 giây/đơn hàng**.
- Đối với file PDF scan/Ảnh chụp hóa đơn: Thời gian bóc tách qua Vision OCR từ **3 đến 5 giây/đơn hàng**.
- Hệ thống hỗ trợ xử lý hàng đợi bất đồng bộ với Redis/Celery hoặc SQLite worker, có khả năng xử lý song song hàng trăm đơn hàng cùng lúc mà không gây đơ hoặc nghẽn giao diện người dùng.

---

## 🧠 NHÓM 4: TRÍ TUỆ NHÂN TẠO & ĐỘ CHÍNH XÁC NGHIỆP VỤ (RAG & ZERO-HALLUCINATION)

### Câu 16: AI có bao giờ tự "bịa" ra mã hàng (Hallucination) khi gặp tên sản phẩm lạ hoặc khách viết sai chính tả không?
**Trả lời thật:**  
**Không bao giờ.** PO Preflight triệt tiêu hiện tượng ảo giác (Zero-Hallucination) bằng 2 cơ chế kiểm soát:
1. **Kiểm tra đối chiếu danh mục đóng (Closed-World Catalog Validation):** Bất kể mô hình AI gợi ý mã gì, hệ thống bắt buộc kiểm tra xem mã đó có tồn tại trong Master Catalog của doanh nghiệp hay không. Nếu không có trong kho, mã hàng lập tức bị đánh dấu là `UNKNOWN_SKU`.
2. **Ngưỡng tin cậy nghiêm ngặt (Confidence Threshold):** Nếu độ tin cậy so khớp dưới 70%, hệ thống không tự ý chọn bừa mà chuyển sang trạng thái `Review required` và yêu cầu nhân viên Sales Admin chọn mã chuẩn trên giao diện Staging chỉ bằng 1 cú click chuột.

### Câu 17: Bộ so khớp 4 tầng (4-Tier RAG) xử lý các từ lóng hoặc tên gọi dân dã tiếng Việt như thế nào?
**Trả lời thật:**  
Hệ thống vận hành cơ chế thác đổ 4 tầng:
- **Tier 1 (Exact Hash):** Khớp 100% mã SKU hoặc Barcode niêm yết (độ trễ <1ms).
- **Tier 2 (Lexical Fuzzy):** Sử dụng thuật toán `RapidFuzz` để bắt các lỗi gõ sai chữ cái, thiếu dấu gạch ngang, nhầm số 0 và chữ O (độ trễ ~5ms).
- **Tier 3 (Semantic Vector):** Sử dụng mô hình `FastEmbed` đa ngữ hiểu ngữ nghĩa tiếng Việt (ví dụ: đại lý ghi *"dây mạng 3m bấm sẵn"*, vector search đối soát và khớp sang mã chuẩn `CAB-CAT6-3M` với độ tin cậy 100%).
- **Tier 4 (LLM Reasoning):** Kích hoạt khi các tầng trên thất bại để đọc ngữ cảnh xung quanh dòng hàng.

### Câu 18: Làm thế nào hệ thống phát hiện các lỗi tính nhầm tiền thuế VAT hoặc sai số học từ phía khách hàng?
**Trả lời thật:**  
Hệ thống tích hợp mô-đun **Tự kiểm toán số học (Self-Reflection Math Verifier)**:
- Sau khi bóc tách, hệ thống tự nhân lại: $\text{Thành tiền từng dòng} = \text{Số lượng} \times \text{Đơn giá} - \text{Chiết khấu}$.
- Cộng dồn toàn bộ các dòng, tính thuế VAT theo tỷ lệ (8% hoặc 10%) và so sánh với trường `Tổng tiền thanh toán` mà khách hàng ghi trên PO.
- Nếu có chênh lệch dù chỉ 1.000 VNĐ, hệ thống gắn cảnh báo `MATH_CALCULATION_DISCREPANCY`, giúp kế toán phát hiện ngay lỗi tính nhầm của đại lý trước khi xuất hóa đơn.

### Câu 19: Nếu chính sách giá hợp đồng hoặc chiết khấu bậc thang của công ty tôi thay đổi giữa tháng thì cập nhật ra sao?
**Trả lời thật:**  
Rất đơn giản và tức thì:
- Quản trị viên hoặc Trưởng phòng kinh doanh có thể tải file Excel bảng giá mới vào mục **Cài đặt → Bảng giá hợp đồng** (`/rules` hoặc `/customers`).
- Hoặc hệ thống tự động đồng bộ bảng giá từ ERP theo chu kỳ.
- Ngay sau khi cập nhật, toàn bộ đơn hàng tiếp nhận từ thời điểm đó sẽ được đối soát theo bảng giá mới có hiệu lực mà không cần khởi động lại phần mềm.

### Câu 20: Chính sách sao lưu dữ liệu (Backup), phục hồi sau thảm họa (Disaster Recovery) và cam kết SLA ra sao?
**Trả lời thật:**  
- **Sao lưu tự động:** Cơ sở dữ liệu và tệp PO gốc được sao lưu tự động hàng ngày (Daily Snapshot) và lưu trữ phân tán tại 2 vùng địa lý độc lập.
- **Thời gian phục hồi mục tiêu (RTO & RPO):**
  - Thời gian phục hồi dịch vụ (RTO): Dưới **30 phút**.
  - Mức độ mất mát dữ liệu tối đa (RPO): Dưới **5 phút** nhờ cơ chế Write-Ahead Logging (WAL).
- **Cam kết dịch vụ (SLA):** Đảm bảo thời gian hoạt động đạt **99.5%** đối với gói Tiêu chuẩn (Growth) và **99.9%** đối với gói Doanh nghiệp (Enterprise Dedicated). Đội ngũ hỗ trợ kỹ thuật trực tuyến 24/7 đối với các sự cố mức độ nghiêm trọng (P1).

---
*Tài liệu được ban hành bởi Ban Công Nghệ & An Toàn Thông Tin — PO Preflight / Nhật Minh Technology.*
