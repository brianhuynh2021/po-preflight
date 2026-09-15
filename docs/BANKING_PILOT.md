# Banking Preflight — Pilot tiền kiểm giải ngân doanh nghiệp

## Phạm vi đã triển khai

Mở `/banking` từ mục **Hồ sơ giải ngân**. Module nhận dữ liệu nhập tay, chạy luật
xác định trên backend và hiển thị lỗi kèm căn cứ đối chiếu. Bộ luật `BANK-PILOT-1`
là giả định minh họa; chưa phải chính sách cấp tín dụng của ngân hàng nào.

### Dùng thử

1. Chạy backend với cấu hình đăng nhập hiện có:
   `.venv/bin/python -m uvicorn preflight.api.app:app --app-dir src --host 127.0.0.1 --port 8001`.
2. Từ `apps/web`, chạy `npm run dev`, đăng nhập portal và mở `/banking`.
   Để tắt cổng debug khi kiểm tra cục bộ:
   `PREFLIGHT_DISABLE_INSPECTOR=1 npm run dev -- --hostname 127.0.0.1 --port 5187`.
3. Chọn **Nạp hồ sơ mẫu**, rồi **Kiểm tra hồ sơ**.
4. Mẫu đề nghị 850 triệu; hạn mức còn lại và hóa đơn còn lại đều 800 triệu.
   Kết quả phải là `Blocked`, với hai lỗi vượt giá trị.
5. Sửa đề nghị thành 800 triệu và kiểm tra lại: `Ready`.
6. Bỏ chọn Hợp đồng mua bán: `Blocked`. Với đủ chứng từ và đề nghị 800 triệu,
   đổi ngày hạn mức về hôm qua: `Review required`.
7. Mở **Xem căn cứ đối chiếu**, hoặc tải hồ sơ và kết quả JSON.

Ngày hạn mức và hóa đơn mẫu lấy theo ngày hiện tại tại Việt Nam. Hồ sơ nằm trong
bộ nhớ trang và mất khi tải lại. Sửa dữ liệu sẽ xóa kết quả cũ. Lỗi API được hiển
thị, không giả lập thành công. Module không gọi AI, lưu hồ sơ, gửi bot hay ghi core banking.

## Quy tắc BANK-PILOT-1

| Mã | Điều kiện | Mức độ |
|---|---|---|
| DOCUMENTS_MISSING | Thiếu đề nghị giải ngân, HĐ tín dụng, HĐ mua bán hoặc hóa đơn trong checklist | Chặn |
| CONTRACT_EXPIRED | Ngày cuối hiệu lực HĐ tín dụng trước ngày kiểm tra | Chặn |
| LIMIT_SNAPSHOT_STALE | Ngày chốt hạn mức trước ngày kiểm tra | Cần xem xét |
| LIMIT_SNAPSHOT_FUTURE | Ngày chốt hạn mức sau ngày kiểm tra | Chặn |
| LIMIT_EXCEEDED | Đề nghị vượt max(0, hạn mức − dư nợ) | Chặn |
| INVOICES_MISSING | Không có dòng dữ liệu hóa đơn | Chặn |
| DUPLICATE_INVOICE | Trùng MST bên bán và số hóa đơn trong cùng hồ sơ | Chặn |
| BENEFICIARY_MISMATCH | MST bên bán khác MST bên thụ hưởng | Chặn |
| BORROWER_MISMATCH | MST bên mua khác MST khách hàng vay | Chặn |
| INVOICE_FUTURE | Ngày hóa đơn sau ngày kiểm tra | Chặn |
| INVOICE_BALANCE_EXCEEDED | Đề nghị vượt tổng giá trị còn lại của hóa đơn qua kiểm tra | Chặn |

Hóa đơn sai bên mua/bán, nằm trong tương lai hoặc bản trùng không được cộng vào
giá trị còn lại. Mỗi hóa đơn còn lại = giá trị hóa đơn − phần đã tài trợ.
Phần đã tài trợ lớn hơn hóa đơn, số âm, NaN, vô cực, phần lẻ VND, trường lạ và
ngoại tệ đều bị từ chối với HTTP 422. Giới hạn 100 hóa đơn/hồ sơ,
200 ký tự/trường văn bản, 15 chữ số cho mỗi giá trị tiền đầu vào và tổng giá trị
hóa đơn để giữ độ chính xác khi hiển thị trên frontend.

Ngày kiểm tra lấy từ server theo `Asia/Ho_Chi_Minh`; HĐ còn hiệu lực trong ngày
hết hạn. Tiền được so sánh chính xác bằng Decimal; bằng ngưỡng được chấp nhận.
Không lỗi = `Ready`; chỉ warning = `Review required`; có error = `Blocked`.

## API và dữ liệu

- `POST /api/v1/banking/analyze`, yêu cầu session/API key hiện có, tối thiểu VIEWER.
- Schema: `src/preflight/banking.py`; TypeScript: `apps/web/app/lib/types.ts`.
- Tiền truyền JSON dạng chuỗi; frontend chỉ chuyển số để hiển thị.
- `findings[].fields` chỉ vị trí dữ liệu; `evidence` chứa giá trị đối chiếu và nguồn
  tài liệu do người nhập cung cấp. Đây không phải bằng chứng đã xác thực bằng OCR.
- Kết quả tải về chứa hồ sơ, kết quả, ngày kiểm tra và phiên bản luật;
  không phải chứng thư kiểm toán và không có chữ ký số.

## Giới hạn và bước tiếp theo

`Ready` chỉ xác nhận dữ liệu cung cấp qua được bộ kiểm tra mẫu. Chưa kiểm tra
tính thật của chứng từ, số tài khoản thụ hưởng, điều kiện giải ngân chi tiết,
KYC/AML, tài sản bảo đảm, phần giữ chỗ hạn mức hay khoản tài trợ ở hồ sơ/ngân hàng khác.
Kiểm tra trùng chỉ thực hiện trong payload hiện tại.

Để triển khai pilot có lưu trữ và xử lý hồ sơ thực tế, cần chốt với ngân hàng:

1. Sản phẩm vay, checklist, nguồn dữ liệu, chính sách ngoại lệ có phiên bản.
2. Hồ sơ nhiều chứng từ; OCR được chấp thuận và vị trí bằng chứng gốc.
3. Lưu trữ theo đơn vị, lịch sử phiên bản và phân quyền truy cập từng hồ sơ.
4. Người lập/người duyệt độc lập, kể cả admin; phê duyệt gắn với phiên bản hồ sơ.
5. Audit lưu giữ độc lập, SSO/MFA và các kiểm soát triển khai của ngân hàng.
6. Đọc dữ liệu hạn mức trước; đối soát/idempotency trước khi ghi hệ thống đích.

Đo thời gian kiểm tra, tỷ lệ bỏ sót lỗi, cảnh báo sai và số lượt bổ sung chứng từ
trên tập hồ sơ được cán bộ nghiệp vụ gán nhãn.

## Kiểm tra

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -p 'test_banking*.py'
./scripts/test.sh
# Tu apps/web: kiem tra tuong tac UI voi API gia lap, desktop va mobile.
npx playwright test --config playwright.banking.config.ts
```
