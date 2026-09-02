"""Leads Repository using SQLAlchemy Core."""

from __future__ import annotations

from typing import Any
from sqlalchemy import select, insert
from sqlalchemy.engine import Connection

from preflight.db.models import leads


class LeadRepository:
    def __init__(self, conn: Connection):
        self.conn = conn

    def create_lead(
        self,
        company_name: str,
        contact_person: str,
        phone: str,
        email: str,
        daily_volume: str,
        current_erp: str,
        notes: str | None = None,
    ) -> int:
        stmt = (
            insert(leads)
            .values(
                company_name=company_name,
                contact_person=contact_person,
                phone=phone,
                email=email,
                daily_volume=daily_volume,
                current_erp=current_erp,
                notes=notes,
            )
            .returning(leads.c.id)
        )
        res = self.conn.execute(stmt).fetchone()
        return res[0]

    def list_leads(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        stmt = select(leads).order_by(leads.c.created_at.desc()).limit(limit).offset(offset)
        return [dict(r._mapping) for r in self.conn.execute(stmt).fetchall()]
