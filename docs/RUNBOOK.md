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
