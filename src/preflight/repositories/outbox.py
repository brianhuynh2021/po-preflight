"""ERP Outbox Repository using SQLAlchemy Core."""

from __future__ import annotations

import json
from typing import Any
from sqlalchemy import select, insert, update, func
from sqlalchemy.engine import Connection

from preflight.db.models import erp_outbox


class OutboxRepository:
    def __init__(self, conn: Connection):
        self.conn = conn

    def enqueue(self, idempotency_key: str, payload: dict[str, Any], order_id: int | None = None) -> int:
        payload_str = json.dumps(payload, ensure_ascii=False)
        ins_stmt = (
            insert(erp_outbox)
            .values(
                order_id=order_id,
                idempotency_key=idempotency_key,
                payload_json=payload_str,
                status="PENDING",
            )
            .returning(erp_outbox.c.id)
        )
        res = self.conn.execute(ins_stmt).fetchone()
        return res[0]

    def get_by_idempotency_key(self, idempotency_key: str) -> dict[str, Any] | None:
        stmt = select(erp_outbox).where(erp_outbox.c.idempotency_key == idempotency_key)
        row = self.conn.execute(stmt).fetchone()
        return dict(row._mapping) if row else None

    def fetch_pending(self, limit: int = 10) -> list[dict[str, Any]]:
        stmt = (
            select(erp_outbox)
            .where(erp_outbox.c.status == "PENDING")
            .order_by(erp_outbox.c.created_at.asc())
            .limit(limit)
        )
        return [dict(r._mapping) for r in self.conn.execute(stmt).fetchall()]

    def mark_processed(self, entry_id: int, status: str = "DELIVERED", error_detail: str | None = None) -> None:
        stmt = (
            update(erp_outbox)
            .where(erp_outbox.c.id == entry_id)
            .values(
                status=status,
                error_detail=error_detail,
                processed_at=func.now(),
            )
        )
        self.conn.execute(stmt)
