from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class LineItem:
    sku: str
    quantity: int
    unit_price: Decimal

    def to_dict(self) -> dict[str, Any]:
        return {
            "sku": self.sku,
            "quantity": self.quantity,
            "unit_price": str(self.unit_price),
        }


@dataclass(frozen=True)
class Order:
    po_number: str
    customer: str
    items: tuple[LineItem, ...]
    currency: str = "VND"

    @property
    def total(self) -> Decimal:
        return sum(
            (item.unit_price * item.quantity for item in self.items),
            start=Decimal("0"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "po_number": self.po_number,
            "customer": self.customer,
            "currency": self.currency,
            "items": [item.to_dict() for item in self.items],
            "total": str(self.total),
        }


@dataclass(frozen=True)
class Product:
    sku: str
    name: str
    unit_price: Decimal
    stock: int
    active: bool = True


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    message: str
    sku: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Analysis:
    order: Order
    findings: list[Finding] = field(default_factory=list)
    status: str = "review_required"
    analysis_id: int | None = None

    @property
    def error_count(self) -> int:
        return sum(f.severity == "error" for f in self.findings)

    @property
    def warning_count(self) -> int:
        return sum(f.severity == "warning" for f in self.findings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "status": self.status,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "order": self.order.to_dict(),
            "findings": [finding.to_dict() for finding in self.findings],
        }
