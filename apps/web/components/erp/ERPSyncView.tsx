"use client";

import { useEffect, useState } from "react";
import { api, describeError } from "@/app/lib/api/client";
import type { OutboxStats } from "@/app/lib/api/types";
import { RefreshCw, CheckCircle2, AlertTriangle, Play } from "lucide-react";
import { useRipple } from "@/app/lib/useRipple";

export function ERPSyncView() {
  const { createRipple } = useRipple();
  const [stats, setStats] = useState<OutboxStats | null>(null);
  const [events, setEvents] = useState<Array<Record<string, unknown>>>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const fetchOutboxData = async () => {
    setIsLoading(true);
    try {
      const [s, evs] = await Promise.all([
        api.erp.getOutboxStatus(),
        api.erp.getOutboxEvents(50),
      ]);
      setStats(s);
      setEvents(evs);
    } catch {
      // Offline fallback
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    Promise.all([api.erp.getOutboxStatus(), api.erp.getOutboxEvents(50)])
      .then(([s, evs]) => {
        if (mounted) {
          setStats(s);
          setEvents(evs);
        }
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, []);

  const handleProcessOutbox = async () => {
    setIsProcessing(true);
    setFeedback(null);
    try {
      const res = await api.erp.processOutbox(20);
      setFeedback({
        type: "success",
        message: `Đã xử lý xong ${res.processed_count} sự kiện Outbox ERP.`,
      });
      await fetchOutboxData();
    } catch (err) {
      setFeedback({
        type: "error",
        message: describeError(err),
      });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="page erp-sync-page page-enter">
      <div className="page-heading">
        <div>
          <p className="eyebrow">TÍCH HỢP HỆ THỐNG DOANH NGHIỆP · ERP Synchronization</p>
          <h1>Đồng bộ ERP (ERP Synchronization) &amp; Outbox Center</h1>
          <p>
            Mô hình Transactional Outbox bảo đảm chuyển phát đơn hàng chính xác một lần (Exactly-Once Delivery) sang SAP S/4HANA, Odoo, MISA AMIS với mã Idempotency chống trùng lặp tuyệt đối.
          </p>
        </div>
        <div style={{ display: "flex", gap: "var(--space-2)" }}>
          <button
            className="secondary-button interactive"
            onClick={(e) => {
              createRipple(e);
              void fetchOutboxData();
            }}
            disabled={isLoading}
            style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-1)" }}
          >
            <RefreshCw size={15} className={isLoading ? "animate-spin" : ""} />
            <span>Làm mới</span>
          </button>
          <button
            className="primary-button interactive"
            onClick={(e) => {
              createRipple(e);
              void handleProcessOutbox();
            }}
            disabled={isProcessing}
            style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-1)" }}
          >
            <Play size={15} />
            <span>{isProcessing ? "Đang đẩy dữ liệu..." : "Chạy xử lý đồng bộ Outbox"}</span>
          </button>
        </div>
      </div>

      {feedback && (
        <div
          style={{
            margin: "0 0 var(--space-4) 0",
            padding: "var(--space-3) var(--space-4)",
            borderRadius: "var(--radius-md)",
            border: feedback.type === "success" ? "1px solid #10b981" : "1px solid #ef4444",
            backgroundColor: feedback.type === "success" ? "rgba(16, 185, 129, 0.08)" : "rgba(239, 68, 68, 0.08)",
            display: "flex",
            alignItems: "center",
            gap: "var(--space-2)",
            color: feedback.type === "success" ? "#10b981" : "#ef4444",
            fontSize: "0.875rem",
          }}
        >
          {feedback.type === "success" ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
          <strong>{feedback.message}</strong>
        </div>
      )}

      {/* Metrics Row */}
      <div className="metrics-row" style={{ marginBottom: "var(--space-5)" }}>
        <div className="metric">
          <span>Chờ phát (Pending)</span>
          <strong className="tabular-nums">{stats?.pending_count ?? 0}</strong>
          <small>
            <i className="metric-dot amber" /> Sẵn sàng xử lý
          </small>
        </div>
        <div className="metric">
          <span>Đang gửi (Processing)</span>
          <strong className="tabular-nums">{stats?.processing_count ?? 0}</strong>
          <small>
            <i className="metric-dot blue" /> Đang kết nối Adapter ERP
          </small>
        </div>
        <div className="metric">
          <span>Đã phát thành công</span>
          <strong className="tabular-nums">{stats?.sent_count ?? 0}</strong>
          <small>
            <i className="metric-dot green" /> Đã xác nhận giao dịch ERP
          </small>
        </div>
        <div className="metric">
          <span>Lỗi / Hàng đợi chết (Dead-Letter)</span>
          <strong className="tabular-nums" style={{ color: (stats?.failed_count ?? 0) > 0 ? "#ef4444" : "inherit" }}>
            {stats?.failed_count ?? 0}
          </strong>
          <small>
            <i className="metric-dot red" /> Yêu cầu can thiệp kỹ thuật
          </small>
        </div>
      </div>

      {/* Outbox Events Table */}
      <div className="content-card table-card">
        <div className="panel-toolbar">
          <div style={{ fontWeight: 600, fontSize: "0.95rem" }}>
            Danh sách tin nhắn Outbox giao dịch (Transactional Outbox Messages) ({events.length})
          </div>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th style={{ width: 60 }}>ID</th>
                <th>Mã đơn hàng</th>
                <th>Loại sự kiện</th>
                <th>Mã Idempotency Key</th>
                <th style={{ textAlign: "center" }}>Trạng thái</th>
                <th style={{ textAlign: "center" }}>Số lần thử</th>
                <th>Mã tham chiếu ERP</th>
                <th>Thời gian</th>
              </tr>
            </thead>
            <tbody>
              {events.map((ev, idx) => {
                const st = String(ev.status || "PENDING").toUpperCase();
                return (
                  <tr key={idx}>
                    <td className="tabular-nums">#{String(ev.id)}</td>
                    <td>
                      <strong>{String(ev.aggregate_id || ev.po_number || "—")}</strong>
                    </td>
                    <td>{String(ev.event_type || "ORDER_APPROVED")}</td>
                    <td>
                      <code style={{ fontSize: "0.75rem" }}>
                        {String(ev.idempotency_key || "—").slice(0, 16)}...
                      </code>
                    </td>
                    <td style={{ textAlign: "center" }}>
                      <span
                        className={
                          st === "SENT" || st === "DELIVERED"
                            ? "catalog-state active"
                            : st === "FAILED" || st === "DEAD_LETTER"
                              ? "catalog-state inactive"
                              : "badge"
                        }
                        style={{ fontSize: "0.75rem", padding: "2px 6px" }}
                      >
                        {st}
                      </span>
                    </td>
                    <td className="tabular-nums" style={{ textAlign: "center" }}>
                      {String(ev.retry_count ?? 0)}
                    </td>
                    <td>
                      {ev.erp_reference ? (
                        <code style={{ color: "var(--color-primary)", fontWeight: 600 }}>
                          {String(ev.erp_reference)}
                        </code>
                      ) : (
                        <span style={{ color: "var(--color-outline)" }}>—</span>
                      )}
                    </td>
                    <td style={{ fontSize: "0.8rem", color: "var(--color-outline)" }}>
                      {String(ev.created_at || "Vừa xong")}
                    </td>
                  </tr>
                );
              })}
              {events.length === 0 && (
                <tr>
                  <td colSpan={8} style={{ textAlign: "center", padding: "var(--space-6)", color: "var(--color-outline)" }}>
                    Chưa có sự kiện nào trong hàng đợi Outbox.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
