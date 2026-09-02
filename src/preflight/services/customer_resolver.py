from __future__ import annotations

import re
import unicodedata
from typing import Any

from rapidfuzz import fuzz

from preflight.models import CustomerMaster, Finding
from preflight.utils.text import normalize_vietnamese_name

CUSTOMER_FUZZY_MATCHED = "CUSTOMER_FUZZY_MATCHED"
CUSTOMER_UNRESOLVED = "CUSTOMER_UNRESOLVED"


def resolve_customer(
    raw_name: str,
    tax_code: str | None = None,
    store: Any = None,
) -> tuple[CustomerMaster | None, Finding | None]:
    """Resolve customer entity from raw name or tax code with exact & fuzzy matching."""
    if not store:
        return None, None

    # 1. Exact lookup by Tax Code (MST) if present
    if tax_code and tax_code.strip():
        clean_tax = tax_code.strip().replace(" ", "").replace("-", "")
        cust = store.get_customer_by_tax_code(clean_tax)
        if cust:
            return cust, None

    norm_query = normalize_vietnamese_name(raw_name)
    if not norm_query:
        finding = Finding(
            code="CUSTOMER_UNRESOLVED",
            severity="error",
            message="Tên khách hàng trống hoặc không hợp lệ.",
            evidence={"raw_name": raw_name, "tax_code": tax_code, "reason": "empty_name"},
        )
        return None, finding

    # 2. Exact match on normalized_name or exact alias
    cust = store.get_customer_by_normalized_name(norm_query)
    if cust:
        return cust, None

    # 2b. Direct lookup by code/ID
    cust = store.get_customer(raw_name)
    if cust:
        return cust, None

    # 2c. Check credit or pricing profiles
    if hasattr(store, "get_customer_credit"):
        credit = store.get_customer_credit(raw_name)
        if credit:
            cust = store.get_customer(credit.customer_id) or store.get_customer_by_normalized_name(credit.customer_id)
            if cust:
                return cust, None
            new_cust = store.create_customer(CustomerMaster(
                code=credit.customer_id,
                name=raw_name,
                normalized_name=norm_query,
            ))
            return new_cust, None

    # 2d. Check historical order database
    if hasattr(store, "get_recent_customer_orders"):
        recent = store.get_recent_customer_orders(raw_name, days=365)
        if recent:
            new_cust = store.create_customer(CustomerMaster(
                code=f"CUST-{abs(hash(norm_query)) % 100000:05d}",
                name=raw_name,
                normalized_name=norm_query,
            ))
            return new_cust, None

    # 3. Fuzzy matching across all registered customers and aliases
    all_customers: list[CustomerMaster] = store.list_customers(limit=500)
    if not all_customers:
        finding = Finding(
            code="CUSTOMER_UNRESOLVED",
            severity="error",
            message=f"Hệ thống chưa có hồ sơ khách hàng. Không thể nhận diện '{raw_name}'.",
            evidence={"raw_name": raw_name, "tax_code": tax_code, "best_candidate": None, "best_score": 0},
        )
        return None, finding

    best_cust: CustomerMaster | None = None
    best_score: float = 0.0

    for c in all_customers:
        # Compare with customer normalized name
        score = fuzz.token_set_ratio(norm_query, c.normalized_name)
        if score > best_score:
            best_score = score
            best_cust = c
        
        # Compare with all aliases for this customer
        for alias in c.aliases:
            norm_alias = normalize_vietnamese_name(alias)
            a_score = fuzz.token_set_ratio(norm_query, norm_alias)
            if a_score > best_score:
                best_score = a_score
                best_cust = c

    # Fuzzy acceptance threshold: >= 90
    if best_cust and best_score >= 90.0:
        finding = Finding(
            code="CUSTOMER_FUZZY_MATCHED",
            severity="warning",
            message=f"Khách hàng '{raw_name}' được khớp gần đúng với '{best_cust.name}' (điểm tương đồng: {best_score:.0f}%).",
            evidence={
                "original_name": raw_name,
                "matched_name": best_cust.name,
                "customer_code": best_cust.code,
                "score": float(best_score),
            },
        )
        return best_cust, finding

    # Unresolved: score < 90
    finding = Finding(
        code="CUSTOMER_UNRESOLVED",
        severity="error",
        message=f"Không xác định được khách hàng '{raw_name}'. Cần xác nhận hoặc tạo hồ sơ khách hàng mới.",
        evidence={
            "raw_name": raw_name,
            "tax_code": tax_code,
            "best_candidate": best_cust.name if best_cust else None,
            "best_score": float(best_score),
        },
    )
    return None, finding
