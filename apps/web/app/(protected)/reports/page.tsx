"use client";

import React, { useEffect, useState } from "react";
import {
  Clock,
  Download,
  Mail,
  RefreshCw,
  ShieldAlert,
  TrendingUp,
  Zap,
  Sparkles,
} from "lucide-react";
import { api } from "@/app/lib/api/client";
import type { PilotReportResponse } from "@/app/lib/api/types";
import { money } from "@/app/lib/derive";

const DEFAULT_REPORT: PilotReportResponse = {
  period: {
    from: new Date(Date.now() - 30 * 86400000).toISOString(),
    to: new Date().toISOString(),
  },
  summary: {
    total_orders_received: 48,
    total_orders_approved: 32,
    total_orders_rejected: 5,
    total_orders_needs_changes: 4,
    total_orders_blocked: 7,
    total_orders_review_required: 12,
    total_orders_ready: 25,
    total_value_processed: 642850000,
    total_lines_processed: 184,
    lines_corrected_count: 9,
    lines_corrected_rate_pct: 4.9,
    avg_intake_to_analyzed_seconds: 2.1,
    avg_analyzed_to_decision_minutes: 8.5,
    orders_blocked_before_erp: 7,
    duplicate_po_count: 2,
    estimated_hours_saved: 18.4,
    avg_cost_per_order_usd: 0.00018,
    total_cost_usd: 0.0086,
    automation_rate_pct: 85.4,
  },
  findings_distribution: {
    PRICE_MISMATCH: 9,
    INSUFFICIENT_STOCK: 6,
    UNKNOWN_SKU: 4,
    DUPLICATE_PO: 2,
    CREDIT_LIMIT_EXCEEDED: 1,
    INVALID_PACK_SIZE: 2,
  },
  rag_tier_breakdown: {
    exact_hash: 54.0,
    lexical_fuzzy: 26.0,
    semantic_vector: 16.0,
    llm_fallback: 4.0,
  },
  daily_trends: [
    { date: "2026-08-28", received: 6, approved: 4, blocked: 1, value: 84000000 },
    { date: "2026-08-29", received: 8, approved: 6, blocked: 1, value: 112000000 },
    { date: "2026-08-30", received: 5, approved: 4, blocked: 0, value: 65000000 },
    { date: "2026-08-31", received: 11, approved: 7, blocked: 2, value: 154000000 },
    { date: "2026-09-01", received: 9, approved: 6, blocked: 1, value: 128000000 },
    { date: "2026-09-02", received: 9, approved: 5, blocked: 2, value: 99850000 },
  ],
  orders_sample: [
    {
      po_number: "PO-10428",
      customer: "Northstar Retail",
      status: "review_required",
      total: 18500000,
      currency: "VND",
      created_at: "2026-09-02T10:15:00Z",
      lines_count: 2,
      findings_count: 1,
      decision_minutes: 6.2,
      cost_usd: 0.00005,
    },
    {
      po_number: "PO-2026-1001",
      customer: "Northstar Distribution",
      status: "ready_for_approval",
      total: 123500000,
      currency: "VND",
      created_at: "2026-09-02T11:27:11Z",
      lines_count: 3,
      findings_count: 0,
      decision_minutes: 4.1,
      cost_usd: 0.00005,
    },
  ],
};

// Business readable dictionary for finding codes
const FINDING_METADATA: Record<string, { label: string; desc: string; severity: "critical" | "warning" }> = {
  PRICE_MISMATCH: {
    label: "Chênh lệch giá bán so với Bảng giá hợp đồng",
    desc: "Đơn giá trên PO sai khác với Catalog chiết khấu đã ký",
    severity: "warning",
  },
  INSUFFICIENT_STOCK: {
    label: "Tồn kho khả dụng (ATP) không đủ đáp ứng",
    desc: "Số lượng đặt vượt quá lượng hàng có sẵn trong kho thực tế",
    severity: "warning",
  },
  UNKNOWN_SKU: {
    label: "Mã hàng (SKU) chưa khai báo trong danh mục",
    desc: "Mã sản phẩm lạ hoặc sai quy cách cần bóc tách kiểm tra",
    severity: "critical",
  },
  DUPLICATE_PO: {
    label: "Nghi ngờ đơn đặt hàng bị trùng lặp (Duplicate PO)",
    desc: "Mã số PO hoặc nội dung trùng với đơn hàng đã tiếp nhận",
    severity: "critical",
  },
  CREDIT_LIMIT_EXCEEDED: {
    label: "Vượt hạn mức tín dụng / công nợ khách hàng",
    desc: "Tổng giá trị đơn vượt quá bảo lãnh nợ cho phép",
    severity: "warning",
  },
  INVALID_PACK_SIZE: {
    label: "Sai quy cách đóng gói tối thiểu (MOQ)",
    desc: "Số lượng đặt không chia hết cho quy cách thùng/kiện",
    severity: "warning",
  },
  POSSIBLE_DUPLICATE: {
    label: "Cảnh báo trùng lặp đơn hàng tiềm ẩn",
    desc: "Trùng số hiệu PO cùng đối tác gửi trong 48 giờ qua",
    severity: "critical",
  },
};

export default function ReportsPage() {
  const [report, setReport] = useState<PilotReportResponse>(DEFAULT_REPORT);
  const [loading, setLoading] = useState(false);
  const [periodFilter, setPeriodFilter] = useState<"7d" | "30d" | "all">("30d");
  const [emailStatus, setEmailStatus] = useState<string | null>(null);
  const [sendingEmail, setSendingEmail] = useState(false);

  useEffect(() => {
    let active = true;
    const fetchAsync = async () => {
      let fromDate: string | undefined;
      const now = new Date();
      if (periodFilter === "7d") {
        fromDate = new Date(now.getTime() - 7 * 86400000).toISOString();
      } else if (periodFilter === "30d") {
        fromDate = new Date(now.getTime() - 30 * 86400000).toISOString();
      }
      try {
        const data = await api.reports.getPilotReport(fromDate);
        if (active && data && data.summary) {
          setReport(data);
        }
      } catch {
        // Fallback to seeded demo report
      }
    };
    void fetchAsync();
    return () => {
      active = false;
    };
  }, [periodFilter]);

  const handleRefresh = async () => {
    setLoading(true);
    let fromDate: string | undefined;
    const now = new Date();
    if (periodFilter === "7d") {
      fromDate = new Date(now.getTime() - 7 * 86400000).toISOString();
    } else if (periodFilter === "30d") {
      fromDate = new Date(now.getTime() - 30 * 86400000).toISOString();
    }
    try {
      const data = await api.reports.getPilotReport(fromDate);
      if (data && data.summary) {
        setReport(data);
      }
    } catch {
      // Fallback
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadCsv = () => {
    let fromDate: string | undefined;
    const now = new Date();
    if (periodFilter === "7d") {
      fromDate = new Date(now.getTime() - 7 * 86400000).toISOString();
    } else if (periodFilter === "30d") {
      fromDate = new Date(now.getTime() - 30 * 86400000).toISOString();
    }
    const url = api.reports.exportPilotCsvUrl(fromDate);
    window.open(url, "_blank");
  };

  const handleSendWeeklyEmail = async () => {
    setSendingEmail(true);
    setEmailStatus(null);
    try {
      const res = await api.reports.sendWeeklyEmail();
      setEmailStatus(res.message || "Đã xử lý gửi email báo cáo tuần thành công!");
    } catch (err: unknown) {
      setEmailStatus(`Lỗi khi gửi email: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setSendingEmail(false);
    }
  };

  const summary = report.summary;
  const maxTrendVal = Math.max(...report.daily_trends.map((t) => t.received), 1);

  return (
    <div style={{ padding: "var(--space-6) var(--space-8)", maxWidth: "1400px", margin: "0 auto" }}>
      {/* 1. Header & Quick Controls */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          flexWrap: "wrap",
          gap: "var(--space-4)",
          marginBottom: "var(--space-6)",
          paddingBottom: "var(--space-5)",
          borderBottom: "1px solid var(--line)",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                padding: "3px 10px",
                borderRadius: "9999px",
                background: "rgba(16,185,129,0.1)",
                color: "var(--color-primary)",
                fontSize: "0.6875rem",
                fontWeight: 700,
                letterSpacing: "0.05em",
                textTransform: "uppercase",
              }}
            >
              <Sparkles size={11} />
              Báo Cáo Hiệu Quả Pilot &amp; ROI
            </span>
          </div>
          <h1
            style={{
              fontSize: "1.625rem",
              fontWeight: 800,
              letterSpacing: "-0.025em",
              color: "var(--ink)",
              margin: 0,
            }}
          >
            Báo Cáo Đo Lường Pilot Vận Hành
          </h1>
          <p style={{ margin: "4px 0 0", fontSize: "0.875rem", color: "var(--muted)" }}>
            Theo dõi thời gian tiết kiệm nhân sự, tỷ lệ ngăn chặn rủi ro tài chính và độ tin cậy của 4-Tier RAG Hybrid
          </p>
        </div>

        {/* Actions bar */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          {/* Period selector */}
          <div
            style={{
              display: "inline-flex",
              background: "var(--canvas)",
              padding: "3px",
              borderRadius: "10px",
              border: "1px solid var(--line)",
            }}
          >
            {[
              { key: "7d", label: "7 ngày qua" },
              { key: "30d", label: "30 ngày qua" },
              { key: "all", label: "Toàn bộ" },
            ].map((tab) => (
              <button
                key={tab.key}
                type="button"
                onClick={() => setPeriodFilter(tab.key as "7d" | "30d" | "all")}
                style={{
                  padding: "5px 12px",
                  fontSize: "0.8125rem",
                  fontWeight: periodFilter === tab.key ? 700 : 500,
                  color: periodFilter === tab.key ? "#ffffff" : "var(--muted)",
                  background: periodFilter === tab.key ? "var(--color-primary)" : "transparent",
                  border: "none",
                  borderRadius: "7px",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <button
            type="button"
            onClick={handleRefresh}
            disabled={loading}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "7px 14px",
              fontSize: "0.8125rem",
              fontWeight: 600,
              color: "var(--ink)",
              background: "var(--paper)",
              border: "1px solid var(--line)",
              borderRadius: "8px",
              cursor: "pointer",
              boxShadow: "0 1px 2px rgba(0,0,0,0.04)",
            }}
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            Làm mới
          </button>

          <button
            type="button"
            onClick={handleDownloadCsv}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "7px 14px",
              fontSize: "0.8125rem",
              fontWeight: 600,
              color: "var(--color-primary)",
              background: "rgba(16,185,129,0.08)",
              border: "1px solid rgba(16,185,129,0.25)",
              borderRadius: "8px",
              cursor: "pointer",
            }}
          >
            <Download size={14} />
            Xuất CSV Báo cáo
          </button>

          <button
            type="button"
            onClick={handleSendWeeklyEmail}
            disabled={sendingEmail}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "7px 16px",
              fontSize: "0.8125rem",
              fontWeight: 600,
              color: "#ffffff",
              background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
              border: "none",
              borderRadius: "8px",
              cursor: "pointer",
              boxShadow: "0 2px 6px rgba(16,185,129,0.3)",
            }}
          >
            <Mail size={14} />
            {sendingEmail ? "Đang gửi..." : "Gửi Email Tuần"}
          </button>
        </div>
      </div>

      {emailStatus && (
        <div
          style={{
            marginBottom: "var(--space-5)",
            padding: "10px 16px",
            borderRadius: "10px",
            background: "rgba(16,185,129,0.1)",
            border: "1px solid rgba(16,185,129,0.3)",
            color: "var(--color-primary)",
            fontSize: "0.8125rem",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span style={{ fontWeight: 500 }}>{emailStatus}</span>
          <button
            onClick={() => setEmailStatus(null)}
            style={{ background: "none", border: "none", cursor: "pointer", fontWeight: 700 }}
          >
            ×
          </button>
        </div>
      )}

      {/* 2. Four Redesigned Hero KPI Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: "var(--space-4)",
          marginBottom: "var(--space-6)",
        }}
      >
        {/* Card 1: Time Saved */}
        <div
          style={{
            background: "var(--paper)",
            border: "1px solid var(--line)",
            borderRadius: "16px",
            padding: "20px 22px",
            boxShadow: "var(--shadow-elevation-1)",
            position: "relative",
            overflow: "hidden",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <span
                style={{
                  fontSize: "0.75rem",
                  fontWeight: 700,
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                  color: "var(--muted)",
                }}
              >
                Thời gian tiết kiệm
              </span>
              <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginTop: "6px" }}>
                <span
                  style={{
                    fontSize: "2rem",
                    fontWeight: 800,
                    letterSpacing: "-0.03em",
                    color: "var(--color-primary)",
                    lineHeight: 1,
                  }}
                >
                  {summary.estimated_hours_saved}h
                </span>
                <span style={{ fontSize: "0.8125rem", color: "var(--muted)", fontWeight: 500 }}>
                  / {summary.total_orders_received} đơn PO
                </span>
              </div>
            </div>
            <div
              style={{
                width: "42px",
                height: "42px",
                borderRadius: "12px",
                background: "rgba(16,185,129,0.12)",
                display: "grid",
                placeItems: "center",
                color: "var(--color-primary)",
              }}
            >
              <Clock size={22} />
            </div>
          </div>
          <div
            style={{
              marginTop: "14px",
              paddingTop: "12px",
              borderTop: "1px solid var(--line)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              fontSize: "0.75rem",
              color: "var(--muted)",
            }}
          >
            <span>Giảm từ 25 phút thủ công</span>
            <span style={{ fontWeight: 700, color: "var(--color-primary)" }}>xuống ~2 phút/đơn</span>
          </div>
        </div>

        {/* Card 2: Risk Blocked */}
        <div
          style={{
            background: "var(--paper)",
            border: "1px solid var(--line)",
            borderRadius: "16px",
            padding: "20px 22px",
            boxShadow: "var(--shadow-elevation-1)",
            position: "relative",
            overflow: "hidden",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <span
                style={{
                  fontSize: "0.75rem",
                  fontWeight: 700,
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                  color: "var(--muted)",
                }}
              >
                Chặn rủi ro trước ERP
              </span>
              <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginTop: "6px" }}>
                <span
                  style={{
                    fontSize: "2rem",
                    fontWeight: 800,
                    letterSpacing: "-0.03em",
                    color: "var(--color-error)",
                    lineHeight: 1,
                  }}
                >
                  {summary.orders_blocked_before_erp} đơn
                </span>
                <span style={{ fontSize: "0.8125rem", color: "var(--muted)", fontWeight: 500 }}>bị chặn lỗi</span>
              </div>
            </div>
            <div
              style={{
                width: "42px",
                height: "42px",
                borderRadius: "12px",
                background: "rgba(239,68,68,0.12)",
                display: "grid",
                placeItems: "center",
                color: "var(--color-error)",
              }}
            >
              <ShieldAlert size={22} />
            </div>
          </div>
          <div
            style={{
              marginTop: "14px",
              paddingTop: "12px",
              borderTop: "1px solid var(--line)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              fontSize: "0.75rem",
              color: "var(--muted)",
            }}
          >
            <span>Bảo vệ số liệu ERP</span>
            <span style={{ fontWeight: 700, color: "var(--color-error)" }}>Sai giá, tồn kho &amp; nợ</span>
          </div>
        </div>

        {/* Card 3: Value Processed */}
        <div
          style={{
            background: "var(--paper)",
            border: "1px solid var(--line)",
            borderRadius: "16px",
            padding: "20px 22px",
            boxShadow: "var(--shadow-elevation-1)",
            position: "relative",
            overflow: "hidden",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <span
                style={{
                  fontSize: "0.75rem",
                  fontWeight: 700,
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                  color: "var(--muted)",
                }}
              >
                Tổng giá trị tiền kiểm
              </span>
              <div style={{ marginTop: "6px" }}>
                <span
                  style={{
                    fontSize: "1.625rem",
                    fontWeight: 800,
                    letterSpacing: "-0.025em",
                    color: "var(--ink)",
                    lineHeight: 1,
                  }}
                >
                  {money(summary.total_value_processed)}
                </span>
              </div>
            </div>
            <div
              style={{
                width: "42px",
                height: "42px",
                borderRadius: "12px",
                background: "rgba(59,130,246,0.12)",
                display: "grid",
                placeItems: "center",
                color: "var(--color-info)",
              }}
            >
              <TrendingUp size={22} />
            </div>
          </div>
          <div
            style={{
              marginTop: "14px",
              paddingTop: "12px",
              borderTop: "1px solid var(--line)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              fontSize: "0.75rem",
              color: "var(--muted)",
            }}
          >
            <span>Quy mô dòng hàng</span>
            <span style={{ fontWeight: 700, color: "var(--ink)" }}>{summary.total_lines_processed} dòng hàng</span>
          </div>
        </div>

        {/* Card 4: Automation Rate */}
        <div
          style={{
            background: "var(--paper)",
            border: "1px solid var(--line)",
            borderRadius: "16px",
            padding: "20px 22px",
            boxShadow: "var(--shadow-elevation-1)",
            position: "relative",
            overflow: "hidden",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <span
                style={{
                  fontSize: "0.75rem",
                  fontWeight: 700,
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                  color: "var(--muted)",
                }}
              >
                Tỷ lệ chuẩn hóa tự động
              </span>
              <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginTop: "6px" }}>
                <span
                  style={{
                    fontSize: "2rem",
                    fontWeight: 800,
                    letterSpacing: "-0.03em",
                    color: "var(--ink)",
                    lineHeight: 1,
                  }}
                >
                  {summary.automation_rate_pct}%
                </span>
                <span style={{ fontSize: "0.8125rem", color: "var(--muted)", fontWeight: 500 }}>qua 4-Tier RAG</span>
              </div>
            </div>
            <div
              style={{
                width: "42px",
                height: "42px",
                borderRadius: "12px",
                background: "rgba(245,158,11,0.12)",
                display: "grid",
                placeItems: "center",
                color: "var(--color-warning)",
              }}
            >
              <Zap size={22} />
            </div>
          </div>
          <div
            style={{
              marginTop: "14px",
              paddingTop: "12px",
              borderTop: "1px solid var(--line)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              fontSize: "0.75rem",
              color: "var(--muted)",
            }}
          >
            <span>Chi phí AI trung bình</span>
            <span style={{ fontWeight: 700, color: "var(--ink)" }}>${summary.avg_cost_per_order_usd.toFixed(5)}/đơn</span>
          </div>
        </div>
      </div>

      {/* 3. Main Dashboard Grid (Polished SVG Trends + Business Findings) */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(480px, 1fr))",
          gap: "var(--space-6)",
          marginBottom: "var(--space-6)",
        }}
      >
        {/* Modern Bar Chart */}
        <div
          style={{
            background: "var(--paper)",
            border: "1px solid var(--line)",
            borderRadius: "16px",
            padding: "24px",
            boxShadow: "var(--shadow-elevation-1)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "20px" }}>
            <div>
              <h2 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--ink)", margin: 0 }}>
                Xu Hướng Tiếp Nhận &amp; Phê Duyệt Đơn Hàng
              </h2>
              <p style={{ fontSize: "0.8125rem", color: "var(--muted)", margin: "4px 0 0" }}>
                Số lượng đơn phân bổ theo ngày tiếp nhận và phân loại kết quả kiểm toán
              </p>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "16px", fontSize: "0.75rem", fontWeight: 600 }}>
              <span style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--ink)" }}>
                <span style={{ width: "10px", height: "10px", borderRadius: "3px", background: "#10b981" }} />
                Đạt chuẩn / Đã duyệt
              </span>
              <span style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--ink)" }}>
                <span style={{ width: "10px", height: "10px", borderRadius: "3px", background: "#ef4444" }} />
                Phát hiện lỗi / Bị chặn
              </span>
            </div>
          </div>

          <div style={{ position: "relative", width: "100%", height: "240px" }}>
            <svg viewBox="0 0 540 220" style={{ width: "100%", height: "100%", overflow: "visible" }}>
              <defs>
                <linearGradient id="barApprovedGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10b981" />
                  <stop offset="100%" stopColor="#059669" />
                </linearGradient>
                <linearGradient id="barBlockedGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#ef4444" />
                  <stop offset="100%" stopColor="#dc2626" />
                </linearGradient>
              </defs>

              {/* Grid Lines */}
              {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => {
                const y = 175 - ratio * 135;
                return (
                  <g key={i}>
                    <line x1="30" y1={y} x2="520" y2={y} stroke="var(--line)" strokeDasharray="3 3" opacity="0.7" />
                    <text x="22" y={y + 3} fontSize="10" fill="var(--muted)" textAnchor="end" fontWeight="500">
                      {Math.round(ratio * maxTrendVal)}
                    </text>
                  </g>
                );
              })}

              {/* Data Bars */}
              {report.daily_trends.map((item, idx) => {
                const totalBars = report.daily_trends.length;
                const chartWidth = 480;
                const slotWidth = chartWidth / totalBars;
                const barWidth = 32;
                const x = 35 + idx * slotWidth + (slotWidth - barWidth) / 2;

                const approvedHeight = (item.approved / maxTrendVal) * 135;
                const blockedHeight = (item.blocked / maxTrendVal) * 135;
                const totalHeight = approvedHeight + blockedHeight;

                const yApproved = 175 - approvedHeight;
                const yBlocked = yApproved - blockedHeight;

                return (
                  <g key={item.date} className="chart-bar-group">
                    {/* Background Column Track */}
                    <rect
                      x={x - 4}
                      y={40}
                      width={barWidth + 8}
                      height={135}
                      rx="8"
                      fill="var(--line)"
                      opacity="0.25"
                    />

                    {/* Approved Part */}
                    <rect
                      x={x}
                      y={yApproved}
                      width={barWidth}
                      height={approvedHeight}
                      rx={item.blocked > 0 ? "0" : "6"}
                      fill="url(#barApprovedGrad)"
                    />

                    {/* Blocked Part */}
                    {item.blocked > 0 && (
                      <rect
                        x={x}
                        y={yBlocked}
                        width={barWidth}
                        height={blockedHeight}
                        rx="6"
                        fill="url(#barBlockedGrad)"
                      />
                    )}

                    {/* Top Total Count */}
                    <text
                      x={x + barWidth / 2}
                      y={175 - totalHeight - 8}
                      fontSize="11"
                      textAnchor="middle"
                      fontWeight="800"
                      fill="var(--ink)"
                    >
                      {item.received}
                    </text>

                    {/* Date Label */}
                    <text
                      x={x + barWidth / 2}
                      y="196"
                      fontSize="11"
                      textAnchor="middle"
                      fill="var(--muted)"
                      fontWeight="600"
                    >
                      {item.date.slice(5)}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        </div>

        {/* Business Friendly Findings Distribution */}
        <div
          style={{
            background: "var(--paper)",
            border: "1px solid var(--line)",
            borderRadius: "16px",
            padding: "24px",
            boxShadow: "var(--shadow-elevation-1)",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
          }}
        >
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
              <div>
                <h2 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--ink)", margin: 0 }}>
                  Phân Bổ Vi Phạm &amp; Cảnh Báo Quy Tắc
                </h2>
                <p style={{ fontSize: "0.8125rem", color: "var(--muted)", margin: "4px 0 0" }}>
                  Phân loại trực quan các vi phạm nghiệp vụ phát hiện tự động bởi Rules Engine
                </p>
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "14px", marginTop: "12px" }}>
              {Object.entries(report.findings_distribution).map(([code, count]) => {
                const meta = FINDING_METADATA[code] || {
                  label: code.replace(/_/g, " "),
                  desc: "Quy tắc kiểm soát tự động",
                  severity: "warning",
                };
                const maxCount = Math.max(...Object.values(report.findings_distribution), 1);
                const pct = Math.round((count / maxCount) * 100);
                const isCritical = meta.severity === "critical";

                return (
                  <div key={code} style={{ display: "flex", flexDirection: "column", gap: "5px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <span
                          style={{
                            display: "inline-block",
                            width: "7px",
                            height: "7px",
                            borderRadius: "50%",
                            background: isCritical ? "#ef4444" : "#f59e0b",
                          }}
                        />
                        <span style={{ fontSize: "0.8125rem", fontWeight: 700, color: "var(--ink)" }}>
                          {meta.label}
                        </span>
                        <code
                          style={{
                            fontSize: "0.6875rem",
                            padding: "2px 6px",
                            borderRadius: "4px",
                            background: "var(--canvas)",
                            border: "1px solid var(--line)",
                            color: "var(--muted)",
                          }}
                        >
                          {code}
                        </code>
                      </div>
                      <span style={{ fontSize: "0.8125rem", fontWeight: 700, color: "var(--ink)" }}>
                        {count} lần <span style={{ color: "var(--muted)", fontWeight: 500 }}>({pct}%)</span>
                      </span>
                    </div>

                    <div
                      style={{
                        height: "7px",
                        width: "100%",
                        borderRadius: "9999px",
                        background: "var(--line)",
                        overflow: "hidden",
                      }}
                    >
                      <div
                        style={{
                          height: "100%",
                          width: `${pct}%`,
                          borderRadius: "9999px",
                          background: isCritical
                            ? "linear-gradient(90deg, #ef4444 0%, #dc2626 100%)"
                            : "linear-gradient(90deg, #f59e0b 0%, #d97706 100%)",
                          transition: "width 0.4s ease",
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 4-Tier RAG Waterfall Status Strip */}
          <div style={{ marginTop: "24px", paddingTop: "16px", borderTop: "1px solid var(--line)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
              <span style={{ fontSize: "0.8125rem", fontWeight: 700, color: "var(--ink)" }}>
                Hiệu Suất Khớp Mã 4-Tier Waterfall RAG
              </span>
              <span style={{ fontSize: "0.75rem", color: "var(--muted)" }}>Tỉ lệ giải quyết SKU</span>
            </div>

            {/* Segmented bar */}
            <div
              style={{
                display: "flex",
                height: "10px",
                borderRadius: "9999px",
                overflow: "hidden",
                gap: "2px",
                background: "var(--line)",
              }}
            >
              <div
                style={{ width: `${report.rag_tier_breakdown.exact_hash}%`, background: "#059669" }}
                title={`Tier 1 Exact Hash: ${report.rag_tier_breakdown.exact_hash}%`}
              />
              <div
                style={{ width: `${report.rag_tier_breakdown.lexical_fuzzy}%`, background: "#0d9488" }}
                title={`Tier 2 Lexical Fuzzy: ${report.rag_tier_breakdown.lexical_fuzzy}%`}
              />
              <div
                style={{ width: `${report.rag_tier_breakdown.semantic_vector}%`, background: "#3b82f6" }}
                title={`Tier 3 Semantic Vector: ${report.rag_tier_breakdown.semantic_vector}%`}
              />
              <div
                style={{ width: `${report.rag_tier_breakdown.llm_fallback}%`, background: "#f59e0b" }}
                title={`Tier 4 LLM Fallback: ${report.rag_tier_breakdown.llm_fallback}%`}
              />
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(4, 1fr)",
                gap: "8px",
                marginTop: "10px",
                fontSize: "0.6875rem",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
                <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#059669" }} />
                <span style={{ color: "var(--muted)" }}>Tier 1 Exact: <strong>{report.rag_tier_breakdown.exact_hash}%</strong></span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
                <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#0d9488" }} />
                <span style={{ color: "var(--muted)" }}>Tier 2 Fuzzy: <strong>{report.rag_tier_breakdown.lexical_fuzzy}%</strong></span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
                <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#3b82f6" }} />
                <span style={{ color: "var(--muted)" }}>Tier 3 Vector: <strong>{report.rag_tier_breakdown.semantic_vector}%</strong></span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
                <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#f59e0b" }} />
                <span style={{ color: "var(--muted)" }}>Tier 4 LLM: <strong>{report.rag_tier_breakdown.llm_fallback}%</strong></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Orders Sample Table */}
      <div
        style={{
          background: "var(--paper)",
          border: "1px solid var(--line)",
          borderRadius: "16px",
          padding: "24px",
          boxShadow: "var(--shadow-elevation-1)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px" }}>
          <div>
            <h2 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--ink)", margin: 0 }}>
              Chi Tiết Đơn Hàng Mẫu Trong Kỳ Đo Lường
            </h2>
            <p style={{ fontSize: "0.8125rem", color: "var(--muted)", margin: "4px 0 0" }}>
              Thời gian đối soát thực tế và chi phí AI trên từng đơn đặt hàng
            </p>
          </div>
          <span
            style={{
              fontSize: "0.75rem",
              fontWeight: 600,
              padding: "4px 10px",
              borderRadius: "6px",
              background: "var(--canvas)",
              color: "var(--muted)",
              border: "1px solid var(--line)",
            }}
          >
            Hiển thị {report.orders_sample.length} đơn mẫu
          </span>
        </div>

        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.8125rem" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--line)", color: "var(--muted)", fontSize: "0.75rem" }}>
                <th style={{ padding: "10px 12px", fontWeight: 700 }}>Mã PO</th>
                <th style={{ padding: "10px 12px", fontWeight: 700 }}>Khách hàng</th>
                <th style={{ padding: "10px 12px", fontWeight: 700 }}>Ngày tiếp nhận</th>
                <th style={{ padding: "10px 12px", fontWeight: 700 }}>Trạng thái</th>
                <th style={{ padding: "10px 12px", fontWeight: 700, textAlign: "right" }}>Giá trị đơn</th>
                <th style={{ padding: "10px 12px", fontWeight: 700, textAlign: "center" }}>Số dòng</th>
                <th style={{ padding: "10px 12px", fontWeight: 700, textAlign: "center" }}>Cảnh báo</th>
                <th style={{ padding: "10px 12px", fontWeight: 700, textAlign: "right" }}>Thời gian xử lý</th>
                <th style={{ padding: "10px 12px", fontWeight: 700, textAlign: "right" }}>Chi phí AI</th>
              </tr>
            </thead>
            <tbody>
              {report.orders_sample.map((o) => (
                <tr
                  key={o.po_number}
                  style={{
                    borderBottom: "1px solid var(--line)",
                    transition: "background 0.15s ease",
                  }}
                >
                  <td style={{ padding: "12px", fontFamily: "var(--font-geist-mono), monospace", fontWeight: 700, color: "var(--ink)" }}>
                    {o.po_number}
                  </td>
                  <td style={{ padding: "12px", fontWeight: 600, color: "var(--ink)" }}>
                    {o.customer}
                  </td>
                  <td style={{ padding: "12px", color: "var(--muted)" }}>
                    {o.created_at ? o.created_at.slice(0, 10) : "—"}
                  </td>
                  <td style={{ padding: "12px" }}>
                    <span
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "4px",
                        padding: "3px 8px",
                        borderRadius: "6px",
                        fontSize: "0.6875rem",
                        fontWeight: 700,
                        background:
                          o.status === "blocked"
                            ? "rgba(239,68,68,0.12)"
                            : o.status === "review_required"
                            ? "rgba(245,158,11,0.12)"
                            : "rgba(16,185,129,0.12)",
                        color:
                          o.status === "blocked"
                            ? "#ef4444"
                            : o.status === "review_required"
                            ? "#d97706"
                            : "#059669",
                      }}
                    >
                      {o.status === "blocked" ? "Bị chặn (Blocked)" : o.status === "review_required" ? "Cần duyệt (Review)" : "Sẵn sàng (Ready)"}
                    </span>
                  </td>
                  <td style={{ padding: "12px", textAlign: "right", fontWeight: 700, color: "var(--ink)", fontVariantNumeric: "tabular-nums" }}>
                    {money(o.total, o.currency)}
                  </td>
                  <td style={{ padding: "12px", textAlign: "center", color: "var(--muted)" }}>
                    {o.lines_count}
                  </td>
                  <td style={{ padding: "12px", textAlign: "center" }}>
                    {o.findings_count > 0 ? (
                      <span
                        style={{
                          padding: "2px 7px",
                          borderRadius: "9999px",
                          background: "rgba(245,158,11,0.15)",
                          color: "#d97706",
                          fontWeight: 700,
                          fontSize: "0.6875rem",
                        }}
                      >
                        {o.findings_count}
                      </span>
                    ) : (
                      <span style={{ color: "var(--muted)" }}>0</span>
                    )}
                  </td>
                  <td style={{ padding: "12px", textAlign: "right", color: "var(--muted)", fontVariantNumeric: "tabular-nums" }}>
                    {o.decision_minutes ? `${o.decision_minutes}m` : "—"}
                  </td>
                  <td style={{ padding: "12px", textAlign: "right", color: "var(--muted)", fontFamily: "var(--font-geist-mono), monospace" }}>
                    ${o.cost_usd.toFixed(5)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
