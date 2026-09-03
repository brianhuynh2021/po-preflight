"use client";

import { useEffect, useRef, useState } from "react";
import type { DecisionType, PurchaseOrder } from "@/app/lib/types";
import {
  MIN_NOTE_LENGTH,
  canDecide,
  decisionBlockedReason,
  isNoteRequired,
  validateNote,
} from "@/app/lib/derive";
import { useAppState } from "@/components/app/AppStateProvider";
import { AlertCircle, CheckCircle2, FileQuestion, XCircle } from "lucide-react";

export function DecisionModal({
  order,
  initialAction = "APPROVE",
  note,
  onNoteChange,
  onClose,
  onConfirm,
}: {
  order: PurchaseOrder;
  initialAction?: DecisionType;
  note: string;
  onNoteChange: (value: string) => void;
  onClose: () => void;
  onConfirm: (action: DecisionType) => void;
}) {
  const [action, setAction] = useState<DecisionType>(initialAction);
  const { user } = useAppState();
  const modalRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
      if (e.key === "Tab" && modalRef.current) {
        const focusables = modalRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusables.length > 0) {
          const first = focusables[0];
          const last = focusables[focusables.length - 1];
          if (e.shiftKey && document.activeElement === first) {
            e.preventDefault();
            last.focus();
          } else if (!e.shiftKey && document.activeElement === last) {
            e.preventDefault();
            first.focus();
          }
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const errorCount = order.findings.filter((f) => f.severity === "Error").length;
  const isAllowed = canDecide(order.status, action);
  const blockedReason = decisionBlockedReason(order.status, action, errorCount);
  const noteError = validateNote(order.status, action, note);
  const noteRequired = isNoteRequired(order.status, action);
  const noteLength = note.trim().length;

  const actorName = user?.user ? user.user.replace("_", " ") : "Người duyệt";

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        ref={modalRef}
        className="modal decision-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="decision-title"
        onMouseDown={(event) => event.stopPropagation()}
        style={{ maxWidth: 520 }}
      >
        <button className="modal-close" onClick={onClose} aria-label="Đóng">
          ×
        </button>
        <span className="review-label">QUYẾT ĐỊNH XỬ LÝ ĐƠN HÀNG</span>
        <h2 id="decision-title">Xác nhận xử lý đơn {order.id}</h2>
        <p style={{ color: "var(--color-outline)", fontSize: "0.875rem", margin: "4px 0 16px" }}>
          Hành động này được ghi nhận bởi <strong>{actorName}</strong> và lưu trữ vào sổ cái kiểm toán bất biến.
        </p>

        {/* Action Selector */}
        <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: "16px" }}>
          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: "12px",
              padding: "10px 14px",
              borderRadius: "var(--radius-md)",
              border: action === "APPROVE" ? "2px solid #10b981" : "1px solid var(--color-outline-variant)",
              backgroundColor: action === "APPROVE" ? "rgba(16, 185, 129, 0.08)" : "transparent",
              cursor: "pointer",
            }}
          >
            <input
              type="radio"
              name="decisionAction"
              checked={action === "APPROVE"}
              onChange={() => setAction("APPROVE")}
            />
            <CheckCircle2 size={18} color="#10b981" />
            <div style={{ flex: 1 }}>
              <strong>Duyệt đơn (Approve)</strong>
              <div style={{ fontSize: "0.75rem", color: "var(--color-outline)" }}>
                Chấp thuận đơn hàng để chuyển sang quy trình đồng bộ ERP.
              </div>
            </div>
          </label>

          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: "12px",
              padding: "10px 14px",
              borderRadius: "var(--radius-md)",
              border: action === "REQUEST_CHANGES" ? "2px solid #f59e0b" : "1px solid var(--color-outline-variant)",
              backgroundColor: action === "REQUEST_CHANGES" ? "rgba(245, 158, 11, 0.08)" : "transparent",
              cursor: "pointer",
            }}
          >
            <input
              type="radio"
              name="decisionAction"
              checked={action === "REQUEST_CHANGES"}
              onChange={() => setAction("REQUEST_CHANGES")}
            />
            <FileQuestion size={18} color="#f59e0b" />
            <div style={{ flex: 1 }}>
              <strong>Yêu cầu sửa đổi (Request changes)</strong>
              <div style={{ fontSize: "0.75rem", color: "var(--color-outline)" }}>
                Chuyển tiếp phản hồi tới khách hàng hoặc nhân viên kinh doanh để điều chỉnh.
              </div>
            </div>
          </label>

          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: "12px",
              padding: "10px 14px",
              borderRadius: "var(--radius-md)",
              border: action === "REJECT" ? "2px solid #ef4444" : "1px solid var(--color-outline-variant)",
              backgroundColor: action === "REJECT" ? "rgba(239, 68, 68, 0.08)" : "transparent",
              cursor: "pointer",
            }}
          >
            <input
              type="radio"
              name="decisionAction"
              checked={action === "REJECT"}
              onChange={() => setAction("REJECT")}
            />
            <XCircle size={18} color="#ef4444" />
            <div style={{ flex: 1 }}>
              <strong>Từ chối đơn (Reject)</strong>
              <div style={{ fontSize: "0.75rem", color: "var(--color-outline)" }}>
                Hủy bỏ đơn hàng do không thể đáp ứng hoặc vi phạm chính sách.
              </div>
            </div>
          </label>
        </div>

        {/* Blocked Alert */}
        {!isAllowed && blockedReason && (
          <div
            style={{
              padding: "10px 12px",
              borderRadius: "var(--radius-md)",
              backgroundColor: "rgba(239, 68, 68, 0.1)",
              border: "1px solid #ef4444",
              color: "#dc2626",
              fontSize: "0.8125rem",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              marginBottom: "16px",
            }}
          >
            <AlertCircle size={16} />
            <span>{blockedReason}</span>
          </div>
        )}

        {/* Warning Acknowledgment */}
        {action === "APPROVE" && order.findings.length > 0 && isAllowed && (
          <div className="decision-warning" style={{ marginBottom: "16px" }}>
            <strong>Đã xác nhận {order.findings.length} cảnh báo phát hiện</strong>
            <span>Bạn đang duyệt đơn hàng này với ghi nhận ngoại lệ vượt rào cản cảnh báo.</span>
          </div>
        )}

        {/* Decision Note Field */}
        <label className="note-field" style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.875rem" }}>
            <span>
              Ghi chú quyết định {noteRequired ? <strong style={{ color: "#ef4444" }}>(bắt buộc ≥10 ký tự)</strong> : "(tùy chọn)"}
            </span>
            <span style={{ fontSize: "0.75rem", color: noteRequired && noteLength < MIN_NOTE_LENGTH ? "#ef4444" : "var(--color-outline)" }}>
              {noteLength}/{MIN_NOTE_LENGTH} ký tự
            </span>
          </div>
          <textarea
            value={note}
            onChange={(event) => onNoteChange(event.target.value)}
            placeholder={
              action === "APPROVE"
                ? "Nhập lý do duyệt ngoại lệ..."
                : action === "REJECT"
                  ? "Nhập lý do từ chối đơn hàng..."
                  : "Nêu rõ các nội dung cần khách hàng điều chỉnh..."
            }
            rows={3}
            style={{
              width: "100%",
              padding: "8px 12px",
              borderRadius: "var(--radius-md)",
              border: noteRequired && noteLength > 0 && noteLength < MIN_NOTE_LENGTH ? "1px solid #ef4444" : "1px solid var(--color-outline-variant)",
              backgroundColor: "var(--color-surface-container-low)",
              color: "var(--color-on-surface)",
              fontSize: "0.875rem",
            }}
          />
          {noteRequired && noteError && noteLength > 0 && (
            <span style={{ fontSize: "0.75rem", color: "#ef4444" }}>{noteError}</span>
          )}
        </label>

        <div className="modal-actions" style={{ marginTop: "20px", display: "flex", justifyContent: "flex-end", gap: "10px" }}>
          <button className="secondary-button" onClick={onClose}>
            Hủy bỏ
          </button>
          <button
            className={action === "REJECT" ? "danger-button" : "approve-button"}
            disabled={!isAllowed || (noteRequired && Boolean(noteError))}
            onClick={() => onConfirm(action)}
            style={{
              padding: "8px 18px",
              borderRadius: "var(--radius-md)",
              cursor: !isAllowed || (noteRequired && Boolean(noteError)) ? "not-allowed" : "pointer",
              opacity: !isAllowed || (noteRequired && Boolean(noteError)) ? 0.5 : 1,
            }}
          >
            {action === "APPROVE" ? "Xác nhận duyệt" : action === "REJECT" ? "Xác nhận từ chối" : "Gửi yêu cầu sửa"}
          </button>
        </div>
      </section>
    </div>
  );
}
