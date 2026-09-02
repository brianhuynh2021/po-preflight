/**
 * Auto-generated from src/preflight/findings_registry.py.
 * DO NOT EDIT MANUALLY. Run `python scripts/gen_findings_ts.py` to regenerate.
 */

export type FindingCode =
  | "DUPLICATE_PO"
  | "CUSTOMER_BLOCKED"
  | "CUSTOMER_ON_HOLD"
  | "OVERDUE_DEBT_BLOCKED"
  | "CREDIT_LIMIT_EXCEEDED"
  | "INVALID_QUANTITY"
  | "INVALID_PRICE"
  | "TAX_RATE_INVALID"
  | "DISCOUNT_EXCEEDS_POLICY"
  | "PROMO_LINE"
  | "UNKNOWN_SKU"
  | "INACTIVE_SKU"
  | "UOM_CONVERSION_MISSING"
  | "BELOW_MOQ"
  | "INVALID_PACK_SIZE"
  | "INSUFFICIENT_STOCK"
  | "CONTRACT_PRICE_EXPIRED"
  | "PRICE_MISMATCH"
  | "FX_RATE_UNAVAILABLE"
  | "TOTAL_MISMATCH"
  | "REVISED_ORDER"
  | "POSSIBLE_DUPLICATE";

export type FindingSeverity = "Info" | "Warning" | "Error";

export type FindingCategory = "catalog" | "price" | "stock" | "credit" | "document" | "duplicate" | "fx";

export interface FindingMetadata {
  code: FindingCode;
  defaultSeverity: FindingSeverity;
  titleVi: string;
  descriptionVi: string;
  category: FindingCategory;
}

export const FINDINGS_REGISTRY: Record<FindingCode, FindingMetadata> = {
  "DUPLICATE_PO": {
    code: "DUPLICATE_PO",
    defaultSeverity: "Error",
    titleVi: 'Trùng lặp mã đơn hàng',
    descriptionVi: 'Mã số PO đã tồn tại và đã được xử lý trước đó trong hệ thống.',
    category: "duplicate",
  },
  "CUSTOMER_BLOCKED": {
    code: "CUSTOMER_BLOCKED",
    defaultSeverity: "Error",
    titleVi: 'Khách hàng bị khóa tài khoản',
    descriptionVi: 'Hồ sơ tín dụng khách hàng đang ở trạng thái Bị chặn, tạm ngưng tiếp nhận đơn.',
    category: "credit",
  },
  "CUSTOMER_ON_HOLD": {
    code: "CUSTOMER_ON_HOLD",
    defaultSeverity: "Warning",
    titleVi: 'Khách hàng đang tạm giữ tín dụng',
    descriptionVi: 'Khách hàng đang trong trạng thái tạm giữ công nợ (ON_HOLD), cần quản lý xem xét.',
    category: "credit",
  },
  "OVERDUE_DEBT_BLOCKED": {
    code: "OVERDUE_DEBT_BLOCKED",
    defaultSeverity: "Error",
    titleVi: 'Nợ quá hạn vượt giới hạn cho phép',
    descriptionVi: 'Khách hàng có nợ quá hạn vượt quá số ngày ân hạn theo chính sách.',
    category: "credit",
  },
  "CREDIT_LIMIT_EXCEEDED": {
    code: "CREDIT_LIMIT_EXCEEDED",
    defaultSeverity: "Warning",
    titleVi: 'Vượt hạn mức tín dụng công nợ',
    descriptionVi: 'Giá trị đơn hàng khiến tổng dư nợ vượt quá hạn mức tín dụng được duyệt.',
    category: "credit",
  },
  "INVALID_QUANTITY": {
    code: "INVALID_QUANTITY",
    defaultSeverity: "Error",
    titleVi: 'Số lượng không hợp lệ',
    descriptionVi: 'Số lượng đặt hàng phải lớn hơn 0.',
    category: "document",
  },
  "INVALID_PRICE": {
    code: "INVALID_PRICE",
    defaultSeverity: "Error",
    titleVi: 'Đơn giá không hợp lệ',
    descriptionVi: 'Đơn giá trên dòng hàng không thể là số âm.',
    category: "price",
  },
  "TAX_RATE_INVALID": {
    code: "TAX_RATE_INVALID",
    defaultSeverity: "Error",
    titleVi: 'Thuế suất VAT không hợp lệ',
    descriptionVi: 'Thuế suất VAT không thuộc các mức thuế suất hợp lệ theo quy định Việt Nam (0%, 5%, 8%, 10%).',
    category: "price",
  },
  "DISCOUNT_EXCEEDS_POLICY": {
    code: "DISCOUNT_EXCEEDS_POLICY",
    defaultSeverity: "Warning",
    titleVi: 'Chiết khấu vượt chính sách quy định',
    descriptionVi: 'Mức chiết khấu trên dòng hàng vượt quá trần chiết khấu tối đa của chính sách.',
    category: "price",
  },
  "PROMO_LINE": {
    code: "PROMO_LINE",
    defaultSeverity: "Info",
    titleVi: 'Dòng hàng khuyến mãi / tặng kèm',
    descriptionVi: 'Sản phẩm tặng kèm hoặc khuyến mãi giá 0 đồng theo chương trình.',
    category: "price",
  },
  "UNKNOWN_SKU": {
    code: "UNKNOWN_SKU",
    defaultSeverity: "Error",
    titleVi: 'Mã SKU không tồn tại trong danh mục',
    descriptionVi: 'Mã sản phẩm trên PO không tìm thấy trong Master Data bảng giá.',
    category: "catalog",
  },
  "INACTIVE_SKU": {
    code: "INACTIVE_SKU",
    defaultSeverity: "Error",
    titleVi: 'Sản phẩm đã ngừng kinh doanh',
    descriptionVi: 'Sản phẩm đã bị vô hiệu hóa hoặc dừng bán trong hệ thống.',
    category: "catalog",
  },
  "UOM_CONVERSION_MISSING": {
    code: "UOM_CONVERSION_MISSING",
    defaultSeverity: "Warning",
    titleVi: 'Thiếu cấu hình quy đổi đơn vị (UOM)',
    descriptionVi: 'Đơn vị tính trên PO khác đơn vị cơ sở và chưa có hệ số quy đổi trong hệ thống.',
    category: "catalog",
  },
  "BELOW_MOQ": {
    code: "BELOW_MOQ",
    defaultSeverity: "Warning",
    titleVi: 'Số lượng đặt dưới mức tối thiểu (MOQ)',
    descriptionVi: 'Số lượng đặt hàng chưa đạt mức đặt hàng tối thiểu quy định cho sản phẩm.',
    category: "stock",
  },
  "INVALID_PACK_SIZE": {
    code: "INVALID_PACK_SIZE",
    defaultSeverity: "Warning",
    titleVi: 'Số lượng đặt không đúng quy cách đóng gói',
    descriptionVi: 'Số lượng đặt không phải là bội số của quy cách đóng thùng/hộp chuẩn.',
    category: "stock",
  },
  "INSUFFICIENT_STOCK": {
    code: "INSUFFICIENT_STOCK",
    defaultSeverity: "Warning",
    titleVi: 'Không đủ tồn kho đáp ứng',
    descriptionVi: 'Tồn kho khả dụng trong kho không đủ đáp ứng số lượng đặt hàng.',
    category: "stock",
  },
  "CONTRACT_PRICE_EXPIRED": {
    code: "CONTRACT_PRICE_EXPIRED",
    defaultSeverity: "Warning",
    titleVi: 'Giá hợp đồng đã hết hiệu lực',
    descriptionVi: 'Thỏa thuận giá theo hợp đồng đã hết hạn so với ngày đơn hàng.',
    category: "price",
  },
  "PRICE_MISMATCH": {
    code: "PRICE_MISMATCH",
    defaultSeverity: "Warning",
    titleVi: 'Chênh lệch giá so với Catalog',
    descriptionVi: 'Đơn giá trên PO có sai lệch vượt ngưỡng dung sai so với giá kỳ vọng.',
    category: "price",
  },
  "FX_RATE_UNAVAILABLE": {
    code: "FX_RATE_UNAVAILABLE",
    defaultSeverity: "Error",
    titleVi: 'Tỷ giá ngoại tệ không khả dụng',
    descriptionVi: 'Không tìm thấy tỷ giá quy đổi cho đơn vị tiền tệ ngoại tệ của đơn hàng.',
    category: "fx",
  },
  "TOTAL_MISMATCH": {
    code: "TOTAL_MISMATCH",
    defaultSeverity: "Warning",
    titleVi: 'Lệch tổng tiền khai báo và tính toán',
    descriptionVi: 'Tổng tiền ghi trên tài liệu lệch so với tổng tiền tính toán từ các dòng hàng.',
    category: "document",
  },
  "REVISED_ORDER": {
    code: "REVISED_ORDER",
    defaultSeverity: "Info",
    titleVi: 'Đơn hàng bản điều chỉnh / tái nộp',
    descriptionVi: 'Đơn hàng được gửi lại sau khi yêu cầu chỉnh sửa, thay thế phiên bản trước đó.',
    category: "document",
  },
  "POSSIBLE_DUPLICATE": {
    code: "POSSIBLE_DUPLICATE",
    defaultSeverity: "Warning",
    titleVi: 'Nghi ngờ đơn hàng bị gửi trùng lặp',
    descriptionVi: 'Phát hiện đơn hàng có nội dung tương tự gần đây từ cùng một khách hàng.',
    category: "duplicate",
  },
};

export const FINDING_TITLE: Record<FindingCode, string> = {
  "DUPLICATE_PO": 'Trùng lặp mã đơn hàng',
  "CUSTOMER_BLOCKED": 'Khách hàng bị khóa tài khoản',
  "CUSTOMER_ON_HOLD": 'Khách hàng đang tạm giữ tín dụng',
  "OVERDUE_DEBT_BLOCKED": 'Nợ quá hạn vượt giới hạn cho phép',
  "CREDIT_LIMIT_EXCEEDED": 'Vượt hạn mức tín dụng công nợ',
  "INVALID_QUANTITY": 'Số lượng không hợp lệ',
  "INVALID_PRICE": 'Đơn giá không hợp lệ',
  "TAX_RATE_INVALID": 'Thuế suất VAT không hợp lệ',
  "DISCOUNT_EXCEEDS_POLICY": 'Chiết khấu vượt chính sách quy định',
  "PROMO_LINE": 'Dòng hàng khuyến mãi / tặng kèm',
  "UNKNOWN_SKU": 'Mã SKU không tồn tại trong danh mục',
  "INACTIVE_SKU": 'Sản phẩm đã ngừng kinh doanh',
  "UOM_CONVERSION_MISSING": 'Thiếu cấu hình quy đổi đơn vị (UOM)',
  "BELOW_MOQ": 'Số lượng đặt dưới mức tối thiểu (MOQ)',
  "INVALID_PACK_SIZE": 'Số lượng đặt không đúng quy cách đóng gói',
  "INSUFFICIENT_STOCK": 'Không đủ tồn kho đáp ứng',
  "CONTRACT_PRICE_EXPIRED": 'Giá hợp đồng đã hết hiệu lực',
  "PRICE_MISMATCH": 'Chênh lệch giá so với Catalog',
  "FX_RATE_UNAVAILABLE": 'Tỷ giá ngoại tệ không khả dụng',
  "TOTAL_MISMATCH": 'Lệch tổng tiền khai báo và tính toán',
  "REVISED_ORDER": 'Đơn hàng bản điều chỉnh / tái nộp',
  "POSSIBLE_DUPLICATE": 'Nghi ngờ đơn hàng bị gửi trùng lặp',
};

export const SEVERITY_BY_CODE: Record<FindingCode, FindingSeverity> = {
  "DUPLICATE_PO": "Error",
  "CUSTOMER_BLOCKED": "Error",
  "CUSTOMER_ON_HOLD": "Warning",
  "OVERDUE_DEBT_BLOCKED": "Error",
  "CREDIT_LIMIT_EXCEEDED": "Warning",
  "INVALID_QUANTITY": "Error",
  "INVALID_PRICE": "Error",
  "TAX_RATE_INVALID": "Error",
  "DISCOUNT_EXCEEDS_POLICY": "Warning",
  "PROMO_LINE": "Info",
  "UNKNOWN_SKU": "Error",
  "INACTIVE_SKU": "Error",
  "UOM_CONVERSION_MISSING": "Warning",
  "BELOW_MOQ": "Warning",
  "INVALID_PACK_SIZE": "Warning",
  "INSUFFICIENT_STOCK": "Warning",
  "CONTRACT_PRICE_EXPIRED": "Warning",
  "PRICE_MISMATCH": "Warning",
  "FX_RATE_UNAVAILABLE": "Error",
  "TOTAL_MISMATCH": "Warning",
  "REVISED_ORDER": "Info",
  "POSSIBLE_DUPLICATE": "Warning",
};
