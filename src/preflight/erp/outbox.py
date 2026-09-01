from __future__ import annotations

import abc
import hashlib
import json
import os
import sqlite3
import time
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any

from preflight.erp.schemas import (
    ERPAdapterType,
    ERPEventStatus,
    ERPSyncPayload,
    OutboxStats,
)


SQLITE_OUTBOX_SCHEMA = """
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
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_erp_outbox_status ON erp_outbox(status);
"""

POSTGRES_OUTBOX_SCHEMA = """
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
    created_at DOUBLE PRECISION NOT NULL,
    updated_at DOUBLE PRECISION NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pg_erp_outbox_status ON erp_outbox(status);
"""


class BaseOutboxStore(abc.ABC):
    """Abstract interface for Transactional Outbox event queue storage."""

    @abc.abstractmethod
    def close(self) -> None:
        pass

    @abc.abstractmethod
    def enqueue_order(
        self,
        po_number: str,
        customer: str,
        items: list[dict[str, Any]],
        total_amount: Decimal,
        currency: str = "VND",
    ) -> ERPSyncPayload:
        pass

    @abc.abstractmethod
    def fetch_pending(self, limit: int = 10) -> list[ERPSyncPayload]:
        pass

    @abc.abstractmethod
    def mark_sent(self, event_id: str, tx_id: str, adapter_type: ERPAdapterType) -> None:
        pass

    @abc.abstractmethod
    def mark_failed(self, event_id: str, error: str) -> None:
        pass

    @abc.abstractmethod
    def get_stats(self) -> OutboxStats:
        pass

    @abc.abstractmethod
    def list_events(self, limit: int = 50) -> list[dict[str, Any]]:
        pass


class OutboxStore(BaseOutboxStore):
    """SQLite-backed Transactional Outbox Store for ERP Sync Events."""

    def __init__(self, db_path: str | Path = "runtime/preflight.db"):
        if isinstance(db_path, str) and db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self.conn:
            self.conn.executescript(SQLITE_OUTBOX_SCHEMA)

    def enqueue_order(
        self,
        po_number: str,
        customer: str,
        items: list[dict[str, Any]],
        total_amount: Decimal,
        currency: str = "VND",
    ) -> ERPSyncPayload:
        """Enqueue an approved purchase order for ERP synchronization."""
        key_src = f"{po_number}:{customer}:{total_amount}"
        idemp_key = hashlib.sha256(key_src.encode("utf-8")).hexdigest()[:24]

        cur = self.conn.cursor()
        cur.execute(
            "SELECT event_id, payload_json, status FROM erp_outbox WHERE idempotency_key = ?",
            (idemp_key,),
        )
        row = cur.fetchone()
        if row:
            data = json.loads(row["payload_json"])
            data["total_amount"] = Decimal(str(data["total_amount"]))
            return ERPSyncPayload(**data)

        event_id = f"evt_{uuid.uuid4().hex[:12]}"
        now = time.time()

        payload = ERPSyncPayload(
            event_id=event_id,
            po_number=po_number,
            customer=customer,
            items=items,
            total_amount=total_amount,
            currency=currency,
            idempotency_key=idemp_key,
            created_at=now,
        )

        payload_dict = payload.model_dump()
        payload_dict["total_amount"] = float(total_amount)

        with self.conn:
            self.conn.execute(
                """
                INSERT INTO erp_outbox (
                    event_id, po_number, customer, total_amount, currency,
                    idempotency_key, payload_json, status, retry_count,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (
                    event_id,
                    po_number,
                    customer,
                    float(total_amount),
                    currency,
                    idemp_key,
                    json.dumps(payload_dict),
                    ERPEventStatus.PENDING.value,
                    now,
                    now,
                ),
            )

        return payload

    def fetch_pending(self, limit: int = 10) -> list[ERPSyncPayload]:
        """Fetch pending events ready to be processed by Outbox Sync Worker."""
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT payload_json FROM erp_outbox
            WHERE status = ? OR (status = ? AND retry_count < 3)
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (ERPEventStatus.PENDING.value, ERPEventStatus.FAILED.value, limit),
        )
        results: list[ERPSyncPayload] = []
        for row in cur.fetchall():
            data = json.loads(row["payload_json"])
            data["total_amount"] = Decimal(str(data["total_amount"]))
            results.append(ERPSyncPayload(**data))
        return results

    def mark_sent(self, event_id: str, tx_id: str, adapter_type: ERPAdapterType) -> None:
        """Mark an outbox event as successfully synchronized to ERP."""
        now = time.time()
        with self.conn:
            self.conn.execute(
                """
                UPDATE erp_outbox
                SET status = ?, transaction_id = ?, adapter_type = ?, last_error = NULL, updated_at = ?
                WHERE event_id = ?
                """,
                (ERPEventStatus.SENT.value, tx_id, adapter_type.value, now, event_id),
            )

    def mark_failed(self, event_id: str, error: str) -> None:
        """Increment retry count and mark outbox event as failed."""
        now = time.time()
        with self.conn:
            self.conn.execute(
                """
                UPDATE erp_outbox
                SET status = ?, retry_count = retry_count + 1, last_error = ?, updated_at = ?
                WHERE event_id = ?
                """,
                (ERPEventStatus.FAILED.value, error, now, event_id),
            )

    def get_stats(self) -> OutboxStats:
        """Retrieve count statistics of outbox queue."""
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT
                SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'PROCESSING' THEN 1 ELSE 0 END) as processing,
                SUM(CASE WHEN status = 'SENT' THEN 1 ELSE 0 END) as sent,
                SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
                COUNT(*) as total
            FROM erp_outbox
            """
        )
        row = cur.fetchone()
        if not row or row["total"] == 0:
            return OutboxStats()

        return OutboxStats(
            pending_count=row["pending"] or 0,
            processing_count=row["processing"] or 0,
            sent_count=row["sent"] or 0,
            failed_count=row["failed"] or 0,
            total_events=row["total"] or 0,
        )

    def list_events(self, limit: int = 50) -> list[dict[str, Any]]:
        """List recent outbox queue events."""
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT event_id, po_number, customer, total_amount, currency,
                   idempotency_key, status, retry_count, transaction_id,
                   adapter_type, last_error, created_at, updated_at
            FROM erp_outbox
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in cur.fetchall()]

    def close(self) -> None:
        self.conn.close()


class PostgresOutboxStore(BaseOutboxStore):
    """PostgreSQL Enterprise Outbox Store with Connection Pooling."""

    def __init__(
        self,
        database_url: str,
        pool_size: int = 20,
        max_overflow: int = 10,
    ):
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self._fallback_sqlite: OutboxStore | None = None
        self._pool_initialized = False
        self._try_init_pool()

    def _try_init_pool(self) -> None:
        try:
            from psycopg2 import pool
            self._pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=self.pool_size + self.max_overflow,
                dsn=self.database_url,
            )
            self._init_pg_schema()
            self._pool_initialized = True
        except Exception:
            self._fallback_sqlite = OutboxStore("runtime/pg_fallback_outbox.db")

    def _init_pg_schema(self) -> None:
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(POSTGRES_OUTBOX_SCHEMA)
            conn.commit()
        finally:
            self._pool.putconn(conn)

    def close(self) -> None:
        if self._pool_initialized and hasattr(self, "_pool"):
            self._pool.closeall()
        if self._fallback_sqlite:
            self._fallback_sqlite.close()

    def enqueue_order(
        self,
        po_number: str,
        customer: str,
        items: list[dict[str, Any]],
        total_amount: Decimal,
        currency: str = "VND",
    ) -> ERPSyncPayload:
        if self._fallback_sqlite:
            return self._fallback_sqlite.enqueue_order(po_number, customer, items, total_amount, currency)
        key_src = f"{po_number}:{customer}:{total_amount}"
        idemp_key = hashlib.sha256(key_src.encode("utf-8")).hexdigest()[:24]

        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT payload_json FROM erp_outbox WHERE idempotency_key = %s", (idemp_key,))
                row = cur.fetchone()
                if row:
                    data = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                    data["total_amount"] = Decimal(str(data["total_amount"]))
                    return ERPSyncPayload(**data)

                event_id = f"evt_{uuid.uuid4().hex[:12]}"
                now = time.time()
                payload = ERPSyncPayload(
                    event_id=event_id,
                    po_number=po_number,
                    customer=customer,
                    items=items,
                    total_amount=total_amount,
                    currency=currency,
                    idempotency_key=idemp_key,
                    created_at=now,
                )
                payload_dict = payload.model_dump()
                payload_dict["total_amount"] = float(total_amount)

                cur.execute(
                    """
                    INSERT INTO erp_outbox (
                        event_id, po_number, customer, total_amount, currency,
                        idempotency_key, payload_json, status, retry_count,
                        created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, %s, %s)
                    """,
                    (
                        event_id, po_number, customer, float(total_amount), currency,
                        idemp_key, json.dumps(payload_dict), ERPEventStatus.PENDING.value, now, now,
                    ),
                )
            conn.commit()
            return payload
        finally:
            self._pool.putconn(conn)

    def fetch_pending(self, limit: int = 10) -> list[ERPSyncPayload]:
        if self._fallback_sqlite:
            return self._fallback_sqlite.fetch_pending(limit)
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT payload_json FROM erp_outbox
                    WHERE status = %s OR (status = %s AND retry_count < 3)
                    ORDER BY created_at ASC
                    LIMIT %s
                    """,
                    (ERPEventStatus.PENDING.value, ERPEventStatus.FAILED.value, limit),
                )
                results: list[ERPSyncPayload] = []
                for row in cur.fetchall():
                    data = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                    data["total_amount"] = Decimal(str(data["total_amount"]))
                    results.append(ERPSyncPayload(**data))
                return results
        finally:
            self._pool.putconn(conn)

    def mark_sent(self, event_id: str, tx_id: str, adapter_type: ERPAdapterType) -> None:
        if self._fallback_sqlite:
            self._fallback_sqlite.mark_sent(event_id, tx_id, adapter_type)
            return
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE erp_outbox
                    SET status = %s, transaction_id = %s, adapter_type = %s, last_error = NULL, updated_at = %s
                    WHERE event_id = %s
                    """,
                    (ERPEventStatus.SENT.value, tx_id, adapter_type.value, time.time(), event_id),
                )
            conn.commit()
        finally:
            self._pool.putconn(conn)

    def mark_failed(self, event_id: str, error: str) -> None:
        if self._fallback_sqlite:
            self._fallback_sqlite.mark_failed(event_id, error)
            return
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE erp_outbox
                    SET status = %s, retry_count = retry_count + 1, last_error = %s, updated_at = %s
                    WHERE event_id = %s
                    """,
                    (ERPEventStatus.FAILED.value, error, time.time(), event_id),
                )
            conn.commit()
        finally:
            self._pool.putconn(conn)

    def get_stats(self) -> OutboxStats:
        if self._fallback_sqlite:
            return self._fallback_sqlite.get_stats()
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END) as pending,
                        SUM(CASE WHEN status = 'PROCESSING' THEN 1 ELSE 0 END) as processing,
                        SUM(CASE WHEN status = 'SENT' THEN 1 ELSE 0 END) as sent,
                        SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
                        COUNT(*) as total
                    FROM erp_outbox
                    """
                )
                row = cur.fetchone()
                if not row or row[4] == 0:
                    return OutboxStats()
                return OutboxStats(
                    pending_count=row[0] or 0,
                    processing_count=row[1] or 0,
                    sent_count=row[2] or 0,
                    failed_count=row[3] or 0,
                    total_events=row[4] or 0,
                )
        finally:
            self._pool.putconn(conn)

    def list_events(self, limit: int = 50) -> list[dict[str, Any]]:
        if self._fallback_sqlite:
            return self._fallback_sqlite.list_events(limit)
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT event_id, po_number, customer, total_amount, currency,
                           idempotency_key, status, retry_count, transaction_id,
                           adapter_type, last_error, created_at, updated_at
                    FROM erp_outbox
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                cols = [desc[0] for desc in cur.description]
                return [dict(zip(cols, row)) for row in cur.fetchall()]
        finally:
            self._pool.putconn(conn)


def create_outbox_store(database_url_or_path: str | Path | None = None) -> BaseOutboxStore:
    """Factory helper creating the appropriate outbox store adapter based on database URL."""
    target = database_url_or_path or os.getenv("DATABASE_URL") or "runtime/preflight.db"
    target_str = str(target).strip()

    if target_str.startswith("postgresql://") or target_str.startswith("postgres://") or target_str.startswith("postgresql+asyncpg://"):
        return PostgresOutboxStore(database_url=target_str)

    if target_str.startswith("sqlite:///"):
        target_str = target_str.replace("sqlite:///", "")

    return OutboxStore(db_path=target_str)
