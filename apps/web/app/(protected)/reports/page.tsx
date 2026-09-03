"use client";

import React, { useEffect, useState } from "react";
import {
  BarChart3,
  Clock,
  Download,
  Mail,
  RefreshCw,
  ShieldAlert,
  TrendingUp,
  Zap,
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
        // Fallback to seeded demo report on connection error
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
    <div className="space-y-6 pb-12">
      {/* Header & Actions */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b pb-4">
        <div>
          <div className="flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-[var(--green)]" />
            <h1 className="text-xl font-bold tracking-tight text-[var(--ink)]">
              Báo Cáo Đo Lường Pilot Vận Hành
            </h1>
          </div>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Theo dõi thời gian tiết kiệm, tỷ lệ chặn lỗi trước ERP và độ tin cậy của 4-Tier RAG Hybrid
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Period selector */}
          <div className="inline-flex rounded-lg border bg-[var(--paper)] p-1 text-xs">
            <button
              onClick={() => setPeriodFilter("7d")}
              className={`rounded px-2.5 py-1 font-medium transition-colors ${
                periodFilter === "7d"
                  ? "bg-[var(--green)] text-white"
                  : "text-[var(--muted)] hover:text-[var(--ink)]"
              }`}
            >
              7 ngày qua
            </button>
            <button
              onClick={() => setPeriodFilter("30d")}
              className={`rounded px-2.5 py-1 font-medium transition-colors ${
                periodFilter === "30d"
                  ? "bg-[var(--green)] text-white"
                  : "text-[var(--muted)] hover:text-[var(--ink)]"
              }`}
            >
              30 ngày qua
            </button>
            <button
              onClick={() => setPeriodFilter("all")}
              className={`rounded px-2.5 py-1 font-medium transition-colors ${
                periodFilter === "all"
                  ? "bg-[var(--green)] text-white"
                  : "text-[var(--muted)] hover:text-[var(--ink)]"
              }`}
            >
              Toàn thời gian
            </button>
          </div>

          <button
            onClick={handleRefresh}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-lg border bg-[var(--paper)] px-3 py-1.5 text-xs font-medium text-[var(--ink)] hover:bg-[var(--canvas)]"
            title="Làm mới"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Làm mới
          </button>

          <button
            onClick={handleDownloadCsv}
            className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--green)] bg-[var(--green-soft)] px-3 py-1.5 text-xs font-medium text-[var(--green)] hover:opacity-90"
          >
            <Download className="h-3.5 w-3.5" />
            Xuất CSV Báo cáo
          </button>

          <button
            onClick={handleSendWeeklyEmail}
            disabled={sendingEmail}
            className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--green)] px-3 py-1.5 text-xs font-medium text-white hover:opacity-90"
          >
            <Mail className="h-3.5 w-3.5" />
            {sendingEmail ? "Đang gửi..." : "Gửi Email Tuần"}
          </button>
        </div>
      </div>

      {emailStatus && (
        <div className="rounded-lg border border-[var(--green)] bg-[var(--green-soft)] p-3 text-xs text-[var(--green)] flex items-center justify-between">
          <span>{emailStatus}</span>
          <button onClick={() => setEmailStatus(null)} className="font-bold ml-2">×</button>
        </div>
      )}

      {/* 4 Hero KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border bg-[var(--paper)] p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[var(--muted)] uppercase">Thời gian tiết kiệm</span>
            <div className="rounded-lg bg-[var(--green-soft)] p-2 text-[var(--green)]">
              <Clock className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-[var(--green)]">
              {summary.estimated_hours_saved}h
            </span>
            <span className="text-xs text-[var(--muted)]">/ {summary.total_orders_received} đơn</span>
          </div>
          <p className="mt-1 text-xs text-[var(--muted)]">
            Giảm từ 25 phút thủ công xuống ~2 phút/đơn
          </p>
        </div>

        <div className="rounded-xl border bg-[var(--paper)] p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[var(--muted)] uppercase">Chặn sai sót trước ERP</span>
            <div className="rounded-lg bg-[var(--red-soft)] p-2 text-[var(--red)]">
              <ShieldAlert className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-[var(--red)]">
              {summary.orders_blocked_before_erp} đơn
            </span>
            <span className="text-xs text-[var(--muted)]">ngăn chặn rủi ro</span>
          </div>
          <p className="mt-1 text-xs text-[var(--muted)]">
            Sai giá, hết tồn kho & vượt hạn mức tín dụng
          </p>
        </div>

        <div className="rounded-xl border bg-[var(--paper)] p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[var(--muted)] uppercase">Tổng giá trị xử lý</span>
            <div className="rounded-lg bg-[var(--blue-soft)] p-2 text-[var(--blue)]">
              <TrendingUp className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-xl font-bold text-[var(--ink)]">
              {money(summary.total_value_processed)}
            </span>
          </div>
          <p className="mt-1 text-xs text-[var(--muted)]">
            Tổng cộng {summary.total_lines_processed} dòng hàng đã rà soát
          </p>
        </div>

        <div className="rounded-xl border bg-[var(--paper)] p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[var(--muted)] uppercase">Chuẩn hóa tự động</span>
            <div className="rounded-lg bg-[var(--amber-soft)] p-2 text-[var(--amber)]">
              <Zap className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-[var(--ink)]">
              {summary.automation_rate_pct}%
            </span>
            <span className="text-xs text-[var(--muted)]">qua 4-Tier RAG</span>
          </div>
          <p className="mt-1 text-xs text-[var(--muted)]">
            Chi phí AI trung bình: ${summary.avg_cost_per_order_usd.toFixed(5)}/đơn
          </p>
        </div>
      </div>

      {/* SVG Charts Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Daily Orders Trend Bar Chart */}
        <div className="rounded-xl border bg-[var(--paper)] p-5 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-[var(--ink)]">Xu Hướng Tiếp Nhận Đơn Hàng</h2>
              <p className="text-xs text-[var(--muted)]">Số lượng đơn hàng phân theo ngày và kết quả duyệt</p>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-[var(--green)]"></span> Duyệt
              </span>
              <span className="flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-[var(--red)]"></span> Bị chặn
              </span>
            </div>
          </div>

          <div className="relative h-56 w-full pt-4">
            <svg className="h-full w-full overflow-visible" viewBox="0 0 500 200">
              {/* Horizontal Grid lines */}
              {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => {
                const y = 180 - ratio * 150;
                return (
                  <g key={i}>
                    <line x1="0" y1={y} x2="500" y2={y} stroke="var(--line)" strokeDasharray="3 3" />
                    <text x="0" y={y - 4} fontSize="10" fill="var(--faint)">
                      {Math.round(ratio * maxTrendVal)}
                    </text>
                  </g>
                );
              })}

              {/* Bars */}
              {report.daily_trends.map((item, idx) => {
                const totalBars = report.daily_trends.length;
                const slotWidth = 500 / totalBars;
                const barWidth = 28;
                const x = idx * slotWidth + (slotWidth - barWidth) / 2;

                const approvedHeight = (item.approved / maxTrendVal) * 150;
                const blockedHeight = (item.blocked / maxTrendVal) * 150;
                const totalHeight = (item.received / maxTrendVal) * 150;

                const yApproved = 180 - approvedHeight;
                const yBlocked = yApproved - blockedHeight;

                return (
                  <g key={item.date} className="group cursor-pointer">
                    {/* Approved segment */}
                    <rect
                      x={x}
                      y={yApproved}
                      width={barWidth}
                      height={approvedHeight}
                      rx="3"
                      fill="var(--green)"
                      opacity="0.9"
                    />
                    {/* Blocked segment */}
                    {item.blocked > 0 && (
                      <rect
                        x={x}
                        y={yBlocked}
                        width={barWidth}
                        height={blockedHeight}
                        rx="3"
                        fill="var(--red)"
                        opacity="0.9"
                      />
                    )}
                    {/* Date label */}
                    <text
                      x={x + barWidth / 2}
                      y="196"
                      fontSize="10"
                      textAnchor="middle"
                      fill="var(--muted)"
                    >
                      {item.date.slice(5)}
                    </text>
                    {/* Top total label */}
                    <text
                      x={x + barWidth / 2}
                      y={180 - totalHeight - 6}
                      fontSize="10"
                      textAnchor="middle"
                      fontWeight="bold"
                      fill="var(--ink)"
                    >
                      {item.received}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        </div>

        {/* Findings Distribution */}
        <div className="rounded-xl border bg-[var(--paper)] p-5 shadow-xs">
          <div className="mb-4">
            <h2 className="text-sm font-semibold text-[var(--ink)]">Phân Bổ Vi Phạm & Cảnh Báo Quy Tắc</h2>
            <p className="text-xs text-[var(--muted)]">Tần suất vi phạm phát hiện tự động bởi Rules Engine</p>
          </div>

          <div className="space-y-3 pt-2">
            {Object.entries(report.findings_distribution).map(([code, count]) => {
              const maxCount = Math.max(...Object.values(report.findings_distribution), 1);
              const pct = Math.round((count / maxCount) * 100);
              const isError = ["PRICE_MISMATCH", "INSUFFICIENT_STOCK", "CREDIT_LIMIT_EXCEEDED"].includes(code);

              return (
                <div key={code} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono font-medium text-[var(--ink)]">{code}</span>
                    <span className="font-semibold text-[var(--muted)]">{count} lần ({pct}%)</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-[var(--canvas)] overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        isError ? "bg-[var(--red)]" : "bg-[var(--amber)]"
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {/* RAG Waterfall 4-Tier Breakdown */}
          <div className="mt-6 border-t pt-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-[var(--ink)]">Hiệu Suất 4-Tier Waterfall RAG</span>
              <span className="text-xs text-[var(--muted)]">Tỉ lệ giải quyết SKU</span>
            </div>
            <div className="flex h-3 w-full rounded-full overflow-hidden">
              <div
                style={{ width: `${report.rag_tier_breakdown.exact_hash}%` }}
                className="bg-emerald-600"
                title={`Exact Hash: ${report.rag_tier_breakdown.exact_hash}%`}
              />
              <div
                style={{ width: `${report.rag_tier_breakdown.lexical_fuzzy}%` }}
                className="bg-teal-500"
                title={`Lexical Fuzzy: ${report.rag_tier_breakdown.lexical_fuzzy}%`}
              />
              <div
                style={{ width: `${report.rag_tier_breakdown.semantic_vector}%` }}
                className="bg-blue-500"
                title={`Semantic Vector: ${report.rag_tier_breakdown.semantic_vector}%`}
              />
              <div
                style={{ width: `${report.rag_tier_breakdown.llm_fallback}%` }}
                className="bg-amber-500"
                title={`LLM Fallback: ${report.rag_tier_breakdown.llm_fallback}%`}
              />
            </div>
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
              <div className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-600"></span>
                <span className="text-[var(--muted)]">Tier 1 Exact: {report.rag_tier_breakdown.exact_hash}%</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-teal-500"></span>
                <span className="text-[var(--muted)]">Tier 2 Fuzzy: {report.rag_tier_breakdown.lexical_fuzzy}%</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-blue-500"></span>
                <span className="text-[var(--muted)]">Tier 3 Vector: {report.rag_tier_breakdown.semantic_vector}%</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-amber-500"></span>
                <span className="text-[var(--muted)]">Tier 4 LLM: {report.rag_tier_breakdown.llm_fallback}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Orders Sample Table */}
      <div className="rounded-xl border bg-[var(--paper)] p-5 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-semibold text-[var(--ink)]">Chi Tiết Đơn Hàng Mẫu Trong Kỳ Đo Lường</h2>
            <p className="text-xs text-[var(--muted)]">Thời gian xử lý và chi phí AI thực tế trên từng đơn đặt hàng</p>
          </div>
          <span className="text-xs text-[var(--muted)]">
            Hiển thị {report.orders_sample.length} đơn
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b text-[var(--muted)]">
                <th className="pb-2 font-medium">Mã PO</th>
                <th className="pb-2 font-medium">Khách hàng</th>
                <th className="pb-2 font-medium">Ngày tiếp nhận</th>
                <th className="pb-2 font-medium">Trạng thái</th>
                <th className="pb-2 font-medium text-right">Giá trị</th>
                <th className="pb-2 font-medium text-center">Số dòng</th>
                <th className="pb-2 font-medium text-center">Cảnh báo</th>
                <th className="pb-2 font-medium text-right">Thời gian xử lý</th>
                <th className="pb-2 font-medium text-right">Chi phí AI</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {report.orders_sample.map((o) => (
                <tr key={o.po_number} className="hover:bg-[var(--canvas)]">
                  <td className="py-2.5 font-mono font-medium text-[var(--ink)]">{o.po_number}</td>
                  <td className="py-2.5 text-[var(--ink)]">{o.customer}</td>
                  <td className="py-2.5 text-[var(--muted)]">{o.created_at ? o.created_at.slice(0, 10) : "—"}</td>
                  <td className="py-2.5">
                    <span
                      className={`inline-flex items-center rounded px-1.5 py-0.5 text-[11px] font-medium ${
                        o.status === "blocked"
                          ? "bg-[var(--red-soft)] text-[var(--red)]"
                          : o.status === "review_required"
                          ? "bg-[var(--amber-soft)] text-[var(--amber)]"
                          : "bg-[var(--green-soft)] text-[var(--green)]"
                      }`}
                    >
                      {o.status}
                    </span>
                  </td>
                  <td className="py-2.5 text-right font-medium text-[var(--ink)]">
                    {money(o.total, o.currency)}
                  </td>
                  <td className="py-2.5 text-center text-[var(--muted)]">{o.lines_count}</td>
                  <td className="py-2.5 text-center text-[var(--muted)]">{o.findings_count}</td>
                  <td className="py-2.5 text-right text-[var(--muted)]">
                    {o.decision_minutes ? `${o.decision_minutes}m` : "—"}
                  </td>
                  <td className="py-2.5 text-right font-mono text-[var(--muted)]">
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
