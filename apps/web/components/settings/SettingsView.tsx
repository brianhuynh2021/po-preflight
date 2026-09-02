"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, AlertTriangle, Send, Link2, RefreshCw } from "lucide-react";
import { api, describeError } from "@/app/lib/api/client";
import { useAppState } from "@/components/app/AppStateProvider";
import { useRipple } from "@/app/lib/useRipple";

export function SettingsView() {
  const { user } = useAppState();
  const { createRipple } = useRipple();
  const [botStatus, setBotStatus] = useState<{
    telegram: Record<string, unknown>;
    zalo: Record<string, unknown>;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [telegramChatId, setTelegramChatId] = useState("");
  const [telegramUsername, setTelegramUsername] = useState("");
  const [linkFeedback, setLinkFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const fetchBotStatus = async () => {
    setIsLoading(true);
    try {
      const res = await api.bot.getStatus();
      setBotStatus(res);
    } catch {
      // Offline
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    api.bot
      .getStatus()
      .then((st) => {
        if (mounted) setBotStatus(st);
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, []);

  const handleLinkTelegram = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!telegramChatId.trim()) return;

    setLinkFeedback(null);
    try {
      const res = await api.bot.linkTelegram(telegramChatId.trim(), telegramUsername.trim() || undefined);
      setLinkFeedback({
        type: "success",
        message: res.message || "Đã liên kết tài khoản Telegram thành công!",
      });
      await fetchBotStatus();
    } catch (err) {
      setLinkFeedback({
        type: "error",
        message: describeError(err),
      });
    }
  };

  const isAdmin = user?.role === "ADMIN" || !user;

  const isTelegramConfigured = Boolean(botStatus?.telegram?.configured);
  const isZaloConfigured = Boolean(botStatus?.zalo?.configured);

  return (
    <div className="page settings-page page-enter">
      <div className="page-heading">
        <div>
          <p className="eyebrow">TÍCH HỢP HỆ THỐNG · Multi-Channel</p>
          <h1>Cấu hình Tích hợp Đa kênh &amp; Webhook</h1>
          <p>
            Trạng thái kết nối bot phê duyệt qua di động (Telegram &amp; Zalo OA) và hướng dẫn cấu hình môi trường bảo mật.
          </p>
        </div>
        <button
          className="secondary-button interactive"
          onClick={(e) => {
            createRipple(e);
            void fetchBotStatus();
          }}
          disabled={isLoading}
          style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-1)" }}
        >
          <RefreshCw size={15} className={isLoading ? "animate-spin" : ""} />
          <span>Làm mới trạng thái</span>
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-5)" }}>
        {/* Telegram Card */}
        <div className="content-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-4)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
              <Send size={20} color="#0088cc" />
              <h2 style={{ fontSize: "1.1rem", margin: 0 }}>Telegram Bot &amp; Phê duyệt Di động</h2>
            </div>
            <span
              className={isTelegramConfigured ? "catalog-state active" : "catalog-state inactive"}
              style={{ padding: "3px 8px", borderRadius: "var(--radius-sm)", fontSize: "0.75rem" }}
            >
              {isTelegramConfigured ? "Đã cấu hình (Live)" : "Chưa cấu hình / Dry-run"}
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)", fontSize: "0.875rem" }}>
            <div style={{ padding: "var(--space-3)", backgroundColor: "var(--color-surface-container-low)", borderRadius: "var(--radius-md)" }}>
              <strong style={{ display: "block", marginBottom: "4px" }}>Hướng dẫn cấu hình biến môi trường:</strong>
              <code style={{ display: "block", fontSize: "0.8rem", color: "var(--color-outline)", lineHeight: 1.5 }}>
                TELEGRAM_BOT_TOKEN=&lt;your_token_from_botfather&gt;<br />
                TELEGRAM_WEBHOOK_SECRET=&lt;strong_random_secret&gt;<br />
                TELEGRAM_DRY_RUN=false
              </code>
            </div>

            {isAdmin && (
              <form onSubmit={handleLinkTelegram} style={{ marginTop: "var(--space-3)", display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
                <h3 style={{ fontSize: "0.9rem", fontWeight: 600, margin: "0 0 4px" }}>Liên kết tài khoản Telegram quản trị:</h3>
                <div>
                  <label style={{ display: "block", fontSize: "0.75rem", color: "var(--color-outline)", marginBottom: 2 }}>
                    Telegram Chat ID:
                  </label>
                  <input
                    type="text"
                    value={telegramChatId}
                    onChange={(e) => setTelegramChatId(e.target.value)}
                    placeholder="Ví dụ: 123456789 hoặc -10012345678"
                    required
                    style={{
                      width: "100%",
                      padding: "6px 10px",
                      borderRadius: "var(--radius-sm)",
                      border: "1px solid var(--color-outline-variant)",
                      backgroundColor: "var(--color-surface-container)",
                    }}
                  />
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "0.75rem", color: "var(--color-outline)", marginBottom: 2 }}>
                    Username Telegram (tùy chọn):
                  </label>
                  <input
                    type="text"
                    value={telegramUsername}
                    onChange={(e) => setTelegramUsername(e.target.value)}
                    placeholder="@username"
                    style={{
                      width: "100%",
                      padding: "6px 10px",
                      borderRadius: "var(--radius-sm)",
                      border: "1px solid var(--color-outline-variant)",
                      backgroundColor: "var(--color-surface-container)",
                    }}
                  />
                </div>
                <button
                  type="submit"
                  className="primary-button interactive"
                  style={{ marginTop: "var(--space-1)", display: "inline-flex", alignItems: "center", justifyContent: "center", gap: "var(--space-1)" }}
                >
                  <Link2 size={15} />
                  <span>Xác nhận liên kết</span>
                </button>
              </form>
            )}

            {linkFeedback && (
              <div
                style={{
                  padding: "var(--space-2) var(--space-3)",
                  borderRadius: "var(--radius-sm)",
                  fontSize: "0.8rem",
                  backgroundColor: linkFeedback.type === "success" ? "rgba(16, 185, 129, 0.1)" : "rgba(239, 68, 68, 0.1)",
                  color: linkFeedback.type === "success" ? "#10b981" : "#ef4444",
                  border: linkFeedback.type === "success" ? "1px solid #10b981" : "1px solid #ef4444",
                }}
              >
                {linkFeedback.message}
              </div>
            )}
          </div>
        </div>

        {/* Zalo OA Card */}
        <div className="content-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-4)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
              <span style={{ fontSize: "1.2rem" }}>💬</span>
              <h2 style={{ fontSize: "1.1rem", margin: 0 }}>Zalo Official Account (Zalo OA)</h2>
            </div>
            <span
              className={isZaloConfigured ? "catalog-state active" : "catalog-state inactive"}
              style={{ padding: "3px 8px", borderRadius: "var(--radius-sm)", fontSize: "0.75rem" }}
            >
              {isZaloConfigured ? "Đã kết nối OA" : "Chưa cấu hình / Sandbox"}
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)", fontSize: "0.875rem" }}>
            <div style={{ padding: "var(--space-3)", backgroundColor: "var(--color-surface-container-low)", borderRadius: "var(--radius-md)" }}>
              <strong style={{ display: "block", marginBottom: "4px" }}>Hướng dẫn cấu hình biến môi trường:</strong>
              <code style={{ display: "block", fontSize: "0.8rem", color: "var(--color-outline)", lineHeight: 1.5 }}>
                ZALO_OA_ID=&lt;your_oa_id&gt;<br />
                ZALO_OA_SECRET=&lt;your_oa_secret&gt;<br />
                ZALO_OA_ACCESS_TOKEN=&lt;your_access_token&gt;<br />
                ZALO_DRY_RUN=false
              </code>
            </div>

            <div style={{ padding: "var(--space-3)", border: "1px solid var(--color-outline-variant)", borderRadius: "var(--radius-md)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-1)" }}>
                {isZaloConfigured ? <CheckCircle2 size={16} color="#10b981" /> : <AlertTriangle size={16} color="#f59e0b" />}
                <strong>Chính sách bảo mật Webhook:</strong>
              </div>
              <p style={{ margin: 0, fontSize: "0.8rem", color: "var(--color-outline)" }}>
                Mọi webhook từ Telegram và Zalo đều bắt buộc phải kèm theo mã token chống giả mạo HMAC-SHA256 để bảo vệ hệ thống trước tấn công giả lập dữ liệu duyệt đơn.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
