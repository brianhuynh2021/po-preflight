from __future__ import annotations

import abc
import json
import os
import sqlite3
import threading
import time
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from preflight.api.errors import ConfigurationError
from preflight.models import (
    Analysis,
    CustomerCreditProfile,
    CustomerMaster,
    CustomerPriceAgreement,
    InventorySnapshot,
    RulePolicy,
    UOMConversion,
    User,
)
from preflight.security.password import hash_password
from preflight.utils.text import normalize_vietnamese_name

from preflight.security.audit_chain import calculate_hash, compute_payload_hash




SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    po_number TEXT NOT NULL,
    customer TEXT NOT NULL,
    status TEXT NOT NULL,
    total TEXT NOT NULL,
    source_file TEXT NOT NULL,
    order_json TEXT NOT NULL,
    findings_json TEXT NOT NULL,
    revision INTEGER DEFAULT 1,
    supersedes_order_id INTEGER NULL,
    requested_changes TEXT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_analyses_po ON analyses(po_number);
CREATE INDEX IF NOT EXISTS idx_analyses_cust_po ON analyses(customer, po_number);
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    po_number TEXT NOT NULL,
    decision TEXT NOT NULL,
    actor TEXT NOT NULL,
    note TEXT NOT NULL,
    display_name TEXT,
    channel TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS channel_identities (
    channel TEXT NOT NULL,
    external_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY(channel, external_id)
);
CREATE TABLE IF NOT EXISTS channel_link_codes (
    code TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL,
    expires_at REAL NOT NULL,
    used INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS processed_webhook_events (
    channel TEXT NOT NULL,
    event_id TEXT NOT NULL,
    processed_at REAL NOT NULL,
    PRIMARY KEY(channel, event_id)
);
CREATE TABLE IF NOT EXISTS sku_alias_learning (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    raw_query TEXT NOT NULL,
    target_sku TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    UNIQUE(customer_id, raw_query)
);
CREATE INDEX IF NOT EXISTS idx_sku_alias_learning ON sku_alias_learning(customer_id, raw_query);

CREATE TABLE IF NOT EXISTS product_embeddings (
    sku TEXT PRIMARY KEY,
    vector_blob BLOB NOT NULL,
    text_hash TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_product_embeddings_sku ON product_embeddings(sku);

CREATE TABLE IF NOT EXISTS audit_blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    block_index INTEGER NOT NULL,
    timestamp REAL NOT NULL,
    po_number TEXT NOT NULL,
    action TEXT NOT NULL,
    actor TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    previous_hash TEXT NOT NULL,
    block_hash TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_blocks_po ON audit_blocks(po_number);

CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    company TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT NOT NULL,
    erp TEXT,
    volume TEXT,
    note TEXT,
    ip_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_leads_created ON leads(created_at DESC);


CREATE TABLE IF NOT EXISTS customer_pricing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    sku TEXT NOT NULL,
    contract_price TEXT NOT NULL,
    min_quantity INTEGER NOT NULL DEFAULT 1,
    discount_percent TEXT NOT NULL DEFAULT '0',
    valid_from TEXT,
    valid_to TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(customer_id, sku, min_quantity)
);
CREATE INDEX IF NOT EXISTS idx_customer_pricing ON customer_pricing(customer_id, sku);

CREATE TABLE IF NOT EXISTS uom_conversions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL,
    uom_code TEXT NOT NULL,
    base_uom TEXT NOT NULL,
    conversion_factor TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(sku, uom_code)
);
CREATE INDEX IF NOT EXISTS idx_uom_conversions ON uom_conversions(sku, uom_code);

CREATE TABLE IF NOT EXISTS customer_credits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL UNIQUE,
    credit_limit TEXT NOT NULL,
    outstanding_balance TEXT NOT NULL DEFAULT '0',
    overdue_balance TEXT NOT NULL DEFAULT '0',
    oldest_overdue_days INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_customer_credits ON customer_credits(customer_id);

CREATE TABLE IF NOT EXISTS rule_policies (
    id INTEGER PRIMARY KEY,
    policy_json TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    updated_by TEXT NOT NULL DEFAULT 'system'
);

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    tax_code TEXT,
    tier TEXT NOT NULL DEFAULT 'STANDARD',
    contact_emails TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_customers_code ON customers(code);
CREATE INDEX IF NOT EXISTS idx_customers_norm_name ON customers(normalized_name);
CREATE INDEX IF NOT EXISTS idx_customers_tax ON customers(tax_code);

CREATE TABLE IF NOT EXISTS customer_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    alias TEXT NOT NULL,
    normalized_alias TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(customer_id, normalized_alias)
);
CREATE INDEX IF NOT EXISTS idx_customer_aliases_norm ON customer_aliases(normalized_alias);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id TEXT NOT NULL DEFAULT 'org_default',
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    email TEXT NOT NULL,
    password_hash TEXT,
    role TEXT NOT NULL DEFAULT 'viewer',
    is_active INTEGER NOT NULL DEFAULT 1,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT NOT NULL,
    key_hash TEXT NOT NULL UNIQUE,
    label TEXT,
    last_used_at TEXT,
    revoked_at TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);

CREATE TABLE IF NOT EXISTS inventory_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL,
    warehouse TEXT NOT NULL DEFAULT 'DEFAULT',
    on_hand NUMERIC NOT NULL DEFAULT 0,
    reserved NUMERIC NOT NULL DEFAULT 0,
    as_of TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'odoo',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_inventory_snapshots_sku ON inventory_snapshots(sku);
CREATE INDEX IF NOT EXISTS idx_inventory_snapshots_as_of ON inventory_snapshots(as_of DESC);

CREATE TABLE IF NOT EXISTS erp_outbox (
    event_id TEXT PRIMARY KEY,
    po_number TEXT NOT NULL,
    customer TEXT NOT NULL,
    total_amount REAL NOT NULL,
    currency TEXT NOT NULL,
    idempotency_key TEXT UNIQUE NOT NULL,
    payload_json TEXT NOT NULL,
    status TEXT NOT NULL,
    retry_count INTEGER NOT NULL DEFAULT 0,
    transaction_id TEXT,
    adapter_type TEXT,
    last_error TEXT,
    next_attempt_at REAL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_erp_outbox_status ON erp_outbox(status);
CREATE INDEX IF NOT EXISTS idx_erp_outbox_idemp ON erp_outbox(idempotency_key);
CREATE INDEX IF NOT EXISTS idx_erp_outbox_po ON erp_outbox(po_number);

CREATE TABLE IF NOT EXISTS request_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    error_message TEXT NOT NULL,
    traceback TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_request_errors_created ON request_errors(created_at DESC);

CREATE TABLE IF NOT EXISTS email_inbox_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT UNIQUE NOT NULL,
    sender TEXT NOT NULL,
    subject TEXT NOT NULL,
    received_at TEXT NOT NULL,
    attachments_count INTEGER NOT NULL DEFAULT 0,
    orders_created INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL,
    error_message TEXT,
    attempts INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_email_inbox_msg_id ON email_inbox_logs(message_id);
"""


POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS analyses (
    id SERIAL PRIMARY KEY,
    po_number VARCHAR(128) NOT NULL,
    customer VARCHAR(255) NOT NULL,
    status VARCHAR(64) NOT NULL,
    total VARCHAR(64) NOT NULL,
    source_file VARCHAR(512) NOT NULL,
    order_json JSONB NOT NULL,
    findings_json JSONB NOT NULL,
    revision INT DEFAULT 1,
    supersedes_order_id INT NULL,
    requested_changes TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_pg_analyses_po ON analyses(po_number);
CREATE INDEX IF NOT EXISTS idx_pg_analyses_cust_po ON analyses(customer, po_number);


CREATE TABLE IF NOT EXISTS decisions (
    id SERIAL PRIMARY KEY,
    po_number VARCHAR(128) NOT NULL,
    decision VARCHAR(64) NOT NULL,
    actor VARCHAR(255) NOT NULL,
    note TEXT NOT NULL,
    display_name VARCHAR(255),
    channel VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS channel_identities (
    channel VARCHAR(64) NOT NULL,
    external_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    role VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(channel, external_id)
);

CREATE TABLE IF NOT EXISTS channel_link_codes (
    code VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    role VARCHAR(64) NOT NULL,
    expires_at DOUBLE PRECISION NOT NULL,
    used INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS processed_webhook_events (
    channel VARCHAR(64) NOT NULL,
    event_id VARCHAR(255) NOT NULL,
    processed_at DOUBLE PRECISION NOT NULL,
    PRIMARY KEY(channel, event_id)
);

CREATE TABLE IF NOT EXISTS sku_alias_learning (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(255) NOT NULL,
    raw_query VARCHAR(512) NOT NULL,
    target_sku VARCHAR(128) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, raw_query)
);
CREATE INDEX IF NOT EXISTS idx_pg_sku_alias_learning ON sku_alias_learning(customer_id, raw_query);

CREATE TABLE IF NOT EXISTS product_embeddings (
    sku VARCHAR(128) PRIMARY KEY,
    vector_blob BYTEA NOT NULL,
    text_hash VARCHAR(64) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_pg_product_embeddings_sku ON product_embeddings(sku);

CREATE TABLE IF NOT EXISTS audit_blocks (
    id SERIAL PRIMARY KEY,
    block_index INTEGER NOT NULL,
    timestamp DOUBLE PRECISION NOT NULL,
    po_number VARCHAR(128) NOT NULL,
    action VARCHAR(64) NOT NULL,
    actor VARCHAR(255) NOT NULL,
    payload_hash VARCHAR(64) NOT NULL,
    previous_hash VARCHAR(64) NOT NULL,
    block_hash VARCHAR(64) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pg_audit_blocks_po ON audit_blocks(po_number);

CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    phone VARCHAR(64) NOT NULL,
    email VARCHAR(255) NOT NULL,
    erp VARCHAR(128),
    volume VARCHAR(128),
    note TEXT,
    ip_hash VARCHAR(128) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_pg_leads_created ON leads(created_at DESC);


CREATE TABLE IF NOT EXISTS customer_pricing (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(255) NOT NULL,
    sku VARCHAR(128) NOT NULL,
    contract_price VARCHAR(64) NOT NULL,
    min_quantity INTEGER NOT NULL DEFAULT 1,
    discount_percent VARCHAR(64) NOT NULL DEFAULT '0',
    valid_from VARCHAR(64),
    valid_to VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, sku, min_quantity)
);
CREATE INDEX IF NOT EXISTS idx_pg_customer_pricing ON customer_pricing(customer_id, sku);

CREATE TABLE IF NOT EXISTS uom_conversions (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(128) NOT NULL,
    uom_code VARCHAR(64) NOT NULL,
    base_uom VARCHAR(64) NOT NULL,
    conversion_factor VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(sku, uom_code)
);
CREATE INDEX IF NOT EXISTS idx_pg_uom_conversions ON uom_conversions(sku, uom_code);

CREATE TABLE IF NOT EXISTS customer_credits (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(255) NOT NULL UNIQUE,
    credit_limit VARCHAR(64) NOT NULL,
    outstanding_balance VARCHAR(64) NOT NULL DEFAULT '0',
    overdue_balance VARCHAR(64) NOT NULL DEFAULT '0',
    oldest_overdue_days INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(64) NOT NULL DEFAULT 'ACTIVE',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_pg_customer_credits ON customer_credits(customer_id);

CREATE TABLE IF NOT EXISTS rule_policies (
    id INT PRIMARY KEY,
    policy_json JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255) NOT NULL DEFAULT 'system'
);

CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    code VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    normalized_name VARCHAR(255) NOT NULL,
    tax_code VARCHAR(64),
    tier VARCHAR(32) NOT NULL DEFAULT 'STANDARD',
    contact_emails TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_pg_customers_code ON customers(code);
CREATE INDEX IF NOT EXISTS idx_pg_customers_norm_name ON customers(normalized_name);
CREATE INDEX IF NOT EXISTS idx_pg_customers_tax ON customers(tax_code);

CREATE TABLE IF NOT EXISTS customer_aliases (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(64) NOT NULL,
    alias VARCHAR(255) NOT NULL,
    normalized_alias VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, normalized_alias)
);
CREATE INDEX IF NOT EXISTS idx_pg_customer_aliases_norm ON customer_aliases(normalized_alias);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    org_id VARCHAR(64) NOT NULL DEFAULT 'org_default',
    username VARCHAR(128) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash TEXT,
    role VARCHAR(32) NOT NULL DEFAULT 'viewer',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_pg_users_username ON users(username);

CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    username VARCHAR(128) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    label VARCHAR(255),
    last_used_at TIMESTAMP WITH TIME ZONE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_pg_api_keys_hash ON api_keys(key_hash);

CREATE TABLE IF NOT EXISTS inventory_snapshots (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(128) NOT NULL,
    warehouse VARCHAR(128) NOT NULL DEFAULT 'DEFAULT',
    on_hand NUMERIC NOT NULL DEFAULT 0,
    reserved NUMERIC NOT NULL DEFAULT 0,
    as_of TIMESTAMP WITH TIME ZONE NOT NULL,
    source VARCHAR(64) NOT NULL DEFAULT 'odoo',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_pg_inventory_snapshots_sku ON inventory_snapshots(sku);

CREATE TABLE IF NOT EXISTS erp_outbox (
    event_id VARCHAR(64) PRIMARY KEY,
    po_number VARCHAR(128) NOT NULL,
    customer VARCHAR(255) NOT NULL,
    total_amount DOUBLE PRECISION NOT NULL,
    currency VARCHAR(16) NOT NULL,
    idempotency_key VARCHAR(128) UNIQUE NOT NULL,
    payload_json JSONB NOT NULL,
    status VARCHAR(32) NOT NULL,
    retry_count INTEGER NOT NULL DEFAULT 0,
    transaction_id VARCHAR(128),
    adapter_type VARCHAR(64),
    last_error TEXT,
    next_attempt_at DOUBLE PRECISION,
    created_at DOUBLE PRECISION NOT NULL,
    updated_at DOUBLE PRECISION NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pg_erp_outbox_status ON erp_outbox(status);
CREATE INDEX IF NOT EXISTS idx_pg_erp_outbox_idemp ON erp_outbox(idempotency_key);
CREATE INDEX IF NOT EXISTS idx_pg_erp_outbox_po ON erp_outbox(po_number);

CREATE TABLE IF NOT EXISTS request_errors (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(64) NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    status_code INTEGER NOT NULL,
    error_message TEXT NOT NULL,
    traceback TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_pg_request_errors_created ON request_errors(created_at DESC);

CREATE TABLE IF NOT EXISTS email_inbox_logs (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(255) UNIQUE NOT NULL,
    sender VARCHAR(255) NOT NULL,
    subject VARCHAR(512) NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE NOT NULL,
    attachments_count INTEGER NOT NULL DEFAULT 0,
    orders_created INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(32) NOT NULL,
    error_message TEXT,
    attempts INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_pg_email_inbox_msg_id ON email_inbox_logs(message_id);
"""



class BaseAuditStore(abc.ABC):
    """Abstract interface defining required audit store persistence capabilities."""

    @abc.abstractmethod
    def close(self) -> None:
        pass

    def __enter__(self) -> BaseAuditStore:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @abc.abstractmethod
    def has_po(self, po_number: str, customer: str | None = None) -> bool:
        pass

    @abc.abstractmethod
    def get_order_by_po(self, po_number: str, customer: str | None = None) -> dict[str, Any] | None:
        pass

    @abc.abstractmethod
    def get_order_revisions(self, po_number: str, customer: str | None = None) -> list[dict[str, Any]]:
        pass

    @abc.abstractmethod
    def get_recent_customer_orders(self, customer: str, days: int = 14) -> list[dict[str, Any]]:
        pass

    @abc.abstractmethod
    def mark_superseded(self, order_id: int) -> None:
        pass

    @abc.abstractmethod
    def record_analysis(self, analysis: Analysis, source_file: str) -> int:
        pass

    @abc.abstractmethod
    def record_received_order(
        self,
        po_number: str,
        customer: str,
        source_file: str,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        pass

    @abc.abstractmethod
    def update_analysis(self, order_id: int, analysis: Analysis) -> None:
        pass

    @abc.abstractmethod
    def create_channel_link_code(
        self, user_id: str, display_name: str, role: str, expires_in_seconds: int = 600
    ) -> str:
        pass

    @abc.abstractmethod
    def consume_channel_link_code(self, code: str) -> dict[str, Any] | None:
        pass

    @abc.abstractmethod
    def record_processed_webhook_event(self, channel: str, event_id: str) -> bool:
        pass

    @abc.abstractmethod
    def save_product_embedding(self, sku: str, vector_bytes: bytes, text_hash: str) -> None:
        pass

    @abc.abstractmethod
    def get_product_embeddings(self) -> list[dict[str, Any]]:
        pass

    @abc.abstractmethod
    def get_product_embedding(self, sku: str) -> dict[str, Any] | None:
        pass

    @abc.abstractmethod
    def record_decision(
        self,
        po_number: str,
        decision: str,
        actor: str,
        note: str = "",
        display_name: str | None = None,
        channel: str | None = None,
    ) -> int:
        pass

    @abc.abstractmethod
    def get_channel_identity(self, channel: str, external_id: str) -> dict[str, Any] | None:
        pass

    @abc.abstractmethod
    def upsert_channel_identity(
        self,
        channel: str,
        external_id: str,
        user_id: str,
        display_name: str,
        role: str,
    ) -> None:
        pass


    @abc.abstractmethod
    def history(self, po_number: str) -> dict[str, list[dict[str, object]]]:
        pass

    @abc.abstractmethod
    def list_orders(
        self,
        status: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
        include_superseded: bool = False,
    ) -> list[dict[str, Any]]:
        pass

    @abc.abstractmethod
    def get_order(self, po_or_id: str | int) -> dict[str, Any] | None:
        pass

    @abc.abstractmethod
    def get_dashboard_stats(self) -> dict[str, Any]:
        pass

    @abc.abstractmethod
    def learn_alias(
        self,
        customer_id: str,
        raw_query: str,
        target_sku: str,
        confidence: float = 1.0,
    ) -> None:
        pass

    @abc.abstractmethod
    def get_customer_alias(self, customer_id: str, raw_query: str) -> str | None:
        pass

    @abc.abstractmethod
    def list_customer_aliases(self, customer_id: str | None = None) -> list[dict[str, Any]]:
        pass

    @abc.abstractmethod
    def append_audit_block(
        self,
        po_number: str,
        action: str,
        actor: str,
        payload: dict[str, Any],
        timestamp: float | None = None,
    ) -> dict[str, Any]:
        pass

    @abc.abstractmethod
    def get_audit_blocks(self, po_number: str) -> list[dict[str, Any]]:
        pass

    @abc.abstractmethod
    def list_audit_events(
        self,
        limit: int = 50,
        offset: int = 0,
        po_number: str | None = None,
        actor: str | None = None,
        action: str | None = None,
    ) -> list[dict[str, Any]]:
        pass

    @abc.abstractmethod
    def set_customer_pricing(self, pricing: CustomerPriceAgreement) -> None:
        pass

    @abc.abstractmethod
    def get_customer_pricing(self, customer_id: str) -> list[CustomerPriceAgreement]:
        pass

    @abc.abstractmethod
    def set_uom_conversion(self, conversion: UOMConversion) -> None:
        pass

    @abc.abstractmethod
    def get_uom_conversions(self, sku: str | None = None) -> list[UOMConversion]:
        pass

    @abc.abstractmethod
    def set_customer_credit(self, credit: CustomerCreditProfile) -> None:
        pass

    @abc.abstractmethod
    def get_customer_credit(self, customer_id: str) -> CustomerCreditProfile | None:
        pass

    @abc.abstractmethod
    def set_policy(self, policy: RulePolicy, updated_by: str = "system") -> None:
        pass

    @abc.abstractmethod
    def get_policy(self) -> RulePolicy:
        pass

    @abc.abstractmethod
    def get_order_by_po(self, po_number: str) -> dict[str, Any] | None:
        pass

    @abc.abstractmethod
    def create_lead(
        self,
        name: str,
        company: str,
        phone: str,
        email: str,
        erp: str | None,
        volume: str | None,
        note: str | None,
        ip_hash: str,
    ) -> dict[str, Any]:
        pass

    @abc.abstractmethod
    def list_leads(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        pass

    @abc.abstractmethod
    def create_customer(self, customer: CustomerMaster) -> CustomerMaster:
        pass

    @abc.abstractmethod
    def get_customer(self, code: str) -> CustomerMaster | None:
        pass

    @abc.abstractmethod
    def get_customer_by_id(self, customer_id: int) -> CustomerMaster | None:
        pass

    @abc.abstractmethod
    def get_customer_by_tax_code(self, tax_code: str) -> CustomerMaster | None:
        pass

    @abc.abstractmethod
    def get_customer_by_normalized_name(self, norm_name: str) -> CustomerMaster | None:
        pass

    @abc.abstractmethod
    def list_customers(self, search: str | None = None, limit: int = 50, offset: int = 0) -> list[CustomerMaster]:
        pass

    @abc.abstractmethod
    def update_customer(self, code: str, data: dict[str, Any]) -> CustomerMaster | None:
        pass

    @abc.abstractmethod
    def delete_customer(self, code: str) -> bool:
        pass

    @abc.abstractmethod
    def add_customer_alias(self, customer_id: str, alias: str) -> None:
        pass

    @abc.abstractmethod
    def list_customer_master_aliases(self, customer_id: str | None = None) -> list[dict[str, Any]]:
        pass

    @abc.abstractmethod
    def create_user(self, user: User) -> User:
        pass

    @abc.abstractmethod
    def get_user(self, username: str) -> User | None:
        pass

    @abc.abstractmethod
    def get_user_by_id(self, user_id: int) -> User | None:
        pass

    @abc.abstractmethod
    def list_users(self) -> list[User]:
        pass

    @abc.abstractmethod
    def update_user(
        self,
        username: str,
        display_name: str | None = None,
        email: str | None = None,
        role: str | None = None,
        password_hash: str | None = None,
        is_active: bool | None = None,
    ) -> User | None:
        pass

    @abc.abstractmethod
    def delete_user(self, username: str) -> bool:
        pass

    @abc.abstractmethod
    def record_failed_login(self, username: str) -> int:
        pass

    @abc.abstractmethod
    def reset_failed_logins(self, username: str) -> None:
        pass

    @abc.abstractmethod
    def is_user_locked(self, username: str) -> bool:
        pass

    @abc.abstractmethod
    def seed_initial_admin(self) -> None:
        pass

    @abc.abstractmethod
    def record_inventory_snapshots(self, snapshots: list[InventorySnapshot]) -> int:
        pass

    @abc.abstractmethod
    def get_latest_inventory_snapshots(self, skus: list[str] | None = None) -> dict[str, InventorySnapshot]:
        pass

    @abc.abstractmethod
    def get_inventory_snapshot(self, sku: str) -> InventorySnapshot | None:
        pass

    @abc.abstractmethod
    def get_allocated_local_stock(self, sku: str) -> Decimal:
        pass

    @abc.abstractmethod
    def get_all_allocated_local_stock(self) -> dict[str, Decimal]:
        pass

    @abc.abstractmethod
    def calculate_atp(self, sku: str, catalog_stock: Decimal | int = Decimal("0")) -> dict[str, Any]:
        pass

    @abc.abstractmethod
    def record_request_error(
        self,
        request_id: str,
        endpoint: str,
        status_code: int,
        error_message: str,
        traceback_str: str = "",
    ) -> None:
        pass

    @abc.abstractmethod
    def get_recent_request_errors(self, limit: int = 10) -> list[dict[str, Any]]:
        pass

    @abc.abstractmethod
    def get_customer_by_contact_email(self, email: str) -> CustomerMaster | None:
        pass

    @abc.abstractmethod
    def record_email_inbox_log(
        self,
        message_id: str,
        sender: str,
        subject: str,
        received_at: str,
        attachments_count: int = 0,
        orders_created: int = 0,
        status: str = "PROCESSED",
        error_message: str | None = None,
    ) -> None:
        pass

    @abc.abstractmethod
    def get_email_inbox_log(self, message_id: str) -> dict[str, Any] | None:
        pass

    @abc.abstractmethod
    def list_email_inbox_logs(self, limit: int = 50) -> list[dict[str, Any]]:
        pass







class AuditStore(BaseAuditStore):
    """SQLite implementation with Write-Ahead Logging (WAL) mode for local development."""

    def __init__(self, path: str | Path = "runtime/preflight.db"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.connection = sqlite3.connect(self.path, check_same_thread=False, timeout=30.0)
        self.connection.row_factory = sqlite3.Row
        with self._lock:
            try:
                # Enable WAL mode for high concurrency
                self.connection.execute("PRAGMA journal_mode=WAL;")
                self.connection.execute("PRAGMA busy_timeout=30000;")
            except Exception:
                pass
            try:
                self.connection.execute("ALTER TABLE customers ADD COLUMN normalized_name TEXT;")
            except Exception:
                pass
            try:
                self.connection.execute("ALTER TABLE customer_aliases ADD COLUMN normalized_alias TEXT;")
            except Exception:
                pass
            try:
                self.connection.execute("ALTER TABLE users ADD COLUMN failed_attempts INTEGER NOT NULL DEFAULT 0;")
            except Exception:
                pass
            try:
                self.connection.execute("ALTER TABLE users ADD COLUMN locked_until TEXT;")
            except Exception:
                pass
            try:
                self.connection.execute(
                    "ALTER TABLE email_inbox_logs ADD COLUMN attempts INTEGER NOT NULL DEFAULT 1;"
                )
            except Exception:
                pass
            self.connection.executescript(SQLITE_SCHEMA)
            try:
                self.connection.execute("ALTER TABLE analyses ADD COLUMN revision INTEGER DEFAULT 1;")
            except Exception:
                pass
            try:
                self.connection.execute("ALTER TABLE analyses ADD COLUMN supersedes_order_id INTEGER NULL;")
            except Exception:
                pass
            try:
                self.connection.execute("ALTER TABLE analyses ADD COLUMN requested_changes TEXT NULL;")
            except Exception:
                pass
            try:
                self.connection.execute("DROP INDEX IF EXISTS ux_analyses_po;")
            except Exception:
                pass
            try:
                self.connection.execute("CREATE INDEX IF NOT EXISTS idx_analyses_po ON analyses(po_number);")
            except Exception:
                pass
            try:
                self.connection.execute("CREATE INDEX IF NOT EXISTS idx_analyses_cust_po ON analyses(customer, po_number);")
            except Exception:
                pass
            try:
                self.connection.execute("ALTER TABLE decisions ADD COLUMN display_name TEXT;")
            except Exception:
                pass
            try:
                self.connection.execute("ALTER TABLE decisions ADD COLUMN channel TEXT;")
            except Exception:
                pass
            self.connection.commit()
            try:
                self.seed_default_customers()
            except Exception:
                pass
            try:
                self.seed_initial_admin()
            except Exception:
                pass


    def close(self) -> None:
        with self._lock:
            self.connection.close()

    def has_po(self, po_number: str, customer: str | None = None) -> bool:
        with self._lock:
            if customer:
                row = self.connection.execute(
                    "SELECT 1 FROM analyses WHERE po_number = ? AND customer = ? AND status != 'superseded' LIMIT 1",
                    (po_number, customer),
                ).fetchone()
            else:
                row = self.connection.execute(
                    "SELECT 1 FROM analyses WHERE po_number = ? AND status != 'superseded' LIMIT 1",
                    (po_number,),
                ).fetchone()
            return row is not None

    def get_order_by_po(self, po_number: str, customer: str | None = None) -> dict[str, Any] | None:
        with self._lock:
            if customer:
                row = self.connection.execute(
                    "SELECT * FROM analyses WHERE po_number = ? AND customer = ? ORDER BY revision DESC, id DESC LIMIT 1",
                    (po_number, customer),
                ).fetchone()
            else:
                row = self.connection.execute(
                    "SELECT * FROM analyses WHERE po_number = ? ORDER BY revision DESC, id DESC LIMIT 1",
                    (po_number,),
                ).fetchone()
            if not row:
                return None
            return self._enrich_order_row(dict(row))

    def get_order_revisions(self, po_number: str, customer: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            if customer:
                rows = self.connection.execute(
                    "SELECT * FROM analyses WHERE po_number = ? AND customer = ? ORDER BY revision ASC, id ASC",
                    (po_number, customer),
                ).fetchall()
            else:
                rows = self.connection.execute(
                    "SELECT * FROM analyses WHERE po_number = ? ORDER BY revision ASC, id ASC",
                    (po_number,),
                ).fetchall()
            return [dict(r) for r in rows]

    def get_recent_customer_orders(self, customer: str, days: int = 14) -> list[dict[str, Any]]:
        with self._lock:
            rows = self.connection.execute(
                "SELECT * FROM analyses WHERE customer = ? AND status != 'superseded' ORDER BY id DESC LIMIT 50",
                (customer,),
            ).fetchall()
            return [dict(r) for r in rows]

    def mark_superseded(self, order_id: int) -> None:
        with self._lock:
            with self.connection:
                self.connection.execute("UPDATE analyses SET status = 'superseded' WHERE id = ?", (order_id,))

    def record_analysis(self, analysis: Analysis, source_file: str) -> int:
        with self._lock:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO analyses (
                    po_number, customer, status, total, source_file,
                    order_json, findings_json, revision, supersedes_order_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    analysis.order.po_number,
                    analysis.order.customer,
                    analysis.status,
                    str(analysis.order.total),
                    source_file,
                    json.dumps(analysis.order.to_dict(), ensure_ascii=False),
                    json.dumps(
                        [finding.to_dict() for finding in analysis.findings],
                        ensure_ascii=False,
                    ),
                    getattr(analysis, "revision", 1),
                    getattr(analysis, "supersedes_order_id", None),
                    datetime.now(UTC).isoformat(),
                ),
            )
            self.connection.commit()
            res_id = int(cursor.lastrowid or 0)
            analysis.analysis_id = res_id
            self.append_audit_block(
                analysis.order.po_number,
                "ORDER_INGESTED",
                "system:ingestion_pipeline",
                {
                    "total": str(analysis.order.total),
                    "status": analysis.status,
                    "revision": getattr(analysis, "revision", 1),
                    "supersedes_order_id": getattr(analysis, "supersedes_order_id", None),
                },
            )
            return res_id

    def record_received_order(
        self,
        po_number: str,
        customer: str,
        source_file: str,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Record an in-flight received order awaiting async background OCR extraction."""
        with self._lock:
            cursor = self.connection.cursor()
            order_dict = {
                "po_number": po_number,
                "customer": customer,
                "items": [],
                "currency": "VND",
                "total": 0,
                "metadata": metadata or {},
            }
            now = datetime.now(UTC).isoformat()
            cursor.execute(
                """
                INSERT INTO analyses (
                    po_number, customer, status, total, source_file,
                    order_json, findings_json, revision, supersedes_order_id, created_at
                ) VALUES (?, ?, 'received', '0', ?, ?, '[]', 1, NULL, ?)
                """,
                (
                    po_number,
                    customer,
                    source_file,
                    json.dumps(order_dict, ensure_ascii=False),
                    now,
                ),
            )
            self.connection.commit()
            res_id = int(cursor.lastrowid or 0)
            self.append_audit_block(
                po_number,
                "ORDER_RECEIVED",
                "system:ocr_intake",
                {"source_file": source_file, "status": "received", "order_id": res_id},
            )
            return res_id

    def update_analysis(self, order_id: int, analysis: Analysis) -> None:
        """Update an existing analysis with confirmed order details and preflight findings."""
        with self._lock:
            with self.connection:
                self.connection.execute(
                    """
                    UPDATE analyses
                    SET po_number = ?, customer = ?, status = ?, total = ?,
                        order_json = ?, findings_json = ?, revision = ?, supersedes_order_id = ?
                    WHERE id = ?
                    """,
                    (
                        analysis.order.po_number,
                        analysis.order.customer,
                        analysis.status,
                        str(analysis.order.total),
                        json.dumps(analysis.order.to_dict(), ensure_ascii=False),
                        json.dumps(
                            [finding.to_dict() for finding in analysis.findings],
                            ensure_ascii=False,
                        ),
                        getattr(analysis, "revision", 1),
                        getattr(analysis, "supersedes_order_id", None),
                        order_id,
                    ),
                )

    def record_decision(
        self,
        po_number: str,
        decision: str,
        actor: str,
        note: str = "",
        display_name: str | None = None,
        channel: str | None = None,
    ) -> int:
        if decision not in {"approved", "rejected", "needs_changes"}:
            raise ValueError("Decision must be approved, rejected, or needs_changes")
        if not self.has_po(po_number):
            raise ValueError(f"PO {po_number} was not found")
        with self._lock:
            with self.connection:
                cursor = self.connection.execute(
                    """
                    INSERT INTO decisions (po_number, decision, actor, note, display_name, channel, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        po_number,
                        decision,
                        actor,
                        note,
                        display_name or actor,
                        channel or "api",
                        datetime.now(UTC).isoformat(),
                    ),
                )
                if decision == "needs_changes":
                    self.connection.execute(
                        "UPDATE analyses SET status = ?, requested_changes = ? WHERE po_number = ?",
                        (decision, note, po_number),
                    )
                else:
                    self.connection.execute(
                        "UPDATE analyses SET status = ? WHERE po_number = ?",
                        (decision, po_number),
                    )
                self.append_audit_block(
                    po_number,
                    f"DECISION_{decision.upper()}",
                    actor,
                    {
                        "decision": decision,
                        "note": note,
                        "actor": actor,
                        "display_name": display_name or actor,
                        "channel": channel or "api",
                    },
                )
                return int(cursor.lastrowid)

    def history(self, po_number: str) -> dict[str, list[dict[str, object]]]:
        with self._lock:
            analyses = [
                dict(row)
                for row in self.connection.execute(
                    "SELECT * FROM analyses WHERE po_number = ? ORDER BY id", (po_number,)
                )
            ]
            decisions = [
                dict(row)
                for row in self.connection.execute(
                    "SELECT * FROM decisions WHERE po_number = ? ORDER BY id", (po_number,)
                )
            ]
            return {"analyses": analyses, "decisions": decisions}

    def list_orders(
        self,
        status: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
        include_superseded: bool = False,
    ) -> list[dict[str, Any]]:
        with self._lock:
            query = """
                SELECT 
                    a.id,
                    a.po_number,
                    a.customer,
                    a.status,
                    a.total,
                    a.source_file,
                    a.order_json,
                    a.findings_json,
                    a.revision,
                    a.supersedes_order_id,
                    a.requested_changes,
                    a.created_at,
                    (SELECT d.decision FROM decisions d WHERE d.po_number = a.po_number ORDER BY d.id DESC LIMIT 1) AS latest_decision,
                    (SELECT d.actor FROM decisions d WHERE d.po_number = a.po_number ORDER BY d.id DESC LIMIT 1) AS latest_actor,
                    (SELECT d.created_at FROM decisions d WHERE d.po_number = a.po_number ORDER BY d.id DESC LIMIT 1) AS decided_at
                FROM analyses a
                WHERE 1=1
            """
            params: list[Any] = []
            if status:
                query += " AND a.status = ?"
                params.append(status)
            elif not include_superseded:
                query += " AND a.status != 'superseded'"
            if search:
                query += " AND (a.po_number LIKE ? OR a.customer LIKE ?)"
                term = f"%{search}%"
                params.extend([term, term])

            query += " ORDER BY a.id DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            rows = self.connection.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def _enrich_order_row(self, data: dict[str, Any]) -> dict[str, Any]:
        po_number = data["po_number"]
        data["decisions"] = [
            dict(d)
            for d in self.connection.execute(
                "SELECT * FROM decisions WHERE po_number = ? ORDER BY id ASC",
                (po_number,),
            ).fetchall()
        ]
        data["revisions"] = [
            dict(r)
            for r in self.connection.execute(
                "SELECT id, po_number, customer, status, total, revision, supersedes_order_id, source_file, created_at FROM analyses WHERE po_number = ? ORDER BY revision ASC, id ASC",
                (po_number,),
            ).fetchall()
        ]
        return data

    def get_order(self, po_or_id: str | int) -> dict[str, Any] | None:
        with self._lock:
            if isinstance(po_or_id, int) or str(po_or_id).isdigit():
                row = self.connection.execute(
                    "SELECT * FROM analyses WHERE id = ? LIMIT 1", (int(po_or_id),)
                ).fetchone()
            else:
                row = self.connection.execute(
                    "SELECT * FROM analyses WHERE po_number = ? ORDER BY revision DESC, id DESC LIMIT 1",
                    (str(po_or_id),),
                ).fetchone()
            if not row:
                return None
            return self._enrich_order_row(dict(row))

    def get_dashboard_stats(self) -> dict[str, Any]:

        with self._lock:
            total_orders = self.connection.execute(
                "SELECT COUNT(*) AS c FROM analyses"
            ).fetchone()["c"]
            status_counts = {
                row["status"]: row["c"]
                for row in self.connection.execute(
                    "SELECT status, COUNT(*) AS c FROM analyses GROUP BY status"
                ).fetchall()
            }
            decisions_count = {
                row["decision"]: row["c"]
                for row in self.connection.execute(
                    "SELECT decision, COUNT(*) AS c FROM decisions GROUP BY decision"
                ).fetchall()
            }
            recent_rows = self.connection.execute(
                """
                SELECT id, po_number, customer, status, total, created_at 
                FROM analyses ORDER BY id DESC LIMIT 5
                """
            ).fetchall()
            return {
                "total_orders": total_orders,
                "status_counts": status_counts,
                "decisions_count": decisions_count,
                "recent_orders": [dict(r) for r in recent_rows],
            }

    def learn_alias(
        self,
        customer_id: str,
        raw_query: str,
        target_sku: str,
        confidence: float = 1.0,
    ) -> None:
        """Record or update a learned customer-specific product alias for active learning."""
        now = datetime.now(UTC).isoformat()
        normalized_query = raw_query.strip().lower()
        normalized_sku = target_sku.strip().upper()
        with self._lock:
            self.connection.execute(
                """
                INSERT INTO sku_alias_learning (customer_id, raw_query, target_sku, confidence, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(customer_id, raw_query) DO UPDATE SET
                    target_sku = excluded.target_sku,
                    confidence = excluded.confidence,
                    created_at = excluded.created_at
                """,
                (customer_id.strip(), normalized_query, normalized_sku, confidence, now),
            )
            self.connection.commit()

    def get_customer_alias(self, customer_id: str, raw_query: str) -> str | None:
        """Lookup a learned alias for a specific customer."""
        normalized_query = raw_query.strip().lower()
        with self._lock:
            row = self.connection.execute(
                """
                SELECT target_sku FROM sku_alias_learning
                WHERE customer_id = ? AND raw_query = ?
                LIMIT 1
                """,
                (customer_id.strip(), normalized_query),
            ).fetchone()
            return str(row["target_sku"]) if row else None

    def list_customer_aliases(self, customer_id: str | None = None) -> list[dict[str, Any]]:
        """List learned customer aliases."""
        with self._lock:
            if customer_id:
                rows = self.connection.execute(
                    "SELECT * FROM sku_alias_learning WHERE customer_id = ? ORDER BY id DESC",
                    (customer_id.strip(),),
                ).fetchall()
            else:
                rows = self.connection.execute(
                    "SELECT * FROM sku_alias_learning ORDER BY id DESC"
                ).fetchall()
            return [dict(r) for r in rows]

    def append_audit_block(
        self,
        po_number: str,
        action: str,
        actor: str,
        payload: dict[str, Any],
        timestamp: float | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            t = timestamp if timestamp is not None else time.time()
            from preflight.observability.context import get_request_id
            req_id = get_request_id()
            if req_id and isinstance(payload, dict) and "request_id" not in payload:
                payload = dict(payload)
                payload["request_id"] = req_id

            last_row = self.connection.execute(
                "SELECT * FROM audit_blocks WHERE po_number = ? ORDER BY block_index DESC LIMIT 1",
                (po_number,),
            ).fetchone()
            if last_row:
                idx = last_row["block_index"] + 1
                prev_hash = last_row["block_hash"]
            else:
                idx = 0
                prev_hash = "0000000000000000000000000000000000000000000000000000000000000000"

            p_hash = compute_payload_hash(payload)
            b_hash = calculate_hash(idx, t, po_number, action, actor, p_hash, prev_hash)

            self.connection.execute(
                """
                INSERT INTO audit_blocks (block_index, timestamp, po_number, action, actor, payload_hash, previous_hash, block_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (idx, t, po_number, action, actor, p_hash, prev_hash, b_hash),
            )
            self.connection.commit()
            return {
                "index": idx,
                "timestamp": t,
                "po_number": po_number,
                "action": action,
                "actor": actor,
                "payload_hash": p_hash,
                "previous_hash": prev_hash,
                "block_hash": b_hash,
            }

    def get_audit_blocks(self, po_number: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self.connection.execute(
                "SELECT block_index as [index], timestamp, po_number, action, actor, payload_hash, previous_hash, block_hash FROM audit_blocks WHERE po_number = ? ORDER BY block_index ASC",
                (po_number,),
            ).fetchall()
            return [dict(r) for r in rows]

    def list_audit_events(
        self,
        limit: int = 50,
        offset: int = 0,
        po_number: str | None = None,
        actor: str | None = None,
        action: str | None = None,
    ) -> list[dict[str, Any]]:
        with self._lock:
            query = """
                SELECT 
                    'block_' || id AS id,
                    'AUDIT_BLOCK' AS event_type,
                    datetime(timestamp, 'unixepoch') AS timestamp,
                    po_number,
                    action,
                    actor,
                    'Block #' || block_index || ' (Hash: ' || substr(block_hash, 1, 12) || '...)' AS detail,
                    block_hash AS hash
                FROM audit_blocks
                UNION ALL
                SELECT
                    'decision_' || id AS id,
                    'DECISION' AS event_type,
                    created_at AS timestamp,
                    po_number,
                    UPPER(decision) AS action,
                    actor,
                    COALESCE(note, '') AS detail,
                    NULL AS hash
                FROM decisions
            """
            params: list[Any] = []
            where_clauses: list[str] = []
            if po_number:
                where_clauses.append("po_number LIKE ?")
                params.append(f"%{po_number}%")
            if actor:
                where_clauses.append("actor LIKE ?")
                params.append(f"%{actor}%")
            if action:
                where_clauses.append("action = ?")
                params.append(action.upper())

            outer_query = f"SELECT * FROM ({query})"
            if where_clauses:
                outer_query += " WHERE " + " AND ".join(where_clauses)
            outer_query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            rows = self.connection.execute(outer_query, params).fetchall()
            return [dict(r) for r in rows]

    def set_customer_pricing(self, pricing: CustomerPriceAgreement) -> None:
        with self._lock:
            self.connection.execute(
                """
                INSERT INTO customer_pricing (customer_id, sku, contract_price, min_quantity, discount_percent, valid_from, valid_to, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(customer_id, sku, min_quantity) DO UPDATE SET
                    contract_price = excluded.contract_price,
                    discount_percent = excluded.discount_percent,
                    valid_from = excluded.valid_from,
                    valid_to = excluded.valid_to,
                    created_at = excluded.created_at
                """,
                (
                    pricing.customer_id.strip(),
                    pricing.sku.strip().upper(),
                    str(pricing.contract_price),
                    pricing.min_quantity,
                    str(pricing.discount_percent),
                    pricing.valid_from,
                    pricing.valid_to,
                    datetime.now(UTC).isoformat(),
                ),
            )
            self.connection.commit()
            if not self.get_customer(pricing.customer_id) and not self.get_customer_by_normalized_name(pricing.customer_id):
                self.create_customer(CustomerMaster(
                    code=pricing.customer_id,
                    name=pricing.customer_id,
                    normalized_name=normalize_vietnamese_name(pricing.customer_id),
                ))

    def get_customer_pricing(self, customer_id: str) -> list[CustomerPriceAgreement]:
        with self._lock:
            rows = self.connection.execute(
                "SELECT * FROM customer_pricing WHERE customer_id = ? COLLATE NOCASE ORDER BY sku ASC, min_quantity DESC",
                (customer_id.strip(),),
            ).fetchall()
            if not rows:
                from preflight.rules_context import normalize_customer_key
                norm_target = normalize_customer_key(customer_id)
                all_rows = self.connection.execute("SELECT * FROM customer_pricing ORDER BY sku ASC, min_quantity DESC").fetchall()
                rows = [r for r in all_rows if normalize_customer_key(r["customer_id"]) == norm_target]
            return [
                CustomerPriceAgreement(
                    customer_id=r["customer_id"],
                    sku=r["sku"],
                    contract_price=Decimal(r["contract_price"]),
                    min_quantity=int(r["min_quantity"]),
                    discount_percent=Decimal(r["discount_percent"]),
                    valid_from=r["valid_from"],
                    valid_to=r["valid_to"],
                )
                for r in rows
            ]

    def set_uom_conversion(self, conversion: UOMConversion) -> None:
        with self._lock:
            self.connection.execute(
                """
                INSERT INTO uom_conversions (sku, uom_code, base_uom, conversion_factor, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(sku, uom_code) DO UPDATE SET
                    base_uom = excluded.base_uom,
                    conversion_factor = excluded.conversion_factor,
                    created_at = excluded.created_at
                """,
                (
                    conversion.sku.strip().upper(),
                    conversion.uom_code.strip().upper(),
                    conversion.base_uom.strip().upper(),
                    str(conversion.conversion_factor),
                    datetime.now(UTC).isoformat(),
                ),
            )
            self.connection.commit()

    def get_uom_conversions(self, sku: str | None = None) -> list[UOMConversion]:
        with self._lock:
            if sku:
                rows = self.connection.execute(
                    "SELECT * FROM uom_conversions WHERE sku = ? ORDER BY uom_code ASC",
                    (sku.strip().upper(),),
                ).fetchall()
            else:
                rows = self.connection.execute("SELECT * FROM uom_conversions ORDER BY sku ASC, uom_code ASC").fetchall()
            return [
                UOMConversion(
                    sku=r["sku"],
                    uom_code=r["uom_code"],
                    base_uom=r["base_uom"],
                    conversion_factor=Decimal(r["conversion_factor"]),
                )
                for r in rows
            ]

    def set_customer_credit(self, credit: CustomerCreditProfile) -> None:
        with self._lock:
            self.connection.execute(
                """
                INSERT INTO customer_credits (customer_id, credit_limit, outstanding_balance, overdue_balance, oldest_overdue_days, status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(customer_id) DO UPDATE SET
                    credit_limit = excluded.credit_limit,
                    outstanding_balance = excluded.outstanding_balance,
                    overdue_balance = excluded.overdue_balance,
                    oldest_overdue_days = excluded.oldest_overdue_days,
                    status = excluded.status,
                    updated_at = excluded.updated_at
                """,
                (
                    credit.customer_id.strip(),
                    str(credit.credit_limit),
                    str(credit.outstanding_balance),
                    str(credit.overdue_balance),
                    credit.oldest_overdue_days,
                    credit.status,
                    datetime.now(UTC).isoformat(),
                ),
            )
            self.connection.commit()
            if not self.get_customer(credit.customer_id) and not self.get_customer_by_normalized_name(credit.customer_id):
                self.create_customer(CustomerMaster(
                    code=credit.customer_id,
                    name=credit.customer_id,
                    normalized_name=normalize_vietnamese_name(credit.customer_id),
                ))

    def get_customer_credit(self, customer_id: str) -> CustomerCreditProfile | None:
        with self._lock:
            row = self.connection.execute(
                "SELECT * FROM customer_credits WHERE customer_id = ? COLLATE NOCASE LIMIT 1",
                (customer_id.strip(),),
            ).fetchone()
            if not row:
                from preflight.rules_context import normalize_customer_key
                norm_target = normalize_customer_key(customer_id)
                all_rows = self.connection.execute("SELECT * FROM customer_credits").fetchall()
                for r in all_rows:
                    if normalize_customer_key(r["customer_id"]) == norm_target:
                        row = r
                        break
            if not row:
                return None
            return CustomerCreditProfile(
                customer_id=row["customer_id"],
                credit_limit=Decimal(row["credit_limit"]),
                outstanding_balance=Decimal(row["outstanding_balance"]),
                overdue_balance=Decimal(row["overdue_balance"]),
                oldest_overdue_days=int(row["oldest_overdue_days"]),
                status=row["status"],
            )


    def set_policy(self, policy: RulePolicy, updated_by: str = "system") -> None:
        with self._lock:
            now = datetime.now(UTC).isoformat()
            self.connection.execute(
                """
                INSERT INTO rule_policies (id, policy_json, updated_at, updated_by)
                VALUES (1, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    policy_json = excluded.policy_json,
                    updated_at = excluded.updated_at,
                    updated_by = excluded.updated_by
                """,
                (json.dumps(policy.to_dict()), now, updated_by),
            )
            self.connection.commit()

    def get_policy(self) -> RulePolicy:
        with self._lock:
            row = self.connection.execute(
                "SELECT policy_json FROM rule_policies WHERE id = 1 LIMIT 1"
            ).fetchone()
            if not row:
                return RulePolicy()
            data = json.loads(row["policy_json"])
            return RulePolicy.from_dict(data)

    def get_channel_identity(self, channel: str, external_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self.connection.execute(
                "SELECT * FROM channel_identities WHERE channel = ? AND external_id = ? LIMIT 1",
                (channel.strip().lower(), str(external_id).strip()),
            ).fetchone()
            if not row:
                return None
            return dict(row)

    def upsert_channel_identity(
        self,
        channel: str,
        external_id: str,
        user_id: str,
        display_name: str,
        role: str,
    ) -> None:
        with self._lock:
            self.connection.execute(
                """
                INSERT INTO channel_identities (channel, external_id, user_id, display_name, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(channel, external_id) DO UPDATE SET
                    user_id = excluded.user_id,
                    display_name = excluded.display_name,
                    role = excluded.role,
                    created_at = excluded.created_at
                """,
                (
                    channel.strip().lower(),
                    str(external_id).strip(),
                    user_id.strip(),
                    display_name.strip(),
                    role.strip().upper(),
                    datetime.now(UTC).isoformat(),
                ),
            )
            self.connection.commit()

    def create_channel_link_code(
        self, user_id: str, display_name: str, role: str, expires_in_seconds: int = 600
    ) -> str:
        with self._lock:
            import secrets
            code = secrets.token_hex(3).upper()
            expires_at = time.time() + expires_in_seconds
            role_str = getattr(role, "name", str(role)).strip().upper()
            self.connection.execute(
                """
                INSERT OR REPLACE INTO channel_link_codes (code, user_id, display_name, role, expires_at, used)
                VALUES (?, ?, ?, ?, ?, 0)
                """,
                (code, str(user_id).strip(), str(display_name).strip(), role_str, expires_at),
            )
            self.connection.commit()
            return code

    def consume_channel_link_code(self, code: str) -> dict[str, Any] | None:
        with self._lock:
            clean_code = code.strip().upper()
            row = self.connection.execute(
                "SELECT * FROM channel_link_codes WHERE code = ? LIMIT 1", (clean_code,)
            ).fetchone()
            if not row:
                return None
            record = dict(row)
            if record.get("used"):
                return None
            if time.time() > float(record["expires_at"]):
                return {"expired": True, "user_id": record["user_id"]}
            self.connection.execute(
                "UPDATE channel_link_codes SET used = 1 WHERE code = ?", (clean_code,)
            )
            self.connection.commit()
            return {
                "expired": False,
                "user_id": record["user_id"],
                "display_name": record["display_name"],
                "role": record["role"],
            }

    def record_processed_webhook_event(self, channel: str, event_id: str) -> bool:
        with self._lock:
            chan = channel.strip().lower()
            ev_id = str(event_id).strip()
            row = self.connection.execute(
                "SELECT 1 FROM processed_webhook_events WHERE channel = ? AND event_id = ? LIMIT 1",
                (chan, ev_id),
            ).fetchone()
            if row:
                return False
            self.connection.execute(
                "INSERT INTO processed_webhook_events (channel, event_id, processed_at) VALUES (?, ?, ?)",
                (chan, ev_id, time.time()),
            )
            self.connection.commit()
            return True

    def save_product_embedding(self, sku: str, vector_bytes: bytes, text_hash: str) -> None:
        with self._lock:
            self.connection.execute(
                """
                INSERT INTO product_embeddings (sku, vector_blob, text_hash, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(sku) DO UPDATE SET
                    vector_blob = excluded.vector_blob,
                    text_hash = excluded.text_hash,
                    updated_at = excluded.updated_at
                """,
                (sku.strip().upper(), vector_bytes, text_hash, datetime.now(UTC).isoformat()),
            )
            self.connection.commit()

    def get_product_embeddings(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self.connection.execute(
                "SELECT sku, vector_blob, text_hash, updated_at FROM product_embeddings"
            ).fetchall()
            return [dict(r) for r in rows]

    def get_product_embedding(self, sku: str) -> dict[str, Any] | None:
        with self._lock:
            row = self.connection.execute(
                "SELECT sku, vector_blob, text_hash, updated_at FROM product_embeddings WHERE sku = ? LIMIT 1",
                (sku.strip().upper(),),
            ).fetchone()
            if not row:
                return None
            return dict(row)

    def create_lead(
        self,
        name: str,
        company: str,
        phone: str,
        email: str,
        erp: str | None,
        volume: str | None,
        note: str | None,
        ip_hash: str,
    ) -> dict[str, Any]:
        now_str = datetime.now(UTC).isoformat()
        with self._lock:
            cur = self.connection.cursor()
            cur.execute(
                """
                INSERT INTO leads (name, company, phone, email, erp, volume, note, ip_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (name, company, phone, email, erp, volume, note, ip_hash, now_str),
            )
            self.connection.commit()
            lead_id = cur.lastrowid or 1
            return {
                "id": lead_id,
                "name": name,
                "company": company,
                "phone": phone,
                "email": email,
                "erp": erp,
                "volume": volume,
                "note": note,
                "ip_hash": ip_hash,
                "created_at": now_str,
            }

    def list_leads(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        with self._lock:
            rows = self.connection.execute(
                "SELECT * FROM leads ORDER BY id DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            return [dict(r) for r in rows]

    def create_customer(self, customer: CustomerMaster) -> CustomerMaster:
        with self._lock:
            norm_name = customer.normalized_name or normalize_vietnamese_name(customer.name)
            now = datetime.now(UTC).isoformat()
            emails_str = ",".join(customer.contact_emails) if customer.contact_emails else ""
            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO customers (code, name, normalized_name, tax_code, tier, contact_emails, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (customer.code.strip(), customer.name.strip(), norm_name, customer.tax_code, customer.tier, emails_str, now),
            )
            cust_id = cursor.lastrowid
            self.connection.commit()

            # Insert aliases
            for alias in customer.aliases:
                if alias and alias.strip():
                    self.add_customer_alias(customer.code, alias.strip())

            return CustomerMaster(
                id=cust_id,
                code=customer.code.strip(),
                name=customer.name.strip(),
                normalized_name=norm_name,
                tax_code=customer.tax_code,
                tier=customer.tier,
                aliases=list(customer.aliases),
                contact_emails=list(customer.contact_emails),
                created_at=now,
            )

    def add_customer_alias(self, customer_id: str, alias: str) -> None:
        with self._lock:
            norm_alias = normalize_vietnamese_name(alias)
            now = datetime.now(UTC).isoformat()
            try:
                self.connection.execute(
                    """
                    INSERT INTO customer_aliases (customer_id, alias, normalized_alias, created_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(customer_id, normalized_alias) DO UPDATE SET
                        alias = excluded.alias,
                        created_at = excluded.created_at
                    """,
                    (customer_id.strip(), alias.strip(), norm_alias, now),
                )
                self.connection.commit()
            except Exception:
                pass

    def get_customer(self, code: str) -> CustomerMaster | None:
        with self._lock:
            row = self.connection.execute(
                "SELECT * FROM customers WHERE code = ? OR id = ? LIMIT 1",
                (code.strip(), int(code) if code.isdigit() else -1),
            ).fetchone()
            if not row:
                return None
            aliases = [
                r["alias"]
                for r in self.connection.execute(
                    "SELECT alias FROM customer_aliases WHERE customer_id = ?",
                    (row["code"],),
                ).fetchall()
            ]
            raw_emails = row["contact_emails"] if "contact_emails" in row.keys() and row["contact_emails"] else ""
            email_list = [e.strip() for e in raw_emails.replace(";", ",").split(",") if e.strip()]
            return CustomerMaster(
                id=row["id"],
                code=row["code"],
                name=row["name"],
                normalized_name=row["normalized_name"],
                tax_code=row["tax_code"],
                tier=row["tier"],
                aliases=aliases,
                contact_emails=email_list,
                created_at=row["created_at"],
            )

    def get_customer_by_id(self, customer_id: int) -> CustomerMaster | None:
        return self.get_customer(str(customer_id))

    def get_customer_by_tax_code(self, tax_code: str) -> CustomerMaster | None:
        with self._lock:
            clean = tax_code.strip().replace(" ", "").replace("-", "")
            row = self.connection.execute(
                "SELECT * FROM customers WHERE tax_code = ? LIMIT 1",
                (clean,),
            ).fetchone()
            if not row:
                return None
            return self.get_customer(row["code"])

    def get_customer_by_normalized_name(self, norm_name: str) -> CustomerMaster | None:
        with self._lock:
            clean = norm_name.strip()
            # 1. Exact match on normalized_name
            row = self.connection.execute(
                "SELECT * FROM customers WHERE normalized_name = ? LIMIT 1",
                (clean,),
            ).fetchone()
            if row:
                return self.get_customer(row["code"])
            
            # 2. Exact match on customer_aliases
            alias_row = self.connection.execute(
                "SELECT customer_id FROM customer_aliases WHERE normalized_alias = ? LIMIT 1",
                (clean,),
            ).fetchone()
            if alias_row:
                return self.get_customer(alias_row["customer_id"])
            return None

    def get_customer_by_contact_email(self, email: str) -> CustomerMaster | None:
        with self._lock:
            clean = email.strip().lower()
            if not clean:
                return None
            rows = self.connection.execute("SELECT * FROM customers").fetchall()
            for r in rows:
                raw_emails = r["contact_emails"] if "contact_emails" in r.keys() and r["contact_emails"] else ""
                email_list = [e.strip().lower() for e in raw_emails.replace(";", ",").split(",") if e.strip()]
                if clean in email_list:
                    return self.get_customer(r["code"])
            return None

    def list_customers(self, search: str | None = None, limit: int = 50, offset: int = 0) -> list[CustomerMaster]:
        with self._lock:
            if search:
                pattern = f"%{search.strip()}%"
                rows = self.connection.execute(
                    """
                    SELECT DISTINCT c.* FROM customers c
                    LEFT JOIN customer_aliases a ON a.customer_id = c.code
                    WHERE c.name LIKE ? OR c.code LIKE ? OR c.tax_code LIKE ? OR c.normalized_name LIKE ? OR a.alias LIKE ?
                    ORDER BY c.id DESC LIMIT ? OFFSET ?
                    """,
                    (pattern, pattern, pattern, pattern, pattern, limit, offset),
                ).fetchall()
            else:
                rows = self.connection.execute(
                    "SELECT * FROM customers ORDER BY id DESC LIMIT ? OFFSET ?",
                    (limit, offset),
                ).fetchall()

            result = []
            for r in rows:
                cust = self.get_customer(r["code"])
                if cust:
                    result.append(cust)
            return result

    def update_customer(self, code: str, data: dict[str, Any]) -> CustomerMaster | None:
        with self._lock:
            cust = self.get_customer(code)
            if not cust:
                return None
            new_name = data.get("name", cust.name).strip()
            new_norm = normalize_vietnamese_name(new_name)
            new_tax = data.get("tax_code", cust.tax_code)
            new_tier = data.get("tier", cust.tier)
            if "contact_emails" in data:
                emails_val = data["contact_emails"]
                if isinstance(emails_val, list):
                    emails_str = ",".join(emails_val)
                else:
                    emails_str = str(emails_val or "")
            else:
                emails_str = ",".join(cust.contact_emails)

            self.connection.execute(
                """
                UPDATE customers SET name = ?, normalized_name = ?, tax_code = ?, tier = ?, contact_emails = ?
                WHERE code = ?
                """,
                (new_name, new_norm, new_tax, new_tier, emails_str, cust.code),
            )
            self.connection.commit()

            if "aliases" in data:
                self.connection.execute("DELETE FROM customer_aliases WHERE customer_id = ?", (cust.code,))
                for a in data["aliases"]:
                    if a and a.strip():
                        self.add_customer_alias(cust.code, a.strip())

            return self.get_customer(cust.code)

    def delete_customer(self, code: str) -> bool:
        with self._lock:
            cust = self.get_customer(code)
            if not cust:
                return False
            self.connection.execute("DELETE FROM customers WHERE code = ?", (cust.code,))
            self.connection.execute("DELETE FROM customer_aliases WHERE customer_id = ?", (cust.code,))
            self.connection.commit()
            return True

    def list_customer_master_aliases(self, customer_id: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            if customer_id:
                rows = self.connection.execute(
                    "SELECT * FROM customer_aliases WHERE customer_id = ? ORDER BY id DESC",
                    (customer_id.strip(),),
                ).fetchall()
            else:
                rows = self.connection.execute(
                    "SELECT * FROM customer_aliases ORDER BY id DESC"
                ).fetchall()
            return [dict(r) for r in rows]

    def record_email_inbox_log(
        self,
        message_id: str,
        sender: str,
        subject: str,
        received_at: str,
        attachments_count: int = 0,
        orders_created: int = 0,
        status: str = "PROCESSED",
        error_message: str | None = None,
    ) -> None:
        with self._lock:
            now = datetime.now(UTC).isoformat()
            self.connection.execute(
                """
                INSERT INTO email_inbox_logs (message_id, sender, subject, received_at, attachments_count, orders_created, status, error_message, attempts, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                ON CONFLICT(message_id) DO UPDATE SET
                    status = excluded.status,
                    orders_created = excluded.orders_created,
                    error_message = excluded.error_message,
                    attempts = email_inbox_logs.attempts + 1
                """,
                (message_id, sender, subject, received_at, attachments_count, orders_created, status, error_message, now),
            )
            self.connection.commit()

    def get_email_inbox_log(self, message_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self.connection.execute(
                "SELECT * FROM email_inbox_logs WHERE message_id = ? LIMIT 1",
                (message_id,),
            ).fetchone()
            return dict(row) if row else None

    def list_email_inbox_logs(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            rows = self.connection.execute(
                "SELECT * FROM email_inbox_logs ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def seed_default_customers(self) -> None:
        with self._lock:
            count = self.connection.execute("SELECT COUNT(*) AS c FROM customers").fetchone()["c"]
            if count == 0:
                defaults = [
                    CustomerMaster(
                        code="CUST-001",
                        name="Tập đoàn Vingroup",
                        tax_code="0101245486",
                        tier="VIP",
                        aliases=["Vingroup", "Vingroup JSC", "CTY CP Vingroup"],
                        contact_emails=["order@vingroup.net", "purchasing@vingroup.net"],
                    ),
                    CustomerMaster(
                        code="CUST-002",
                        name="Northstar Retail",
                        tax_code="0109876543",
                        tier="PLATINUM",
                        aliases=["Northstar", "Northstar Store", "Northstar Distribution"],
                        contact_emails=["orders@northstar.vn", "purchasing@northstar.vn", "procurement@northstar.com"],
                    ),
                    CustomerMaster(
                        code="CUST-003",
                        name="Acme Corp",
                        tax_code="0308765432",
                        tier="STANDARD",
                        aliases=["Acme", "Acme Vietnam", "Acme Corporation"],
                        contact_emails=["sales@acme.vn", "orders@acme.com"],
                    ),
                    CustomerMaster(
                        code="CUST-004",
                        name="Alpha Technology",
                        tax_code="0312345678",
                        tier="STANDARD",
                        aliases=["Alpha Tech", "CTY TNHH Alpha", "Alpha Corp"],
                        contact_emails=["it@alpha.vn", "procurement@alphatech.com"],
                    ),
                ]
                for d in defaults:
                    self.create_customer(d)

    def create_user(self, user: User) -> User:
        with self._lock:
            now_iso = datetime.now(UTC).isoformat()
            self.connection.execute(
                """
                INSERT INTO users (org_id, username, display_name, email, password_hash, role, is_active, failed_attempts, locked_until, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(username) DO UPDATE SET
                    display_name = excluded.display_name,
                    email = excluded.email,
                    password_hash = COALESCE(excluded.password_hash, users.password_hash),
                    role = excluded.role,
                    is_active = excluded.is_active
                """,
                (
                    user.org_id,
                    user.username.strip().lower(),
                    user.display_name.strip(),
                    user.email.strip().lower(),
                    user.password_hash,
                    user.role.strip().lower(),
                    1 if user.is_active else 0,
                    user.failed_attempts,
                    user.locked_until,
                    user.created_at or now_iso,
                ),
            )
            self.connection.commit()
            return self.get_user(user.username) or user

    def get_user(self, username: str) -> User | None:
        with self._lock:
            row = self.connection.execute(
                "SELECT * FROM users WHERE username = ? COLLATE NOCASE",
                (username.strip(),),
            ).fetchone()
            if not row:
                return None
            return User(
                id=row["id"],
                org_id=row["org_id"],
                username=row["username"],
                display_name=row["display_name"],
                email=row["email"],
                password_hash=row["password_hash"],
                role=row["role"],
                is_active=bool(row["is_active"]),
                failed_attempts=row["failed_attempts"],
                locked_until=row["locked_until"],
                created_at=row["created_at"],
            )

    def get_user_by_id(self, user_id: int) -> User | None:
        with self._lock:
            row = self.connection.execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            if not row:
                return None
            return User(
                id=row["id"],
                org_id=row["org_id"],
                username=row["username"],
                display_name=row["display_name"],
                email=row["email"],
                password_hash=row["password_hash"],
                role=row["role"],
                is_active=bool(row["is_active"]),
                failed_attempts=row["failed_attempts"],
                locked_until=row["locked_until"],
                created_at=row["created_at"],
            )

    def list_users(self) -> list[User]:
        with self._lock:
            rows = self.connection.execute("SELECT * FROM users ORDER BY id ASC").fetchall()
            return [
                User(
                    id=row["id"],
                    org_id=row["org_id"],
                    username=row["username"],
                    display_name=row["display_name"],
                    email=row["email"],
                    password_hash=row["password_hash"],
                    role=row["role"],
                    is_active=bool(row["is_active"]),
                    failed_attempts=row["failed_attempts"],
                    locked_until=row["locked_until"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

    def update_user(
        self,
        username: str,
        display_name: str | None = None,
        email: str | None = None,
        role: str | None = None,
        password_hash: str | None = None,
        is_active: bool | None = None,
    ) -> User | None:
        with self._lock:
            user = self.get_user(username)
            if not user:
                return None
            new_disp = display_name if display_name is not None else user.display_name
            new_email = email if email is not None else user.email
            new_role = role if role is not None else user.role
            new_pwd = password_hash if password_hash is not None else user.password_hash
            new_active = is_active if is_active is not None else user.is_active

            self.connection.execute(
                """
                UPDATE users
                SET display_name = ?, email = ?, role = ?, password_hash = ?, is_active = ?
                WHERE username = ? COLLATE NOCASE
                """,
                (
                    new_disp.strip(),
                    new_email.strip().lower(),
                    new_role.strip().lower(),
                    new_pwd,
                    1 if new_active else 0,
                    username.strip(),
                ),
            )
            self.connection.commit()
            return self.get_user(username)

    def delete_user(self, username: str) -> bool:
        with self._lock:
            cursor = self.connection.execute(
                "DELETE FROM users WHERE username = ? COLLATE NOCASE",
                (username.strip(),),
            )
            self.connection.commit()
            return cursor.rowcount > 0

    def record_failed_login(self, username: str) -> int:
        with self._lock:
            row = self.connection.execute(
                "SELECT failed_attempts FROM users WHERE username = ? COLLATE NOCASE",
                (username.strip(),),
            ).fetchone()
            if not row:
                return 0
            attempts = row["failed_attempts"] + 1
            locked_until = None
            if attempts >= 5:
                # Lock for 15 minutes (900 seconds)
                locked_until = datetime.fromtimestamp(time.time() + 900, tz=UTC).isoformat()
            self.connection.execute(
                "UPDATE users SET failed_attempts = ?, locked_until = ? WHERE username = ? COLLATE NOCASE",
                (attempts, locked_until, username.strip()),
            )
            self.connection.commit()
            return attempts

    def reset_failed_logins(self, username: str) -> None:
        with self._lock:
            self.connection.execute(
                "UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE username = ? COLLATE NOCASE",
                (username.strip(),),
            )
            self.connection.commit()

    def is_user_locked(self, username: str) -> bool:
        with self._lock:
            row = self.connection.execute(
                "SELECT locked_until FROM users WHERE username = ? COLLATE NOCASE",
                (username.strip(),),
            ).fetchone()
            if not row or not row["locked_until"]:
                return False
            try:
                locked_dt = datetime.fromisoformat(row["locked_until"])
                if locked_dt > datetime.now(UTC):
                    return True
                else:
                    self.reset_failed_logins(username)
                    return False
            except Exception:
                return False

    def seed_initial_admin(self) -> None:
        with self._lock:
            count = self.connection.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
            if count == 0:
                defaults = [
                    User(
                        username="admin",
                        display_name="Hệ Thống Quản Trị",
                        email="admin@preflight.vn",
                        password_hash=hash_password("Admin@123456"),
                        role="admin",
                        created_at=datetime.now(UTC).isoformat(),
                    ),
                    User(
                        username="director",
                        display_name="Giám Đốc Phê Duyệt",
                        email="director@preflight.vn",
                        password_hash=hash_password("Director@123456"),
                        role="director",
                        created_at=datetime.now(UTC).isoformat(),
                    ),
                    User(
                        username="manager",
                        display_name="Trưởng Phòng Vận Hành",
                        email="manager@preflight.vn",
                        password_hash=hash_password("Manager@123456"),
                        role="manager",
                        created_at=datetime.now(UTC).isoformat(),
                    ),
                    User(
                        username="sales_admin",
                        display_name="Nhân Viên Sales Admin",
                        email="sales@preflight.vn",
                        password_hash=hash_password("Sales@123456"),
                        role="sales_admin",
                        created_at=datetime.now(UTC).isoformat(),
                    ),
                    User(
                        username="auditor",
                        display_name="Kiểm Toán Viên",
                        email="auditor@preflight.vn",
                        password_hash=hash_password("Auditor@123456"),
                        role="auditor",
                        created_at=datetime.now(UTC).isoformat(),
                    ),
                    User(
                        username="viewer",
                        display_name="Người Xem Báo Cáo",
                        email="viewer@preflight.vn",
                        password_hash=hash_password("Viewer@123456"),
                        role="viewer",
                        created_at=datetime.now(UTC).isoformat(),
                    ),
                ]
                for u in defaults:
                    self.create_user(u)

    def record_inventory_snapshots(self, snapshots: list[InventorySnapshot]) -> int:
        with self._lock:
            count = 0
            now_iso = datetime.now(UTC).isoformat()
            for s in snapshots:
                as_of_val = s.as_of or now_iso
                self.connection.execute(
                    """
                    INSERT INTO inventory_snapshots (sku, warehouse, on_hand, reserved, as_of, source, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (s.sku.strip(), s.warehouse.strip(), str(s.on_hand), str(s.reserved), as_of_val, s.source.strip(), now_iso),
                )
                count += 1
            self.connection.commit()
            return count

    def get_latest_inventory_snapshots(self, skus: list[str] | None = None) -> dict[str, InventorySnapshot]:
        with self._lock:
            if skus:
                clean_skus = [s.strip() for s in skus if s]
                if not clean_skus:
                    return {}
                placeholders = ",".join("?" for _ in clean_skus)
                rows = self.connection.execute(
                    f"""
                    SELECT id, sku, warehouse, on_hand, reserved, as_of, source
                    FROM inventory_snapshots
                    WHERE sku IN ({placeholders})
                    ORDER BY id DESC
                    """,
                    tuple(clean_skus),
                ).fetchall()
            else:
                rows = self.connection.execute(
                    """
                    SELECT id, sku, warehouse, on_hand, reserved, as_of, source
                    FROM inventory_snapshots
                    ORDER BY id DESC
                    """
                ).fetchall()

            snapshots: dict[str, InventorySnapshot] = {}
            for r in rows:
                sku = r["sku"]
                if sku not in snapshots:
                    snapshots[sku] = InventorySnapshot(
                        id=r["id"],
                        sku=sku,
                        warehouse=r["warehouse"],
                        on_hand=Decimal(str(r["on_hand"])),
                        reserved=Decimal(str(r["reserved"])),
                        as_of=str(r["as_of"]),
                        source=r["source"],
                    )
            return snapshots

    def get_inventory_snapshot(self, sku: str) -> InventorySnapshot | None:
        snaps = self.get_latest_inventory_snapshots(skus=[sku])
        return snaps.get(sku.strip())

    def get_all_allocated_local_stock(self) -> dict[str, Decimal]:
        """Calculate local stock allocations for approved orders not yet exported to ERP."""
        with self._lock:
            rows = self.connection.execute(
                """
                SELECT a.id, a.po_number, a.order_json
                FROM analyses a
                WHERE LOWER(a.status) = 'approved'
                """
            ).fetchall()
            if not rows:
                return {}

            sent_pos = set()
            try:
                sent_rows = self.connection.execute(
                    "SELECT po_number FROM erp_outbox WHERE status = 'SENT'"
                ).fetchall()
                sent_pos = {r["po_number"] for r in sent_rows if r["po_number"]}
            except Exception:
                pass

            uom_conversions = self.get_uom_conversions()
            uom_map = {(u.sku, u.uom_code): u.conversion_factor for u in uom_conversions}

            allocations: dict[str, Decimal] = {}
            for r in rows:
                po_num = r["po_number"]
                if po_num in sent_pos:
                    continue
                raw_json = r["order_json"]
                if not raw_json:
                    continue
                od = json.loads(raw_json) if isinstance(raw_json, str) else raw_json
                items = od.get("items", [])
                for item in items:
                    sku = item.get("sku", "").strip()
                    if not sku:
                        continue
                    qty = Decimal(str(item.get("quantity", 0)))
                    uom = str(item.get("uom", "PCS")).strip().upper()
                    factor = uom_map.get((sku, uom), Decimal("1.0"))
                    base_qty = qty * factor
                    allocations[sku] = allocations.get(sku, Decimal("0")) + base_qty

            return allocations

    def get_allocated_local_stock(self, sku: str) -> Decimal:
        return self.get_all_allocated_local_stock().get(sku.strip(), Decimal("0"))

    def calculate_atp(self, sku: str, catalog_stock: Decimal | int = Decimal("0")) -> dict[str, Any]:
        snapshot = self.get_inventory_snapshot(sku)
        allocated = self.get_allocated_local_stock(sku)
        if snapshot:
            on_hand = snapshot.on_hand
            reserved = snapshot.reserved
            as_of = snapshot.as_of
            source = snapshot.source
        else:
            on_hand = Decimal(str(catalog_stock))
            reserved = Decimal("0")
            as_of = ""
            source = "catalog"

        atp = max(Decimal("0"), on_hand - reserved - allocated)
        is_stale = False
        if as_of:
            try:
                dt = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
                age_hours = (datetime.now(UTC) - dt).total_seconds() / 3600.0
                policy = self.get_policy()
                if age_hours > policy.inventory_stale_hours:
                    is_stale = True
            except Exception:
                pass

        return {
            "sku": sku,
            "on_hand": on_hand,
            "reserved_erp": reserved,
            "allocated_local": allocated,
            "atp": atp,
            "as_of": as_of,
            "source": source,
            "is_stale": is_stale,
        }

    def record_request_error(
        self,
        request_id: str,
        endpoint: str,
        status_code: int,
        error_message: str,
        traceback_str: str = "",
    ) -> None:
        with self._lock:
            now_iso = datetime.now(timezone.utc).isoformat()
            self.connection.execute(
                """
                INSERT INTO request_errors (request_id, endpoint, status_code, error_message, traceback, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (request_id, endpoint, status_code, error_message, traceback_str, now_iso),
            )
            # Prune older than 7 days
            seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            self.connection.execute("DELETE FROM request_errors WHERE created_at < ?", (seven_days_ago,))
            self.connection.commit()

    def get_recent_request_errors(self, limit: int = 10) -> list[dict[str, Any]]:
        with self._lock:
            rows = self.connection.execute(
                """
                SELECT id, request_id, endpoint, status_code, error_message, traceback, created_at
                FROM request_errors
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]






class PostgresAuditStore(BaseAuditStore):
    """Enterprise PostgreSQL Audit Store with psycopg 3 Connection Pooling."""

    def __init__(
        self,
        database_url: str,
        pool_size: int = 20,
        max_overflow: int = 10,
    ):
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow

        try:
            from psycopg_pool import ConnectionPool
            from psycopg.rows import dict_row

            self._pool = ConnectionPool(
                conninfo=self.database_url,
                min_size=1,
                max_size=self.pool_size + self.max_overflow,
                open=True,
                timeout=3.0,
                kwargs={"row_factory": dict_row, "connect_timeout": 3},
            )
            self._init_pg_schema()
        except Exception as exc:
            raise ConfigurationError(
                f"Không thể kết nối đến PostgreSQL database tại {database_url}: {exc}"
            ) from exc

    def _init_pg_schema(self) -> None:
        with self._pool.connection(timeout=3.0) as conn:
            with conn.cursor() as cur:
                cur.execute(POSTGRES_SCHEMA)
            conn.commit()
        try:
            self.seed_initial_admin()
        except Exception:
            pass

    def close(self) -> None:
        if hasattr(self, "_pool"):
            self._pool.close()

    def has_po(self, po_number: str, customer: str | None = None) -> bool:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                if customer:
                    cur.execute("SELECT 1 FROM analyses WHERE po_number = %s AND customer = %s AND status != 'superseded' LIMIT 1", (po_number, customer))
                else:
                    cur.execute("SELECT 1 FROM analyses WHERE po_number = %s AND status != 'superseded' LIMIT 1", (po_number,))
                return cur.fetchone() is not None

    def get_order_by_po(self, po_number: str, customer: str | None = None) -> dict[str, Any] | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                if customer:
                    cur.execute("SELECT * FROM analyses WHERE po_number = %s AND customer = %s ORDER BY revision DESC, id DESC LIMIT 1", (po_number, customer))
                else:
                    cur.execute("SELECT * FROM analyses WHERE po_number = %s ORDER BY revision DESC, id DESC LIMIT 1", (po_number,))
                row = cur.fetchone()
                if not row:
                    return None
                data = dict(row)
                po_num = data["po_number"]
                cur.execute("SELECT * FROM decisions WHERE po_number = %s ORDER BY id ASC", (po_num,))
                data["decisions"] = [dict(d) for d in cur.fetchall()]
                cur.execute(
                    "SELECT id, po_number, customer, status, total, revision, supersedes_order_id, source_file, created_at FROM analyses WHERE po_number = %s ORDER BY revision ASC, id ASC",
                    (po_num,),
                )
                data["revisions"] = [dict(r) for r in cur.fetchall()]
                return data

    def get_order_revisions(self, po_number: str, customer: str | None = None) -> list[dict[str, Any]]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                if customer:
                    cur.execute("SELECT * FROM analyses WHERE po_number = %s AND customer = %s ORDER BY revision ASC, id ASC", (po_number, customer))
                else:
                    cur.execute("SELECT * FROM analyses WHERE po_number = %s ORDER BY revision ASC, id ASC", (po_number,))
                return [dict(r) for r in cur.fetchall()]

    def get_recent_customer_orders(self, customer: str, days: int = 14) -> list[dict[str, Any]]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM analyses WHERE customer = %s AND status != 'superseded' ORDER BY id DESC LIMIT 50",
                    (customer,),
                )
                return [dict(r) for r in cur.fetchall()]

    def mark_superseded(self, order_id: int) -> None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE analyses SET status = 'superseded' WHERE id = %s", (order_id,))
            conn.commit()

    def record_analysis(self, analysis: Analysis, source_file: str) -> int:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO analyses (
                        po_number, customer, status, total, source_file,
                        order_json, findings_json, revision, supersedes_order_id, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        analysis.order.po_number,
                        analysis.order.customer,
                        analysis.status,
                        str(analysis.order.total),
                        source_file,
                        json.dumps(analysis.order.to_dict(), ensure_ascii=False),
                        json.dumps([f.to_dict() for f in analysis.findings], ensure_ascii=False),
                        getattr(analysis, "revision", 1),
                        getattr(analysis, "supersedes_order_id", None),
                        datetime.now(UTC).isoformat(),
                    ),
                )
                res_id = int(cur.fetchone()["id"])
            conn.commit()
            analysis.analysis_id = res_id
            return res_id

    def record_received_order(
        self,
        po_number: str,
        customer: str,
        source_file: str,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                order_dict = {
                    "po_number": po_number,
                    "customer": customer,
                    "items": [],
                    "currency": "VND",
                    "total": 0,
                    "metadata": metadata or {},
                }
                now = datetime.now(UTC).isoformat()
                cur.execute(
                    """
                    INSERT INTO analyses (
                        po_number, customer, status, total, source_file,
                        order_json, findings_json, revision, supersedes_order_id, created_at
                    ) VALUES (%s, %s, 'received', '0', %s, %s, '[]', 1, NULL, %s)
                    RETURNING id
                    """,
                    (
                        po_number,
                        customer,
                        source_file,
                        json.dumps(order_dict, ensure_ascii=False),
                        now,
                    ),
                )
                res_id = int(cur.fetchone()["id"])
            conn.commit()
            self.append_audit_block(
                po_number,
                "ORDER_RECEIVED",
                "system:ocr_intake",
                {"source_file": source_file, "status": "received", "order_id": res_id},
            )
            return res_id

    def update_analysis(self, order_id: int, analysis: Analysis) -> None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE analyses
                    SET po_number = %s, customer = %s, status = %s, total = %s,
                        order_json = %s, findings_json = %s, revision = %s, supersedes_order_id = %s
                    WHERE id = %s
                    """,
                    (
                        analysis.order.po_number,
                        analysis.order.customer,
                        analysis.status,
                        str(analysis.order.total),
                        json.dumps(analysis.order.to_dict(), ensure_ascii=False),
                        json.dumps([f.to_dict() for f in analysis.findings], ensure_ascii=False),
                        getattr(analysis, "revision", 1),
                        getattr(analysis, "supersedes_order_id", None),
                        order_id,
                    ),
                )
            conn.commit()

    def record_decision(
        self,
        po_number: str,
        decision: str,
        actor: str,
        note: str = "",
        display_name: str | None = None,
        channel: str | None = None,
    ) -> int:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO decisions (po_number, decision, actor, note, display_name, channel, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        po_number,
                        decision,
                        actor,
                        note,
                        display_name or actor,
                        channel or "api",
                        datetime.now(UTC).isoformat(),
                    ),
                )
                d_id = int(cur.fetchone()["id"])
                if decision == "needs_changes":
                    cur.execute(
                        "UPDATE analyses SET status = %s, requested_changes = %s WHERE po_number = %s",
                        (decision, note, po_number),
                    )
                else:
                    cur.execute(
                        "UPDATE analyses SET status = %s WHERE po_number = %s",
                        (decision, po_number),
                    )
            conn.commit()
            return d_id

    def history(self, po_number: str) -> dict[str, list[dict[str, object]]]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM analyses WHERE po_number = %s ORDER BY id", (po_number,))
                analyses = [dict(r) for r in cur.fetchall()]
                cur.execute("SELECT * FROM decisions WHERE po_number = %s ORDER BY id", (po_number,))
                decisions = [dict(r) for r in cur.fetchall()]
            return {"analyses": analyses, "decisions": decisions}

    def list_orders(
        self,
        status: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
        include_superseded: bool = False,
    ) -> list[dict[str, Any]]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT a.id, a.po_number, a.customer, a.status, a.total, a.source_file,
                           a.order_json, a.findings_json, a.revision, a.supersedes_order_id, a.requested_changes, a.created_at,
                           (SELECT d.decision FROM decisions d WHERE d.po_number = a.po_number ORDER BY d.id DESC LIMIT 1) AS latest_decision,
                           (SELECT d.actor FROM decisions d WHERE d.po_number = a.po_number ORDER BY d.id DESC LIMIT 1) AS latest_actor,
                           (SELECT d.created_at FROM decisions d WHERE d.po_number = a.po_number ORDER BY d.id DESC LIMIT 1) AS decided_at
                    FROM analyses a
                    WHERE 1=1
                """
                params: list[Any] = []
                if status:
                    query += " AND a.status = %s"
                    params.append(status)
                elif not include_superseded:
                    query += " AND a.status != 'superseded'"
                if search:
                    query += " AND (a.po_number ILIKE %s OR a.customer ILIKE %s)"
                    term = f"%{search}%"
                    params.extend([term, term])
                query += " ORDER BY a.id DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                cur.execute(query, params)
                return [dict(r) for r in cur.fetchall()]

    def get_order(self, po_or_id: str | int) -> dict[str, Any] | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                if isinstance(po_or_id, int) or str(po_or_id).isdigit():
                    cur.execute("SELECT * FROM analyses WHERE id = %s LIMIT 1", (int(po_or_id),))
                else:
                    cur.execute("SELECT * FROM analyses WHERE po_number = %s ORDER BY revision DESC, id DESC LIMIT 1", (str(po_or_id),))
                row = cur.fetchone()
                if not row:
                    return None
                data = dict(row)
                po_num = data["po_number"]
                cur.execute("SELECT * FROM decisions WHERE po_number = %s ORDER BY id ASC", (po_num,))
                data["decisions"] = [dict(d) for d in cur.fetchall()]
                cur.execute(
                    "SELECT id, po_number, customer, status, total, revision, supersedes_order_id, source_file, created_at FROM analyses WHERE po_number = %s ORDER BY revision ASC, id ASC",
                    (po_num,),
                )
                data["revisions"] = [dict(r) for r in cur.fetchall()]
                return data

    def get_order_by_po(self, po_number: str) -> dict[str, Any] | None:
        return self.get_order(po_number)

    def get_dashboard_stats(self) -> dict[str, Any]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM analyses")
                total = cur.fetchone()["count"]
                cur.execute("SELECT status, COUNT(*) as count FROM analyses GROUP BY status")
                status_counts = {r["status"]: r["count"] for r in cur.fetchall()}
                cur.execute("SELECT decision, COUNT(*) as count FROM decisions GROUP BY decision")
                decisions_count = {r["decision"]: r["count"] for r in cur.fetchall()}
                cur.execute("SELECT id, po_number, customer, status, total, created_at FROM analyses ORDER BY id DESC LIMIT 5")
                recent = [dict(r) for r in cur.fetchall()]
            return {
                "total_orders": total,
                "status_counts": status_counts,
                "decisions_count": decisions_count,
                "recent_orders": recent,
            }

    def learn_alias(
        self,
        customer_id: str,
        raw_query: str,
        target_sku: str,
        confidence: float = 1.0,
    ) -> None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO sku_alias_learning (customer_id, raw_query, target_sku, confidence, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT(customer_id, raw_query) DO UPDATE SET
                        target_sku = EXCLUDED.target_sku,
                        confidence = EXCLUDED.confidence,
                        created_at = EXCLUDED.created_at
                    """,
                    (customer_id.strip(), raw_query.strip().lower(), target_sku.strip().upper(), confidence, datetime.now(UTC).isoformat()),
                )
            conn.commit()

    def get_customer_alias(self, customer_id: str, raw_query: str) -> str | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT target_sku FROM sku_alias_learning WHERE customer_id = %s AND raw_query = %s LIMIT 1",
                    (customer_id.strip(), raw_query.strip().lower()),
                )
                row = cur.fetchone()
                return str(row["target_sku"]) if row else None

    def list_customer_aliases(self, customer_id: str | None = None) -> list[dict[str, Any]]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                if customer_id:
                    cur.execute("SELECT * FROM sku_alias_learning WHERE customer_id = %s ORDER BY id DESC", (customer_id.strip(),))
                else:
                    cur.execute("SELECT * FROM sku_alias_learning ORDER BY id DESC")
                return [dict(r) for r in cur.fetchall()]

    def append_audit_block(
        self,
        po_number: str,
        action: str,
        actor: str,
        payload: dict[str, Any],
        timestamp: float | None = None,
    ) -> dict[str, Any]:
        with self._pool.connection() as conn:
            t = timestamp if timestamp is not None else time.time()
            from preflight.observability.context import get_request_id
            req_id = get_request_id()
            if req_id and isinstance(payload, dict) and "request_id" not in payload:
                payload = dict(payload)
                payload["request_id"] = req_id

            with conn.cursor() as cur:
                cur.execute(
                    "SELECT block_index, block_hash FROM audit_blocks WHERE po_number = %s ORDER BY block_index DESC LIMIT 1",
                    (po_number,),
                )
                last_row = cur.fetchone()
                if last_row:
                    idx = last_row["block_index"] + 1
                    prev_hash = last_row["block_hash"]
                else:
                    idx = 0
                    prev_hash = "0000000000000000000000000000000000000000000000000000000000000000"

                p_hash = compute_payload_hash(payload)
                b_hash = calculate_hash(idx, t, po_number, action, actor, p_hash, prev_hash)

                cur.execute(
                    """
                    INSERT INTO audit_blocks (block_index, timestamp, po_number, action, actor, payload_hash, previous_hash, block_hash)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (idx, t, po_number, action, actor, p_hash, prev_hash, b_hash),
                )
            conn.commit()
            return {
                "index": idx,
                "timestamp": t,
                "po_number": po_number,
                "action": action,
                "actor": actor,
                "payload_hash": p_hash,
                "previous_hash": prev_hash,
                "block_hash": b_hash,
            }

    def get_audit_blocks(self, po_number: str) -> list[dict[str, Any]]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT block_index as index, timestamp, po_number, action, actor, payload_hash, previous_hash, block_hash FROM audit_blocks WHERE po_number = %s ORDER BY block_index ASC",
                    (po_number,),
                )
                return [dict(r) for r in cur.fetchall()]

    def list_audit_events(
        self,
        limit: int = 50,
        offset: int = 0,
        po_number: str | None = None,
        actor: str | None = None,
        action: str | None = None,
    ) -> list[dict[str, Any]]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT 
                        'block_' || id::text AS id,
                        'AUDIT_BLOCK' AS event_type,
                        to_timestamp(timestamp)::text AS timestamp,
                        po_number,
                        action,
                        actor,
                        'Block #' || block_index::text || ' (Hash: ' || substring(block_hash from 1 for 12) || '...)' AS detail,
                        block_hash AS hash
                    FROM audit_blocks
                    UNION ALL
                    SELECT
                        'decision_' || id::text AS id,
                        'DECISION' AS event_type,
                        created_at::text AS timestamp,
                        po_number,
                        UPPER(decision) AS action,
                        actor,
                        COALESCE(note, '') AS detail,
                        NULL AS hash
                    FROM decisions
                """
                params: list[Any] = []
                where_clauses: list[str] = []
                if po_number:
                    where_clauses.append("po_number ILIKE %s")
                    params.append(f"%{po_number}%")
                if actor:
                    where_clauses.append("actor ILIKE %s")
                    params.append(f"%{actor}%")
                if action:
                    where_clauses.append("action = %s")
                    params.append(action.upper())

                outer_query = f"SELECT * FROM ({query}) sub"
                if where_clauses:
                    outer_query += " WHERE " + " AND ".join(where_clauses)
                outer_query += " ORDER BY timestamp DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])

                cur.execute(outer_query, params)
                return [dict(r) for r in cur.fetchall()]

    def set_customer_pricing(self, pricing: CustomerPriceAgreement) -> None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO customer_pricing (customer_id, sku, contract_price, min_quantity, discount_percent, valid_from, valid_to, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT(customer_id, sku, min_quantity) DO UPDATE SET
                        contract_price = EXCLUDED.contract_price,
                        discount_percent = EXCLUDED.discount_percent,
                        valid_from = EXCLUDED.valid_from,
                        valid_to = EXCLUDED.valid_to,
                        created_at = EXCLUDED.created_at
                    """,
                    (
                        pricing.customer_id.strip(),
                        pricing.sku.strip().upper(),
                        str(pricing.contract_price),
                        pricing.min_quantity,
                        str(pricing.discount_percent),
                        pricing.valid_from,
                        pricing.valid_to,
                        datetime.now(UTC).isoformat(),
                    ),
                )
            conn.commit()

    def get_customer_pricing(self, customer_id: str) -> list[CustomerPriceAgreement]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM customer_pricing WHERE customer_id = %s ORDER BY sku ASC, min_quantity DESC",
                    (customer_id.strip(),),
                )
                return [
                    CustomerPriceAgreement(
                        customer_id=r["customer_id"],
                        sku=r["sku"],
                        contract_price=Decimal(r["contract_price"]),
                        min_quantity=int(r["min_quantity"]),
                        discount_percent=Decimal(r["discount_percent"]),
                        valid_from=r["valid_from"],
                        valid_to=r["valid_to"],
                    )
                    for r in cur.fetchall()
                ]

    def set_uom_conversion(self, conversion: UOMConversion) -> None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO uom_conversions (sku, uom_code, base_uom, conversion_factor, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT(sku, uom_code) DO UPDATE SET
                        base_uom = EXCLUDED.base_uom,
                        conversion_factor = EXCLUDED.conversion_factor,
                        created_at = EXCLUDED.created_at
                    """,
                    (
                        conversion.sku.strip().upper(),
                        conversion.uom_code.strip().upper(),
                        conversion.base_uom.strip().upper(),
                        str(conversion.conversion_factor),
                        datetime.now(UTC).isoformat(),
                    ),
                )
            conn.commit()

    def get_uom_conversions(self, sku: str | None = None) -> list[UOMConversion]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                if sku:
                    cur.execute(
                        "SELECT * FROM uom_conversions WHERE sku = %s ORDER BY uom_code ASC",
                        (sku.strip().upper(),),
                    )
                else:
                    cur.execute("SELECT * FROM uom_conversions ORDER BY sku ASC, uom_code ASC")
                return [
                    UOMConversion(
                        sku=r["sku"],
                        uom_code=r["uom_code"],
                        base_uom=r["base_uom"],
                        conversion_factor=Decimal(r["conversion_factor"]),
                    )
                    for r in cur.fetchall()
                ]

    def set_customer_credit(self, credit: CustomerCreditProfile) -> None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO customer_credits (customer_id, credit_limit, outstanding_balance, overdue_balance, oldest_overdue_days, status, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT(customer_id) DO UPDATE SET
                        credit_limit = EXCLUDED.credit_limit,
                        outstanding_balance = EXCLUDED.outstanding_balance,
                        overdue_balance = EXCLUDED.overdue_balance,
                        oldest_overdue_days = EXCLUDED.oldest_overdue_days,
                        status = EXCLUDED.status,
                        updated_at = EXCLUDED.updated_at
                    """,
                    (
                        credit.customer_id.strip(),
                        str(credit.credit_limit),
                        str(credit.outstanding_balance),
                        str(credit.overdue_balance),
                        credit.oldest_overdue_days,
                        credit.status,
                        datetime.now(UTC).isoformat(),
                    ),
                )
            conn.commit()

    def get_customer_credit(self, customer_id: str) -> CustomerCreditProfile | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM customer_credits WHERE customer_id = %s LIMIT 1",
                    (customer_id.strip(),),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return CustomerCreditProfile(
                    customer_id=row["customer_id"],
                    credit_limit=Decimal(row["credit_limit"]),
                    outstanding_balance=Decimal(row["outstanding_balance"]),
                    overdue_balance=Decimal(row["overdue_balance"]),
                    oldest_overdue_days=int(row["oldest_overdue_days"]),
                    status=row["status"],
                )

    def set_policy(self, policy: RulePolicy, updated_by: str = "system") -> None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO rule_policies (id, policy_json, updated_at, updated_by)
                    VALUES (1, %s, %s, %s)
                    ON CONFLICT(id) DO UPDATE SET
                        policy_json = EXCLUDED.policy_json,
                        updated_at = EXCLUDED.updated_at,
                        updated_by = EXCLUDED.updated_by
                    """,
                    (json.dumps(policy.to_dict()), datetime.now(UTC).isoformat(), updated_by),
                )
            conn.commit()

    def get_policy(self) -> RulePolicy:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT policy_json FROM rule_policies WHERE id = 1 LIMIT 1")
                row = cur.fetchone()
                if not row:
                    return RulePolicy()
                val = row["policy_json"]
                data = json.loads(val) if isinstance(val, str) else val
                return RulePolicy.from_dict(data)

    def get_channel_identity(self, channel: str, external_id: str) -> dict[str, Any] | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM channel_identities WHERE channel = %s AND external_id = %s LIMIT 1",
                    (channel.strip().lower(), str(external_id).strip()),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return dict(row)

    def upsert_channel_identity(
        self,
        channel: str,
        external_id: str,
        user_id: str,
        display_name: str,
        role: str,
    ) -> None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO channel_identities (channel, external_id, user_id, display_name, role, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT(channel, external_id) DO UPDATE SET
                        user_id = EXCLUDED.user_id,
                        display_name = EXCLUDED.display_name,
                        role = EXCLUDED.role,
                        created_at = EXCLUDED.created_at
                    """,
                    (
                        channel.strip().lower(),
                        str(external_id).strip(),
                        user_id.strip(),
                        display_name.strip(),
                        role.strip().upper(),
                        datetime.now(UTC).isoformat(),
                    ),
                )
            conn.commit()

    def create_channel_link_code(
        self, user_id: str, display_name: str, role: str, expires_in_seconds: int = 600
    ) -> str:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                import secrets
                code = secrets.token_hex(3).upper()
                expires_at = time.time() + expires_in_seconds
                role_str = getattr(role, "name", str(role)).strip().upper()
                cur.execute(
                    """
                    INSERT INTO channel_link_codes (code, user_id, display_name, role, expires_at, used)
                    VALUES (%s, %s, %s, %s, %s, 0)
                    ON CONFLICT(code) DO UPDATE SET
                        user_id = EXCLUDED.user_id,
                        display_name = EXCLUDED.display_name,
                        role = EXCLUDED.role,
                        expires_at = EXCLUDED.expires_at,
                        used = 0
                    """,
                    (code, str(user_id).strip(), str(display_name).strip(), role_str, expires_at),
                )
            conn.commit()
            return code

    def consume_channel_link_code(self, code: str) -> dict[str, Any] | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                clean_code = code.strip().upper()
                cur.execute(
                    "SELECT * FROM channel_link_codes WHERE code = %s LIMIT 1", (clean_code,)
                )
                row = cur.fetchone()
                if not row:
                    return None
                record = dict(row)
                if record.get("used"):
                    return None
                if time.time() > float(record["expires_at"]):
                    return {"expired": True, "user_id": record["user_id"]}
                cur.execute(
                    "UPDATE channel_link_codes SET used = 1 WHERE code = %s", (clean_code,)
                )
            conn.commit()
            return {
                "expired": False,
                "user_id": record["user_id"],
                "display_name": record["display_name"],
                "role": record["role"],
            }

    def record_processed_webhook_event(self, channel: str, event_id: str) -> bool:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                chan = channel.strip().lower()
                ev_id = str(event_id).strip()
                cur.execute(
                    "SELECT 1 FROM processed_webhook_events WHERE channel = %s AND event_id = %s LIMIT 1",
                    (chan, ev_id),
                )
                if cur.fetchone():
                    return False
                cur.execute(
                    "INSERT INTO processed_webhook_events (channel, event_id, processed_at) VALUES (%s, %s, %s)",
                    (chan, ev_id, time.time()),
                )
            conn.commit()
            return True

    def save_product_embedding(self, sku: str, vector_bytes: bytes, text_hash: str) -> None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO product_embeddings (sku, vector_blob, text_hash, updated_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT(sku) DO UPDATE SET
                        vector_blob = EXCLUDED.vector_blob,
                        text_hash = EXCLUDED.text_hash,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (sku.strip().upper(), vector_bytes, text_hash),
                )
            conn.commit()

    def get_product_embeddings(self) -> list[dict[str, Any]]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT sku, vector_blob, text_hash, updated_at FROM product_embeddings")
                rows = cur.fetchall()
                return [dict(r) for r in rows]

    def get_product_embedding(self, sku: str) -> dict[str, Any] | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT sku, vector_blob, text_hash, updated_at FROM product_embeddings WHERE sku = %s LIMIT 1",
                    (sku.strip().upper(),),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return dict(row)

    def create_lead(
        self,
        name: str,
        company: str,
        phone: str,
        email: str,
        erp: str | None,
        volume: str | None,
        note: str | None,
        ip_hash: str,
    ) -> dict[str, Any]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO leads (name, company, phone, email, erp, volume, note, ip_hash)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, name, company, phone, email, erp, volume, note, ip_hash, created_at
                    """,
                    (name, company, phone, email, erp, volume, note, ip_hash),
                )
                row = cur.fetchone()
                conn.commit()
                if row:
                    res = dict(row)
                    if isinstance(res.get("created_at"), datetime):
                        res["created_at"] = res["created_at"].isoformat()
                    return res
                return {}

    def list_leads(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM leads ORDER BY id DESC LIMIT %s OFFSET %s",
                    (limit, offset),
                )
                rows = cur.fetchall()
                result = []
                for r in rows:
                    d = dict(r)
                    if isinstance(d.get("created_at"), datetime):
                        d["created_at"] = d["created_at"].isoformat()
                    result.append(d)
                return result

    def create_customer(self, customer: CustomerMaster) -> CustomerMaster:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                norm_name = customer.normalized_name or normalize_vietnamese_name(customer.name)
                emails_str = ",".join(customer.contact_emails) if customer.contact_emails else ""
                cur.execute(
                    """
                    INSERT INTO customers (code, name, normalized_name, tax_code, tier, contact_emails)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id, code, name, normalized_name, tax_code, tier, contact_emails, created_at
                    """,
                    (customer.code.strip(), customer.name.strip(), norm_name, customer.tax_code, customer.tier, emails_str),
                )
                row = cur.fetchone()
                conn.commit()
                for alias in customer.aliases:
                    if alias and alias.strip():
                        self.add_customer_alias(customer.code, alias.strip())
                res = dict(row)
                if isinstance(res.get("created_at"), datetime):
                    res["created_at"] = res["created_at"].isoformat()
                return CustomerMaster(
                    id=res["id"],
                    code=res["code"],
                    name=res["name"],
                    normalized_name=res["normalized_name"],
                    tax_code=res.get("tax_code"),
                    tier=res["tier"],
                    aliases=list(customer.aliases),
                    contact_emails=list(customer.contact_emails),
                    created_at=res["created_at"],
                )

    def add_customer_alias(self, customer_id: str, alias: str) -> None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                norm_alias = normalize_vietnamese_name(alias)
                cur.execute(
                    """
                    INSERT INTO customer_aliases (customer_id, alias, normalized_alias)
                    VALUES (%s, %s, %s)
                    ON CONFLICT(customer_id, normalized_alias) DO UPDATE SET
                        alias = EXCLUDED.alias,
                        created_at = CURRENT_TIMESTAMP
                    """,
                    (customer_id.strip(), alias.strip(), norm_alias),
                )
            conn.commit()

    def get_customer(self, code: str) -> CustomerMaster | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                if str(code).isdigit():
                    cur.execute("SELECT * FROM customers WHERE code = %s OR id = %s LIMIT 1", (str(code).strip(), int(code)))
                else:
                    cur.execute("SELECT * FROM customers WHERE code = %s LIMIT 1", (str(code).strip(),))
                row = cur.fetchone()
                if not row:
                    return None
                cur.execute("SELECT alias FROM customer_aliases WHERE customer_id = %s", (row["code"],))
                alias_rows = cur.fetchall()
                aliases = [r["alias"] for r in alias_rows]
                created_at = row["created_at"].isoformat() if isinstance(row.get("created_at"), datetime) else str(row.get("created_at"))
                raw_emails = row.get("contact_emails") or ""
                email_list = [e.strip() for e in raw_emails.replace(";", ",").split(",") if e.strip()]
                return CustomerMaster(
                    id=row["id"],
                    code=row["code"],
                    name=row["name"],
                    normalized_name=row["normalized_name"],
                    tax_code=row.get("tax_code"),
                    tier=row["tier"],
                    aliases=aliases,
                    contact_emails=email_list,
                    created_at=created_at,
                )

    def get_customer_by_id(self, customer_id: int) -> CustomerMaster | None:
        return self.get_customer(str(customer_id))

    def get_customer_by_tax_code(self, tax_code: str) -> CustomerMaster | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                clean = tax_code.strip().replace(" ", "").replace("-", "")
                cur.execute("SELECT code FROM customers WHERE tax_code = %s LIMIT 1", (clean,))
                row = cur.fetchone()
                if not row:
                    return None
                return self.get_customer(row["code"])

    def get_customer_by_normalized_name(self, norm_name: str) -> CustomerMaster | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                clean = norm_name.strip()
                cur.execute("SELECT code FROM customers WHERE normalized_name = %s LIMIT 1", (clean,))
                row = cur.fetchone()
                if row:
                    return self.get_customer(row["code"])
                cur.execute("SELECT customer_id FROM customer_aliases WHERE normalized_alias = %s LIMIT 1", (clean,))
                alias_row = cur.fetchone()
                if alias_row:
                    return self.get_customer(alias_row["customer_id"])
                return None

    def get_customer_by_contact_email(self, email: str) -> CustomerMaster | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                clean = email.strip().lower()
                if not clean:
                    return None
                cur.execute("SELECT code, contact_emails FROM customers")
                rows = cur.fetchall()
                for r in rows:
                    raw_emails = r.get("contact_emails") or ""
                    email_list = [e.strip().lower() for e in raw_emails.replace(";", ",").split(",") if e.strip()]
                    if clean in email_list:
                        return self.get_customer(r["code"])
                return None

    def list_customers(self, search: str | None = None, limit: int = 50, offset: int = 0) -> list[CustomerMaster]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                if search:
                    pattern = f"%{search.strip()}%"
                    cur.execute(
                        """
                        SELECT DISTINCT c.code FROM customers c
                        LEFT JOIN customer_aliases a ON a.customer_id = c.code
                        WHERE c.name ILIKE %s OR c.code ILIKE %s OR c.tax_code ILIKE %s OR c.normalized_name ILIKE %s OR a.alias ILIKE %s
                        ORDER BY c.code ASC LIMIT %s OFFSET %s
                        """,
                        (pattern, pattern, pattern, pattern, pattern, limit, offset),
                    )
                else:
                    cur.execute("SELECT code FROM customers ORDER BY id DESC LIMIT %s OFFSET %s", (limit, offset))
                rows = cur.fetchall()
                result = []
                for r in rows:
                    cust = self.get_customer(r["code"])
                    if cust:
                        result.append(cust)
                return result

    def update_customer(self, code: str, data: dict[str, Any]) -> CustomerMaster | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cust = self.get_customer(code)
                if not cust:
                    return None
                new_name = data.get("name", cust.name).strip()
                new_norm = normalize_vietnamese_name(new_name)
                new_tax = data.get("tax_code", cust.tax_code)
                new_tier = data.get("tier", cust.tier)
                if "contact_emails" in data:
                    emails_val = data["contact_emails"]
                    if isinstance(emails_val, list):
                        emails_str = ",".join(emails_val)
                    else:
                        emails_str = str(emails_val or "")
                else:
                    emails_str = ",".join(cust.contact_emails)

                cur.execute(
                    """
                    UPDATE customers SET name = %s, normalized_name = %s, tax_code = %s, tier = %s, contact_emails = %s
                    WHERE code = %s
                    """,
                    (new_name, new_norm, new_tax, new_tier, emails_str, cust.code),
                )
                if "aliases" in data:
                    cur.execute("DELETE FROM customer_aliases WHERE customer_id = %s", (cust.code,))
                    for a in data["aliases"]:
                        if a and a.strip():
                            self.add_customer_alias(cust.code, a.strip())
            conn.commit()
            return self.get_customer(cust.code)

    def delete_customer(self, code: str) -> bool:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cust = self.get_customer(code)
                if not cust:
                    return False
                cur.execute("DELETE FROM customers WHERE code = %s", (cust.code,))
                cur.execute("DELETE FROM customer_aliases WHERE customer_id = %s", (cust.code,))
            conn.commit()
            return True

    def list_customer_master_aliases(self, customer_id: str | None = None) -> list[dict[str, Any]]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                if customer_id:
                    cur.execute("SELECT * FROM customer_aliases WHERE customer_id = %s ORDER BY id DESC", (customer_id.strip(),))
                else:
                    cur.execute("SELECT * FROM customer_aliases ORDER BY id DESC")
                rows = cur.fetchall()
                return [dict(r) for r in rows]

    def create_user(self, user: User) -> User:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (org_id, username, display_name, email, password_hash, role, is_active, failed_attempts, locked_until)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT(username) DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        email = EXCLUDED.email,
                        password_hash = COALESCE(EXCLUDED.password_hash, users.password_hash),
                        role = EXCLUDED.role,
                        is_active = EXCLUDED.is_active
                    """,
                    (
                        user.org_id,
                        user.username.strip().lower(),
                        user.display_name.strip(),
                        user.email.strip().lower(),
                        user.password_hash,
                        user.role.strip().lower(),
                        user.is_active,
                        user.failed_attempts,
                        user.locked_until,
                    ),
                )
            conn.commit()
            return self.get_user(user.username) or user

    def get_user(self, username: str) -> User | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE username = %s LIMIT 1", (username.strip().lower(),))
                row = cur.fetchone()
                if not row:
                    return None
                created_at = row["created_at"].isoformat() if isinstance(row.get("created_at"), datetime) else str(row.get("created_at"))
                locked_until = row["locked_until"].isoformat() if isinstance(row.get("locked_until"), datetime) else (str(row.get("locked_until")) if row.get("locked_until") else None)
                return User(
                    id=row["id"],
                    org_id=row["org_id"],
                    username=row["username"],
                    display_name=row["display_name"],
                    email=row["email"],
                    password_hash=row["password_hash"],
                    role=row["role"],
                    is_active=bool(row["is_active"]),
                    failed_attempts=int(row.get("failed_attempts", 0)),
                    locked_until=locked_until,
                    created_at=created_at,
                )

    def get_user_by_id(self, user_id: int) -> User | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE id = %s LIMIT 1", (user_id,))
                row = cur.fetchone()
                if not row:
                    return None
                created_at = row["created_at"].isoformat() if isinstance(row.get("created_at"), datetime) else str(row.get("created_at"))
                locked_until = row["locked_until"].isoformat() if isinstance(row.get("locked_until"), datetime) else (str(row.get("locked_until")) if row.get("locked_until") else None)
                return User(
                    id=row["id"],
                    org_id=row["org_id"],
                    username=row["username"],
                    display_name=row["display_name"],
                    email=row["email"],
                    password_hash=row["password_hash"],
                    role=row["role"],
                    is_active=bool(row["is_active"]),
                    failed_attempts=int(row.get("failed_attempts", 0)),
                    locked_until=locked_until,
                    created_at=created_at,
                )

    def list_users(self) -> list[User]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT username FROM users ORDER BY id ASC")
                rows = cur.fetchall()
                results = []
                for r in rows:
                    u = self.get_user(r["username"])
                    if u:
                        results.append(u)
                return results

    def update_user(
        self,
        username: str,
        display_name: str | None = None,
        email: str | None = None,
        role: str | None = None,
        password_hash: str | None = None,
        is_active: bool | None = None,
    ) -> User | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                user = self.get_user(username)
                if not user:
                    return None
                new_disp = display_name if display_name is not None else user.display_name
                new_email = email if email is not None else user.email
                new_role = role if role is not None else user.role
                new_pwd = password_hash if password_hash is not None else user.password_hash
                new_active = is_active if is_active is not None else user.is_active

                cur.execute(
                    """
                    UPDATE users
                    SET display_name = %s, email = %s, role = %s, password_hash = %s, is_active = %s
                    WHERE username = %s
                    """,
                    (new_disp.strip(), new_email.strip().lower(), new_role.strip().lower(), new_pwd, new_active, username.strip().lower()),
                )
            conn.commit()
            return self.get_user(username)

    def delete_user(self, username: str) -> bool:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE username = %s", (username.strip().lower(),))
                affected = cur.rowcount > 0
            conn.commit()
            return affected

    def record_failed_login(self, username: str) -> int:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT failed_attempts FROM users WHERE username = %s", (username.strip().lower(),))
                row = cur.fetchone()
                if not row:
                    return 0
                attempts = int(row.get("failed_attempts", 0)) + 1
                locked_until = None
                if attempts >= 5:
                    locked_until = datetime.fromtimestamp(time.time() + 900, tz=UTC)
                cur.execute(
                    "UPDATE users SET failed_attempts = %s, locked_until = %s WHERE username = %s",
                    (attempts, locked_until, username.strip().lower()),
                )
            conn.commit()
            return attempts

    def reset_failed_logins(self, username: str) -> None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE username = %s", (username.strip().lower(),))
            conn.commit()

    def is_user_locked(self, username: str) -> bool:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT locked_until FROM users WHERE username = %s", (username.strip().lower(),))
                row = cur.fetchone()
                if not row or not row.get("locked_until"):
                    return False
                try:
                    locked_val = row["locked_until"]
                    locked_dt = locked_val if isinstance(locked_val, datetime) else datetime.fromisoformat(str(locked_val))
                    if locked_dt.tzinfo is None:
                        locked_dt = locked_dt.replace(tzinfo=UTC)
                    if locked_dt > datetime.now(UTC):
                        return True
                    else:
                        self.reset_failed_logins(username)
                        return False
                except Exception:
                    return False

    def seed_initial_admin(self) -> None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS c FROM users")
                row = cur.fetchone()
                count = int(row["c"]) if row else 0
                if count == 0:
                    defaults = [
                        User(
                            username="admin",
                            display_name="Hệ Thống Quản Trị",
                            email="admin@preflight.vn",
                            password_hash=hash_password("Admin@123456"),
                            role="admin",
                            created_at=datetime.now(UTC).isoformat(),
                        ),
                        User(
                            username="director",
                            display_name="Giám Đốc Phê Duyệt",
                            email="director@preflight.vn",
                            password_hash=hash_password("Director@123456"),
                            role="director",
                            created_at=datetime.now(UTC).isoformat(),
                        ),
                        User(
                            username="manager",
                            display_name="Trưởng Phòng Vận Hành",
                            email="manager@preflight.vn",
                            password_hash=hash_password("Manager@123456"),
                            role="manager",
                            created_at=datetime.now(UTC).isoformat(),
                        ),
                        User(
                            username="sales_admin",
                            display_name="Nhân Viên Sales Admin",
                            email="sales@preflight.vn",
                            password_hash=hash_password("Sales@123456"),
                            role="sales_admin",
                            created_at=datetime.now(UTC).isoformat(),
                        ),
                        User(
                            username="auditor",
                            display_name="Kiểm Toán Viên",
                            email="auditor@preflight.vn",
                            password_hash=hash_password("Auditor@123456"),
                            role="auditor",
                            created_at=datetime.now(UTC).isoformat(),
                        ),
                        User(
                            username="viewer",
                            display_name="Người Xem Báo Cáo",
                            email="viewer@preflight.vn",
                            password_hash=hash_password("Viewer@123456"),
                            role="viewer",
                            created_at=datetime.now(UTC).isoformat(),
                        ),
                    ]
                    for u in defaults:
                        self.create_user(u)

    def record_inventory_snapshots(self, snapshots: list[InventorySnapshot]) -> int:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                count = 0
                now_iso = datetime.now(UTC).isoformat()
                for s in snapshots:
                    as_of_val = s.as_of or now_iso
                    cur.execute(
                        """
                        INSERT INTO inventory_snapshots (sku, warehouse, on_hand, reserved, as_of, source, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (s.sku.strip(), s.warehouse.strip(), str(s.on_hand), str(s.reserved), as_of_val, s.source.strip(), now_iso),
                    )
                    count += 1
            conn.commit()
            return count

    def get_latest_inventory_snapshots(self, skus: list[str] | None = None) -> dict[str, InventorySnapshot]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                if skus:
                    clean_skus = [s.strip() for s in skus if s]
                    if not clean_skus:
                        return {}
                    cur.execute(
                        """
                        SELECT id, sku, warehouse, on_hand, reserved, as_of, source
                        FROM inventory_snapshots
                        WHERE sku = ANY(%s)
                        ORDER BY id DESC
                        """,
                        (clean_skus,),
                    )
                else:
                    cur.execute(
                        """
                        SELECT id, sku, warehouse, on_hand, reserved, as_of, source
                        FROM inventory_snapshots
                        ORDER BY id DESC
                        """
                    )
                rows = cur.fetchall()
                snapshots: dict[str, InventorySnapshot] = {}
                for r in rows:
                    sku = r["sku"]
                    if sku not in snapshots:
                        as_of_str = r["as_of"].isoformat() if isinstance(r["as_of"], datetime) else str(r["as_of"])
                        snapshots[sku] = InventorySnapshot(
                            id=r["id"],
                            sku=sku,
                            warehouse=r["warehouse"],
                            on_hand=Decimal(str(r["on_hand"])),
                            reserved=Decimal(str(r["reserved"])),
                            as_of=as_of_str,
                            source=r["source"],
                        )
                return snapshots

    def get_inventory_snapshot(self, sku: str) -> InventorySnapshot | None:
        snaps = self.get_latest_inventory_snapshots(skus=[sku])
        return snaps.get(sku.strip())

    def get_all_allocated_local_stock(self) -> dict[str, Decimal]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT a.id, a.po_number, a.order_json
                    FROM analyses a
                    WHERE LOWER(a.status) = 'approved'
                    """
                )
                rows = cur.fetchall()
                sent_pos = set()
                try:
                    cur.execute("SELECT po_number FROM erp_outbox WHERE status = 'SENT'")
                    sent_rows = cur.fetchall()
                    sent_pos = {r["po_number"] for r in sent_rows if r["po_number"]}
                except Exception:
                    pass

                uom_conversions = self.get_uom_conversions()
                uom_map = {(u.sku, u.uom_code): u.conversion_factor for u in uom_conversions}

                allocations: dict[str, Decimal] = {}
                for r in rows:
                    po_num = r["po_number"]
                    if po_num in sent_pos:
                        continue
                    raw_json = r["order_json"]
                    if not raw_json:
                        continue
                    od = json.loads(raw_json) if isinstance(raw_json, str) else raw_json
                    items = od.get("items", [])
                    for item in items:
                        sku = item.get("sku", "").strip()
                        if not sku:
                            continue
                        qty = Decimal(str(item.get("quantity", 0)))
                        uom = str(item.get("uom", "PCS")).strip().upper()
                        factor = uom_map.get((sku, uom), Decimal("1.0"))
                        base_qty = qty * factor
                        allocations[sku] = allocations.get(sku, Decimal("0")) + base_qty

                return allocations

    def get_allocated_local_stock(self, sku: str) -> Decimal:
        return self.get_all_allocated_local_stock().get(sku.strip(), Decimal("0"))

    def calculate_atp(self, sku: str, catalog_stock: Decimal | int = Decimal("0")) -> dict[str, Any]:
        snapshot = self.get_inventory_snapshot(sku)
        allocated = self.get_allocated_local_stock(sku)
        if snapshot:
            on_hand = snapshot.on_hand
            reserved = snapshot.reserved
            as_of = snapshot.as_of
            source = snapshot.source
        else:
            on_hand = Decimal(str(catalog_stock))
            reserved = Decimal("0")
            as_of = ""
            source = "catalog"

        atp = max(Decimal("0"), on_hand - reserved - allocated)
        is_stale = False
        if as_of:
            try:
                dt = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
                age_hours = (datetime.now(UTC) - dt).total_seconds() / 3600.0
                policy = self.get_policy()
                if age_hours > policy.inventory_stale_hours:
                    is_stale = True
            except Exception:
                pass

        return {
            "sku": sku,
            "on_hand": on_hand,
            "reserved_erp": reserved,
            "allocated_local": allocated,
            "atp": atp,
            "as_of": as_of,
            "source": source,
            "is_stale": is_stale,
        }

    def record_request_error(
        self,
        request_id: str,
        endpoint: str,
        status_code: int,
        error_message: str,
        traceback_str: str = "",
    ) -> None:
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO request_errors (request_id, endpoint, status_code, error_message, traceback)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (request_id, endpoint, status_code, error_message, traceback_str),
            )
            cur.execute(
                """
                DELETE FROM request_errors
                WHERE created_at < NOW() - INTERVAL '7 days'
                """
            )

    def get_recent_request_errors(self, limit: int = 10) -> list[dict[str, Any]]:
        with self._cursor() as cur:
            cur.execute(
                """
                SELECT id, request_id, endpoint, status_code, error_message, traceback, created_at
                FROM request_errors
                ORDER BY id DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def record_email_inbox_log(
        self,
        message_id: str,
        sender: str,
        subject: str,
        received_at: str,
        attachments_count: int = 0,
        orders_created: int = 0,
        status: str = "PROCESSED",
        error_message: str | None = None,
    ) -> None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO email_inbox_logs (message_id, sender, subject, received_at, attachments_count, orders_created, status, error_message, attempts, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(message_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        orders_created = EXCLUDED.orders_created,
                        error_message = EXCLUDED.error_message,
                        attempts = email_inbox_logs.attempts + 1
                    """,
                    (message_id, sender, subject, received_at, attachments_count, orders_created, status, error_message),
                )
            conn.commit()

    def get_email_inbox_log(self, message_id: str) -> dict[str, Any] | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM email_inbox_logs WHERE message_id = %s LIMIT 1",
                    (message_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def list_email_inbox_logs(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM email_inbox_logs ORDER BY id DESC LIMIT %s",
                    (limit,),
                )
                rows = cur.fetchall()
                return [dict(r) for r in rows]









def create_audit_store(database_url_or_path: str | Path | None = None) -> BaseAuditStore:
    """Factory helper creating the appropriate database adapter based on connection string."""
    target = database_url_or_path or os.getenv("DATABASE_URL") or "runtime/preflight.db"
    target_str = str(target).strip()

    if target_str.startswith("postgresql://") or target_str.startswith("postgres://") or target_str.startswith("postgresql+asyncpg://"):
        return PostgresAuditStore(database_url=target_str)
    
    if target_str.startswith("sqlite:///"):
        target_str = target_str.replace("sqlite:///", "")

    return AuditStore(path=target_str)
