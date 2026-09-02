"""Customers Repository using SQLAlchemy Core."""

from __future__ import annotations

from typing import Any
from sqlalchemy import select, insert, update
from sqlalchemy.engine import Connection

from preflight.db.models import customers, customer_aliases, customer_credits


class CustomerRepository:
    def __init__(self, conn: Connection):
        self.conn = conn

    def get_or_create(self, org_id: int, name: str, code: str | None = None) -> dict[str, Any]:
        """Finds a customer by normalized name or creates a new customer record."""
        norm = name.strip().lower()
        stmt = select(customers).where(customers.c.org_id == org_id, customers.c.normalized_name == norm)
        row = self.conn.execute(stmt).fetchone()
        if row:
            return dict(row._mapping)

        # Also check customer aliases
        alias_stmt = (
            select(customers)
            .join(customer_aliases, customer_aliases.c.customer_id == customers.c.id)
            .where(customers.c.org_id == org_id, customer_aliases.c.alias_normalized == norm)
        )
        alias_row = self.conn.execute(alias_stmt).fetchone()
        if alias_row:
            return dict(alias_row._mapping)

        # Generate customer code if not provided
        if not code:
            count_stmt = select(customers.c.id).where(customers.c.org_id == org_id)
            total = len(self.conn.execute(count_stmt).fetchall())
            code = f"CUST-{total + 1:04d}"

        ins_stmt = (
            insert(customers)
            .values(org_id=org_id, code=code, name=name.strip(), normalized_name=norm)
            .returning(customers)
        )
        res = self.conn.execute(ins_stmt).fetchone()
        return dict(res._mapping)

    def get_by_id(self, customer_id: int) -> dict[str, Any] | None:
        stmt = select(customers).where(customers.c.id == customer_id)
        row = self.conn.execute(stmt).fetchone()
        return dict(row._mapping) if row else None

    def list_customers(self, org_id: int) -> list[dict[str, Any]]:
        stmt = select(customers).where(customers.c.org_id == org_id).order_by(customers.c.name)
        return [dict(r._mapping) for r in self.conn.execute(stmt).fetchall()]
