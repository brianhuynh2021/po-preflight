from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Callable, Mapping

from preflight.models import (
    CustomerCreditProfile,
    CustomerPriceAgreement,
    InventorySnapshot,
    Order,
    Product,
    RulePolicy,
    UOMConversion,
)

if TYPE_CHECKING:
    from preflight.store import BaseAuditStore


def normalize_customer_key(name: str) -> str:
    """Normalize customer name to a standard key for master data lookup.
    
    Strips accents, corporate prefixes/suffixes, and punctuation.
    """
    if not name:
        return ""
    nfkd = unicodedata.normalize("NFKD", name.strip())
    without_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    cleaned = without_accents.upper()

    patterns = [
        r"\bCONG TY CO PHAN\b",
        r"\bCONG TY TNHH MTV\b",
        r"\bCONG TY TNHH\b",
        r"\bCONG TY\b",
        r"\bCTY CP\b",
        r"\bCT CP\b",
        r"\bCTY TNHH\b",
        r"\bCTY\b",
        r"\bTNHH MTV\b",
        r"\bTNHH\b",
        r"\bCO PHAN\b",
        r"\bJSC\b",
        r"\bCO\.,? LTD\b",
        r"\bLTD\b",
        r"\bCORP\b",
        r"\bINC\b",
    ]
    for p in patterns:
        cleaned = re.sub(p, " ", cleaned)

    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


@dataclass(frozen=True)
class RuleContext:
    catalog: dict[str, Product]
    pricing_agreements: tuple[CustomerPriceAgreement, ...] = ()
    uom_conversions: tuple[UOMConversion, ...] = ()
    customer_credit: CustomerCreditProfile | None = None
    price_tolerance_percent: Decimal = Decimal("0")
    stock_safety_margin: int = 0
    allow_inactive_sku: bool = False
    max_discount_percent: Decimal = Decimal("15")
    overdue_grace_days: int = 30
    credit_limit_block_percent: Decimal = Decimal("20")
    credit_hold_behaviour: str = "review"  # "block" | "review"
    policy_version: str = "2.0"
    order_date: str | None = None
    duplicate: bool = False
    recent_customer_orders: tuple[Order, ...] = ()
    revision_diff: dict[str, Any] | None = None
    fx_rates: Mapping[str, Decimal] = field(default_factory=dict)  # "USD_VND" -> rate
    fx_source: str = "static"  # "static" | "live" | "none"
    inventory_snapshots: tuple[InventorySnapshot, ...] = ()
    inventory_allocations: Mapping[str, Decimal] = field(default_factory=dict)
    inventory_stale_hours: int = 24

    def get_inventory_snapshot(self, sku: str) -> InventorySnapshot | None:
        clean_sku = sku.strip().upper()
        for s in self.inventory_snapshots:
            if s.sku.strip().upper() == clean_sku:
                return s
        return None

    def get_atp_info(self, sku: str) -> dict[str, Any]:
        snapshot = self.get_inventory_snapshot(sku)
        clean_sku = sku.strip().upper()
        # Look up allocated local stock
        allocated = Decimal("0")
        for k, v in self.inventory_allocations.items():
            if k.strip().upper() == clean_sku:
                allocated = v
                break

        prod = self.catalog.get(sku) or self.catalog.get(clean_sku)
        if snapshot:
            on_hand = snapshot.on_hand
            reserved_erp = snapshot.reserved
            as_of = snapshot.as_of
            source = snapshot.source
        else:
            on_hand = Decimal(str(prod.stock)) if prod else Decimal("0")
            reserved_erp = Decimal("0")
            as_of = ""
            source = "catalog"

        safety_margin = Decimal(str(self.stock_safety_margin))
        atp = max(Decimal("0"), on_hand - reserved_erp - allocated - safety_margin)

        is_stale = False
        if as_of:
            try:
                dt = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
                age_hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0
                if age_hours > self.inventory_stale_hours:
                    is_stale = True
            except Exception:
                pass

        return {
            "sku": sku,
            "on_hand": on_hand,
            "reserved_erp": reserved_erp,
            "allocated_local": allocated,
            "safety_margin": safety_margin,
            "atp": atp,
            "as_of": as_of,
            "source": source,
            "is_stale": is_stale,
        }

    def available_stock(self, product: Product) -> int:
        """Calculate effective available stock (ATP) factoring in inventory safety margins."""
        info = self.get_atp_info(product.sku)
        return int(info["atp"])



def build_rule_context(
    store: BaseAuditStore,
    catalog: dict[str, Product],
    order: Order,
    *,
    policy: RulePolicy | None = None,
    fx_provider: Callable[[str, str], tuple[Decimal, str]] | None = None,
    duplicate: bool | None = None,
    revision_diff: dict[str, Any] | None = None,
) -> RuleContext:
    """Central factory for building immutable RuleContext from store, master data, and policies."""
    if policy is None:
        try:
            policy = store.get_policy()
        except Exception:
            policy = RulePolicy()

    raw_customer = order.customer.strip()
    norm_customer = normalize_customer_key(raw_customer)

    # 1. Customer Credit Profile
    credit = store.get_customer_credit(raw_customer)
    if not credit and norm_customer != raw_customer:
        credit = store.get_customer_credit(norm_customer)

    # 2. Customer Pricing Agreements
    pricing_list = store.get_customer_pricing(raw_customer)
    if not pricing_list and norm_customer != raw_customer:
        pricing_list = store.get_customer_pricing(norm_customer)

    # 3. UOM Conversions
    uom_list = store.get_uom_conversions()

    # 4. Duplication Check
    is_duplicate = duplicate if duplicate is not None else store.has_po(order.po_number)

    # 5. Recent customer orders for near-duplicate detection
    recent_orders: list[Order] = []
    if hasattr(store, "get_recent_customer_orders"):
        try:
            recent_rows = store.get_recent_customer_orders(raw_customer, days=14)
            for r in recent_rows:
                ord_data = r.get("order_json")
                if ord_data:
                    import json
                    from preflight.models import LineItem
                    od = json.loads(ord_data) if isinstance(ord_data, str) else ord_data
                    items = tuple(
                        LineItem(
                            sku=it.get("sku", ""),
                            quantity=int(it.get("quantity", 1)),
                            unit_price=Decimal(str(it.get("unit_price", 0))),
                            uom=it.get("uom", "PCS"),
                        )
                        for it in od.get("items", [])
                    )
                    recent_orders.append(
                        Order(
                            po_number=od.get("po_number", r.get("po_number", "")),
                            customer=od.get("customer", r.get("customer", "")),
                            items=items,
                            currency=od.get("currency", "VND"),
                            order_date=od.get("order_date") or r.get("created_at"),
                        )
                    )
        except Exception:
            pass

    # 6. FX Rates for non-VND orders
    fx_rates: dict[str, Decimal] = {}
    fx_source = "static"
    order_currency = (order.currency or "VND").strip().upper()
    if order_currency != "VND":
        if fx_provider is not None:
            rate, source = fx_provider(order_currency, "VND")
            fx_rates[f"{order_currency}_VND"] = rate
            fx_source = source
        else:
            from preflight.currency import fx_engine
            rate_val, source = fx_engine.get_rate_info(order_currency, "VND")
            fx_rates[f"{order_currency}_VND"] = rate_val
            fx_source = source

    order_date = order.order_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 7. Inventory Snapshots & Local Allocations for ATP
    inventory_snapshots: list[InventorySnapshot] = []
    inventory_allocations: dict[str, Decimal] = {}
    if hasattr(store, "get_latest_inventory_snapshots"):
        try:
            snaps_dict = store.get_latest_inventory_snapshots()
            inventory_snapshots = list(snaps_dict.values())
        except Exception:
            pass
    if hasattr(store, "get_all_allocated_local_stock"):
        try:
            inventory_allocations = store.get_all_allocated_local_stock()
        except Exception:
            pass

    return RuleContext(
        catalog=catalog,
        pricing_agreements=tuple(pricing_list),
        uom_conversions=tuple(uom_list),
        customer_credit=credit,
        price_tolerance_percent=policy.price_tolerance_percent,
        stock_safety_margin=policy.stock_safety_margin,
        allow_inactive_sku=policy.allow_inactive_sku,
        max_discount_percent=getattr(policy, "max_discount_percent", Decimal("15")),
        overdue_grace_days=getattr(policy, "overdue_grace_days", 30),
        credit_limit_block_percent=getattr(policy, "credit_limit_block_percent", Decimal("20")),
        credit_hold_behaviour=getattr(policy, "credit_hold_behaviour", "review"),
        policy_version=getattr(policy, "version", "2.0"),
        order_date=order_date,
        duplicate=is_duplicate,
        recent_customer_orders=tuple(recent_orders),
        revision_diff=revision_diff,
        fx_rates=fx_rates,
        fx_source=fx_source,
        inventory_snapshots=tuple(inventory_snapshots),
        inventory_allocations=inventory_allocations,
        inventory_stale_hours=getattr(policy, "inventory_stale_hours", 24),
    )

