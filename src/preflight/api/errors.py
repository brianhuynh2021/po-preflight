from __future__ import annotations

from typing import Any, Sequence


class PreflightError(Exception):
    """Base domain and HTTP exception conforming to RFC 7807 Problem Details."""

    status_code: int = 500
    code: str = "INTERNAL_ERROR"
    title: str = "Internal Server Error"
    message_vi: str = "Lỗi hệ thống nội bộ."

    def __init__(
        self,
        message_vi: str | None = None,
        *,
        detail: Any = None,
        errors: Sequence[dict[str, Any]] | None = None,
        status_code: int | None = None,
        code: str | None = None,
        title: str | None = None,
    ):
        msg = message_vi or self.message_vi
        super().__init__(msg)
        self.message_vi = msg
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code
        if title is not None:
            self.title = title
        self.detail = detail or self.message_vi
        self.errors = list(errors) if errors else None

    def to_problem_dict(self, request_id: str | None = None) -> dict[str, Any]:
        doc: dict[str, Any] = {
            "type": f"https://popreflight.vn/errors/{self.code.lower()}",
            "title": self.title,
            "status": self.status_code,
            "code": self.code,
            "detail": self.message_vi,
            "request_id": request_id or "",
        }
        if self.errors:
            doc["errors"] = self.errors
        elif isinstance(self.detail, dict):
            doc["detail_info"] = self.detail
        return doc


class ParseError(PreflightError):
    status_code = 400
    code = "PARSE_ERROR"
    title = "Bad Request - Parse Error"
    message_vi = "Không thể đọc hoặc phân tích dữ liệu đơn hàng."


class UnsupportedFormat(PreflightError):
    status_code = 415
    code = "UNSUPPORTED_FORMAT"
    title = "Unsupported Media Type"
    message_vi = "Định dạng tệp không được hỗ trợ. Vui lòng tải lên tệp PDF, JSON, PNG hoặc JPG."


class PayloadTooLarge(PreflightError):
    status_code = 413
    code = "PAYLOAD_TOO_LARGE"
    title = "Payload Too Large"
    message_vi = "Kích thước tệp vượt quá giới hạn cho phép (tối đa 10MB)."


class NotFound(PreflightError):
    status_code = 404
    code = "NOT_FOUND"
    title = "Resource Not Found"
    message_vi = "Không tìm thấy tài nguyên yêu cầu."


class DecisionConflict(PreflightError):
    status_code = 409
    code = "DECISION_CONFLICT"
    title = "Decision Conflict"
    message_vi = "Xung đột trạng thái quyết định đơn hàng."


class ValidationFailed(PreflightError):
    status_code = 422
    code = "VALIDATION_FAILED"
    title = "Unprocessable Entity"
    message_vi = "Dữ liệu yêu cầu không hợp lệ."


class Forbidden(PreflightError):
    status_code = 403
    code = "FORBIDDEN"
    title = "Forbidden"
    message_vi = "Bạn không có quyền thực hiện hành động này."


class Unauthorized(PreflightError):
    status_code = 401
    code = "UNAUTHORIZED"
    title = "Unauthorized"
    message_vi = "Yêu cầu xác thực hợp lệ để truy cập hệ thống."


class RateLimited(PreflightError):
    status_code = 429
    code = "RATE_LIMITED"
    title = "Too Many Requests"
    message_vi = "Vượt quá giới hạn tần suất yêu cầu. Vui lòng thử lại sau."


class UpstreamUnavailable(PreflightError):
    status_code = 503
    code = "UPSTREAM_UNAVAILABLE"
    title = "Service Unavailable"
    message_vi = "Dịch vụ liên kết tạm thời không khả dụng."


class ConfigurationError(PreflightError):
    status_code = 500
    code = "CONFIGURATION_ERROR"
    title = "Configuration Error"
    message_vi = "Lỗi cấu hình hệ thống."


class InternalError(PreflightError):
    status_code = 500
    code = "INTERNAL_ERROR"
    title = "Internal Server Error"
    message_vi = "Lỗi hệ thống nội bộ."
