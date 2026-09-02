from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class LineItem:
    sku: str
    quantity: int
    unit_price: Decimal
    uom: str = "PCS"

    def to_dict(self) -> dict[str, Any]:
        return {
            "sku": self.sku,
            "quantity": self.quantity,
            "unit_price": str(self.unit_price),
            "uom": self.uom,
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

    @property
    def subtotal(self) -> Decimal:
        return self.total

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
    base_uom: str = "PCS"
    moq: int = 1
    pack_size: int = 1
    category: str | None = None
    barcode: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "sku": self.sku,
            "name": self.name,
            "unit_price": str(self.unit_price),
            "stock": self.stock,
            "active": self.active,
            "base_uom": self.base_uom,
            "moq": self.moq,
            "pack_size": self.pack_size,
            "category": self.category,
            "barcode": self.barcode,
        }


@dataclass(frozen=True)
class CustomerPriceAgreement:
    customer_id: str
    sku: str
    contract_price: Decimal
    min_quantity: int = 1
    discount_percent: Decimal = Decimal("0")
    valid_from: str | None = None
    valid_to: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "customer_id": self.customer_id,
            "sku": self.sku,
            "contract_price": str(self.contract_price),
            "min_quantity": self.min_quantity,
            "discount_percent": str(self.discount_percent),
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
        }


@dataclass(frozen=True)
class UOMConversion:
    sku: str
    uom_code: str
    base_uom: str
    conversion_factor: Decimal

    def to_dict(self) -> dict[str, Any]:
        return {
            "sku": self.sku,
            "uom_code": self.uom_code,
            "base_uom": self.base_uom,
            "conversion_factor": str(self.conversion_factor),
        }


@dataclass(frozen=True)
class CustomerCreditProfile:
    customer_id: str
    credit_limit: Decimal
    outstanding_balance: Decimal
    overdue_balance: Decimal
    oldest_overdue_days: int = 0
    status: str = "ACTIVE"  # ACTIVE, ON_HOLD, BLOCKED

    @property
    def available_credit(self) -> Decimal:
        return max(Decimal("0"), self.credit_limit - self.outstanding_balance)

    def to_dict(self) -> dict[str, Any]:
        return {
            "customer_id": self.customer_id,
            "credit_limit": str(self.credit_limit),
            "outstanding_balance": str(self.outstanding_balance),
            "overdue_balance": str(self.overdue_balance),
            "oldest_overdue_days": self.oldest_overdue_days,
            "status": self.status,
            "available_credit": str(self.available_credit),
        }


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    message: str
    sku: str | None = None
    evidence: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


OrderFinding = Finding


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


OrderAnalysis = Analysis


@dataclass(frozen=True)
class RulePolicy:
    price_tolerance_percent: Decimal = Decimal("0")
    stock_safety_margin: int = 0
    allow_inactive_sku: bool = False
    auto_approve_ready: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "price_tolerance_percent": str(self.price_tolerance_percent),
            "stock_safety_margin": self.stock_safety_margin,
            "allow_inactive_sku": self.allow_inactive_sku,
            "auto_approve_ready": self.auto_approve_ready,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RulePolicy:
        return cls(
            price_tolerance_percent=Decimal(str(data.get("price_tolerance_percent", 0))),
            stock_safety_margin=int(data.get("stock_safety_margin", 0)),
            allow_inactive_sku=bool(data.get("allow_inactive_sku", False)),
            auto_approve_ready=bool(data.get("auto_approve_ready", False)),
        )
