from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping

from preflight.models import (
    Analysis,
    CustomerCreditProfile,
    CustomerPriceAgreement,
    Finding,
    Order,
    Product,
    UOMConversion,
)
from preflight.rag.matcher import HybridSKUMatcher
from preflight.rules_context import RuleContext


def analyze_order(
    order: Order,
    ctx: RuleContext | dict[str, Product],
    *,
    duplicate: bool = False,
    price_tolerance_percent: Decimal = Decimal("0"),
    pricing_agreements: list[CustomerPriceAgreement] | None = None,
    uom_conversions: list[UOMConversion] | None = None,
    customer_credit: CustomerCreditProfile | None = None,
) -> Analysis:
    """Pure rule evaluation engine.
    
    Given an order and an immutable RuleContext, deterministically evaluates:
    - Customer credit status & exposure limits
    - Duplicate PO detection
    - Item quantity & price sanity
    - Hybrid SKU recognition & active catalog status
    - Unit of Measure (UOM) conversions & MOQ/packaging validation
    - Warehouse stock availability with safety margin thresholds
    - Tiered volume customer contract pricing
    - Multi-currency FX conversion and tolerance thresholding
    """
    if isinstance(ctx, dict):
        # Gracefully wrap legacy catalog dict into RuleContext
        fx_rates: dict[str, Decimal] = {}
        fx_source = "static"
        order_currency = (order.currency or "VND").strip().upper()
        if order_currency != "VND":
            from preflight.currency import fx_engine
            rate_val, fx_source = fx_engine.get_rate_info(order_currency, "VND")
            fx_rates[f"{order_currency}_VND"] = rate_val

        context = RuleContext(
            catalog=ctx,
            pricing_agreements=tuple(pricing_agreements or ()),
            uom_conversions=tuple(uom_conversions or ()),
            customer_credit=customer_credit,
            price_tolerance_percent=price_tolerance_percent,
            duplicate=duplicate,
            fx_rates=fx_rates,
            fx_source=fx_source,
        )
    else:
        context = ctx


    findings: list[Finding] = []
    catalog = context.catalog
    matcher = HybridSKUMatcher(catalog)

    if context.duplicate:
        findings.append(
            Finding(
                code="DUPLICATE_PO",
                severity="error",
                message=f"PO {order.po_number} has already been processed.",
            )
        )

    # -------------------------------------------------------------
    # 1. Customer Credit & Debt Risk Rules
    # -------------------------------------------------------------
    customer_credit = context.customer_credit
    if customer_credit:
        if customer_credit.status == "BLOCKED":
            findings.append(
                Finding(
                    code="CUSTOMER_BLOCKED",
                    severity="error",
                    message=f"Customer '{order.customer}' credit status is BLOCKED. Order intake suspended.",
                )
            )
        elif customer_credit.overdue_balance > 0 and customer_credit.oldest_overdue_days > 30:
            findings.append(
                Finding(
                    code="OVERDUE_DEBT_BLOCKED",
                    severity="error",
                    message=(
                        f"Customer '{order.customer}' has overdue debt of {customer_credit.overdue_balance:,.0f} VND "
                        f"aged {customer_credit.oldest_overdue_days} days (exceeds 30-day grace limit)."
                    ),
                )
            )
        
        # Calculate Credit Ceiling Exposure
        total_exposure = customer_credit.outstanding_balance + order.total
        if total_exposure > customer_credit.credit_limit:
            deficit = total_exposure - customer_credit.credit_limit
            findings.append(
                Finding(
                    code="CREDIT_LIMIT_EXCEEDED",
                    severity="error" if customer_credit.credit_limit == 0 or (deficit / customer_credit.credit_limit) > Decimal("0.2") else "warning",
                    message=(
                        f"Order total {order.total:,.0f} VND pushes customer credit exposure to {total_exposure:,.0f} VND, "
                        f"exceeding approved credit limit of {customer_credit.credit_limit:,.0f} VND by {deficit:,.0f} VND."
                    ),
                )
            )

    # Fast lookup for pricing agreements by (customer_id, sku)
    agreements_map: dict[tuple[str, str], CustomerPriceAgreement] = {}
    for pa in context.pricing_agreements:
        agreements_map[(pa.customer_id.strip().upper(), pa.sku.strip().upper())] = pa
        from preflight.rules_context import normalize_customer_key
        norm_key = normalize_customer_key(pa.customer_id)
        if norm_key:
            agreements_map[(norm_key, pa.sku.strip().upper())] = pa


    # Fast lookup for UOM conversions by (sku, uom_code)
    uom_map: dict[tuple[str, str], Decimal] = {}
    for u in context.uom_conversions:
        uom_map[(u.sku.strip().upper(), u.uom_code.strip().upper())] = u.conversion_factor

    # -------------------------------------------------------------
    # 2. Line Item Rules & Validations
    # -------------------------------------------------------------
    for item in order.items:
        if item.quantity <= 0:
            findings.append(
                Finding(
                    code="INVALID_QUANTITY",
                    severity="error",
                    sku=item.sku,
                    message=f"SKU {item.sku}: quantity must be positive (received {item.quantity}).",
                )
            )
        if item.unit_price < 0:
            findings.append(
                Finding(
                    code="INVALID_PRICE",
                    severity="error",
                    sku=item.sku,
                    message=f"SKU {item.sku}: unit price cannot be negative (received {item.unit_price}).",
                )
            )

        product = catalog.get(item.sku)

        if product is None:
            # Check Hybrid SKU Matcher for suggestions
            resolution = matcher.resolve(item.sku, customer_id=order.customer)
            if resolution.is_confident and resolution.matched_sku:
                findings.append(
                    Finding(
                        code="UNKNOWN_SKU",
                        severity="warning",
                        sku=item.sku,
                        message=(
                            f"SKU '{item.sku}' not found in catalog. "
                            f"AI suggested match: '{resolution.matched_sku}' ({resolution.name}) "
                            f"with {resolution.confidence_score*100:.0f}% confidence [{resolution.tier_used.value}]."
                        ),
                    )
                )
            else:
                findings.append(
                    Finding(
                        code="UNKNOWN_SKU",
                        severity="error",
                        sku=item.sku,
                        message=f"SKU {item.sku} does not exist in the catalog.",
                    )
                )
            continue

        if not product.active:
            inactive_severity = "warning" if context.allow_inactive_sku else "error"
            findings.append(
                Finding(
                    code="INACTIVE_SKU",
                    severity=inactive_severity,
                    sku=item.sku,
                    message=f"SKU {item.sku} is inactive.",
                )
            )

        # -------------------------------------------------------------
        # UOM & MOQ / Pack Multiplier Rules
        # -------------------------------------------------------------
        declared_uom = (getattr(item, "uom", None) or "PCS").strip().upper()
        base_uom = (getattr(product, "base_uom", None) or "PCS").strip().upper()
        
        conversion_factor = Decimal("1.0")
        if declared_uom != base_uom:
            conversion_factor = uom_map.get((item.sku.upper(), declared_uom), Decimal("1.0"))

        base_quantity = Decimal(str(item.quantity)) * conversion_factor
        moq = getattr(product, "moq", 1)
        pack_size = getattr(product, "pack_size", 1)

        if base_quantity < Decimal(str(moq)):
            findings.append(
                Finding(
                    code="BELOW_MOQ",
                    severity="warning",
                    sku=item.sku,
                    message=(
                        f"SKU {item.sku}: ordered {item.quantity} {declared_uom} (~{base_quantity:.0f} {base_uom}) "
                        f"is below supplier Minimum Order Quantity (MOQ: {moq} {base_uom})."
                    ),
                )
            )

        if pack_size > 1 and (base_quantity % Decimal(str(pack_size))) != 0:
            findings.append(
                Finding(
                    code="INVALID_PACK_SIZE",
                    severity="warning",
                    sku=item.sku,
                    message=(
                        f"SKU {item.sku}: ordered quantity ({base_quantity:.0f} {base_uom}) is not a multiple "
                        f"of standard packaging pack size ({pack_size} {base_uom}/pack)."
                    ),
                )
            )

        # Warehouse stock verification against base inventory units & safety margin
        effective_stock = max(0, product.stock - context.stock_safety_margin)
        if int(base_quantity) > effective_stock:
            safety_note = f" (safety margin: {context.stock_safety_margin})" if context.stock_safety_margin > 0 else ""
            findings.append(
                Finding(
                    code="INSUFFICIENT_STOCK",
                    severity="warning",
                    sku=item.sku,
                    message=(
                        f"SKU {item.sku}: ordered {item.quantity} {declared_uom} (~{base_quantity:.0f} {base_uom}), "
                        f"only {product.stock} {base_uom} in stock{safety_note}."
                    ),
                )
            )

        # -------------------------------------------------------------
        # Contract Pricing & Multi-Currency FX Tolerance
        # -------------------------------------------------------------
        from preflight.rules_context import normalize_customer_key
        norm_order_cust = normalize_customer_key(order.customer)
        cust_agreement = agreements_map.get((order.customer.strip().upper(), item.sku.strip().upper())) or agreements_map.get((norm_order_cust, item.sku.strip().upper()))
        
        expected_price = product.unit_price
        if cust_agreement and item.quantity >= cust_agreement.min_quantity:
            discount_mult = Decimal("1") - (cust_agreement.discount_percent / Decimal("100"))
            expected_price = cust_agreement.contract_price * discount_mult

        if declared_uom != base_uom and conversion_factor > Decimal("0"):
            expected_price = expected_price * conversion_factor


        if expected_price > 0:
            order_curr = (order.currency or "VND").strip().upper()
            if order_curr != "VND":
                fx_key = f"{order_curr}_VND"
                fx_rate = context.fx_rates.get(fx_key)
                if fx_rate is None or fx_rate <= Decimal("0"):
                    findings.append(
                        Finding(
                            code="FX_RATE_UNAVAILABLE",
                            severity="error",
                            sku=item.sku,
                            message=f"Tỷ giá cho cặp tiền {order_curr}/VND không khả dụng.",
                        )
                    )
                else:
                    converted_price = Decimal(str(item.unit_price)) * fx_rate
                    difference = abs(converted_price - expected_price)
                    percent = (difference / expected_price) * Decimal("100")
                    if percent > context.price_tolerance_percent:
                        source_note = " (tỷ giá tĩnh)" if context.fx_source == "static" else ""
                        findings.append(
                            Finding(
                                code="PRICE_MISMATCH",
                                severity="warning",
                                sku=item.sku,
                                message=(
                                    f"SKU {item.sku}: PO price {item.unit_price:,.2f} {order_curr} "
                                    f"(~{converted_price:,.0f} VND), target price {expected_price:,.0f} VND "
                                    f"({percent:.2f}% difference at FX rate {fx_rate:,.2f}{source_note})."
                                ),
                            )
                        )
            else:
                difference = abs(item.unit_price - expected_price)
                percent = (difference / expected_price) * Decimal("100")
                if percent > context.price_tolerance_percent:
                    findings.append(
                        Finding(
                            code="PRICE_MISMATCH",
                            severity="warning",
                            sku=item.sku,
                            message=(
                                f"SKU {item.sku}: PO price {item.unit_price:,.0f} VND, "
                                f"target price {expected_price:,.0f} VND ({percent:.2f}% difference)."
                            ),
                        )
                    )

    if any(f.severity == "error" for f in findings):
        status = "blocked"
    elif findings:
        status = "review_required"
    else:
        status = "ready_for_approval"
    return Analysis(order=order, findings=findings, status=status)


class DecisionValidationError(Exception):
    """Raised when an approval/rejection decision violates financial control & governance constraints."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def validate_order_decision(
    current_status: str,
    decision: str,
    note: str | None = None,
    error_count: int = 0,
) -> None:
    """Enforce financial control and governance constraints for PO decisions:
    1. A Blocked order (with error findings) can NEVER be approved -> HTTP 409
    2. An already decided order (approved/rejected) cannot be re-decided -> HTTP 409
    3. Rejection, changes requested, or approval over warnings requires an exception note (min 10 chars) -> HTTP 422
    """
    normalized_decision = decision.lower().strip()
    normalized_status = current_status.lower().strip()
    clean_note = (note or "").strip()

    if normalized_status in {"approved", "rejected"}:
        raise DecisionValidationError(
            f"Order has already been decided ({current_status}). Re-decision is not permitted.",
            status_code=409,
        )

    if normalized_decision == "approved":
        if normalized_status == "blocked" or error_count > 0:
            raise DecisionValidationError(
                "A blocked order with validation errors cannot be approved. Resolve all blocking findings before approving.",
                status_code=409,
            )
        if normalized_status in {"review_required", "warning"}:
            if len(clean_note) < 10:
                raise DecisionValidationError(
                    "Approving an order with review findings requires an exception note of at least 10 characters.",
                    status_code=422,
                )
    elif normalized_decision in {"rejected", "needs_changes"}:
        if len(clean_note) < 10:
            raise DecisionValidationError(
                f"A justification note of at least 10 characters is required to {normalized_decision.replace('_', ' ')}.",
                status_code=422,
            )
