"use client";

import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FileText,
  ScanLine,
  Package,
  Workflow,
  Zap,
  ShieldCheck,
  RefreshCw,
  Lock,
  History,
  Settings,
  Globe,
  ChevronDown,
  MoreHorizontal,
  type LucideIcon,
} from "lucide-react";
import { useAppState } from "@/components/app/AppStateProvider";
import { useRipple } from "@/app/lib/useRipple";

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

interface NavGroup {
  name: string;
  items: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    name: "OPERATIONS",
    items: [
      { label: "Overview", href: "/overview", icon: LayoutDashboard },
      { label: "Orders", href: "/orders", icon: FileText },
      { label: "Staging Studio", href: "/staging", icon: ScanLine },
      { label: "Product Catalog", href: "/catalog", icon: Package },
    ],
  },
  {
    name: "AI & ORCHESTRATION",
    items: [
      { label: "LangGraph Visualizer", href: "/agent-graph", icon: Workflow },
      { label: "4-Tier RAG Tester", href: "/rag-playground", icon: Zap },
      { label: "Rules & Policies", href: "/rules", icon: ShieldCheck },
    ],
  },
  {
    name: "COMPLIANCE & ERP",
    items: [
      { label: "ERP Outbox Sync", href: "/erp-sync", icon: RefreshCw },
      { label: "Merkle Certificate", href: "/audit-certificate", icon: Lock },
      { label: "Audit Log", href: "/audit-log", icon: History },
      { label: "Bot Settings", href: "/settings", icon: Settings },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { orders } = useAppState();
  const { createRipple } = useRipple();

  const attentionCount = orders.filter(
    (order) => order.status === "Review required" || order.status === "Blocked",
  ).length;

  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark" aria-hidden="true">
          ✈
        </span>
        <span>Preflight</span>
      </div>

      <div className="workspace-switcher interactive" onClick={createRipple}>
        <span className="workspace-avatar">N</span>
        <span>
          <strong>Northwind Co.</strong>
          <small>Operations workspace</small>
        </span>
        <ChevronDown size={14} style={{ opacity: 0.7 }} aria-hidden="true" />
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
              const IconComponent = item.icon;

              return (
                <a
                  key={item.href}
                  href={item.href}
                  className={isActive ? "nav-item active interactive" : "nav-item interactive"}
                  onClick={createRipple}
                >
                  <span className="nav-icon" aria-hidden="true" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <IconComponent size={18} strokeWidth={1.75} />
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
        className="interactive"
        onClick={createRipple}
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
        <Globe size={15} strokeWidth={1.75} />
        <span>Marketing Landing Page ↗</span>
      </a>

      <div className="processing-card">
        <span className="live-dot" />
        <div>
          <strong>Processing is healthy</strong>
          <small>Last checked just now</small>
        </div>
      </div>

      <button className="profile interactive" onClick={createRipple}>
        <span className="profile-avatar">MC</span>
        <span>
          <strong>Maya Chen</strong>
          <small>Operations manager</small>
        </span>
        <MoreHorizontal size={16} style={{ opacity: 0.7 }} aria-hidden="true" />
      </button>
    </aside>
  );
}
