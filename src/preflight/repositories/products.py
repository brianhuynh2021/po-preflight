"""Products Repository using SQLAlchemy Core."""

from __future__ import annotations

from typing import Any
from decimal import Decimal
from sqlalchemy import select, insert, update, delete
from sqlalchemy.engine import Connection

from preflight.db.models import products, uom_conversions
from preflight.models import Product


class ProductRepository:
    def __init__(self, conn: Connection):
        self.conn = conn

    def get_by_sku(self, org_id: int, sku: str) -> dict[str, Any] | None:
        stmt = select(products).where(products.c.org_id == org_id, products.c.sku == sku)
        row = self.conn.execute(stmt).fetchone()
        return dict(row._mapping) if row else None

    def list_all(self, org_id: int) -> list[dict[str, Any]]:
        stmt = select(products).where(products.c.org_id == org_id).order_by(products.c.sku)
        return [dict(r._mapping) for r in self.conn.execute(stmt).fetchall()]

    def upsert_product(
        self,
        org_id: int,
        sku: str,
        name: str,
        unit_price: Decimal | float,
        stock: int = 0,
        active: bool = True,
        base_uom: str = "PCS",
        moq: int = 1,
        pack_size: int = 1,
        category: str | None = None,
        barcode: str | None = None,
    ) -> dict[str, Any]:
        existing = self.get_by_sku(org_id, sku)
        if existing:
            stmt = (
                update(products)
                .where(products.c.id == existing["id"])
                .values(
                    name=name,
                    unit_price=unit_price,
                    stock=stock,
                    active=active,
                    base_uom=base_uom,
                    moq=moq,
                    pack_size=pack_size,
                    category=category,
                    barcode=barcode,
                )
                .returning(products)
            )
            res = self.conn.execute(stmt).fetchone()
            return dict(res._mapping)

        ins_stmt = (
            insert(products)
            .values(
                org_id=org_id,
                sku=sku,
                name=name,
                unit_price=unit_price,
                stock=stock,
                active=active,
                base_uom=base_uom,
                moq=moq,
                pack_size=pack_size,
                category=category,
                barcode=barcode,
            )
            .returning(products)
        )
        res = self.conn.execute(ins_stmt).fetchone()
        return dict(res._mapping)
