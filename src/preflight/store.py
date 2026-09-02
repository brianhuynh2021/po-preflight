from __future__ import annotations

import abc
import json
import os
import sqlite3
import threading
import time
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from preflight.api.errors import ConfigurationError
from preflight.models import (
    Analysis,
    CustomerCreditProfile,
    CustomerPriceAgreement,
    RulePolicy,
    UOMConversion,
)

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
    created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_analyses_po ON analyses(po_number);
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_pg_analyses_po ON analyses(po_number);


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
    def has_po(self, po_number: str) -> bool:
        pass

    @abc.abstractmethod
    def record_analysis(self, analysis: Analysis, source_file: str) -> int:
        pass

    @abc.abstractmethod
    def update_analysis(self, order_id: int, analysis: Analysis) -> None:
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
                # Deduplicate legacy rows before applying unique constraint index
                self.connection.execute(
                    "DELETE FROM analyses WHERE id NOT IN (SELECT MAX(id) FROM analyses GROUP BY po_number)"
                )
                self.connection.commit()
            except Exception:
                pass
            self.connection.executescript(SQLITE_SCHEMA)
            try:
                self.connection.execute("ALTER TABLE decisions ADD COLUMN display_name TEXT;")
            except Exception:
                pass
            try:
                self.connection.execute("ALTER TABLE decisions ADD COLUMN channel TEXT;")
            except Exception:
                pass
            self.connection.commit()


    def close(self) -> None:
        with self._lock:
            self.connection.close()

    def has_po(self, po_number: str) -> bool:
        with self._lock:
            row = self.connection.execute(
                "SELECT 1 FROM analyses WHERE po_number = ? LIMIT 1", (po_number,)
            ).fetchone()
            return row is not None

    def record_analysis(self, analysis: Analysis, source_file: str) -> int:
        with self._lock:
            try:
                cursor = self.connection.cursor()
                cursor.execute(
                    """
                    INSERT INTO analyses (
                        po_number, customer, status, total, source_file,
                        order_json, findings_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
                        datetime.now(UTC).isoformat(),
                    ),
                )
                self.connection.commit()
                self.append_audit_block(
                    analysis.order.po_number,
                    "ORDER_INGESTED",
                    "system:ingestion_pipeline",
                    {"total": str(analysis.order.total), "status": analysis.status},
                )
                if cursor.lastrowid is not None:
                    analysis.analysis_id = int(cursor.lastrowid)
                    return analysis.analysis_id
                existing = self.get_order(analysis.order.po_number)
                if existing:
                    analysis.analysis_id = int(existing["id"])
                    return analysis.analysis_id
                return 0
            except (sqlite3.IntegrityError, sqlite3.OperationalError):
                # Concurrent race condition: another thread/worker inserted the exact same PO number
                existing = self.get_order(analysis.order.po_number)
                if existing:
                    dup_finding = {
                        "code": "DUPLICATE_PO",
                        "severity": "error",
                        "message": f"PO {analysis.order.po_number} has already been processed.",
                    }
                    raw_findings = existing.get("findings_json") or "[]"
                    findings_list = json.loads(raw_findings) if isinstance(raw_findings, str) else raw_findings
                    if not any(isinstance(f, dict) and f.get("code") == "DUPLICATE_PO" for f in findings_list):
                        findings_list.append(dup_finding)
                    self.connection.execute(
                        "UPDATE analyses SET status = 'blocked', findings_json = ? WHERE id = ?",
                        (json.dumps(findings_list, ensure_ascii=False), existing["id"]),
                    )
                    self.connection.commit()
                    analysis.analysis_id = int(existing["id"])
                    analysis.status = "blocked"
                    return analysis.analysis_id
                raise



    def update_analysis(self, order_id: int, analysis: Analysis) -> None:
        """Update an existing analysis with confirmed order details and preflight findings."""
        with self._lock:
            with self.connection:
                self.connection.execute(
                    """
                    UPDATE analyses
                    SET po_number = ?, customer = ?, status = ?, total = ?,
                        order_json = ?, findings_json = ?
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
            if search:
                query += " AND (a.po_number LIKE ? OR a.customer LIKE ?)"
                term = f"%{search}%"
                params.extend([term, term])

            query += " ORDER BY a.id DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            rows = self.connection.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def get_order(self, po_or_id: str | int) -> dict[str, Any] | None:
        with self._lock:
            if isinstance(po_or_id, int) or str(po_or_id).isdigit():
                row = self.connection.execute(
                    "SELECT * FROM analyses WHERE id = ? LIMIT 1", (int(po_or_id),)
                ).fetchone()
            else:
                row = self.connection.execute(
                    "SELECT * FROM analyses WHERE po_number = ? ORDER BY id DESC LIMIT 1",
                    (str(po_or_id),),
                ).fetchone()
            if not row:
                return None
            data = dict(row)
            data["decisions"] = [
                dict(d)
                for d in self.connection.execute(
                    "SELECT * FROM decisions WHERE po_number = ? ORDER BY id ASC",
                    (data["po_number"],),
                ).fetchall()
            ]
            return data

    def get_order_by_po(self, po_number: str) -> dict[str, Any] | None:
        return self.get_order(po_number)

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

    def close(self) -> None:
        if hasattr(self, "_pool"):
            self._pool.close()

    def has_po(self, po_number: str) -> bool:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM analyses WHERE po_number = %s LIMIT 1", (po_number,))
                return cur.fetchone() is not None

    def record_analysis(self, analysis: Analysis, source_file: str) -> int:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO analyses (
                        po_number, customer, status, total, source_file,
                        order_json, findings_json, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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
                        datetime.now(UTC).isoformat(),
                    ),
                )
                res_id = int(cur.fetchone()["id"])
            conn.commit()
            analysis.analysis_id = res_id
            return res_id

    def update_analysis(self, order_id: int, analysis: Analysis) -> None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE analyses
                    SET po_number = %s, customer = %s, status = %s, total = %s,
                        order_json = %s, findings_json = %s
                    WHERE id = %s
                    """,
                    (
                        analysis.order.po_number,
                        analysis.order.customer,
                        analysis.status,
                        str(analysis.order.total),
                        json.dumps(analysis.order.to_dict(), ensure_ascii=False),
                        json.dumps([f.to_dict() for f in analysis.findings], ensure_ascii=False),
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
    ) -> list[dict[str, Any]]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT a.id, a.po_number, a.customer, a.status, a.total, a.source_file,
                           a.order_json, a.findings_json, a.created_at,
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
                    cur.execute("SELECT * FROM analyses WHERE po_number = %s ORDER BY id DESC LIMIT 1", (str(po_or_id),))
                row = cur.fetchone()
                if not row:
                    return None
                data = dict(row)
                cur.execute("SELECT * FROM decisions WHERE po_number = %s ORDER BY id ASC", (data["po_number"],))
                data["decisions"] = [dict(d) for d in cur.fetchall()]
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








def create_audit_store(database_url_or_path: str | Path | None = None) -> BaseAuditStore:
    """Factory helper creating the appropriate database adapter based on connection string."""
    target = database_url_or_path or os.getenv("DATABASE_URL") or "runtime/preflight.db"
    target_str = str(target).strip()

    if target_str.startswith("postgresql://") or target_str.startswith("postgres://") or target_str.startswith("postgresql+asyncpg://"):
        return PostgresAuditStore(database_url=target_str)
    
    if target_str.startswith("sqlite:///"):
        target_str = target_str.replace("sqlite:///", "")

    return AuditStore(path=target_str)
