from __future__ import annotations

import hashlib
import json
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


class OutboxStore:
    """SQLite-backed Transactional Outbox Store for ERP Sync Events."""

    def __init__(self, db_path: str | Path = "runtime/preflight.db"):
        if isinstance(db_path, str) and db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self.conn:
            self.conn.execute(
                """
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
                )
                """
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_erp_outbox_status ON erp_outbox(status)"
            )

    def enqueue_order(
        self,
        po_number: str,
        customer: str,
        items: list[dict[str, Any]],
        total_amount: Decimal,
        currency: str = "VND",
    ) -> ERPSyncPayload:
        """Enqueue an approved purchase order for ERP synchronization."""
        # Calculate Deterministic Idempotency Key (SHA256 of PO + Customer + Total)
        key_src = f"{po_number}:{customer}:{total_amount}"
        idemp_key = hashlib.sha256(key_src.encode("utf-8")).hexdigest()[:24]

        # Check if already enqueued
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
