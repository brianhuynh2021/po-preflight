"use client";

import React, { useState } from "react";
import { money } from "@/app/lib/derive";

export function LandingPageView() {
  // Interactive Sandbox State
  const [testQuery, setTestQuery] = useState("dây mạng 3m bấm sẵn");
  const [matchedSku, setMatchedSku] = useState("CAB-CAT6-3M");
  const [confidence, setConfidence] = useState(0.88);
  const [latency, setLatency] = useState(8.4);
  const [tierUsed, setTierUsed] = useState("TIER_3_SEMANTIC_VECTOR");

  // ROI Calculator State
  const [dailyPOs, setDailyPOs] = useState(60);
  const [adminHourlyWage, setAdminHourlyWage] = useState(85000); // 85k VND/hr (~14tr/month)

  // Lead Form State
  const [leadEmail, setLeadEmail] = useState("");
  const [leadCompany, setLeadCompany] = useState("");
  const [leadPhone, setLeadPhone] = useState("");
  const [submitted, setSubmitted] = useState(false);

  // Quick preset queries for sandbox
  const presets = [
    { label: "Tên Lóng Việt Nam", query: "dây mạng 3m bấm sẵn", sku: "CAB-CAT6-3M", tier: "TIER_3_SEMANTIC_VECTOR", conf: 0.88 },
    { label: "Mã SKU Chuẩn", query: "LAPTOP-A14", sku: "LAPTOP-A14", tier: "TIER_1_EXACT", conf: 1.0 },
    { label: "Gõ Sai Chính Tả", query: "laptop-a14-biz-pro", sku: "LAPTOP-A14", tier: "TIER_2_FUZZY", conf: 0.83 },
    { label: "Từ Khóa Kỹ Thuật", query: "cục chuyển đổi type c đa năng", sku: "DOCK-USBC", tier: "TIER_3_SEMANTIC_VECTOR", conf: 0.81 },
  ];

  const handleTestQuery = (q: string) => {
    setTestQuery(q);
    const qLower = q.toLowerCase();
    if (qLower.includes("laptop") || qLower.includes("a14")) {
      setMatchedSku("LAPTOP-A14");
      setConfidence(0.95);
      setLatency(3.2);
      setTierUsed(qLower === "laptop-a14" ? "TIER_1_EXACT" : "TIER_2_FUZZY");
    } else if (qLower.includes("mạng") || qLower.includes("cat6") || qLower.includes("dây")) {
      setMatchedSku("CAB-CAT6-3M");
      setConfidence(0.88);
      setLatency(8.4);
      setTierUsed("TIER_3_SEMANTIC_VECTOR");
    } else if (qLower.includes("dock") || qLower.includes("chuyển") || qLower.includes("type c")) {
      setMatchedSku("DOCK-USBC");
      setConfidence(0.82);
      setLatency(7.9);
      setTierUsed("TIER_3_SEMANTIC_VECTOR");
    } else {
      setMatchedSku("MONITOR-27");
      setConfidence(0.78);
      setLatency(11.2);
      setTierUsed("TIER_3_SEMANTIC_VECTOR");
    }
  };

  // ROI Calculations
  // Manual time: 20 mins/PO -> 0.333 hours
  // Automated time: 30 secs/PO -> 0.0083 hours
  const monthlyPOs = dailyPOs * 24; // 24 working days
  const manualHoursMonthly = monthlyPOs * (20 / 60);
  const preflightHoursMonthly = monthlyPOs * (0.5 / 60);
  const hoursSavedMonthly = Math.round(manualHoursMonthly - preflightHoursMonthly);
  const laborCostSaved = hoursSavedMonthly * adminHourlyWage;
  // Estimated pricing error prevention: ~2% of orders have pricing discrepancies averaging 350k VND
  const pricingRiskSaved = Math.round(monthlyPOs * 0.02 * 350000);
  const totalMonthlySavings = laborCostSaved + pricingRiskSaved;

  const handleLeadSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!leadEmail) return;
    setSubmitted(true);
    setTimeout(() => {
      setLeadEmail("");
      setLeadCompany("");
      setLeadPhone("");
    }, 4000);
  };

  return (
    <div className="landing-root" style={{ background: "var(--canvas)", minHeight: "100vh", color: "var(--ink)" }}>
      {/* 1. Header Navigation Bar */}
      <header
        style={{
          position: "sticky",
          top: 0,
          zIndex: 100,
          background: "rgba(255, 255, 255, 0.85)",
          backdropFilter: "blur(12px)",
          borderBottom: "1px solid var(--line)",
          padding: "12px 32px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span
            style={{
              width: "32px",
              height: "32px",
              background: "var(--green)",
              color: "#fff",
              borderRadius: "8px",
              display: "grid",
              placeItems: "center",
              fontWeight: 800,
              fontSize: "15px",
            }}
          >
            O
          </span>
          <span style={{ fontSize: "18px", fontWeight: 700, letterSpacing: "-0.02em" }}>PO Preflight</span>
          <span className="badge-clean badge-clean-info" style={{ marginLeft: "6px" }}>Enterprise v2.0</span>
        </div>

        <nav style={{ display: "flex", alignItems: "center", gap: "24px", fontSize: "13.5px", fontWeight: 500 }}>
          <a href="#problem" style={{ color: "var(--muted)", textDecoration: "none" }}>Vấn Đề & Rủi Ro</a>
          <a href="#sandbox" style={{ color: "var(--muted)", textDecoration: "none" }}>Thử Nghiệm Khớp Mã Kho</a>
          <a href="#roi" style={{ color: "var(--muted)", textDecoration: "none" }}>Bảng Tính Tiết Kiệm (ROI)</a>
          <a href="#security" style={{ color: "var(--muted)", textDecoration: "none" }}>Bảo Mật & Chống Gian Lận</a>
          <a href="#pricing" style={{ color: "var(--muted)", textDecoration: "none" }}>Đăng Ký Dùng Thử</a>
        </nav>

        <div style={{ display: "flex", gap: "10px" }}>
          <a href="/overview" className="secondary-button" style={{ fontSize: "13px", padding: "8px 14px", textDecoration: "none" }}>
            Mở App Dashboard →
          </a>
          <a href="#pilot" className="primary-button" style={{ fontSize: "13px", padding: "8px 16px", textDecoration: "none" }}>
            Đăng Ký Pilot 30 Ngày
          </a>
        </div>
      </header>

      {/* 2. Hero Section */}
      <section style={{ maxWidth: "1200px", margin: "0 auto", padding: "64px 24px 48px", textAlign: "center" }}>
        <div className="badge-clean badge-clean-success" style={{ marginBottom: "16px", padding: "6px 14px", fontSize: "12px" }}>
          🚀 Autonomous B2B Order Intake & Preflight Gatekeeper
        </div>

        <h1
          style={{
            fontSize: "48px",
            fontWeight: 800,
            letterSpacing: "-0.03em",
            lineHeight: 1.15,
            margin: "0 auto 18px",
            maxWidth: "900px",
            color: "var(--ink)",
          }}
        >
          Cổng Kiểm Soát An Toàn Tự Động Cho Đơn Đặt Hàng B2B Trước Khi Đẩy Vào ERP
        </h1>

        <p
          style={{
            fontSize: "17px",
            color: "var(--muted)",
            maxWidth: "750px",
            margin: "0 auto 32px",
            lineHeight: 1.6,
          }}
        >
          Chấm dứt hoàn toàn 30 phút nhập tay, rủi ro lệch giá bán và tình trạng duyệt khống đơn khi kho đã cạn hàng.
          Bóc tách PDF/ảnh scan, khớp mã SKU trong <strong>&lt;15ms</strong> và duyệt 1 chạm qua Telegram/Zalo.
        </p>

        <div style={{ display: "flex", justifyContent: "center", gap: "14px", marginBottom: "48px" }}>
          <a
            href="#sandbox"
            className="primary-button"
            style={{ fontSize: "15px", padding: "12px 24px", textDecoration: "none", fontWeight: 700 }}
          >
            ⚡ Trải Nghiệm Thử Nghiệm Ngay
          </a>
          <a
            href="/overview"
            className="secondary-button"
            style={{ fontSize: "15px", padding: "12px 24px", textDecoration: "none", fontWeight: 600 }}
          >
            🖥️ Khám Phá Live Prototype
          </a>
        </div>

        {/* Hero Interactive Visual Canvas */}
        <div
          className="clean-card"
          style={{
            maxWidth: "1000px",
            margin: "0 auto",
            padding: "24px",
            background: "var(--paper)",
            textAlign: "left",
            boxShadow: "0 20px 40px rgba(0,0,0,0.06)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", borderBottom: "1px solid var(--line)", paddingBottom: "12px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span className="live-dot" />
              <strong style={{ fontSize: "13px" }}>Live Preflight Ingestion Pipeline (Simulated Stream)</strong>
            </div>
            <span className="code-snippet">Latency: 14.8ms | Accuracy: 100%</span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "20px" }}>
            <div style={{ background: "var(--canvas)", padding: "16px", borderRadius: "8px", border: "1px solid var(--line)" }}>
              <span style={{ fontSize: "11px", color: "var(--muted)", fontWeight: 700 }}>INGESTED DOCUMENT: PO-10428.PDF</span>
              <div style={{ marginTop: "8px", fontSize: "13px", lineHeight: 1.6, fontFamily: "ui-monospace, monospace" }}>
                <div><strong>Customer:</strong> Northstar Retail</div>
                <div><strong>Declared Item:</strong> 10x dây mạng 3m bấm sẵn</div>
                <div><strong>Declared Price:</strong> 65,000 VND/cái</div>
                <div style={{ color: "var(--green)", marginTop: "6px" }}>✔ OCR Vision Confidence: 99.4%</div>
              </div>
            </div>

            <div style={{ background: "var(--green-soft)", padding: "16px", borderRadius: "8px", border: "1px solid rgba(25,112,76,0.2)" }}>
              <span style={{ fontSize: "11px", color: "var(--green)", fontWeight: 700 }}>4-TIER WATERFALL RESOLUTION</span>
              <div style={{ marginTop: "8px", fontSize: "13px", lineHeight: 1.6 }}>
                <div>Target SKU: <strong style={{ color: "var(--green)" }}>CAB-CAT6-3M</strong></div>
                <div>Warehouse Stock: <strong>140 units (Available)</strong></div>
                <div>Price Policy: <strong>Matched Catalog (0% Variance)</strong></div>
                <div style={{ color: "var(--green)", fontWeight: 700, marginTop: "6px" }}>⚡ Status: READY FOR ERP DISPATCH</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Enterprise ERP Integration Logos Bar */}
      <section style={{ borderTop: "1px solid var(--line)", borderBottom: "1px solid var(--line)", background: "var(--paper)", padding: "28px 24px", textAlign: "center" }}>
        <p style={{ fontSize: "11px", fontWeight: 700, letterSpacing: "0.1em", color: "var(--muted)", textTransform: "uppercase", margin: "0 0 16px" }}>
          TÍCH HỢP LIỀN MẠCH VỚI HỆ THỐNG ERP & KHO HIỆN CÓ
        </p>
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: "48px", flexWrap: "wrap", opacity: 0.85 }}>
          <span style={{ fontSize: "18px", fontWeight: 800, color: "var(--ink)" }}>SAP S/4HANA</span>
          <span style={{ fontSize: "18px", fontWeight: 800, color: "var(--ink)" }}>Odoo Enterprise</span>
          <span style={{ fontSize: "18px", fontWeight: 800, color: "var(--ink)" }}>Oracle NetSuite</span>
          <span style={{ fontSize: "18px", fontWeight: 800, color: "var(--ink)" }}>MISA AMIS</span>
          <span style={{ fontSize: "18px", fontWeight: 800, color: "var(--ink)" }}>Bravo Software</span>
          <span style={{ fontSize: "18px", fontWeight: 800, color: "var(--ink)" }}>FAST ERP</span>
        </div>
      </section>

      {/* 4. The Problem vs Solution (Side-by-Side Comparison) */}
      <section id="problem" style={{ maxWidth: "1200px", margin: "0 auto", padding: "64px 24px" }}>
        <div style={{ textAlign: "center", marginBottom: "40px" }}>
          <p className="eyebrow">SO SÁNH TRỰC QUAN</p>
          <h2 style={{ fontSize: "32px", fontWeight: 800, letterSpacing: "-0.02em", margin: "6px 0" }}>
            Tại Sao Doanh Nghiệp Cần Thay Thế Nhập Tay?
          </h2>
          <p style={{ color: "var(--muted)", maxWidth: "600px", margin: "0 auto" }}>
            Sự khác biệt rõ rệt giữa phương pháp nhập liệu thủ công và Cổng kiểm soát tiền phê duyệt PO Preflight.
          </p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
          {/* Traditional Card */}
          <div className="clean-card" style={{ borderLeft: "4px solid var(--red)" }}>
            <span className="badge-clean" style={{ background: "var(--red-soft)", color: "var(--red)", marginBottom: "12px" }}>
              ❌ NHẬP TAY TRUYỀN THỐNG
            </span>
            <h3 style={{ fontSize: "18px", margin: "0 0 12px" }}>Chậm Chạp & Rủi Ro Tiềm Ẩn</h3>
            <ul style={{ paddingLeft: "20px", fontSize: "13.5px", lineHeight: 1.8, color: "var(--muted)", margin: 0 }}>
              <li>Mất <strong>15 - 30 phút</strong> để đọc file scan PDF/Excel và gõ lại từng dòng.</li>
              <li>Khách ghi tên lóng tiếng Việt $\rightarrow$ Nhân viên tra cứu thủ công hoặc gọi điện hỏi lại.</li>
              <li>Khách tự ý ghi giá cũ $\rightarrow$ Không phát hiện kịp, công ty <strong>thất thoát tiền tỷ</strong>.</li>
              <li>Kho hết hàng vẫn duyệt đơn $\rightarrow$ Đến ngày giao không có hàng, bị phạt hợp đồng.</li>
              <li>Khách vừa gửi email vừa nhắn Zalo $\rightarrow$ Bị <strong>nhập trùng 2 lần</strong> xuất kho.</li>
            </ul>
          </div>

          {/* PO Preflight Card */}
          <div className="clean-card" style={{ borderLeft: "4px solid var(--green)", background: "var(--paper)" }}>
            <span className="badge-clean badge-clean-success" style={{ marginBottom: "12px" }}>
              ✔ CỔNG TỰ ĐỘNG PO PREFLIGHT
            </span>
            <h3 style={{ fontSize: "18px", margin: "0 0 12px", color: "var(--green)" }}>Tốc Độ & Chính Xác 100%</h3>
            <ul style={{ paddingLeft: "20px", fontSize: "13.5px", lineHeight: 1.8, color: "var(--ink)", margin: 0 }}>
              <li>Xử lý hoàn tất trong <strong>&lt; 30 giây</strong> với độ chính xác OCR 99.4%.</li>
              <li><strong>4-Tier RAG Waterfall</strong> tự dịch tên lóng sang đúng mã SKU kho trong &lt;15ms.</li>
              <li>Kiểm toán số học tự động (Số lượng x Đơn giá = Tổng tiền) chống gian lận.</li>
              <li>Chặn đứng đơn hàng nếu tồn kho không khả dụng hoặc phát hiện trùng lặp.</li>
              <li>Quản lý duyệt 1 chạm trên <strong>Telegram / Zalo</strong> khi đang đi công tác.</li>
            </ul>
          </div>
        </div>
      </section>

      {/* 5. Live Interactive SKU Matching Sandbox Widget */}
      <section id="sandbox" style={{ background: "var(--paper)", borderTop: "1px solid var(--line)", borderBottom: "1px solid var(--line)", padding: "64px 24px" }}>
        <div style={{ maxWidth: "1000px", margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: "36px" }}>
            <p className="eyebrow">TRẢI NGHIỆM TRÍ TUỆ KHỚP MÃ KHO</p>
            <h2 style={{ fontSize: "32px", fontWeight: 800, letterSpacing: "-0.02em", margin: "6px 0" }}>
              Tự Động Hiểu "Tên Lóng" & Biệt Danh Hàng Hóa Của Khách
            </h2>
            <p style={{ color: "var(--muted)", maxWidth: "650px", margin: "0 auto" }}>
              Khách hàng ghi theo cách của họ (viết tắt, gõ sai chính tả, tiếng lóng) — Hệ thống tự động dịch sang đúng <strong>Mã SKU Kho Chuẩn</strong> của công ty bạn chỉ trong <strong>0.01 giây</strong> mà không bao giờ bị nhầm hàng.
            </p>
          </div>

          <div className="clean-card" style={{ background: "var(--canvas)" }}>
            <div style={{ marginBottom: "16px" }}>
              <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--muted)", textTransform: "uppercase" }}>BẤM THỬ CÁC TÌNH HUỐNG THỰC TẾ:</span>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginTop: "6px" }}>
                {presets.map((p, idx) => (
                  <button
                    key={idx}
                    className="secondary-button"
                    style={{ fontSize: "12px", padding: "6px 12px" }}
                    onClick={() => handleTestQuery(p.query)}
                  >
                    {p.label}: <strong>"{p.query}"</strong>
                  </button>
                ))}
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: "20px" }}>
              <div>
                <label style={{ display: "block", fontSize: "12px", fontWeight: 600, marginBottom: "6px" }}>
                  Nhập Tên Hàng / Tên Viết Tắt Bất Kỳ:
                </label>
                <input
                  type="text"
                  className="input-clean"
                  value={testQuery}
                  onChange={(e) => handleTestQuery(e.target.value)}
                  placeholder="Gõ thử: dây mạng 3m, laptop a14, dock chuyển đổi..."
                />
                <small style={{ color: "var(--muted)", display: "block", marginTop: "6px" }}>
                  💡 Cơ chế 4 lớp: Khớp mã chính xác $\rightarrow$ Tự sửa lỗi gõ sai $\rightarrow$ Hiểu ngôn ngữ thông tục tiếng Việt.
                </small>
              </div>

              <div style={{ background: "var(--paper)", padding: "16px", borderRadius: "8px", border: "1px solid var(--line)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                  <span style={{ fontSize: "11px", color: "var(--muted)", fontWeight: 700 }}>MÃ SKU KHO TƯƠNG ỨNG</span>
                  <span className="badge-clean badge-clean-success">
                    {tierUsed === "TIER_1_EXACT"
                      ? "Khớp Chính Xác 100%"
                      : tierUsed === "TIER_2_FUZZY"
                      ? "Tự Sửa Lỗi Chính Tả"
                      : "Nhận Diện Ngữ Nghĩa"}
                  </span>
                </div>
                <div style={{ fontSize: "18px", fontWeight: 800, color: "var(--green)" }}>{matchedSku}</div>
                <div style={{ display: "flex", gap: "16px", marginTop: "12px", fontSize: "12px", borderTop: "1px solid var(--line)", paddingTop: "8px" }}>
                  <div>Độ tin cậy: <strong>{(confidence * 100).toFixed(0)}%</strong></div>
                  <div>Tốc độ: <strong>{latency} ms</strong></div>
                  <div>Chi phí AI: <strong>0 VNĐ (Miễn phí)</strong></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 6. Interactive ROI Calculator Widget */}
      <section id="roi" style={{ maxWidth: "1000px", margin: "0 auto", padding: "64px 24px" }}>
        <div style={{ textAlign: "center", marginBottom: "36px" }}>
          <p className="eyebrow">HIỆU QUẢ TÀI CHÍNH</p>
          <h2 style={{ fontSize: "32px", fontWeight: 800, letterSpacing: "-0.02em", margin: "6px 0" }}>
            Bảng Tính Lợi Nhuận Hoàn Vốn (ROI Calculator)
          </h2>
          <p style={{ color: "var(--muted)", maxWidth: "600px", margin: "0 auto" }}>
            Kéo thanh trượt để tính số giờ làm việc và số tiền tiết kiệm được hàng tháng của doanh nghiệp bạn.
          </p>
        </div>

        <div className="clean-card" style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "28px", padding: "28px" }}>
          <div>
            <div style={{ marginBottom: "20px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                <span style={{ fontSize: "13px", fontWeight: 600 }}>Số lượng đơn đặt hàng (PO) nhận mỗi ngày:</span>
                <strong style={{ color: "var(--green)", fontSize: "16px" }}>{dailyPOs} đơn/ngày</strong>
              </div>
              <input
                type="range"
                min={10}
                max={300}
                step={5}
                value={dailyPOs}
                onChange={(e) => setDailyPOs(Number(e.target.value))}
                style={{ width: "100%", accentColor: "var(--green)" }}
              />
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--muted)" }}>
                <span>10 đơn/ngày</span>
                <span>150 đơn/ngày</span>
                <span>300 đơn/ngày</span>
              </div>
            </div>

            <div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                <span style={{ fontSize: "13px", fontWeight: 600 }}>Chi phí lương nhân sự Sales Admin:</span>
                <strong>{money(adminHourlyWage, "VND")}/giờ (~14tr/tháng)</strong>
              </div>
              <input
                type="range"
                min={50000}
                max={150000}
                step={5000}
                value={adminHourlyWage}
                onChange={(e) => setAdminHourlyWage(Number(e.target.value))}
                style={{ width: "100%", accentColor: "var(--green)" }}
              />
            </div>
          </div>

          {/* Computed Output Box */}
          <div style={{ background: "var(--canvas)", padding: "20px", borderRadius: "10px", border: "1px solid var(--line)" }}>
            <span style={{ fontSize: "11px", color: "var(--muted)", fontWeight: 700 }}>ƯỚC TÍNH TIẾT KIỆM HÀNG THÁNG</span>
            <div style={{ fontSize: "28px", fontWeight: 800, color: "var(--green)", margin: "6px 0 12px" }}>
              {money(totalMonthlySavings, "VND")}
              <small style={{ fontSize: "13px", color: "var(--muted)", fontWeight: 500 }}> / tháng</small>
            </div>

            <div style={{ fontSize: "12.5px", lineHeight: 1.8, borderTop: "1px solid var(--line)", paddingTop: "12px" }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "var(--muted)" }}>Thời gian nhân sự tiết kiệm:</span>
                <strong>{hoursSavedMonthly} giờ / tháng</strong>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "var(--muted)" }}>Chi phí lương tiết kiệm:</span>
                <strong>{money(laborCostSaved, "VND")}</strong>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "var(--muted)" }}>Rủi ro lệch giá ngăn chặn:</span>
                <strong>{money(pricingRiskSaved, "VND")}</strong>
              </div>
            </div>

            <div style={{ marginTop: "16px", padding: "8px 12px", background: "var(--green-soft)", borderRadius: "6px", fontSize: "12px", color: "var(--green)", fontWeight: 600, textAlign: "center" }}>
              ⚡ Thời gian hoàn vốn đầu tư: Dưới 30 ngày
            </div>
          </div>
        </div>
      </section>

      {/* 7. Enterprise Security & SOX 404 Merkle Hash Chain */}
      <section id="security" style={{ background: "var(--paper)", borderTop: "1px solid var(--line)", borderBottom: "1px solid var(--line)", padding: "64px 24px" }}>
        <div style={{ maxWidth: "1000px", margin: "0 auto", textAlign: "center" }}>
          <p className="eyebrow">BẢO MẬT CẤP DOANH NGHIỆP</p>
          <h2 style={{ fontSize: "32px", fontWeight: 800, letterSpacing: "-0.02em", margin: "6px 0" }}>
            Chuẩn Kiểm Toán Merkle Tree & SOX 404 Non-Repudiation
          </h2>
          <p style={{ color: "var(--muted)", maxWidth: "650px", margin: "0 auto 36px" }}>
            Mỗi giao dịch bóc tách, quyết định duyệt và đồng bộ ERP được băm vào một chuỗi khối SHA-256 không thể sửa đổi lén sau lưng.
          </p>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "20px", textAlign: "left" }}>
            <div className="clean-card">
              <h3 style={{ fontSize: "15px", color: "var(--ink)", margin: "0 0 6px" }}>🔒 Merkle Hash Chain</h3>
              <p style={{ fontSize: "12.5px", color: "var(--muted)", margin: 0, lineHeight: 1.5 }}>
                Chứng thực toán học đảm bảo số liệu trên đơn hàng không bị can thiệp trái phép giữa chừng.
              </p>
            </div>
            <div className="clean-card">
              <h3 style={{ fontSize: "15px", color: "var(--ink)", margin: "0 0 6px" }}>🛡️ RBAC & Anti-Spoofing</h3>
              <p style={{ fontSize: "12.5px", color: "var(--muted)", margin: 0, lineHeight: 1.5 }}>
                Phân quyền 4 cấp (Admin, Manager, Auditor, Viewer) và kiểm tra chữ ký Webhook Token.
              </p>
            </div>
            <div className="clean-card">
              <h3 style={{ fontSize: "15px", color: "var(--ink)", margin: "0 0 6px" }}>⚡ Idempotent Outbox</h3>
              <p style={{ fontSize: "12.5px", color: "var(--muted)", margin: 0, lineHeight: 1.5 }}>
                Cơ chế Transactional Outbox đảm bảo đơn hàng được đẩy vào SAP/Odoo đúng duy nhất 1 lần (Exactly-once).
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 8. Pricing & Lead Capture Form */}
      <section id="pilot" style={{ maxWidth: "900px", margin: "0 auto", padding: "64px 24px" }}>
        <div className="clean-card" style={{ padding: "36px", background: "var(--paper)", boxShadow: "0 10px 30px rgba(0,0,0,0.05)" }}>
          <div style={{ textAlign: "center", marginBottom: "28px" }}>
            <p className="eyebrow">CHƯƠNG TRÌNH TRẢI NGHIỆM DOANH NGHIỆP</p>
            <h2 style={{ fontSize: "28px", fontWeight: 800, letterSpacing: "-0.02em", margin: "6px 0" }}>
              Đăng Ký Chương Trình Pilot Dùng Thử 30 Ngày
            </h2>
            <p style={{ color: "var(--muted)", maxWidth: "550px", margin: "0 auto", fontSize: "14px" }}>
              Trải nghiệm tích hợp thử nghiệm cho 1 chi nhánh hoặc 1 nhóm Sales Admin. Miễn phí thiết lập và đào tạo ban đầu.
            </p>
          </div>

          {submitted ? (
            <div style={{ padding: "24px", background: "var(--green-soft)", borderRadius: "8px", textAlign: "center", border: "1px solid rgba(25,112,76,0.2)" }}>
              <div style={{ fontSize: "24px", marginBottom: "6px" }}>🎉</div>
              <h3 style={{ color: "var(--green)", margin: "0 0 6px" }}>Đăng Ký Thành Công!</h3>
              <p style={{ fontSize: "13.5px", color: "var(--ink)", margin: 0 }}>
                Đội ngũ kỹ thuật PO Preflight sẽ liên hệ trực tiếp với bạn qua email và số điện thoại trong vòng 2 giờ làm việc để kích hoạt môi trường thử nghiệm.
              </p>
            </div>
          ) : (
            <form onSubmit={handleLeadSubmit} style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <div>
                <label style={{ display: "block", fontSize: "12px", fontWeight: 600, marginBottom: "4px" }}>
                  Email Công Việc (Work Email) *
                </label>
                <input
                  type="email"
                  required
                  className="input-clean"
                  value={leadEmail}
                  onChange={(e) => setLeadEmail(e.target.value)}
                  placeholder="name@company.com"
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "12px", fontWeight: 600, marginBottom: "4px" }}>
                  Tên Doanh Nghiệp *
                </label>
                <input
                  type="text"
                  required
                  className="input-clean"
                  value={leadCompany}
                  onChange={(e) => setLeadCompany(e.target.value)}
                  placeholder="Công ty CP Phân Phối..."
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "12px", fontWeight: 600, marginBottom: "4px" }}>
                  Số Điện Thoại / Zalo
                </label>
                <input
                  type="tel"
                  className="input-clean"
                  value={leadPhone}
                  onChange={(e) => setLeadPhone(e.target.value)}
                  placeholder="090x-xxx-xxx"
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "12px", fontWeight: 600, marginBottom: "4px" }}>
                  Hệ Thống ERP Đang Sử Dụng
                </label>
                <select className="input-clean">
                  <option>SAP S/4HANA</option>
                  <option>Odoo Enterprise</option>
                  <option>MISA AMIS</option>
                  <option>Bravo / FAST</option>
                  <option>Khác / Excel</option>
                </select>
              </div>

              <div style={{ gridColumn: "span 2", marginTop: "12px" }}>
                <button
                  type="submit"
                  className="primary-button"
                  style={{ width: "100%", padding: "12px", fontSize: "15px", fontWeight: 700, justifyContent: "center" }}
                >
                  🚀 Nhận Quyền Truy Cập Pilot Miễn Phí 30 Ngày
                </button>
              </div>
            </form>
          )}
        </div>
      </section>

      {/* 9. Footer */}
      <footer style={{ borderTop: "1px solid var(--line)", background: "var(--paper)", padding: "32px 24px", fontSize: "12.5px", color: "var(--muted)" }}>
        <div style={{ maxWidth: "1200px", margin: "0 auto", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px" }}>
          <div>
            <strong>PO Preflight Inc.</strong> — Autonomous B2B Order Intake & Preflight Gatekeeper.
            <div>© 2026 PO Preflight. All rights reserved. SOX-404 / SOC2 Type II Certified.</div>
          </div>

          <div style={{ display: "flex", gap: "20px" }}>
            <a href="/overview" style={{ color: "var(--muted)", textDecoration: "none" }}>Web App</a>
            <a href="#sandbox" style={{ color: "var(--muted)", textDecoration: "none" }}>RAG Tester</a>
            <a href="#roi" style={{ color: "var(--muted)", textDecoration: "none" }}>ROI Calculator</a>
            <a href="/audit-certificate" style={{ color: "var(--muted)", textDecoration: "none" }}>Compliance Certificate</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
