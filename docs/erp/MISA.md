# MISA AMIS Open API Integration Contract & Pilot Readiness

> **Status:** Paused pending sandbox credentials per Prompt C3 development protocol:  
> *"Điều kiện trước: có tài khoản sandbox MISA AMIS (hoặc ERP pilot: Bravo/Fast/Odoo). Nếu chưa có → DỪNG, không viết code 'đoán' API. Ghi vào docs/erp/MISA.md những gì cần từ khách."*

---

## 1. Pilot Readiness Checklist (Required from Client)

To connect PO Preflight directly with MISA AMIS Production/Sandbox without synthetic guesswork, the enterprise client or partner must provision the following access points:

### 1.1 API Access Credentials
- **MISA API Gateway URL**: Official Open API gateway (e.g., `https://openapi.misa.vn` or dedicated tenant sandbox endpoint).
- **Application ID (`MISA_APP_ID`)**: Client application identifier registered in MISA Developer Portal.
- **Client Secret / Access Token (`MISA_ACCESS_TOKEN`)**:
  - For Sandbox testing: A static long-lived token or OAuth2 client credentials (`client_id`, `client_secret`).
  - Token refresh endpoint if using OAuth2 authorization code flow.
- **Company Code / Tenant ID**: Unique identifier for the client's MISA accounting workspace (`company_code` or `db_id`).

### 1.2 Master Data Pre-requisites
- **Customer Mapping (`account_object`)**:
  - Field convention used for tax identification (`tax_code` vs `account_object_code`).
  - Policy flag: Is PO Preflight permitted to automatically insert new customers if missing, or must it pause in `review_required`?
- **SKU Mapping (`inventory_item`)**:
  - Primary SKU field (`inventory_item_code`).
  - Base Unit of Measure (UOM) definitions (`unit_id` / `unit_name`).
- **Warehouse Location (`stock`)**:
  - Default receiving warehouse code for new sales orders (`stock_code`).

---

## 2. Target API Specification & Mapping

Once sandbox credentials are supplied, PO Preflight will map verified purchase orders into MISA Sales Orders (`sa_order` / `sa_order_detail`):

### 2.1 Voucher Header Mapping (`sa_order`)

| PO Preflight Field | MISA AMIS Voucher Field | Type | Description / Fallback |
| :--- | :--- | :--- | :--- |
| `po_number` | `ref_no` / `reference_no` | string | Original PO reference number |
| `customer` | `account_object_code` / `tax_code` | string | Resolved via customer tax code / code |
| `id` | `note` | string | `"PO Preflight #{order_id}"` for traceability |
| `created_at` | `voucher_date` / `order_date` | ISO date | Creation date of order voucher |
| `currency` | `currency_id` | string | ISO currency code (`VND`, `USD`) |
| `total` | `total_amount` | decimal | Gross order total verified by Preflight math |

### 2.2 Voucher Detail Line Mapping (`sa_order_detail`)

| PO Preflight Line Field | MISA AMIS Detail Field | Type | Description |
| :--- | :--- | :--- | :--- |
| `line_number` | `sort_order` | int | 1-indexed line position |
| `sku` | `inventory_item_code` | string | Mapped warehouse item code |
| `description` / `name` | `inventory_item_name` | string | Item display title |
| `uom` | `unit_name` | string | Base or conversion unit of measure |
| `quantity` | `quantity` | decimal | Ordered item quantity |
| `unit_price` | `unit_price` | decimal | Agreed contract price |
| `discount_rate` | `discount_rate` | decimal | Discount % (if applicable) |
| `tax_rate` | `vat_rate` | decimal | VAT % (e.g., 8% or 10%) |

---

## 3. Sandboxed Contract Testing Protocol

When `MISA_SANDBOX_TOKEN` and `MISA_API_URL` are provided:
1. **End-to-End Sales Order Creation**:
   - Post an order with 3 distinct SKUs to MISA sandbox.
   - Read back the created voucher via MISA GET endpoint.
   - Assert exact mathematical and field-level parity (PO number, customer tax code, quantities, unit prices, line totals).
2. **Idempotency Guarantee**:
   - Re-send identical payload with the same `idempotency_key`.
   - Verify that MISA returns HTTP 200/409 with the existing transaction ID without duplicating vouchers.
3. **Fault Tolerance & Circuit Breaking**:
   - Simulate network timeouts and verify transactional outbox lease recovery resets status to `PENDING` without dropping records.

---

## 4. Hourly Reconciliation Engine

Prompt C3 requires continuous audit alignment between PO Preflight outbox and the ERP:
- A cron job (`preflight.erp.reconciliation`) runs every hour.
- Queries all outbox events marked `SENT` in the last 24 hours.
- Calls MISA voucher inquiry API to verify:
  1. Voucher still exists in MISA (not deleted manually).
  2. Voucher total matches Preflight recorded total.
- If divergence is detected:
  - Records a system finding `RECONCILIATION_MISMATCH` in the database.
  - Surfaces warning in `/api/v1/admin/health` and `/overview`.
  - Dispatches immediate alert to admin via Telegram/Zalo.

---

## 5. UI Integration

- **ERP Sync Outbox Page (`/erp-sync`)**:
  - Displays direct deep-link to the created MISA voucher: `https://amisapp.misa.vn/sa/order/{transaction_id}`.
  - Provides a **"Đối soát ngay"** (Reconcile Now) button calling `POST /api/v1/erp/reconcile` for manual operational checks.
