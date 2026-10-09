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
   - Locate the matching `request_id` under **10 Lỗi Server 5xx Gần Nhất** (10 Most Recent 5xx Server Errors). Click **Chi tiết** (Details) to view the full traceback without needing SSH access.

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

## 6. Email Intake (Receiving POs via Email)

Customers send POs to a mailbox; the system reads the attachments, matches the
customer by sender address, runs the preflight rule set and replies
automatically in Vietnamese.

### 6.1 Environment variables

| Variable | Required | Default | Notes |
|---|---|---|---|
| `EMAIL_INTAKE_ENABLED` | | `false` | Enables/disables the feature |
| `IMAP_HOST` | ✅ | — | If unset ⇒ mailbox polling is skipped |
| `IMAP_PORT` | | `993` | |
| `IMAP_USER` / `IMAP_PASSWORD` | ✅ | — | Gmail/Workspace must use an **App Password** |
| `IMAP_FOLDER` | | `INBOX` | |
| `IMAP_SSL` | | `true` | |
| `SMTP_HOST` | ✅ | — | If unset ⇒ log only, **no real email is sent** |
| `SMTP_PORT` | | `587` | |
| `SMTP_USER` / `SMTP_PASSWORD` | | — | |
| `SMTP_FROM` | | `noreply@preflight.vn` | Should be a real company address |
| `SMTP_SSL` | | `false` | `false` ⇒ use STARTTLS |
| `EMAIL_POLL_INTERVAL` | | `120` | Seconds, used only in `--loop` mode |
| `EMAIL_DRY_RUN` | | `false` | `true` ⇒ read-only: **no email is sent, nothing is marked as read** |
| `EMAIL_ALLOWED_SENDERS` | | — | Comma-separated list of email addresses. Only emails from these addresses are processed; all other emails are ignored completely |

> **Trial runs with an existing mailbox:** always set `EMAIL_DRY_RUN=true` and
> `EMAIL_ALLOWED_SENDERS` first. The system treats **every unread email** as a
> PO to be processed, so if you point it at a personal mailbox without
> restrictions, your friends and partners will receive automatic emails saying
> "please resend your order".

> **Note:** the mailbox used for intake should be a **dedicated** mailbox (e.g.
> `po@company.vn`), not shared with a personal mailbox — every unread email in
> it is treated as a PO to be processed.

### 6.2 Operations

```bash
# Run a single poll (for use with cron)
preflight intake email --once

# Run continuously, polling every EMAIL_POLL_INTERVAL
preflight intake email --loop

# Limit the number of emails per poll (default 20)
preflight intake email --once --max-messages 50
```

Via the API (requires the `sales_admin` permission):

```bash
curl -X POST "$API/api/v1/intake/email/poll?max_messages=20" -H "X-API-Key: $KEY"
curl "$API/api/v1/intake/email/status" -H "X-API-Key: $KEY"
curl "$API/api/v1/intake/email/logs?limit=50" -H "X-API-Key: $KEY"
```

### 6.3 Email statuses in `email_inbox_logs`

| Status | Meaning | Marked as read? | Reply to customer? |
|---|---|---|---|
| `PROCESSED` | All attachments created orders | ✅ | ✅ Confirmation |
| `PARTIAL` | Some attachments failed, the rest created orders | ✅ | ✅ Lists the failed files |
| `IGNORED` | No valid attachments, **or** it is an automated email | ✅ | Only if it is not an automated email |
| `ERROR` | No attachment could be extracted | ❌ (left for retry) | ✅ Tells the customer the order could not be received |
| `GAVE_UP` | `MAX_PROCESSING_ATTEMPTS` (3) attempts were made | ✅ | ❌ |
| `DUPLICATE` | Already processed before (by `Message-ID`) | ✅ | ❌ |
| `SKIPPED` | Sender is not in `EMAIL_ALLOWED_SENDERS` | ❌ | ❌ |

### 6.4 Safety mechanisms

- **Mail-loop prevention:** never replies to emails from `MAILER-DAEMON`,
  `noreply`, emails with `Auto-Submitted`/`Precedence: bulk`, or `List-Id`.
  Outgoing emails carry `Auto-Submitted: auto-replied` so the counterparty does
  not reply back.
- **Queue-starvation prevention:** each poll reserves most of its quota for
  emails that have **never been processed** and uses the remainder to retry old
  emails. This way a backlog of broken emails does not leave new orders stuck.
- **Resource limits:** files > 25 MB are skipped; at most 20 files per email;
  IMAP and SMTP both have a 30-second timeout.
- **Idempotency:** keyed by `Message-ID`, so re-polling does not create
  duplicate orders.

### 6.5 Troubleshooting

| Symptom | Common cause | Resolution |
|---|---|---|
| `imap_configured: false` | `IMAP_HOST`/`IMAP_USER` missing | Set the environment variables, then restart |
| Poll returns 0 emails even though the mailbox has mail | The emails are already marked as read | Only **unread** emails are fetched; mark them as unread to process them again |
| Customer reports not receiving the email | `SMTP_HOST` is not set | When it is missing, the system only logs and does not actually send |
| Many `GAVE_UP` emails | Customer sent the wrong format | Check `error_message` in `/logs`, contact the customer, resend the `PO_MAU.xlsx` template |
| Order has the warning `CUSTOMER_UNRESOLVED` | Sender's email is not registered | Add the address to `contact_emails` of the corresponding customer |
