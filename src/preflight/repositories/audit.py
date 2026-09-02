"""Audit Blocks Repository using SQLAlchemy Core."""

from __future__ import annotations

import json
from typing import Any
from sqlalchemy import select, insert, func
from sqlalchemy.engine import Connection

from preflight.db.models import audit_blocks
from preflight.security.audit_chain import AuditBlock


class AuditRepository:
    def __init__(self, conn: Connection):
        self.conn = conn

    def append_block(self, block: AuditBlock, order_id: int | None = None, request_id: str | None = None) -> int:
        ins_stmt = (
            insert(audit_blocks)
            .values(
                block_index=block.index,
                previous_hash=block.previous_hash,
                block_hash=block.block_hash,
                order_id=order_id,
                request_id=request_id,
                timestamp=block.timestamp,
                event_type=getattr(block, "action", "STATE_TRANSITION"),
                actor=block.actor,
                payload_json=getattr(block, "payload_hash", ""),
                signature=getattr(block, "signature", None),
            )
            .returning(audit_blocks.c.id)
        )
        res = self.conn.execute(ins_stmt).fetchone()
        return res[0]

    def get_latest_block(self) -> dict[str, Any] | None:
        stmt = select(audit_blocks).order_by(audit_blocks.c.block_index.desc()).limit(1)
        row = self.conn.execute(stmt).fetchone()
        return dict(row._mapping) if row else None

    def list_blocks(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        stmt = select(audit_blocks).order_by(audit_blocks.c.block_index.asc()).limit(limit).offset(offset)
        return [dict(r._mapping) for r in self.conn.execute(stmt).fetchall()]

    def count_blocks(self) -> int:
        return self.conn.execute(select(func.count(audit_blocks.c.id))).scalar() or 0
