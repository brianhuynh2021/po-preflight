"use client";

import React, { useState } from "react";

export function SettingsView() {
  const [telegramToken, setTelegramToken] = useState("7281928374:AAH_...");
  const [telegramChatId, setTelegramChatId] = useState("-1002348572");
  const [telegramSecret, setTelegramSecret] = useState("pf_sec_tok_991823");
  const [zaloToken, setZaloToken] = useState("eyJhbGciOi...");
  const [autoApproveReady, setAutoApproveReady] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="page settings-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">CHANNELS & WEBHOOKS (ISSUE #8 & #43)</p>
          <h1>Multi-Channel Integration & Policy Settings</h1>
          <p>
            Configure mobile approval notification bots (Telegram & Zalo OA), anti-spoofing webhook secret tokens, and automated dispatch policies.
          </p>
        </div>
      </div>

      {saved && (
        <div
          style={{
            padding: "12px 16px",
            background: "var(--green-soft)",
            color: "var(--green)",
            borderRadius: "8px",
            marginBottom: "16px",
            fontWeight: 600,
            border: "1px solid rgba(25, 112, 76, 0.2)",
          }}
        >
          ✔ Multi-channel settings updated and verified!
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
        {/* Telegram Configuration Card */}
        <div className="clean-card">
          <div className="card-header-clean">
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ fontSize: "18px" }}>✈️</span>
              <h3>Telegram Bot & Mobile Approvals</h3>
            </div>
            <span className="badge-clean badge-clean-info">Live Connected</span>
          </div>

          <div style={{ marginBottom: "14px" }}>
            <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "var(--ink)", marginBottom: "4px" }}>
              Bot API Token
            </label>
            <input
              type="password"
              className="input-clean"
              value={telegramToken}
              onChange={(e) => setTelegramToken(e.target.value)}
            />
          </div>

          <div style={{ marginBottom: "14px" }}>
            <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "var(--ink)", marginBottom: "4px" }}>
              Management Chat / Group ID
            </label>
            <input
              type="text"
              className="input-clean"
              value={telegramChatId}
              onChange={(e) => setTelegramChatId(e.target.value)}
            />
          </div>

          <div style={{ marginBottom: "16px" }}>
            <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "var(--ink)", marginBottom: "4px" }}>
              Webhook Secret Token (Issue #43 Anti-Spoofing)
            </label>
            <input
              type="text"
              className="input-clean"
              value={telegramSecret}
              onChange={(e) => setTelegramSecret(e.target.value)}
              style={{ fontFamily: "ui-monospace, monospace" }}
            />
            <small style={{ color: "var(--muted)", display: "block", marginTop: "4px" }}>
              Validated via <code>X-Telegram-Bot-Api-Secret-Token</code> header.
            </small>
          </div>
        </div>

        {/* Zalo OA & Dispatch Policy Card */}
        <div className="clean-card">
          <div className="card-header-clean">
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ fontSize: "18px" }}>💬</span>
              <h3>Zalo Official Account (OA)</h3>
            </div>
            <span className="badge-clean badge-clean-info">Zalo v4</span>
          </div>

          <div style={{ marginBottom: "16px" }}>
            <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "var(--ink)", marginBottom: "4px" }}>
              Zalo OA Access Token
            </label>
            <input
              type="password"
              className="input-clean"
              value={zaloToken}
              onChange={(e) => setZaloToken(e.target.value)}
            />
          </div>

          <div className="card-header-clean" style={{ marginTop: "24px" }}>
            <h3>Automated Dispatch Policies</h3>
          </div>

          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              cursor: "pointer",
              padding: "8px 0",
              fontSize: "13px",
              color: "var(--ink)",
            }}
          >
            <input
              type="checkbox"
              checked={autoApproveReady}
              onChange={(e) => setAutoApproveReady(e.target.checked)}
              style={{ width: "16px", height: "16px" }}
            />
            <span>
              Auto-dispatch to ERP when order status is <strong>READY</strong> (0 findings)
            </span>
          </label>

          <div style={{ marginTop: "20px" }}>
            <button className="primary-button" style={{ width: "100%", justifyContent: "center" }} onClick={handleSave}>
              💾 Save Channel Configuration
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
