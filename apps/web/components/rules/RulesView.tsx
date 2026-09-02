"use client";

import { useEffect, useState } from "react";
import { ShieldAlert, AlertTriangle, Save, RefreshCw, CheckCircle2, AlertCircle } from "lucide-react";
import { api, describeError } from "@/app/lib/api/client";
import type { RuleConfig } from "@/app/lib/api/types";
import { useRipple } from "@/app/lib/useRipple";

export function RulesView() {
  const { createRipple } = useRipple();
  const [config, setConfig] = useState<RuleConfig>({
    price_tolerance_percent: 0.0,
    stock_safety_margin: 0,
    allow_inactive_sku: false,
    auto_approve_ready: false,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const fetchConfig = async () => {
    setIsLoading(true);
    try {
      const cfg = await api.rules.getConfig();
      setConfig(cfg);
    } catch {
      // Offline fallback
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    api.rules
      .getConfig()
      .then((cfg) => {
        if (mounted) setConfig(cfg);
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setFeedback(null);
    try {
      const res = await api.rules.updateConfig(config);
      setConfig(res.policy);
      setFeedback({
        type: "success",
        message: "Đã cập nhật cấu hình quy tắc và chính sách kiểm định thành công!",
      });
    } catch (err) {
      setFeedback({
        type: "error",
        message: describeError(err),
      });
    } finally {
      setIsSaving(false);
    }
  };

  const coreRules = [
    {
      code: "PRICE_MISMATCH",
      name: "Chênh lệch giá so với Catalog",
      description: "Yêu cầu rà soát khi đơn giá tiếp nhận sai khác so với bảng giá Catalog đang hiệu lực.",
      severity: "Cảnh báo (Warning)",
      owner: "Phòng Kinh doanh",
    },
    {
      code: "INSUFFICIENT_STOCK",
      name: "Không đủ tồn kho khả dụng",
      description: "Cảnh báo khi số lượng đặt hàng vượt quá số lượng tồn kho khả dụng tại thời điểm kiểm tra.",
      severity: "Cảnh báo (Warning)",
      owner: "Phòng Vận hành & Kho",
    },
    {
      code: "UNKNOWN_SKU",
      name: "Mã SKU không tồn tại",
      description: "Chặn ngay lập tức các dòng hàng có mã SKU chưa được khai báo trong hệ thống danh mục.",
      severity: "Lỗi chặn (Fatal Error)",
      owner: "Quản trị danh mục",
    },
    {
      code: "INACTIVE_SKU",
      name: "Sản phẩm ngừng kinh doanh",
      description: "Chặn các đơn đặt sản phẩm đã vô hiệu hóa hoặc kết thúc vòng đời thương mại.",
      severity: "Lỗi chặn (Fatal Error)",
      owner: "Phòng Sản phẩm",
    },
    {
      code: "DUPLICATE_PO",
      name: "Trùng lặp mã đơn hàng (PO)",
      description: "Chặn các đơn hàng trùng mã số PO từ cùng một khách hàng đã được lưu vết trước đó.",
      severity: "Lỗi chặn (Fatal Error)",
      owner: "Phòng Kế toán & Tài chính",
    },
    {
      code: "UOM_CONVERSION_MISSING",
      name: "Thiếu cấu hình quy đổi đơn vị (UOM)",
      description: "Cảnh báo khi đơn vị đặt hàng khác đơn vị cơ sở nhưng chưa khai báo hệ số quy đổi.",
      severity: "Cảnh báo (Warning)",
      owner: "Phòng Chuỗi cung ứng",
    },
  ];

  return (
    <div className="page simple-page page-enter">
      <div className="page-heading">
        <div>
          <p className="eyebrow">QUẢN TRỊ QUY TẮC &amp; CHÍNH SÁCH</p>
          <h1>Quy tắc kiểm tra &amp; Tham số chính sách</h1>
          <p>Hệ thống quy tắc xác thực định trước được áp dụng đồng bộ cho mọi đơn hàng tiếp nhận.</p>
        </div>
        <button
          className="secondary-button interactive"
          onClick={(e) => {
            createRipple(e);
            void fetchConfig();
          }}
          disabled={isLoading}
          style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-1)" }}
        >
          <RefreshCw size={15} className={isLoading ? "animate-spin" : ""} />
          <span>Làm mới</span>
        </button>
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

      {/* Dynamic Config Parameters Card */}
      <form onSubmit={handleSave} className="content-card" style={{ padding: "var(--space-5)", marginBottom: "var(--space-5)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-4)" }}>
          <h2 style={{ fontSize: "1.1rem", margin: 0 }}>Tham số kiểm tra động (Policy Parameters)</h2>
          <button
            type="submit"
            className="primary-button interactive"
            disabled={isSaving}
            style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-1)" }}
          >
            <Save size={15} />
            <span>{isSaving ? "Đang lưu..." : "Lưu thay đổi chính sách"}</span>
          </button>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-4)" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: 4 }}>
              Dung sai chênh lệch giá cho phép (%)
            </label>
            <input
              type="number"
              step="0.1"
              min="0"
              max="50"
              value={config.price_tolerance_percent}
              onChange={(e) => setConfig({ ...config, price_tolerance_percent: Number(e.target.value) })}
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: "var(--radius-sm)",
                border: "1px solid var(--color-outline-variant)",
                backgroundColor: "var(--color-surface-container-low)",
              }}
            />
            <small style={{ color: "var(--color-outline)", display: "block", marginTop: 4 }}>
              Mặc định: 0.0% (mọi sai lệch đều tạo cảnh báo).
            </small>
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: 4 }}>
              Biên độ an toàn tồn kho kho (Safety Margin - Đơn vị)
            </label>
            <input
              type="number"
              min="0"
              value={config.stock_safety_margin}
              onChange={(e) => setConfig({ ...config, stock_safety_margin: Number(e.target.value) })}
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: "var(--radius-sm)",
                border: "1px solid var(--color-outline-variant)",
                backgroundColor: "var(--color-surface-container-low)",
              }}
            />
            <small style={{ color: "var(--color-outline)", display: "block", marginTop: 4 }}>
              Lượng tồn kho dự phòng giữ lại không được phân bổ vào đơn mới.
            </small>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginTop: "var(--space-2)" }}>
            <input
              id="allowInactive"
              type="checkbox"
              checked={config.allow_inactive_sku}
              onChange={(e) => setConfig({ ...config, allow_inactive_sku: e.target.checked })}
              style={{ width: 18, height: 18 }}
            />
            <label htmlFor="allowInactive" style={{ fontSize: "0.875rem", cursor: "pointer" }}>
              Cho phép tiếp nhận SKU ngừng kinh doanh (Chuyển từ Lỗi chặn sang Cảnh báo)
            </label>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginTop: "var(--space-2)" }}>
            <input
              id="autoApprove"
              type="checkbox"
              checked={config.auto_approve_ready}
              onChange={(e) => setConfig({ ...config, auto_approve_ready: e.target.checked })}
              style={{ width: 18, height: 18 }}
            />
            <label htmlFor="autoApprove" style={{ fontSize: "0.875rem", cursor: "pointer" }}>
              Tự động phê duyệt các đơn hàng ở trạng thái READY (0 lỗi, 0 cảnh báo)
            </label>
          </div>
        </div>
      </form>

      {/* Core Rules List */}
      <section className="content-card rules-card">
        <div style={{ padding: "var(--space-4) var(--space-5)", borderBottom: "1px solid var(--color-outline-variant)" }}>
          <h2 style={{ fontSize: "1.05rem", margin: 0 }}>Quy tắc kiểm định cốt lõi ({coreRules.length})</h2>
        </div>
        {coreRules.map((rule) => {
          const isError = rule.severity.includes("Lỗi");
          return (
            <div className="rule-row interactive" key={rule.code} style={{ padding: "var(--space-4) var(--space-5)" }}>
              <span
                className={`rule-symbol ${isError ? "block" : "review"}`}
                style={{ display: "flex", alignItems: "center", justifyContent: "center" }}
              >
                {isError ? (
                  <ShieldAlert size={16} strokeWidth={2.2} />
                ) : (
                  <AlertTriangle size={15} strokeWidth={2.2} />
                )}
              </span>
              <div>
                <strong>{rule.name}</strong>
                <p>{rule.description}</p>
                <code style={{ fontSize: "0.75rem", color: "var(--color-primary)" }}>{rule.code}</code>
              </div>
              <span className={`severity ${isError ? "severity-block" : "severity-review"}`}>
                {rule.severity}
              </span>
              <span className="rule-owner">{rule.owner}</span>
            </div>
          );
        })}
      </section>
    </div>
  );
}
