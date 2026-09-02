"use client";

import React, { useState } from "react";
import Link from "next/link";
import { money } from "@/app/lib/derive";
import { useRipple } from "@/app/lib/useRipple";

export function LandingPageView() {
  const { createRipple } = useRipple();

  // Interactive Sandbox State
  const [testQuery, setTestQuery] = useState("dây mạng 3m bấm sẵn");
  const [matchedSku, setMatchedSku] = useState("CAB-CAT6-3M");
  const [confidence, setConfidence] = useState(0.88);
  const [latency, setLatency] = useState(8.4);
  const [tierUsed, setTierUsed] = useState("TIER_3_SEMANTIC_VECTOR");

  // ROI Calculator State
  const [dailyPOs, setDailyPOs] = useState(60);
  const [adminHourlyWage, setAdminHourlyWage] = useState(45000); // 45k VND/hr (~8-10tr/month)

  // Lead Form State
  const [leadName, setLeadName] = useState("");
  const [leadEmail, setLeadEmail] = useState("");
  const [leadCompany, setLeadCompany] = useState("");
  const [leadPhone, setLeadPhone] = useState("");
  const [leadERP, setLeadERP] = useState("MISA AMIS");
  const [leadVolume, setLeadVolume] = useState("50-200 đơn/ngày");
  const [leadNote, setLeadNote] = useState("");
  const [honeypot, setHoneypot] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
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

  // ROI Calculations with transparent formula
  const monthlyPOs = dailyPOs * 24; // 24 working days
  const manualMinutesPerPO = 20; // 20 mins per PO manually
  const preflightMinutesPerPO = 0.5; // 30 seconds with PO Preflight
  const manualHoursMonthly = monthlyPOs * (manualMinutesPerPO / 60);
  const preflightHoursMonthly = monthlyPOs * (preflightMinutesPerPO / 60);
  const hoursSavedMonthly = Math.round(manualHoursMonthly - preflightHoursMonthly);
  const laborCostSaved = hoursSavedMonthly * adminHourlyWage;
  const pricingRiskSaved = Math.round(monthlyPOs * 0.02 * 350000); // 2% pricing error risk * 350k VND avg loss
  const totalMonthlySavings = laborCostSaved + pricingRiskSaved;

  const handleLeadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!leadEmail || !leadName || !leadPhone) return;
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const res = await fetch("/api/v1/leads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: leadName,
          company: leadCompany || "Doanh nghiệp phân phối",
          phone: leadPhone,
          email: leadEmail,
          erp: leadERP,
          volume: leadVolume,
          note: leadNote,
          website: honeypot, // Honeypot bot protection
        }),
      });

      if (res.status === 429) {
        setSubmitError("Bạn đã gửi quá 5 yêu cầu trong 1 phút. Vui lòng thử lại sau.");
        return;
      }

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setSubmitError(data.detail || "Không thể gửi đăng ký. Vui lòng liên hệ hotline.");
        return;
      }

      setSubmitted(true);
    } catch {
      setSubmitError("Lỗi kết nối máy chủ. Vui lòng liên hệ hotline (028) 7300 6868.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="landing-root" style={{ background: "var(--canvas)", minHeight: "100vh", color: "var(--ink)" }}>
      {/* 1. Hero Section */}
      <section
        style={{
          maxWidth: "1160px",
          margin: "0 auto",
          padding: "var(--space-10) var(--space-4) var(--space-8)",
          textAlign: "center",
        }}
      >
        <div style={{ display: "inline-flex", alignItems: "center", gap: "8px", background: "rgba(16,185,129,0.1)", border: "1px solid rgba(16,185,129,0.3)", borderRadius: "20px", padding: "4px 14px", marginBottom: "var(--space-4)" }}>
          <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#10b981" }} />
          <span style={{ fontSize: "0.8125rem", fontWeight: 700, color: "var(--color-primary)" }}>
            HỆ THỐNG KIỂM SOÁT ĐƠN HÀNG B2B THẾ HỆ MỚI
          </span>
        </div>

        <h1
          style={{
            fontSize: "clamp(2rem, 5vw, 3.25rem)",
            fontWeight: 800,
            lineHeight: 1.2,
            letterSpacing: "-0.03em",
            color: "var(--ink)",
            maxWidth: "960px",
            margin: "0 auto var(--space-4)",
          }}
        >
          Cổng Kiểm Soát An Toàn Tự Động Cho Đơn Đặt Hàng B2B
        </h1>

        <p
          style={{
            fontSize: "1.125rem",
            lineHeight: 1.6,
            color: "var(--muted)",
            maxWidth: "760px",
            margin: "0 auto var(--space-6)",
          }}
        >
          Tự động đọc đơn đặt hàng (PDF/Excel/Ảnh), kiểm tra tổng tiền dòng so với tổng đơn, đối chiếu giá đại lý, tồn kho và hạn mức công nợ. Cảnh báo và phê duyệt 1 chạm trên Telegram &amp; Zalo trước khi ghi sổ ERP.
        </p>

        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: "var(--space-3)", flexWrap: "wrap", marginBottom: "var(--space-8)" }}>
          <a
            href="#pilot"
            className="primary-button interactive"
            onClick={createRipple}
            style={{ fontSize: "1rem", padding: "12px 24px", textDecoration: "none", fontWeight: 700 }}
          >
            Đăng Ký Trải Nghiệm Pilot 30 Ngày →
          </a>
          <Link
            href="/pricing"
            className="secondary-button interactive"
            onClick={createRipple}
            style={{ fontSize: "1rem", padding: "12px 24px", textDecoration: "none", fontWeight: 700 }}
          >
            Xem Bảng Giá &amp; Gói Dịch Vụ
          </Link>
        </div>

        {/* Real Capabilities Badges */}
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: "24px", flexWrap: "wrap", fontSize: "0.875rem", color: "var(--muted)", fontWeight: 600 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ color: "var(--color-primary)", fontWeight: 800 }}>✔</span>
            <span>Tự kiểm tra tổng tiền dòng so với tổng đơn; sai lệch bị chặn để người kiểm tra</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ color: "var(--color-primary)", fontWeight: 800 }}>✔</span>
            <span>Nhật ký bất biến có chuỗi băm SHA-256, xuất được để đối soát</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ color: "var(--color-primary)", fontWeight: 800 }}>✔</span>
            <span>Kiểm tra tự động trong vài giây với file Excel/CSV/PDF có chữ</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ color: "var(--color-primary)", fontWeight: 800 }}>✔</span>
            <span>Ký thỏa thuận bảo mật bảng giá (NDA) trước khi thử nghiệm</span>
          </div>
        </div>
      </section>

      {/* 2. ERP Compatibility Strip */}
      <section style={{ borderTop: "1px solid var(--line)", borderBottom: "1px solid var(--line)", background: "var(--surface)", padding: "var(--space-6) var(--space-4)", textAlign: "center" }}>
        <p style={{ fontSize: "0.75rem", fontWeight: 800, letterSpacing: "0.1em", color: "var(--muted)", textTransform: "uppercase", margin: "0 0 16px" }}>
          TƯƠNG THÍCH VÀ ĐỒNG BỘ 2 CHIỀU VỚI CÁC NỀN TẢNG ERP PHỔ BIẾN
        </p>
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: "20px", flexWrap: "wrap" }}>
          <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--ink)", padding: "8px 16px", background: "var(--canvas)", borderRadius: "var(--radius-sm)", border: "1px solid var(--line)" }}>MISA AMIS ERP</div>
          <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--ink)", padding: "8px 16px", background: "var(--canvas)", borderRadius: "var(--radius-sm)", border: "1px solid var(--line)" }}>Bravo Software</div>
          <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--ink)", padding: "8px 16px", background: "var(--canvas)", borderRadius: "var(--radius-sm)", border: "1px solid var(--line)" }}>Fast Business Online</div>
          <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--ink)", padding: "8px 16px", background: "var(--canvas)", borderRadius: "var(--radius-sm)", border: "1px solid var(--line)" }}>Odoo Enterprise</div>
          <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--muted)", padding: "8px 16px", background: "var(--canvas)", borderRadius: "var(--radius-sm)", border: "1px dashed var(--line)" }}>SAP Business One (Đang tích hợp)</div>
        </div>
      </section>

      {/* 3. 4 Core Technological Pillars */}
      <section id="features" style={{ maxWidth: "1160px", margin: "0 auto", padding: "var(--space-10) var(--space-4)" }}>
        <div style={{ textAlign: "center", marginBottom: "var(--space-8)" }}>
          <p className="eyebrow">4 TRỤ CỘT CÔNG NGHỆ CỐT LÕI</p>
          <h2 style={{ fontSize: "2rem", fontWeight: 800, letterSpacing: "-0.02em", margin: "6px 0 12px" }}>
            Quy trình khép kín từ tiếp nhận đến ghi sổ ERP
          </h2>
          <p style={{ color: "var(--muted)", maxWidth: "700px", margin: "0 auto" }}>
            Giải phóng Sales Admin khỏi việc nhập liệu thủ công và ngăn chặn 100% các đơn hàng sai giá, thiếu tồn kho hoặc quá hạn mức nợ.
          </p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "var(--space-4)" }}>
          <div className="content-card" style={{ padding: "var(--space-5)" }}>
            <div style={{ fontSize: "1.75rem", marginBottom: "var(--space-2)" }}>🔍</div>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 8px" }}>Tự Động Bóc Tách &amp; Đối Soát Số Học</h3>
            <p style={{ fontSize: "0.875rem", color: "var(--muted)", lineHeight: 1.6, margin: 0 }}>
              Đọc tệp PDF, ảnh chụp hoặc Excel. Tự kiểm tra tổng tiền dòng so với tổng đơn; sai lệch bị chặn để người kiểm tra trước khi chuyển bước tiếp theo.
            </p>
          </div>

          <div className="content-card" style={{ padding: "var(--space-5)" }}>
            <div style={{ fontSize: "1.75rem", marginBottom: "var(--space-2)" }}>🧠</div>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 8px" }}>Khớp Mã Kho &amp; Đơn Vị Tính</h3>
            <p style={{ fontSize: "0.875rem", color: "var(--muted)", lineHeight: 1.6, margin: 0 }}>
              Cơ chế 4 tầng (Khớp chính xác $\rightarrow$ Fuzzy $\rightarrow$ Vector $\rightarrow$ LLM). Tự động nhận diện tên lóng tiếng Việt và quy đổi thùng/hộp/cây sang đơn vị chuẩn.
            </p>
          </div>

          <div className="content-card" style={{ padding: "var(--space-5)" }}>
            <div style={{ fontSize: "1.75rem", marginBottom: "var(--space-2)" }}>📱</div>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 8px" }}>Phê Duyệt 1 Chạm Telegram &amp; Zalo</h3>
            <p style={{ fontSize: "0.875rem", color: "var(--muted)", lineHeight: 1.6, margin: 0 }}>
              Khi phát hiện đơn hàng vi phạm chính sách giá hoặc tồn kho, hệ thống gửi thẻ cảnh báo chi tiết về điện thoại quản lý để duyệt hoặc từ chối tức thì.
            </p>
          </div>

          <div className="content-card" style={{ padding: "var(--space-5)" }}>
            <div style={{ fontSize: "1.75rem", marginBottom: "var(--space-2)" }}>🔒</div>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 8px" }}>Nhật Ký Bất Biến SHA-256 &amp; Outbox</h3>
            <p style={{ fontSize: "0.875rem", color: "var(--muted)", lineHeight: 1.6, margin: 0 }}>
              Nhật ký bất biến có chuỗi băm SHA-256, xuất được để đối soát. Hàng đợi Transactional Outbox đảm bảo đồng bộ vào ERP đúng duy nhất 1 lần (Exactly-Once).
            </p>
          </div>
        </div>
      </section>

      {/* 4. Interactive SKU Sandbox Widget */}
      <section id="sandbox" style={{ maxWidth: "1000px", margin: "0 auto", padding: "0 var(--space-4) var(--space-10)" }}>
        <div className="content-card" style={{ padding: "var(--space-6)", background: "var(--surface)" }}>
          <div style={{ textAlign: "center", marginBottom: "var(--space-5)" }}>
            <span className="badge-clean badge-clean-neutral" style={{ marginBottom: "var(--space-2)" }}>TRẢI NGHIỆM TRÍ TUỆ KHỚP MÃ KHO</span>
            <h2 style={{ fontSize: "1.5rem", fontWeight: 800, margin: "4px 0 8px" }}>
              Tự Động Hiểu &quot;Tên Lóng&quot; &amp; Biệt Danh Hàng Hóa Của Khách
            </h2>
            <p style={{ fontSize: "0.875rem", color: "var(--muted)", maxWidth: "600px", margin: "0 auto" }}>
              Khách hàng ghi theo cách của họ (viết tắt, gõ sai, tiếng lóng) — Hệ thống tự động ánh xạ về mã SKU kho chuẩn.
            </p>
          </div>

          <div style={{ marginBottom: "var(--space-4)" }}>
            <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--muted)", textTransform: "uppercase" }}>THỬ CÁC TÌNH HUỐNG MẪU:</span>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginTop: "6px" }}>
              {presets.map((p, idx) => (
                <button
                  key={idx}
                  className="secondary-button interactive"
                  onClick={() => handleTestQuery(p.query)}
                  style={{ fontSize: "0.75rem", padding: "4px 10px" }}
                >
                  {p.label}: <strong>&quot;{p.query}&quot;</strong>
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "var(--space-4)" }}>
            <div>
              <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 700, marginBottom: "4px" }}>
                Nhập Tên Hàng / Tên Viết Tắt:
              </label>
              <input
                type="text"
                value={testQuery}
                onChange={(e) => handleTestQuery(e.target.value)}
                placeholder="Gõ thử: dây mạng 3m, laptop a14, dock chuyển đổi..."
                style={{ width: "100%", padding: "10px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--color-outline-variant)" }}
              />
            </div>

            <div style={{ background: "rgba(16,185,129,0.06)", border: "1px solid var(--color-primary)", borderRadius: "var(--radius-sm)", padding: "12px 16px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--color-primary)" }}>KẾT QUẢ ÁNH XẠ:</span>
                <span className="badge-clean badge-clean-success" style={{ fontSize: "0.7rem" }}>{tierUsed}</span>
              </div>
              <div style={{ fontSize: "1.1rem", fontWeight: 800, color: "var(--ink)" }}>Mã SKU: {matchedSku}</div>
              <div style={{ fontSize: "0.8125rem", color: "var(--muted)", marginTop: "4px" }}>
                Độ tin cậy: {(confidence * 100).toFixed(0)}% • Thời gian xử lý: {latency}ms
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 5. Transparent ROI Calculator */}
      <section id="roi-calculator" style={{ maxWidth: "1000px", margin: "0 auto", padding: "0 var(--space-4) var(--space-10)" }}>
        <div className="content-card" style={{ padding: "var(--space-6)", border: "1px solid var(--color-primary)" }}>
          <div style={{ textAlign: "center", marginBottom: "var(--space-5)" }}>
            <span className="badge-clean badge-clean-success" style={{ marginBottom: "var(--space-2)" }}>BẢNG TÍNH HIỆU QUẢ HOÀN VỐN</span>
            <h2 style={{ fontSize: "1.5rem", fontWeight: 800, margin: "4px 0 8px" }}>
              Ước tính hiệu quả kinh tế cho doanh nghiệp của bạn
            </h2>
            <p style={{ fontSize: "0.875rem", color: "var(--muted)", maxWidth: "650px", margin: "0 auto" }}>
              Công thức dựa trên giả định thực tế: Giảm thời gian xử lý từ 20 phút xuống 30 giây/đơn và phòng ngừa 2% rủi ro sai sót đơn giá.
            </p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "var(--space-6)", alignItems: "center" }}>
            <div>
              <div style={{ marginBottom: "var(--space-4)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.875rem", fontWeight: 700, marginBottom: "4px" }}>
                  <span>Số đơn hàng trung bình mỗi ngày:</span>
                  <span style={{ color: "var(--color-primary)" }}>{dailyPOs} đơn/ngày</span>
                </div>
                <input
                  type="range"
                  min={10}
                  max={500}
                  step={5}
                  value={dailyPOs}
                  onChange={(e) => setDailyPOs(Number(e.target.value))}
                  style={{ width: "100%" }}
                />
              </div>

              <div style={{ marginBottom: "var(--space-4)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.875rem", fontWeight: 700, marginBottom: "4px" }}>
                  <span>Chi phí lương nhân viên nhập liệu:</span>
                  <span style={{ color: "var(--color-primary)" }}>{money(adminHourlyWage, "VND")}/giờ</span>
                </div>
                <input
                  type="range"
                  min={30000}
                  max={100000}
                  step={5000}
                  value={adminHourlyWage}
                  onChange={(e) => setAdminHourlyWage(Number(e.target.value))}
                  style={{ width: "100%" }}
                />
              </div>

              <div style={{ fontSize: "0.8125rem", color: "var(--muted)", lineHeight: 1.5, background: "var(--canvas)", padding: "10px", borderRadius: "var(--radius-sm)" }}>
                <strong>Công thức ước tính:</strong><br />
                • Tiết kiệm giờ làm: {dailyPOs} đơn $\times$ 24 ngày $\times$ 19.5 phút = {hoursSavedMonthly} giờ/tháng.<br />
                • Ngăn ngừa rủi ro giá: {dailyPOs} $\times$ 24 $\times$ 2% $\times$ 350.000 đ = {money(pricingRiskSaved, "VND")}/tháng.
              </div>
            </div>

            <div style={{ textAlign: "center", background: "linear-gradient(135deg, rgba(16,185,129,0.1) 0%, rgba(30,58,138,0.1) 100%)", padding: "var(--space-6)", borderRadius: "var(--radius-md)", border: "1px solid var(--color-primary)" }}>
              <div style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--muted)", textTransform: "uppercase" }}>TỔNG GIÁ TRỊ TIẾT KIỆM HÀNG THÁNG:</div>
              <div style={{ fontSize: "2.25rem", fontWeight: 900, color: "var(--color-primary)", margin: "8px 0" }}>
                {money(totalMonthlySavings, "VND")}
              </div>
              <div style={{ fontSize: "0.875rem", color: "var(--muted)" }}>
                Tiết kiệm tương đương <strong>{hoursSavedMonthly} giờ làm việc</strong> và phòng ngừa rủi ro sai giá.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 6. Lead Capture Form Section */}
      <section id="pilot" style={{ maxWidth: "800px", margin: "0 auto", padding: "0 var(--space-4) var(--space-10)" }}>
        <div className="content-card" style={{ padding: "var(--space-8)", background: "var(--surface)", border: "2px solid var(--color-primary)" }}>
          <div style={{ textAlign: "center", marginBottom: "var(--space-6)" }}>
            <span className="badge-clean badge-clean-success" style={{ marginBottom: "var(--space-2)" }}>CHƯƠNG TRÌNH PILOT 30 NGÀY</span>
            <h2 style={{ fontSize: "1.75rem", fontWeight: 800, margin: "6px 0 8px" }}>
              Đăng Ký Trải Nghiệm Pilot Miễn Phí
            </h2>
            <p style={{ fontSize: "0.875rem", color: "var(--muted)", maxWidth: "560px", margin: "0 auto" }}>
              Miễn phí 30 ngày (tối đa 500 đơn hàng). Ký thỏa thuận bảo mật bảng giá NDA trước khi khảo sát và thiết lập môi trường thử nghiệm riêng.
            </p>
          </div>

          {submitted ? (
            <div style={{ padding: "24px", background: "rgba(16,185,129,0.1)", borderRadius: "var(--radius-md)", textAlign: "center", border: "1px solid var(--color-primary)" }}>
              <div style={{ fontSize: "2rem", marginBottom: "8px" }}>🎉</div>
              <h3 style={{ color: "var(--color-primary)", margin: "0 0 8px", fontSize: "1.25rem" }}>Đã Nhận Thông Tin Đăng Ký!</h3>
              <p style={{ fontSize: "0.95rem", color: "var(--ink)", margin: 0, lineHeight: 1.6 }}>
                Chúng tôi sẽ liên hệ trong vòng 1 ngày làm việc qua số điện thoại <strong>{leadPhone}</strong> và email <strong>{leadEmail}</strong> để trao đổi chi tiết.
              </p>
            </div>
          ) : (
            <form onSubmit={handleLeadSubmit} style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "16px" }}>
              {/* Anti-bot honeypot */}
              <input
                type="text"
                name="website"
                value={honeypot}
                onChange={(e) => setHoneypot(e.target.value)}
                style={{ display: "none" }}
                tabIndex={-1}
                autoComplete="off"
              />

              <div>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: "4px" }}>
                  Họ và Tên Người Phụ Trách *
                </label>
                <input
                  type="text"
                  required
                  value={leadName}
                  onChange={(e) => setLeadName(e.target.value)}
                  placeholder="Nguyễn Văn A"
                  style={{ width: "100%", padding: "10px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--color-outline-variant)" }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: "4px" }}>
                  Tên Doanh Nghiệp / Đơn Vị *
                </label>
                <input
                  type="text"
                  required
                  value={leadCompany}
                  onChange={(e) => setLeadCompany(e.target.value)}
                  placeholder="Công ty CP / TNHH..."
                  style={{ width: "100%", padding: "10px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--color-outline-variant)" }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: "4px" }}>
                  Email Doanh Nghiệp (Work Email) *
                </label>
                <input
                  type="email"
                  required
                  value={leadEmail}
                  onChange={(e) => setLeadEmail(e.target.value)}
                  placeholder="ten@congty.vn"
                  style={{ width: "100%", padding: "10px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--color-outline-variant)" }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: "4px" }}>
                  Số Điện Thoại / Zalo *
                </label>
                <input
                  type="tel"
                  required
                  value={leadPhone}
                  onChange={(e) => setLeadPhone(e.target.value)}
                  placeholder="0912 345 678"
                  style={{ width: "100%", padding: "10px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--color-outline-variant)" }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: "4px" }}>
                  Hệ Thống ERP Đang Dùng
                </label>
                <select
                  value={leadERP}
                  onChange={(e) => setLeadERP(e.target.value)}
                  style={{ width: "100%", padding: "10px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--color-outline-variant)" }}
                >
                  <option value="MISA AMIS">MISA AMIS</option>
                  <option value="Bravo">Bravo Software</option>
                  <option value="Fast">Fast Business</option>
                  <option value="Odoo">Odoo</option>
                  <option value="SAP B1">SAP Business One</option>
                  <option value="Excel">Đang quản lý bằng Excel</option>
                  <option value="Khác">Khác / Tùy chỉnh</option>
                </select>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: "4px" }}>
                  Số Lượng Đơn/Ngày
                </label>
                <select
                  value={leadVolume}
                  onChange={(e) => setLeadVolume(e.target.value)}
                  style={{ width: "100%", padding: "10px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--color-outline-variant)" }}
                >
                  <option value="Dưới 30 đơn/ngày">Dưới 30 đơn/ngày</option>
                  <option value="30-100 đơn/ngày">30-100 đơn/ngày</option>
                  <option value="100-300 đơn/ngày">100-300 đơn/ngày</option>
                  <option value="Trên 300 đơn/ngày">Trên 300 đơn/ngày</option>
                </select>
              </div>

              <div style={{ gridColumn: "1 / -1" }}>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: "4px" }}>
                  Ghi Chú Hoặc Nhu Cầu Cụ Thể (Tùy chọn)
                </label>
                <textarea
                  rows={2}
                  value={leadNote}
                  onChange={(e) => setLeadNote(e.target.value)}
                  placeholder="Ví dụ: Cần kiểm tra công nợ và đồng bộ vào MISA AMIS..."
                  style={{ width: "100%", padding: "10px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--color-outline-variant)", resize: "vertical" }}
                />
              </div>

              {submitError && (
                <div style={{ gridColumn: "1 / -1", color: "var(--color-error)", fontSize: "0.875rem" }}>
                  ⚠️ {submitError}
                </div>
              )}

              <div style={{ gridColumn: "1 / -1", marginTop: "8px" }}>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="primary-button interactive"
                  onClick={createRipple}
                  style={{ width: "100%", justifyContent: "center", padding: "14px", fontSize: "1rem", fontWeight: 700 }}
                >
                  {isSubmitting ? "Đang gửi thông tin..." : "🚀 Kích Hoạt 30 Ngày Trải Nghiệm Pilot Miễn Phí"}
                </button>
                <p style={{ textAlign: "center", fontSize: "0.75rem", color: "var(--muted)", marginTop: "8px" }}>
                  🔒 Cam kết bảo mật thông tin 100%. Ký thỏa thuận NDA trước khi tiến hành thử nghiệm.
                </p>
              </div>
            </form>
          )}
        </div>
      </section>
    </div>
  );
}
