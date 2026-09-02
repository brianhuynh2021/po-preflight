from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from preflight.models import LineItem, Order
from preflight.services.decisions import DecisionResult


@dataclass(frozen=True)
class ERPItemDraft:
    sku: str
    description: str
    quantity: int
    uom: str
    unit_price: Decimal
    line_total: Decimal

    def to_dict(self) -> dict[str, Any]:
        return {
            "sku": self.sku,
            "description": self.description,
            "quantity": self.quantity,
            "uom": self.uom,
            "unit_price": str(self.unit_price),
            "line_total": str(self.line_total),
        }


@dataclass(frozen=True)
class ERPOrderDraft:
    po_number: str
    customer: str
    currency: str
    items: tuple[ERPItemDraft, ...]
    subtotal: Decimal
    approved_by: str | None = None
    approved_at: str | None = None
    source_analysis_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "po_number": self.po_number,
            "customer": self.customer,
            "currency": self.currency,
            "items": [item.to_dict() for item in self.items],
            "subtotal": str(self.subtotal),
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "source_analysis_id": self.source_analysis_id,
        }


def build_erp_payload(
    order_source: dict[str, Any] | Order,
    *,
    decision: DecisionResult | dict[str, Any] | None = None,
    source_analysis_id: int | None = None,
) -> ERPOrderDraft:
    """Build a validated, immutable ERPOrderDraft from an order row or domain Order object."""
    approved_by: str | None = None
    approved_at: str | None = None

    if isinstance(decision, DecisionResult):
        approved_by = decision.actor
        approved_at = decision.created_at
    elif isinstance(decision, dict):
        approved_by = decision.get("actor")
        approved_at = decision.get("created_at")

    if isinstance(order_source, Order):
        po_number = order_source.po_number
        customer = order_source.customer
        currency = order_source.currency or "VND"
        raw_items = order_source.items
    elif isinstance(order_source, dict):
        if "order_json" in order_source and order_source["order_json"]:
            try:
                parsed = json.loads(order_source["order_json"])
                po_number = parsed.get("po_number", order_source.get("po_number", ""))
                customer = parsed.get("customer", order_source.get("customer", ""))
                currency = parsed.get("currency", order_source.get("currency", "VND"))
                raw_items = parsed.get("items", [])
            except Exception:
                po_number = order_source.get("po_number", "")
                customer = order_source.get("customer", "")
                currency = order_source.get("currency", "VND")
                raw_items = order_source.get("items") or order_source.get("line_items") or []
        else:
            po_number = order_source.get("po_number", "")
            customer = order_source.get("customer", "")
            currency = order_source.get("currency", "VND")
            raw_items = order_source.get("items") or order_source.get("line_items") or []

        if source_analysis_id is None:
            source_analysis_id = order_source.get("id") or order_source.get("analysis_id")

        if approved_by is None:
            decisions = order_source.get("decisions", [])
            if decisions:
                last_dec = decisions[-1]
                approved_by = last_dec.get("actor")
                approved_at = last_dec.get("created_at")
    else:
        raise ValueError(f"Unsupported order source type: {type(order_source)}")

    if not raw_items:
        raise ValueError("ERP payload items cannot be empty.")

    item_drafts: list[ERPItemDraft] = []
    for item in raw_items:
        if isinstance(item, LineItem):
            sku = item.sku
            desc = item.sku
            qty = item.quantity
            uom = item.uom or "PCS"
            u_price = Decimal(str(item.unit_price))
            l_total = u_price * Decimal(str(qty))
        elif isinstance(item, dict):
            sku = str(item.get("sku", "")).strip()
            desc = str(item.get("description") or item.get("name") or sku).strip()
            qty = int(item.get("quantity", 1))
            uom = str(item.get("uom", "PCS")).strip()
            u_price = Decimal(str(item.get("unit_price", 0)))
            l_total = Decimal(str(item.get("line_total") or (u_price * Decimal(str(qty)))))
        else:
            raise ValueError(f"Unsupported line item format: {item}")

        item_drafts.append(
            ERPItemDraft(
                sku=sku,
                description=desc,
                quantity=qty,
                uom=uom,
                unit_price=u_price,
                line_total=l_total,
            )
        )

    computed_subtotal = sum((it.line_total for it in item_drafts), start=Decimal("0"))

    return ERPOrderDraft(
        po_number=po_number,
        customer=customer,
        currency=currency,
        items=tuple(item_drafts),
        subtotal=computed_subtotal,
        approved_by=approved_by,
        approved_at=approved_at,
        source_analysis_id=source_analysis_id,
    )
