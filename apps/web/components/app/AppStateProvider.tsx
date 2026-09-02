"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import type {
  ActivityEvent,
  Decision,
  FindingCode,
  OrderStatus,
  PurchaseOrder,
} from "@/app/lib/types";
import { FINDING_TITLE } from "@/app/lib/types";
import { seedOrders } from "@/app/lib/seed";
import type { AuthUser, SystemModes } from "@/app/lib/api/types";
import { api, describeError } from "@/app/lib/api/client";

interface AppState {
  orders: PurchaseOrder[];
  setOrders: React.Dispatch<React.SetStateAction<PurchaseOrder[]>>;
  activity: ActivityEvent[];
  setActivity: React.Dispatch<React.SetStateAction<ActivityEvent[]>>;
  isLiveConnected: boolean;
  isLoading: boolean;
  error: string | null;
  user: AuthUser | null;
  systemModes: SystemModes | null;
  healthStatus: "healthy" | "disconnected" | "checking";
  refreshOrders: () => Promise<void>;
  refreshAuth: () => Promise<void>;
  logout: () => Promise<void>;
}

const AppStateContext = createContext<AppState | null>(null);

function mapBackendStatusToFE(backendStatus: string): OrderStatus {
  const s = (backendStatus || "").toLowerCase();
  if (s.includes("ready") || s === "ready_for_approval") return "Ready";
  if (s.includes("block")) return "Blocked";
  if (s.includes("approv")) return "Approved";
  if (s.includes("change") || s === "needs_changes") return "Changes requested";
  if (s.includes("reject")) return "Rejected";
  return "Review required";
}

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [orders, setOrders] = useState<PurchaseOrder[]>(seedOrders);
  const [activity, setActivity] = useState<ActivityEvent[]>([]);
  const [isLiveConnected, setIsLiveConnected] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [systemModes, setSystemModes] = useState<SystemModes | null>(null);
  const [healthStatus, setHealthStatus] = useState<"healthy" | "disconnected" | "checking">("checking");

  const refreshAuth = useCallback(async () => {
    try {
      const u = await api.auth.me();
      setUser(u);
    } catch {
      // In dev or unauthenticated, user might be null or fall back
      setUser(null);
    }
  }, []);

  const refreshSystemModes = useCallback(async () => {
    try {
      const modes = await api.system.getModes();
      setSystemModes(modes);
    } catch {
      // System modes offline
    }
  }, []);

  const checkHealth = useCallback(async () => {
    try {
      await api.health.checkReady();
      setHealthStatus("healthy");
    } catch {
      setHealthStatus("disconnected");
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.auth.logout();
    } catch {
      // Ignore
    } finally {
      setUser(null);
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }
  }, []);

  const refreshOrders = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const liveData = await api.orders.list();
      if (Array.isArray(liveData)) {
        if (liveData.length > 0) {
          const liveOrders: PurchaseOrder[] = await Promise.all(
            liveData.map(async (sum) => {
              try {
                const detail = await api.orders.get(sum.id);
                const mappedDecisions: Decision[] = (detail.decisions || []).map((d) => ({
                  type:
                    d.decision === "approved"
                      ? "APPROVE"
                      : d.decision === "rejected"
                        ? "REJECT"
                        : "REQUEST_CHANGES",
                  actor: d.actor,
                  note: d.note || "",
                  createdAt: d.created_at || new Date().toISOString(),
                }));

                return {
                  id: detail.po_number || sum.po_number,
                  customer: detail.customer || sum.customer,
                  submittedAt: detail.created_at || sum.created_at || new Date().toISOString(),
                  sourceFile: detail.source_file || `${sum.po_number}.json`,
                  value: Number(detail.total ?? sum.total ?? 0),
                  currency: detail.currency || sum.currency || "VND",
                  status: mapBackendStatusToFE(detail.status || sum.status),
                  findings: (detail.findings || []).map((f) => ({
                    code: (f.code as FindingCode) || "PRICE_MISMATCH",
                    severity: f.severity === "error" ? "Error" : "Warning",
                    title: FINDING_TITLE[f.code as FindingCode] || f.message || "Phát hiện bất thường",
                    detail: f.message || "",
                    evidence: f.evidence || "",
                    sku: f.sku || null,
                  })),
                  lines: (detail.items || []).map((it) => ({
                    sku: it.sku,
                    product: it.name || it.sku,
                    quantity: it.quantity,
                    available: it.stock_available ?? 100,
                    unitPrice: Number(it.unit_price),
                    catalogPrice: Number(it.catalog_unit_price ?? it.unit_price),
                  })),
                  owner: detail.decisions?.[0]?.actor || "Hệ thống Preflight",
                  // Email-sourced orders are recorded with a "email://<sender>/<file>" source_file.
                  sourceChannel: detail.source_file?.startsWith("email://") ? "email" : "web",
                  senderEmail: detail.source_file?.startsWith("email://")
                    ? detail.source_file.slice("email://".length).split("/")[0]
                    : undefined,
                  timeline: (detail.decisions || []).map((d) => ({
                    title: d.decision === "approved" ? "Đã duyệt đơn" : d.decision === "rejected" ? "Đã từ chối đơn" : "Yêu cầu chỉnh sửa",
                    detail: d.note || `Quyết định: ${d.decision} bởi ${d.actor}`,
                    time: d.created_at || "Vừa xong",
                    type: "human" as const,
                  })),
                  decisions: mappedDecisions,
                };
              } catch {
                return {
                  id: sum.po_number,
                  customer: sum.customer,
                  submittedAt: sum.created_at || new Date().toISOString(),
                  sourceFile: `${sum.po_number}.json`,
                  value: Number(sum.total),
                  currency: sum.currency || "VND",
                  status: mapBackendStatusToFE(sum.status),
                  findings: [],
                  lines: [],
                  owner: "Hệ thống Preflight",
                  timeline: [],
                  decisions: [],
                };
              }
            }),
          );
          setOrders(liveOrders);
        } else {
          setOrders([]);
        }
        setIsLiveConnected(true);
      }
    } catch (err) {
      setError(describeError(err));
      setIsLiveConnected(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refreshAuth();
    void refreshSystemModes();
    void checkHealth();
    void refreshOrders();

    // 30s health check interval
    const interval = setInterval(() => {
      void checkHealth();
      void refreshSystemModes();
    }, 30000);

    // Connect to real-time SSE stream via api client
    const cleanup = api.connectRealtimeStream(
      (payload) => {
        setIsLiveConnected(true);
        if (payload.event === "order.created" || payload.event === "order.decided" || payload.event === "erp.synced") {
          setActivity((prev) => [
            {
              title: `Sự kiện: ${payload.event}`,
              detail: `Đơn ${String(payload.data?.po_number || "")} — trạng thái: ${String(payload.data?.status || "đã xử lý")}`,
              time: "Vừa xong",
              type: "system",
            },
            ...prev,
          ]);
          void refreshOrders();
        }
      },
      () => {
        setIsLiveConnected(false);
      },
    );

    return () => {
      clearInterval(interval);
      cleanup();
    };
  }, [refreshAuth, refreshSystemModes, checkHealth, refreshOrders]);

  const value = useMemo(
    () => ({
      orders,
      setOrders,
      activity,
      setActivity,
      isLiveConnected,
      isLoading,
      error,
      user,
      systemModes,
      healthStatus,
      refreshOrders,
      refreshAuth,
      logout,
    }),
    [
      orders,
      activity,
      isLiveConnected,
      isLoading,
      error,
      user,
      systemModes,
      healthStatus,
      refreshOrders,
      refreshAuth,
      logout,
    ],
  );

  return (
    <AppStateContext.Provider value={value}>
      {children}
    </AppStateContext.Provider>
  );
}

export function useAppState(): AppState {
  const ctx = useContext(AppStateContext);
  if (!ctx) {
    throw new Error("useAppState must be used within an AppStateProvider");
  }
  return ctx;
}
