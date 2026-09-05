from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class LineItem:
    sku: str
    quantity: int
    unit_price: Decimal
    uom: str = "PCS"
    raw_sku: str | None = None
    description: str | None = None
    discount_percent: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("0")
    is_promo: bool = False

    @property
    def line_net(self) -> Decimal:
        base = self.unit_price * self.quantity
        pct_disc = (base * self.discount_percent) / Decimal("100")
        net = base - self.discount_amount - pct_disc
        return max(Decimal("0"), net)

    @property
    def line_tax(self) -> Decimal:
        return (self.line_net * self.tax_rate) / Decimal("100")

    @property
    def line_total(self) -> Decimal:
        return self.line_net + self.line_tax

    def to_dict(self) -> dict[str, Any]:
        return {
            "sku": self.sku,
            "raw_sku": self.raw_sku or self.sku,
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": str(self.unit_price),
            "uom": self.uom,
            "discount_percent": str(self.discount_percent),
            "discount_amount": str(self.discount_amount),
            "tax_rate": str(self.tax_rate),
            "is_promo": self.is_promo,
            "line_net": str(self.line_net),
            "line_tax": str(self.line_tax),
            "line_total": str(self.line_total),
        }


@dataclass
class Order:
    po_number: str
    customer: str
    items: tuple[LineItem, ...]
    currency: str = "VND"
    order_date: str | None = None
    header_discount_amount: Decimal = Decimal("0")
    shipping_fee: Decimal = Decimal("0")
    declared_subtotal: Decimal | None = None
    declared_tax: Decimal | None = None
    declared_total: Decimal | None = None
    created_by: str = ""
    last_modified_by: str = ""

    @property
    def subtotal(self) -> Decimal:
        raw_sum = sum((item.line_net for item in self.items), start=Decimal("0"))
        return max(Decimal("0"), raw_sum - self.header_discount_amount)

    @property
    def tax_amount(self) -> Decimal:
        return sum((item.line_tax for item in self.items), start=Decimal("0"))

    @property
    def grand_total(self) -> Decimal:
        return self.subtotal + self.tax_amount + self.shipping_fee

    @property
    def total(self) -> Decimal:
        return self.grand_total

    def to_dict(self) -> dict[str, Any]:
        return {
            "po_number": self.po_number,
            "customer": self.customer,
            "currency": self.currency,
            "order_date": self.order_date,
            "header_discount_amount": str(self.header_discount_amount),
            "shipping_fee": str(self.shipping_fee),
            "declared_subtotal": str(self.declared_subtotal) if self.declared_subtotal is not None else None,
            "declared_tax": str(self.declared_tax) if self.declared_tax is not None else None,
            "declared_total": str(self.declared_total) if self.declared_total is not None else None,
            "created_by": self.created_by,
            "last_modified_by": self.last_modified_by,
            "items": [item.to_dict() for item in self.items],
            "subtotal": str(self.subtotal),
            "tax_amount": str(self.tax_amount),
            "total": str(self.total),
            "grand_total": str(self.grand_total),
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
    outstanding_balance: Decimal = Decimal("0")
    overdue_balance: Decimal = Decimal("0")
    oldest_overdue_days: int = 0
    status: str = "ACTIVE"

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
    severity: str  # "info", "warning", "error"
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
    policy_version: str = "2.0"
    catalog_snapshot_at: str | None = None
    revision: int = 1
    supersedes_order_id: int | None = None

    @property
    def error_count(self) -> int:
        return sum(f.severity == "error" for f in self.findings)

    @property
    def warning_count(self) -> int:
        return sum(f.severity == "warning" for f in self.findings)

    @property
    def info_count(self) -> int:
        return sum(f.severity == "info" for f in self.findings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "status": self.status,
            "revision": self.revision,
            "supersedes_order_id": self.supersedes_order_id,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "policy_version": self.policy_version,
            "catalog_snapshot_at": self.catalog_snapshot_at,
            "order": self.order.to_dict(),
            "findings": [finding.to_dict() for finding in self.findings],
        }


OrderAnalysis = Analysis


@dataclass(frozen=True)
class ApprovalTier:
    max_amount: Decimal | None
    required_role: str = "manager"
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_amount": str(self.max_amount) if self.max_amount is not None else None,
            "required_role": self.required_role,
            "description": self.description,
        }


@dataclass(frozen=True)
class RulePolicy:
    price_tolerance_percent: Decimal = Decimal("0")
    stock_safety_margin: int = 0
    allow_inactive_sku: bool = False
    auto_approve_ready: bool = False
    max_discount_percent: Decimal = Decimal("15")
    overdue_grace_days: int = 30
    credit_limit_block_percent: Decimal = Decimal("20")
    credit_hold_behaviour: str = "review"  # "block" | "review"
    approval_tiers: tuple[ApprovalTier, ...] = (
        ApprovalTier(max_amount=Decimal("50000000"), required_role="manager", description="Dưới 50 triệu"),
        ApprovalTier(max_amount=None, required_role="director", description="Trên 50 triệu"),
    )
    credit_exception_min_role: str = "director"
    enforce_separation_of_duties: bool = True
    inventory_stale_hours: int = 24
    version: str = "2.0"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RulePolicy:
        tiers = data.get("approval_tiers")
        if tiers is not None:
            parsed_tiers = []
            for t in tiers:
                if isinstance(t, ApprovalTier):
                    parsed_tiers.append(t)
                elif isinstance(t, dict):
                    max_amt = Decimal(str(t["max_amount"])) if t.get("max_amount") is not None else None
                    req_role = str(t.get("required_role") or t.get("min_role") or "manager").strip().lower()
                    desc = t.get("description")
                    parsed_tiers.append(ApprovalTier(max_amount=max_amt, required_role=req_role, description=desc))
            approval_tuple = tuple(parsed_tiers)
        else:
            approval_tuple = (
                ApprovalTier(max_amount=Decimal("50000000"), required_role="manager", description="Dưới 50 triệu"),
                ApprovalTier(max_amount=None, required_role="director", description="Trên 50 triệu"),
            )

        return cls(
            price_tolerance_percent=Decimal(str(data.get("price_tolerance_percent", "0"))),
            stock_safety_margin=int(data.get("stock_safety_margin", 0)),
            allow_inactive_sku=bool(data.get("allow_inactive_sku", False)),
            auto_approve_ready=bool(data.get("auto_approve_ready", False)),
            max_discount_percent=Decimal(str(data.get("max_discount_percent", "15"))),
            overdue_grace_days=int(data.get("overdue_grace_days", 30)),
            credit_limit_block_percent=Decimal(str(data.get("credit_limit_block_percent", "20"))),
            credit_hold_behaviour=str(data.get("credit_hold_behaviour", "review")).strip().lower(),
            approval_tiers=approval_tuple,
            credit_exception_min_role=str(data.get("credit_exception_min_role", "director")).strip().lower(),
            enforce_separation_of_duties=bool(data.get("enforce_separation_of_duties", True)),
            inventory_stale_hours=int(data.get("inventory_stale_hours", 24)),
            version=str(data.get("version", "2.0")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "price_tolerance_percent": str(self.price_tolerance_percent),
            "stock_safety_margin": self.stock_safety_margin,
            "allow_inactive_sku": self.allow_inactive_sku,
            "auto_approve_ready": self.auto_approve_ready,
            "max_discount_percent": str(self.max_discount_percent),
            "overdue_grace_days": self.overdue_grace_days,
            "credit_limit_block_percent": str(self.credit_limit_block_percent),
            "credit_hold_behaviour": self.credit_hold_behaviour,
            "approval_tiers": [t.to_dict() for t in self.approval_tiers],
            "credit_exception_min_role": self.credit_exception_min_role,
            "enforce_separation_of_duties": self.enforce_separation_of_duties,
            "inventory_stale_hours": self.inventory_stale_hours,
            "version": self.version,
        }


@dataclass
class User:
    username: str
    display_name: str
    email: str
    password_hash: str | None = None
    role: str = "viewer"  # viewer, auditor, sales_admin, manager, director, admin
    org_id: str = "org_default"
    is_active: bool = True
    failed_attempts: int = 0
    locked_until: str | None = None
    id: int | None = None
    created_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "org_id": self.org_id,
            "username": self.username,
            "display_name": self.display_name,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "failed_attempts": self.failed_attempts,
            "locked_until": self.locked_until,
            "created_at": self.created_at,
        }


@dataclass
class CustomerMaster:
    code: str
    name: str
    normalized_name: str = ""
    tax_code: str | None = None
    tier: str = "STANDARD"
    aliases: list[str] = field(default_factory=list)
    contact_emails: list[str] = field(default_factory=list)
    id: int | None = None
    created_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "normalized_name": self.normalized_name,
            "tax_code": self.tax_code,
            "tier": self.tier,
            "aliases": self.aliases,
            "contact_emails": self.contact_emails,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class InventorySnapshot:
    sku: str
    warehouse: str = "DEFAULT"
    on_hand: Decimal = Decimal("0")
    reserved: Decimal = Decimal("0")
    as_of: str = ""
    source: str = "odoo"
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "sku": self.sku,
            "warehouse": self.warehouse,
            "on_hand": str(self.on_hand),
            "reserved": str(self.reserved),
            "as_of": self.as_of,
            "source": self.source,
        }


@dataclass
class OrganizationScope:
    code: str
    name: str
    description: str = ""
    icon: str = ""
    parent_code: str | None = None
    is_active: bool = True
    id: int | None = None
    created_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "parent_code": self.parent_code,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


@dataclass
class RuleDefinitionRecord:
    id: str
    code: str
    name: str
    description: str
    category: str
    severity: str
    owner: str
    enabled: bool = True
    scope: str = "global"
    custom_condition: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "severity": self.severity,
            "owner": self.owner,
            "enabled": self.enabled,
            "scope": self.scope,
            "custom_condition": self.custom_condition,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }



