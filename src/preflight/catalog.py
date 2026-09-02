from __future__ import annotations

import csv
import os
import threading
from decimal import Decimal, InvalidOperation
from pathlib import Path

from preflight.models import Product

_CATALOG_LOCK = threading.Lock()
_CATALOG_CACHE: dict[str, tuple[float, dict[str, Product]]] = {}


def invalidate_catalog_cache(path: str | Path | None = None) -> None:
    """Explicitly invalidate in-memory catalog cache."""
    with _CATALOG_LOCK:
        if path is None:
            _CATALOG_CACHE.clear()
        else:
            resolved_key = str(Path(path).resolve())
            _CATALOG_CACHE.pop(resolved_key, None)


def load_catalog(path: str | Path | None = None) -> dict[str, Product]:
    """Load product master catalog from CSV file with mtime caching and strict validation.

    Supported CSV columns:
    - Required: sku, name, unit_price, stock
    - Optional: active (default True), base_uom (default PCS), moq (default 1),
                pack_size (default 1), category (default None), barcode (default None)
    """
    if path is None:
        raw_path = os.getenv("CATALOG_PATH", "examples/catalog.csv")
        source = Path(raw_path)
    else:
        source = Path(path)

    if not source.exists():
        raise FileNotFoundError(f"Catalog file not found: {source}")

    resolved_path = str(source.resolve())
    current_mtime = source.stat().st_mtime

    with _CATALOG_LOCK:
        if resolved_path in _CATALOG_CACHE:
            cached_mtime, cached_products = _CATALOG_CACHE[resolved_path]
            if cached_mtime == current_mtime:
                return cached_products

    with source.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("Tệp catalog rỗng hoặc thiếu tiêu đề cột (header)")

        # Normalize fieldnames
        field_map = {f.strip().lower(): f for f in reader.fieldnames if f}
        required_fields = ["sku", "name", "unit_price", "stock"]
        missing_required = [rf for rf in required_fields if rf not in field_map]
        if missing_required:
            raise ValueError(f"Tệp catalog thiếu các cột bắt buộc: {', '.join(missing_required)}")

        products: dict[str, Product] = {}
        line_no = 1  # Header is line 1

        for raw_row in reader:
            line_no += 1
            row = {k.strip().lower(): (v.strip() if v else "") for k, v in raw_row.items() if k}

            sku = row.get("sku", "").upper()
            if not sku:
                raise ValueError(f"Dòng {line_no}: Cột 'sku' không được để trống")

            name = row.get("name", "")
            if not name:
                raise ValueError(f"Dòng {line_no}: Cột 'name' không được để trống")

            # Validate unit_price
            raw_price = row.get("unit_price", "")
            try:
                unit_price = Decimal(raw_price.replace(",", ""))
                if unit_price < 0:
                    raise ValueError("Giá đơn vị không được âm")
            except (InvalidOperation, ValueError) as exc:
                raise ValueError(f"Dòng {line_no}: Cột 'unit_price' ({raw_price!r}) không phải là số hợp lệ") from exc

            # Validate stock
            raw_stock = row.get("stock", "")
            try:
                stock = int(raw_stock)
                if stock < 0:
                    raise ValueError("Tồn kho không được âm")
            except ValueError as exc:
                raise ValueError(f"Dòng {line_no}: Cột 'stock' ({raw_stock!r}) phải là số nguyên >= 0") from exc

            # Optional active
            raw_active = row.get("active", "true").lower()
            active = raw_active in {"1", "true", "yes", "active"}

            # Optional base_uom
            base_uom = row.get("base_uom", "PCS").upper() or "PCS"

            # Optional moq
            raw_moq = row.get("moq", "1") or "1"
            try:
                moq = int(raw_moq)
                if moq < 1:
                    raise ValueError("MOQ phải >= 1")
            except ValueError as exc:
                raise ValueError(f"Dòng {line_no}: Cột 'moq' ({raw_moq!r}) phải là số nguyên >= 1") from exc

            # Optional pack_size
            raw_pack = row.get("pack_size", "1") or "1"
            try:
                pack_size = int(raw_pack)
                if pack_size < 1:
                    raise ValueError("Pack size phải >= 1")
            except ValueError as exc:
                raise ValueError(f"Dòng {line_no}: Cột 'pack_size' ({raw_pack!r}) phải là số nguyên >= 1") from exc

            # Optional category and barcode
            category = row.get("category") or None
            barcode = row.get("barcode") or None

            product = Product(
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
            products[sku] = product

    if not products:
        raise ValueError("Tệp catalog không chứa dòng sản phẩm nào")

    with _CATALOG_LOCK:
        _CATALOG_CACHE[resolved_path] = (current_mtime, products)

    return products


get_catalog = load_catalog

