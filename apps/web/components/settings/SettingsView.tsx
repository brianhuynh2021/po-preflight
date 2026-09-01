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
          <p className="eyebrow">TÍCH HỢP ĐA KÊNH &amp; WEBHOOKS (ISSUE #8 &amp; #43)</p>
          <h1>Cấu hình Tích hợp Đa kênh &amp; Chính sách</h1>
          <p>
            Cấu hình bot thông báo &amp; phê duyệt qua thiết bị di động (Telegram &amp; Zalo OA), mã bảo mật webhook chống giả mạo và chính sách tự động đẩy đơn sang ERP.
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
          ✔ Đã cập nhật và xác thực cấu hình đa kênh thành công!
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
        {/* Telegram Configuration Card */}
        <div className="clean-card">
          <div className="card-header-clean">
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ fontSize: "18px" }}>✈️</span>
              <h3>Telegram Bot &amp; Phê duyệt Di động</h3>
            </div>
            <span className="badge-clean badge-clean-info">Đang kết nối trực tiếp</span>
          </div>

          <div style={{ marginBottom: "14px" }}>
            <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "var(--ink)", marginBottom: "4px" }}>
              Mã Bot API Token
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
              ID Nhóm / Kênh Quản lý (Chat/Group ID)
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
              Mã bí mật Webhook (Chống giả mạo - Issue #43)
            </label>
            <input
              type="text"
              className="input-clean"
              value={telegramSecret}
              onChange={(e) => setTelegramSecret(e.target.value)}
              style={{ fontFamily: "ui-monospace, monospace" }}
            />
            <small style={{ color: "var(--muted)", display: "block", marginTop: "4px" }}>
              Xác thực an toàn qua tiêu đề <code>X-Telegram-Bot-Api-Secret-Token</code>.
            </small>
          </div>
        </div>

        {/* Zalo OA & Dispatch Policy Card */}
        <div className="clean-card">
          <div className="card-header-clean">
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ fontSize: "18px" }}>💬</span>
              <h3>Zalo Official Account (Zalo OA)</h3>
            </div>
            <span className="badge-clean badge-clean-info">Zalo v4</span>
          </div>

          <div style={{ marginBottom: "16px" }}>
            <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "var(--ink)", marginBottom: "4px" }}>
              Mã truy cập Zalo OA (Access Token)
            </label>
            <input
              type="password"
              className="input-clean"
              value={zaloToken}
              onChange={(e) => setZaloToken(e.target.value)}
            />
          </div>

          <div className="card-header-clean" style={{ marginTop: "24px" }}>
            <h3>Chính sách Tự động Đẩy đơn (Dispatch Policy)</h3>
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
              Tự động đẩy vào ERP khi trạng thái đơn hàng là <strong>READY</strong> (0 cảnh báo)
            </span>
          </label>

          <div style={{ marginTop: "20px" }}>
            <button className="primary-button" style={{ width: "100%", justifyContent: "center" }} onClick={handleSave}>
              💾 Lưu Cấu hình Đa kênh
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
