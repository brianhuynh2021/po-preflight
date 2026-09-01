"use client";

import { usePathname } from "next/navigation";

import { useAppState } from "@/components/app/AppStateProvider";

const NAV_ITEMS: { label: string; href: string; icon: string; group?: string }[] = [
  { label: "Overview", href: "/overview", icon: "⌂", group: "CORE" },
  { label: "Orders", href: "/orders", icon: "▤", group: "CORE" },
  { label: "Staging Studio", href: "/staging", icon: "✎", group: "IDP" },
  { label: "Catalog", href: "/catalog", icon: "□", group: "CATALOG" },
  { label: "RAG Playground", href: "/rag-playground", icon: "⚡", group: "AI" },
  { label: "LangGraph Agent", href: "/agent-graph", icon: "⎇", group: "AI" },
  { label: "Rules & Policies", href: "/rules", icon: "✓", group: "RULES" },
  { label: "ERP Outbox Sync", href: "/erp-sync", icon: "⇄", group: "ERP" },
  { label: "Merkle Certificate", href: "/audit-certificate", icon: "🔒", group: "AUDIT" },
  { label: "Audit Log", href: "/audit-log", icon: "◷", group: "AUDIT" },
  { label: "Bot Settings", href: "/settings", icon: "⚙", group: "SETTINGS" },
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
      <nav aria-label="Primary navigation">
        {NAV_ITEMS.map((item) => (
          <a
            key={item.href}
            href={item.href}
            className={
              (item.href === "/overview" && pathname === "/") ||
              pathname === item.href ||
              pathname.startsWith(`${item.href}/`)
                ? "nav-item active"
                : "nav-item"
            }
          >
            <span className="nav-icon" aria-hidden="true">
              {item.icon}
            </span>
            {item.label}
            {item.label === "Orders" && attentionCount > 0 ? (
              <span className="nav-count">{attentionCount}</span>
            ) : null}
          </a>
        ))}
      </nav>
      <div className="sidebar-spacer" />
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
