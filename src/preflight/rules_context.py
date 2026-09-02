from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Callable, Mapping

from preflight.models import (
    CustomerCreditProfile,
    CustomerPriceAgreement,
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
    TODO(B5): Replace with canonical customer_id from CustomerMaster.
    """
    if not name:
        return ""
    # Normalize unicode NFKD and remove diacritics
    nfkd = unicodedata.normalize("NFKD", name.strip())
    without_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    cleaned = without_accents.upper()

    # Remove corporate entity prefixes and suffixes in Vietnamese & English
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

    # Remove non-alphanumeric punctuation
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    # Collapse multiple whitespaces
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
    duplicate: bool = False
    fx_rates: Mapping[str, Decimal] = field(default_factory=dict)  # "USD_VND" -> rate
    fx_source: str = "static"  # "static" | "live" | "none"


def build_rule_context(
    store: BaseAuditStore,
    catalog: dict[str, Product],
    order: Order,
    *,
    policy: RulePolicy | None = None,
    fx_provider: Callable[[str, str], tuple[Decimal, str]] | None = None,
    duplicate: bool | None = None,
) -> RuleContext:
    """Central factory for building immutable RuleContext from store, master data, and policies.
    
    This is the ONLY designated location for pulling customer pricing, UOM conversions,
    credit profiles, PO duplication checks, and currency exchange rates before pure rule evaluation.
    """
    if policy is None:
        try:
            policy = store.get_policy()
        except Exception:
            policy = RulePolicy()

    # Determine customer lookup keys (both raw and normalized)
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

    # 5. FX Rates for non-VND orders
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

    return RuleContext(
        catalog=catalog,
        pricing_agreements=tuple(pricing_list),
        uom_conversions=tuple(uom_list),
        customer_credit=credit,
        price_tolerance_percent=policy.price_tolerance_percent,
        stock_safety_margin=policy.stock_safety_margin,
        allow_inactive_sku=policy.allow_inactive_sku,
        duplicate=is_duplicate,
        fx_rates=fx_rates,
        fx_source=fx_source,
    )
