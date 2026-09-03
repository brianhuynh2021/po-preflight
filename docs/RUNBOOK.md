# Operations Runbook — PO Preflight

This runbook outlines operational procedures for running, debugging, monitoring, and maintaining the **PO Preflight** B2B Order Intake & Verification Gateway in staging and production environments.

---

## 1. Tracing Errors with `request_id`

Every HTTP request to PO Preflight is assigned a unique `request_id` (propagated via the `X-Request-ID` header, returned in error problem details JSON, logged in structured JSON logs, and persisted in audit trail blocks).

### From UI Error Toast to Root Cause

1. **Capture the Request ID**:
   - In the web application, error toasts and the `/admin/health` dashboard display the exact `request_id` (e.g. `c7a4b89f` or UUID).
   - In API error responses (RFC 7807 Problem Details), extract `instance: "urn:uuid:<request_id>"`.

2. **Querying Admin Health & Server Error Log**:
   - Navigate to `/admin/health` in the frontend (or call `GET /api/v1/admin/health` as an Admin).
   - Locate the matching `request_id` under **10 Lỗi Server 5xx Gần Nhất**. Click **Chi tiết** to view the full traceback without needing SSH access.

3. **Searching Centralized Logs (ELK / CloudWatch / Datadog)**:
   - If structured JSON logging is enabled (`PREFLIGHT_LOG_FORMAT=json`), query:
     ```json
     { "request_id": "c7a4b89f" }
     ```
   - All log lines emitted by the request pipeline, rules engine, and ERP workers will be correlated.

4. **Inspecting Audit Trail History**:
   - Query the Merkle audit trail for the order to verify if state was recorded before the failure:
     ```bash
     curl -H "Authorization: Bearer $ADMIN_TOKEN" https://preflight.company.internal/api/v1/audit/blocks/PO-10428
     ```

---

## 2. Resolving ERP Outbox `DEAD_LETTER` Events

When an outbound synchronization to SAP, Odoo, or MISA AMIS fails repeatedly (exceeding `MAX_RETRIES = 3`), the event is marked `DEAD_LETTER` to prevent blocking subsequent orders.

### Diagnostic & Recovery Workflow

1. **Inspect Dead-Lettered Outbox Events**:
   ```bash
   curl -H "Authorization: Bearer $ADMIN_TOKEN" https://preflight.company.internal/api/v1/erp/outbox
   ```
   Filter events where `"status": "DEAD_LETTER"`. Check `"last_error"` (e.g., `Invalid Customer Tax ID`, `HTTP 503 Upstream Timeout`, `SKU mapping missing in ERP`).

2. **Fix Upstream Data / Connection**:
   - If the error is due to an invalid customer alias or master SKU, correct it in `/customers` or `/catalog`.
   - If the error is an ERP network outage, ensure the ERP endpoint is reachable.

3. **Re-trigger Synchronization**:
   - Call the sync endpoint with the order ID to re-enqueue and dispatch:
     ```bash
     curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
          https://preflight.company.internal/api/v1/erp/sync/10428
     ```

---

## 3. Secret & JWT Key Rotation

PO Preflight signs session tokens using HMAC-SHA256 with `PREFLIGHT_SECRET_KEY` (or `PREFLIGHT_JWT_SECRET`).

### Zero-Downtime Secret Rotation Procedure

1. **Deploy New Secondary Secret**:
   - Set `PREFLIGHT_SECRET_KEY_NEW` with the new 32+ character random hex string while keeping `PREFLIGHT_SECRET_KEY` active.
2. **Switch Primary Secret**:
   - Update `PREFLIGHT_SECRET_KEY` to the new secret and remove the old key during the maintenance window.
   - Active users will re-authenticate via `/login` and obtain new secure JWT session cookies.

---

## 4. Database Backup & Restore

### SQLite (Local & Single-Node Deployment)

- **Backup using SQLite Online Backup API / VACUUM INTO**:
  ```bash
  sqlite3 runtime/preflight.db "VACUUM INTO 'backups/preflight-backup-$(date +%Y%m%d%H%M%S).db';"
  ```
- **Restore from Backup**:
  ```bash
  # Stop the service
  pkill -f "preflight.api"
  # Replace DB
  cp backups/preflight-backup-YYYYMMDD.db runtime/preflight.db
  # Restart service
  ./scripts/run.sh
  ```

### PostgreSQL (Enterprise Deployment)

- **Backup**:
  ```bash
  pg_dump -Fc -h $PGHOST -U $PGUSER -d $PGDATABASE -f backups/preflight_pg_$(date +%Y%m%d%H%M%S).dump
  ```
- **Restore**:
  ```bash
  pg_restore -h $PGHOST -U $PGUSER -d $PGDATABASE --clean --if-exists backups/preflight_pg_YYYYMMDD.dump
  ```

---

## 5. Prometheus Metrics Reference

| Metric Name | Type | Description | Alert Threshold |
| :--- | :--- | :--- | :--- |
| `po_preflight_uptime_seconds` | Counter | Service uptime in seconds | Process restart alert |
| `po_preflight_http_requests_total` | Counter | Total HTTP requests by method, path, status | Error rate > 1% over 5m |
| `po_preflight_http_request_duration_seconds` | Summary | Request latency quantiles (P50, P90, P99) | P99 > 2.0s |
| `po_preflight_orders_processed_total` | Counter | Orders processed by status & risk level | Anomaly drop |
| `po_preflight_findings_total` | Counter | Findings detected by violation code & severity | High spike in `PRICE_MISMATCH` |
| `po_preflight_outbox_pending_count` | Gauge | Number of events awaiting ERP sync | > 20 for > 15m |
| `po_preflight_outbox_pending_max_age_seconds` | Gauge | Age of oldest pending outbox event | > 300s (5m) |
| `po_preflight_sku_resolutions_total` | Counter | SKU resolution count by tier | LLM fallback ratio > 15% |
| `po_preflight_erp_sync_total` | Counter | ERP sync count by adapter & status | Failure count > 5 |

---

## 6. Email Intake (Tiếp nhận PO qua Email)

Khách hàng gửi PO tới một hộp thư; hệ thống đọc tệp đính kèm, khớp khách hàng
theo địa chỉ người gửi, chạy bộ quy tắc preflight và trả lời tự động bằng
tiếng Việt.

### 6.1 Biến môi trường

| Biến | Bắt buộc | Mặc định | Ghi chú |
|---|---|---|---|
| `EMAIL_INTAKE_ENABLED` | | `false` | Bật/tắt tính năng |
| `IMAP_HOST` | ✅ | — | Không đặt ⇒ bỏ qua việc quét hộp thư |
| `IMAP_PORT` | | `993` | |
| `IMAP_USER` / `IMAP_PASSWORD` | ✅ | — | Gmail/Workspace phải dùng **App Password** |
| `IMAP_FOLDER` | | `INBOX` | |
| `IMAP_SSL` | | `true` | |
| `SMTP_HOST` | ✅ | — | Không đặt ⇒ chỉ ghi log, **không gửi mail thật** |
| `SMTP_PORT` | | `587` | |
| `SMTP_USER` / `SMTP_PASSWORD` | | — | |
| `SMTP_FROM` | | `noreply@preflight.vn` | Nên là địa chỉ có thật của công ty |
| `SMTP_SSL` | | `false` | `false` ⇒ dùng STARTTLS |
| `EMAIL_POLL_INTERVAL` | | `120` | Giây, chỉ dùng cho chế độ `--loop` |
| `EMAIL_DRY_RUN` | | `false` | `true` ⇒ chỉ đọc: **không gửi mail, không đánh dấu đã đọc** |
| `EMAIL_ALLOWED_SENDERS` | | — | Danh sách email (phân cách bằng dấu phẩy). Chỉ xử lý thư từ các địa chỉ này, thư khác bỏ qua hoàn toàn |

> **Chạy thử với hộp thư có sẵn:** luôn đặt `EMAIL_DRY_RUN=true` và
> `EMAIL_ALLOWED_SENDERS` trước. Hệ thống coi **mọi thư chưa đọc** là PO cần
> xử lý, nên nếu trỏ vào hộp thư cá nhân mà không giới hạn, bạn bè và đối tác
> của bạn sẽ nhận được mail tự động "vui lòng gửi lại đơn hàng".

> **Lưu ý:** hộp thư dùng cho intake nên là hộp thư **riêng** (vd
> `po@congty.vn`), không dùng chung với hộp thư cá nhân — mọi thư chưa đọc
> trong đó đều bị coi là PO cần xử lý.

### 6.2 Vận hành

```bash
# Quét một lần (dùng cho cron)
preflight intake email --once

# Chạy liên tục, tự quét theo EMAIL_POLL_INTERVAL
preflight intake email --loop

# Giới hạn số thư mỗi lần quét (mặc định 20)
preflight intake email --once --max-messages 50
```

Qua API (cần quyền `sales_admin`):

```bash
curl -X POST "$API/api/v1/intake/email/poll?max_messages=20" -H "X-API-Key: $KEY"
curl "$API/api/v1/intake/email/status" -H "X-API-Key: $KEY"
curl "$API/api/v1/intake/email/logs?limit=50" -H "X-API-Key: $KEY"
```

### 6.3 Trạng thái thư trong `email_inbox_logs`

| Trạng thái | Ý nghĩa | Đánh dấu đã đọc? | Có trả lời khách? |
|---|---|---|---|
| `PROCESSED` | Tất cả tệp đính kèm đã tạo đơn | ✅ | ✅ Xác nhận |
| `PARTIAL` | Một phần tệp lỗi, phần còn lại đã tạo đơn | ✅ | ✅ Nêu rõ tệp lỗi |
| `IGNORED` | Không có tệp hợp lệ, **hoặc** là thư tự động | ✅ | Chỉ khi không phải thư tự động |
| `ERROR` | Không bóc tách được tệp nào | ❌ (để thử lại) | ✅ Báo không nhận được |
| `GAVE_UP` | Đã thử `MAX_PROCESSING_ATTEMPTS` (3) lần | ✅ | ❌ |
| `DUPLICATE` | Đã xử lý trước đó (theo `Message-ID`) | ✅ | ❌ |
| `SKIPPED` | Người gửi ngoài `EMAIL_ALLOWED_SENDERS` | ❌ | ❌ |

### 6.4 Cơ chế an toàn

- **Chống vòng lặp thư:** không bao giờ trả lời thư từ `MAILER-DAEMON`,
  `noreply`, thư có `Auto-Submitted`/`Precedence: bulk` hoặc `List-Id`. Thư
  gửi đi mang `Auto-Submitted: auto-replied` để phía đối tác không trả lời lại.
- **Chống nghẽn hàng đợi:** mỗi lần quét dành phần lớn hạn ngạch cho thư
  **chưa từng xử lý**, phần còn lại để thử lại thư cũ. Nhờ đó một đống thư
  hỏng tồn đọng không làm đơn hàng mới bị kẹt.
- **Giới hạn tài nguyên:** tệp > 25 MB bị bỏ qua; tối đa 20 tệp/thư; IMAP và
  SMTP đều có timeout 30 giây.
- **Idempotency:** khóa theo `Message-ID`, nên quét lại không tạo đơn trùng.

### 6.5 Xử lý sự cố

| Hiện tượng | Nguyên nhân thường gặp | Cách xử lý |
|---|---|---|
| `imap_configured: false` | Thiếu `IMAP_HOST`/`IMAP_USER` | Đặt biến môi trường rồi khởi động lại |
| Quét ra 0 thư dù hộp thư có mail | Thư đã ở trạng thái đã đọc | Chỉ thư **chưa đọc** mới được lấy; đánh dấu chưa đọc để xử lý lại |
| Khách báo không nhận được mail | `SMTP_HOST` chưa đặt | Khi thiếu, hệ thống chỉ ghi log chứ không gửi thật |
| Nhiều thư `GAVE_UP` | Khách gửi sai định dạng | Xem `error_message` trong `/logs`, liên hệ khách, gửi lại `PO_MAU.xlsx` |
| Đơn có cảnh báo `CUSTOMER_UNRESOLVED` | Email người gửi chưa khai báo | Thêm địa chỉ vào `contact_emails` của khách hàng tương ứng |
