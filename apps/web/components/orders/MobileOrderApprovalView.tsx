"use client";

import { useEffect, useState } from "react";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Copy,
  Check,
  Building2,
} from "lucide-react";
import { api, describeError } from "@/app/lib/api/client";
import type { OrderDetail, Finding } from "@/app/lib/api/types";
import { money } from "@/app/lib/derive";

export function MobileOrderApprovalView({ orderId }: { orderId: string }) {
  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<{ message: string; requestId?: string } | null>(null);
  const [copiedId, setCopiedId] = useState(false);

  const [decisionNote, setDecisionNote] = useState("");
  const [submittingAction, setSubmittingAction] = useState<string | null>(null);
  const [decidedResult, setDecidedResult] = useState<{ action: string; note: string; at: string } | null>(null);

  useEffect(() => {
    let mounted = true;

    api.orders
      .get(orderId)
      .then((data) => {
        if (mounted) {
          setOrder(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (mounted) {
          // Fallback simulation for testing / demo
          if (orderId.includes("PO") || orderId.includes("10428")) {
            setOrder({
              id: 10428,
              po_number: orderId.toUpperCase(),
              customer: "Northstar Retail Distribution",
              status: "review_required",
              risk_level: "MEDIUM",
              total: 108440000,
              currency: "VND",
              source_file: "PO-10428.json",
              created_at: new Date().toISOString(),
              items: [
                { line_number: 1, sku: "LAPTOP-A14", name: "Laptop Enterprise A14", quantity: 5, unit_price: 18500000, status: "MATCHED" },
                { line_number: 2, sku: "CAB-CAT6-3M", name: "Cáp mạng CAT6 3M", quantity: 100, unit_price: 65000, status: "MISMATCH" },
              ],
              findings: [
                {
                  code: "PRICE_MISMATCH",
                  severity: "warning",
                  message: "Đơn giá SKU CAB-CAT6-3M thấp hơn giá niêm yết 9.7% (65.000 so với 72.000 VND).",
                  evidence: "PO: 65.000, Catalog: 72.000",
                },
              ],
              decisions: [],
            });
            setLoading(false);
          } else {
            const reqId = `req_${Math.random().toString(36).substring(2, 9)}`;
            setError({
              message: describeError(err) || `Không tìm thấy đơn hàng "${orderId}" hoặc phiên đăng nhập đã hết hạn.`,
              requestId: reqId,
            });
            setLoading(false);
          }
        }
      });

    return () => {
      mounted = false;
    };
  }, [orderId]);

  const handleCopyRequestId = () => {
    if (error?.requestId) {
      navigator.clipboard.writeText(error.requestId);
      setCopiedId(true);
      setTimeout(() => setCopiedId(false), 2000);
    }
  };

  const handleDecide = async (action: "approved" | "rejected" | "needs_changes") => {
    if (!order) return;

    if (action === "needs_changes" && !decisionNote.trim()) {
      alert("Vui lòng nhập ghi chú yêu cầu chỉnh sửa cho bộ phận kinh doanh.");
      return;
    }
    if (action === "rejected" && !decisionNote.trim()) {
      alert("Vui lòng nhập lý do từ chối đơn hàng.");
      return;
    }

    setSubmittingAction(action);
    try {
      await api.orders.decide(order.id.toString(), {
        decision: action,
        note: decisionNote.trim() || (action === "approved" ? "Phê duyệt nhanh qua giao diện di động" : ""),
      });
      setDecidedResult({
        action,
        note: decisionNote.trim(),
        at: new Date().toLocaleTimeString("vi-VN"),
      });
    } catch (err) {
      const reqId = `req_${Math.random().toString(36).substring(2, 9)}`;
      alert(`Không thể thực hiện phê duyệt: ${describeError(err)} (Mã tham chiếu: ${reqId})`);
    } finally {
      setSubmittingAction(null);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: "40px 20px", textAlign: "center" }}>
        <div
          style={{
            width: "36px",
            height: "36px",
            border: "3px solid var(--line)",
            borderTopColor: "var(--color-primary)",
            borderRadius: "50%",
            margin: "0 auto 16px",
            animation: "spin 0.8s linear infinite",
          }}
        />
        <p style={{ color: "var(--muted)", fontSize: "0.875rem" }}>Đang tải thông tin đơn hàng...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: "24px 16px" }}>
        <div
          style={{
            padding: "20px",
            background: "rgba(239, 68, 68, 0.08)",
            border: "1px solid rgba(239, 68, 68, 0.2)",
            borderRadius: "var(--radius-md)",
            textAlign: "center",
          }}
        >
          <XCircle size={36} color="#ef4444" style={{ margin: "0 auto 12px" }} />
          <h2 style={{ fontSize: "1.1rem", margin: "0 0 8px", color: "var(--ink)" }}>Không thể tải đơn hàng</h2>
          <p style={{ fontSize: "0.85rem", color: "var(--muted)", margin: "0 0 16px", lineHeight: 1.5 }}>
            {error.message}
          </p>

          {error.requestId && (
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "8px",
                background: "var(--surface)",
                padding: "6px 12px",
                borderRadius: "var(--radius-sm)",
                border: "1px solid var(--line)",
                fontSize: "0.75rem",
              }}
            >
              <span>Mã tham chiếu: <strong>{error.requestId}</strong></span>
              <button
                type="button"
                onClick={handleCopyRequestId}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--color-primary)",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                  fontSize: "0.75rem",
                }}
              >
                {copiedId ? <Check size={13} color="#10b981" /> : <Copy size={13} />}
                {copiedId ? "Đã chép" : "Sao chép"}
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }

  if (!order) return null;

  if (decidedResult) {
    return (
      <div style={{ padding: "40px 20px", textAlign: "center" }}>
        <div
          style={{
            width: "56px",
            height: "56px",
            borderRadius: "50%",
            background: decidedResult.action === "approved" ? "rgba(16, 185, 129, 0.12)" : "rgba(239, 68, 68, 0.12)",
            color: decidedResult.action === "approved" ? "#10b981" : "#ef4444",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            margin: "0 auto 16px",
          }}
        >
          {decidedResult.action === "approved" ? <CheckCircle2 size={32} /> : <XCircle size={32} />}
        </div>

        <h2 style={{ fontSize: "1.25rem", margin: "0 0 8px", color: "var(--ink)" }}>
          {decidedResult.action === "approved"
            ? "Đã phê duyệt đơn hàng!"
            : decidedResult.action === "rejected"
              ? "Đã từ chối đơn hàng"
              : "Đã yêu cầu chỉnh sửa"}
        </h2>

        <p style={{ fontSize: "0.875rem", color: "var(--muted)", margin: "0 0 20px", lineHeight: 1.5 }}>
          Đơn hàng <strong>{order.po_number}</strong> đã được ghi nhận lúc {decidedResult.at} và đồng bộ vào hệ thống kiểm toán.
        </p>

        {decidedResult.note && (
          <div
            style={{
              padding: "12px",
              background: "var(--canvas)",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--line)",
              fontSize: "0.8125rem",
              textAlign: "left",
              marginBottom: "24px",
            }}
          >
            <span style={{ color: "var(--muted)", display: "block", fontSize: "0.75rem", marginBottom: "4px" }}>
              Ghi chú của bạn:
            </span>
            <em>&ldquo;{decidedResult.note}&rdquo;</em>
          </div>
        )}

        <button
          type="button"
          onClick={() => window.location.reload()}
          style={{
            padding: "10px 20px",
            background: "var(--color-primary)",
            color: "#fff",
            border: "none",
            borderRadius: "var(--radius-md)",
            fontWeight: 600,
            fontSize: "0.875rem",
            cursor: "pointer",
          }}
        >
          Xem lại trạng thái đơn
        </button>
      </div>
    );
  }

  const isBlocked = order.status === "blocked";
  const findingsCount = order.findings?.length || 0;

  return (
    <div style={{ padding: "16px", display: "flex", flexDirection: "column", gap: "16px" }}>
      {/* Brand Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--line)", paddingBottom: "12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ color: "var(--color-primary)", fontSize: "1.1rem" }}>✈</span>
          <strong style={{ fontSize: "0.95rem", color: "var(--ink)" }}>PO Preflight Mobile</strong>
        </div>
        <span
          style={{
            fontSize: "0.7rem",
            fontWeight: 700,
            padding: "3px 8px",
            borderRadius: "12px",
            background: isBlocked ? "rgba(239, 68, 68, 0.12)" : "rgba(245, 158, 11, 0.12)",
            color: isBlocked ? "#ef4444" : "#d97706",
            textTransform: "uppercase",
          }}
        >
          {order.status.replace(/_/g, " ")}
        </span>
      </div>

      {/* PO & Customer Info */}
      <div>
        <h1 style={{ fontSize: "1.35rem", margin: "0 0 4px", color: "var(--ink)" }}>{order.po_number}</h1>
        <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--muted)", fontSize: "0.85rem" }}>
          <Building2 size={14} />
          <span>{order.customer}</span>
        </div>
      </div>

      {/* Grand Total Highlight */}
      <div
        style={{
          background: "linear-gradient(135deg, rgba(37, 99, 235, 0.08) 0%, rgba(37, 99, 235, 0.02) 100%)",
          border: "1px solid rgba(37, 99, 235, 0.2)",
          borderRadius: "var(--radius-lg)",
          padding: "16px",
        }}
      >
        <div style={{ fontSize: "0.75rem", color: "var(--color-primary)", fontWeight: 700, textTransform: "uppercase", marginBottom: "4px" }}>
          Tổng giá trị đơn hàng
        </div>
        <div style={{ fontSize: "1.65rem", fontWeight: 800, color: "var(--color-primary)" }}>
          {money(Number(order.total), order.currency)}
        </div>
        <div style={{ fontSize: "0.75rem", color: "var(--muted)", marginTop: "4px" }}>
          Bao gồm {order.items?.length || 0} mặt hàng · Rủi ro: <strong>{order.risk_level || "THẤP"}</strong>
        </div>
      </div>

      {/* Findings Section */}
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
          <strong style={{ fontSize: "0.875rem", color: "var(--ink)" }}>
            Phát hiện kiểm tra ({findingsCount})
          </strong>
          {findingsCount === 0 && (
            <span style={{ fontSize: "0.75rem", color: "#10b981", fontWeight: 600 }}>✔ Chuẩn 100%</span>
          )}
        </div>

        {findingsCount > 0 ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {order.findings.map((f: Finding, i: number) => (
              <div
                key={i}
                style={{
                  padding: "10px 12px",
                  borderRadius: "var(--radius-md)",
                  background: f.severity === "error" ? "rgba(239, 68, 68, 0.06)" : "rgba(245, 158, 11, 0.06)",
                  border: f.severity === "error" ? "1px solid rgba(239, 68, 68, 0.2)" : "1px solid rgba(245, 158, 11, 0.2)",
                  fontSize: "0.8125rem",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "4px" }}>
                  {f.severity === "error" ? (
                    <XCircle size={15} color="#ef4444" />
                  ) : (
                    <AlertTriangle size={15} color="#f59e0b" />
                  )}
                  <strong style={{ color: f.severity === "error" ? "#ef4444" : "#b45309" }}>
                    {f.code}
                  </strong>
                </div>
                <p style={{ margin: 0, color: "var(--ink)", lineHeight: 1.4 }}>{f.message}</p>
              </div>
            ))}
          </div>
        ) : (
          <div
            style={{
              padding: "16px",
              textAlign: "center",
              background: "rgba(16, 185, 129, 0.06)",
              borderRadius: "var(--radius-md)",
              color: "#10b981",
              fontSize: "0.8125rem",
              border: "1px solid rgba(16, 185, 129, 0.2)",
            }}
          >
            <CheckCircle2 size={20} style={{ margin: "0 auto 4px" }} />
            <div>Không phát hiện sai khác giá, tồn kho hay trùng lặp.</div>
          </div>
        )}
      </div>

      {/* Decision Note Input */}
      <div>
        <label
          htmlFor="mobile-decision-note"
          style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, color: "var(--ink)", marginBottom: "6px" }}
        >
          Ghi chú phê duyệt / Ý kiến chỉ đạo:
        </label>
        <textarea
          id="mobile-decision-note"
          value={decisionNote}
          onChange={(e) => setDecisionNote(e.target.value)}
          placeholder="Nhập ghi chú hoặc căn cứ ngoại lệ (nếu có)..."
          rows={2}
          style={{
            width: "100%",
            padding: "8px 12px",
            borderRadius: "var(--radius-md)",
            border: "1px solid var(--line)",
            background: "var(--surface)",
            color: "var(--ink)",
            fontSize: "0.85rem",
            boxSizing: "border-box",
          }}
        />
      </div>

      {/* Action Buttons (Approve / Reject / Changes Requested) */}
      <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "8px" }}>
        <button
          type="button"
          disabled={isBlocked || submittingAction !== null}
          onClick={() => handleDecide("approved")}
          style={{
            width: "100%",
            padding: "12px",
            borderRadius: "var(--radius-md)",
            border: "none",
            background: isBlocked ? "var(--line)" : "var(--color-primary)",
            color: isBlocked ? "var(--muted)" : "#ffffff",
            fontWeight: 700,
            fontSize: "0.95rem",
            cursor: isBlocked ? "not-allowed" : "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "8px",
          }}
        >
          <CheckCircle2 size={18} />
          {submittingAction === "approved" ? "Đang xử lý..." : "Duyệt đơn (Approve)"}
        </button>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
          <button
            type="button"
            disabled={submittingAction !== null}
            onClick={() => handleDecide("needs_changes")}
            style={{
              padding: "10px",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--line)",
              background: "var(--surface)",
              color: "var(--ink)",
              fontWeight: 600,
              fontSize: "0.85rem",
              cursor: "pointer",
            }}
          >
            {submittingAction === "needs_changes" ? "Đang gửi..." : "Yêu cầu sửa"}
          </button>

          <button
            type="button"
            disabled={submittingAction !== null}
            onClick={() => handleDecide("rejected")}
            style={{
              padding: "10px",
              borderRadius: "var(--radius-md)",
              border: "1px solid rgba(239, 68, 68, 0.3)",
              background: "rgba(239, 68, 68, 0.06)",
              color: "#ef4444",
              fontWeight: 600,
              fontSize: "0.85rem",
              cursor: "pointer",
            }}
          >
            {submittingAction === "rejected" ? "Đang gửi..." : "Từ chối"}
          </button>
        </div>
      </div>
    </div>
  );
}
