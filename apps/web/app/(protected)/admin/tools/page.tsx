import Link from "next/link";
import { Workflow, Zap, Lock, ScanLine, ArrowRight } from "lucide-react";

export default function AdminToolsPage() {
  const tools = [
    {
      title: "Công cụ kiểm thử SKU (4-Tier RAG)",
      description:
        "Kiểm thử khả năng đối chiếu biệt danh SKU tiếng Việt, tra cứu độ tự tin qua 4 tầng: Exact -> RapidFuzz -> Dense Vector -> Gemini LLM.",
      href: "/rag-playground",
      icon: Zap,
      tag: "Trí tuệ nhân tạo RAG",
    },
    {
      title: "Sơ đồ luồng Agentic LangGraph",
      description:
        "Xem trực quan máy trạng thái LangGraph, các nút phân tích, trạm ngắt Human-in-the-Loop và điểm khôi phục trạng thái.",
      href: "/agent-graph",
      icon: Workflow,
      tag: "Agentic StateGraph",
    },
    {
      title: "Chứng thư nhật ký (chuỗi băm SHA-256)",
      description:
        "Xuất và kiểm định chứng chỉ tính toàn vẹn của sổ cái kiểm toán, xác thực chuỗi băm mật mã học không thể làm giả.",
      href: "/audit-certificate",
      icon: Lock,
      tag: "Mật mã học & Toàn vẹn",
    },
    {
      title: "Trạm xem xét bóc tách cũ (Staging Studio)",
      description:
        "Giao diện xem xét và xác nhận dữ liệu trích xuất OCR chuyên sâu (đã được tích hợp trực tiếp vào chi tiết đơn hàng).",
      href: "/staging",
      icon: ScanLine,
      tag: "Công cụ phụ trợ",
    },
  ];

  return (
    <div className="page admin-tools-page page-enter">
      <header className="page-header" style={{ marginBottom: "var(--space-6)" }}>
        <div>
          <p className="eyebrow">QUẢN TRỊ HỆ THỐNG · CHẨN ĐOÁN</p>
          <h1>Công cụ kỹ thuật &amp; RAG (Admin Diagnostics)</h1>
          <p style={{ color: "var(--muted)", margin: "4px 0 0", fontSize: "0.875rem" }}>
            Trung tâm quản trị các công cụ chẩn đoán chuyên sâu, kiểm thử ngữ nghĩa và kiểm toán mật mã học.
          </p>
        </div>
      </header>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
          gap: "var(--space-4)",
        }}
      >
        {tools.map((tool) => {
          const Icon = tool.icon;
          return (
            <Link
              key={tool.href}
              href={tool.href}
              className="content-card interactive"
              style={{
                textDecoration: "none",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                padding: "var(--space-5)",
                borderRadius: "var(--radius-lg)",
                transition: "all 0.2s cubic-bezier(0.16, 1, 0.3, 1)",
                border: "1px solid var(--line)",
              }}
            >
              <div>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    marginBottom: "var(--space-3)",
                  }}
                >
                  <div
                    style={{
                      width: "42px",
                      height: "42px",
                      borderRadius: "var(--radius-md)",
                      background: "rgba(37, 99, 235, 0.08)",
                      color: "var(--color-primary)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <Icon size={22} />
                  </div>
                  <span
                    style={{
                      fontSize: "0.7rem",
                      fontWeight: 700,
                      padding: "3px 8px",
                      borderRadius: "12px",
                      background: "var(--canvas)",
                      color: "var(--muted)",
                      border: "1px solid var(--line)",
                    }}
                  >
                    {tool.tag}
                  </span>
                </div>

                <h3 style={{ color: "var(--ink)", fontSize: "1.05rem", margin: "0 0 6px" }}>
                  {tool.title}
                </h3>
                <p style={{ color: "var(--muted)", fontSize: "0.825rem", lineHeight: 1.5, margin: 0 }}>
                  {tool.description}
                </p>
              </div>

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  marginTop: "var(--space-4)",
                  color: "var(--color-primary)",
                  fontWeight: 600,
                  fontSize: "0.8125rem",
                }}
              >
                <span>Mở công cụ</span>
                <ArrowRight size={15} />
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
