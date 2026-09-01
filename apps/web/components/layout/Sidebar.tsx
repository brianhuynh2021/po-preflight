"use client";

import { usePathname } from "next/navigation";
import { useAppState } from "@/components/app/AppStateProvider";

interface NavGroup {
  name: string;
  items: { label: string; href: string; icon: string }[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    name: "OPERATIONS",
    items: [
      { label: "Overview", href: "/overview", icon: "⌂" },
      { label: "Orders", href: "/orders", icon: "▤" },
      { label: "Staging Studio", href: "/staging", icon: "✎" },
      { label: "Product Catalog", href: "/catalog", icon: "□" },
    ],
  },
  {
    name: "AI & ORCHESTRATION",
    items: [
      { label: "LangGraph Visualizer", href: "/agent-graph", icon: "⎇" },
      { label: "4-Tier RAG Tester", href: "/rag-playground", icon: "⚡" },
      { label: "Rules & Policies", href: "/rules", icon: "✓" },
    ],
  },
  {
    name: "COMPLIANCE & ERP",
    items: [
      { label: "ERP Outbox Sync", href: "/erp-sync", icon: "⇄" },
      { label: "Merkle Certificate", href: "/audit-certificate", icon: "🔒" },
      { label: "Audit Log", href: "/audit-log", icon: "◷" },
      { label: "Bot Settings", href: "/settings", icon: "⚙" },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { orders } = useAppState();

  const attentionCount = orders.filter(
    (order) => order.status === "Review required" || order.status === "Blocked",
  ).length;

  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark" aria-hidden="true">
          O
        </span>
        <span>Preflight</span>
      </div>
      <div className="workspace-switcher">
        <span className="workspace-avatar">N</span>
        <span>
          <strong>Northwind Co.</strong>
          <small>Operations workspace</small>
        </span>
        <span aria-hidden="true">⌄</span>
      </div>

      <nav aria-label="Primary navigation" style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
        {NAV_GROUPS.map((group) => (
          <div key={group.name} style={{ marginBottom: "6px" }}>
            <div className="nav-section-label">{group.name}</div>
            {group.items.map((item) => {
              const isActive =
                (item.href === "/overview" && pathname === "/") ||
                pathname === item.href ||
                pathname.startsWith(`${item.href}/`);

              return (
                <a
                  key={item.href}
                  href={item.href}
                  className={isActive ? "nav-item active" : "nav-item"}
                >
                  <span className="nav-icon" aria-hidden="true">
                    {item.icon}
                  </span>
                  <span>{item.label}</span>
                  {item.label === "Orders" && attentionCount > 0 ? (
                    <span className="nav-count">{attentionCount}</span>
                  ) : null}
                </a>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="sidebar-spacer" />
      <a
        href="/landing"
        target="_blank"
        rel="noreferrer"
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          padding: "8px 12px",
          background: "var(--canvas)",
          border: "1px solid var(--line)",
          borderRadius: "6px",
          fontSize: "12px",
          fontWeight: 600,
          color: "var(--green)",
          textDecoration: "none",
          marginBottom: "10px",
        }}
      >
        <span>🌐</span>
        <span>Marketing Landing Page ↗</span>
      </a>
      <div className="processing-card">
        <span className="live-dot" />
        <div>
          <strong>Processing is healthy</strong>
          <small>Last checked just now</small>
        </div>
      </div>
      <button className="profile">
        <span className="profile-avatar">MC</span>
        <span>
          <strong>Maya Chen</strong>
          <small>Operations manager</small>
        </span>
        <span aria-hidden="true">⋯</span>
      </button>
    </aside>
  );
}
