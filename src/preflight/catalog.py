from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

from preflight.models import Product


def load_catalog(path: str | Path) -> dict[str, Product]:
    source = Path(path)
    with source.open(encoding="utf-8-sig", newline="") as handle:
        rows = csv.DictReader(handle)
        products = {
            row["sku"].strip().upper(): Product(
                sku=row["sku"].strip().upper(),
                name=row["name"].strip(),
                unit_price=Decimal(row["unit_price"].strip()),
                stock=int(row["stock"].strip()),
                active=row.get("active", "true").strip().lower() in {"1", "true", "yes"},
            )
            for row in rows
        }
    if not products:
        raise ValueError("Catalog is empty")
    return products
