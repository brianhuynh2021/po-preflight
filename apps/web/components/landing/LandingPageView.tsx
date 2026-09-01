"use client";

import React, { useState, useEffect } from "react";
import { money } from "@/app/lib/derive";

export function LandingPageView() {
  // Auto-Playing Video Simulation State
  const [activeDemoTab, setActiveDemoTab] = useState<"intake" | "approval" | "merkle">("intake");
  const [isPlaying, setIsPlaying] = useState(true);
  const [progress, setProgress] = useState(0);

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
  const [leadName, setLeadName] = useState("");
  const [leadRole, setLeadRole] = useState("Trưởng Phòng Mua Hàng / Sales Admin");
  const [leadEmail, setLeadEmail] = useState("");
  const [leadCompany, setLeadCompany] = useState("");
  const [leadPhone, setLeadPhone] = useState("");
  const [leadERP, setLeadERP] = useState("SAP S/4HANA");
  const [submitted, setSubmitted] = useState(false);

  // Policy Modal State
  const [activePolicyModal, setActivePolicyModal] = useState<"privacy" | "terms" | "sla" | "nda" | null>(null);

  // Auto-play timer for video simulation
  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          setActiveDemoTab((curr) => {
            if (curr === "intake") return "approval";
            if (curr === "approval") return "merkle";
            return "intake";
          });
          return 0;
        }
        return prev + 2.5; // 4 seconds per cycle
      });
    }, 100);
    return () => clearInterval(interval);
  }, [isPlaying, activeDemoTab]);

  const selectTab = (tab: "intake" | "approval" | "merkle") => {
    setActiveDemoTab(tab);
    setProgress(0);
  };

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
  const monthlyPOs = dailyPOs * 24; // 24 working days
  const manualHoursMonthly = monthlyPOs * (20 / 60);
  const preflightHoursMonthly = monthlyPOs * (0.5 / 60);
  const hoursSavedMonthly = Math.round(manualHoursMonthly - preflightHoursMonthly);
  const laborCostSaved = hoursSavedMonthly * adminHourlyWage;
  const pricingRiskSaved = Math.round(monthlyPOs * 0.02 * 350000);
  const totalMonthlySavings = laborCostSaved + pricingRiskSaved;

  const handleLeadSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!leadEmail) return;
    setSubmitted(true);
    setTimeout(() => {
      setLeadName("");
      setLeadEmail("");
      setLeadCompany("");
      setLeadPhone("");
    }, 5000);
  };

  return (
    <div className="landing-root" style={{ background: "var(--canvas)", minHeight: "100vh", color: "var(--ink)", fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" }}>
      {/* 0. Top Founder Hotline & Direct Support Banner */}
      <div
        style={{
          background: "linear-gradient(90deg, #0f2b20 0%, #1e3a8a 100%)",
          color: "#ffffff",
          padding: "8px 24px",
          fontSize: "12.5px",
          fontWeight: 600,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "8px",
          borderBottom: "1px solid rgba(255,255,255,0.12)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ background: "#10b981", color: "#fff", padding: "1px 6px", borderRadius: "4px", fontSize: "10px", fontWeight: 800 }}>NHẬT MINH TECH</span>
          <span>Cổng Kiểm Soát Đơn Hàng B2B Tự Động Hóa Dành Cho Doanh Nghiệp Phân Phối &amp; Bán Buôn.</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "16px", fontSize: "12px" }}>
          <a href="tel:0984883750" style={{ color: "#fef08a", textDecoration: "none", fontWeight: 700, display: "flex", alignItems: "center", gap: "4px" }}>
            📞 Hotline / Zalo Founder: 0984 883 750
          </a>
          <a href="https://www.facebook.com/profile.php?id=61592607906687" target="_blank" rel="noopener noreferrer" style={{ color: "#93c5fd", textDecoration: "none", fontWeight: 700, display: "flex", alignItems: "center", gap: "4px" }}>
            🔵 Facebook Sáng Lập Viên
          </a>
        </div>
      </div>

      {/* 1. Main Navigation Bar */}
      <header
        style={{
          position: "sticky",
          top: 0,
          zIndex: 100,
          background: "rgba(255, 255, 255, 0.94)",
          backdropFilter: "blur(12px)",
          borderBottom: "1px solid var(--line)",
          padding: "14px 32px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          boxShadow: "0 4px 20px rgba(0,0,0,0.03)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <span
            style={{
              width: "36px",
              height: "36px",
              background: "linear-gradient(135deg, #059669 0%, #10b981 100%)",
              color: "#fff",
              borderRadius: "10px",
              display: "grid",
              placeItems: "center",
              fontWeight: 900,
              fontSize: "17px",
              boxShadow: "0 4px 12px rgba(16,185,129,0.3)",
            }}
          >
            P
          </span>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span style={{ fontSize: "19px", fontWeight: 800, letterSpacing: "-0.02em", color: "var(--ink)" }}>PO Preflight</span>
              <span className="badge-clean badge-clean-success" style={{ fontSize: "10px", padding: "1px 6px" }}>Nhật Minh Tech</span>
            </div>
            <div style={{ fontSize: "10px", color: "var(--muted)", fontWeight: 500 }}>Cổng Tiền Phê Duyệt Đơn Hàng B2B</div>
          </div>
        </div>

        <nav className="landing-nav-links">
          <a href="#demo-video" style={{ color: "var(--muted)", textDecoration: "none", transition: "color 0.2s" }}>🎬 Video Demo Tự Động</a>
          <a href="#problem" style={{ color: "var(--muted)", textDecoration: "none" }}>So Sánh Giải Pháp</a>
          <a href="#features" style={{ color: "var(--muted)", textDecoration: "none" }}>4 Trụ Cột Công Nghệ</a>
          <a href="#sandbox" style={{ color: "var(--muted)", textDecoration: "none" }}>Thử Khớp Mã RAG</a>
          <a href="#pricing" style={{ color: "var(--muted)", textDecoration: "none" }}>Gói Dịch Vụ</a>
          <a href="#security" style={{ color: "var(--muted)", textDecoration: "none" }}>Bảo Mật SOX 404</a>
          <a href="#contact" style={{ color: "var(--muted)", textDecoration: "none" }}>Liên Hệ Trực Tiếp</a>
        </nav>

        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <a href="/overview" className="secondary-button" style={{ fontSize: "13px", padding: "8px 14px", textDecoration: "none", fontWeight: 600 }}>
            🖥️ Mở Prototype App
          </a>
          <a
            href="#pilot"
            className="primary-button"
            style={{
              fontSize: "13px",
              padding: "9px 18px",
              textDecoration: "none",
              fontWeight: 700,
              background: "linear-gradient(135deg, #059669 0%, #10b981 100%)",
              boxShadow: "0 4px 14px rgba(16,185,129,0.35)",
            }}
          >
            🚀 Dùng Thử 14 Ngày
          </a>
        </div>
      </header>

      {/* 2. Hero Section */}
      <section style={{ maxWidth: "1240px", margin: "0 auto", padding: "64px 24px 36px", textAlign: "center" }}>
        <div style={{ display: "inline-flex", alignItems: "center", gap: "8px", background: "rgba(16,185,129,0.12)", border: "1px solid rgba(16,185,129,0.3)", padding: "6px 16px", borderRadius: "30px", marginBottom: "20px" }}>
          <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#10b981", display: "inline-block" }} />
          <span style={{ fontSize: "12.5px", fontWeight: 700, color: "#065f46" }}>
            DỰ ÁN PHÁT TRIỂN BỞI CÔNG TY CÔNG NGHỆ NHẬT MINH (NHAT MINH TECH)
          </span>
        </div>

        <h1 className="landing-hero-title">
          Cổng Kiểm Soát An Toàn Tự Động Cho Đơn Đặt Hàng B2B Trước Khi Đẩy Vào ERP
        </h1>

        <p className="landing-hero-subhead">
          Chấm dứt hoàn toàn 30 phút nhập tay, rủi ro lệch giá bán và tình trạng duyệt khống đơn khi kho đã cạn hàng.
          Bóc tách PDF/ảnh scan trong <strong>&lt;15ms</strong>, tự động hiểu tiếng lóng hàng hóa bằng AI 4 lớp và duyệt 1 chạm tức thì qua <strong>Telegram / Zalo</strong>.
        </p>

        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: "16px", marginBottom: "40px", flexWrap: "wrap" }}>
          <a
            href="#pilot"
            className="primary-button"
            style={{
              fontSize: "16px",
              padding: "14px 28px",
              textDecoration: "none",
              fontWeight: 800,
              background: "linear-gradient(135deg, #059669 0%, #10b981 100%)",
              boxShadow: "0 8px 24px rgba(16,185,129,0.4)",
            }}
          >
            🚀 Đăng Ký Trải Nghiệm Pilot 14 Ngày Miễn Phí →
          </a>
          <a
            href="#demo-video"
            className="secondary-button"
            style={{ fontSize: "15px", padding: "14px 24px", textDecoration: "none", fontWeight: 700 }}
          >
            🎬 Xem Video Demo Tự Động Chạy (3 Phút)
          </a>
          <a
            href="tel:0984883750"
            className="secondary-button"
            style={{ fontSize: "15px", padding: "14px 20px", textDecoration: "none", fontWeight: 700, color: "#0284c7", borderColor: "#bae6fd" }}
          >
            📞 Gọi Founder: 0984 883 750
          </a>
        </div>

        {/* Real Startup Trust Badges */}
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: "28px", flexWrap: "wrap", fontSize: "12.5px", color: "var(--muted)", fontWeight: 600 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ color: "#10b981", fontSize: "15px" }}>✔</span>
            <span>Bóc tách Zero-Hallucination &amp; Tự kiểm toán số học 100%</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ color: "#10b981", fontSize: "15px" }}>✔</span>
            <span>Founder-Led: Kỹ sư trưởng trực tiếp cấu hình &amp; hỗ trợ 1-1</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ color: "#10b981", fontSize: "15px" }}>✔</span>
            <span>Chạy thử trực tiếp trên tập file PO thực tế của bạn</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ color: "#10b981", fontSize: "15px" }}>✔</span>
            <span>Cam kết ký thỏa thuận NDA bảo mật bảng giá</span>
          </div>
        </div>
      </section>

      {/* 3. ERP Integrations Ribbon */}
      <section style={{ borderTop: "1px solid var(--line)", borderBottom: "1px solid var(--line)", background: "var(--paper)", padding: "28px 24px", textAlign: "center" }}>
        <p style={{ fontSize: "11px", fontWeight: 800, letterSpacing: "0.12em", color: "var(--muted)", textTransform: "uppercase", margin: "0 0 16px" }}>
          TƯƠNG THÍCH VÀ ĐỒNG BỘ 2 CHIỀU VỚI CÁC NỀN TẢNG ERP DOANH NGHIỆP TẠI VIỆT NAM
        </p>
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: "36px", flexWrap: "wrap" }}>
          <div style={{ fontWeight: 800, fontSize: "16px", color: "#1e293b", padding: "6px 14px", background: "#f8fafc", borderRadius: "6px", border: "1px solid #e2e8f0" }}>SAP S/4HANA</div>
          <div style={{ fontWeight: 800, fontSize: "16px", color: "#1e293b", padding: "6px 14px", background: "#f8fafc", borderRadius: "6px", border: "1px solid #e2e8f0" }}>Odoo Enterprise</div>
          <div style={{ fontWeight: 800, fontSize: "16px", color: "#1e293b", padding: "6px 14px", background: "#f8fafc", borderRadius: "6px", border: "1px solid #e2e8f0" }}>MISA AMIS ERP</div>
          <div style={{ fontWeight: 800, fontSize: "16px", color: "#1e293b", padding: "6px 14px", background: "#f8fafc", borderRadius: "6px", border: "1px solid #e2e8f0" }}>Bravo Software</div>
          <div style={{ fontWeight: 800, fontSize: "16px", color: "#1e293b", padding: "6px 14px", background: "#f8fafc", borderRadius: "6px", border: "1px solid #e2e8f0" }}>FAST Financial</div>
          <div style={{ fontWeight: 800, fontSize: "16px", color: "#1e293b", padding: "6px 14px", background: "#f8fafc", borderRadius: "6px", border: "1px solid #e2e8f0" }}>Excel / Google Sheets</div>
        </div>
      </section>

      {/* 4. AUTO-PLAYING INTERACTIVE VIDEO DEMO SHOWCASE PLAYER */}
      <section id="demo-video" style={{ maxWidth: "1200px", margin: "64px auto", padding: "0 24px" }}>
        <div
          className="clean-card"
          style={{
            padding: "26px",
            background: "var(--paper)",
            borderRadius: "16px",
            boxShadow: "0 25px 60px rgba(0,0,0,0.09)",
            border: "1px solid var(--line)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px", flexWrap: "wrap", gap: "12px" }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span className="live-dot" />
                <span className="eyebrow" style={{ margin: 0, color: "var(--green)" }}>TRẢI NGHIỆM TRỰC TIẾP — QUY TRÌNH 3 CHẶNG TỰ ĐỘNG HÓA</span>
              </div>
              <h2 style={{ fontSize: "24px", fontWeight: 800, margin: "4px 0 0", letterSpacing: "-0.01em" }}>
                Mô Phỏng Trực Quan Quy Trình Bóc Tách &amp; Phê Duyệt PO Tự Động
              </h2>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <button
                className="secondary-button"
                style={{ fontSize: "12px", padding: "7px 14px", fontWeight: 700 }}
                onClick={() => setIsPlaying(!isPlaying)}
              >
                {isPlaying ? "⏸ Tạm Dừng" : "▶ Tiếp Tục Phát"}
              </button>
            </div>
          </div>

          {/* 3 Horizontal Progress Segment Tabs */}
          <div className="landing-step-tabs">
            {/* Step 1 Tab */}
            <div
              onClick={() => selectTab("intake")}
              style={{
                cursor: "pointer",
                padding: "12px 16px",
                borderRadius: "10px",
                background: activeDemoTab === "intake" ? "var(--canvas)" : "transparent",
                border: activeDemoTab === "intake" ? "2px solid var(--green)" : "1px solid var(--line)",
                position: "relative",
                overflow: "hidden",
                transition: "all 0.2s ease",
              }}
            >
              <div style={{ fontSize: "13px", fontWeight: 800, color: activeDemoTab === "intake" ? "var(--green)" : "var(--ink)" }}>
                1. Bóc Tách &amp; Đối Chiếu Song Song
              </div>
              <div style={{ fontSize: "11px", color: "var(--muted)", marginTop: "2px" }}>OCR Vision + Khớp kho RAG &lt;15ms</div>
              {activeDemoTab === "intake" && (
                <div
                  style={{
                    position: "absolute",
                    bottom: 0,
                    left: 0,
                    height: "3px",
                    background: "var(--green)",
                    width: `${progress}%`,
                    transition: "width 0.1s linear",
                  }}
                />
              )}
            </div>

            {/* Step 2 Tab */}
            <div
              onClick={() => selectTab("approval")}
              style={{
                cursor: "pointer",
                padding: "12px 16px",
                borderRadius: "10px",
                background: activeDemoTab === "approval" ? "var(--canvas)" : "transparent",
                border: activeDemoTab === "approval" ? "2px solid var(--amber)" : "1px solid var(--line)",
                position: "relative",
                overflow: "hidden",
                transition: "all 0.2s ease",
              }}
            >
              <div style={{ fontSize: "13px", fontWeight: 800, color: activeDemoTab === "approval" ? "var(--amber)" : "var(--ink)" }}>
                2. Bắn Alert &amp; Duyệt 1 Chạm Telegram/Zalo
              </div>
              <div style={{ fontSize: "11px", color: "var(--muted)", marginTop: "2px" }}>Dừng luồng HITL khi có rủi ro</div>
              {activeDemoTab === "approval" && (
                <div
                  style={{
                    position: "absolute",
                    bottom: 0,
                    left: 0,
                    height: "3px",
                    background: "var(--amber)",
                    width: `${progress}%`,
                    transition: "width 0.1s linear",
                  }}
                />
              )}
            </div>

            {/* Step 3 Tab */}
            <div
              onClick={() => selectTab("merkle")}
              style={{
                cursor: "pointer",
                padding: "12px 16px",
                borderRadius: "10px",
                background: activeDemoTab === "merkle" ? "var(--canvas)" : "transparent",
                border: activeDemoTab === "merkle" ? "2px solid var(--green)" : "1px solid var(--line)",
                position: "relative",
                overflow: "hidden",
                transition: "all 0.2s ease",
              }}
            >
              <div style={{ fontSize: "13px", fontWeight: 800, color: activeDemoTab === "merkle" ? "var(--green)" : "var(--ink)" }}>
                3. Chứng Thư Merkle &amp; Đẩy SAP ERP
              </div>
              <div style={{ fontSize: "11px", color: "var(--muted)", marginTop: "2px" }}>Niêm phong SHA-256 SOX 404</div>
              {activeDemoTab === "merkle" && (
                <div
                  style={{
                    position: "absolute",
                    bottom: 0,
                    left: 0,
                    height: "3px",
                    background: "var(--green)",
                    width: `${progress}%`,
                    transition: "width 0.1s linear",
                  }}
                />
              )}
            </div>
          </div>

          {/* Animated Media Frame */}
          <div
            style={{
              position: "relative",
              borderRadius: "12px",
              overflow: "hidden",
              border: "1px solid var(--line)",
              background: "#0d1117",
              boxShadow: "inset 0 0 30px rgba(0,0,0,0.6)",
            }}
          >
            {activeDemoTab === "intake" && (
              <div>
                {/* 100% Native Vietnamese Dual-Pane OCR & Ingestion Simulation */}
                <div style={{ padding: "20px 20px 90px", minHeight: "400px", color: "#f8fafc", background: "linear-gradient(135deg, #0b1320 0%, #111e33 100%)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px", flexWrap: "wrap", gap: "10px", paddingBottom: "10px", borderBottom: "1px solid rgba(255,255,255,0.1)" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <span style={{ fontSize: "16px" }}>📄</span>
                      <span style={{ fontWeight: 700, fontSize: "13px", color: "#60a5fa" }}>ĐƠN HÀNG: DON-HANG-VIN-2026-8899.PDF</span>
                      <span style={{ fontSize: "11px", background: "rgba(59,130,246,0.2)", color: "#93c5fd", padding: "2px 8px", borderRadius: "12px", border: "1px solid rgba(59,130,246,0.4)" }}>PDF Scan Gốc</span>
                    </div>
                    <div style={{ display: "flex", gap: "8px", fontSize: "11px" }}>
                      <span style={{ background: "rgba(16,185,129,0.2)", color: "#34d399", padding: "3px 10px", borderRadius: "6px", fontWeight: 600 }}>✔ OCR Vision: 99.4%</span>
                      <span style={{ background: "rgba(245,158,11,0.2)", color: "#fbbf24", padding: "3px 10px", borderRadius: "6px", fontWeight: 600 }}>⚡ Đối chiếu: 14.8ms</span>
                    </div>
                  </div>

                  <div className="landing-demo-grid">
                    {/* Left: Vietnamese Purchase Order PDF Scan */}
                    <div style={{ background: "#ffffff", color: "#0f172a", padding: "14px", borderRadius: "8px", fontSize: "11px", boxShadow: "0 8px 24px rgba(0,0,0,0.3)", position: "relative" }}>
                      <div style={{ borderBottom: "2px solid #0f172a", paddingBottom: "6px", marginBottom: "6px" }}>
                        <div style={{ fontWeight: 800, fontSize: "11px", color: "#1e3a8a", textTransform: "uppercase" }}>Tập Đoàn Bán Lẻ Vingroup</div>
                        <div style={{ fontSize: "8.5px", color: "#64748b" }}>Số 7 Đường Bằng Lăng 1, KĐT Vinhomes Riverside, Long Biên, Hà Nội</div>
                        <div style={{ marginTop: "3px", fontWeight: 700, fontSize: "12px", color: "#0f172a", textAlign: "center" }}>ĐƠN ĐẶT HÀNG MUA B2B (PO)</div>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "9.5px", marginTop: "2px" }}>
                          <span>Số PO: <strong>PO-VN-2026-8899</strong></span>
                          <span>Ngày: <strong>01/09/2026</strong></span>
                        </div>
                      </div>
                      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "9px", marginTop: "4px" }}>
                        <thead>
                          <tr style={{ background: "#f1f5f9", borderBottom: "1px solid #cbd5e1" }}>
                            <th style={{ padding: "3px", textAlign: "left" }}>Tên mặt hàng scan</th>
                            <th style={{ padding: "3px", textAlign: "center" }}>SL</th>
                            <th style={{ padding: "3px", textAlign: "right" }}>Đơn giá</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr style={{ borderBottom: "1px solid #f1f5f9", background: "rgba(59,130,246,0.06)" }}>
                            <td style={{ padding: "3px" }}>1. Laptop Doanh Nghiệp A14 (16GB)</td>
                            <td style={{ padding: "3px", textAlign: "center" }}>10</td>
                            <td style={{ padding: "3px", textAlign: "right" }}>18.500.000 đ</td>
                          </tr>
                          <tr style={{ borderBottom: "1px solid #f1f5f9", background: "rgba(59,130,246,0.06)" }}>
                            <td style={{ padding: "3px" }}>2. Dây mạng 3m đúc sẵn Cat6</td>
                            <td style={{ padding: "3px", textAlign: "center" }}>50</td>
                            <td style={{ padding: "3px", textAlign: "right" }}>72.000 đ</td>
                          </tr>
                          <tr style={{ borderBottom: "1px solid #f1f5f9", background: "rgba(245,158,11,0.08)" }}>
                            <td style={{ padding: "3px" }}>3. Tai nghe họp chống ồn Pro</td>
                            <td style={{ padding: "3px", textAlign: "center" }}>5</td>
                            <td style={{ padding: "3px", textAlign: "right" }}>1.450.000 đ</td>
                          </tr>
                        </tbody>
                      </table>
                      <div style={{ marginTop: "6px", display: "flex", justifyContent: "space-between", fontWeight: 700, fontSize: "10.5px", borderTop: "1px dashed #cbd5e1", paddingTop: "4px" }}>
                        <span>Tổng tiền PO:</span>
                        <span style={{ color: "#1e3a8a" }}>195.850.000 đ</span>
                      </div>
                      <div style={{ position: "absolute", bottom: "8px", right: "10px", border: "1.5px solid #dc2626", color: "#dc2626", padding: "1px 6px", borderRadius: "4px", transform: "rotate(-6deg)", fontSize: "8.5px", fontWeight: 800 }}>
                        ✔ ĐÃ DUYỆT THU MUA
                      </div>
                    </div>

                    {/* Right: Automated Catalog & Inventory Matching */}
                    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                      <div style={{ background: "rgba(15,23,42,0.8)", border: "1px solid rgba(16,185,129,0.3)", borderRadius: "8px", padding: "8px 10px" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <span style={{ fontWeight: 700, fontSize: "11.5px", color: "#34d399" }}>Mã SKU: LAPTOP-A14 (Laptop Doanh Nghiệp)</span>
                          <span style={{ fontSize: "9.5px", background: "rgba(16,185,129,0.2)", color: "#34d399", padding: "2px 6px", borderRadius: "4px" }}>Tier 1 Exact</span>
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "10.5px", color: "#cbd5e1", marginTop: "3px" }}>
                          <span>Giá catalog: 18.500.000 đ (Khớp 100%)</span>
                          <span style={{ color: "#34d399", fontWeight: 600 }}>Tồn kho: 25 chiếc (Đủ hàng)</span>
                        </div>
                      </div>

                      <div style={{ background: "rgba(15,23,42,0.8)", border: "1px solid rgba(59,130,246,0.3)", borderRadius: "8px", padding: "8px 10px" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <span style={{ fontWeight: 700, fontSize: "11.5px", color: "#60a5fa" }}>Mã SKU: CAB-CAT6-3M (Cáp Mạng Cat6 3m)</span>
                          <span style={{ fontSize: "9.5px", background: "rgba(59,130,246,0.2)", color: "#93c5fd", padding: "2px 6px", borderRadius: "4px" }}>Tier 3 RAG Vector</span>
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "10.5px", color: "#cbd5e1", marginTop: "3px" }}>
                          <span>Tự động hiểu &quot;Dây mạng 3m đúc sẵn&quot;</span>
                          <span style={{ color: "#34d399", fontWeight: 600 }}>Tồn kho: 120 sợi (Đủ hàng)</span>
                        </div>
                      </div>

                      <div style={{ background: "rgba(120,53,15,0.25)", border: "1px solid rgba(245,158,11,0.5)", borderRadius: "8px", padding: "8px 10px" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <span style={{ fontWeight: 700, fontSize: "11.5px", color: "#fbbf24" }}>Mã SKU: HEADSET-PRO (Tai Nghe Chống Ồn)</span>
                          <span style={{ fontSize: "9.5px", background: "rgba(245,158,11,0.3)", color: "#fbbf24", padding: "2px 6px", borderRadius: "4px" }}>Cảnh Báo Tồn Kho</span>
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "10.5px", color: "#fef08a", marginTop: "3px" }}>
                          <span>Đơn mua: 5 chiếc</span>
                          <span style={{ fontWeight: 700, color: "#f87171" }}>Tồn kho tổng: 0 chiếc (Hết hàng sẵn)</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div
                  style={{
                    position: "absolute",
                    bottom: 0,
                    left: 0,
                    right: 0,
                    background: "linear-gradient(to top, rgba(13,17,23,0.95), rgba(13,17,23,0.7), transparent)",
                    padding: "20px 24px",
                    color: "#fff",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
                    <div>
                      <span className="badge-clean badge-clean-success" style={{ marginBottom: "6px", display: "inline-block" }}>
                        CHẶNG 1 &amp; 2: BÓC TÁCH OCR &amp; ĐỐI CHIẾU SONG SONG
                      </span>
                      <h3 style={{ margin: "4px 0", fontSize: "16px", color: "#fff" }}>
                        Đối Chiếu Trực Quan File Đơn Hàng Gốc vs Dữ Liệu Bóc Tách Tự Động
                      </h3>
                      <p style={{ margin: 0, fontSize: "13px", color: "#9ca3af", maxWidth: "800px" }}>
                        Hệ thống tự động đọc file PDF/ảnh scan mờ, bóc tách từng dòng sản phẩm với độ chính xác 99.4%, kiểm tra tồn kho và định dạng tiền tệ VNĐ trong 14.8ms.
                      </p>
                    </div>
                    <span className="code-snippet" style={{ color: "#34d399", background: "rgba(6,78,59,0.8)", borderColor: "#059669" }}>
                      Độ chính xác: 99.4% | Trạng thái: Hợp lệ
                    </span>
                  </div>
                </div>
              </div>
            )}

            {activeDemoTab === "approval" && (
              <div>
                {/* 100% Native Vietnamese LangGraph & Telegram Bot Approval Simulation */}
                <div style={{ padding: "20px 20px 90px", minHeight: "400px", color: "#f8fafc", background: "linear-gradient(135deg, #0b1120 0%, #1a162b 100%)" }}>
                  <div className="landing-approval-grid">
                    {/* Left: LangGraph DAG visualizer */}
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "10px" }}>
                        <span style={{ fontSize: "16px" }}>🦜</span>
                        <span style={{ fontWeight: 800, fontSize: "13px", color: "#c084fc" }}>SƠ ĐỒ LUỒNG LANGGRAPH AI TỰ ĐỘNG</span>
                      </div>
                      
                      <div style={{ display: "flex", flexDirection: "column", gap: "7px", fontSize: "10.5px" }}>
                        <div style={{ padding: "7px 10px", background: "rgba(16,185,129,0.15)", border: "1px solid #10b981", borderRadius: "6px", display: "flex", justifyContent: "space-between" }}>
                          <span>1. 📥 Tiếp Nhận &amp; OCR Bóc Tách PDF</span>
                          <span style={{ color: "#34d399", fontWeight: 600 }}>✔ Xong (142ms)</span>
                        </div>
                        <div style={{ padding: "7px 10px", background: "rgba(16,185,129,0.15)", border: "1px solid #10b981", borderRadius: "6px", display: "flex", justifyContent: "space-between" }}>
                          <span>2. 🧠 Khớp Mã Kho 4 Lớp (Hybrid RAG)</span>
                          <span style={{ color: "#34d399", fontWeight: 600 }}>✔ Xong (12ms)</span>
                        </div>
                        <div style={{ padding: "7px 10px", background: "rgba(245,158,11,0.2)", border: "1px solid #f59e0b", borderRadius: "6px", display: "flex", justifyContent: "space-between" }}>
                          <span>3. ⚖️ Kiểm Tra Luật Giá &amp; Tồn Kho</span>
                          <span style={{ color: "#fbbf24", fontWeight: 700 }}>⚠ Phát hiện: Hết tồn kho</span>
                        </div>
                        <div style={{ padding: "9px 10px", background: "rgba(245,158,11,0.3)", border: "2px solid #fbbf24", borderRadius: "8px", boxShadow: "0 0 16px rgba(245,158,11,0.4)" }}>
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            <span style={{ fontWeight: 800, color: "#fef08a" }}>4. ⏸️ ĐIỂM DỪNG PHÊ DUYỆT (HITL Checkpoint)</span>
                            <span style={{ fontSize: "9px", background: "#d97706", color: "#fff", padding: "2px 6px", borderRadius: "10px", fontWeight: 700 }}>ĐANG TẠM DỪNG</span>
                          </div>
                          <div style={{ fontSize: "9.5px", color: "#fef3c7", marginTop: "3px" }}>
                            Đã tạm dừng luồng và bắn cảnh báo tới điện thoại Giám đốc để xin ý kiến.
                          </div>
                        </div>
                        <div style={{ padding: "7px 10px", background: "rgba(255,255,255,0.04)", border: "1px dashed rgba(255,255,255,0.2)", borderRadius: "6px", display: "flex", justifyContent: "space-between", color: "#94a3b8" }}>
                          <span>5. 🚀 Đẩy Vào SAP S/4HANA &amp; Ghi Sổ Cái</span>
                          <span>🔒 Chờ Lệnh Duyệt</span>
                        </div>
                      </div>
                    </div>

                    {/* Right: Real Telegram Mobile Mockup in Vietnamese */}
                    <div style={{ background: "#17212b", borderRadius: "16px", border: "3px solid #2b5278", padding: "10px", boxShadow: "0 15px 35px rgba(0,0,0,0.6)", maxWidth: "330px", margin: "0 auto" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px", paddingBottom: "6px", borderBottom: "1px solid #242f3d", marginBottom: "6px" }}>
                        <span style={{ width: "24px", height: "24px", borderRadius: "50%", background: "#2481cc", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "12px" }}>🤖</span>
                        <div>
                          <div style={{ fontSize: "11px", fontWeight: 700, color: "#fff" }}>Preflight Alert Bot</div>
                          <div style={{ fontSize: "8.5px", color: "#6c7883" }}>bot • trực tuyến</div>
                        </div>
                      </div>

                      <div style={{ background: "#182533", padding: "8px 10px", borderRadius: "8px", fontSize: "10px", color: "#e4ecf2", lineHeight: 1.4 }}>
                        <div style={{ fontWeight: 700, color: "#64b5f6", marginBottom: "3px" }}>📋 CẢNH BÁO PO — ĐƠN HÀNG CẦN DUYỆT</div>
                        <div style={{ fontSize: "9.5px", color: "#90caf9", borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: "3px", marginBottom: "3px" }}>
                          Mã PO: <strong>PO-VN-2026-8899</strong><br/>
                          Khách hàng: <strong>Tập Đoàn Vingroup</strong><br/>
                          Tổng tiền: <strong>195.850.000 đ</strong>
                        </div>
                        <div style={{ fontSize: "9px", color: "#ffb74d" }}>
                          ⚠️ Trạng thái: <strong>CẦN DUYỆT (Review Required)</strong><br/>
                          🛡️ Rủi ro: <strong>Thiếu 5 tai nghe Headset-Pro</strong>
                        </div>
                      </div>

                      {/* Telegram Action Buttons */}
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px", marginTop: "6px" }}>
                        <button style={{ background: "#10b981", border: "none", color: "#fff", padding: "6px 4px", borderRadius: "6px", fontSize: "10px", fontWeight: 700, cursor: "pointer" }}>
                          🟢 Duyệt Đơn
                        </button>
                        <button style={{ background: "#ef4444", border: "none", color: "#fff", padding: "6px 4px", borderRadius: "6px", fontSize: "10px", fontWeight: 700, cursor: "pointer" }}>
                          🔴 Từ Chối
                        </button>
                      </div>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr", marginTop: "4px" }}>
                        <button style={{ background: "#2481cc", border: "none", color: "#fff", padding: "5px 4px", borderRadius: "6px", fontSize: "9px", fontWeight: 600, cursor: "pointer" }}>
                          📝 Yêu Cầu Sửa / Mở Cổng Web
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <div
                  style={{
                    position: "absolute",
                    bottom: 0,
                    left: 0,
                    right: 0,
                    background: "linear-gradient(to top, rgba(13,17,23,0.95), rgba(13,17,23,0.7), transparent)",
                    padding: "20px 24px",
                    color: "#fff",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
                    <div>
                      <span className="badge-clean badge-clean-warning" style={{ marginBottom: "6px", display: "inline-block" }}>
                        CHẶNG 3 &amp; 4: LUỒNG LANGGRAPH HITL &amp; DUYỆT TRÊN TELEGRAM / ZALO
                      </span>
                      <h3 style={{ margin: "4px 0", fontSize: "16px", color: "#fff" }}>
                        Tự Động Bắn Cảnh Báo Lệch Giá / Hết Hàng Về Telegram &amp; Zalo
                      </h3>
                      <p style={{ margin: 0, fontSize: "13px", color: "#9ca3af", maxWidth: "800px" }}>
                        Luồng LangGraph tự động dừng lại khi phát hiện đơn hàng có rủi ro và gửi thông báo giàu thông tin về điện thoại. Quản lý bấm [🟢 Duyệt Đơn] hoặc [🔴 Từ Chối] chỉ với 1 chạm.
                      </p>
                    </div>
                    <span className="code-snippet" style={{ color: "#fbbf24", background: "rgba(120,53,15,0.8)", borderColor: "#d97706" }}>
                      Điểm dừng HITL: Đang tạm dừng (Chờ Quản lý duyệt)
                    </span>
                  </div>
                </div>
              </div>
            )}

            {activeDemoTab === "merkle" && (
              <div>
                {/* 100% Native Vietnamese Merkle Certificate & SAP Outbox Simulation */}
                <div style={{ padding: "20px 20px 90px", minHeight: "400px", color: "#f8fafc", background: "linear-gradient(135deg, #061912 0%, #0d271e 100%)" }}>
                  <div className="landing-merkle-grid">
                    {/* Left: SOX 404 Cryptographic Merkle Certificate */}
                    <div style={{ background: "rgba(6,78,59,0.25)", border: "1px solid #10b981", borderRadius: "10px", padding: "14px", boxShadow: "0 8px 30px rgba(6,78,59,0.3)" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "10px" }}>
                        <span style={{ fontSize: "16px" }}>🔒</span>
                        <span style={{ fontWeight: 800, fontSize: "12px", color: "#34d399", textTransform: "uppercase" }}>CHỨNG THƯ SỐ NIÊM PHONG BĂM MERKLE</span>
                      </div>

                      <div style={{ display: "flex", flexDirection: "column", gap: "7px", fontSize: "10.5px" }}>
                        <div style={{ background: "rgba(0,0,0,0.3)", padding: "6px 8px", borderRadius: "6px" }}>
                          <div style={{ color: "#9ca3af", fontSize: "9px" }}>MÃ BĂM GỐC (MERKLE ROOT HASH - SHA-256):</div>
                          <div style={{ fontFamily: "monospace", color: "#34d399", fontSize: "10px", wordBreak: "break-all", marginTop: "2px" }}>
                            e7f8c92a1b4d830f6e1298c5417ab49d8c63e27189a03b5f7e4a112233445566
                          </div>
                        </div>

                        <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.08)", paddingBottom: "3px" }}>
                          <span style={{ color: "#9ca3af" }}>Thời gian niêm phong:</span>
                          <span style={{ fontWeight: 600, color: "#e2e8f0" }}>01/09/2026 14:32:05 (Giờ VN)</span>
                        </div>

                        <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.08)", paddingBottom: "3px" }}>
                          <span style={{ color: "#9ca3af" }}>Người ký phê duyệt:</span>
                          <span style={{ fontWeight: 600, color: "#60a5fa" }}>Trần Minh Tâm (GĐ Vận Hành)</span>
                        </div>

                        <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.08)", paddingBottom: "3px" }}>
                          <span style={{ color: "#9ca3af" }}>Kênh phê duyệt:</span>
                          <span style={{ fontWeight: 600, color: "#34d399" }}>Telegram 2FA Mobile (Xác thực OTP)</span>
                        </div>

                        <div style={{ marginTop: "3px", background: "rgba(16,185,129,0.15)", color: "#a7f3d0", padding: "5px 7px", borderRadius: "4px", fontSize: "9.5px" }}>
                          ✔ Đảm bảo tuân thủ SOX 404: Dữ liệu bất biến chống sửa đổi lén.
                        </div>
                      </div>
                    </div>

                    {/* Right: SAP S/4HANA ERP Outbox Dispatched */}
                    <div style={{ background: "rgba(15,23,42,0.8)", border: "1px solid rgba(59,130,246,0.4)", borderRadius: "10px", padding: "14px" }}>
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "10px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <span style={{ fontSize: "16px" }}>🚀</span>
                          <span style={{ fontWeight: 800, fontSize: "12px", color: "#60a5fa" }}>ĐỒNG BỘ SAP S/4HANA &amp; ODOO ERP</span>
                        </div>
                        <span style={{ background: "rgba(16,185,129,0.2)", color: "#34d399", fontSize: "9px", padding: "2px 6px", borderRadius: "10px", fontWeight: 700 }}>ĐÃ GHI SỔ CÁI</span>
                      </div>

                      <div style={{ display: "flex", flexDirection: "column", gap: "7px", fontSize: "10.5px" }}>
                        <div style={{ background: "rgba(0,0,0,0.3)", padding: "6px 8px", borderRadius: "6px" }}>
                          <div style={{ color: "#9ca3af", fontSize: "9px" }}>MÃ ĐƠN BÁN HÀNG SAP (SALES ORDER ID):</div>
                          <div style={{ fontWeight: 700, fontSize: "12px", color: "#60a5fa", marginTop: "2px" }}>SAP-SO-20268899</div>
                        </div>

                        <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.08)", paddingBottom: "3px" }}>
                          <span style={{ color: "#9ca3af" }}>Khóa chống trùng (Idempotency):</span>
                          <span style={{ fontFamily: "monospace", color: "#cbd5e1" }}>373a8527101d02ec</span>
                        </div>

                        <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.08)", paddingBottom: "3px" }}>
                          <span style={{ color: "#9ca3af" }}>Thời gian ghi nhận ERP:</span>
                          <span style={{ fontWeight: 600, color: "#34d399" }}>&lt; 4.2ms (Tức thì)</span>
                        </div>

                        <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.08)", paddingBottom: "3px" }}>
                          <span style={{ color: "#9ca3af" }}>Độ tin cậy giao dịch:</span>
                          <span style={{ fontWeight: 600, color: "#34d399" }}>100% Exactly-Once (Không trùng lặp)</span>
                        </div>

                        <div style={{ marginTop: "3px", background: "rgba(59,130,246,0.15)", color: "#bfdbfe", padding: "5px 7px", borderRadius: "4px", fontSize: "9.5px" }}>
                          ✔ Tự động hạch toán kế toán không cần nhân viên nhập tay vào ERP.
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div
                  style={{
                    position: "absolute",
                    bottom: 0,
                    left: 0,
                    right: 0,
                    background: "linear-gradient(to top, rgba(13,17,23,0.95), rgba(13,17,23,0.7), transparent)",
                    padding: "20px 24px",
                    color: "#fff",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
                    <div>
                      <span className="badge-clean badge-clean-success" style={{ marginBottom: "6px", display: "inline-block" }}>
                        CHẶNG 5 &amp; 6: CHỨNG THƯ MERKLE SOX 404 &amp; ĐỒNG BỘ SAP ERP
                      </span>
                      <h3 style={{ margin: "4px 0", fontSize: "16px", color: "#fff" }}>
                        Niêm Phong Chữ Ký Mã Hóa SHA-256 &amp; Đẩy Đơn Vào SAP S/4HANA Đúng Duy Nhất 1 Lần
                      </h3>
                      <p style={{ margin: 0, fontSize: "13px", color: "#9ca3af", maxWidth: "800px" }}>
                        Toàn bộ nhật ký bóc tách và người duyệt được băm vào chuỗi Merkle Tree chống sửa đổi lén. Sổ cái Outbox đảm bảo đồng bộ vào ERP chính xác tuyệt đối 100%.
                      </p>
                    </div>
                    <span className="code-snippet" style={{ color: "#34d399", background: "rgba(6,78,59,0.8)", borderColor: "#059669" }}>
                      Mã Băm Merkle: Đã Xác Thực | Đồng bộ SAP: 100% Hoàn Tất
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Live Telemetry Log Ticker below video frame */}
          <div
            style={{
              marginTop: "14px",
              padding: "10px 16px",
              background: "var(--canvas)",
              borderRadius: "8px",
              border: "1px solid var(--line)",
              fontSize: "12px",
              fontFamily: "ui-monospace, monospace",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "8px",
            }}
          >
            <div>
              <span style={{ color: "var(--green)", fontWeight: 700 }}>● HỆ THỐNG XỬ LÝ THỜI GIAN THỰC:</span>{" "}
              {activeDemoTab === "intake" && (
                <span>Bóc tách PO-VN-2026-8899.pdf ➔ Trích xuất 3 dòng sản phẩm ➔ Độ chính xác 99.4% ➔ Không ảo giác</span>
              )}
              {activeDemoTab === "approval" && (
                <span>Cảnh báo hết tồn kho SKU: HEADSET-PRO ➔ Bắn tin nhắn Telegram tới @giamdoc ➔ Chờ xác nhận</span>
              )}
              {activeDemoTab === "merkle" && (
                <span>Khởi tạo Merkle Root: e7f8c92a1b4d... ➔ Đẩy vào SAP S/4HANA (Mã đơn: SAP-SO-20268899)</span>
              )}
            </div>
            <span style={{ color: "var(--muted)" }}>Tự động chuyển tiếp sau mỗi 4 giây</span>
          </div>
        </div>
      </section>

      {/* 5. The Problem vs Solution (Side-by-Side Comparison) */}
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

        <div className="landing-grid-2">
          {/* Traditional Card */}
          <div className="clean-card" style={{ borderLeft: "4px solid var(--red)" }}>
            <span className="badge-clean" style={{ background: "var(--red-soft)", color: "var(--red)", marginBottom: "12px" }}>
              ❌ NHẬP TAY TRUYỀN THỐNG
            </span>
            <h3 style={{ fontSize: "18px", margin: "0 0 12px" }}>Chậm Chạp &amp; Rủi Ro Tiềm Ẩn</h3>
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
            <h3 style={{ fontSize: "18px", margin: "0 0 12px", color: "var(--green)" }}>Tốc Độ &amp; Chính Xác 100%</h3>
            <ul style={{ paddingLeft: "20px", fontSize: "13.5px", lineHeight: 1.8, color: "var(--ink)", margin: 0 }}>
              <li>Xử lý hoàn tất trong <strong>&lt; 30 giây</strong> với độ chính xác OCR 99.4%.</li>
              <li><strong>4 Lớp Khớp Mã Kho</strong> tự dịch tên lóng sang đúng mã SKU kho trong &lt;15ms.</li>
              <li>Kiểm toán số học tự động (Số lượng x Đơn giá = Tổng tiền) chống gian lận.</li>
              <li>Chặn đứng đơn hàng nếu tồn kho không khả dụng hoặc phát hiện trùng lặp.</li>
              <li>Quản lý duyệt 1 chạm trên <strong>Telegram / Zalo</strong> khi đang đi công tác.</li>
            </ul>
          </div>
        </div>
      </section>

      {/* 6. 4 Core Technological Pillars Section */}
      <section id="features" style={{ background: "var(--paper)", borderTop: "1px solid var(--line)", borderBottom: "1px solid var(--line)", padding: "64px 24px" }}>
        <div style={{ maxWidth: "1200px", margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: "48px" }}>
            <p className="eyebrow">4 TRỤ CỘT CÔNG NGHỆ CỐT LÕI</p>
            <h2 style={{ fontSize: "32px", fontWeight: 800, letterSpacing: "-0.02em", margin: "6px 0" }}>
              Những Đột Phá Giúp PO Preflight Hoạt Động Chuẩn Xác 100%
            </h2>
            <p style={{ color: "var(--muted)", maxWidth: "750px", margin: "0 auto" }}>
              Được thiết kế chuyên biệt để tự động hóa an toàn khâu tiếp nhận đơn hàng cho các doanh nghiệp bán buôn và chuỗi phân phối tại Việt Nam.
            </p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "24px" }}>
            <div className="clean-card" style={{ borderTop: "3px solid #10b981" }}>
              <div style={{ fontSize: "28px", marginBottom: "12px" }}>🔍</div>
              <h3 style={{ fontSize: "16px", fontWeight: 700, margin: "0 0 8px" }}>Bóc Tách Zero-Hallucination</h3>
              <p style={{ fontSize: "13px", color: "var(--muted)", lineHeight: 1.6, margin: 0 }}>
                Không bao giờ tự ý bịa số liệu. Cơ chế tự kiểm toán số học kiểm tra chéo tổng tiền vs từng dòng chi tiết, loại bỏ 100% rủi ro AI ảo giác.
              </p>
            </div>

            <div className="clean-card" style={{ borderTop: "3px solid #3b82f6" }}>
              <div style={{ fontSize: "28px", marginBottom: "12px" }}>🧠</div>
              <h3 style={{ fontSize: "16px", fontWeight: 700, margin: "0 0 8px" }}>4-Tier Waterfall Hybrid RAG</h3>
              <p style={{ fontSize: "13px", color: "var(--muted)", lineHeight: 1.6, margin: 0 }}>
                Thác lọc 4 tầng: Exact Hash Match $\rightarrow$ RapidFuzz $\rightarrow$ Vector Character Trigrams $\rightarrow$ LLM Reranker. Tự động dịch tên lóng sang mã SKU kho trong &lt;15ms.
              </p>
            </div>

            <div className="clean-card" style={{ borderTop: "3px solid #f59e0b" }}>
              <div style={{ fontSize: "28px", marginBottom: "12px" }}>📱</div>
              <h3 style={{ fontSize: "16px", fontWeight: 700, margin: "0 0 8px" }}>Phê Duyệt 1 Chạm Telegram &amp; Zalo</h3>
              <p style={{ fontSize: "13px", color: "var(--muted)", lineHeight: 1.6, margin: 0 }}>
                Human-In-The-Loop: Luồng xử lý tự động dừng khi phát hiện rủi ro và bắn cảnh báo tới Telegram/Zalo. Quản lý bấm Duyệt 1 chạm ngay trên điện thoại.
              </p>
            </div>

            <div className="clean-card" style={{ borderTop: "3px solid #8b5cf6" }}>
              <div style={{ fontSize: "28px", marginBottom: "12px" }}>🔒</div>
              <h3 style={{ fontSize: "16px", fontWeight: 700, margin: "0 0 8px" }}>SOX 404 Merkle &amp; Outbox Sync</h3>
              <p style={{ fontSize: "13px", color: "var(--muted)", lineHeight: 1.6, margin: 0 }}>
                Mỗi quyết định được niêm phong chuỗi băm Merkle Tree SHA-256 bất biến. Sổ cái Transactional Outbox đồng bộ vào ERP đúng duy nhất 1 lần (Exactly-Once).
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 7. Live Interactive SKU Matching Sandbox Widget */}
      <section id="sandbox" style={{ maxWidth: "1000px", margin: "0 auto", padding: "64px 24px" }}>
        <div style={{ textAlign: "center", marginBottom: "36px" }}>
          <p className="eyebrow">TRẢI NGHIỆM TRÍ TUỆ KHỚP MÃ KHO</p>
          <h2 style={{ fontSize: "32px", fontWeight: 800, letterSpacing: "-0.02em", margin: "6px 0" }}>
            Tự Động Hiểu &quot;Tên Lóng&quot; &amp; Biệt Danh Hàng Hóa Của Khách
          </h2>
          <p style={{ color: "var(--muted)", maxWidth: "650px", margin: "0 auto" }}>
            Khách hàng ghi theo cách của họ (viết tắt, gõ sai chính tả, tiếng lóng) — Hệ thống tự động dịch sang đúng <strong>Mã SKU Kho Chuẩn</strong> của công ty bạn chỉ trong <strong>0.01 giây</strong> mà không bao giờ bị nhầm hàng.
          </p>
        </div>

        <div className="clean-card" style={{ background: "var(--paper)" }}>
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
                  {p.label}: <strong>&quot;{p.query}&quot;</strong>
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

            <div style={{ background: "var(--canvas)", padding: "16px", borderRadius: "8px", border: "1px solid var(--line)" }}>
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
      </section>

      {/* 8. Interactive ROI Calculator Widget */}
      <section id="roi" style={{ background: "var(--paper)", borderTop: "1px solid var(--line)", borderBottom: "1px solid var(--line)", padding: "64px 24px" }}>
        <div style={{ maxWidth: "1000px", margin: "0 auto" }}>
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
        </div>
      </section>

      {/* 9. Startup-Friendly Pricing Packages */}
      <section id="pricing" style={{ maxWidth: "1200px", margin: "0 auto", padding: "64px 24px" }}>
        <div style={{ textAlign: "center", marginBottom: "48px" }}>
          <p className="eyebrow">GÓI ĐỒNG HÀNH &amp; TRIỂN KHAI THỰC TẾ</p>
          <h2 style={{ fontSize: "32px", fontWeight: 800, letterSpacing: "-0.02em", margin: "6px 0" }}>
            Chi Phí Tinh Gọn — Giá Trị Thiết Thực Cho Doanh Nghiệp Việt
          </h2>
          <p style={{ color: "var(--muted)", maxWidth: "600px", margin: "0 auto" }}>
            Không phí ẩn. Trực tiếp đội ngũ kỹ sư Nhật Minh Tech hỗ trợ cấu hình và đồng hành cùng đội ngũ Sales Admin của bạn.
          </p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "28px" }}>
          {/* Starter Plan */}
          <div className="clean-card" style={{ padding: "32px 24px", position: "relative" }}>
            <h3 style={{ fontSize: "20px", fontWeight: 800, margin: "0 0 6px" }}>Gói Startup / Vừa</h3>
            <p style={{ fontSize: "13px", color: "var(--muted)", margin: "0 0 16px" }}>Cho đại lý phân phối &amp; doanh nghiệp vừa</p>
            <div style={{ fontSize: "32px", fontWeight: 900, color: "var(--ink)", marginBottom: "16px" }}>
              1.900.000 đ<small style={{ fontSize: "13px", color: "var(--muted)", fontWeight: 500 }}> / tháng</small>
            </div>
            <ul style={{ listStyle: "none", padding: 0, margin: "0 0 24px", fontSize: "13px", lineHeight: 2 }}>
              <li>✔ Xử lý tối đa <strong>500 đơn PO / tháng</strong></li>
              <li>✔ Bóc tách OCR Vision chuẩn xác 99.4%</li>
              <li>✔ Khớp mã kho 4 lớp cơ bản (RAG)</li>
              <li>✔ Cảnh báo Telegram &amp; Zalo Bot 1 chạm</li>
              <li>✔ Hỗ trợ kỹ thuật trực tiếp qua Zalo/Hotline</li>
            </ul>
            <a href="#pilot" className="secondary-button" style={{ width: "100%", justifyContent: "center", textDecoration: "none", padding: "10px", fontWeight: 700 }}>
              Đăng Ký Gói Startup
            </a>
          </div>

          {/* Professional Plan (Featured) */}
          <div className="clean-card" style={{ padding: "32px 24px", border: "2px solid #10b981", boxShadow: "0 12px 35px rgba(16,185,129,0.15)", position: "relative" }}>
            <div style={{ position: "absolute", top: "-12px", right: "20px", background: "#10b981", color: "#fff", fontSize: "10px", fontWeight: 800, padding: "3px 10px", borderRadius: "12px", textTransform: "uppercase" }}>
              ⭐ KHUYÊN DÙNG
            </div>
            <h3 style={{ fontSize: "20px", fontWeight: 800, margin: "0 0 6px", color: "#065f46" }}>Gói Chuyên Nghiệp (Pro)</h3>
            <p style={{ fontSize: "13px", color: "var(--muted)", margin: "0 0 16px" }}>Cho chuỗi phân phối đa kho và tổng thầu B2B</p>
            <div style={{ fontSize: "32px", fontWeight: 900, color: "var(--green)", marginBottom: "16px" }}>
              4.900.000 đ<small style={{ fontSize: "13px", color: "var(--muted)", fontWeight: 500 }}> / tháng</small>
            </div>
            <ul style={{ listStyle: "none", padding: 0, margin: "0 0 24px", fontSize: "13px", lineHeight: 2 }}>
              <li>✔ Xử lý tối đa <strong>3.000 đơn PO / tháng</strong></li>
              <li>✔ Toàn bộ tính năng gói Startup</li>
              <li>✔ Đồng bộ 2 chiều vào SAP / Odoo / MISA / Bravo</li>
              <li>✔ Chứng thư số Merkle Tree SOX 404</li>
              <li>✔ Tự học thêm biệt danh hàng hóa mới</li>
              <li>✔ Hỗ trợ kỹ sư dedicated 24/7 trực tiếp</li>
            </ul>
            <a href="#pilot" className="primary-button" style={{ width: "100%", justifyContent: "center", textDecoration: "none", padding: "10px", fontWeight: 700, background: "linear-gradient(135deg, #059669 0%, #10b981 100%)" }}>
              Dùng Thử Gói Pro 14 Ngày
            </a>
          </div>

          {/* Enterprise / On-Premise Plan */}
          <div className="clean-card" style={{ padding: "32px 24px", position: "relative" }}>
            <h3 style={{ fontSize: "20px", fontWeight: 800, margin: "0 0 6px" }}>Gói On-Premise / May Đo</h3>
            <p style={{ fontSize: "13px", color: "var(--muted)", margin: "0 0 16px" }}>Cài đặt trên Server riêng của doanh nghiệp</p>
            <div style={{ fontSize: "24px", fontWeight: 900, color: "var(--ink)", marginBottom: "16px" }}>
              Tùy Biến Theo Yêu Cầu
            </div>
            <ul style={{ listStyle: "none", padding: 0, margin: "0 0 24px", fontSize: "13px", lineHeight: 2 }}>
              <li>✔ <strong>Không giới hạn số lượng đơn PO</strong></li>
              <li>✔ Cài đặt trên Private Cloud hoặc Server nội bộ</li>
              <li>✔ Tùy biến phân luồng phê duyệt theo phòng ban</li>
              <li>✔ Ký cam kết bảo mật NDA pháp lý</li>
              <li>✔ Kỹ sư Nhật Minh Tech tới tận nơi hỗ trợ Onsite</li>
            </ul>
            <a href="tel:0984883750" className="secondary-button" style={{ width: "100%", justifyContent: "center", textDecoration: "none", padding: "10px", fontWeight: 700 }}>
              📞 Gọi 0984 883 750 Tư Vấn
            </a>
          </div>
        </div>
      </section>

      {/* 10. Security & Compliance Section */}
      <section id="security" style={{ background: "var(--paper)", borderTop: "1px solid var(--line)", borderBottom: "1px solid var(--line)", padding: "64px 24px" }}>
        <div style={{ maxWidth: "1100px", margin: "0 auto", textAlign: "center" }}>
          <p className="eyebrow">BẢO MẬT &amp; CAM KẾT PHÁP LÝ</p>
          <h2 style={{ fontSize: "32px", fontWeight: 800, letterSpacing: "-0.02em", margin: "6px 0" }}>
            Bảo Vệ Tuyệt Đối Bảng Giá &amp; Dữ Liệu Khách Hàng Của Bạn
          </h2>
          <p style={{ color: "var(--muted)", maxWidth: "700px", margin: "0 auto 36px" }}>
            Chúng tôi hiểu rằng bảng giá đại lý và thông tin khách hàng là tài sản sống còn của doanh nghiệp. Mọi dòng dữ liệu đều được bảo vệ nghiêm ngặt.
          </p>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "20px", textAlign: "left" }}>
            <div className="clean-card">
              <h3 style={{ fontSize: "15px", color: "var(--ink)", margin: "0 0 6px" }}>🔒 Mã Hóa Đầu Cuối AES-256</h3>
              <p style={{ fontSize: "12.5px", color: "var(--muted)", margin: 0, lineHeight: 1.6 }}>
                Dữ liệu file scan và thông tin giá bán được mã hóa ngay khi truyền tải qua TLS 1.3 và lưu trữ bằng chuẩn AES-256 an toàn.
              </p>
            </div>
            <div className="clean-card">
              <h3 style={{ fontSize: "15px", color: "var(--ink)", margin: "0 0 6px" }}>📜 Cam Kết NDA Pháp Lý</h3>
              <p style={{ fontSize: "12.5px", color: "var(--muted)", margin: 0, lineHeight: 1.6 }}>
                Ký thỏa thuận bảo mật thông tin (NDA) có giá trị pháp lý trước khi triển khai, cam kết không chia sẻ dữ liệu cho bất kỳ bên thứ ba nào.
              </p>
            </div>
            <div className="clean-card">
              <h3 style={{ fontSize: "15px", color: "var(--ink)", margin: "0 0 6px" }}>🇻🇳 Server Đặt Tại Việt Nam</h3>
              <p style={{ fontSize: "12.5px", color: "var(--muted)", margin: 0, lineHeight: 1.6 }}>
                Hạ tầng máy chủ đặt tại Trung tâm dữ liệu VNPT &amp; Viettel IDC, tuân thủ Nghị định 13/2023/NĐ-CP về Bảo vệ dữ liệu cá nhân.
              </p>
            </div>
            <div className="clean-card">
              <h3 style={{ fontSize: "15px", color: "var(--ink)", margin: "0 0 6px" }}>⚖️ Merkle Root SOX 404</h3>
              <p style={{ fontSize: "12.5px", color: "var(--muted)", margin: 0, lineHeight: 1.6 }}>
                Chứng thực toán học bằng cây Merkle băm SHA-256 không thể sửa đổi lén sau lưng, làm bằng chứng pháp lý đối soát kế toán.
              </p>
            </div>
            <div className="clean-card">
              <h3 style={{ fontSize: "15px", color: "var(--ink)", margin: "0 0 6px" }}>🛡️ Phân Quyền 4 Cấp (RBAC)</h3>
              <p style={{ fontSize: "12.5px", color: "var(--muted)", margin: 0, lineHeight: 1.6 }}>
                Phân quyền chặt chẽ giữa Admin, Giám đốc phê duyệt, Kiểm toán viên nội bộ và Nhân viên bóc tách.
              </p>
            </div>
            <div className="clean-card">
              <h3 style={{ fontSize: "15px", color: "var(--ink)", margin: "0 0 6px" }}>⚡ Idempotent Exactly-Once</h3>
              <p style={{ fontSize: "12.5px", color: "var(--muted)", margin: 0, lineHeight: 1.6 }}>
                Cơ chế Transactional Outbox đảm bảo đơn hàng đẩy vào ERP đúng duy nhất 1 lần, loại bỏ 100% rủi ro tạo đơn trùng.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 11. FAQ Section */}
      <section style={{ maxWidth: "900px", margin: "0 auto", padding: "64px 24px" }}>
        <div style={{ textAlign: "center", marginBottom: "40px" }}>
          <p className="eyebrow">GIẢI ĐÁP THẮC MẮC</p>
          <h2 style={{ fontSize: "30px", fontWeight: 800, letterSpacing: "-0.02em", margin: "6px 0" }}>
            Câu Hỏi Thường Gặp
          </h2>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div className="clean-card" style={{ padding: "20px" }}>
            <h4 style={{ fontSize: "15px", fontWeight: 700, margin: "0 0 8px" }}>PO Preflight có cần cài đặt phần mềm vào máy tính nhân viên không?</h4>
            <p style={{ fontSize: "13.5px", color: "var(--muted)", lineHeight: 1.6, margin: 0 }}>
              Hoàn toàn không. PO Preflight hoạt động 100% trên nền tảng Cloud hoặc Private Server của công ty bạn. Nhân viên và Giám đốc có thể sử dụng qua trình duyệt web hoặc nhận thông báo và phê duyệt trực tiếp trên Telegram và Zalo.
            </p>
          </div>

          <div className="clean-card" style={{ padding: "20px" }}>
            <h4 style={{ fontSize: "15px", fontWeight: 700, margin: "0 0 8px" }}>Hệ thống có tự động cập nhật khi công ty tôi thêm mã SKU sản phẩm mới không?</h4>
            <p style={{ fontSize: "13.5px", color: "var(--muted)", lineHeight: 1.6, margin: 0 }}>
              Có. Hệ thống có cơ chế đồng bộ tự động với cơ sở dữ liệu ERP/Kho của bạn. Mỗi khi bạn thêm sản phẩm mới vào ERP, mô hình RAG sẽ tự động nạp mã SKU và học các từ khóa liên quan trong vòng 5 phút.
            </p>
          </div>

          <div className="clean-card" style={{ padding: "20px" }}>
            <h4 style={{ fontSize: "15px", fontWeight: 700, margin: "0 0 8px" }}>Thời gian triển khai thực tế mất bao lâu?</h4>
            <p style={{ fontSize: "13.5px", color: "var(--muted)", lineHeight: 1.6, margin: 0 }}>
              Chỉ từ <strong>1 đến 2 ngày làm việc</strong>. Kỹ sư trưởng Nhật Minh Tech sẽ trực tiếp cấu hình, nạp danh mục sản phẩm và test thực tế trên chính file PO của doanh nghiệp bạn.
            </p>
          </div>
        </div>
      </section>

      {/* 12. Lead Capture & Pilot Registration Form */}
      <section id="pilot" style={{ maxWidth: "900px", margin: "0 auto", padding: "0 24px 64px" }}>
        <div className="clean-card" style={{ padding: "40px", background: "var(--paper)", boxShadow: "0 15px 45px rgba(0,0,0,0.08)", border: "2px solid #10b981" }}>
          <div style={{ textAlign: "center", marginBottom: "28px" }}>
            <span className="badge-clean badge-clean-success" style={{ marginBottom: "8px" }}>CHƯƠNG TRÌNH ĐỒNG HÀNH MIỄN PHÍ</span>
            <h2 style={{ fontSize: "30px", fontWeight: 800, letterSpacing: "-0.02em", margin: "6px 0" }}>
              Đăng Ký Trải Nghiệm Pilot 14 Ngày
            </h2>
            <p style={{ color: "var(--muted)", maxWidth: "580px", margin: "0 auto", fontSize: "14.5px" }}>
              Miễn phí 100 đơn hàng đầu tiên. Không yêu cầu thẻ tín dụng. Founder Nhật Minh Tech sẽ liên hệ và thiết lập môi trường thử nghiệm riêng cho doanh nghiệp của bạn.
            </p>
          </div>

          {submitted ? (
            <div style={{ padding: "28px", background: "var(--green-soft)", borderRadius: "10px", textAlign: "center", border: "1px solid rgba(25,112,76,0.2)" }}>
              <div style={{ fontSize: "32px", marginBottom: "8px" }}>🎉</div>
              <h3 style={{ color: "var(--green)", margin: "0 0 8px", fontSize: "20px" }}>Đăng Ký Pilot Thành Công!</h3>
              <p style={{ fontSize: "14px", color: "var(--ink)", margin: 0, lineHeight: 1.6 }}>
                Founder Huỳnh Nguyễn (Nhật Minh Tech) sẽ liên hệ trực tiếp với bạn qua số điện thoại <strong>{leadPhone || "của bạn"}</strong> và email <strong>{leadEmail}</strong> trong vòng 15 phút làm việc.
              </p>
            </div>
          ) : (
            <form onSubmit={handleLeadSubmit} style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "18px" }}>
              <div>
                <label style={{ display: "block", fontSize: "12.5px", fontWeight: 700, marginBottom: "6px" }}>
                  Họ và Tên Người Phụ Trách *
                </label>
                <input
                  type="text"
                  required
                  className="input-clean"
                  value={leadName}
                  onChange={(e) => setLeadName(e.target.value)}
                  placeholder="Nguyễn Văn A"
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "12.5px", fontWeight: 700, marginBottom: "6px" }}>
                  Chức Vụ / Phòng Ban
                </label>
                <select className="input-clean" value={leadRole} onChange={(e) => setLeadRole(e.target.value)}>
                  <option>Trưởng Phòng Mua Hàng / Thu Mua</option>
                  <option>Giám Đốc Vận Hành (COO)</option>
                  <option>Trưởng Nhóm Sales Admin</option>
                  <option>Giám Đốc Công Nghệ (CTO / IT Head)</option>
                  <option>Ban Giám Đốc / CEO</option>
                </select>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "12.5px", fontWeight: 700, marginBottom: "6px" }}>
                  Email Công Việc (Work Email) *
                </label>
                <input
                  type="email"
                  required
                  className="input-clean"
                  value={leadEmail}
                  onChange={(e) => setLeadEmail(e.target.value)}
                  placeholder="ten.nguyen@congty.com"
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "12.5px", fontWeight: 700, marginBottom: "6px" }}>
                  Số Điện Thoại / Zalo Nhận Tư Vấn *
                </label>
                <input
                  type="tel"
                  required
                  className="input-clean"
                  value={leadPhone}
                  onChange={(e) => setLeadPhone(e.target.value)}
                  placeholder="0984.xxx.xxx"
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "12.5px", fontWeight: 700, marginBottom: "6px" }}>
                  Tên Doanh Nghiệp / Đơn Vị *
                </label>
                <input
                  type="text"
                  required
                  className="input-clean"
                  value={leadCompany}
                  onChange={(e) => setLeadCompany(e.target.value)}
                  placeholder="Công ty CP / TNHH..."
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "12.5px", fontWeight: 700, marginBottom: "6px" }}>
                  Hệ Thống ERP Đang Sử Dụng
                </label>
                <select className="input-clean" value={leadERP} onChange={(e) => setLeadERP(e.target.value)}>
                  <option>SAP S/4HANA</option>
                  <option>Odoo Enterprise</option>
                  <option>MISA AMIS ERP</option>
                  <option>Bravo Software</option>
                  <option>FAST Financial</option>
                  <option>Khác / Đang dùng Excel</option>
                </select>
              </div>

              <div style={{ gridColumn: "span 2", marginTop: "10px" }}>
                <button
                  type="submit"
                  className="primary-button"
                  style={{
                    width: "100%",
                    padding: "14px",
                    fontSize: "16px",
                    fontWeight: 800,
                    justifyContent: "center",
                    background: "linear-gradient(135deg, #059669 0%, #10b981 100%)",
                    boxShadow: "0 6px 20px rgba(16,185,129,0.4)",
                  }}
                >
                  🚀 Kích Hoạt 14 Ngày Trải Nghiệm Pilot Miễn Phí
                </button>
                <p style={{ textAlign: "center", fontSize: "11.5px", color: "var(--muted)", marginTop: "8px" }}>
                  🔒 Cam kết bảo mật thông tin 100%. Ký thỏa thuận NDA trước khi tiến hành thử nghiệm.
                </p>
              </div>
            </form>
          )}
        </div>
      </section>

      {/* 13. Comprehensive Authentic Footer with Real Contact, Address & Policies */}
      <footer id="contact" style={{ borderTop: "2px solid var(--line)", background: "#0b1320", color: "#cbd5e1", padding: "64px 32px 32px", fontSize: "13px" }}>
        <div style={{ maxWidth: "1240px", margin: "0 auto" }}>
          {/* Main Footer Grid */}
          <div className="landing-footer-grid">
            {/* Column 1: Company Profile & Authentic Location */}
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px" }}>
                <span style={{ width: "32px", height: "32px", background: "#10b981", color: "#fff", borderRadius: "8px", display: "grid", placeItems: "center", fontWeight: 900 }}>N</span>
                <span style={{ fontSize: "18px", fontWeight: 800, color: "#fff" }}>Công Ty Công Nghệ Nhật Minh</span>
              </div>
              <p style={{ fontSize: "12.5px", lineHeight: 1.7, color: "#94a3b8", marginBottom: "16px" }}>
                <strong>NHAT MINH TECHNOLOGY (NHAT MINH TECH)</strong><br />
                Đơn vị phát triển nền tảng <strong>PO Preflight</strong> — Cổng Tiền Phê Duyệt &amp; Kiểm Soát Đơn Hàng B2B Tự Động Hóa Chuẩn SOX 404 Hàng Đầu Cho Doanh Nghiệp Việt Nam.
              </p>

              <div style={{ fontSize: "12.5px", lineHeight: 1.8, color: "#cbd5e1" }}>
                <div>📍 <strong>Địa chỉ trụ sở:</strong> Khu phố 5, P. Tân Khai, Đồng Nai</div>
                <div>🌐 <strong>Phạm vi triển khai:</strong> Hỗ trợ On-site tại Đồng Nai, TP.HCM, Bình Dương &amp; Triển khai Remote toàn quốc.</div>
              </div>
            </div>

            {/* Column 2: Direct Contact Channels & Founder Hotline */}
            <div>
              <h4 style={{ fontSize: "14px", fontWeight: 800, color: "#fff", textTransform: "uppercase", marginBottom: "14px", letterSpacing: "0.05em" }}>
                KÊNH LIÊN HỆ TRỰC TIẾP
              </h4>
              <ul style={{ listStyle: "none", padding: 0, margin: 0, lineHeight: 2.2, fontSize: "12.5px" }}>
                <li>
                  📞 <strong>Hotline / Zalo Founder:</strong>{" "}
                  <a href="tel:0984883750" style={{ color: "#fef08a", textDecoration: "none", fontWeight: 700 }}>0984 883 750</a>
                </li>
                <li>
                  ✉️ <strong>Email Trực Tiếp:</strong>{" "}
                  <a href="mailto:huynh2102@gmail.com" style={{ color: "#67e8f9", textDecoration: "none" }}>huynh2102@gmail.com</a>
                </li>
                <li>
                  🔵 <strong>Facebook Sáng Lập Viên:</strong>{" "}
                  <a href="https://www.facebook.com/profile.php?id=61592607906687" target="_blank" rel="noopener noreferrer" style={{ color: "#60a5fa", textDecoration: "none" }}>
                    Huỳnh Nguyễn (Nhật Minh Tech)
                  </a>
                </li>
                <li>
                  ✈️ <strong>Telegram Hỗ Trợ:</strong>{" "}
                  <span style={{ color: "#cbd5e1" }}>@popreflight_support_bot</span>
                </li>
              </ul>
            </div>

            {/* Column 3: Platform Features & Quick Links */}
            <div>
              <h4 style={{ fontSize: "14px", fontWeight: 800, color: "#fff", textTransform: "uppercase", marginBottom: "14px", letterSpacing: "0.05em" }}>
                GIẢI PHÁP &amp; HỆ THỐNG
              </h4>
              <ul style={{ listStyle: "none", padding: 0, margin: 0, lineHeight: 2.2, fontSize: "12.5px" }}>
                <li><a href="/overview" style={{ color: "#94a3b8", textDecoration: "none" }}>App Dashboard Tổng Quan</a></li>
                <li><a href="/orders" style={{ color: "#94a3b8", textDecoration: "none" }}>Quản Lý Đơn Đặt Hàng (Orders)</a></li>
                <li><a href="/agent-graph" style={{ color: "#94a3b8", textDecoration: "none" }}>Sơ Đồ LangGraph AI Visualizer</a></li>
                <li><a href="/rag-playground" style={{ color: "#94a3b8", textDecoration: "none" }}>4-Tier Hybrid RAG Engine</a></li>
                <li><a href="/erp-sync" style={{ color: "#94a3b8", textDecoration: "none" }}>Transactional Outbox ERP Sync</a></li>
                <li><a href="/audit-certificate" style={{ color: "#94a3b8", textDecoration: "none" }}>Chứng Thư Băm Merkle SOX 404</a></li>
                <li><a href="/settings" style={{ color: "#94a3b8", textDecoration: "none" }}>Cấu Hình Bot Telegram &amp; Zalo</a></li>
              </ul>
            </div>

            {/* Column 4: Compliance, Security & Policies */}
            <div>
              <h4 style={{ fontSize: "14px", fontWeight: 800, color: "#fff", textTransform: "uppercase", marginBottom: "14px", letterSpacing: "0.05em" }}>
                CHÍNH SÁCH &amp; PHÁP LÝ
              </h4>
              <ul style={{ listStyle: "none", padding: 0, margin: 0, lineHeight: 2.2, fontSize: "12.5px" }}>
                <li>
                  <button onClick={() => setActivePolicyModal("privacy")} style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer", padding: 0, fontSize: "12.5px", textAlign: "left" }}>
                    📄 Chính Sách Bảo Mật Dữ Liệu
                  </button>
                </li>
                <li>
                  <button onClick={() => setActivePolicyModal("terms")} style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer", padding: 0, fontSize: "12.5px", textAlign: "left" }}>
                    📄 Điều Khoản Dịch Vụ &amp; Sử Dụng
                  </button>
                </li>
                <li>
                  <button onClick={() => setActivePolicyModal("sla")} style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer", padding: 0, fontSize: "12.5px", textAlign: "left" }}>
                    📄 Cam Kết Chất Lượng Dịch Vụ (SLA 99.9%)
                  </button>
                </li>
                <li>
                  <button onClick={() => setActivePolicyModal("nda")} style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer", padding: 0, fontSize: "12.5px", textAlign: "left" }}>
                    📄 Thỏa Thuận Bảo Mật Bảng Giá (NDA)
                  </button>
                </li>
              </ul>

              <div style={{ marginTop: "16px", padding: "10px", background: "rgba(255,255,255,0.05)", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.1)" }}>
                <div style={{ color: "#34d399", fontWeight: 700, fontSize: "11px", marginBottom: "4px" }}>✔ TIÊU CHUẨN KỸ THUẬT</div>
                <div style={{ fontSize: "11px", color: "#94a3b8" }}>Mã hóa AES-256 • Merkle SHA-256 SOX 404 • Zero-Hallucination Math Grounding</div>
              </div>
            </div>
          </div>

          {/* Bottom Copyright Bar */}
          <div style={{ borderTop: "1px solid rgba(255,255,255,0.1)", paddingTop: "24px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px", fontSize: "12px", color: "#64748b" }}>
            <div>
              © 2026 Nhật Minh Technology (Nhat Minh Tech). Bản quyền đã được đăng ký bảo hộ.
            </div>
            <div style={{ display: "flex", gap: "16px" }}>
              <span>Thời gian phản hồi RAG: &lt;15ms</span>
              <span>•</span>
              <span>Trạng thái máy chủ: 🟢 Hoạt động 100% bình thường</span>
            </div>
          </div>
        </div>
      </footer>

      {/* 14. Floating 1-Touch Contact Buttons for Quick Action */}
      <div style={{ position: "fixed", bottom: "24px", right: "24px", display: "flex", flexDirection: "column", gap: "10px", zIndex: 999 }}>
        <a
          href="https://www.facebook.com/profile.php?id=61592607906687"
          target="_blank"
          rel="noopener noreferrer"
          title="Facebook Huỳnh Nguyễn (Nhật Minh Tech)"
          style={{
            width: "48px",
            height: "48px",
            borderRadius: "50%",
            background: "#1877f2",
            color: "#fff",
            display: "grid",
            placeItems: "center",
            boxShadow: "0 8px 20px rgba(24,119,242,0.4)",
            textDecoration: "none",
            fontSize: "14px",
            fontWeight: 900,
          }}
        >
          FB
        </a>
        <a
          href="tel:0984883750"
          title="Gọi Hotline 0984 883 750"
          style={{
            width: "48px",
            height: "48px",
            borderRadius: "50%",
            background: "#10b981",
            color: "#fff",
            display: "grid",
            placeItems: "center",
            boxShadow: "0 8px 20px rgba(16,185,129,0.4)",
            textDecoration: "none",
            fontSize: "20px",
          }}
        >
          📞
        </a>
      </div>

      {/* 15. Policy & Legal Modal Popup */}
      {activePolicyModal && (
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
              background: "#ffffff",
              color: "#0f172a",
              maxWidth: "680px",
              width: "100%",
              maxHeight: "85vh",
              overflowY: "auto",
              borderRadius: "14px",
              padding: "28px",
              boxShadow: "0 25px 50px rgba(0,0,0,0.25)",
              position: "relative",
            }}
          >
            <button
              onClick={() => setActivePolicyModal(null)}
              style={{
                position: "absolute",
                top: "16px",
                right: "16px",
                background: "#f1f5f9",
                border: "none",
                borderRadius: "50%",
                width: "32px",
                height: "32px",
                cursor: "pointer",
                fontWeight: 700,
              }}
            >
              ✕
            </button>

            {activePolicyModal === "privacy" && (
              <div>
                <h3 style={{ fontSize: "20px", fontWeight: 800, margin: "0 0 12px", color: "#1e3a8a" }}>
                  Chính Sách Bảo Mật Dữ Liệu Doanh Nghiệp
                </h3>
                <p style={{ fontSize: "13.5px", lineHeight: 1.7, color: "#334155" }}>
                  Công ty Công nghệ Nhật Minh cam kết bảo vệ tuyệt đối dữ liệu đơn hàng, thông tin khách hàng, bảng giá đại lý và danh mục sản phẩm của Quý Doanh nghiệp.
                </p>
                <h4 style={{ fontSize: "14px", fontWeight: 700, marginTop: "16px" }}>1. Thu thập và xử lý dữ liệu</h4>
                <p style={{ fontSize: "13px", lineHeight: 1.6, color: "#475569" }}>
                  Hệ thống chỉ xử lý dữ liệu file scan đơn hàng và mã SKU nhằm mục đích bóc tách, đối chiếu kho và đồng bộ vào hệ thống ERP theo sự ủy quyền của Doanh nghiệp.
                </p>
                <h4 style={{ fontSize: "14px", fontWeight: 700, marginTop: "16px" }}>2. Vị trí lưu trữ &amp; Mã hóa</h4>
                <p style={{ fontSize: "13px", lineHeight: 1.6, color: "#475569" }}>
                  Toàn bộ cơ sở dữ liệu được lưu trữ an toàn, tuân thủ Nghị định 13/2023/NĐ-CP. Dữ liệu được mã hóa bằng thuật toán AES-256 trong trạng thái tĩnh và TLS 1.3 trong truyền tải.
                </p>
              </div>
            )}

            {activePolicyModal === "terms" && (
              <div>
                <h3 style={{ fontSize: "20px", fontWeight: 800, margin: "0 0 12px", color: "#1e3a8a" }}>
                  Điều Khoản Dịch Vụ &amp; Sử Dụng
                </h3>
                <p style={{ fontSize: "13.5px", lineHeight: 1.7, color: "#334155" }}>
                  Điều khoản này quy định quyền và trách nhiệm của Nhật Minh Tech và Khách hàng Doanh nghiệp khi sử dụng Cổng kiểm soát đơn hàng PO Preflight.
                </p>
                <h4 style={{ fontSize: "14px", fontWeight: 700, marginTop: "16px" }}>1. Trách nhiệm dịch vụ</h4>
                <p style={{ fontSize: "13px", lineHeight: 1.6, color: "#475569" }}>
                  PO Preflight cung cấp công cụ tự động hóa kiểm tra tính hợp lệ của đơn hàng và bảo đảm tính toàn vẹn của dữ liệu thông qua chữ ký số Merkle Tree.
                </p>
                <h4 style={{ fontSize: "14px", fontWeight: 700, marginTop: "16px" }}>2. Quyền sở hữu trí tuệ</h4>
                <p style={{ fontSize: "13px", lineHeight: 1.6, color: "#475569" }}>
                  Khách hàng sở hữu 100% dữ liệu đơn hàng và danh mục sản phẩm của mình. Nhật Minh Tech không sử dụng dữ liệu thương mại của Khách hàng để huấn luyện các mô hình AI công cộng.
                </p>
              </div>
            )}

            {activePolicyModal === "sla" && (
              <div>
                <h3 style={{ fontSize: "20px", fontWeight: 800, margin: "0 0 12px", color: "#065f46" }}>
                  Cam Kết Chất Lượng Dịch Vụ (SLA 99.9% Uptime)
                </h3>
                <p style={{ fontSize: "13.5px", lineHeight: 1.7, color: "#334155" }}>
                  Chúng tôi cam kết thời gian hoạt động liên tục (Uptime) đạt tối thiểu <strong>99.9%</strong> mỗi tháng cho tất cả các dịch vụ bóc tách OCR và đồng bộ ERP.
                </p>
                <h4 style={{ fontSize: "14px", fontWeight: 700, marginTop: "16px" }}>1. Thời gian phản hồi sự cố</h4>
                <p style={{ fontSize: "13px", lineHeight: 1.6, color: "#475569" }}>
                  Kỹ sư trưởng Nhật Minh Tech túc trực phản hồi trực tiếp qua Hotline/Zalo <strong>0984 883 750</strong> trong vòng <strong>15 phút</strong>.
                </p>
                <h4 style={{ fontSize: "14px", fontWeight: 700, marginTop: "16px" }}>2. Bồi hoàn vi phạm SLA</h4>
                <p style={{ fontSize: "13px", lineHeight: 1.6, color: "#475569" }}>
                  Nếu thời gian Uptime dưới 99.9%, Khách hàng sẽ được khấu trừ 10% đến 50% cước phí thuê bao của tháng tương ứng theo hợp đồng dịch vụ.
                </p>
              </div>
            )}

            {activePolicyModal === "nda" && (
              <div>
                <h3 style={{ fontSize: "20px", fontWeight: 800, margin: "0 0 12px", color: "#78350f" }}>
                  Thỏa Thuận Bảo Mật Bảng Giá (NDA Compliance)
                </h3>
                <p style={{ fontSize: "13.5px", lineHeight: 1.7, color: "#334155" }}>
                  Quy định bảo mật độc quyền thông tin chiết khấu thương mại, danh sách nhà phân phối và chính sách giá bán của Khách hàng.
                </p>
                <h4 style={{ fontSize: "14px", fontWeight: 700, marginTop: "16px" }}>1. Nghĩa vụ bảo mật</h4>
                <p style={{ fontSize: "13px", lineHeight: 1.6, color: "#475569" }}>
                  Đội ngũ kỹ sư Nhật Minh Tech không được phép truy cập, sao chép hoặc tiết lộ biểu giá của Khách hàng dưới bất kỳ hình thức nào.
                </p>
                <h4 style={{ fontSize: "14px", fontWeight: 700, marginTop: "16px" }}>2. Hiệu lực thỏa thuận</h4>
                <p style={{ fontSize: "13px", lineHeight: 1.6, color: "#475569" }}>
                  Thỏa thuận bảo mật có hiệu lực vô thời hạn kể từ ngày bắt đầu chạy thử nghiệm (Pilot) hoặc ký hợp đồng chính thức.
                </p>
              </div>
            )}

            <div style={{ marginTop: "24px", textAlign: "right" }}>
              <button
                onClick={() => setActivePolicyModal(null)}
                className="primary-button"
                style={{ padding: "8px 18px", fontSize: "13px" }}
              >
                Đóng Cửa Sổ
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
