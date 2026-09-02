"""SQLAlchemy Core Relational Schema v2 Definitions.

Defines all tables using SQLAlchemy Core (no ORM session) for clean, high-performance,
and fully transactional data persistence across SQLite and PostgreSQL.
"""

from __future__ import annotations

from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    BigInteger,
    String,
    Text,
    Numeric,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    func,
)

metadata = MetaData()

# -----------------------------------------------------------------------------
# 1. Multi-Tenant Organization & User Access Control
# -----------------------------------------------------------------------------
organizations = Table(
    "organizations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("code", String(64), unique=True, nullable=False, index=True),
    Column("name", String(255), nullable=False),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("org_id", Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("username", String(128), unique=True, nullable=False, index=True),
    Column("display_name", String(255), nullable=False),
    Column("email", String(255), nullable=True),
    Column("password_hash", String(255), nullable=True),
    Column("role", String(64), nullable=False, default="VIEWER"),
    Column("is_active", Boolean, nullable=False, default=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)

api_keys = Table(
    "api_keys",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("key_hash", String(128), unique=True, nullable=False, index=True),
    Column("label", String(128), nullable=False),
    Column("last_used_at", DateTime(timezone=True), nullable=True),
    Column("revoked_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)

channel_identities = Table(
    "channel_identities",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("channel", String(64), nullable=False),  # telegram, zalo
    Column("external_id", String(128), nullable=False),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    UniqueConstraint("channel", "external_id", name="uq_channel_identity"),
)

# -----------------------------------------------------------------------------
# 2. Customers & Catalog Products (Relational Master Data)
# -----------------------------------------------------------------------------
customers = Table(
    "customers",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("org_id", Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("code", String(64), nullable=False, index=True),
    Column("name", String(255), nullable=False),
    Column("normalized_name", String(255), nullable=False, index=True),
    Column("tax_code", String(64), nullable=True),
    Column("tier", String(64), nullable=True, default="STANDARD"),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    UniqueConstraint("org_id", "code", name="uq_customer_org_code"),
)

customer_aliases = Table(
    "customer_aliases",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("customer_id", Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("alias_normalized", String(255), nullable=False),
    UniqueConstraint("customer_id", "alias_normalized", name="uq_customer_alias"),
)

products = Table(
    "products",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("org_id", Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("sku", String(128), nullable=False, index=True),
    Column("name", String(255), nullable=False),
    Column("unit_price", Numeric(18, 4), nullable=False),
    Column("stock", Integer, nullable=False, default=0),
    Column("active", Boolean, nullable=False, default=True),
    Column("base_uom", String(32), nullable=False, default="PCS"),
    Column("moq", Integer, nullable=False, default=1),
    Column("pack_size", Integer, nullable=False, default=1),
    Column("category", String(128), nullable=True),
    Column("barcode", String(64), nullable=True),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    UniqueConstraint("org_id", "sku", name="uq_product_org_sku"),
)

uom_conversions = Table(
    "uom_conversions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("product_id", Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True),
    Column("sku", String(128), nullable=True, index=True),
    Column("uom_code", String(32), nullable=False),
    Column("base_uom", String(32), nullable=True),
    Column("factor", Numeric(12, 4), nullable=True),
    Column("conversion_factor", String(32), nullable=True),
)

customer_prices = Table(
    "customer_prices",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("customer_id", Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("product_id", Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("contract_price", Numeric(18, 4), nullable=False),
    Column("min_quantity", Integer, nullable=False, default=1),
    Column("discount_percent", Numeric(5, 2), nullable=False, default=0),
    Column("valid_from", DateTime(timezone=True), nullable=True),
    Column("valid_to", DateTime(timezone=True), nullable=True),
)

customer_credits = Table(
    "customer_credits",
    metadata,
    Column("customer_id", Integer, ForeignKey("customers.id", ondelete="CASCADE"), primary_key=True),
    Column("credit_limit", Numeric(18, 2), nullable=False, default=0),
    Column("outstanding_balance", Numeric(18, 2), nullable=False, default=0),
    Column("overdue_balance", Numeric(18, 2), nullable=False, default=0),
    Column("oldest_overdue_days", Integer, nullable=False, default=0),
    Column("status", String(32), nullable=False, default="GOOD"),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    Column("source", String(64), nullable=False, default="MANUAL"),
)

# -----------------------------------------------------------------------------
# 3. Orders, Lines, Findings & Decision Workflow
# -----------------------------------------------------------------------------
orders = Table(
    "orders",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("org_id", Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("customer_id", Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=True, index=True),
    Column("po_number", String(128), nullable=False, index=True),
    Column("revision", Integer, nullable=False, default=1),
    Column("supersedes_order_id", Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True),
    Column("status", String(64), nullable=False, default="received", index=True),
    Column("rule_status", String(64), nullable=False, default="ready_for_approval", index=True),
    Column("currency", String(16), nullable=False, default="VND"),
    Column("subtotal", Numeric(18, 4), nullable=False, default=0),
    Column("tax_amount", Numeric(18, 4), nullable=False, default=0),
    Column("grand_total", Numeric(18, 4), nullable=False, default=0),
    Column("source_file", String(255), nullable=True),
    Column("source_path", String(512), nullable=True),
    Column("source_channel", String(64), nullable=False, default="web_upload"),
    Column("created_by", String(128), nullable=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False, index=True),
    Column("analyzed_at", DateTime(timezone=True), nullable=True),
    UniqueConstraint("org_id", "customer_id", "po_number", "revision", name="uq_org_cust_po_rev"),
)

order_lines = Table(
    "order_lines",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("order_id", Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("line_no", Integer, nullable=False),
    Column("raw_sku", String(128), nullable=True),
    Column("sku", String(128), nullable=False),
    Column("product_id", Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True),
    Column("description", Text, nullable=True),
    Column("quantity", Integer, nullable=False),
    Column("uom", String(32), nullable=False, default="PCS"),
    Column("base_quantity", Integer, nullable=False),
    Column("unit_price", Numeric(18, 4), nullable=False),
    Column("discount_percent", Numeric(5, 2), nullable=False, default=0),
    Column("discount_amount", Numeric(18, 4), nullable=False, default=0),
    Column("tax_rate", Numeric(5, 2), nullable=False, default=0),
    Column("is_promo", Boolean, nullable=False, default=False),
    Column("line_total", Numeric(18, 4), nullable=False),
)

findings = Table(
    "findings",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("order_id", Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("line_id", Integer, ForeignKey("order_lines.id", ondelete="CASCADE"), nullable=True, index=True),
    Column("code", String(64), nullable=False, index=True),
    Column("severity", String(32), nullable=False, index=True),
    Column("message", Text, nullable=False),
    Column("evidence_json", Text, nullable=True),
)

decisions = Table(
    "decisions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("order_id", Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=True, index=True),
    Column("po_number", String(128), nullable=True, index=True),
    Column("decision", String(64), nullable=False, index=True),
    Column("actor_user_id", Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    Column("actor", String(128), nullable=False),
    Column("display_name", String(255), nullable=True),
    Column("channel", String(64), nullable=False, default="web"),
    Column("note", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)

# -----------------------------------------------------------------------------
# 4. Cryptographic Audit Log & Transactional ERP Outbox
# -----------------------------------------------------------------------------
audit_blocks = Table(
    "audit_blocks",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("block_index", Integer, unique=True, nullable=False, index=True),
    Column("previous_hash", String(64), nullable=False),
    Column("block_hash", String(64), unique=True, nullable=False, index=True),
    Column("order_id", Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True),
    Column("po_number", String(128), nullable=True, index=True),
    Column("request_id", String(64), nullable=True),
    Column("timestamp", Float, nullable=False),
    Column("event_type", String(64), nullable=True, index=True),
    Column("action", String(64), nullable=True, index=True),
    Column("actor", String(128), nullable=False),
    Column("payload_json", Text, nullable=True),
    Column("payload_hash", String(64), nullable=True),
    Column("signature", String(128), nullable=True),
)

erp_outbox = Table(
    "erp_outbox",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("order_id", Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True),
    Column("idempotency_key", String(128), unique=True, nullable=False, index=True),
    Column("payload_json", Text, nullable=False),
    Column("status", String(32), nullable=False, default="PENDING", index=True),
    Column("error_detail", Text, nullable=True),
    Column("next_attempt_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    Column("processed_at", DateTime(timezone=True), nullable=True),
)

# -----------------------------------------------------------------------------
# 5. Policies, SKU Alias Learning & Leads
# -----------------------------------------------------------------------------
rule_policies = Table(
    "rule_policies",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("org_id", Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True),
    Column("policy_json", Text, nullable=False),
    Column("updated_by", String(128), nullable=True),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
)

sku_alias_learning = Table(
    "sku_alias_learning",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("customer_id", String(255), nullable=True, index=True),
    Column("raw_query", String(255), nullable=False, index=True),
    Column("target_sku", String(128), nullable=False, index=True),
    Column("confidence", Float, nullable=False, default=1.0),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)

leads = Table(
    "leads",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(255), nullable=True),
    Column("company", String(255), nullable=True),
    Column("company_name", String(255), nullable=True),
    Column("contact_person", String(255), nullable=True),
    Column("phone", String(64), nullable=False),
    Column("email", String(255), nullable=False),
    Column("erp", String(128), nullable=True),
    Column("volume", String(64), nullable=True),
    Column("daily_volume", String(64), nullable=True),
    Column("current_erp", String(128), nullable=True),
    Column("note", Text, nullable=True),
    Column("notes", Text, nullable=True),
    Column("ip_hash", String(128), nullable=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)
