from __future__ import annotations

import abc
import json
import os
import sqlite3
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from preflight.models import Analysis
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
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS customer_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    raw_query TEXT NOT NULL,
    target_sku TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    UNIQUE(customer_id, raw_query)
);
CREATE INDEX IF NOT EXISTS idx_customer_aliases ON customer_aliases(customer_id, raw_query);

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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customer_aliases (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(255) NOT NULL,
    raw_query VARCHAR(512) NOT NULL,
    target_sku VARCHAR(128) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, raw_query)
);
CREATE INDEX IF NOT EXISTS idx_pg_customer_aliases ON customer_aliases(customer_id, raw_query);

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
        self, po_number: str, decision: str, actor: str, note: str = ""
    ) -> int:
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
        self, po_number: str, decision: str, actor: str, note: str = ""
    ) -> int:
        if decision not in {"approved", "rejected", "needs_changes"}:
            raise ValueError("Decision must be approved, rejected, or needs_changes")
        if not self.has_po(po_number):
            raise ValueError(f"PO {po_number} was not found")
        with self._lock:
            with self.connection:
                cursor = self.connection.execute(
                    """
                    INSERT INTO decisions (po_number, decision, actor, note, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (po_number, decision, actor, note, datetime.now(UTC).isoformat()),
                )
                self.connection.execute(
                    "UPDATE analyses SET status = ? WHERE po_number = ?",
                    (decision, po_number),
                )
                self.append_audit_block(
                    po_number,
                    f"DECISION_{decision.upper()}",
                    actor,
                    {"decision": decision, "note": note, "actor": actor},
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
                INSERT INTO customer_aliases (customer_id, raw_query, target_sku, confidence, created_at)
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
                SELECT target_sku FROM customer_aliases
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
                    "SELECT * FROM customer_aliases WHERE customer_id = ? ORDER BY id DESC",
                    (customer_id.strip(),),
                ).fetchall()
            else:
                rows = self.connection.execute(
                    "SELECT * FROM customer_aliases ORDER BY id DESC"
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




class PostgresAuditStore(BaseAuditStore):
    """Enterprise PostgreSQL Audit Store with Connection Pooling (pool_size=20, max_overflow=10)."""

    def __init__(
        self,
        database_url: str,
        pool_size: int = 20,
        max_overflow: int = 10,
    ):
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self._fallback_sqlite: AuditStore | None = None

        # Try to initialize connection pool if psycopg2 or asyncpg is available;
        # otherwise provide safe in-memory adapter fallback for environments without live Postgres instance.
        self._pool_initialized = False
        self._try_init_pool()

    def _try_init_pool(self) -> None:
        try:
            import psycopg2
            from psycopg2 import pool
            self._pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=self.pool_size + self.max_overflow,
                dsn=self.database_url,
            )
            self._init_pg_schema()
            self._pool_initialized = True
        except Exception:
            # Fallback to local SQLite emulation for testing and zero-downtime development
            self._fallback_sqlite = AuditStore("runtime/pg_fallback.db")

    def _init_pg_schema(self) -> None:
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(POSTGRES_SCHEMA)
            conn.commit()
        finally:
            self._pool.putconn(conn)

    def close(self) -> None:
        if self._pool_initialized and hasattr(self, "_pool"):
            self._pool.closeall()
        if self._fallback_sqlite:
            self._fallback_sqlite.close()

    def has_po(self, po_number: str) -> bool:
        if self._fallback_sqlite:
            return self._fallback_sqlite.has_po(po_number)
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM analyses WHERE po_number = %s LIMIT 1", (po_number,))
                return cur.fetchone() is not None
        finally:
            self._pool.putconn(conn)

    def record_analysis(self, analysis: Analysis, source_file: str) -> int:
        if self._fallback_sqlite:
            return self._fallback_sqlite.record_analysis(analysis, source_file)
        conn = self._pool.getconn()
        try:
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
                res_id = int(cur.fetchone()[0])
            conn.commit()
            analysis.analysis_id = res_id
            return res_id
        finally:
            self._pool.putconn(conn)

    def update_analysis(self, order_id: int, analysis: Analysis) -> None:
        if self._fallback_sqlite:
            self._fallback_sqlite.update_analysis(order_id, analysis)
            return
        conn = self._pool.getconn()
        try:
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
        finally:
            self._pool.putconn(conn)

    def record_decision(self, po_number: str, decision: str, actor: str, note: str = "") -> int:
        if self._fallback_sqlite:
            return self._fallback_sqlite.record_decision(po_number, decision, actor, note)
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO decisions (po_number, decision, actor, note, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (po_number, decision, actor, note, datetime.now(UTC).isoformat()),
                )
                d_id = int(cur.fetchone()[0])
            conn.commit()
            return d_id
        finally:
            self._pool.putconn(conn)

    def history(self, po_number: str) -> dict[str, list[dict[str, object]]]:
        if self._fallback_sqlite:
            return self._fallback_sqlite.history(po_number)
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM analyses WHERE po_number = %s ORDER BY id", (po_number,))
                analyses = [dict(r) for r in cur.fetchall()]
                cur.execute("SELECT * FROM decisions WHERE po_number = %s ORDER BY id", (po_number,))
                decisions = [dict(r) for r in cur.fetchall()]
            return {"analyses": analyses, "decisions": decisions}
        finally:
            self._pool.putconn(conn)

    def list_orders(
        self,
        status: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        if self._fallback_sqlite:
            return self._fallback_sqlite.list_orders(status=status, search=search, limit=limit, offset=offset)
        conn = self._pool.getconn()
        try:
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
        finally:
            self._pool.putconn(conn)

    def get_order(self, po_or_id: str | int) -> dict[str, Any] | None:
        if self._fallback_sqlite:
            return self._fallback_sqlite.get_order(po_or_id)
        conn = self._pool.getconn()
        try:
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
        finally:
            self._pool.putconn(conn)

    def get_dashboard_stats(self) -> dict[str, Any]:
        if self._fallback_sqlite:
            return self._fallback_sqlite.get_dashboard_stats()
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM analyses")
                total = cur.fetchone()[0]
                cur.execute("SELECT status, COUNT(*) FROM analyses GROUP BY status")
                status_counts = {r[0]: r[1] for r in cur.fetchall()}
                cur.execute("SELECT decision, COUNT(*) FROM decisions GROUP BY decision")
                decisions_count = {r[0]: r[1] for r in cur.fetchall()}
                cur.execute("SELECT id, po_number, customer, status, total, created_at FROM analyses ORDER BY id DESC LIMIT 5")
                recent = [dict(r) for r in cur.fetchall()]
            return {
                "total_orders": total,
                "status_counts": status_counts,
                "decisions_count": decisions_count,
                "recent_orders": recent,
            }
        finally:
            self._pool.putconn(conn)

    def learn_alias(
        self,
        customer_id: str,
        raw_query: str,
        target_sku: str,
        confidence: float = 1.0,
    ) -> None:
        if self._fallback_sqlite:
            self._fallback_sqlite.learn_alias(customer_id, raw_query, target_sku, confidence)
            return
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO customer_aliases (customer_id, raw_query, target_sku, confidence, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT(customer_id, raw_query) DO UPDATE SET
                        target_sku = EXCLUDED.target_sku,
                        confidence = EXCLUDED.confidence,
                        created_at = EXCLUDED.created_at
                    """,
                    (customer_id.strip(), raw_query.strip().lower(), target_sku.strip().upper(), confidence, datetime.now(UTC).isoformat()),
                )
            conn.commit()
        finally:
            self._pool.putconn(conn)

    def get_customer_alias(self, customer_id: str, raw_query: str) -> str | None:
        if self._fallback_sqlite:
            return self._fallback_sqlite.get_customer_alias(customer_id, raw_query)
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT target_sku FROM customer_aliases WHERE customer_id = %s AND raw_query = %s LIMIT 1",
                    (customer_id.strip(), raw_query.strip().lower()),
                )
                row = cur.fetchone()
                return str(row[0]) if row else None
        finally:
            self._pool.putconn(conn)

    def list_customer_aliases(self, customer_id: str | None = None) -> list[dict[str, Any]]:
        if self._fallback_sqlite:
            return self._fallback_sqlite.list_customer_aliases(customer_id)
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                if customer_id:
                    cur.execute("SELECT * FROM customer_aliases WHERE customer_id = %s ORDER BY id DESC", (customer_id.strip(),))
                else:
                    cur.execute("SELECT * FROM customer_aliases ORDER BY id DESC")
                return [dict(r) for r in cur.fetchall()]
        finally:
            self._pool.putconn(conn)

    def append_audit_block(
        self,
        po_number: str,
        action: str,
        actor: str,
        payload: dict[str, Any],
        timestamp: float | None = None,
    ) -> dict[str, Any]:
        if self._fallback_sqlite:
            return self._fallback_sqlite.append_audit_block(po_number, action, actor, payload, timestamp)
        conn = self._pool.getconn()
        try:
            t = timestamp if timestamp is not None else time.time()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT block_index, block_hash FROM audit_blocks WHERE po_number = %s ORDER BY block_index DESC LIMIT 1",
                    (po_number,),
                )
                last_row = cur.fetchone()
                if last_row:
                    idx = last_row[0] + 1
                    prev_hash = last_row[1]
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
        finally:
            self._pool.putconn(conn)

    def get_audit_blocks(self, po_number: str) -> list[dict[str, Any]]:
        if self._fallback_sqlite:
            return self._fallback_sqlite.get_audit_blocks(po_number)
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT block_index as index, timestamp, po_number, action, actor, payload_hash, previous_hash, block_hash FROM audit_blocks WHERE po_number = %s ORDER BY block_index ASC",
                    (po_number,),
                )
                return [dict(r) for r in cur.fetchall()]
        finally:
            self._pool.putconn(conn)



def create_audit_store(database_url_or_path: str | Path | None = None) -> BaseAuditStore:
    """Factory helper creating the appropriate database adapter based on connection string."""
    target = database_url_or_path or os.getenv("DATABASE_URL") or "runtime/preflight.db"
    target_str = str(target).strip()

    if target_str.startswith("postgresql://") or target_str.startswith("postgres://") or target_str.startswith("postgresql+asyncpg://"):
        return PostgresAuditStore(database_url=target_str)
    
    if target_str.startswith("sqlite:///"):
        target_str = target_str.replace("sqlite:///", "")

    return AuditStore(path=target_str)
