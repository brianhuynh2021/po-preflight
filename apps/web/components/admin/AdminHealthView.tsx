"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Clock,
  Copy,
  Database,
  Layers,
  Radio,
  RefreshCw,
  Server,
  ShieldAlert,
  Zap,
} from "lucide-react";

interface DatabaseHealth {
  status: string;
  latency_ms: number;
  db_type: string;
}

interface OutboxHealth {
  pending: number;
  processing: number;
  sent: number;
  failed: number;
  dead_letter: number;
  total: number;
}

interface InventoryStaleness {
  total_snapshots: number;
  stale_count: number;
  newest_as_of: string | null;
}

interface RequestErrorRecord {
  id: number;
  request_id: string;
  endpoint: string;
  status_code: number;
  error_message: string;
  traceback?: string | null;
  created_at: string;
}

interface AdminHealthData {
  status: string;
  environment: string;
  version: string;
  log_format: string;
  otel_enabled: boolean;
  sentry_enabled: boolean;
  uptime_seconds: number;
  database: DatabaseHealth;
  outbox: OutboxHealth;
  inventory: InventoryStaleness;
  recent_errors: RequestErrorRecord[];
}

export function AdminHealthView() {
  const [data, setData] = useState<AdminHealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [selectedError, setSelectedError] = useState<RequestErrorRecord | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch("/api/v1/admin/health");
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      const json = await res.json();
      setData(json);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Không thể tải dữ liệu giám sát hệ thống.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let mounted = true;
    const runFetch = async () => {
      try {
        const res = await fetch("/api/v1/admin/health");
        if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        const json = await res.json();
        if (mounted) {
          setData(json);
          setLoading(false);
        }
      } catch (err: unknown) {
        if (mounted) {
          setError(err instanceof Error ? err.message : "Không thể tải dữ liệu giám sát.");
          setLoading(false);
        }
      }
    };

    runFetch();
    const interval = setInterval(runFetch, 15000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const copyRequestId = (reqId: string) => {
    navigator.clipboard.writeText(reqId);
    setCopiedId(reqId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const formatUptime = (seconds: number) => {
    const d = Math.floor(seconds / (3600 * 24));
    const h = Math.floor((seconds % (3600 * 24)) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (d > 0) return `${d}d ${h}h ${m}m`;
    if (h > 0) return `${h}h ${m}m ${s}s`;
    return `${m}m ${s}s`;
  };

  return (
    <div className="page-container" style={{ padding: "var(--space-6)" }}>
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "var(--space-6)",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
            <Activity size={28} color="var(--color-primary, #2563eb)" />
            <h1 style={{ margin: 0, fontSize: "1.5rem", fontWeight: 700 }}>
              Giám sát & Sức khỏe Hệ thống (Observability)
            </h1>
          </div>
          <p style={{ margin: "4px 0 0", color: "var(--color-text-muted, #64748b)", fontSize: "0.875rem" }}>
            Trạng thái hạ tầng máy chủ, độ trễ cơ sở dữ liệu, hàng đợi ERP Outbox và nhật ký lỗi Request-ID 5xx.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="btn btn-secondary interactive"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "var(--space-2)",
            padding: "8px 16px",
            borderRadius: "6px",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          <RefreshCw size={16} className={loading ? "spin-animation" : ""} />
          <span>{loading ? "Đang tải..." : "Làm mới"}</span>
        </button>
      </div>

      {error && (
        <div
          style={{
            backgroundColor: "rgba(239, 68, 68, 0.1)",
            border: "1px solid rgba(239, 68, 68, 0.3)",
            color: "#b91c1c",
            padding: "var(--space-4)",
            borderRadius: "8px",
            marginBottom: "var(--space-6)",
            display: "flex",
            alignItems: "center",
            gap: "var(--space-3)",
          }}
        >
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {data && (
        <>
          {/* Key Metric Cards */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: "var(--space-4)",
              marginBottom: "var(--space-6)",
            }}
          >
            {/* Status Card */}
            <div className="card" style={{ padding: "var(--space-4)", borderRadius: "8px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", color: "var(--color-text-muted)" }}>
                <span style={{ fontSize: "0.8125rem", fontWeight: 600 }}>TRẠNG THÁI TỔNG THỂ</span>
                {data.status === "healthy" ? (
                  <CheckCircle2 size={18} color="#16a34a" />
                ) : (
                  <ShieldAlert size={18} color="#dc2626" />
                )}
              </div>
              <div style={{ fontSize: "1.375rem", fontWeight: 700, marginTop: "8px", textTransform: "capitalize" }}>
                {data.status === "healthy" ? "Hoạt động tốt" : data.status === "degraded" ? "Cảnh báo" : "Gặp sự cố"}
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginTop: "4px" }}>
                Môi trường: <strong>{data.environment}</strong> (v{data.version})
              </div>
            </div>

            {/* Database Card */}
            <div className="card" style={{ padding: "var(--space-4)", borderRadius: "8px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", color: "var(--color-text-muted)" }}>
                <span style={{ fontSize: "0.8125rem", fontWeight: 600 }}>CƠ SỞ DỮ LIỆU</span>
                <Database size={18} color="var(--color-primary)" />
              </div>
              <div style={{ fontSize: "1.375rem", fontWeight: 700, marginTop: "8px" }}>
                {data.database.latency_ms} ms
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginTop: "4px" }}>
                Động cơ: <strong>{data.database.db_type.toUpperCase()}</strong> • Ping OK
              </div>
            </div>

            {/* Outbox Pending Card */}
            <div className="card" style={{ padding: "var(--space-4)", borderRadius: "8px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", color: "var(--color-text-muted)" }}>
                <span style={{ fontSize: "0.8125rem", fontWeight: 600 }}>ERP OUTBOX HÀNG ĐỢI</span>
                <Layers size={18} color="#f59e0b" />
              </div>
              <div style={{ fontSize: "1.375rem", fontWeight: 700, marginTop: "8px" }}>
                {data.outbox.pending} / {data.outbox.total}
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginTop: "4px" }}>
                Đã gửi: {data.outbox.sent} • Dead-letter:{" "}
                <strong style={{ color: data.outbox.dead_letter > 0 ? "#dc2626" : "inherit" }}>
                  {data.outbox.dead_letter}
                </strong>
              </div>
            </div>

            {/* Inventory Snapshots */}
            <div className="card" style={{ padding: "var(--space-4)", borderRadius: "8px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", color: "var(--color-text-muted)" }}>
                <span style={{ fontSize: "0.8125rem", fontWeight: 600 }}>TỒN KHO SNAPSHOT</span>
                <Server size={18} color="#8b5cf6" />
              </div>
              <div style={{ fontSize: "1.375rem", fontWeight: 700, marginTop: "8px" }}>
                {data.inventory.total_snapshots} SKUs
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginTop: "4px" }}>
                Hết hạn:{" "}
                <strong style={{ color: data.inventory.stale_count > 0 ? "#f59e0b" : "inherit" }}>
                  {data.inventory.stale_count} SKUs
                </strong>
              </div>
            </div>

            {/* Uptime & Observability Card */}
            <div className="card" style={{ padding: "var(--space-4)", borderRadius: "8px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", color: "var(--color-text-muted)" }}>
                <span style={{ fontSize: "0.8125rem", fontWeight: 600 }}>THỜI GIAN HOẠT ĐỘNG</span>
                <Clock size={18} color="#06b6d4" />
              </div>
              <div style={{ fontSize: "1.375rem", fontWeight: 700, marginTop: "8px" }}>
                {formatUptime(data.uptime_seconds)}
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", marginTop: "4px" }}>
                OTel: {data.otel_enabled ? "Bật" : "Tắt"} • Sentry: {data.sentry_enabled ? "Bật" : "Tắt"}
              </div>
            </div>
          </div>

          {/* System Configurations Section */}
          <div className="card" style={{ padding: "var(--space-5)", borderRadius: "8px", marginBottom: "var(--space-6)" }}>
            <h2 style={{ fontSize: "1.0625rem", fontWeight: 600, margin: "0 0 var(--space-4)" }}>
              Cấu hình Runtime & Tracing
            </h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "var(--space-4)" }}>
              <div style={{ padding: "12px", background: "var(--color-bg-subtle, rgba(0,0,0,0.03))", borderRadius: "6px" }}>
                <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)" }}>ĐỊNH DẠNG NHẬT KÝ (LOG FORMAT)</div>
                <div style={{ fontWeight: 600, marginTop: "4px", fontSize: "0.9375rem" }}>
                  <code>{data.log_format.toUpperCase()}</code> (Tự động chuyển JSON trên production)
                </div>
              </div>

              <div style={{ padding: "12px", background: "var(--color-bg-subtle, rgba(0,0,0,0.03))", borderRadius: "6px" }}>
                <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)" }}>OPENTELEMETRY TRACING (OTLP)</div>
                <div style={{ fontWeight: 600, marginTop: "4px", fontSize: "0.9375rem", display: "flex", alignItems: "center", gap: "6px" }}>
                  <Radio size={14} color={data.otel_enabled ? "#16a34a" : "#64748b"} />
                  <span>{data.otel_enabled ? "Đang xuất sang OTLP Collector" : "Chưa bật (No-op Fallback)"}</span>
                </div>
              </div>

              <div style={{ padding: "12px", background: "var(--color-bg-subtle, rgba(0,0,0,0.03))", borderRadius: "6px" }}>
                <div style={{ fontSize: "0.75rem", color: "var(--color-text-muted)" }}>THEO DÕI SỰ CỐ SENTRY</div>
                <div style={{ fontWeight: 600, marginTop: "4px", fontSize: "0.9375rem", display: "flex", alignItems: "center", gap: "6px" }}>
                  <Zap size={14} color={data.sentry_enabled ? "#16a34a" : "#64748b"} />
                  <span>{data.sentry_enabled ? "Đã kết nối Sentry DSN" : "Chưa kích hoạt SENTRY_DSN"}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Recent 5xx Request Errors Table */}
          <div className="card" style={{ padding: "var(--space-5)", borderRadius: "8px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-4)" }}>
              <h2 style={{ fontSize: "1.0625rem", fontWeight: 600, margin: 0 }}>
                10 Lỗi Server 5xx Gần Nhất (Request-ID Correlation)
              </h2>
              <span style={{ fontSize: "0.8125rem", color: "var(--color-text-muted)" }}>
                Tự động dọn dẹp sau 7 ngày
              </span>
            </div>

            {data.recent_errors.length === 0 ? (
              <div
                style={{
                  padding: "var(--space-6)",
                  textAlign: "center",
                  color: "#16a34a",
                  background: "rgba(22, 163, 74, 0.05)",
                  borderRadius: "6px",
                  fontWeight: 500,
                }}
              >
                <CheckCircle2 size={24} style={{ margin: "0 auto 8px", display: "block" }} />
                Không có lỗi 5xx nào được ghi nhận gần đây. Hệ thống đang vận hành ổn định 100%!
              </div>
            ) : (
              <div style={{ overflowX: "auto" }}>
                <table className="table" style={{ width: "100%", fontSize: "0.875rem" }}>
                  <thead>
                    <tr>
                      <th style={{ textAlign: "left", padding: "10px" }}>Thời gian</th>
                      <th style={{ textAlign: "left", padding: "10px" }}>Mã Request ID</th>
                      <th style={{ textAlign: "left", padding: "10px" }}>Endpoint</th>
                      <th style={{ textAlign: "left", padding: "10px" }}>HTTP</th>
                      <th style={{ textAlign: "left", padding: "10px" }}>Thông điệp lỗi</th>
                      <th style={{ textAlign: "center", padding: "10px" }}>Thao tác</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.recent_errors.map((err) => (
                      <tr key={err.id}>
                        <td style={{ padding: "10px", whiteSpace: "nowrap", color: "var(--color-text-muted)" }}>
                          {new Date(err.created_at).toLocaleString("vi-VN")}
                        </td>
                        <td style={{ padding: "10px" }}>
                          <span
                            style={{
                              fontFamily: "monospace",
                              padding: "2px 6px",
                              borderRadius: "4px",
                              background: "var(--color-bg-subtle, #f1f5f9)",
                              fontWeight: 600,
                              fontSize: "0.8125rem",
                            }}
                          >
                            {err.request_id}
                          </span>
                        </td>
                        <td style={{ padding: "10px", fontFamily: "monospace", fontSize: "0.8125rem" }}>
                          {err.endpoint}
                        </td>
                        <td style={{ padding: "10px" }}>
                          <span
                            style={{
                              background: "rgba(239, 68, 68, 0.15)",
                              color: "#dc2626",
                              padding: "2px 6px",
                              borderRadius: "4px",
                              fontWeight: 700,
                              fontSize: "0.75rem",
                            }}
                          >
                            {err.status_code}
                          </span>
                        </td>
                        <td style={{ padding: "10px", maxWidth: "300px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {err.error_message}
                        </td>
                        <td style={{ padding: "10px", textAlign: "center" }}>
                          <div style={{ display: "flex", gap: "6px", justifyContent: "center" }}>
                            <button
                              className="btn btn-sm btn-ghost interactive"
                              onClick={() => copyRequestId(err.request_id)}
                              title="Sao chép Request-ID"
                              style={{ padding: "4px 8px" }}
                            >
                              <Copy size={13} />
                              <span>{copiedId === err.request_id ? "Đã chép!" : "Chép ID"}</span>
                            </button>
                            {err.traceback && (
                              <button
                                className="btn btn-sm btn-secondary interactive"
                                onClick={() => setSelectedError(err)}
                                style={{ padding: "4px 8px" }}
                              >
                                Chi tiết
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Traceback Modal */}
          {selectedError && (
            <div
              style={{
                position: "fixed",
                inset: 0,
                backgroundColor: "rgba(0, 0, 0, 0.5)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                zIndex: 9999,
                padding: "var(--space-4)",
              }}
              onClick={() => setSelectedError(null)}
            >
              <div
                className="card"
                style={{
                  maxWidth: "800px",
                  width: "100%",
                  maxHeight: "85vh",
                  overflowY: "auto",
                  padding: "var(--space-6)",
                  borderRadius: "10px",
                }}
                onClick={(e) => e.stopPropagation()}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-4)" }}>
                  <h3 style={{ margin: 0, fontSize: "1.125rem", fontWeight: 700 }}>
                    Chi tiết Lỗi Request-ID: <code>{selectedError.request_id}</code>
                  </h3>
                  <button className="btn btn-secondary btn-sm" onClick={() => setSelectedError(null)}>
                    Đóng
                  </button>
                </div>

                <div style={{ marginBottom: "var(--space-3)", fontSize: "0.875rem" }}>
                  <strong>Endpoint:</strong> <code>{selectedError.endpoint}</code> • <strong>HTTP:</strong> {selectedError.status_code}
                </div>
                <div style={{ marginBottom: "var(--space-4)", fontSize: "0.875rem", color: "#dc2626" }}>
                  <strong>Lỗi:</strong> {selectedError.error_message}
                </div>

                {selectedError.traceback && (
                  <pre
                    style={{
                      background: "#0f172a",
                      color: "#f8fafc",
                      padding: "var(--space-4)",
                      borderRadius: "6px",
                      fontSize: "0.75rem",
                      overflowX: "auto",
                      whiteSpace: "pre-wrap",
                      lineHeight: 1.5,
                    }}
                  >
                    {selectedError.traceback}
                  </pre>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
