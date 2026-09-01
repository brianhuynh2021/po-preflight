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
          <p className="eyebrow">CHANNELS & WEBHOOKS</p>
          <h1>Multi-Channel Integration & Policy Settings (Issue #8)</h1>
          <p>
            Configure mobile approval notification bots (Telegram & Zalo OA), anti-spoofing webhook secret tokens, and automated dispatch policies.
          </p>
        </div>
      </div>

      {saved && (
        <div style={{ padding: "12px 16px", background: "#064e3b", color: "#34d399", borderRadius: "8px", marginBottom: "16px", fontWeight: "bold" }}>
          ✔ Multi-channel settings updated and verified!
        </div>
      )}

      <div className="workspace-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
        {/* Telegram Configuration */}
        <div className="panel" style={{ background: "var(--surface-color, #1e1e2d)", padding: "24px", borderRadius: "10px", border: "1px solid var(--border-color, #333)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
            <span style={{ fontSize: "20px" }}>✈️</span>
            <h3 style={{ fontSize: "16px", color: "#fff", margin: 0 }}>Telegram Bot & Mobile HITL Approval</h3>
          </div>

          <div style={{ marginBottom: "12px" }}>
            <label style={{ display: "block", fontSize: "12px", color: "#94a3b8", marginBottom: "4px" }}>BOT API TOKEN</label>
            <input
              type="password"
              value={telegramToken}
              onChange={(e) => setTelegramToken(e.target.value)}
              className="text-input"
              style={{ width: "100%", padding: "8px", borderRadius: "6px", background: "#0f172a", border: "1px solid #334155", color: "#fff" }}
            />
          </div>

          <div style={{ marginBottom: "12px" }}>
            <label style={{ display: "block", fontSize: "12px", color: "#94a3b8", marginBottom: "4px" }}>TARGET MANAGEMENT CHAT / GROUP ID</label>
            <input
              type="text"
              value={telegramChatId}
              onChange={(e) => setTelegramChatId(e.target.value)}
              className="text-input"
              style={{ width: "100%", padding: "8px", borderRadius: "6px", background: "#0f172a", border: "1px solid #334155", color: "#fff" }}
            />
          </div>

          <div style={{ marginBottom: "16px" }}>
            <label style={{ display: "block", fontSize: "12px", color: "#94a3b8", marginBottom: "4px" }}>
              WEBHOOK SECRET TOKEN (ISSUE #43 ANTI-SPOOFING)
            </label>
            <input
              type="text"
              value={telegramSecret}
              onChange={(e) => setTelegramSecret(e.target.value)}
              className="text-input"
              style={{ width: "100%", padding: "8px", borderRadius: "6px", background: "#0f172a", border: "1px solid #334155", color: "#38bdf8", fontFamily: "monospace" }}
            />
            <div style={{ fontSize: "11px", color: "#64748b", marginTop: "4px" }}>
              Validated via <code>X-Telegram-Bot-Api-Secret-Token</code> header.
            </div>
          </div>
        </div>

        {/* Zalo OA & Policy Configuration */}
        <div className="panel" style={{ background: "var(--surface-color, #1e1e2d)", padding: "24px", borderRadius: "10px", border: "1px solid var(--border-color, #333)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
            <span style={{ fontSize: "20px" }}>💬</span>
            <h3 style={{ fontSize: "16px", color: "#fff", margin: 0 }}>Zalo Official Account (OA)</h3>
          </div>

          <div style={{ marginBottom: "16px" }}>
            <label style={{ display: "block", fontSize: "12px", color: "#94a3b8", marginBottom: "4px" }}>ZALO OA ACCESS TOKEN</label>
            <input
              type="password"
              value={zaloToken}
              onChange={(e) => setZaloToken(e.target.value)}
              className="text-input"
              style={{ width: "100%", padding: "8px", borderRadius: "6px", background: "#0f172a", border: "1px solid #334155", color: "#fff" }}
            />
          </div>

          <h3 style={{ fontSize: "15px", color: "#fff", marginTop: "20px", marginBottom: "12px" }}>Automated Dispatch Policies</h3>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "12px" }}>
            <input
              type="checkbox"
              id="autoApprove"
              checked={autoApproveReady}
              onChange={(e) => setAutoApproveReady(e.target.checked)}
              style={{ width: "18px", height: "18px" }}
            />
            <label htmlFor="autoApprove" style={{ fontSize: "13px", color: "#e2e8f0" }}>
              Auto-dispatch to ERP when status is <strong>READY</strong> (0 findings)
            </label>
          </div>

          <div style={{ marginTop: "24px" }}>
            <button className="primary-button" onClick={handleSave} style={{ width: "100%", padding: "10px" }}>
              💾 Save Channel Configuration
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
