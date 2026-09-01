from __future__ import annotations

from decimal import Decimal

from preflight.currency import fx_engine
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


def analyze_order(
    order: Order,
    catalog: dict[str, Product],
    *,
    duplicate: bool = False,
    price_tolerance_percent: Decimal = Decimal("0"),
    pricing_agreements: list[CustomerPriceAgreement] | None = None,
    uom_conversions: list[UOMConversion] | None = None,
    customer_credit: CustomerCreditProfile | None = None,
) -> Analysis:
    findings: list[Finding] = []
    matcher = HybridSKUMatcher(catalog)
    if duplicate:
        findings.append(
            Finding(
                code="DUPLICATE_PO",
                severity="error",
                message=f"PO {order.po_number} has already been processed.",
            )
        )

    # -------------------------------------------------------------
    # 1. Customer Credit & Debt Risk Rules (Issue #74)
    # -------------------------------------------------------------
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
    if pricing_agreements:
        for pa in pricing_agreements:
            agreements_map[(pa.customer_id.strip().upper(), pa.sku.strip().upper())] = pa

    # Fast lookup for UOM conversions by (sku, uom_code)
    uom_map: dict[tuple[str, str], Decimal] = {}
    if uom_conversions:
        for u in uom_conversions:
            uom_map[(u.sku.strip().upper(), u.uom_code.strip().upper())] = u.conversion_factor

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
            findings.append(
                Finding(
                    code="INACTIVE_SKU",
                    severity="error",
                    sku=item.sku,
                    message=f"SKU {item.sku} is inactive.",
                )
            )

        # -------------------------------------------------------------
        # 2. UOM & MOQ / Pack Multiplier Rules (Issue #73)
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

        # Warehouse stock verification against base inventory units
        if int(base_quantity) > product.stock:
            findings.append(
                Finding(
                    code="INSUFFICIENT_STOCK",
                    severity="warning",
                    sku=item.sku,
                    message=(
                        f"SKU {item.sku}: ordered {item.quantity} {declared_uom} (~{base_quantity:.0f} {base_uom}), "
                        f"only {product.stock} {base_uom} in stock."
                    ),
                )
            )

        # -------------------------------------------------------------
        # 3. Contract Pricing & Tiered Volume Discounts (Issue #72)
        # -------------------------------------------------------------
        expected_price = product.unit_price
        cust_agreement = agreements_map.get((order.customer.strip().upper(), item.sku.strip().upper()))
        if cust_agreement and item.quantity >= cust_agreement.min_quantity:
            discount_mult = Decimal("1") - (cust_agreement.discount_percent / Decimal("100"))
            expected_price = cust_agreement.contract_price * discount_mult

        if expected_price > 0:
            order_curr = (order.currency or "VND").upper()
            if order_curr != "VND":
                converted_price = Decimal(str(fx_engine.convert(item.unit_price, order_curr, "VND")))
                difference = abs(converted_price - expected_price)
                percent = (difference / expected_price) * Decimal("100")
                if percent > price_tolerance_percent:
                    findings.append(
                        Finding(
                            code="PRICE_MISMATCH",
                            severity="warning",
                            sku=item.sku,
                            message=(
                                f"SKU {item.sku}: PO price {item.unit_price:,.2f} {order_curr} "
                                f"(~{converted_price:,.0f} VND), target price {expected_price:,.0f} VND "
                                f"({percent:.2f}% difference at FX rate {fx_engine.get_rate(order_curr, 'VND'):,.2f})."
                            ),
                        )
                    )
            else:
                difference = abs(item.unit_price - expected_price)
                percent = (difference / expected_price) * Decimal("100")
                if percent > price_tolerance_percent:
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
    """Raised when an approval/rejection decision violates SOX 404/governance constraints."""

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

