from __future__ import annotations

from decimal import Decimal

from preflight.currency import fx_engine
from preflight.models import Analysis, Finding, Order, Product
from preflight.rag.matcher import HybridSKUMatcher


def analyze_order(
    order: Order,
    catalog: dict[str, Product],
    *,
    duplicate: bool = False,
    price_tolerance_percent: Decimal = Decimal("0"),
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

    for item in order.items:
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
        if item.quantity > product.stock:
            findings.append(
                Finding(
                    code="INSUFFICIENT_STOCK",
                    severity="warning",
                    sku=item.sku,
                    message=(
                        f"SKU {item.sku}: ordered {item.quantity}, only {product.stock} in stock."
                    ),
                )
            )
        if product.unit_price > 0:
            order_curr = (order.currency or "VND").upper()
            if order_curr != "VND":
                converted_price = Decimal(str(fx_engine.convert(item.unit_price, order_curr, "VND")))
                difference = abs(converted_price - product.unit_price)
                percent = (difference / product.unit_price) * Decimal("100")
                if percent > price_tolerance_percent:
                    findings.append(
                        Finding(
                            code="PRICE_MISMATCH",
                            severity="warning",
                            sku=item.sku,
                            message=(
                                f"SKU {item.sku}: PO price {item.unit_price:,.2f} {order_curr} "
                                f"(~{converted_price:,.0f} VND), catalog price {product.unit_price:,.0f} VND "
                                f"({percent:.2f}% difference at FX rate {fx_engine.get_rate(order_curr, 'VND'):,.2f})."
                            ),
                        )
                    )
            else:
                difference = abs(item.unit_price - product.unit_price)
                percent = (difference / product.unit_price) * Decimal("100")
                if percent > price_tolerance_percent:
                    findings.append(
                        Finding(
                            code="PRICE_MISMATCH",
                            severity="warning",
                            sku=item.sku,
                            message=(
                                f"SKU {item.sku}: PO price {item.unit_price:,.0f}, "
                                f"catalog price {product.unit_price:,.0f} "
                                f"({percent:.2f}% difference)."
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
