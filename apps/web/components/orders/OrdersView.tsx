"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams, usePathname } from "next/navigation";
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
  Edit3,
  Save,
  Trash2,
  Copy,
  ChevronLeft,
  ChevronRight,
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
import type { DashboardStats, SKUMatchCandidate } from "@/app/lib/api/types";

interface ToastState {
  type: "success" | "error";
  message: string;
  requestId?: string;
}

export function OrdersView() {
  const { orders, isLoading, error, refreshOrders } = useAppState();
  const { createRipple } = useRipple();
  const searchParams = useSearchParams();
  const pathname = usePathname();

  // URL state synchronization
  const [selectedId, setSelectedId] = useState<string>(() => searchParams?.get("id") || "");
  const [query, setQuery] = useState(() => searchParams?.get("q") || "");
  const [statusFilter, setStatusFilter] = useState<"All" | OrderStatus>(
    () => (searchParams?.get("status") as "All" | OrderStatus) || "All",
  );
  const [customerFilter, setCustomerFilter] = useState<string>(() => searchParams?.get("customer") || "All");
  const [severityFilter, setSeverityFilter] = useState<"All" | "Error" | "Warning" | "Clean">(
    () => (searchParams?.get("severity") as "All" | "Error" | "Warning" | "Clean") || "All",
  );
  const [sortBy, setSortBy] = useState<"date_desc" | "date_asc" | "value_desc" | "value_asc" | "po">(
    () => (searchParams?.get("sort") as "date_desc" | "date_asc" | "value_desc" | "value_asc" | "po") || "date_desc",
  );
  const [page, setPage] = useState<number>(() => {
    const p = parseInt(searchParams?.get("page") || "1", 10);
    return isNaN(p) || p < 1 ? 1 : p;
  });

  const [uploadOpen, setUploadOpen] = useState(false);
  const [decisionOpen, setDecisionOpen] = useState(false);
  const [decisionAction, setDecisionAction] = useState<DecisionType>("APPROVE");
  const [sideBySideOpen, setSideBySideOpen] = useState(false);
  const [decisionNote, setDecisionNote] = useState("");
  const [toast, setToast] = useState<ToastState | null>(null);
  const [copiedRequestId, setCopiedRequestId] = useState(false);
  const [stats, setStats] = useState<DashboardStats | null>(null);

  // Sync state back to URL query params
  useEffect(() => {
    const params = new URLSearchParams();
    if (query) params.set("q", query);
    if (statusFilter !== "All") params.set("status", statusFilter);
    if (customerFilter !== "All") params.set("customer", customerFilter);
    if (severityFilter !== "All") params.set("severity", severityFilter);
    if (sortBy !== "date_desc") params.set("sort", sortBy);
    if (page > 1) params.set("page", page.toString());
    if (selectedId) params.set("id", selectedId);

    const queryString = params.toString();
    const newUrl = queryString ? `${pathname}?${queryString}` : pathname;
    window.history.replaceState(null, "", newUrl);
  }, [query, statusFilter, customerFilter, severityFilter, sortBy, page, selectedId, pathname]);

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

  // Unique customers for dropdown filter
  const distinctCustomers = useMemo(() => {
    const set = new Set<string>();
    orders.forEach((o) => {
      if (o.customer) set.add(o.customer);
    });
    return Array.from(set).sort();
  }, [orders]);

  // Filtered & Sorted orders
  const filteredOrders = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    const list = orders.filter((order) => {
      const matchesText =
        !normalized ||
        `${order.id} ${order.customer}`.toLowerCase().includes(normalized);
      const matchesStatus = statusFilter === "All" || order.status === statusFilter;
      const matchesCustomer = customerFilter === "All" || order.customer === customerFilter;

      let matchesSeverity = true;
      const hasError = order.findings.some((f) => f.severity === "Error");
      const hasWarning = order.findings.some((f) => f.severity === "Warning");
      if (severityFilter === "Error") matchesSeverity = hasError;
      else if (severityFilter === "Warning") matchesSeverity = hasWarning && !hasError;
      else if (severityFilter === "Clean") matchesSeverity = !hasError && !hasWarning;

      return matchesText && matchesStatus && matchesCustomer && matchesSeverity;
    });

    // Sorting
    list.sort((a, b) => {
      if (sortBy === "date_desc") {
        return new Date(b.submittedAt).getTime() - new Date(a.submittedAt).getTime();
      }
      if (sortBy === "date_asc") {
        return new Date(a.submittedAt).getTime() - new Date(b.submittedAt).getTime();
      }
      if (sortBy === "value_desc") {
        return b.value - a.value;
      }
      if (sortBy === "value_asc") {
        return a.value - b.value;
      }
      if (sortBy === "po") {
        return a.id.localeCompare(b.id);
      }
      return 0;
    });

    return list;
  }, [orders, query, statusFilter, customerFilter, severityFilter, sortBy]);

  const selected = useMemo(() => {
    if (selectedId) {
      const found = orders.find((o) => o.id === selectedId);
      if (found) return found;
    }
    return filteredOrders[0] || orders[0];
  }, [orders, filteredOrders, selectedId]);

  const attentionCount = orders.filter(
    (order) => order.status === "Review required" || order.status === "Blocked",
  ).length;

  const showToast = (message: string, type: "success" | "error" = "success", requestId?: string) => {
    setToast({ type, message, requestId });
    window.setTimeout(() => setToast(null), 5000);
  };

  const handleCopyRequestId = () => {
    if (toast?.requestId) {
      navigator.clipboard.writeText(toast.requestId);
      setCopiedRequestId(true);
      setTimeout(() => setCopiedRequestId(false), 2000);
    }
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
      const reqId = `req_${Math.random().toString(36).substring(2, 9)}`;
      showToast(describeError(err), "error", reqId);
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
          <p style={{ color: "var(--muted)", maxWidth: 460 }}>{error}</p>
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
          <p className="eyebrow">QUẢN LÝ ĐƠN HÀNG · PURCHASE ORDERS</p>
          <h1>Đơn đặt hàng (Purchase Orders)</h1>
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
          <span>Tải lên đơn hàng (Upload PO)</span>
        </button>
      </div>

      <OrdersMetrics orders={orders} attentionCount={attentionCount} stats={stats} />

      {isLoading && orders.length === 0 ? (
        <div style={{ padding: "var(--space-8)", textAlign: "center", color: "var(--muted)" }}>
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
          <p>Đang tải dữ liệu đơn hàng và chạy quy tắc kiểm tra...</p>
        </div>
      ) : (
        <div className="workspace-grid">
          <OrderQueue
            orders={filteredOrders}
            totalCount={filteredOrders.length}
            selectedId={selected?.id || ""}
            query={query}
            statusFilter={statusFilter}
            customerFilter={customerFilter}
            severityFilter={severityFilter}
            sortBy={sortBy}
            page={page}
            pageSize={8}
            distinctCustomers={distinctCustomers}
            onQueryChange={(q) => {
              setQuery(q);
              setPage(1);
            }}
            onStatusFilterChange={(s) => {
              setStatusFilter(s);
              setPage(1);
            }}
            onCustomerFilterChange={(c) => {
              setCustomerFilter(c);
              setPage(1);
            }}
            onSeverityFilterChange={(sev) => {
              setSeverityFilter(sev);
              setPage(1);
            }}
            onSortChange={(sort) => {
              setSortBy(sort);
              setPage(1);
            }}
            onPageChange={setPage}
            onSelect={setSelectedId}
            onResetFilters={() => {
              setQuery("");
              setStatusFilter("All");
              setCustomerFilter("All");
              setSeverityFilter("All");
              setSortBy("date_desc");
              setPage(1);
            }}
          />

          {selected ? (
            <OrderDetail
              key={selected.id}
              order={selected}
              onOpenDecision={() => openDecisionModal("APPROVE")}
              onRequestChanges={() => openDecisionModal("REQUEST_CHANGES")}
              onRejectOrder={() => openDecisionModal("REJECT")}
              onOpenSideBySide={() => setSideBySideOpen(true)}
              onSavedRecheck={async () => {
                await refreshOrders();
                showToast("Đã lưu chỉnh sửa và chạy lại quy tắc kiểm tra thành công!", "success");
              }}
              onError={(msg, reqId) => showToast(msg, "error", reqId)}
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
                const reqId = `req_${Math.random().toString(36).substring(2, 9)}`;
                showToast(describeError(err), "error", reqId);
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

      {/* Accessible Toast Notification with Request ID */}
      {toast && (
        <div
          className="toast"
          role="status"
          aria-live="polite"
          style={{
            borderColor: toast.type === "success" ? "#10b981" : "#ef4444",
            backgroundColor: toast.type === "success" ? "var(--surface)" : "#fef2f2",
            color: toast.type === "success" ? "inherit" : "#dc2626",
            display: "flex",
            alignItems: "center",
            gap: "10px",
            boxShadow: "0 4px 14px rgba(0,0,0,0.12)",
          }}
        >
          {toast.type === "success" ? (
            <Check size={18} strokeWidth={2.5} color="#10b981" />
          ) : (
            <AlertCircle size={18} strokeWidth={2.5} color="#ef4444" />
          )}
          <div style={{ flex: 1, fontSize: "0.85rem" }}>
            <div>{toast.message}</div>
            {toast.requestId && (
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  marginTop: "4px",
                  fontSize: "0.75rem",
                  color: "#991b1b",
                  background: "rgba(239, 68, 68, 0.1)",
                  padding: "2px 6px",
                  borderRadius: "4px",
                }}
              >
                <span>Mã tham chiếu: <strong>{toast.requestId}</strong></span>
                <button
                  type="button"
                  onClick={handleCopyRequestId}
                  style={{
                    background: "none",
                    border: "none",
                    color: "#dc2626",
                    cursor: "pointer",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "2px",
                    fontSize: "0.75rem",
                    padding: 0,
                  }}
                >
                  {copiedRequestId ? <Check size={12} color="#10b981" /> : <Copy size={12} />}
                  {copiedRequestId ? "Đã chép" : "Sao chép"}
                </button>
              </div>
            )}
          </div>
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
        <div className="sparkline" aria-label="Biểu đồ đơn hàng 7 ngày qua">
          {trend7Days.map((val, idx) => (
            <div
              key={idx}
              className="spark-bar"
              style={{
                height: `${Math.max(12, Math.min(100, (val / (Math.max(...trend7Days, 1))) * 100))}%`,
              }}
              title={`Ngày ${idx + 1}: ${val} đơn`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function OrderQueue({
  orders,
  totalCount,
  selectedId,
  query,
  statusFilter,
  customerFilter,
  severityFilter,
  sortBy,
  page,
  pageSize,
  distinctCustomers,
  onQueryChange,
  onStatusFilterChange,
  onCustomerFilterChange,
  onSeverityFilterChange,
  onSortChange,
  onPageChange,
  onSelect,
  onResetFilters,
}: {
  orders: PurchaseOrder[];
  totalCount: number;
  selectedId: string;
  query: string;
  statusFilter: "All" | OrderStatus;
  customerFilter: string;
  severityFilter: "All" | "Error" | "Warning" | "Clean";
  sortBy: "date_desc" | "date_asc" | "value_desc" | "value_asc" | "po";
  page: number;
  pageSize: number;
  distinctCustomers: string[];
  onQueryChange: (value: string) => void;
  onStatusFilterChange: (value: "All" | OrderStatus) => void;
  onCustomerFilterChange: (value: string) => void;
  onSeverityFilterChange: (value: "All" | "Error" | "Warning" | "Clean") => void;
  onSortChange: (value: "date_desc" | "date_asc" | "value_desc" | "value_asc" | "po") => void;
  onPageChange: (page: number) => void;
  onSelect: (id: string) => void;
  onResetFilters: () => void;
}) {
  const { createRipple } = useRipple();

  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
  const currentPage = Math.min(page, totalPages);
  const pagedOrders = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return orders.slice(start, start + pageSize);
  }, [orders, currentPage, pageSize]);

  return (
    <section className="queue-panel" aria-label="Danh sách đơn hàng">
      {/* Top Search & Filter Bar */}
      <div className="panel-toolbar" style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        <div style={{ display: "flex", gap: "8px", width: "100%" }}>
          <label className="search" style={{ flex: 1 }}>
            <Search size={15} strokeWidth={2} style={{ opacity: 0.6 }} aria-hidden="true" />
            <input
              value={query}
              onChange={(event) => onQueryChange(event.target.value)}
              placeholder="Tìm mã PO hoặc khách hàng..."
            />
          </label>
          <select
            value={sortBy}
            onChange={(e) => onSortChange(e.target.value as "date_desc" | "date_asc" | "value_desc" | "value_asc" | "po")}
            aria-label="Sắp xếp đơn hàng"
            style={{ fontSize: "0.8rem", minWidth: "125px" }}
          >
            <option value="date_desc">Mới nhất</option>
            <option value="date_asc">Cũ nhất</option>
            <option value="value_desc">Giá trị cao nhất</option>
            <option value="value_asc">Giá trị thấp nhất</option>
            <option value="po">Mã PO (A-Z)</option>
          </select>
        </div>

        {/* Secondary Filter Row: Status, Customer, Severity */}
        <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1.2fr 1fr", gap: "6px" }}>
          <select
            value={statusFilter}
            onChange={(event) => onStatusFilterChange(event.target.value as "All" | OrderStatus)}
            aria-label="Lọc đơn hàng theo trạng thái"
            style={{ fontSize: "0.75rem", padding: "4px 8px" }}
          >
            <option value="All">Tất cả trạng thái</option>
            <option value="Review required">Cần xem xét</option>
            <option value="Blocked">Bị chặn</option>
            <option value="Ready">Sẵn sàng duyệt</option>
            <option value="Approved">Đã duyệt</option>
            <option value="Changes requested">Yêu cầu sửa</option>
            <option value="Rejected">Đã từ chối</option>
            <option value="Received">Đang bóc tách</option>
          </select>

          <select
            value={customerFilter}
            onChange={(event) => onCustomerFilterChange(event.target.value)}
            aria-label="Lọc theo khách hàng"
            style={{ fontSize: "0.75rem", padding: "4px 8px" }}
          >
            <option value="All">Tất cả khách hàng</option>
            {distinctCustomers.map((cust) => (
              <option key={cust} value={cust}>
                {cust}
              </option>
            ))}
          </select>

          <select
            value={severityFilter}
            onChange={(event) => onSeverityFilterChange(event.target.value as "All" | "Error" | "Warning" | "Clean")}
            aria-label="Lọc theo mức độ cảnh báo"
            style={{ fontSize: "0.75rem", padding: "4px 8px" }}
          >
            <option value="All">Mọi mức độ</option>
            <option value="Error">Có lỗi chặn</option>
            <option value="Warning">Có cảnh báo</option>
            <option value="Clean">Đạt 100%</option>
          </select>
        </div>
      </div>

      <div className="queue-header">
        <span>Đơn hàng</span>
        <span>Trạng thái</span>
        <span>Giá trị</span>
      </div>

      <div className="queue-list">
        {pagedOrders.map((order) => (
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

        {pagedOrders.length === 0 ? (
          <div className="empty-state" style={{ padding: "var(--space-6) var(--space-4)", textAlign: "center" }}>
            <FileText size={28} strokeWidth={1.5} style={{ opacity: 0.4, margin: "0 auto var(--space-2)" }} />
            <p style={{ margin: "0 0 12px", color: "var(--muted)", fontSize: "0.85rem" }}>
              Không có đơn hàng nào khớp với bộ lọc tìm kiếm.
            </p>
            <button
              type="button"
              className="secondary-button"
              style={{ fontSize: "0.75rem", padding: "4px 10px" }}
              onClick={onResetFilters}
            >
              Đặt lại tất cả bộ lọc
            </button>
          </div>
        ) : null}
      </div>

      {/* Pagination Footer */}
      {totalCount > 0 && (
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "8px 12px",
            borderTop: "1px solid var(--line)",
            fontSize: "0.75rem",
            color: "var(--muted)",
          }}
        >
          <span>
            Trang <strong>{currentPage}</strong> / {totalPages} ({totalCount} đơn)
          </span>
          <div style={{ display: "flex", gap: "4px" }}>
            <button
              type="button"
              disabled={currentPage <= 1}
              onClick={() => onPageChange(currentPage - 1)}
              style={{
                padding: "3px 8px",
                border: "1px solid var(--line)",
                background: "var(--surface)",
                borderRadius: "4px",
                cursor: currentPage <= 1 ? "not-allowed" : "pointer",
                opacity: currentPage <= 1 ? 0.5 : 1,
              }}
              aria-label="Trang trước"
            >
              <ChevronLeft size={13} />
            </button>
            <button
              type="button"
              disabled={currentPage >= totalPages}
              onClick={() => onPageChange(currentPage + 1)}
              style={{
                padding: "3px 8px",
                border: "1px solid var(--line)",
                background: "var(--surface)",
                borderRadius: "4px",
                cursor: currentPage >= totalPages ? "not-allowed" : "pointer",
                opacity: currentPage >= totalPages ? 0.5 : 1,
              }}
              aria-label="Trang tiếp"
            >
              <ChevronRight size={13} />
            </button>
          </div>
        </div>
      )}
    </section>
  );
}

function OrderDetail({
  order,
  onOpenDecision,
  onRequestChanges,
  onRejectOrder,
  onOpenSideBySide,
  onSavedRecheck,
  onError,
}: {
  order: PurchaseOrder;
  onOpenDecision: () => void;
  onRequestChanges: () => void;
  onRejectOrder: () => void;
  onOpenSideBySide: () => void;
  onSavedRecheck: () => Promise<void>;
  onError: (msg: string, reqId?: string) => void;
}) {
  const { createRipple } = useRipple();

  // Inline editing state for line items
  const [isEditing, setIsEditing] = useState(false);
  const [editLines, setEditLines] = useState<
    Array<{ sku: string; product?: string; quantity: number; unitPrice: number; uom?: string }>
  >(() =>
    (order.lines || []).map((l) => ({
      sku: l.sku,
      product: l.product,
      quantity: l.quantity,
      unitPrice: l.unitPrice,
      uom: l.uom || "Cái",
    })),
  );
  const [savingChanges, setSavingChanges] = useState(false);
  const [skuSuggestions, setSkuSuggestions] = useState<SKUMatchCandidate[]>([]);
  const [activeSearchIndex, setActiveSearchIndex] = useState<number | null>(null);

  const handleStartEdit = () => {
    setEditLines(
      (order.lines || []).map((l) => ({
        sku: l.sku,
        product: l.product,
        quantity: l.quantity,
        unitPrice: l.unitPrice,
        uom: l.uom || "Cái",
      })),
    );
    setIsEditing(true);
  };

  const handleLineChange = (
    index: number,
    field: "sku" | "product" | "quantity" | "unitPrice" | "uom",
    val: string | number,
  ) => {
    setEditLines((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], [field]: val };
      return next;
    });
  };

  const handleAddLine = () => {
    setEditLines((prev) => [
      ...prev,
      { sku: "", product: "Sản phẩm mới", quantity: 1, unitPrice: 0, uom: "Cái" },
    ]);
  };

  const handleRemoveLine = (index: number) => {
    if (editLines.length <= 1) {
      alert("Đơn hàng phải có ít nhất một dòng sản phẩm.");
      return;
    }
    setEditLines((prev) => prev.filter((_, idx) => idx !== index));
  };

  const handleSkuSearch = async (query: string, index: number) => {
    handleLineChange(index, "sku", query.toUpperCase());
    setActiveSearchIndex(index);
    if (query.trim().length >= 2) {
      try {
        const res = await api.sku.resolve(query.trim(), order.customer);
        setSkuSuggestions(res.candidates || []);
      } catch {
        setSkuSuggestions([]);
      }
    } else {
      setSkuSuggestions([]);
    }
  };

  const handleSelectSuggestion = (index: number, cand: SKUMatchCandidate) => {
    setEditLines((prev) => {
      const next = [...prev];
      next[index] = {
        ...next[index],
        sku: cand.sku,
        product: cand.name,
        unitPrice: cand.unit_price || next[index].unitPrice,
      };
      return next;
    });
    setActiveSearchIndex(null);
    setSkuSuggestions([]);
  };

  const handleSaveAndRecheck = async () => {
    // Validate lines
    for (let i = 0; i < editLines.length; i++) {
      if (!editLines[i].sku.trim()) {
        alert(`Dòng #${i + 1} chưa nhập mã SKU.`);
        return;
      }
      if (editLines[i].quantity <= 0) {
        alert(`Dòng #${i + 1} có số lượng phải lớn hơn 0.`);
        return;
      }
      if (editLines[i].unitPrice < 0) {
        alert(`Dòng #${i + 1} có đơn giá không hợp lệ.`);
        return;
      }
    }

    setSavingChanges(true);
    try {
      await api.orders.confirmExtraction(order.id, {
        po_number: order.id,
        customer: order.customer,
        currency: order.currency,
        items: editLines.map((l) => ({
          sku: l.sku.trim().toUpperCase(),
          quantity: l.quantity,
          unit_price: l.unitPrice,
          uom: l.uom,
        })),
      });
      setIsEditing(false);
      await onSavedRecheck();
    } catch (err) {
      const reqId = `req_${Math.random().toString(36).substring(2, 9)}`;
      onError(`Lỗi khi lưu và chạy lại kiểm tra: ${describeError(err)}`, reqId);
    } finally {
      setSavingChanges(false);
    }
  };

  const isExtractionReview = order.status === "Received" || (order.status as string) === "extraction_review";

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

      {/* Notice banner if order is in extraction review / needs review */}
      {isExtractionReview && (
        <div
          style={{
            padding: "10px 14px",
            background: "rgba(124, 58, 237, 0.08)",
            border: "1px solid rgba(124, 58, 237, 0.3)",
            borderRadius: "var(--radius-md)",
            color: "#6d28d9",
            fontSize: "0.825rem",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            marginBottom: "var(--space-3)",
          }}
        >
          <Info size={16} />
          <span>
            <strong>Xem xét bóc tách (Extraction Review):</strong> Dữ liệu đã được AI OCR trích xuất sơ bộ. Vui lòng đối chiếu với tài liệu gốc và bấm <strong>&ldquo;Chỉnh sửa dòng hàng&rdquo;</strong> nếu có sai khác mã SKU hoặc số lượng.
          </span>
        </div>
      )}

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

        {/* Line Items Section with Inline Editing & SKU Resolver */}
        <div className="section-title line-title">
          <div>
            <h3>Dòng hàng chuẩn hóa</h3>
            <p>Dữ liệu trích xuất đối chiếu với Danh mục sản phẩm công ty</p>
          </div>
          <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
            {!isEditing ? (
              <button
                type="button"
                className="secondary-button"
                onClick={handleStartEdit}
                style={{ fontSize: "0.75rem", padding: "4px 10px", display: "inline-flex", alignItems: "center", gap: "4px" }}
              >
                <Edit3 size={13} />
                <span>Chỉnh sửa dòng hàng</span>
              </button>
            ) : (
              <>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setIsEditing(false)}
                  style={{ fontSize: "0.75rem", padding: "4px 10px" }}
                >
                  Hủy bỏ
                </button>
                <button
                  type="button"
                  className="primary-button"
                  disabled={savingChanges}
                  onClick={handleSaveAndRecheck}
                  style={{ fontSize: "0.75rem", padding: "4px 12px", display: "inline-flex", alignItems: "center", gap: "4px" }}
                >
                  <Save size={13} />
                  <span>{savingChanges ? "Đang lưu & chạy lại..." : "Lưu & chạy lại kiểm tra"}</span>
                </button>
              </>
            )}
            <button className="text-button interactive" onClick={onOpenSideBySide} style={{ fontSize: "0.8rem" }}>
              Xem tệp gốc
            </button>
          </div>
        </div>

        {isEditing ? (
          /* Editable Table Mode */
          <div className="table-wrap" style={{ border: "1px solid var(--color-primary)", borderRadius: "var(--radius-md)", padding: "8px" }}>
            <table style={{ fontSize: "0.825rem" }}>
              <thead>
                <tr>
                  <th style={{ width: "38%" }}>Mã SKU / Tìm kiếm gợi ý</th>
                  <th style={{ width: "15%", textAlign: "right" }}>Số lượng</th>
                  <th style={{ width: "15%", textAlign: "right" }}>Đơn vị tính</th>
                  <th style={{ width: "22%", textAlign: "right" }}>Đơn giá PO ({order.currency})</th>
                  <th style={{ width: "10%", textAlign: "center" }}>Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {editLines.map((line, idx) => (
                  <tr key={idx}>
                    <td style={{ position: "relative" }}>
                      <input
                        type="text"
                        value={line.sku}
                        onChange={(e) => handleSkuSearch(e.target.value, idx)}
                        onFocus={() => {
                          if (line.sku) handleSkuSearch(line.sku, idx);
                        }}
                        placeholder="Nhập mã SKU hoặc biệt danh..."
                        style={{
                          width: "100%",
                          padding: "6px 8px",
                          fontWeight: 700,
                          borderRadius: "4px",
                          border: "1px solid var(--line)",
                          background: "var(--surface)",
                        }}
                      />
                      {line.product && (
                        <div style={{ fontSize: "0.7rem", color: "var(--muted)", marginTop: "2px" }}>
                          {line.product}
                        </div>
                      )}

                      {/* SKU Candidates Dropdown */}
                      {activeSearchIndex === idx && skuSuggestions.length > 0 && (
                        <div
                          style={{
                            position: "absolute",
                            top: "100%",
                            left: 0,
                            right: 0,
                            zIndex: 50,
                            background: "var(--surface)",
                            border: "1px solid var(--line)",
                            borderRadius: "var(--radius-md)",
                            boxShadow: "0 6px 20px rgba(0,0,0,0.15)",
                            maxHeight: "180px",
                            overflowY: "auto",
                          }}
                        >
                          <div style={{ padding: "4px 8px", fontSize: "0.65rem", background: "var(--canvas)", color: "var(--muted)", fontWeight: 700 }}>
                            GỢI Ý KHỚP MÃ THÔNG MINH (4-TIER RAG):
                          </div>
                          {skuSuggestions.map((cand, cIdx) => (
                            <div
                              key={cIdx}
                              onClick={() => handleSelectSuggestion(idx, cand)}
                              style={{
                                padding: "6px 8px",
                                borderBottom: "1px solid var(--line)",
                                cursor: "pointer",
                                fontSize: "0.75rem",
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "center",
                              }}
                              onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(37, 99, 235, 0.08)")}
                              onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                            >
                              <div>
                                <strong>{cand.sku}</strong> — {cand.name}
                              </div>
                              <span
                                style={{
                                  fontSize: "0.65rem",
                                  padding: "2px 6px",
                                  borderRadius: "4px",
                                  background: "rgba(16, 185, 129, 0.1)",
                                  color: "#10b981",
                                  fontWeight: 700,
                                }}
                              >
                                {cand.tier_used || cand.match_tier || "RAG"} ({Math.round(cand.confidence_score * 100)}%)
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <input
                        type="number"
                        min="1"
                        value={line.quantity}
                        onChange={(e) => handleLineChange(idx, "quantity", parseInt(e.target.value, 10) || 1)}
                        style={{
                          width: "70px",
                          padding: "6px 8px",
                          textAlign: "right",
                          borderRadius: "4px",
                          border: "1px solid var(--line)",
                        }}
                      />
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <input
                        type="text"
                        value={line.uom || "Cái"}
                        onChange={(e) => handleLineChange(idx, "uom", e.target.value)}
                        placeholder="Cái, Sợi..."
                        style={{
                          width: "60px",
                          padding: "6px 8px",
                          textAlign: "right",
                          borderRadius: "4px",
                          border: "1px solid var(--line)",
                        }}
                      />
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <input
                        type="number"
                        min="0"
                        value={line.unitPrice}
                        onChange={(e) => handleLineChange(idx, "unitPrice", parseFloat(e.target.value) || 0)}
                        style={{
                          width: "110px",
                          padding: "6px 8px",
                          textAlign: "right",
                          borderRadius: "4px",
                          border: "1px solid var(--line)",
                        }}
                      />
                    </td>
                    <td style={{ textAlign: "center" }}>
                      <button
                        type="button"
                        onClick={() => handleRemoveLine(idx)}
                        style={{
                          background: "none",
                          border: "none",
                          color: "#ef4444",
                          cursor: "pointer",
                          padding: "4px",
                        }}
                        title="Xóa dòng này"
                      >
                        <Trash2 size={15} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "10px", padding: "4px 8px" }}>
              <button
                type="button"
                className="secondary-button"
                onClick={handleAddLine}
                style={{ fontSize: "0.75rem", padding: "4px 10px", display: "inline-flex", alignItems: "center", gap: "4px" }}
              >
                <Plus size={13} />
                <span>Thêm dòng hàng</span>
              </button>

              <div style={{ display: "flex", gap: "8px" }}>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setIsEditing(false)}
                  style={{ fontSize: "0.75rem", padding: "6px 12px" }}
                >
                  Hủy
                </button>
                <button
                  type="button"
                  className="primary-button"
                  disabled={savingChanges}
                  onClick={handleSaveAndRecheck}
                  style={{ fontSize: "0.75rem", padding: "6px 14px", display: "inline-flex", alignItems: "center", gap: "6px" }}
                >
                  <Save size={14} />
                  <span>{savingChanges ? "Đang chạy lại kiểm tra..." : "Lưu & chạy lại kiểm tra"}</span>
                </button>
              </div>
            </div>
          </div>
        ) : (
          /* Normal Read-only Table */
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
        )}

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
            <div style={{ color: "var(--muted)", fontSize: "0.875rem", padding: "var(--space-2) 0" }}>
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
