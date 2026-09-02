from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from preflight.models import Finding

CategoryType = Literal["catalog", "price", "stock", "credit", "document", "duplicate", "fx"]
SeverityType = Literal["info", "warning", "error"]


@dataclass(frozen=True)
class FindingSpec:
    code: str
    default_severity: SeverityType
    title_vi: str
    description_vi: str
    category: CategoryType


FINDING_SPECS: list[FindingSpec] = [
    FindingSpec(
        code="DUPLICATE_PO",
        default_severity="error",
        title_vi="Trùng lặp mã đơn hàng",
        description_vi="Mã số PO đã tồn tại và đã được xử lý trước đó trong hệ thống.",
        category="duplicate",
    ),
    FindingSpec(
        code="CUSTOMER_BLOCKED",
        default_severity="error",
        title_vi="Khách hàng bị khóa tài khoản",
        description_vi="Hồ sơ tín dụng khách hàng đang ở trạng thái Bị chặn, tạm ngưng tiếp nhận đơn.",
        category="credit",
    ),
    FindingSpec(
        code="CUSTOMER_ON_HOLD",
        default_severity="warning",
        title_vi="Khách hàng đang tạm giữ tín dụng",
        description_vi="Khách hàng đang trong trạng thái tạm giữ công nợ (ON_HOLD), cần quản lý xem xét.",
        category="credit",
    ),
    FindingSpec(
        code="CUSTOMER_FUZZY_MATCHED",
        default_severity="warning",
        title_vi="Khớp khách hàng gần đúng",
        description_vi="Tên khách hàng trên PO được nhận diện theo thuật toán so khớp gần đúng (fuzzy match).",
        category="customer",
    ),
    FindingSpec(
        code="CUSTOMER_UNRESOLVED",
        default_severity="error",
        title_vi="Không xác định được khách hàng",
        description_vi="Tên khách hàng hoặc mã số thuế trên PO không khớp với hồ sơ khách hàng nào trong hệ thống.",
        category="customer",
    ),
    FindingSpec(
        code="OVERDUE_DEBT_BLOCKED",
        default_severity="error",
        title_vi="Nợ quá hạn vượt giới hạn cho phép",
        description_vi="Khách hàng có nợ quá hạn vượt quá số ngày ân hạn theo chính sách.",
        category="credit",
    ),
    FindingSpec(
        code="CREDIT_LIMIT_EXCEEDED",
        default_severity="warning",
        title_vi="Vượt hạn mức tín dụng công nợ",
        description_vi="Giá trị đơn hàng khiến tổng dư nợ vượt quá hạn mức tín dụng được duyệt.",
        category="credit",
    ),
    FindingSpec(
        code="INVALID_QUANTITY",
        default_severity="error",
        title_vi="Số lượng không hợp lệ",
        description_vi="Số lượng đặt hàng phải lớn hơn 0.",
        category="document",
    ),
    FindingSpec(
        code="INVALID_PRICE",
        default_severity="error",
        title_vi="Đơn giá không hợp lệ",
        description_vi="Đơn giá trên dòng hàng không thể là số âm.",
        category="price",
    ),
    FindingSpec(
        code="TAX_RATE_INVALID",
        default_severity="error",
        title_vi="Thuế suất VAT không hợp lệ",
        description_vi="Thuế suất VAT không thuộc các mức thuế suất hợp lệ theo quy định Việt Nam (0%, 5%, 8%, 10%).",
        category="price",
    ),
    FindingSpec(
        code="DISCOUNT_EXCEEDS_POLICY",
        default_severity="warning",
        title_vi="Chiết khấu vượt chính sách quy định",
        description_vi="Mức chiết khấu trên dòng hàng vượt quá trần chiết khấu tối đa của chính sách.",
        category="price",
    ),
    FindingSpec(
        code="PROMO_LINE",
        default_severity="info",
        title_vi="Dòng hàng khuyến mãi / tặng kèm",
        description_vi="Sản phẩm tặng kèm hoặc khuyến mãi giá 0 đồng theo chương trình.",
        category="price",
    ),
    FindingSpec(
        code="UNKNOWN_SKU",
        default_severity="error",
        title_vi="Mã SKU không tồn tại trong danh mục",
        description_vi="Mã sản phẩm trên PO không tìm thấy trong Master Data bảng giá.",
        category="catalog",
    ),
    FindingSpec(
        code="INACTIVE_SKU",
        default_severity="error",
        title_vi="Sản phẩm đã ngừng kinh doanh",
        description_vi="Sản phẩm đã bị vô hiệu hóa hoặc dừng bán trong hệ thống.",
        category="catalog",
    ),
    FindingSpec(
        code="UOM_CONVERSION_MISSING",
        default_severity="warning",
        title_vi="Thiếu cấu hình quy đổi đơn vị (UOM)",
        description_vi="Đơn vị tính trên PO khác đơn vị cơ sở và chưa có hệ số quy đổi trong hệ thống.",
        category="catalog",
    ),
    FindingSpec(
        code="BELOW_MOQ",
        default_severity="warning",
        title_vi="Số lượng đặt dưới mức tối thiểu (MOQ)",
        description_vi="Số lượng đặt hàng chưa đạt mức đặt hàng tối thiểu quy định cho sản phẩm.",
        category="stock",
    ),
    FindingSpec(
        code="INVALID_PACK_SIZE",
        default_severity="warning",
        title_vi="Số lượng đặt không đúng quy cách đóng gói",
        description_vi="Số lượng đặt không phải là bội số của quy cách đóng thùng/hộp chuẩn.",
        category="stock",
    ),
    FindingSpec(
        code="INSUFFICIENT_STOCK",
        default_severity="warning",
        title_vi="Không đủ tồn kho đáp ứng (ATP)",
        description_vi="Tồn kho khả dụng (Available to Promise) không đủ đáp ứng số lượng đặt sau khi trừ giữ chỗ và phân bổ nội bộ.",
        category="stock",
    ),
    FindingSpec(
        code="INVENTORY_STALE",
        default_severity="warning",
        title_vi="Dữ liệu tồn kho ERP bị cũ",
        description_vi="Thời gian đồng bộ tồn kho từ ERP đã vượt quá ngưỡng quy định trong chính sách, cần đồng bộ lại.",
        category="stock",
    ),
    FindingSpec(
        code="CONTRACT_PRICE_EXPIRED",
        default_severity="warning",
        title_vi="Giá hợp đồng đã hết hiệu lực",
        description_vi="Thỏa thuận giá theo hợp đồng đã hết hạn so với ngày đơn hàng.",
        category="price",
    ),
    FindingSpec(
        code="PRICE_MISMATCH",
        default_severity="warning",
        title_vi="Chênh lệch giá so với Catalog",
        description_vi="Đơn giá trên PO có sai lệch vượt ngưỡng dung sai so với giá kỳ vọng.",
        category="price",
    ),
    FindingSpec(
        code="FX_RATE_UNAVAILABLE",
        default_severity="error",
        title_vi="Tỷ giá ngoại tệ không khả dụng",
        description_vi="Không tìm thấy tỷ giá quy đổi cho đơn vị tiền tệ ngoại tệ của đơn hàng.",
        category="fx",
    ),
    FindingSpec(
        code="TOTAL_MISMATCH",
        default_severity="warning",
        title_vi="Lệch tổng tiền khai báo và tính toán",
        description_vi="Tổng tiền ghi trên tài liệu lệch so với tổng tiền tính toán từ các dòng hàng.",
        category="document",
    ),
    FindingSpec(
        code="REVISED_ORDER",
        default_severity="info",
        title_vi="Đơn hàng bản điều chỉnh / tái nộp",
        description_vi="Đơn hàng được gửi lại sau khi yêu cầu chỉnh sửa, thay thế phiên bản trước đó.",
        category="document",
    ),
    FindingSpec(
        code="POSSIBLE_DUPLICATE",
        default_severity="warning",
        title_vi="Nghi ngờ đơn hàng bị gửi trùng lặp",
        description_vi="Phát hiện đơn hàng có nội dung tương tự gần đây từ cùng một khách hàng.",
        category="duplicate",
    ),
]

_REGISTRY_MAP: dict[str, FindingSpec] = {spec.code: spec for spec in FINDING_SPECS}


class FindingsRegistry:
    """Central registry & factory for all domain findings in PO Preflight."""

    @classmethod
    def get(cls, code: str) -> FindingSpec | None:
        return _REGISTRY_MAP.get(code)

    @classmethod
    def make(
        cls,
        code: str,
        message: str,
        *,
        severity: SeverityType | None = None,
        sku: str | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> Finding:
        spec = _REGISTRY_MAP.get(code)
        eff_severity = severity or (spec.default_severity if spec else "warning")
        
        # Ensure structured evidence has at least 2 keys for explainability
        eff_evidence = evidence or {}
        if "rule_version" not in eff_evidence:
            eff_evidence = {**eff_evidence, "rule_version": "2.0"}
        if "code" not in eff_evidence:
            eff_evidence = {**eff_evidence, "code": code}

        return Finding(
            code=code,
            severity=eff_severity,
            message=message,
            sku=sku,
            evidence=eff_evidence,
        )


registry = FindingsRegistry
