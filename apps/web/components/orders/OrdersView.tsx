"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Search,
  Plus,
  Split,
  Check,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Info,
  FileText,
  User,
  RotateCw,
  AlertCircle,
  Mail,
} from "lucide-react";

import type { DecisionType, OrderStatus, PurchaseOrder } from "@/app/lib/types";
import { useAppState } from "@/components/app/AppStateProvider";
import { money } from "@/app/lib/derive";
import { StatusBadge } from "@/components/common/StatusBadge";
import { SubmittedAt } from "@/components/common/SubmittedAt";
import { UploadModal } from "@/components/orders/UploadModal";
import { DecisionModal } from "@/components/orders/DecisionModal";
import { SideBySideViewer } from "@/components/orders/SideBySideViewer";
import { useRipple } from "@/app/lib/useRipple";
import { api, describeError } from "@/app/lib/api/client";
import type { DashboardStats } from "@/app/lib/api/types";

export function OrdersView() {
  const { orders, isLoading, error, refreshOrders } = useAppState();
  const { createRipple } = useRipple();

  const [selectedId, setSelectedId] = useState<string>("");
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<"All" | OrderStatus>("All");
  const [uploadOpen, setUploadOpen] = useState(false);
  const [decisionOpen, setDecisionOpen] = useState(false);
  const [decisionAction, setDecisionAction] = useState<DecisionType>("APPROVE");
  const [sideBySideOpen, setSideBySideOpen] = useState(false);
  const [decisionNote, setDecisionNote] = useState("");
  const [toast, setToast] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);

  const loadStats = useCallback(async () => {
    try {
      const s = await api.dashboard.getStats();
      setStats(s);
    } catch {
      // Keep previous stats
    }
  }, []);

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

  const filteredOrders = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return orders.filter((order) => {
      const matchesText =
        !normalized ||
        `${order.id} ${order.customer}`.toLowerCase().includes(normalized);
      const matchesFilter = filter === "All" || order.status === filter;
      return matchesText && matchesFilter;
    });
  }, [filter, orders, query]);

  const selected = useMemo(() => {
    if (selectedId) {
      const found = orders.find((o) => o.id === selectedId);
      if (found) return found;
    }
    return orders[0];
  }, [orders, selectedId]);

  const attentionCount = orders.filter(
    (order) => order.status === "Review required" || order.status === "Blocked",
  ).length;

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ type, message });
    window.setTimeout(() => setToast(null), 4000);
  };

  const handleDecisionConfirm = async (action: DecisionType) => {
    if (!selected) return;

    const backendDecisionMap: Record<DecisionType, string> = {
      APPROVE: "approved",
      REJECT: "rejected",
      REQUEST_CHANGES: "needs_changes",
    };

    try {
      await api.orders.decide(selected.id, {
        decision: backendDecisionMap[action],
        note: decisionNote.trim(),
      });
      await refreshOrders();
      await loadStats();
      setDecisionOpen(false);
      setDecisionNote("");
      showToast(
        action === "APPROVE"
          ? `Đơn hàng ${selected.id} đã được phê duyệt và ghi nhận vào sổ cái kiểm toán.`
          : action === "REJECT"
            ? `Đã từ chối đơn hàng ${selected.id}.`
            : `Đã chuyển trạng thái yêu cầu sửa đổi cho đơn hàng ${selected.id}.`,
        "success",
      );
    } catch (err) {
      showToast(describeError(err), "error");
    }
  };

  const openDecisionModal = (action: DecisionType) => {
    setDecisionAction(action);
    setDecisionNote("");
    setDecisionOpen(true);
  };

  if (error && orders.length === 0) {
    return (
      <div className="page orders-page page-enter">
        <div className="page-heading">
          <div>
            <p className="eyebrow">QUẢN LÝ ĐƠN HÀNG</p>
            <h1>Đơn đặt hàng (Purchase Orders)</h1>
          </div>
        </div>
        <div
          className="content-card"
          style={{
            padding: "var(--space-8)",
            textAlign: "center",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "var(--space-3)",
          }}
        >
          <AlertCircle size={40} color="#ef4444" />
          <h2>Không kết nối được máy chủ</h2>
          <p style={{ color: "var(--color-outline)", maxWidth: 460 }}>{error}</p>
          <button
            className="primary-button interactive"
            onClick={() => void refreshOrders()}
            style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-1)", marginTop: "var(--space-2)" }}
          >
            <RotateCw size={16} />
            <span>Thử lại kết nối</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="page orders-page page-enter">
      <div className="page-heading">
        <div>
          <p className="eyebrow">QUẢN LÝ ĐƠN HÀNG · Purchase orders</p>
          <h1>Đơn đặt hàng (Purchase orders)</h1>
          <p>Kiểm tra dữ liệu bóc tách, rà soát cảnh báo vi phạm và thực hiện quyết định phê duyệt.</p>
        </div>
        <button
          className="primary-button interactive"
          onClick={(e) => {
            createRipple(e);
            setUploadOpen(true);
          }}
          style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-1)" }}
        >
          <Plus size={16} strokeWidth={2.2} aria-hidden="true" />
          <span>Tải lên đơn hàng (Upload purchase order)</span>
        </button>
      </div>

      <OrdersMetrics orders={orders} attentionCount={attentionCount} stats={stats} />

      {isLoading && orders.length === 0 ? (
        <div style={{ padding: "var(--space-6)", textAlign: "center", color: "var(--color-outline)" }}>
          Đang tải dữ liệu đơn hàng...
        </div>
      ) : (
        <div className="workspace-grid">
          <OrderQueue
            orders={filteredOrders}
            selectedId={selected?.id || ""}
            query={query}
            filter={filter}
            onQueryChange={setQuery}
            onFilterChange={setFilter}
            onSelect={setSelectedId}
          />

          {selected ? (
            <OrderDetail
              order={selected}
              onOpenDecision={() => openDecisionModal("APPROVE")}
              onRequestChanges={() => openDecisionModal("REQUEST_CHANGES")}
              onRejectOrder={() => openDecisionModal("REJECT")}
              onOpenSideBySide={() => setSideBySideOpen(true)}
            />
          ) : (
            <div className="content-card" style={{ padding: "var(--space-6)", textAlign: "center" }}>
              <FileText size={32} style={{ opacity: 0.3, marginBottom: "var(--space-2)" }} />
              <p>Chưa có đơn hàng nào được chọn.</p>
            </div>
          )}
        </div>
      )}

      {sideBySideOpen && selected && (
        <SideBySideViewer
          order={selected}
          onClose={() => setSideBySideOpen(false)}
        />
      )}

      {uploadOpen && (
        <UploadModal
          onClose={() => setUploadOpen(false)}
          onFile={async (name, file) => {
            setUploadOpen(false);
            if (file) {
              showToast(`Đang tải lên và xử lý ${name}...`);
              try {
                const res = await api.orders.upload(file, name);
                await refreshOrders();
                await loadStats();
                if (res && res.status === "received") {
                  showToast(`Đã tiếp nhận ${name}. Đang bóc tách dữ liệu bằng AI OCR trong nền...`);
                } else {
                  showToast(`Đã tải lên và kiểm tra xong đơn hàng ${name}.`, "success");
                }
              } catch (err) {
                showToast(describeError(err), "error");
              }
            }
          }}
        />
      )}

      {decisionOpen && selected && (
        <DecisionModal
          order={selected}
          initialAction={decisionAction}
          note={decisionNote}
          onNoteChange={setDecisionNote}
          onClose={() => setDecisionOpen(false)}
          onConfirm={handleDecisionConfirm}
        />
      )}

      {toast && (
        <div
          className="toast"
          role="status"
          style={{
            borderColor: toast.type === "success" ? "#10b981" : "#ef4444",
            backgroundColor: toast.type === "success" ? "var(--color-surface)" : "#fef2f2",
            color: toast.type === "success" ? "inherit" : "#dc2626",
          }}
        >
          {toast.type === "success" ? (
            <Check size={16} strokeWidth={2.5} color="#10b981" />
          ) : (
            <AlertCircle size={16} strokeWidth={2.5} color="#ef4444" />
          )}
          <span>{toast.message}</span>
        </div>
      )}
    </div>
  );
}

function OrdersMetrics({
  orders,
  attentionCount,
  stats,
}: {
  orders: PurchaseOrder[];
  attentionCount: number;
  stats: DashboardStats | null;
}) {
  const readyCount = stats?.ready_count ?? orders.filter((o) => o.status === "Ready").length;
  const approvedToday = stats?.approved_today ?? orders.filter((o) => o.status === "Approved").length;
  const avgDecision = stats?.avg_decision_minutes != null ? `${stats.avg_decision_minutes}m` : "—";
  const trend7Days = stats?.orders_last_7_days || [0, 0, 0, 0, 0, 0, orders.length];
  const maxTrend = Math.max(...trend7Days, 1);

  return (
    <div className="metrics-row">
      <div className="metric">
        <span>Cần xử lý</span>
        <strong className="tabular-nums">{attentionCount}</strong>
        <small>
          <i className="metric-dot amber" /> Cần xem xét hoặc chỉnh sửa
        </small>
      </div>
      <div className="metric">
        <span>Sẵn sàng duyệt</span>
        <strong className="tabular-nums">{readyCount}</strong>
        <small>
          <i className="metric-dot green" /> Đạt tất cả kiểm tra quy tắc
        </small>
      </div>
      <div className="metric">
        <span>Đã duyệt hôm nay</span>
        <strong className="tabular-nums">{approvedToday}</strong>
        <small>
          <i className="metric-dot blue" /> Thời gian xử lý TB: {avgDecision}
        </small>
      </div>
      <div className="metric metric-chart">
        <span>Tổng đơn 7 ngày qua</span>
        <strong className="tabular-nums">{trend7Days.reduce((a, b) => a + b, 0)}</strong>
        <div className="spark" aria-label="Biểu đồ đơn hàng 7 ngày qua">
          {trend7Days.map((val, idx) => (
            <i
              key={idx}
              style={{
                height: `${Math.max(15, Math.round((val / maxTrend) * 100))}%`,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function OrderQueue({
  orders,
  selectedId,
  query,
  filter,
  onQueryChange,
  onFilterChange,
  onSelect,
}: {
  orders: PurchaseOrder[];
  selectedId: string;
  query: string;
  filter: "All" | OrderStatus;
  onQueryChange: (value: string) => void;
  onFilterChange: (value: "All" | OrderStatus) => void;
  onSelect: (id: string) => void;
}) {
  const { createRipple } = useRipple();

  return (
    <section className="queue-panel" aria-label="Danh sách đơn hàng">
      <div className="panel-toolbar">
        <label className="search">
          <Search size={15} strokeWidth={2} style={{ opacity: 0.6 }} aria-hidden="true" />
          <input
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="Tìm mã PO hoặc khách hàng"
          />
        </label>
        <select
          value={filter}
          onChange={(event) => onFilterChange(event.target.value as typeof filter)}
          aria-label="Lọc đơn hàng theo trạng thái"
        >
          <option value="All">Tất cả trạng thái</option>
          <option value="Review required">Cần xem xét</option>
          <option value="Blocked">Bị chặn</option>
          <option value="Ready">Sẵn sàng duyệt</option>
          <option value="Approved">Đã duyệt</option>
          <option value="Changes requested">Yêu cầu sửa</option>
          <option value="Rejected">Đã từ chối</option>
        </select>
      </div>
      <div className="queue-header">
        <span>Đơn hàng</span>
        <span>Trạng thái</span>
        <span>Giá trị</span>
      </div>
      <div className="queue-list">
        {orders.map((order) => (
          <button
            key={order.id}
            className={selectedId === order.id ? "order-row selected interactive" : "order-row interactive"}
            onClick={(e) => {
              createRipple(e);
              onSelect(order.id);
            }}
          >
            <span className="order-identity">
              <strong>{order.id}</strong>
              <small>{order.customer}</small>
              <em>
                <SubmittedAt iso={order.submittedAt} />
              </em>
            </span>
            <span>
              <StatusBadge status={order.status} />
              {order.findings.length > 0 ? (
                <small className="finding-count tabular-nums">
                  {order.findings.length} cảnh báo
                </small>
              ) : null}
            </span>
            <span className="order-value">
              <strong className="tabular-nums">{money(order.value, order.currency)}</strong>
              <small>{order.currency}</small>
            </span>
          </button>
        ))}
        {orders.length === 0 ? (
          <div className="empty-state">
            <FileText size={28} strokeWidth={1.5} style={{ opacity: 0.4, marginBottom: "var(--space-2)" }} />
            <p>Không có đơn hàng nào khớp với bộ lọc.</p>
          </div>
        ) : null}
      </div>
    </section>
  );
}

function OrderDetail({
  order,
  onOpenDecision,
  onRequestChanges,
  onRejectOrder,
  onOpenSideBySide,
}: {
  order: PurchaseOrder;
  onOpenDecision: () => void;
  onRequestChanges: () => void;
  onRejectOrder: () => void;
  onOpenSideBySide: () => void;
}) {
  const { createRipple } = useRipple();

  return (
    <section className="detail-panel" aria-label={`Chi tiết đơn hàng ${order.id}`}>
      <div className="detail-header">
        <div>
          <div className="detail-title">
            <h2>{order.id}</h2>
            <StatusBadge status={order.status} />
          </div>
          <p>
            {order.customer} · Tiếp nhận <SubmittedAt iso={order.submittedAt} />
          </p>
        </div>
        <div style={{ display: "flex", gap: "var(--space-2)" }}>
          <button
            className="secondary-button interactive"
            onClick={(e) => {
              createRipple(e);
              onOpenSideBySide();
            }}
            style={{ fontSize: "var(--text-xs)", padding: "6px 10px", display: "inline-flex", alignItems: "center", gap: "var(--space-1)" }}
          >
            <Split size={14} strokeWidth={2} />
            <span>Đối chiếu gốc (Side-by-Side)</span>
          </button>
        </div>
      </div>
      <div className="order-summary">
        <div>
          <span>Tổng giá trị</span>
          <strong className="tabular-nums">{money(order.value, order.currency)}</strong>
        </div>
        <div>
          <span>Số dòng hàng</span>
          <strong className="tabular-nums">{order.lines.length}</strong>
        </div>
        <div>
          <span>Người phụ trách</span>
          <strong>{order.owner}</strong>
        </div>
        <div>
          <span>Nguồn tiếp nhận</span>
          {order.sourceChannel === "email" || order.sourceFile.startsWith("email://") ? (
            <strong className="source-name" style={{ display: "inline-flex", alignItems: "center", gap: "4px", color: "var(--color-primary)" }}>
              <Mail size={13} /> {order.senderEmail || order.sourceFile.replace("email://", "")}
            </strong>
          ) : (
            <strong className="source-name">{order.sourceFile}</strong>
          )}
        </div>
      </div>

      <div className="detail-body">
        <div className="section-title">
          <div>
            <h3>Phát hiện kiểm tra (Validation findings)</h3>
            <p>Bằng chứng đối chiếu từ hệ thống quy tắc định trước</p>
          </div>
          <span className="finding-pill tabular-nums">{order.findings.length}</span>
        </div>
        {order.findings.length ? (
          <div className="findings">
            {order.findings.map((finding) => (
              <article
                className={`finding finding-${finding.severity === "Error" ? "blocked" : finding.severity === "Info" ? "info" : "review"}`}
                key={`${finding.code}-${finding.sku ?? ""}`}
              >
                <div className="finding-symbol" aria-hidden="true" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
                  {finding.severity === "Error" ? (
                    <XCircle size={16} strokeWidth={2.2} />
                  ) : finding.severity === "Info" ? (
                    <Info size={15} strokeWidth={2.2} />
                  ) : (
                    <AlertTriangle size={15} strokeWidth={2.2} />
                  )}
                </div>
                <div>
                  <div className="finding-top">
                    <strong>{finding.title}</strong>
                    <span>{finding.severity === "Error" ? "Lỗi chặn" : finding.severity === "Info" ? "Thông tin" : "Cảnh báo"}</span>
                  </div>
                  <p>{finding.detail}</p>
                  <code>{finding.evidence}</code>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="clear-state">
            <span style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
              <CheckCircle2 size={20} strokeWidth={2.2} />
            </span>
            <div>
              <strong>Đạt tất cả kiểm tra quy tắc</strong>
              <p>Đơn hàng không có phát hiện sai khác về giá, tồn kho hay trùng lặp.</p>
            </div>
          </div>
        )}

        <div className="section-title line-title">
          <div>
            <h3>Dòng hàng chuẩn hóa</h3>
            <p>Dữ liệu trích xuất đối chiếu với Danh mục sản phẩm công ty</p>
          </div>
          <button className="text-button interactive" onClick={onOpenSideBySide}>
            Xem tệp gốc
          </button>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>SKU / Sản phẩm</th>
                <th style={{ textAlign: "right" }}>Số lượng</th>
                <th style={{ textAlign: "right" }}>Tồn kho</th>
                <th style={{ textAlign: "right" }}>Đơn giá PO</th>
                <th style={{ textAlign: "right" }}>Chiết khấu</th>
                <th style={{ textAlign: "right" }}>VAT</th>
                <th style={{ textAlign: "right" }}>Giá Catalog</th>
              </tr>
            </thead>
            <tbody>
              {order.lines.map((line) => (
                <tr key={line.sku}>
                  <td>
                    <strong>{line.sku}</strong>
                    <small>{line.product}</small>
                  </td>
                  <td className="tabular-nums" style={{ textAlign: "right" }}>
                    {line.quantity} {line.uom || ""}
                  </td>
                  <td
                    className={`tabular-nums ${line.available < line.quantity ? "cell-warning" : ""}`}
                    style={{ textAlign: "right" }}
                  >
                    {line.available}
                  </td>
                  <td
                    className={`tabular-nums ${line.catalogPrice > 0 && line.unitPrice !== line.catalogPrice && !line.isPromo ? "cell-warning" : ""}`}
                    style={{ textAlign: "right" }}
                  >
                    {line.isPromo ? "0 (Tặng/KM)" : money(line.unitPrice, order.currency)}
                  </td>
                  <td className="tabular-nums" style={{ textAlign: "right" }}>
                    {line.discountPercent ? `${line.discountPercent}%` : line.discountAmount ? money(line.discountAmount, order.currency) : "—"}
                  </td>
                  <td className="tabular-nums" style={{ textAlign: "right" }}>
                    {line.taxRate !== undefined && line.taxRate > 0 ? `${line.taxRate}%` : "—"}
                  </td>
                  <td className="tabular-nums" style={{ textAlign: "right" }}>
                    {line.catalogPrice ? money(line.catalogPrice, order.currency) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="section-title timeline-title">
          <div>
            <h3>Lịch sử xử lý &amp; Quyết định (Activity)</h3>
            <p>Toàn bộ bằng chứng và tiến trình phê duyệt của đơn hàng</p>
          </div>
        </div>
        <div className="timeline">
          {order.decisions && order.decisions.length > 0 ? (
            order.decisions.map((dec, index) => (
              <div className="timeline-event" key={index}>
                <span
                  className="timeline-mark human"
                  style={{ display: "flex", alignItems: "center", justifyContent: "center" }}
                >
                  <User size={13} strokeWidth={2.2} />
                </span>
                <div>
                  <strong>
                    {dec.type === "APPROVE"
                      ? "Đã duyệt đơn hàng"
                      : dec.type === "REJECT"
                        ? "Đã từ chối đơn hàng"
                        : "Đã gửi yêu cầu chỉnh sửa"}
                  </strong>
                  <p>{dec.note || `Thực hiện bởi: ${dec.actor}`}</p>
                </div>
                <time>{new Date(dec.createdAt).toLocaleTimeString("vi-VN")}</time>
              </div>
            ))
          ) : (
            <div style={{ color: "var(--color-outline)", fontSize: "0.875rem", padding: "var(--space-2) 0" }}>
              Chưa có quyết định nào được ghi nhận cho đơn hàng này.
            </div>
          )}
        </div>
      </div>

      <div className="decision-bar" style={{ display: "flex", gap: "var(--space-2)", justifyContent: "flex-end" }}>
        <button
          className="secondary-button interactive"
          onClick={(e) => {
            createRipple(e);
            onRequestChanges();
          }}
          disabled={order.status === "Approved" || order.status === "Rejected"}
        >
          Yêu cầu sửa (Request changes)
        </button>
        <button
          className="danger-button interactive"
          onClick={(e) => {
            createRipple(e);
            onRejectOrder();
          }}
          disabled={order.status === "Approved" || order.status === "Rejected"}
          style={{
            padding: "8px 16px",
            borderRadius: "var(--radius-md)",
            border: "1px solid var(--color-error)",
            backgroundColor: "transparent",
            color: "var(--color-error)",
            cursor: order.status === "Approved" || order.status === "Rejected" ? "not-allowed" : "pointer",
          }}
        >
          Từ chối
        </button>
        <button
          className="approve-button interactive"
          onClick={(e) => {
            createRipple(e);
            onOpenDecision();
          }}
          disabled={order.status === "Blocked" || order.status === "Approved" || order.status === "Rejected"}
        >
          {order.status === "Approved"
            ? "Đã duyệt"
            : order.status === "Blocked"
              ? "Cần giải quyết lỗi chặn"
              : "Xem xét & Duyệt đơn (Review and approve)"}
        </button>
      </div>
    </section>
  );
}
