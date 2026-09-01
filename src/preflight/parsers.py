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


def _decimal(value: Any, field: str) -> Decimal:
    try:
        return Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, AttributeError) as exc:
        raise OrderParseError(f"{field} is not a valid number: {value!r}") from exc


def _quantity(value: Any) -> int:
    try:
        quantity = int(str(value).strip())
    except ValueError as exc:
        raise OrderParseError(f"quantity is invalid: {value!r}") from exc
    if quantity <= 0:
        raise OrderParseError("quantity must be greater than zero")
    return quantity


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

    items = tuple(
        LineItem(
            sku=str(item.get("sku", "")).strip().upper(),
            quantity=_quantity(item.get("quantity")),
            unit_price=_decimal(item.get("unit_price"), "unit_price"),
        )
        for item in raw_items
    )
    if any(not item.sku for item in items):
        raise OrderParseError("An item is missing its SKU")
    return Order(
        po_number=po_number,
        customer=customer,
        items=items,
        currency=str(data.get("currency", "VND")).strip().upper() or "VND",
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
            "items": [
                {
                    "sku": row.get("sku"),
                    "quantity": row.get("quantity"),
                    "unit_price": row.get("unit_price"),
                }
                for row in rows
            ],
        }
    )


def parse_text(text: str) -> Order:
    header_pattern = re.compile(r"^(PO_NUMBER|CUSTOMER|CURRENCY)\s*:\s*(.+)$", re.I)
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
        if len(parts) != 3 or parts[0].upper() == "SKU":
            continue
        items.append(
            {"sku": parts[0], "quantity": parts[1], "unit_price": parts[2]}
        )

    return _order_from_mapping(
        {
            "po_number": headers.get("po_number"),
            "customer": headers.get("customer"),
            "currency": headers.get("currency", "VND"),
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
    if suffix in {".txt", ".md"}:
        return parse_text(source.read_text(encoding="utf-8"))
    if suffix == ".pdf":
        return parse_pdf(source)
    raise OrderParseError(f"Unsupported file format: {suffix or '(no extension)'}")


def parse_order_content(content: str, suffix: str = ".json") -> Order:
    """Parse raw text/JSON/CSV content into a domain Order."""
    import io

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
        handle = io.StringIO(content)
        rows = list(csv.DictReader(handle))
        if not rows:
            raise OrderParseError("CSV contains no line items")
        first = rows[0]
        return _order_from_mapping(
            {
                "po_number": first.get("po_number"),
                "customer": first.get("customer"),
                "currency": first.get("currency", "VND"),
                "items": [
                    {
                        "sku": row.get("sku"),
                        "quantity": row.get("quantity"),
                        "unit_price": row.get("unit_price"),
                    }
                    for row in rows
                ],
            }
        )

    return parse_text(content)

