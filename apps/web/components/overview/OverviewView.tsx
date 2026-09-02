"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, AlertTriangle, XCircle, Plus, CheckCircle2 } from "lucide-react";
import { useAppState } from "@/components/app/AppStateProvider";
import { money } from "@/app/lib/derive";
import { useRipple } from "@/app/lib/useRipple";
import { api } from "@/app/lib/api/client";
import type { DashboardStats } from "@/app/lib/api/types";

export function OverviewView() {
  const { orders } = useAppState();
  const { createRipple } = useRipple();
  const [stats, setStats] = useState<DashboardStats | null>(null);

  useEffect(() => {
    let mounted = true;
    api.dashboard
      .getStats()
      .then((s) => {
        if (mounted) setStats(s);
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, [orders]);

  const attention = orders.filter(
    (order) => order.status === "Review required" || order.status === "Blocked",
  );

  const attentionCount = attention.length;
  const headline =
    attentionCount === 0
      ? "Không có đơn cần xử lý"
      : `${attentionCount} đơn hàng cần xử lý`;

  const straightThroughRate =
    stats?.straight_through_rate != null ? `${stats.straight_through_rate}%` : "—";

  const trend7Days = stats?.orders_last_7_days || [0, 0, 0, 0, 0, 0, orders.length];
  const maxTrend = Math.max(...trend7Days, 1);
  const daysOfWeek = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];

  return (
    <div className="page simple-page page-enter">
      <div className="page-heading">
        <div>
          <p className="eyebrow">TỔNG QUAN VẬN HÀNH · Operations overview</p>
          <h1>Bảng điều khiển hệ thống (Operations overview)</h1>
          <p>
            {attentionCount === 0
              ? "Tất cả đơn hàng đang vận hành thông suốt và tuân thủ các quy tắc định trước."
              : `Hiện có ${attentionCount} đơn hàng cần kiểm tra và giải quyết ngoại lệ.`}
          </p>
        </div>
        <Link
          className="primary-button interactive"
          href="/orders"
          onClick={createRipple}
          style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-1)" }}
        >
          <Plus size={16} strokeWidth={2.2} />
          <span>Tải lên đơn hàng (PO)</span>
        </Link>
      </div>

      <div className="overview-hero">
        <div>
          <span className="overview-label">TRỌNG TÂM HÔM NAY</span>
          <h2>{headline}</h2>
          <p>
            {attentionCount > 0
              ? "Rà soát các cảnh báo về chênh lệch giá, số lượng vượt tồn kho hoặc thông tin mã SKU chưa khớp."
              : "Không có lỗi chặn hoặc cảnh báo vi phạm. Các đơn hàng mới sẽ tự động qua kiểm định."}
          </p>
          <Link
            className="light-button interactive"
            href="/orders"
            onClick={createRipple}
            style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-1)" }}
          >
            <span>Xem danh sách đơn hàng</span>
            <ArrowRight size={14} strokeWidth={2} />
          </Link>
        </div>
        <div className="radial">
          <strong>{straightThroughRate}</strong>
          <span>
            Tỷ lệ duyệt
            <br />
            tự động
          </span>
        </div>
      </div>

      <div className="overview-columns">
        <section className="content-card">
          <div className="card-heading">
            <div>
              <h2>Hàng đợi cần chú ý (Attention queue)</h2>
              <p>Sắp xếp theo mức độ tác động kinh doanh</p>
            </div>
            <Link href="/orders" className="text-button interactive" onClick={createRipple}>
              Xem tất cả ({attentionCount})
            </Link>
          </div>
          {attention.length > 0 ? (
            attention.slice(0, 5).map((order) => (
              <Link
                className="attention-row interactive"
                key={order.id}
                href="/orders"
                onClick={createRipple}
              >
                <span
                  className={`attention-icon ${order.status === "Blocked" ? "red" : "amber"}`}
                  style={{ display: "flex", alignItems: "center", justifyContent: "center" }}
                >
                  {order.status === "Blocked" ? (
                    <XCircle size={16} strokeWidth={2.2} />
                  ) : (
                    <AlertTriangle size={15} strokeWidth={2.2} />
                  )}
                </span>
                <span>
                  <strong>
                    {order.id} · {order.customer}
                  </strong>
                  <small>
                    {order.findings.length} phát hiện cảnh báo kiểm tra
                  </small>
                </span>
                <b className="tabular-nums">{money(order.value, order.currency)}</b>
                <ArrowRight size={14} strokeWidth={1.75} style={{ opacity: 0.6 }} />
              </Link>
            ))
          ) : (
            <div style={{ padding: "var(--space-6)", textAlign: "center", color: "var(--color-outline)" }}>
              <CheckCircle2 size={32} color="#10b981" style={{ margin: "0 auto var(--space-2)" }} />
              <p>Không có đơn hàng nào cần xử lý gấp.</p>
            </div>
          )}
        </section>

        <section className="content-card">
          <div className="card-heading">
            <div>
              <h2>Luồng xử lý 7 ngày qua (Weekly flow)</h2>
              <p>Số lượng đơn hàng tiếp nhận theo ngày</p>
            </div>
            <span className="positive">Tổng {trend7Days.reduce((a, b) => a + b, 0)} đơn</span>
          </div>
          <div className="bar-chart">
            {trend7Days.map((val, idx) => (
              <div key={idx}>
                <i
                  className={idx === 6 ? "today" : ""}
                  style={{ height: `${Math.max(12, Math.round((val / maxTrend) * 100))}%` }}
                />
                <small>{daysOfWeek[idx] || `N-${6 - idx}`}</small>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
