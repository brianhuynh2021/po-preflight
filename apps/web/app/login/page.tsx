"use client";

import { useState } from "react";
import { KeyRound, ShieldCheck, ArrowRight, AlertCircle } from "lucide-react";
import { api, describeError } from "@/app/lib/api/client";

export default function LoginPage() {
  const [apiKey, setApiKey] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey.trim()) return;

    setIsLoading(true);
    setError(null);
    try {
      await api.auth.login(apiKey.trim());
      window.location.href = "/overview";
    } catch (err) {
      setError(describeError(err));
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickKey = (key: string) => {
    setApiKey(key);
    setError(null);
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "radial-gradient(circle at 50% 30%, rgba(16, 185, 129, 0.08) 0%, transparent 60%), var(--canvas)",
        padding: "var(--space-4)",
      }}
    >
      <div
        className="content-card"
        style={{
          width: "100%",
          maxWidth: 440,
          padding: "var(--space-8) var(--space-6)",
          borderRadius: "var(--radius-xl)",
          boxShadow: "0 20px 50px -10px rgba(0, 0, 0, 0.12), 0 0 0 1px var(--line)",
          backgroundColor: "var(--paper)",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: "var(--space-6)" }}>
          <div
            style={{
              width: 54,
              height: 54,
              borderRadius: "14px",
              background: "linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.25) 100%)",
              color: "var(--color-primary)",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              marginBottom: "var(--space-3)",
              border: "1px solid rgba(16, 185, 129, 0.3)",
              boxShadow: "0 4px 12px rgba(16, 185, 129, 0.15)",
            }}
          >
            <ShieldCheck size={28} />
          </div>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 800, margin: 0, color: "var(--ink)", letterSpacing: "-0.02em" }}>
            PO Preflight
          </h1>
          <p style={{ fontSize: "0.875rem", color: "var(--muted)", marginTop: "var(--space-1)" }}>
            Hệ thống tiền kiểm &amp; phê duyệt đơn hàng B2B
          </p>
        </div>

        {error && (
          <div
            style={{
              marginBottom: "var(--space-4)",
              padding: "var(--space-3)",
              borderRadius: "var(--radius-md)",
              backgroundColor: "rgba(239, 68, 68, 0.1)",
              border: "1px solid #ef4444",
              display: "flex",
              alignItems: "center",
              gap: "var(--space-2)",
              color: "#dc2626",
              fontSize: "0.875rem",
            }}
          >
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
          <div>
            <label
              htmlFor="apiKey"
              style={{
                display: "block",
                fontSize: "0.875rem",
                fontWeight: 600,
                marginBottom: "var(--space-1)",
                color: "var(--ink)",
              }}
            >
              Khóa truy cập hệ thống (API Key)
            </label>
            <div style={{ position: "relative" }}>
              <input
                id="apiKey"
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Nhập khóa API (ví dụ: pf_dev_mgr_8802)"
                required
                style={{
                  width: "100%",
                  padding: "11px 14px 11px 40px",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid var(--line-strong)",
                  backgroundColor: "var(--canvas)",
                  color: "var(--ink)",
                  fontSize: "0.9375rem",
                  transition: "all 0.15s ease",
                }}
              />
              <KeyRound
                size={18}
                style={{
                  position: "absolute",
                  left: 12,
                  top: "50%",
                  transform: "translateY(-50%)",
                  color: "var(--muted)",
                }}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading || !apiKey.trim()}
            className="primary-button interactive"
            style={{
              width: "100%",
              padding: "12px",
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              gap: "var(--space-2)",
              fontSize: "0.95rem",
              fontWeight: 700,
              background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
              boxShadow: "0 4px 12px rgba(16, 185, 129, 0.3)",
            }}
          >
            <span>{isLoading ? "Đang xác thực..." : "Đăng nhập hệ thống"}</span>
            <ArrowRight size={16} />
          </button>
        </form>

        <div style={{ marginTop: "var(--space-6)", paddingTop: "var(--space-4)", borderTop: "1px solid var(--line)" }}>
          <p style={{ fontSize: "0.75rem", color: "var(--muted)", marginBottom: "var(--space-2)", textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 700 }}>
            KHÓA TRẢI NGHIỆM THEO VAI TRÒ (DEV DEMO):
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
            <button
              type="button"
              onClick={() => handleQuickKey("pf_dev_adm_9901")}
              style={{
                fontSize: "0.75rem",
                fontWeight: 600,
                padding: "6px 10px",
                borderRadius: "var(--radius-sm)",
                border: apiKey === "pf_dev_adm_9901" ? "1px solid var(--color-primary)" : "1px solid var(--line)",
                background: apiKey === "pf_dev_adm_9901" ? "rgba(16, 185, 129, 0.12)" : "var(--canvas)",
                color: apiKey === "pf_dev_adm_9901" ? "var(--color-primary)" : "var(--ink)",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              👑 Quản trị (Admin)
            </button>
            <button
              type="button"
              onClick={() => handleQuickKey("pf_dev_mgr_8802")}
              style={{
                fontSize: "0.75rem",
                fontWeight: 600,
                padding: "6px 10px",
                borderRadius: "var(--radius-sm)",
                border: apiKey === "pf_dev_mgr_8802" ? "1px solid var(--color-primary)" : "1px solid var(--line)",
                background: apiKey === "pf_dev_mgr_8802" ? "rgba(16, 185, 129, 0.12)" : "var(--canvas)",
                color: apiKey === "pf_dev_mgr_8802" ? "var(--color-primary)" : "var(--ink)",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              👔 Quản lý duyệt (Manager)
            </button>
            <button
              type="button"
              onClick={() => handleQuickKey("pf_dev_view_6604")}
              style={{
                fontSize: "0.75rem",
                fontWeight: 600,
                padding: "6px 10px",
                borderRadius: "var(--radius-sm)",
                border: apiKey === "pf_dev_view_6604" ? "1px solid var(--color-primary)" : "1px solid var(--line)",
                background: apiKey === "pf_dev_view_6604" ? "rgba(16, 185, 129, 0.12)" : "var(--canvas)",
                color: apiKey === "pf_dev_view_6604" ? "var(--color-primary)" : "var(--ink)",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              👁️ Người xem (Viewer)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
