from __future__ import annotations

import csv
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from preflight.models import LineItem, Order


class OrderParseError(ValueError):
    pass


def _decimal(value: Any, field: str = "number") -> Decimal:
    """Robust decimal parser handling standard and Vietnamese/European number formats.
    Examples:
    - '1250000' -> Decimal('1250000')
    - '1.250.000' -> Decimal('1250000')
    - '1,250,000' -> Decimal('1250000')
    - '1 250 000' -> Decimal('1250000')
    - '1.250.000,50' -> Decimal('1250000.50')
    - '1,250,000.50' -> Decimal('1250000.50')
    """
    if value is None:
        return Decimal("0")
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))

    s = str(value).strip().replace(" ", "")
    if not s:
        return Decimal("0")

    # Check for invalid alphabetic text (excluding known currency abbreviations)
    non_curr_text = re.sub(r"(?i)(vnd|vnđ|đ|\$|€|eur|usd)", "", s)
    if re.search(r"[a-zA-Z]", non_curr_text):
        raise OrderParseError(f"{field} is not a valid number: {value!r}")

    # Remove currency symbols (đ, VND, $, €) and stray text
    s_clean = re.sub(r"[^\d,\.\-]", "", s)
    if not s_clean or s_clean in {"-", ".", ","}:
        raise OrderParseError(f"{field} is not a valid number: {value!r}")

    # Vietnamese/European mixed format
    if "." in s_clean and "," in s_clean:
        if s_clean.rfind(",") > s_clean.rfind("."):
            # 1.250.000,50 -> 1250000.50
            s_clean = s_clean.replace(".", "").replace(",", ".")
        else:
            # 1,250,000.50 -> 1250000.50
            s_clean = s_clean.replace(",", "")
    elif "." in s_clean and not "," in s_clean:
        parts = s_clean.split(".")
        # Thousands separator with dot: 1.250.000 or 18.500
        if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3 and int(parts[0]) > 0 and len(parts[0]) <= 3):
            s_clean = s_clean.replace(".", "")
    elif "," in s_clean and not "." in s_clean:
        parts = s_clean.split(",")
        # Thousands separator with comma: 1,250,000
        if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3 and int(parts[0]) > 0 and len(parts[0]) <= 3):
            s_clean = s_clean.replace(",", "")
        else:
            # Decimal comma: 1250000,50 -> 1250000.50
            s_clean = s_clean.replace(",", ".")

    try:
        return Decimal(s_clean)
    except (InvalidOperation, AttributeError, ValueError) as exc:
        raise OrderParseError(f"{field} is not a valid number: {value!r}") from exc


def _quantity(value: Any) -> int:
    try:
        val_dec = _decimal(value, "quantity")
        quantity = int(val_dec)
    except Exception as exc:
        raise OrderParseError(f"quantity is invalid: {value!r}") from exc
    if quantity <= 0:
        raise OrderParseError("quantity must be greater than zero")
    return quantity


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    s = str(value).strip().lower()
    return s in {"true", "1", "yes", "t", "km", "tặng", "tên tặng", "hàng tặng", "promo"}


def _order_from_mapping(data: dict[str, Any]) -> Order:
    po_number = str(data.get("po_number", "")).strip()
    customer = str(data.get("customer", "")).strip()
    raw_items = data.get("items")
    if not po_number:
        raise OrderParseError("Missing po_number")
    if not customer:
        raise OrderParseError("Missing customer")
    if not isinstance(raw_items, list) or not raw_items:
        raise OrderParseError("An order must contain at least one item")

    items = []
    for item in raw_items:
        raw_sku = str(item.get("raw_sku") or item.get("sku", "")).strip()
        sku = str(item.get("sku", "")).strip().upper() or raw_sku.upper()
        desc = str(item.get("description", "")).strip() or None
        unit_price = _decimal(item.get("unit_price"), "unit_price")
        
        # Check promo detection
        is_promo = _bool(item.get("is_promo"))
        if not is_promo:
            combined_desc = f"{sku} {desc or ''}".upper()
            if unit_price == Decimal("0") or any(k in combined_desc for k in ["KM", "TẶNG", "KHUYEN MAI", "KHUYẾN MÃI", "HANG TANG"]):
                is_promo = True

        disc_pct = _decimal(item.get("discount_percent") or item.get("discount_pct") or 0, "discount_percent")
        disc_amt = _decimal(item.get("discount_amount") or 0, "discount_amount")
        tax_rate = _decimal(item.get("tax_rate") or item.get("vat") or 0, "tax_rate")

        items.append(
            LineItem(
                sku=sku,
                raw_sku=raw_sku or sku,
                description=desc,
                quantity=_quantity(item.get("quantity")),
                unit_price=unit_price,
                uom=str(item.get("uom", "PCS") or "PCS").strip().upper(),
                discount_percent=disc_pct,
                discount_amount=disc_amt,
                tax_rate=tax_rate,
                is_promo=is_promo,
            )
        )

    if any(not item.sku for item in items):
        raise OrderParseError("An item is missing its SKU")

    header_disc = _decimal(data.get("header_discount_amount") or data.get("discount_amount") or 0, "header_discount_amount")
    shipping = _decimal(data.get("shipping_fee") or 0, "shipping_fee")

    decl_subtotal = _decimal(data.get("declared_subtotal"), "declared_subtotal") if data.get("declared_subtotal") is not None else None
    decl_tax = _decimal(data.get("declared_tax"), "declared_tax") if data.get("declared_tax") is not None else None
    decl_total = _decimal(data.get("declared_total") or data.get("total"), "declared_total") if (data.get("declared_total") is not None or data.get("total") is not None) else None

    return Order(
        po_number=po_number,
        customer=customer,
        items=tuple(items),
        currency=str(data.get("currency", "VND")).strip().upper() or "VND",
        header_discount_amount=header_disc,
        shipping_fee=shipping,
        declared_subtotal=decl_subtotal,
        declared_tax=decl_tax,
        declared_total=decl_total,
    )


def parse_json(path: Path) -> Order:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise OrderParseError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise OrderParseError("The JSON root must be an object")
    return _order_from_mapping(data)


def parse_csv(path: Path) -> Order:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise OrderParseError("CSV contains no line items")
    first = rows[0]
    return _order_from_mapping(
        {
            "po_number": first.get("po_number"),
            "customer": first.get("customer"),
            "currency": first.get("currency", "VND"),
            "shipping_fee": first.get("shipping_fee"),
            "header_discount_amount": first.get("header_discount_amount"),
            "declared_total": first.get("declared_total") or first.get("total"),
            "items": [
                {
                    "sku": row.get("sku"),
                    "raw_sku": row.get("raw_sku"),
                    "description": row.get("description"),
                    "quantity": row.get("quantity"),
                    "unit_price": row.get("unit_price"),
                    "uom": row.get("uom", "PCS"),
                    "discount_percent": row.get("discount_percent") or row.get("discount_pct"),
                    "discount_amount": row.get("discount_amount"),
                    "tax_rate": row.get("tax_rate") or row.get("vat"),
                    "is_promo": row.get("is_promo"),
                }
                for row in rows
            ],
        }
    )


def parse_text(text: str) -> Order:
    header_pattern = re.compile(r"^(PO_NUMBER|CUSTOMER|CURRENCY|TOTAL|SHIPPING|DISCOUNT)\s*:\s*(.+)$", re.I)
    headers: dict[str, str] = {}
    items: list[dict[str, str]] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = header_pattern.match(line)
        if match:
            headers[match.group(1).lower()] = match.group(2).strip()
            continue
        if "|" not in line:
            continue
        parts = [part.strip() for part in line.split("|")]
        if not parts or parts[0].upper() in {"SKU", "STT", "NO"}:
            continue

        if len(parts) == 3:
            # Format: SKU | QTY | UNIT_PRICE
            items.append(
                {"sku": parts[0], "quantity": parts[1], "unit_price": parts[2], "uom": "PCS"}
            )
        elif len(parts) == 4:
            # Format: SKU | QTY | UOM | UNIT_PRICE
            items.append(
                {"sku": parts[0], "quantity": parts[1], "uom": parts[2], "unit_price": parts[3]}
            )
        elif len(parts) >= 5:
            # Format: SKU | QTY | UOM | UNIT_PRICE | DISCOUNT% | VAT%
            items.append(
                {
                    "sku": parts[0],
                    "quantity": parts[1],
                    "uom": parts[2],
                    "unit_price": parts[3],
                    "discount_percent": parts[4] if len(parts) > 4 else "0",
                    "tax_rate": parts[5] if len(parts) > 5 else "0",
                }
            )

    return _order_from_mapping(
        {
            "po_number": headers.get("po_number"),
            "customer": headers.get("customer"),
            "currency": headers.get("currency", "VND"),
            "declared_total": headers.get("total"),
            "shipping_fee": headers.get("shipping"),
            "header_discount_amount": headers.get("discount"),
            "items": items,
        }
    )


def parse_pdf(path: Path) -> Order:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise OrderParseError(
            "PDF support requires an optional dependency: python3 -m pip install '.[pdf]'"
        ) from exc
    text = "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    if not text.strip():
        raise OrderParseError("The PDF has no text layer and requires OCR")
    return parse_text(text)


def parse_order(path: str | Path) -> Order:
    source = Path(path)
    if not source.is_file():
        raise OrderParseError(f"File not found: {source}")
    suffix = source.suffix.lower()
    if suffix == ".json":
        return parse_json(source)
    if suffix == ".csv":
        return parse_csv(source)
    if suffix in {".xlsx", ".xlsm", ".xls"}:
        from preflight.ingestion.excel_parser import ExcelExtractor
        extractor = ExcelExtractor()
        _, domain_order = extractor.extract(source.read_bytes(), source.name)
        return domain_order
    if suffix in {".txt", ".md"}:
        return parse_text(source.read_text(encoding="utf-8"))
    if suffix == ".pdf":
        return parse_pdf(source)
    raise OrderParseError(f"Unsupported file format: {suffix or '(no extension)'}")


def parse_order_content(content: str, suffix: str = ".json") -> Order:
    """Parse raw text/JSON/CSV content into a domain Order."""
    suffix = suffix.lower()
    if suffix == ".json":
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise OrderParseError(f"Invalid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise OrderParseError("The JSON root must be an object")
        return _order_from_mapping(data)
    if suffix == ".csv":
        import io
        rows = list(csv.DictReader(io.StringIO(content)))
        if not rows:
            raise OrderParseError("CSV contains no line items")
        first = rows[0]
        return _order_from_mapping(
            {
                "po_number": first.get("po_number"),
                "customer": first.get("customer"),
                "currency": first.get("currency", "VND"),
                "shipping_fee": first.get("shipping_fee"),
                "header_discount_amount": first.get("header_discount_amount"),
                "declared_total": first.get("declared_total") or first.get("total"),
                "items": [
                    {
                        "sku": row.get("sku"),
                        "raw_sku": row.get("raw_sku"),
                        "description": row.get("description"),
                        "quantity": row.get("quantity"),
                        "unit_price": row.get("unit_price"),
                        "uom": row.get("uom", "PCS"),
                        "discount_percent": row.get("discount_percent") or row.get("discount_pct"),
                        "discount_amount": row.get("discount_amount"),
                        "tax_rate": row.get("tax_rate") or row.get("vat"),
                        "is_promo": row.get("is_promo"),
                    }
                    for row in rows
                ],
            }
        )
    return parse_text(content)
