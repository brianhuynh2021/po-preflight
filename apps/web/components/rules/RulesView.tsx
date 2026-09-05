"use client";

import { useEffect, useState } from "react";
import {
  ShieldAlert,
  AlertTriangle,
  Save,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Building2,
  Plus,
  Trash2,
  Layers,
  Sparkles,
  Info,
  Globe2,
} from "lucide-react";
import { api, describeError } from "@/app/lib/api/client";
import type { RuleConfig, OrganizationScope, ConfigurableRuleItem } from "@/app/lib/api/types";
import { useRipple } from "@/app/lib/useRipple";

interface ConfigurableRule {
  id: string;
  code: string;
  name: string;
  description: string;
  category: "price" | "stock" | "catalog" | "credit" | "document" | string;
  severity: "block" | "warning" | "disabled";
  owner: string;
  enabled: boolean;
  scope: string;
  customCondition?: string;
  custom_condition?: string | null;
}

const DEFAULT_SCOPES: OrganizationScope[] = [
  { code: "global", name: "Toàn Doanh Nghiệp (Global)", description: "Quy tắc nền tảng chung", icon: "🌐" },
  { code: "north", name: "Chi Nhánh Miền Bắc", description: "Kho Hải Phòng & Hà Nội", icon: "🏔️" },
  { code: "south", name: "Chi Nhánh Miền Nam", description: "Kho Bình Dương & TP.HCM", icon: "🌴" },
  { code: "mt", name: "Chuỗi Siêu Thị (MT)", description: "WinMart, AEON, Co.opmart", icon: "🛒" },
  { code: "gt", name: "Đại Lý Tỉnh (GT)", description: "Nhà phân phối truyền thống", icon: "🏪" },
];

const INITIAL_RULES: ConfigurableRule[] = [
  {
    id: "r1",
    code: "PRICE_MISMATCH",
    name: "Chênh lệch giá bán so với Catalog hợp đồng",
    description: "Tự động phát hiện khi đơn giá tiếp nhận sai khác so với bảng giá Catalog đang hiệu lực.",
    category: "price",
    severity: "warning",
    owner: "Phòng Kinh doanh",
    enabled: true,
    scope: "global",
  },
  {
    id: "r2",
    code: "INSUFFICIENT_STOCK",
    name: "Không đủ tồn kho khả dụng (ATP)",
    description: "Cảnh báo khi số lượng đặt vượt quá tồn kho khả dụng thực tế sau khi trừ phân bổ giữ chỗ.",
    category: "stock",
    severity: "warning",
    owner: "Phòng Vận hành & Kho",
    enabled: true,
    scope: "global",
  },
  {
    id: "r3",
    code: "UNKNOWN_SKU",
    name: "Mã SKU chưa khai báo trong hệ thống",
    description: "Chặn ngay lập tức các dòng hàng có mã sản phẩm lạ chưa có trong Master Data.",
    category: "catalog",
    severity: "block",
    owner: "Quản trị danh mục",
    enabled: true,
    scope: "global",
  },
  {
    id: "r4",
    code: "INACTIVE_SKU",
    name: "Sản phẩm đã ngừng kinh doanh",
    description: "Chặn các đơn đặt hàng chứa sản phẩm đã vô hiệu hóa hoặc kết thúc vòng đời thương mại.",
    category: "catalog",
    severity: "block",
    owner: "Phòng Sản phẩm",
    enabled: true,
    scope: "global",
  },
  {
    id: "r5",
    code: "DUPLICATE_PO",
    name: "Nghi ngờ trùng lặp mã đơn hàng (PO)",
    description: "Chặn các đơn hàng gửi trùng số hiệu PO từ cùng một khách hàng trong vòng 48 giờ.",
    category: "document",
    severity: "block",
    owner: "Phòng Kế toán & Tài chính",
    enabled: true,
    scope: "global",
  },
  {
    id: "r6",
    code: "UOM_CONVERSION_MISSING",
    name: "Thiếu cấu hình quy đổi đơn vị (UOM)",
    description: "Cảnh báo khi đơn vị đặt hàng khác đơn vị cơ sở kho nhưng chưa khai báo hệ số quy đổi.",
    category: "catalog",
    severity: "warning",
    owner: "Phòng Chuỗi cung ứng",
    enabled: true,
    scope: "global",
  },
  {
    id: "r7",
    code: "REGIONAL_FREIGHT_SURCHARGE",
    name: "Phụ phí vận chuyển vùng sâu / liên tỉnh",
    description: "Tự động kiểm tra phụ cước vận chuyển đối với đơn hàng giao tới kho ngoại tỉnh Miền Bắc.",
    category: "price",
    severity: "warning",
    owner: "Phòng Logistics",
    enabled: true,
    scope: "north",
    customCondition: "Áp dụng cho điểm giao hàng ngoài bán kính 50km từ kho chính",
  },
  {
    id: "r8",
    code: "MT_STRICT_PALLET_MOQ",
    name: "Quy cách đóng thùng & Pallet siêu thị (MT)",
    description: "Bắt buộc số lượng đặt phải là bội số của Pallet chuẩn (không xé lẻ thùng) với kênh Siêu thị.",
    category: "stock",
    severity: "block",
    owner: "Phòng Khách hàng Chuỗi MT",
    enabled: true,
    scope: "mt",
    customCondition: "Bắt buộc số lượng chia hết cho MOQ thùng carton",
  },
];

export function RulesView() {
  const { createRipple } = useRipple();
  const [scopes, setScopes] = useState<OrganizationScope[]>(DEFAULT_SCOPES);
  const [selectedScope, setSelectedScope] = useState<string>("global");
  const [rules, setRules] = useState<ConfigurableRule[]>(INITIAL_RULES);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showAddScopeModal, setShowAddScopeModal] = useState(false);

  // New rule draft state
  const [newRuleName, setNewRuleName] = useState("");
  const [newRuleCode, setNewRuleCode] = useState("");
  const [newRuleDesc, setNewRuleDesc] = useState("");
  const [newRuleCategory, setNewRuleCategory] = useState<ConfigurableRule["category"]>("price");
  const [newRuleSeverity, setNewRuleSeverity] = useState<ConfigurableRule["severity"]>("warning");
  const [newRuleOwner, setNewRuleOwner] = useState("Phòng Kinh doanh");
  const [newRuleCondition, setNewRuleCondition] = useState("");

  // New scope draft state
  const [newScopeCode, setNewScopeCode] = useState("");
  const [newScopeName, setNewScopeName] = useState("");
  const [newScopeDesc, setNewScopeDesc] = useState("");
  const [newScopeIcon, setNewScopeIcon] = useState("🏢");

  const [config, setConfig] = useState<RuleConfig>({
    price_tolerance_percent: 0.0,
    stock_safety_margin: 0,
    allow_inactive_sku: false,
    auto_approve_ready: false,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Manual refresh handler
  const refreshAllData = async () => {
    setIsLoading(true);
    try {
      const [cfg, dbScopes, dbRules] = await Promise.all([
        api.rules.getConfig().catch(() => null),
        api.rules.getScopes().catch(() => null),
        api.rules.listDefinitions("all").catch(() => null),
      ]);

      if (cfg) setConfig(cfg);
      if (dbScopes && dbScopes.length > 0) {
        setScopes(dbScopes);
      }
      if (dbRules && dbRules.length > 0) {
        const mappedRules: ConfigurableRule[] = dbRules.map((r: ConfigurableRuleItem) => ({
          id: r.id,
          code: r.code,
          name: r.name,
          description: r.description,
          category: r.category,
          severity: r.severity,
          owner: r.owner,
          enabled: r.enabled,
          scope: r.scope,
          customCondition: r.custom_condition || undefined,
          custom_condition: r.custom_condition,
        }));
        setRules(mappedRules);
      }
    } catch {
      // Offline fallback preserves initial states
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let active = true;
    Promise.all([
      api.rules.getConfig().catch(() => null),
      api.rules.getScopes().catch(() => null),
      api.rules.listDefinitions("all").catch(() => null),
    ])
      .then(([cfg, dbScopes, dbRules]) => {
        if (!active) return;
        if (cfg) setConfig(cfg);
        if (dbScopes && dbScopes.length > 0) setScopes(dbScopes);
        if (dbRules && dbRules.length > 0) {
          const mappedRules: ConfigurableRule[] = dbRules.map((r: ConfigurableRuleItem) => ({
            id: r.id,
            code: r.code,
            name: r.name,
            description: r.description,
            category: r.category,
            severity: r.severity,
            owner: r.owner,
            enabled: r.enabled,
            scope: r.scope,
            customCondition: r.custom_condition || undefined,
            custom_condition: r.custom_condition,
          }));
          setRules(mappedRules);
        }
      })
      .catch(() => {});

    return () => {
      active = false;
    };
  }, []);

  const handleToggleRule = async (id: string) => {
    const target = rules.find((r) => r.id === id);
    if (!target) return;
    const newEnabled = !target.enabled;

    // Optimistic UI update
    setRules((prev) =>
      prev.map((r) => (r.id === id ? { ...r, enabled: newEnabled } : r))
    );

    try {
      await api.rules.updateDefinition(id, { enabled: newEnabled });
      setFeedback({
        type: "success",
        message: `Đã ${newEnabled ? "kích hoạt" : "tạm dừng"} quy tắc [${target.code}] thành công và đồng bộ CSDL!`,
      });
    } catch (err) {
      // Revert on error
      setRules((prev) =>
        prev.map((r) => (r.id === id ? { ...r, enabled: target.enabled } : r))
      );
      setFeedback({
        type: "error",
        message: `Lỗi cập nhật trạng thái quy tắc: ${describeError(err)}`,
      });
    }
  };

  const handleChangeSeverity = async (id: string, severity: "block" | "warning" | "disabled") => {
    const target = rules.find((r) => r.id === id);
    if (!target) return;
    const prevSeverity = target.severity;
    const prevEnabled = target.enabled;
    const newEnabled = severity !== "disabled";

    // Optimistic UI update
    setRules((prev) =>
      prev.map((r) => (r.id === id ? { ...r, severity, enabled: newEnabled } : r))
    );

    try {
      await api.rules.updateDefinition(id, { severity, enabled: newEnabled });
      setFeedback({
        type: "success",
        message: `Đã cập nhật mức độ xử lý [${severity.toUpperCase()}] cho quy tắc [${target.code}]!`,
      });
    } catch (err) {
      // Revert on error
      setRules((prev) =>
        prev.map((r) => (r.id === id ? { ...r, severity: prevSeverity, enabled: prevEnabled } : r))
      );
      setFeedback({
        type: "error",
        message: `Lỗi cập nhật mức độ: ${describeError(err)}`,
      });
    }
  };

  const handleAddRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRuleName || !newRuleCode) return;

    const formattedCode = newRuleCode.toUpperCase().replace(/\s+/g, "_");
    const rulePayload = {
      code: formattedCode,
      name: newRuleName,
      description: newRuleDesc || "Quy tắc nghiệp vụ mở rộng tùy biến",
      category: newRuleCategory,
      severity: newRuleSeverity,
      owner: newRuleOwner,
      enabled: newRuleSeverity !== "disabled",
      scope: selectedScope,
      custom_condition: newRuleCondition || null,
    };

    try {
      const created = await api.rules.createDefinition(rulePayload);
      const newRuleItem: ConfigurableRule = {
        id: created.id,
        code: created.code,
        name: created.name,
        description: created.description,
        category: created.category,
        severity: created.severity,
        owner: created.owner,
        enabled: created.enabled,
        scope: created.scope,
        customCondition: created.custom_condition || undefined,
        custom_condition: created.custom_condition,
      };

      setRules((prev) => [newRuleItem, ...prev.filter((r) => r.id !== newRuleItem.id)]);
      setShowAddModal(false);
      setNewRuleName("");
      setNewRuleCode("");
      setNewRuleDesc("");
      setNewRuleCondition("");
      setFeedback({
        type: "success",
        message: `Đã lưu quy tắc mới [${created.code}] vào CSDL cho phạm vi [${selectedScope.toUpperCase()}]!`,
      });
    } catch (err) {
      setFeedback({
        type: "error",
        message: `Không thể tạo quy tắc: ${describeError(err)}`,
      });
    }
  };

  const handleDeleteRule = async (id: string) => {
    const target = rules.find((r) => r.id === id);
    if (!target) return;

    if (!confirm(`Bạn có chắc chắn muốn xóa vĩnh viễn quy tắc [${target.name}] (${target.code})?`)) {
      return;
    }

    try {
      await api.rules.deleteDefinition(id);
      setRules((prev) => prev.filter((r) => r.id !== id));
      setFeedback({
        type: "success",
        message: `Đã xóa quy tắc [${target.code}] khỏi hệ thống CSDL!`,
      });
    } catch (err) {
      setFeedback({
        type: "error",
        message: `Lỗi khi xóa quy tắc: ${describeError(err)}`,
      });
    }
  };

  const handleAddScope = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newScopeCode || !newScopeName) return;

    const formattedCode = newScopeCode.toLowerCase().trim().replace(/\s+/g, "_");
    try {
      const created = await api.rules.createScope({
        code: formattedCode,
        name: newScopeName,
        description: newScopeDesc || "Phạm vi chính sách mở rộng",
        icon: newScopeIcon || "🏢",
      });

      setScopes((prev) => [...prev, created]);
      setSelectedScope(created.code);
      setShowAddScopeModal(false);
      setNewScopeCode("");
      setNewScopeName("");
      setNewScopeDesc("");
      setNewScopeIcon("🏢");
      setFeedback({
        type: "success",
        message: `Đã tạo mới phạm vi chính sách [${created.name}] (${created.code}) thành công!`,
      });
    } catch (err) {
      setFeedback({
        type: "error",
        message: `Lỗi tạo phạm vi chính sách: ${describeError(err)}`,
      });
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setFeedback(null);
    try {
      const res = await api.rules.updateConfig(config);
      setConfig(res.policy);
      setFeedback({
        type: "success",
        message: `Đã cập nhật chính sách đa tầng & ma trận quy tắc [${selectedScope.toUpperCase()}] thành công!`,
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

  // Filter rules by active scope + global inherited rules
  const visibleRules = rules.filter(
    (r) => r.scope === selectedScope || (selectedScope !== "global" && r.scope === "global")
  );

  const activeScopeObj = scopes.find((s) => s.code === selectedScope);

  return (
    <div style={{ padding: "var(--space-6) var(--space-8)", maxWidth: "1400px", margin: "0 auto" }}>
      {/* 1. Page Header */}
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
              Enterprise Dynamic Policy Engine
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
            Quản Trị Quy Tắc &amp; Ma Trận Chính Sách Phân Cấp
          </h1>
          <p style={{ margin: "4px 0 0", fontSize: "0.875rem", color: "var(--muted)" }}>
            Tách biệt cơ chế xác thực cốt lõi và chính sách phân cấp theo Vùng miền, Chi nhánh &amp; Kênh phân phối. Lưu trữ động vào CSDL.
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <button
            type="button"
            className="secondary-button interactive"
            onClick={(e) => {
              createRipple(e);
              setIsLoading(true);
              void refreshAllData();
            }}
            disabled={isLoading}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "8px 16px",
              borderRadius: "8px",
            }}
          >
            <RefreshCw size={14} className={isLoading ? "animate-spin" : ""} />
            <span>{isLoading ? "Đang tải..." : "Làm mới CSDL"}</span>
          </button>

          <button
            type="button"
            onClick={() => setShowAddModal(true)}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "8px 16px",
              borderRadius: "8px",
              background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
              color: "#ffffff",
              border: "none",
              fontWeight: 600,
              fontSize: "0.8125rem",
              cursor: "pointer",
              boxShadow: "0 2px 6px rgba(16,185,129,0.3)",
            }}
          >
            <Plus size={15} />
            <span>Thêm quy tắc mới</span>
          </button>
        </div>
      </div>

      {feedback && (
        <div
          style={{
            margin: "0 0 var(--space-5) 0",
            padding: "12px 18px",
            borderRadius: "12px",
            border: feedback.type === "success" ? "1px solid rgba(16, 185, 129, 0.3)" : "1px solid rgba(239, 68, 68, 0.3)",
            backgroundColor: feedback.type === "success" ? "rgba(16, 185, 129, 0.08)" : "rgba(239, 68, 68, 0.08)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "var(--space-2)",
            color: feedback.type === "success" ? "var(--color-primary)" : "var(--color-error)",
            fontSize: "0.875rem",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            {feedback.type === "success" ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
            <strong>{feedback.message}</strong>
          </div>
          <button
            onClick={() => setFeedback(null)}
            style={{ background: "none", border: "none", cursor: "pointer", fontWeight: 700 }}
          >
            ×
          </button>
        </div>
      )}

      {/* 2. Hierarchical Scope Switcher (Google & MIT Style Policy Cascade) */}
      <div
        style={{
          background: "var(--paper)",
          border: "1px solid var(--line)",
          borderRadius: "16px",
          padding: "16px 20px",
          marginBottom: "var(--space-5)",
          boxShadow: "var(--shadow-elevation-1)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "12px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Layers size={18} color="var(--color-primary)" />
            <span style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--ink)" }}>
              Phạm Vi Áp Dụng Chính Sách (Policy Scopes):
            </span>
          </div>

          <div
            style={{
              display: "inline-flex",
              background: "var(--canvas)",
              padding: "4px",
              borderRadius: "10px",
              border: "1px solid var(--line)",
              flexWrap: "wrap",
              gap: "4px",
              alignItems: "center",
            }}
          >
            {scopes.map((scope) => {
              const isSelected = selectedScope === scope.code;
              const displayLabel = scope.icon ? `${scope.icon} ${scope.name}` : scope.name;
              return (
                <button
                  key={scope.code}
                  type="button"
                  onClick={() => setSelectedScope(scope.code)}
                  style={{
                    padding: "6px 14px",
                    fontSize: "0.8125rem",
                    fontWeight: isSelected ? 700 : 500,
                    color: isSelected ? "#ffffff" : "var(--muted)",
                    background: isSelected ? "var(--color-primary)" : "transparent",
                    border: "none",
                    borderRadius: "8px",
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  <span>{displayLabel}</span>
                </button>
              );
            })}

            <button
              type="button"
              onClick={() => setShowAddScopeModal(true)}
              title="Thêm phạm vi hoặc chi nhánh mới vào CSDL"
              style={{
                padding: "6px 12px",
                fontSize: "0.8125rem",
                fontWeight: 600,
                color: "var(--color-primary)",
                background: "rgba(16,185,129,0.08)",
                border: "1px dashed var(--color-primary)",
                borderRadius: "8px",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "4px",
                transition: "all 0.15s ease",
              }}
            >
              <Plus size={14} />
              <span>Thêm phạm vi</span>
            </button>
          </div>
        </div>

        <div
          style={{
            marginTop: "12px",
            paddingTop: "12px",
            borderTop: "1px solid var(--line)",
            fontSize: "0.75rem",
            color: "var(--muted)",
            display: "flex",
            alignItems: "center",
            gap: "6px",
          }}
        >
          <Info size={14} color="var(--color-primary)" />
          <span>
            {selectedScope === "global"
              ? "Đang cấu hình Chính sách Gốc (Global Policy Invariants). Mọi chi nhánh và phân khúc đối tác sẽ tự động kế thừa bộ luật này."
              : `Đang cấu hình Quy tắc Riêng cho [${activeScopeObj?.name || selectedScope.toUpperCase()}]. Các quy tắc tại đây sẽ ghi đè (Override) hoặc bổ sung thêm vào chính sách Toàn doanh nghiệp.`}
          </span>
        </div>
      </div>

      {/* 3. Scope Parameters Form */}
      <form
        onSubmit={handleSave}
        style={{
          background: "var(--paper)",
          border: "1px solid var(--line)",
          borderRadius: "16px",
          padding: "24px",
          marginBottom: "var(--space-6)",
          boxShadow: "var(--shadow-elevation-1)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-4)" }}>
          <div>
            <h2 style={{ fontSize: "1rem", fontWeight: 700, margin: 0, color: "var(--ink)" }}>
              Tham Số Kiểm Tra Động Cho [{selectedScope.toUpperCase()}]
            </h2>
            <p style={{ margin: "2px 0 0", fontSize: "0.8125rem", color: "var(--muted)" }}>
              Tùy biến dung sai giá, tỷ lệ tồn kho dự phòng và cơ chế Human-in-the-Loop
            </p>
          </div>
          <button
            type="submit"
            disabled={isSaving}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "8px 18px",
              borderRadius: "8px",
              background: "var(--color-primary)",
              color: "#ffffff",
              border: "none",
              fontWeight: 600,
              fontSize: "0.8125rem",
              cursor: "pointer",
            }}
          >
            <Save size={15} />
            <span>{isSaving ? "Đang lưu..." : "Lưu thay đổi chính sách"}</span>
          </button>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "var(--space-4)" }}>
          <div style={{ background: "var(--canvas)", padding: "16px", borderRadius: "12px", border: "1px solid var(--line)" }}>
            <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: 6, color: "var(--ink)" }}>
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
                borderRadius: "8px",
                border: "1px solid var(--line)",
                backgroundColor: "var(--paper)",
                color: "var(--ink)",
                fontWeight: 600,
              }}
            />
            <small style={{ color: "var(--muted)", display: "block", marginTop: 6, fontSize: "0.75rem" }}>
              Khoảng lệch giá tối đa không kích hoạt cảnh báo (Khuyên dùng: 0.0% cho Siêu thị, 0.5% cho Đại lý).
            </small>
          </div>

          <div style={{ background: "var(--canvas)", padding: "16px", borderRadius: "12px", border: "1px solid var(--line)" }}>
            <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: 6, color: "var(--ink)" }}>
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
                borderRadius: "8px",
                border: "1px solid var(--line)",
                backgroundColor: "var(--paper)",
                color: "var(--ink)",
                fontWeight: 600,
              }}
            />
            <small style={{ color: "var(--muted)", display: "block", marginTop: 6, fontSize: "0.75rem" }}>
              Lượng tồn kho đệm dự phòng không được phân bổ (Ví dụ: 10 đơn vị giữ chỗ khẩn cấp).
            </small>
          </div>

          <div style={{ background: "var(--canvas)", padding: "16px", borderRadius: "12px", border: "1px solid var(--line)", display: "flex", flexDirection: "column", justifyContent: "center" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <input
                id="allowInactive"
                type="checkbox"
                checked={config.allow_inactive_sku}
                onChange={(e) => setConfig({ ...config, allow_inactive_sku: e.target.checked })}
                style={{ width: 18, height: 18, accentColor: "var(--color-primary)", cursor: "pointer" }}
              />
              <label htmlFor="allowInactive" style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--ink)", cursor: "pointer" }}>
                Cho phép tiếp nhận SKU ngừng kinh doanh
              </label>
            </div>
            <small style={{ color: "var(--muted)", display: "block", marginTop: 6, fontSize: "0.75rem" }}>
              Hạ cấp từ Lỗi chặn (Fatal) sang Cảnh báo (Warning) cho các đợt thanh lý xả kho.
            </small>
          </div>

          <div style={{ background: "var(--canvas)", padding: "16px", borderRadius: "12px", border: "1px solid var(--line)", display: "flex", flexDirection: "column", justifyContent: "center" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <input
                id="autoApprove"
                type="checkbox"
                checked={config.auto_approve_ready}
                onChange={(e) => setConfig({ ...config, auto_approve_ready: e.target.checked })}
                style={{ width: 18, height: 18, accentColor: "var(--color-primary)", cursor: "pointer" }}
              />
              <label htmlFor="autoApprove" style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--ink)", cursor: "pointer" }}>
                Tự động duyệt đơn READY thẳng vào ERP
              </label>
            </div>
            <small style={{ color: "var(--muted)", display: "block", marginTop: 6, fontSize: "0.75rem" }}>
              Đơn hàng 0 lỗi, 0 cảnh báo được đồng bộ ngay không cần chữ ký con người (STP Mode).
            </small>
          </div>
        </div>
      </form>

      {/* 4. Interactive Policy Rules Matrix (Google & MIT Style) */}
      <section
        style={{
          background: "var(--paper)",
          border: "1px solid var(--line)",
          borderRadius: "16px",
          padding: "24px",
          boxShadow: "var(--shadow-elevation-1)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "8px" }}>
          <div>
            <h2 style={{ fontSize: "1.05rem", fontWeight: 700, margin: 0, color: "var(--ink)" }}>
              Ma Trận Quy Tắc Nghiệp Vụ Có Hiệu Lực ({visibleRules.length} quy tắc)
            </h2>
            <p style={{ margin: "2px 0 0", fontSize: "0.8125rem", color: "var(--muted)" }}>
              Linh hoạt Bật/Tắt, đổi mức độ nghiêm trọng và gán điều kiện theo từng phòng ban/vùng miền
            </p>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "12px", fontSize: "0.75rem" }}>
            <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#ef4444" }} />
              Lỗi chặn (Fatal Block)
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#f59e0b" }} />
              Cảnh báo cần duyệt (Warning)
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--muted)" }} />
              Bỏ qua (Disabled)
            </span>
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {visibleRules.map((rule) => {
            const isBlock = rule.severity === "block";
            const isWarning = rule.severity === "warning";
            const isDisabled = rule.severity === "disabled" || !rule.enabled;

            return (
              <div
                key={rule.id}
                style={{
                  background: isDisabled ? "var(--canvas)" : "var(--paper)",
                  border: "1px solid var(--line)",
                  borderRadius: "12px",
                  padding: "16px 20px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  flexWrap: "wrap",
                  gap: "16px",
                  opacity: isDisabled ? 0.6 : 1,
                  transition: "all 0.2s ease",
                }}
              >
                {/* Left: Icon & Description */}
                <div style={{ display: "flex", alignItems: "flex-start", gap: "14px", flex: "1 1 450px" }}>
                  <div
                    style={{
                      width: "36px",
                      height: "36px",
                      borderRadius: "10px",
                      background: isDisabled
                        ? "var(--line)"
                        : isBlock
                        ? "rgba(239, 68, 68, 0.12)"
                        : "rgba(245, 158, 11, 0.12)",
                      color: isDisabled
                        ? "var(--muted)"
                        : isBlock
                        ? "var(--color-error)"
                        : "var(--color-warning)",
                      display: "grid",
                      placeItems: "center",
                      flexShrink: 0,
                    }}
                  >
                    {isBlock ? <ShieldAlert size={18} /> : <AlertTriangle size={18} />}
                  </div>

                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                      <strong style={{ fontSize: "0.875rem", color: "var(--ink)" }}>{rule.name}</strong>
                      <code
                        style={{
                          fontSize: "0.6875rem",
                          padding: "2px 6px",
                          borderRadius: "4px",
                          background: "var(--canvas)",
                          border: "1px solid var(--line)",
                          color: "var(--color-primary)",
                          fontFamily: "var(--font-geist-mono), monospace",
                        }}
                      >
                        {rule.code}
                      </code>
                      {rule.scope !== "global" && (
                        <span
                          style={{
                            fontSize: "0.6875rem",
                            padding: "2px 7px",
                            borderRadius: "9999px",
                            background: "rgba(59, 130, 246, 0.12)",
                            color: "#3b82f6",
                            fontWeight: 700,
                          }}
                        >
                          {rule.scope.toUpperCase()}
                        </span>
                      )}
                    </div>
                    <p style={{ margin: "4px 0 0", fontSize: "0.8125rem", color: "var(--muted)" }}>
                      {rule.description}
                    </p>
                    {(rule.custom_condition || rule.customCondition) && (
                      <div style={{ marginTop: "4px", fontSize: "0.75rem", color: "#3b82f6", fontWeight: 500 }}>
                        ↳ Điều kiện: {rule.custom_condition || rule.customCondition}
                      </div>
                    )}
                  </div>
                </div>

                {/* Center: Rule Owner */}
                <div style={{ minWidth: "150px" }}>
                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "6px",
                      fontSize: "0.75rem",
                      padding: "4px 10px",
                      borderRadius: "6px",
                      background: "var(--canvas)",
                      border: "1px solid var(--line)",
                      color: "var(--muted)",
                      fontWeight: 500,
                    }}
                  >
                    <Building2 size={12} />
                    {rule.owner}
                  </span>
                </div>

                {/* Right: Severity Dropdown & Toggle Switch */}
                <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
                  {/* Severity selector */}
                  <select
                    value={rule.severity}
                    onChange={(e) => void handleChangeSeverity(rule.id, e.target.value as ConfigurableRule["severity"])}
                    style={{
                      padding: "6px 10px",
                      fontSize: "0.8125rem",
                      fontWeight: 600,
                      borderRadius: "8px",
                      border: "1px solid var(--line)",
                      background: "var(--paper)",
                      color: isBlock ? "#ef4444" : isWarning ? "#d97706" : "var(--muted)",
                      cursor: "pointer",
                    }}
                  >
                    <option value="block">🔴 Lỗi chặn (Fatal Error)</option>
                    <option value="warning">🟡 Cảnh báo (Warning)</option>
                    <option value="disabled">⚪ Tạm ngưng (Disabled)</option>
                  </select>

                  {/* Toggle Switch */}
                  <button
                    type="button"
                    onClick={() => void handleToggleRule(rule.id)}
                    title={rule.enabled ? "Đang kích hoạt quy tắc (Bấm để tạm dừng)" : "Đã tạm dừng quy tắc (Bấm để kích hoạt)"}
                    style={{
                      width: "44px",
                      height: "24px",
                      borderRadius: "9999px",
                      background: rule.enabled ? "var(--color-primary)" : "var(--line)",
                      border: "none",
                      position: "relative",
                      cursor: "pointer",
                      transition: "background 0.2s ease",
                      padding: 0,
                    }}
                  >
                    <span
                      style={{
                        position: "absolute",
                        top: "2px",
                        left: rule.enabled ? "22px" : "2px",
                        width: "20px",
                        height: "20px",
                        borderRadius: "50%",
                        background: "#ffffff",
                        boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
                        transition: "left 0.2s ease",
                      }}
                    />
                  </button>

                  {/* Delete rule button */}
                  <button
                    type="button"
                    onClick={() => void handleDeleteRule(rule.id)}
                    title="Xóa quy tắc khỏi CSDL"
                    style={{
                      background: "none",
                      border: "none",
                      color: "var(--muted)",
                      cursor: "pointer",
                      padding: "4px",
                      borderRadius: "4px",
                      display: "grid",
                      placeItems: "center",
                    }}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* 5. Add Custom Rule Modal (MIT Declarative Rule Builder) */}
      {showAddModal && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.6)",
            backdropFilter: "blur(4px)",
            display: "grid",
            placeItems: "center",
            zIndex: 1000,
            padding: "20px",
          }}
        >
          <div
            style={{
              background: "var(--paper)",
              color: "var(--ink)",
              maxWidth: "600px",
              width: "100%",
              borderRadius: "16px",
              padding: "28px",
              boxShadow: "var(--shadow-elevation-4)",
              border: "1px solid var(--line)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "18px" }}>
              <div>
                <h3 style={{ margin: 0, fontSize: "1.15rem", fontWeight: 800 }}>
                  Thêm Quy Tắc Nghiệp Vụ Mới (Dynamic Rule Builder)
                </h3>
                <p style={{ margin: "4px 0 0", fontSize: "0.8125rem", color: "var(--muted)" }}>
                  Định nghĩa điều kiện kiểm tra cho phạm vi [{selectedScope.toUpperCase()}] và lưu vào CSDL
                </p>
              </div>
              <button
                onClick={() => setShowAddModal(false)}
                style={{ background: "none", border: "none", fontSize: "1.2rem", cursor: "pointer", color: "var(--muted)" }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddRule} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <div>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: "4px" }}>
                  Tên quy tắc nghiệp vụ *
                </label>
                <input
                  type="text"
                  required
                  placeholder="Ví dụ: Giới hạn đơn hàng không giao sau 18h"
                  value={newRuleName}
                  onChange={(e) => setNewRuleName(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    borderRadius: "8px",
                    border: "1px solid var(--line)",
                    background: "var(--canvas)",
                    color: "var(--ink)",
                  }}
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: "4px" }}>
                    Mã code hệ thống (Unique Code) *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="VD: CUTOFF_TIME_LIMIT"
                    value={newRuleCode}
                    onChange={(e) => setNewRuleCode(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "8px 12px",
                      borderRadius: "8px",
                      border: "1px solid var(--line)",
                      background: "var(--canvas)",
                      color: "var(--ink)",
                      fontFamily: "var(--font-geist-mono), monospace",
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: "4px" }}>
                    Phân nhóm nghiệp vụ
                  </label>
                  <select
                    value={newRuleCategory}
                    onChange={(e) => setNewRuleCategory(e.target.value as ConfigurableRule["category"])}
                    style={{
                      width: "100%",
                      padding: "8px 12px",
                      borderRadius: "8px",
                      border: "1px solid var(--line)",
                      background: "var(--canvas)",
                      color: "var(--ink)",
                    }}
                  >
                    <option value="price">Giá &amp; Chiết khấu (Price)</option>
                    <option value="stock">Kho &amp; Tồn khả dụng (Stock)</option>
                    <option value="catalog">Danh mục &amp; SKU (Catalog)</option>
                    <option value="credit">Công nợ &amp; Tín dụng (Credit)</option>
                    <option value="document">Hợp lệ văn bản (Document)</option>
                  </select>
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: "4px" }}>
                  Mô tả chi tiết quy định
                </label>
                <textarea
                  rows={2}
                  placeholder="Mô tả khi nào quy tắc bị vi phạm và hướng dẫn xử lý..."
                  value={newRuleDesc}
                  onChange={(e) => setNewRuleDesc(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    borderRadius: "8px",
                    border: "1px solid var(--line)",
                    background: "var(--canvas)",
                    color: "var(--ink)",
                  }}
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: "4px" }}>
                    Mức độ xử lý vi phạm
                  </label>
                  <select
                    value={newRuleSeverity}
                    onChange={(e) => setNewRuleSeverity(e.target.value as ConfigurableRule["severity"])}
                    style={{
                      width: "100%",
                      padding: "8px 12px",
                      borderRadius: "8px",
                      border: "1px solid var(--line)",
                      background: "var(--canvas)",
                      color: "var(--ink)",
                    }}
                  >
                    <option value="block">🔴 Lỗi chặn (Fatal Block - Không cho duyệt)</option>
                    <option value="warning">🟡 Cảnh báo (Warning - Cần quản lý phê duyệt)</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: "4px" }}>
                    Bộ phận chịu trách nhiệm
                  </label>
                  <input
                    type="text"
                    value={newRuleOwner}
                    onChange={(e) => setNewRuleOwner(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "8px 12px",
                      borderRadius: "8px",
                      border: "1px solid var(--line)",
                      background: "var(--canvas)",
                      color: "var(--ink)",
                    }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: "4px" }}>
                  Biểu thức điều kiện kiểm tra (DSL / Condition Expression)
                </label>
                <input
                  type="text"
                  placeholder="VD: order.total > 50000000 && order.delivery_hour >= 18"
                  value={newRuleCondition}
                  onChange={(e) => setNewRuleCondition(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    borderRadius: "8px",
                    border: "1px solid var(--line)",
                    background: "var(--canvas)",
                    color: "var(--ink)",
                    fontFamily: "var(--font-geist-mono), monospace",
                    fontSize: "0.75rem",
                  }}
                />
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "12px" }}>
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  style={{
                    padding: "8px 16px",
                    borderRadius: "8px",
                    border: "1px solid var(--line)",
                    background: "var(--paper)",
                    color: "var(--ink)",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  Hủy bỏ
                </button>
                <button
                  type="submit"
                  style={{
                    padding: "8px 20px",
                    borderRadius: "8px",
                    border: "none",
                    background: "var(--color-primary)",
                    color: "#ffffff",
                    fontWeight: 700,
                    cursor: "pointer",
                  }}
                >
                  Lưu &amp; Kích hoạt quy tắc
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 6. Add Custom Scope Modal (MIT Multi-Entity / Multi-Region Scope Builder) */}
      {showAddScopeModal && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.6)",
            backdropFilter: "blur(4px)",
            display: "grid",
            placeItems: "center",
            zIndex: 1000,
            padding: "20px",
          }}
        >
          <div
            style={{
              background: "var(--paper)",
              color: "var(--ink)",
              maxWidth: "520px",
              width: "100%",
              borderRadius: "16px",
              padding: "28px",
              boxShadow: "var(--shadow-elevation-4)",
              border: "1px solid var(--line)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "18px" }}>
              <div>
                <h3 style={{ margin: 0, fontSize: "1.15rem", fontWeight: 800, display: "flex", alignItems: "center", gap: "8px" }}>
                  <Globe2 size={20} color="var(--color-primary)" />
                  Thêm Phạm Vi / Vùng Miền Mới
                </h3>
                <p style={{ margin: "4px 0 0", fontSize: "0.8125rem", color: "var(--muted)" }}>
                  Tạo phân cấp mới cho Chi nhánh, Kênh phân phối, hoặc Công ty con
                </p>
              </div>
              <button
                onClick={() => setShowAddScopeModal(false)}
                style={{ background: "none", border: "none", fontSize: "1.2rem", cursor: "pointer", color: "var(--muted)" }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddScope} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "12px" }}>
                <div>
                  <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: "4px" }}>
                    Biểu tượng / Icon
                  </label>
                  <input
                    type="text"
                    value={newScopeIcon}
                    onChange={(e) => setNewScopeIcon(e.target.value)}
                    placeholder="VD: 🌊, 🏢, ⚡"
                    style={{
                      width: "100%",
                      padding: "8px 12px",
                      borderRadius: "8px",
                      border: "1px solid var(--line)",
                      background: "var(--canvas)",
                      color: "var(--ink)",
                      textAlign: "center",
                      fontSize: "1.1rem",
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: "4px" }}>
                    Mã phạm vi (Unique Code) *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="VD: central, ecommerce"
                    value={newScopeCode}
                    onChange={(e) => setNewScopeCode(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "8px 12px",
                      borderRadius: "8px",
                      border: "1px solid var(--line)",
                      background: "var(--canvas)",
                      color: "var(--ink)",
                      fontFamily: "var(--font-geist-mono), monospace",
                    }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: "4px" }}>
                  Tên hiển thị phạm vi *
                </label>
                <input
                  type="text"
                  required
                  placeholder="VD: Chi Nhánh Miền Trung, Kênh TMĐT TikTok Shop"
                  value={newScopeName}
                  onChange={(e) => setNewScopeName(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    borderRadius: "8px",
                    border: "1px solid var(--line)",
                    background: "var(--canvas)",
                    color: "var(--ink)",
                  }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: "4px" }}>
                  Mô tả phạm vi &amp; đối tượng áp dụng
                </label>
                <textarea
                  rows={2}
                  placeholder="VD: Áp dụng riêng cho kho Đà Nẵng và các nhà phân phối duyên hải miền Trung..."
                  value={newScopeDesc}
                  onChange={(e) => setNewScopeDesc(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    borderRadius: "8px",
                    border: "1px solid var(--line)",
                    background: "var(--canvas)",
                    color: "var(--ink)",
                  }}
                />
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "12px" }}>
                <button
                  type="button"
                  onClick={() => setShowAddScopeModal(false)}
                  style={{
                    padding: "8px 16px",
                    borderRadius: "8px",
                    border: "1px solid var(--line)",
                    background: "var(--paper)",
                    color: "var(--ink)",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  Hủy bỏ
                </button>
                <button
                  type="submit"
                  style={{
                    padding: "8px 20px",
                    borderRadius: "8px",
                    border: "none",
                    background: "var(--color-primary)",
                    color: "#ffffff",
                    fontWeight: 700,
                    cursor: "pointer",
                  }}
                >
                  Lưu phạm vi mới
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
