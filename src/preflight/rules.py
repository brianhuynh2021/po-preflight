from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Mapping

from preflight.findings_registry import registry
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


def format_money(amount: Decimal | int | float, currency: str = "VND") -> str:
    """Format monetary amounts cleanly based on currency."""
    curr = (currency or "VND").upper().strip()
    if curr == "VND":
        return f"{amount:,.0f} VND"
    return f"{amount:,.2f} {curr}"


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
    """Pure rule evaluation engine v2.
    
    Given an order and an immutable RuleContext, deterministically evaluates:
    - Customer credit status & exposure limits (configurable policy & grace days)
    - Duplicate PO detection
    - Item quantity & price sanity
    - VAT tax rate legality (0%, 5%, 8%, 10%)
    - Discount policy thresholds
    - Promo item recognition & price mismatch skipping
    - Hybrid SKU recognition & active catalog status
    - Unit of Measure (UOM) conversions & MOQ/packaging validation
    - Warehouse stock availability with safety margin thresholds
    - Contract pricing with validity dates & tiered volume brackets
    - Multi-currency FX conversion and tolerance thresholding
    - Declared total mathematical discrepancy verification
    """
    order_currency = (order.currency or "VND").strip().upper()

    if isinstance(ctx, dict):
        fx_rates: dict[str, Decimal] = {}
        fx_source = "static"
        if order_currency != "VND":
            from preflight.currency import fx_engine
            rate_val, fx_source = fx_engine.get_rate_info(order_currency, "VND")
            fx_rates[f"{order_currency}_VND"] = rate_val

        order_date = order.order_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

        context = RuleContext(
            catalog=ctx,
            pricing_agreements=tuple(pricing_agreements or ()),
            uom_conversions=tuple(uom_conversions or ()),
            customer_credit=customer_credit,
            price_tolerance_percent=price_tolerance_percent,
            order_date=order_date,
            duplicate=duplicate,
            fx_rates=fx_rates,
            fx_source=fx_source,
        )
    else:
        context = ctx

    findings: list[Finding] = []
    catalog = context.catalog
    matcher = HybridSKUMatcher(catalog)
    order_date_str = context.order_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # -------------------------------------------------------------
    # 0. Duplicate & Revision PO Detection
    # -------------------------------------------------------------
    if context.revision_diff:
        findings.append(
            registry.make(
                code="REVISED_ORDER",
                severity="info",
                message=f"Đơn hàng được nộp lại theo phiên bản mới. Thay đổi: {context.revision_diff.get('summary', 'Đã cập nhật dữ liệu.')}",
                evidence={
                    "summary": context.revision_diff.get("summary", ""),
                    "changes": context.revision_diff.get("changes", []),
                    "old_total": str(context.revision_diff.get("old_total", "")),
                    "new_total": str(context.revision_diff.get("new_total", "")),
                    "rule_version": context.policy_version,
                },
            )
        )

    if context.duplicate:
        findings.append(
            registry.make(
                code="DUPLICATE_PO",
                severity="error",
                message=f"PO {order.po_number} has already been processed.",
                evidence={
                    "po_number": order.po_number,
                    "customer": order.customer,
                    "rule_version": context.policy_version,
                },
            )
        )
    elif context.recent_customer_orders:
        curr_items = {(it.sku.strip().upper(), it.quantity) for it in order.items}
        for cand in context.recent_customer_orders:
            if cand.po_number.strip().upper() == order.po_number.strip().upper():
                continue
            cand_items = {(it.sku.strip().upper(), it.quantity) for it in cand.items}
            union_len = len(curr_items | cand_items)
            if union_len == 0:
                continue
            jaccard = len(curr_items & cand_items) / union_len
            cand_tot = cand.grand_total if hasattr(cand, "grand_total") else cand.total
            curr_tot = order.grand_total
            tot_diff_ratio = abs(curr_tot - cand_tot) / max(Decimal("1"), cand_tot)
            if jaccard >= 0.9 and tot_diff_ratio < Decimal("0.01"):
                findings.append(
                    registry.make(
                        code="POSSIBLE_DUPLICATE",
                        severity="warning",
                        message=(
                            f"Nghi ngờ trùng lặp với đơn hàng {cand.po_number} "
                            f"(độ tương đồng dòng hàng {jaccard*100:.0f}%, chênh lệch tổng tiền {tot_diff_ratio*100:.1f}%)."
                        ),
                        evidence={
                            "matched_po": cand.po_number,
                            "jaccard_similarity": f"{jaccard*100:.0f}%",
                            "candidate_total": str(cand_tot),
                            "rule_version": context.policy_version,
                        },
                    )
                )
                break

    # -------------------------------------------------------------
    # 1. Customer Credit & Debt Risk Rules (Configurable Policy)
    # -------------------------------------------------------------
    customer_credit = context.customer_credit
    if customer_credit:
        if customer_credit.status == "BLOCKED":
            findings.append(
                registry.make(
                    code="CUSTOMER_BLOCKED",
                    severity="error",
                    message=f"Customer '{order.customer}' credit status is BLOCKED. Order intake suspended.",
                    evidence={
                        "credit_status": "BLOCKED",
                        "customer": order.customer,
                        "rule_version": context.policy_version,
                    },
                )
            )
        elif customer_credit.status == "ON_HOLD":
            hold_sev = "error" if context.credit_hold_behaviour == "block" else "warning"
            findings.append(
                registry.make(
                    code="CUSTOMER_ON_HOLD",
                    severity=hold_sev,
                    message=f"Customer '{order.customer}' credit status is ON_HOLD. Review required before release.",
                    evidence={
                        "credit_status": "ON_HOLD",
                        "hold_behaviour": context.credit_hold_behaviour,
                        "rule_version": context.policy_version,
                    },
                )
            )

        if customer_credit.overdue_balance > 0 and customer_credit.oldest_overdue_days > context.overdue_grace_days:
            findings.append(
                registry.make(
                    code="OVERDUE_DEBT_BLOCKED",
                    severity="error",
                    message=(
                        f"Customer '{order.customer}' has overdue debt of {format_money(customer_credit.overdue_balance, order_currency)} "
                        f"aged {customer_credit.oldest_overdue_days} days (exceeds {context.overdue_grace_days}-day grace limit)."
                    ),
                    evidence={
                        "overdue_balance": str(customer_credit.overdue_balance),
                        "oldest_overdue_days": customer_credit.oldest_overdue_days,
                        "grace_limit_days": context.overdue_grace_days,
                        "rule_version": context.policy_version,
                    },
                )
            )

        # Multi-currency exposure conversion if order is non-VND
        order_exposure_in_credit_curr = order.grand_total
        fx_note = ""
        if order_currency != "VND":
            fx_rate = context.fx_rates.get(f"{order_currency}_VND", Decimal("1"))
            if fx_rate > 0:
                order_exposure_in_credit_curr = order.grand_total * fx_rate
                fx_note = f" (~{format_money(order_exposure_in_credit_curr, 'VND')} at rate {fx_rate:,.2f})"

        total_exposure = customer_credit.outstanding_balance + order_exposure_in_credit_curr
        if total_exposure > customer_credit.credit_limit:
            deficit = total_exposure - customer_credit.credit_limit
            pct_over = (deficit / customer_credit.credit_limit) * Decimal("100") if customer_credit.credit_limit > 0 else Decimal("100")
            is_blocking = customer_credit.credit_limit == 0 or pct_over > context.credit_limit_block_percent
            findings.append(
                registry.make(
                    code="CREDIT_LIMIT_EXCEEDED",
                    severity="error" if is_blocking else "warning",
                    message=(
                        f"Order total {format_money(order.grand_total, order_currency)}{fx_note} pushes customer credit exposure to {format_money(total_exposure, 'VND')}, "
                        f"exceeding approved credit limit of {format_money(customer_credit.credit_limit, 'VND')} by {format_money(deficit, 'VND')}."
                    ),
                    evidence={
                        "credit_limit": str(customer_credit.credit_limit),
                        "total_exposure": str(total_exposure),
                        "deficit": str(deficit),
                        "block_threshold_percent": str(context.credit_limit_block_percent),
                        "rule_version": context.policy_version,
                    },
                )
            )

    # Group pricing agreements by (customer, sku)
    from preflight.rules_context import normalize_customer_key
    norm_order_cust = normalize_customer_key(order.customer)

    agreements_by_sku: dict[str, list[CustomerPriceAgreement]] = {}
    for pa in context.pricing_agreements:
        pa_cust_norm = normalize_customer_key(pa.customer_id)
        if pa.customer_id.strip().upper() == order.customer.strip().upper() or pa_cust_norm == norm_order_cust:
            sku_k = pa.sku.strip().upper()
            agreements_by_sku.setdefault(sku_k, []).append(pa)

    # UOM mapping
    uom_map: dict[tuple[str, str], Decimal] = {
        (u.sku.strip().upper(), u.uom_code.strip().upper()): u.conversion_factor
        for u in context.uom_conversions
    }

    VALID_TAX_RATES = {Decimal("0"), Decimal("5"), Decimal("8"), Decimal("10")}

    # -------------------------------------------------------------
    # 2. Line Item Rules & Validations
    # -------------------------------------------------------------
    for item in order.items:
        if item.quantity <= 0:
            findings.append(
                registry.make(
                    code="INVALID_QUANTITY",
                    severity="error",
                    sku=item.sku,
                    message=f"SKU {item.sku}: quantity must be positive (received {item.quantity}).",
                    evidence={
                        "received_quantity": item.quantity,
                        "expected_min": 1,
                        "rule_version": context.policy_version,
                    },
                )
            )
        if item.unit_price < 0:
            findings.append(
                registry.make(
                    code="INVALID_PRICE",
                    severity="error",
                    sku=item.sku,
                    message=f"SKU {item.sku}: unit price cannot be negative (received {item.unit_price}).",
                    evidence={
                        "received_price": str(item.unit_price),
                        "expected_min": "0",
                        "rule_version": context.policy_version,
                    },
                )
            )

        # Tax Rate Validation (VAT in Vietnam)
        if item.tax_rate not in VALID_TAX_RATES:
            findings.append(
                registry.make(
                    code="TAX_RATE_INVALID",
                    severity="error",
                    sku=item.sku,
                    message=f"SKU {item.sku}: Thuế suất VAT {item.tax_rate:g}% không hợp lệ theo quy định Việt Nam (chỉ chấp nhận 0%, 5%, 8%, 10%).",
                    evidence={
                        "received_tax_rate": str(item.tax_rate),
                        "valid_tax_rates": "0, 5, 8, 10",
                        "rule_version": context.policy_version,
                    },
                )
            )

        # Discount Policy Validation
        if item.discount_percent > context.max_discount_percent:
            findings.append(
                registry.make(
                    code="DISCOUNT_EXCEEDS_POLICY",
                    severity="warning",
                    sku=item.sku,
                    message=f"SKU {item.sku}: Mức chiết khấu {item.discount_percent:g}% vượt quá chính sách tối đa {context.max_discount_percent:g}%.",
                    evidence={
                        "discount_percent": str(item.discount_percent),
                        "policy_max_discount": str(context.max_discount_percent),
                        "rule_version": context.policy_version,
                    },
                )
            )

        product = catalog.get(item.sku)

        if product is None:
            resolution = matcher.resolve(item.sku, customer_id=order.customer)
            if resolution.is_confident and resolution.matched_sku:
                findings.append(
                    registry.make(
                        code="UNKNOWN_SKU",
                        severity="warning",
                        sku=item.sku,
                        message=(
                            f"SKU '{item.sku}' not found in catalog. "
                            f"AI suggested match: '{resolution.matched_sku}' ({resolution.name}) "
                            f"with {resolution.confidence_score*100:.0f}% confidence [{resolution.tier_used.value}]."
                        ),
                        evidence={
                            "po_sku": item.sku,
                            "suggested_sku": resolution.matched_sku,
                            "confidence": f"{resolution.confidence_score*100:.0f}%",
                            "resolution_tier": resolution.tier_used.value,
                            "rule_version": context.policy_version,
                        },
                    )
                )
            else:
                findings.append(
                    registry.make(
                        code="UNKNOWN_SKU",
                        severity="error",
                        sku=item.sku,
                        message=f"SKU {item.sku} does not exist in the catalog.",
                        evidence={
                            "po_sku": item.sku,
                            "status": "NOT_FOUND",
                            "rule_version": context.policy_version,
                        },
                    )
                )
            continue

        if not product.active:
            inactive_sev = "warning" if context.allow_inactive_sku else "error"
            findings.append(
                registry.make(
                    code="INACTIVE_SKU",
                    severity=inactive_sev,
                    sku=item.sku,
                    message=f"SKU {item.sku} is inactive.",
                    evidence={
                        "sku": item.sku,
                        "product_active": False,
                        "allow_inactive_policy": context.allow_inactive_sku,
                        "rule_version": context.policy_version,
                    },
                )
            )

        # -------------------------------------------------------------
        # UOM & MOQ / Pack Multiplier Rules
        # -------------------------------------------------------------
        declared_uom = (getattr(item, "uom", None) or "PCS").strip().upper()
        base_uom = (getattr(product, "base_uom", None) or "PCS").strip().upper()
        
        conversion_factor = Decimal("1.0")
        if declared_uom != base_uom:
            if (item.sku.upper(), declared_uom) in uom_map:
                conversion_factor = uom_map[(item.sku.upper(), declared_uom)]
            else:
                findings.append(
                    registry.make(
                        code="UOM_CONVERSION_MISSING",
                        severity="warning",
                        sku=item.sku,
                        message=(
                            f"SKU {item.sku}: ordered in '{declared_uom}' but catalog base UOM is '{base_uom}', "
                            f"and no conversion factor is configured."
                        ),
                        evidence={
                            "declared_uom": declared_uom,
                            "base_uom": base_uom,
                            "conversion_factor": "MISSING",
                            "rule_version": context.policy_version,
                        },
                    )
                )

        base_quantity = Decimal(str(item.quantity)) * conversion_factor
        moq = getattr(product, "moq", 1)
        pack_size = getattr(product, "pack_size", 1)

        if base_quantity < Decimal(str(moq)):
            findings.append(
                registry.make(
                    code="BELOW_MOQ",
                    severity="warning",
                    sku=item.sku,
                    message=(
                        f"SKU {item.sku}: ordered {item.quantity} {declared_uom} (~{base_quantity:.0f} {base_uom}) "
                        f"is below supplier Minimum Order Quantity (MOQ: {moq} {base_uom})."
                    ),
                    evidence={
                        "ordered_base_quantity": str(base_quantity),
                        "moq": str(moq),
                        "base_uom": base_uom,
                        "rule_version": context.policy_version,
                    },
                )
            )

        if pack_size > 1 and (base_quantity % Decimal(str(pack_size))) != 0:
            findings.append(
                registry.make(
                    code="INVALID_PACK_SIZE",
                    severity="warning",
                    sku=item.sku,
                    message=(
                        f"SKU {item.sku}: ordered quantity ({base_quantity:.0f} {base_uom}) is not a multiple "
                        f"of standard packaging pack size ({pack_size} {base_uom}/pack)."
                    ),
                    evidence={
                        "ordered_base_quantity": str(base_quantity),
                        "pack_size": str(pack_size),
                        "base_uom": base_uom,
                        "rule_version": context.policy_version,
                    },
                )
            )

        # Stock verification using available_stock
        avail_stock = context.available_stock(product)
        if int(base_quantity) > avail_stock:
            safety_note = f" (safety margin: {context.stock_safety_margin})" if context.stock_safety_margin > 0 else ""
            findings.append(
                registry.make(
                    code="INSUFFICIENT_STOCK",
                    severity="warning",
                    sku=item.sku,
                    message=(
                        f"SKU {item.sku}: ordered {item.quantity} {declared_uom} (~{base_quantity:.0f} {base_uom}), "
                        f"only {product.stock} {base_uom} in stock{safety_note}."
                    ),
                    evidence={
                        "ordered_quantity": str(item.quantity),
                        "available_stock": str(avail_stock),
                        "total_stock": str(product.stock),
                        "safety_margin": str(context.stock_safety_margin),
                        "uom": base_uom,
                        "rule_version": context.policy_version,
                    },
                )
            )

        # -------------------------------------------------------------
        # Promo Line Check vs Price Mismatch
        # -------------------------------------------------------------
        if getattr(item, "is_promo", False):
            findings.append(
                registry.make(
                    code="PROMO_LINE",
                    severity="info",
                    sku=item.sku,
                    message=f"SKU {item.sku}: Dòng hàng khuyến mãi / tặng kèm (đơn giá {format_money(item.unit_price, order_currency)}).",
                    evidence={
                        "unit_price": str(item.unit_price),
                        "is_promo": True,
                        "rule_version": context.policy_version,
                    },
                )
            )
            continue

        # -------------------------------------------------------------
        # Contract Pricing with Validity Period & Volume Tiers
        # -------------------------------------------------------------
        matching_agreements = agreements_by_sku.get(item.sku.strip().upper(), [])
        valid_agreements: list[CustomerPriceAgreement] = []
        expired_agreements: list[CustomerPriceAgreement] = []

        for agr in matching_agreements:
            is_valid_date = True
            if agr.valid_from and order_date_str < agr.valid_from:
                is_valid_date = False
            if agr.valid_to and order_date_str > agr.valid_to:
                is_valid_date = False

            if is_valid_date:
                valid_agreements.append(agr)
            else:
                expired_agreements.append(agr)

        if not valid_agreements and expired_agreements:
            exp_agr = expired_agreements[0]
            findings.append(
                registry.make(
                    code="CONTRACT_PRICE_EXPIRED",
                    severity="warning",
                    sku=item.sku,
                    message=(
                        f"SKU {item.sku}: Giá hợp đồng ({format_money(exp_agr.contract_price, 'VND')}) "
                        f"đã hết hiệu lực (hiệu lực: {exp_agr.valid_from or '—'} đến {exp_agr.valid_to or '—'}). "
                        f"Hệ thống sẽ đối chiếu theo giá Catalog chuẩn."
                    ),
                    evidence={
                        "contract_price": str(exp_agr.contract_price),
                        "valid_from": str(exp_agr.valid_from),
                        "valid_to": str(exp_agr.valid_to),
                        "order_date": order_date_str,
                        "rule_version": context.policy_version,
                    },
                )
            )

        # Select highest qualifying min_quantity tier among valid agreements
        selected_agreement: CustomerPriceAgreement | None = None
        qualifying = [agr for agr in valid_agreements if item.quantity >= agr.min_quantity]
        if qualifying:
            qualifying.sort(key=lambda x: x.min_quantity, reverse=True)
            selected_agreement = qualifying[0]

        expected_price = product.unit_price
        price_source = "catalog"
        if selected_agreement:
            discount_mult = Decimal("1") - (selected_agreement.discount_percent / Decimal("100"))
            expected_price = selected_agreement.contract_price * discount_mult
            price_source = f"contract_tier(min_qty={selected_agreement.min_quantity})"

        if declared_uom != base_uom and conversion_factor > Decimal("0"):
            expected_price = expected_price * conversion_factor

        if expected_price > 0:
            if order_currency != "VND":
                fx_key = f"{order_currency}_VND"
                fx_rate = context.fx_rates.get(fx_key)
                if fx_rate is None or fx_rate <= Decimal("0"):
                    findings.append(
                        registry.make(
                            code="FX_RATE_UNAVAILABLE",
                            severity="error",
                            sku=item.sku,
                            message=f"Tỷ giá cho cặp tiền {order_currency}/VND không khả dụng.",
                            evidence={
                                "order_currency": order_currency,
                                "target_currency": "VND",
                                "rule_version": context.policy_version,
                            },
                        )
                    )
                else:
                    converted_price = Decimal(str(item.unit_price)) * fx_rate
                    difference = abs(converted_price - expected_price)
                    percent = (difference / expected_price) * Decimal("100")
                    if percent > context.price_tolerance_percent:
                        source_note = " (tỷ giá tĩnh)" if context.fx_source == "static" else ""
                        findings.append(
                            registry.make(
                                code="PRICE_MISMATCH",
                                severity="warning",
                                sku=item.sku,
                                message=(
                                    f"SKU {item.sku}: PO price {format_money(item.unit_price, order_currency)} "
                                    f"(~{format_money(converted_price, 'VND')}), target price {format_money(expected_price, 'VND')} "
                                    f"({percent:.2f}% difference at FX rate {fx_rate:,.2f}{source_note})."
                                ),
                                evidence={
                                    "po_price": str(item.unit_price),
                                    "converted_price_vnd": str(converted_price),
                                    "expected_price": str(expected_price),
                                    "fx_rate": str(fx_rate),
                                    "source": price_source,
                                    "tolerance_percent": str(context.price_tolerance_percent),
                                    "rule_version": context.policy_version,
                                },
                            )
                        )
            else:
                difference = abs(item.unit_price - expected_price)
                percent = (difference / expected_price) * Decimal("100")
                if percent > context.price_tolerance_percent:
                    findings.append(
                        registry.make(
                            code="PRICE_MISMATCH",
                            severity="warning",
                            sku=item.sku,
                            message=(
                                f"SKU {item.sku}: PO price {format_money(item.unit_price, 'VND')}, "
                                f"target price {format_money(expected_price, 'VND')} ({percent:.2f}% difference)."
                            ),
                            evidence={
                                "po_price": str(item.unit_price),
                                "expected_price": str(expected_price),
                                "source": price_source,
                                "tolerance_percent": str(context.price_tolerance_percent),
                                "rule_version": context.policy_version,
                            },
                        )
                    )

    # -------------------------------------------------------------
    # 3. Declared Total Verification vs Computed Total
    # -------------------------------------------------------------
    if order.declared_total is not None:
        diff = abs(order.declared_total - order.grand_total)
        min_abs_tol = Decimal("1000") if order_currency == "VND" else Decimal("0.05")
        rel_tol = order.grand_total * Decimal("0.005")
        tolerance = max(min_abs_tol, rel_tol)

        rounded_sum = sum((round(it.line_total) for it in order.items), start=Decimal("0"))
        is_rounding = (abs(rounded_sum - order.declared_total) <= min_abs_tol) and (diff <= order.grand_total * Decimal("0.01"))

        if diff > tolerance and not is_rounding:
            findings.append(
                registry.make(
                    code="TOTAL_MISMATCH",
                    severity="warning",
                    message=(
                        f"Tổng tiền khai báo ({format_money(order.declared_total, order_currency)}) "
                        f"lệch so với tổng tiền tính toán ({format_money(order.grand_total, order_currency)}) "
                        f"chênh lệch {format_money(diff, order_currency)}."
                    ),
                    evidence={
                        "declared_total": str(order.declared_total),
                        "computed_grand_total": str(order.grand_total),
                        "difference": str(diff),
                        "tolerance": str(tolerance),
                        "rule_version": context.policy_version,
                    },
                )
            )

    if any(f.severity == "error" for f in findings):
        status = "blocked"
    elif any(f.severity == "warning" for f in findings):
        status = "review_required"
    else:
        status = "ready_for_approval"

    now_iso = datetime.now(timezone.utc).isoformat()
    return Analysis(
        order=order,
        findings=findings,
        status=status,
        policy_version=context.policy_version,
        catalog_snapshot_at=now_iso,
    )


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
