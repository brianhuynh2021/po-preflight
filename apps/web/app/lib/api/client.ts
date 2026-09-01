/**
 * PO Preflight Type-Safe API Client SDK
 * Target API Gateway: http://localhost:8001 (FastAPI)
 */

import type {
  AgentRunRequest,
  AgentRunResponse,
  CatalogItem,
  ConfirmExtractionRequest,
  CustomerCreditProfile,
  CustomerPriceAgreement,
  DashboardStats,
  DecisionRequest,
  DecisionResponse,
  ERPAdapterType,
  ERPSyncResponse,
  ExtractedOrder,
  OrderDetail,
  OrderSummary,
  OutboxStats,
  RuleConfig,
  SKUMatchResult,
  UOMConversion,
} from "./types";


const DEFAULT_BASE_URL = "http://localhost:8001";

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public data: unknown,
  ) {
    super(`API Error ${status} ${statusText}: ${JSON.stringify(data)}`);
    this.name = "ApiError";
  }
}

export interface ClientConfig {
  baseUrl?: string;
  headers?: Record<string, string>;
}

export function createApiClient(config: ClientConfig = {}) {
  const baseUrl = config.baseUrl || DEFAULT_BASE_URL;

  async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const url = `${baseUrl}${path}`;
    const headers = {
      Accept: "application/json",
      ...config.headers,
      ...options.headers,
    };

    const res = await fetch(url, { ...options, headers });

    if (!res.ok) {
      let errorData;
      try {
        errorData = await res.json();
      } catch {
        errorData = await res.text();
      }
      throw new ApiError(res.status, res.statusText, errorData);
    }

    return res.json() as Promise<T>;
  }

  // =========================================================================
  // 1. Purchase Orders API
  // =========================================================================
  const orders = {
    list: (params?: { status?: string; search?: string; limit?: number; offset?: number }) => {
      const q = new URLSearchParams();
      if (params?.status) q.append("status", params.status);
      if (params?.search) q.append("search", params.search);
      if (params?.limit) q.append("limit", params.limit.toString());
      if (params?.offset) q.append("offset", params.offset.toString());
      const queryStr = q.toString() ? `?${q.toString()}` : "";
      return request<OrderSummary[]>(`/api/v1/orders${queryStr}`);
    },

    get: (orderId: number | string) => {
      return request<OrderDetail>(`/api/v1/orders/${orderId}`);
    },

    upload: async (file: File | Blob, filename: string, stagedReview = false) => {
      const formData = new FormData();
      formData.append("file", file, filename);
      const queryStr = stagedReview ? "?staged_review=true" : "";
      return request<OrderDetail>(`/api/v1/orders/upload${queryStr}`, {
        method: "POST",
        body: formData,
      });
    },

    confirmExtraction: (orderId: number | string, payload: ConfirmExtractionRequest) => {
      return request<OrderDetail>(`/api/v1/orders/${orderId}/confirm-extraction`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    },

    decide: (orderId: number | string, payload: DecisionRequest) => {
      return request<DecisionResponse>(`/api/v1/orders/${orderId}/decide`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    },
  };

  // =========================================================================
  // 2. LangGraph Stateful Workflow Agent API
  // =========================================================================
  const agent = {
    run: (payload: AgentRunRequest) => {
      return request<AgentRunResponse>("/api/v1/agent/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    },

    resume: (threadId: string, payload: { decision: "APPROVED" | "REJECTED"; decided_by: string; notes?: string }) => {
      return request<AgentRunResponse>(`/api/v1/agent/resume/${threadId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    },

    getState: (threadId: string) => {
      return request<{
        thread_id: string;
        values: Record<string, unknown>;
        next_nodes: string[];
        checkpoint_id?: string;
      }>(`/api/v1/agent/state/${threadId}`);
    },
  };

  // =========================================================================
  // 3. 4-Tier SKU Resolution RAG API
  // =========================================================================
  const sku = {
    resolve: (querySku: string, customerId?: string) => {
      return request<SKUMatchResult>("/api/v1/sku/resolve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query_sku: querySku, customer_id: customerId }),
      });
    },

    batchResolve: (queries: Array<{ query_sku: string; customer_id?: string }>) => {
      return request<SKUMatchResult[]>("/api/v1/sku/batch-resolve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ queries }),
      });
    },
  };

  // =========================================================================
  // 4. Multimodal Ingestion & Vision OCR API
  // =========================================================================
  const ingest = {
    extract: async (file: File | Blob, filename: string) => {
      const formData = new FormData();
      formData.append("file", file, filename);
      return request<ExtractedOrder>("/api/v1/ingest/extract", {
        method: "POST",
        body: formData,
      });
    },
  };

  // =========================================================================
  // 5. Multi-Channel Approval Bot API (Telegram / Zalo)
  // =========================================================================
  const bot = {
    status: () => {
      return request<{
        telegram: { configured: boolean; dry_run: boolean };
        zalo: { configured: boolean; dry_run: boolean };
      }>("/api/v1/bot/status");
    },

    notifyTelegram: (orderId: number | string) => {
      return request<{ success: boolean; dry_run: boolean }>(`/api/v1/bot/telegram/notify/${orderId}`, {
        method: "POST",
      });
    },

    notifyZalo: (orderId: number | string) => {
      return request<{ success: boolean; dry_run: boolean }>(`/api/v1/bot/zalo/notify/${orderId}`, {
        method: "POST",
      });
    },
  };

  // =========================================================================
  // 6. ERP Integration & Transactional Outbox API
  // =========================================================================
  const erp = {
    sync: (orderId: number | string, adapterType: ERPAdapterType = "MOCK_SAP") => {
      return request<ERPSyncResponse>(`/api/v1/erp/sync/${orderId}?adapter_type=${adapterType}`, {
        method: "POST",
      });
    },

    processOutbox: (limit = 10, adapterType: ERPAdapterType = "MOCK_SAP") => {
      return request<{
        processed_count: number;
        adapter_used: string;
        responses: ERPSyncResponse[];
        outbox_stats: OutboxStats;
      }>(`/api/v1/erp/outbox/process?limit=${limit}&adapter_type=${adapterType}`, {
        method: "POST",
      });
    },

    getOutboxStatus: (limit = 20) => {
      return request<{
        stats: OutboxStats;
        events: Array<Record<string, unknown>>;
      }>(`/api/v1/erp/outbox/status?limit=${limit}`);
    },
  };

  // =========================================================================
  // 7. Enterprise B2B Contracts & Risk Master Data APIs
  // =========================================================================
  const b2b = {
    getCustomerPrices: (customerId: string) => {
      return request<CustomerPriceAgreement[]>(`/api/v1/customers/${customerId}/prices`);
    },
    setCustomerPrice: (customerId: string, payload: Omit<CustomerPriceAgreement, "customer_id">) => {
      return request<{ status: string; pricing: CustomerPriceAgreement }>(`/api/v1/customers/${customerId}/prices`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    },
    getCustomerCredit: (customerId: string) => {
      return request<CustomerCreditProfile>(`/api/v1/customers/${customerId}/credit`);
    },
    setCustomerCredit: (customerId: string, payload: Omit<CustomerCreditProfile, "customer_id">) => {
      return request<{ status: string; profile: CustomerCreditProfile }>(`/api/v1/customers/${customerId}/credit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    },
    getUOMConversions: (sku?: string) => {
      const q = sku ? `?sku=${encodeURIComponent(sku)}` : "";
      return request<UOMConversion[]>(`/api/v1/masters/uom-conversions${q}`);
    },
    setUOMConversion: (payload: UOMConversion) => {
      return request<{ status: string; conversion: UOMConversion }>("/api/v1/masters/uom-conversions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    },
  };

  // =========================================================================
  // 8. System Dashboard, Catalog, Rules & Realtime SSE APIs
  // =========================================================================
  const dashboard = {
    getStats: () => request<DashboardStats>("/api/v1/dashboard/stats"),
  };

  const catalog = {
    list: () => request<CatalogItem[]>("/api/v1/catalog"),
  };

  const rules = {
    getConfig: () => request<RuleConfig>("/api/v1/rules"),
  };

  function connectRealtimeStream(
    onEvent: (data: { event: string; data: Record<string, unknown>; timestamp?: number }) => void,
    onError?: (err: Event) => void,
  ): () => void {
    if (typeof window === "undefined" || !window.EventSource) {
      return () => {};
    }
    const eventSource = new EventSource(`${baseUrl}/api/v1/events/stream`);

    eventSource.onmessage = (e) => {
      try {
        const parsed = JSON.parse(e.data);
        onEvent(parsed);
      } catch {
        // Raw text event
      }
    };

    if (onError) {
      eventSource.onerror = onError;
    }

    return () => {
      eventSource.close();
    };
  }

  return {
    orders,
    agent,
    sku,
    ingest,
    bot,
    erp,
    b2b,
    dashboard,
    catalog,
    rules,
    connectRealtimeStream,
  };
}

export const api = createApiClient();

