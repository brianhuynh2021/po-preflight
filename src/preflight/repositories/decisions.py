"""Decisions Repository using SQLAlchemy Core."""

from __future__ import annotations

from typing import Any
from sqlalchemy import select, insert, update
from sqlalchemy.engine import Connection

from preflight.db.models import decisions, orders


class DecisionRepository:
    def __init__(self, conn: Connection):
        self.conn = conn

    def record_decision(
        self,
        order_id: int,
        decision: str,
        actor: str,
        channel: str = "web",
        note: str | None = None,
        actor_user_id: int | None = None,
    ) -> int:
        ins_stmt = (
            insert(decisions)
            .values(
                order_id=order_id,
                decision=decision,
                actor=actor,
                actor_user_id=actor_user_id,
                channel=channel,
                note=note,
            )
            .returning(decisions.c.id)
        )
        res = self.conn.execute(ins_stmt).fetchone()
        dec_id = res[0]

        # Update order status
        new_status = decision  # approved, rejected, needs_changes
        self.conn.execute(
            update(orders).where(orders.c.id == order_id).values(status=new_status)
        )
        return dec_id

    def list_decisions(self, order_id: int) -> list[dict[str, Any]]:
        stmt = select(decisions).where(decisions.c.order_id == order_id).order_by(decisions.c.created_at.desc())
        return [dict(r._mapping) for r in self.conn.execute(stmt).fetchall()]
