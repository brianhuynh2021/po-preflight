"use client";

import { useEffect, useState } from "react";
import { money } from "@/app/lib/derive";
import { api, describeError } from "@/app/lib/api/client";
import type { OrderDetail, OrderSummary } from "@/app/lib/api/types";
import { CheckCircle2, AlertCircle, RefreshCw, FileText, Check, Plus, Trash2 } from "lucide-react";
import { useRipple } from "@/app/lib/useRipple";

const initialOrderDetail: OrderDetail = {
  id: 1,
  po_number: "PO-10431",
  customer: "Acme Global Distributors",
  currency: "VND",
  status: "extraction_review",
  risk_level: "LOW",
  source_file: "acme-po-10431.pdf",
  total: 224000000,
  created_at: "2026-09-01T08:00:00Z",
  items: [
    { line_number: 1, sku: "LAPTOP-A14", name: "A14 Business Laptop", quantity: 10, unit_price: "18500000", status: "MATCHED" },
    { line_number: 2, sku: "HEADSET-PRO", name: "Pro Noise-Canceling Headset", quantity: 5, unit_price: "2800000", status: "MATCHED" },
  ],
  findings: [],
  decisions: [],
};

export function ExtractionReviewStudio() {
  const { createRipple } = useRipple();
  const [stagedOrders, setStagedOrders] = useState<OrderSummary[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<OrderDetail | null>(initialOrderDetail);
  const [isLoading, setIsLoading] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const [poNumber, setPoNumber] = useState("PO-10431");
  const [customer, setCustomer] = useState("Acme Global Distributors");
  const [currency, setCurrency] = useState("VND");
  const [items, setItems] = useState<
    Array<{
      line_number: number;
      sku: string;
      name: string;
      quantity: number;
      unit_price: number;
    }>
  >([
    { line_number: 1, sku: "LAPTOP-A14", name: "A14 Business Laptop", quantity: 10, unit_price: 18500000 },
    { line_number: 2, sku: "HEADSET-PRO", name: "Pro Noise-Canceling Headset", quantity: 5, unit_price: 2800000 },
  ]);

  const fetchStagedOrders = async () => {
    setIsLoading(true);
    try {
      const list = await api.orders.list();
      const reviewOrders = list.filter((o) => o.status === "extraction_review" || o.status === "review_required");
      setStagedOrders(reviewOrders.length > 0 ? reviewOrders : list);
      if (reviewOrders.length > 0 && !selectedOrder) {
        await loadOrderDetail(reviewOrders[0].id);
      } else if (list.length > 0 && !selectedOrder) {
        await loadOrderDetail(list[0].id);
      }
    } catch {
      // Offline / fallback
    } finally {
      setIsLoading(false);
    }
  };

  const loadOrderDetail = async (orderId: number) => {
    try {
      const detail = await api.orders.get(orderId);
      setSelectedOrder(detail);
      setPoNumber(detail.po_number);
      setCustomer(detail.customer);
      setCurrency(detail.currency || "VND");
      setItems(
        (detail.items || []).map((it, idx) => ({
          line_number: it.line_number || idx + 1,
          sku: it.sku,
          name: it.name,
          quantity: it.quantity,
          unit_price: Number(it.unit_price),
        })),
      );
    } catch {
      // Ignore
    }
  };

  useEffect(() => {
    let mounted = true;
    api.orders
      .list()
      .then(async (list) => {
        if (!mounted) return;
        const reviewOrders = list.filter((o) => o.status === "extraction_review" || o.status === "review_required");
        const effectiveList = reviewOrders.length > 0 ? reviewOrders : list;
        setStagedOrders(effectiveList);
        if (effectiveList.length > 0) {
          const detail = await api.orders.get(effectiveList[0].id).catch(() => null);
          if (mounted && detail) {
            setSelectedOrder(detail);
            setPoNumber(detail.po_number);
            setCustomer(detail.customer);
            setCurrency(detail.currency || "VND");
            setItems(
              (detail.items || []).map((it, idx) => ({
                line_number: it.line_number || idx + 1,
                sku: it.sku,
                name: it.name,
                quantity: it.quantity,
                unit_price: Number(it.unit_price),
              })),
            );
          }
        }
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, []);

  const handleItemChange = (index: number, field: string, val: string | number) => {
    setItems((prev) =>
      prev.map((it, i) => (i === index ? { ...it, [field]: val } : it)),
    );
  };

  const addItem = () => {
    setItems((prev) => [
      ...prev,
      {
        line_number: prev.length + 1,
        sku: "",
        name: "Sản phẩm mới",
        quantity: 1,
        unit_price: 0,
      },
    ]);
  };

  const removeItem = (index: number) => {
    setItems((prev) => prev.filter((_, i) => i !== index));
  };

  const handleConfirmExtraction = async () => {
    if (!selectedOrder) return;
    setIsConfirming(true);
    setFeedback(null);
    try {
      const res = await api.orders.confirmExtraction(selectedOrder.id, {
        po_number: poNumber,
        customer,
        currency,
        items: items.map((it) => ({
          sku: it.sku,
          name: it.name,
          quantity: Number(it.quantity),
          unit_price: Number(it.unit_price),
        })),
      });
      setSelectedOrder(res);
      setFeedback({
        type: "success",
        message: `Đã xác nhận dữ liệu trích xuất thành công! Trạng thái mới: ${res.status.toUpperCase()} (${res.findings.length} phát hiện kiểm tra).`,
      });
      await fetchStagedOrders();
    } catch (err) {
      setFeedback({
        type: "error",
        message: describeError(err),
      });
    } finally {
      setIsConfirming(false);
    }
  };

  const totalValue = items.reduce((acc, it) => acc + Number(it.quantity) * Number(it.unit_price), 0);

  return (
    <div className="page staging-page page-enter">
      <div className="page-heading">
        <div>
          <p className="eyebrow">XỬ LÝ TÀI LIỆU THÔNG MINH (IDP) · Extraction Review</p>
          <h1>Không gian Rà soát bóc tách (Extraction Review Studio)</h1>
          <p>
            Môi trường Human-in-the-Loop để đối chiếu vùng nhận diện OCR, điều chỉnh mã SKU và hiệu đính số lượng trước khi chạy kiểm tra quy tắc.
          </p>
        </div>
        <div style={{ display: "flex", gap: "var(--space-2)" }}>
          <button
            className="secondary-button interactive"
            onClick={(e) => {
              createRipple(e);
              void fetchStagedOrders();
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
              void handleConfirmExtraction();
            }}
            disabled={isConfirming || !selectedOrder || items.length === 0}
            style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-1)" }}
          >
            <Check size={16} />
            <span>{isConfirming ? "Đang xử lý..." : "Xác nhận & Chạy kiểm tra quy tắc"}</span>
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
          {feedback.type === "success" ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
          <strong>{feedback.message}</strong>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: "var(--space-5)" }}>
        {/* Left: Orders Queue */}
        <div className="content-card" style={{ padding: "var(--space-4)" }}>
          <h2 style={{ fontSize: "1rem", marginBottom: "var(--space-3)" }}>Hàng đợi cần rà soát</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            {stagedOrders.map((o) => (
              <button
                key={o.id}
                onClick={() => void loadOrderDetail(o.id)}
                className={`order-row interactive ${selectedOrder?.id === o.id ? "selected" : ""}`}
                style={{
                  textAlign: "left",
                  padding: "8px 12px",
                  borderRadius: "var(--radius-md)",
                  border: selectedOrder?.id === o.id ? "1px solid var(--color-primary)" : "1px solid var(--color-outline-variant)",
                  background: selectedOrder?.id === o.id ? "var(--color-surface-container-high)" : "transparent",
                  cursor: "pointer",
                }}
              >
                <div style={{ fontWeight: 600, fontSize: "0.875rem" }}>{o.po_number}</div>
                <div style={{ fontSize: "0.75rem", color: "var(--color-outline)" }}>{o.customer}</div>
                <div style={{ fontSize: "0.75rem", marginTop: 4, display: "flex", justifyContent: "space-between" }}>
                  <span>{money(o.total, o.currency)}</span>
                  <span className="badge" style={{ fontSize: "0.7rem", padding: "1px 4px" }}>
                    {o.status}
                  </span>
                </div>
              </button>
            ))}
            {stagedOrders.length === 0 && (
              <div style={{ color: "var(--color-outline)", fontSize: "0.875rem", padding: "var(--space-4)", textAlign: "center" }}>
                Không có đơn hàng nào trong hàng đợi rà soát.
              </div>
            )}
          </div>
        </div>

        {/* Right: Line Items Editor */}
        {selectedOrder ? (
          <div className="content-card" style={{ padding: "var(--space-5)" }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1.5fr 1fr", gap: "var(--space-3)", marginBottom: "var(--space-4)" }}>
              <div>
                <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, marginBottom: 4 }}>
                  MÃ ĐƠN HÀNG (PO NUMBER)
                </label>
                <input
                  type="text"
                  value={poNumber}
                  onChange={(e) => setPoNumber(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: "var(--radius-sm)",
                    border: "1px solid var(--color-outline-variant)",
                  }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, marginBottom: 4 }}>
                  KHÁCH HÀNG (CUSTOMER)
                </label>
                <input
                  type="text"
                  value={customer}
                  onChange={(e) => setCustomer(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: "var(--radius-sm)",
                    border: "1px solid var(--color-outline-variant)",
                  }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, marginBottom: 4 }}>
                  TIỀN TỆ (CURRENCY)
                </label>
                <select
                  value={currency}
                  onChange={(e) => setCurrency(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: "var(--radius-sm)",
                    border: "1px solid var(--color-outline-variant)",
                  }}
                >
                  <option value="VND">VND (Việt Nam Đồng)</option>
                  <option value="USD">USD (Đô la Mỹ)</option>
                </select>
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-2)" }}>
              <h3 style={{ fontSize: "1rem", margin: 0 }}>Danh sách dòng hàng bóc tách (Extracted Line Items)</h3>
              <button
                className="secondary-button interactive"
                onClick={addItem}
                style={{ fontSize: "0.75rem", padding: "4px 8px", display: "inline-flex", alignItems: "center", gap: 4 }}
              >
                <Plus size={14} />
                <span>Thêm dòng</span>
              </button>
            </div>

            <div className="table-wrap" style={{ marginBottom: "var(--space-4)" }}>
              <table>
                <thead>
                  <tr>
                    <th style={{ width: 40 }}>#</th>
                    <th>Mã SKU</th>
                    <th>Tên sản phẩm</th>
                    <th style={{ width: 100, textAlign: "right" }}>Số lượng</th>
                    <th style={{ width: 160, textAlign: "right" }}>Đơn giá ({currency})</th>
                    <th style={{ width: 160, textAlign: "right" }}>Thành tiền</th>
                    <th style={{ width: 50 }}></th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((it, idx) => (
                    <tr key={idx}>
                      <td>{idx + 1}</td>
                      <td>
                        <input
                          type="text"
                          value={it.sku}
                          onChange={(e) => handleItemChange(idx, "sku", e.target.value)}
                          placeholder="Mã SKU..."
                          style={{ width: "100%", padding: "4px 6px", borderRadius: "var(--radius-xs)" }}
                        />
                      </td>
                      <td>
                        <input
                          type="text"
                          value={it.name}
                          onChange={(e) => handleItemChange(idx, "name", e.target.value)}
                          style={{ width: "100%", padding: "4px 6px", borderRadius: "var(--radius-xs)" }}
                        />
                      </td>
                      <td>
                        <input
                          type="number"
                          value={it.quantity}
                          onChange={(e) => handleItemChange(idx, "quantity", Number(e.target.value))}
                          style={{ width: "100%", padding: "4px 6px", textAlign: "right" }}
                        />
                      </td>
                      <td>
                        <input
                          type="number"
                          value={it.unit_price}
                          onChange={(e) => handleItemChange(idx, "unit_price", Number(e.target.value))}
                          style={{ width: "100%", padding: "4px 6px", textAlign: "right" }}
                        />
                      </td>
                      <td className="tabular-nums" style={{ textAlign: "right", fontWeight: 600 }}>
                        {money(it.quantity * it.unit_price, currency)}
                      </td>
                      <td>
                        <button
                          onClick={() => removeItem(idx)}
                          style={{ background: "transparent", border: "none", color: "#ef4444", cursor: "pointer", padding: 4 }}
                        >
                          <Trash2 size={15} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "var(--space-4)", fontSize: "1rem", fontWeight: 700 }}>
              <span>Tổng giá trị sau hiệu đính:</span>
              <span className="tabular-nums" style={{ color: "var(--color-primary)" }}>
                {money(totalValue, currency)}
              </span>
            </div>
          </div>
        ) : (
          <div className="content-card" style={{ padding: "var(--space-8)", textAlign: "center" }}>
            <FileText size={36} style={{ opacity: 0.3, margin: "0 auto var(--space-2)" }} />
            <p>Chọn một đơn hàng từ danh sách bên trái để bắt đầu rà soát.</p>
          </div>
        )}
      </div>
    </div>
  );
}
