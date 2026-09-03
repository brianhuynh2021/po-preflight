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
from typing import Any, Sequence

from preflight.api.errors import ConfigurationError
from preflight.erp.schemas import (
    ERPAdapterType,
    ERPEventStatus,
    ERPSyncPayload,
    OutboxStats,
)


def compute_idempotency_key(
    analysis_id: int | str | None,
    po_number: str,
    items: Sequence[dict[str, Any] | Any],
) -> str:
    """Compute deterministic SHA256 idempotency key: sha256(analysis_id:po_number:revision_hash)[:24]."""
    normalized_items = []
    for it in items:
        if hasattr(it, "to_dict"):
            d = it.to_dict()
        elif isinstance(it, dict):
            d = {
                "sku": str(it.get("sku", "")).strip(),
                "description": str(it.get("description", "")).strip(),
                "quantity": int(it.get("quantity", 1)),
                "uom": str(it.get("uom", "PCS")).strip(),
                "unit_price": str(it.get("unit_price", 0)),
                "line_total": str(it.get("line_total", 0)),
            }
        else:
            d = {"raw": str(it)}
        normalized_items.append(d)

    normalized_items.sort(key=lambda x: (x.get("sku", ""), x.get("quantity", 0)))
    revision_hash = hashlib.sha256(json.dumps(normalized_items, sort_keys=True).encode("utf-8")).hexdigest()
    src = f"{analysis_id or 0}:{po_number}:{revision_hash}"
    return hashlib.sha256(src.encode("utf-8")).hexdigest()[:24]


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
    next_attempt_at REAL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_erp_outbox_status ON erp_outbox(status);
CREATE INDEX IF NOT EXISTS idx_erp_outbox_idemp ON erp_outbox(idempotency_key);
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
    next_attempt_at DOUBLE PRECISION,
    created_at DOUBLE PRECISION NOT NULL,
    updated_at DOUBLE PRECISION NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pg_erp_outbox_status ON erp_outbox(status);
CREATE INDEX IF NOT EXISTS idx_pg_erp_outbox_idemp ON erp_outbox(idempotency_key);
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
        idempotency_key: str | None = None,
        approved_by: str | None = None,
        approved_at: str | None = None,
        source_analysis_id: int | None = None,
    ) -> ERPSyncPayload:
        pass

    @abc.abstractmethod
    def fetch_pending(self, limit: int = 10) -> list[ERPSyncPayload]:
        pass

    @abc.abstractmethod
    def recover_stale_leases(self, lease_seconds: float = 60.0) -> int:
        pass

    @abc.abstractmethod
    def mark_sent(self, event_id: str, tx_id: str, adapter_type: ERPAdapterType | str) -> None:
        pass

    @abc.abstractmethod
    def mark_failed(self, event_id: str, error: str) -> None:
        pass

    @abc.abstractmethod
    def get_by_idempotency_key(self, idempotency_key: str) -> dict[str, Any] | None:
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
            # Migration check: add next_attempt_at if missing
            cur = self.conn.cursor()
            cur.execute("PRAGMA table_info(erp_outbox)")
            cols = [col[1] for col in cur.fetchall()]
            if "next_attempt_at" not in cols:
                cur.execute("ALTER TABLE erp_outbox ADD COLUMN next_attempt_at REAL")

    def enqueue_order(
        self,
        po_number: str,
        customer: str,
        items: list[dict[str, Any]],
        total_amount: Decimal,
        currency: str = "VND",
        idempotency_key: str | None = None,
        approved_by: str | None = None,
        approved_at: str | None = None,
        source_analysis_id: int | None = None,
    ) -> ERPSyncPayload:
        """Enqueue an approved purchase order for ERP synchronization."""
        if not idempotency_key:
            idempotency_key = compute_idempotency_key(source_analysis_id, po_number, items)

        cur = self.conn.cursor()
        cur.execute(
            "SELECT event_id, payload_json, status FROM erp_outbox WHERE idempotency_key = ?",
            (idempotency_key,),
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
            idempotency_key=idempotency_key,
            created_at=now,
            approved_by=approved_by,
            approved_at=approved_at,
            source_analysis_id=source_analysis_id,
        )

        payload_dict = payload.model_dump()
        payload_dict["total_amount"] = float(total_amount)

        with self.conn:
            self.conn.execute(
                """
                INSERT INTO erp_outbox (
                    event_id, po_number, customer, total_amount, currency,
                    idempotency_key, payload_json, status, retry_count,
                    next_attempt_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, NULL, ?, ?)
                """,
                (
                    event_id,
                    po_number,
                    customer,
                    float(total_amount),
                    currency,
                    idempotency_key,
                    json.dumps(payload_dict),
                    ERPEventStatus.PENDING.value,
                    now,
                    now,
                ),
            )

        return payload

    def fetch_pending(self, limit: int = 10) -> list[ERPSyncPayload]:
        """Fetch pending events and mark them as PROCESSING atomically."""
        now = time.time()
        timeout_threshold = now - 300.0  # 5 minutes processing timeout

        with self.conn:
            cur = self.conn.cursor()
            cur.execute(
                """
                SELECT event_id, payload_json FROM erp_outbox
                WHERE (status = ? AND (next_attempt_at IS NULL OR next_attempt_at <= ?))
                   OR (status = ? AND updated_at < ?)
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (ERPEventStatus.PENDING.value, now, ERPEventStatus.PROCESSING.value, timeout_threshold, limit),
            )
            rows = cur.fetchall()
            if not rows:
                return []

            event_ids = [row["event_id"] for row in rows]
            placeholders = ",".join("?" * len(event_ids))
            cur.execute(
                f"""
                UPDATE erp_outbox
                SET status = ?, updated_at = ?
                WHERE event_id IN ({placeholders})
                """,
                [ERPEventStatus.PROCESSING.value, now, *event_ids],
            )

            results: list[ERPSyncPayload] = []
            for row in rows:
                data = json.loads(row["payload_json"])
                data["total_amount"] = Decimal(str(data["total_amount"]))
                results.append(ERPSyncPayload(**data))
            return results

    def recover_stale_leases(self, lease_seconds: float = 60.0) -> int:
        """Reset events stuck in PROCESSING for longer than lease_seconds back to PENDING."""
        now = time.time()
        stale_threshold = now - lease_seconds
        with self.conn:
            cur = self.conn.cursor()
            cur.execute(
                """
                UPDATE erp_outbox
                SET status = ?, updated_at = ?
                WHERE status = ? AND updated_at < ?
                """,
                (ERPEventStatus.PENDING.value, now, ERPEventStatus.PROCESSING.value, stale_threshold),
            )
            return cur.rowcount

    def mark_sent(self, event_id: str, tx_id: str, adapter_type: ERPAdapterType | str) -> None:
        """Mark an outbox event as successfully synchronized to ERP."""
        now = time.time()
        adapter_val = adapter_type.value if hasattr(adapter_type, "value") else str(adapter_type)
        with self.conn:
            self.conn.execute(
                """
                UPDATE erp_outbox
                SET status = ?, transaction_id = ?, adapter_type = ?, last_error = NULL, updated_at = ?
                WHERE event_id = ?
                """,
                (ERPEventStatus.SENT.value, tx_id, adapter_val, now, event_id),
            )

    def mark_failed(self, event_id: str, error: str) -> None:
        """Increment retry count and update status to PENDING with backoff or DEAD_LETTER."""
        now = time.time()
        with self.conn:
            cur = self.conn.cursor()
            cur.execute("SELECT retry_count FROM erp_outbox WHERE event_id = ?", (event_id,))
            row = cur.fetchone()
            current_retry = (row["retry_count"] if row else 0) + 1

            if current_retry >= 3:
                # Permanent failure -> DEAD_LETTER
                cur.execute(
                    """
                    UPDATE erp_outbox
                    SET status = ?, retry_count = ?, last_error = ?, updated_at = ?
                    WHERE event_id = ?
                    """,
                    (ERPEventStatus.DEAD_LETTER.value, current_retry, error, now, event_id),
                )
            else:
                # Exponential backoff: 1 min, 5 min, 30 min
                delays = [60.0, 300.0, 1800.0]
                delay_sec = delays[min(current_retry - 1, len(delays) - 1)]
                next_attempt = now + delay_sec
                cur.execute(
                    """
                    UPDATE erp_outbox
                    SET status = ?, retry_count = ?, next_attempt_at = ?, last_error = ?, updated_at = ?
                    WHERE event_id = ?
                    """,
                    (ERPEventStatus.PENDING.value, current_retry, next_attempt, error, now, event_id),
                )

    def get_by_idempotency_key(self, idempotency_key: str) -> dict[str, Any] | None:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT event_id, po_number, customer, total_amount, currency,
                   idempotency_key, payload_json, status, retry_count,
                   transaction_id, adapter_type, last_error, next_attempt_at,
                   created_at, updated_at
            FROM erp_outbox
            WHERE idempotency_key = ?
            """,
            (idempotency_key,),
        )
        row = cur.fetchone()
        return dict(row) if row else None

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
                SUM(CASE WHEN status = 'DEAD_LETTER' THEN 1 ELSE 0 END) as dead_letter,
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
            dead_letter_count=row["dead_letter"] or 0,
            total_events=row["total"] or 0,
        )

    def list_events(self, limit: int = 50) -> list[dict[str, Any]]:
        """List recent outbox queue events."""
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT event_id, po_number, customer, total_amount, currency,
                   idempotency_key, payload_json, status, retry_count, transaction_id,
                   adapter_type, last_error, next_attempt_at, created_at, updated_at
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
    """PostgreSQL Enterprise Outbox Store with psycopg 3 Connection Pooling."""

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
                f"Không thể kết nối đến PostgreSQL outbox database tại {database_url}: {exc}"
            ) from exc

    def _init_pg_schema(self) -> None:
        with self._pool.connection(timeout=3.0) as conn:
            with conn.cursor() as cur:
                cur.execute(POSTGRES_OUTBOX_SCHEMA)
            conn.commit()

    def close(self) -> None:
        if hasattr(self, "_pool"):
            self._pool.close()

    def enqueue_order(
        self,
        po_number: str,
        customer: str,
        items: list[dict[str, Any]],
        total_amount: Decimal,
        currency: str = "VND",
        idempotency_key: str | None = None,
        approved_by: str | None = None,
        approved_at: str | None = None,
        source_analysis_id: int | None = None,
    ) -> ERPSyncPayload:
        if not idempotency_key:
            idempotency_key = compute_idempotency_key(source_analysis_id, po_number, items)

        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT payload_json FROM erp_outbox WHERE idempotency_key = %s", (idempotency_key,))
                row = cur.fetchone()
                if row:
                    val = row["payload_json"]
                    data = json.loads(val) if isinstance(val, str) else val
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
                    idempotency_key=idempotency_key,
                    created_at=now,
                    approved_by=approved_by,
                    approved_at=approved_at,
                    source_analysis_id=source_analysis_id,
                )
                payload_dict = payload.model_dump()
                payload_dict["total_amount"] = float(total_amount)

                cur.execute(
                    """
                    INSERT INTO erp_outbox (
                        event_id, po_number, customer, total_amount, currency,
                        idempotency_key, payload_json, status, retry_count,
                        next_attempt_at, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, NULL, %s, %s)
                    """,
                    (
                        event_id, po_number, customer, float(total_amount), currency,
                        idempotency_key, json.dumps(payload_dict), ERPEventStatus.PENDING.value, now, now,
                    ),
                )
            conn.commit()
            return payload

    def fetch_pending(self, limit: int = 10) -> list[ERPSyncPayload]:
        with self._pool.connection() as conn:
            now = time.time()
            timeout_threshold = now - 300.0
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT event_id, payload_json FROM erp_outbox
                    WHERE (status = %s AND (next_attempt_at IS NULL OR next_attempt_at <= %s))
                       OR (status = %s AND updated_at < %s)
                    ORDER BY created_at ASC
                    LIMIT %s
                    FOR UPDATE SKIP LOCKED
                    """,
                    (ERPEventStatus.PENDING.value, now, ERPEventStatus.PROCESSING.value, timeout_threshold, limit),
                )
                rows = cur.fetchall()
                if not rows:
                    return []

                event_ids = [row["event_id"] for row in rows]
                cur.execute(
                    """
                    UPDATE erp_outbox
                    SET status = %s, updated_at = %s
                    WHERE event_id = ANY(%s)
                    """,
                    (ERPEventStatus.PROCESSING.value, now, event_ids),
                )

                results: list[ERPSyncPayload] = []
                for row in rows:
                    val = row["payload_json"]
                    data = json.loads(val) if isinstance(val, str) else val
                    data["total_amount"] = Decimal(str(data["total_amount"]))
                    results.append(ERPSyncPayload(**data))
            conn.commit()
            return results

    def recover_stale_leases(self, lease_seconds: float = 60.0) -> int:
        """Reset events stuck in PROCESSING for longer than lease_seconds back to PENDING."""
        now = time.time()
        stale_threshold = now - lease_seconds
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE erp_outbox
                    SET status = %s, updated_at = %s
                    WHERE status = %s AND updated_at < %s
                    """,
                    (ERPEventStatus.PENDING.value, now, ERPEventStatus.PROCESSING.value, stale_threshold),
                )
                conn.commit()
                return cur.rowcount

    def mark_sent(self, event_id: str, tx_id: str, adapter_type: ERPAdapterType | str) -> None:
        adapter_val = adapter_type.value if hasattr(adapter_type, "value") else str(adapter_type)
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE erp_outbox
                    SET status = %s, transaction_id = %s, adapter_type = %s, last_error = NULL, updated_at = %s
                    WHERE event_id = %s
                    """,
                    (ERPEventStatus.SENT.value, tx_id, adapter_val, time.time(), event_id),
                )
            conn.commit()

    def mark_failed(self, event_id: str, error: str) -> None:
        now = time.time()
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT retry_count FROM erp_outbox WHERE event_id = %s", (event_id,))
                row = cur.fetchone()
                current_retry = (row["retry_count"] if row else 0) + 1
                if current_retry >= 3:
                    cur.execute(
                        """
                        UPDATE erp_outbox
                        SET status = %s, retry_count = %s, last_error = %s, updated_at = %s
                        WHERE event_id = %s
                        """,
                        (ERPEventStatus.DEAD_LETTER.value, current_retry, error, now, event_id),
                    )
                else:
                    delays = [60.0, 300.0, 1800.0]
                    delay_sec = delays[min(current_retry - 1, len(delays) - 1)]
                    next_attempt = now + delay_sec
                    cur.execute(
                        """
                        UPDATE erp_outbox
                        SET status = %s, retry_count = %s, next_attempt_at = %s, last_error = %s, updated_at = %s
                        WHERE event_id = %s
                        """,
                        (ERPEventStatus.PENDING.value, current_retry, next_attempt, error, now, event_id),
                    )
            conn.commit()

    def get_by_idempotency_key(self, idempotency_key: str) -> dict[str, Any] | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT event_id, po_number, customer, total_amount, currency,
                           idempotency_key, payload_json, status, retry_count,
                           transaction_id, adapter_type, last_error, next_attempt_at,
                           created_at, updated_at
                    FROM erp_outbox
                    WHERE idempotency_key = %s
                    """,
                    (idempotency_key,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return dict(row)

    def get_stats(self) -> OutboxStats:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END) as pending,
                        SUM(CASE WHEN status = 'PROCESSING' THEN 1 ELSE 0 END) as processing,
                        SUM(CASE WHEN status = 'SENT' THEN 1 ELSE 0 END) as sent,
                        SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
                        SUM(CASE WHEN status = 'DEAD_LETTER' THEN 1 ELSE 0 END) as dead_letter,
                        COUNT(*) as total
                    FROM erp_outbox
                    """
                )
                row = cur.fetchone()
                if not row or (row.get("total") or 0) == 0:
                    return OutboxStats()
                return OutboxStats(
                    pending_count=int(row.get("pending") or 0),
                    processing_count=int(row.get("processing") or 0),
                    sent_count=int(row.get("sent") or 0),
                    failed_count=int(row.get("failed") or 0),
                    dead_letter_count=int(row.get("dead_letter") or 0),
                    total_events=int(row.get("total") or 0),
                )

    def list_events(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT event_id, po_number, customer, total_amount, currency,
                           idempotency_key, payload_json, status, retry_count, transaction_id,
                           adapter_type, last_error, next_attempt_at, created_at, updated_at
                    FROM erp_outbox
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                return [dict(row) for row in cur.fetchall()]


def create_outbox_store(database_url_or_path: str | Path | None = None) -> BaseOutboxStore:
    """Factory helper creating the appropriate outbox store adapter based on database URL."""
    target = database_url_or_path or os.getenv("DATABASE_URL") or "runtime/preflight.db"
    target_str = str(target).strip()

    if target_str.startswith("postgresql://") or target_str.startswith("postgres://") or target_str.startswith("postgresql+asyncpg://"):
        return PostgresOutboxStore(database_url=target_str)

    if target_str.startswith("sqlite:///"):
        target_str = target_str.replace("sqlite:///", "")

    return OutboxStore(db_path=target_str)
