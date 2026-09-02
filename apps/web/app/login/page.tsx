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
        backgroundColor: "var(--color-surface-dim)",
        padding: "var(--space-4)",
      }}
    >
      <div
        className="content-card"
        style={{
          width: "100%",
          maxWidth: 440,
          padding: "var(--space-6)",
          borderRadius: "var(--radius-xl)",
          boxShadow: "var(--shadow-elevation-3)",
          backgroundColor: "var(--color-surface)",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: "var(--space-6)" }}>
          <div
            style={{
              width: 52,
              height: 52,
              borderRadius: "var(--radius-full)",
              backgroundColor: "var(--color-primary-container)",
              color: "var(--color-on-primary-container)",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              marginBottom: "var(--space-3)",
            }}
          >
            <ShieldCheck size={28} />
          </div>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 700, margin: 0, color: "var(--color-on-surface)" }}>
            PO Preflight
          </h1>
          <p style={{ fontSize: "0.875rem", color: "var(--color-outline)", marginTop: "var(--space-1)" }}>
            Hệ thống kiểm định đơn hàng B2B tự động
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
                color: "var(--color-on-surface-variant)",
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
                  padding: "var(--space-3) var(--space-4) var(--space-3) 40px",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid var(--color-outline-variant)",
                  backgroundColor: "var(--color-surface-container-low)",
                  color: "var(--color-on-surface)",
                  fontSize: "0.95rem",
                }}
              />
              <KeyRound
                size={18}
                style={{
                  position: "absolute",
                  left: 12,
                  top: "50%",
                  transform: "translateY(-50%)",
                  color: "var(--color-outline)",
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
              padding: "var(--space-3)",
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              gap: "var(--space-2)",
              fontSize: "0.95rem",
              fontWeight: 600,
            }}
          >
            <span>{isLoading ? "Đang xác thực..." : "Đăng nhập hệ thống"}</span>
            <ArrowRight size={16} />
          </button>
        </form>

        <div style={{ marginTop: "var(--space-6)", paddingTop: "var(--space-4)", borderTop: "1px solid var(--color-outline-variant)" }}>
          <p style={{ fontSize: "0.75rem", color: "var(--color-outline)", marginBottom: "var(--space-2)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Khóa thử nghiệm theo vai trò (Dev Mode):
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-2)" }}>
            <button
              type="button"
              onClick={() => handleQuickKey("pf_dev_adm_9901")}
              style={{
                fontSize: "0.75rem",
                padding: "4px 8px",
                borderRadius: "var(--radius-sm)",
                border: "1px solid var(--color-outline-variant)",
                background: "var(--color-surface-container)",
                cursor: "pointer",
              }}
            >
              👑 Quản trị (Admin)
            </button>
            <button
              type="button"
              onClick={() => handleQuickKey("pf_dev_mgr_8802")}
              style={{
                fontSize: "0.75rem",
                padding: "4px 8px",
                borderRadius: "var(--radius-sm)",
                border: "1px solid var(--color-outline-variant)",
                background: "var(--color-surface-container)",
                cursor: "pointer",
              }}
            >
              👔 Quản lý duyệt (Manager)
            </button>
            <button
              type="button"
              onClick={() => handleQuickKey("pf_dev_view_6604")}
              style={{
                fontSize: "0.75rem",
                padding: "4px 8px",
                borderRadius: "var(--radius-sm)",
                border: "1px solid var(--color-outline-variant)",
                background: "var(--color-surface-container)",
                cursor: "pointer",
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
