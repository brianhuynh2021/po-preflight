import type {
  AuditEvent,
  AuthUser,
  CatalogItem,
  ConfirmExtractionRequest,
  CreateUserPayload,
  CustomerCreditProfile,
  CustomerMaster,
  CustomerPriceAgreement,
  DashboardStats,
  ERPAdapterType,
  ERPSyncResponse,
  IngestionJobStatus,
  OrderDetail,
  OrderSummary,
  OutboxStats,
  RuleConfig,
  SKUMatchResult,
  SystemModes,
  UOMConversion,
  UpdateUserPayload,
  UserAccount,
} from "./types";

export class ApiError extends Error {
  public readonly status: number;
  public readonly statusText: string;
  public readonly data: unknown;

  constructor(status: number, statusText: string, data: unknown) {
    super(`API Error ${status} ${statusText}`);
    this.name = "ApiError";
    this.status = status;
    this.statusText = statusText;
    this.data = data;
  }
}

export function describeError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.data && typeof err.data === "object") {
      const p = err.data as { detail?: string; title?: string; message?: string };
      if (p.detail) return String(p.detail);
      if (p.title) return String(p.title);
      if (p.message) return String(p.message);
    }
    return `Lỗi máy chủ (${err.status}: ${err.statusText})`;
  }
  if (err instanceof Error) {
    return err.message;
  }
  return "Đã xảy ra lỗi không xác định";
}

export interface ClientConfig {
  baseUrl?: string;
  headers?: Record<string, string>;
}

const DEFAULT_BASE_URL = "http://localhost:8001";

export function createApiClient(config: ClientConfig = {}) {
  const baseUrl = config.baseUrl || DEFAULT_BASE_URL;

  async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const url = `${baseUrl}${path}`;
    const headers = {
      Accept: "application/json",
      ...config.headers,
      ...options.headers,
    };

    const res = await fetch(url, {
      ...options,
      headers,
      credentials: "include",
    });

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
  // 1. Auth & Session API
  // =========================================================================
  const auth = {
    login: (apiKey: string) =>
      request<AuthUser>("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: apiKey }),
      }),
    me: () => request<AuthUser>("/api/v1/auth/me"),
    logout: () =>
      request<{ success: boolean; message: string }>("/api/v1/auth/logout", {
        method: "POST",
      }),
  };

  // =========================================================================
  // 2. Purchase Orders API
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

    getSourceUrl: (orderId: number | string) => `${baseUrl}/api/v1/orders/${orderId}/source`,

    upload: async (file: File | Blob, filename: string, stagedReview = false) => {
      const formData = new FormData();
      formData.append("file", file, filename);
      const queryStr = stagedReview ? "?staged_review=true" : "";
      const url = `${baseUrl}/api/v1/orders/upload${queryStr}`;
      const res = await fetch(url, {
        method: "POST",
        headers: {
          ...config.headers,
        },
        credentials: "include",
        body: formData,
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        throw new ApiError(res.status, res.statusText, data);
      }
      return data as OrderDetail;
    },

    decide: (orderId: number | string, payload: { decision: string; note?: string }) => {
      return request<OrderDetail>(`/api/v1/orders/${orderId}/decide`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    },

    confirmExtraction: (orderId: number | string, payload: ConfirmExtractionRequest) => {
      return request<OrderDetail>(`/api/v1/orders/${orderId}/confirm-extraction`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    },
  };

  // =========================================================================
  // 3. Audit & Cryptographic Blocks API
  // =========================================================================
  const audit = {
    getEvents: (params?: { limit?: number; offset?: number; po_number?: string; actor?: string; action?: string }) => {
      const q = new URLSearchParams();
      if (params?.limit) q.append("limit", params.limit.toString());
      if (params?.offset) q.append("offset", params.offset.toString());
      if (params?.po_number) q.append("po_number", params.po_number);
      if (params?.actor) q.append("actor", params.actor);
      if (params?.action) q.append("action", params.action);
      const queryStr = q.toString() ? `?${q.toString()}` : "";
      return request<AuditEvent[]>(`/api/v1/audit/events${queryStr}`);
    },
    getBlocks: (poNumber: string) => request<Array<Record<string, unknown>>>(`/api/v1/audit/blocks/${poNumber}`),
  };

  // =========================================================================
  // 4. LangGraph Stateful Agent API
  // =========================================================================
  const agent = {
    start: (poNumber: string, payload?: Record<string, unknown>) => {
      return request<{ thread_id: string; status: string; current_node: string }>("/api/v1/agent/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ po_number: poNumber, ...payload }),
      });
    },
    resume: (threadId: string, payload: { decision: string; manager_note?: string; actor?: string }) => {
      return request<{ thread_id: string; status: string; final_state: Record<string, unknown> }>(
        `/api/v1/agent/${threadId}/resume`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        },
      );
    },
    getState: (threadId: string) => {
      return request<Record<string, unknown>>(`/api/v1/agent/${threadId}/state`);
    },
    getHistory: (threadId: string) => {
      return request<Array<Record<string, unknown>>>(`/api/v1/agent/${threadId}/history`);
    },
  };

  // =========================================================================
  // 5. SKU Waterfall Matcher API
  // =========================================================================
  const sku = {
    match: (query: string, customerId?: string) => {
      return request<SKUMatchResult>("/api/v1/matcher/sku", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, customer_id: customerId }),
      });
    },
    resolve: (query: string, customerId?: string) => {
      return request<SKUMatchResult>("/api/v1/matcher/sku", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, customer_id: customerId }),
      });
    },
    teachAlias: (customerId: string, rawQuery: string, targetSku: string) => {
      return request<{ success: boolean; message: string }>("/api/v1/matcher/alias", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_id: customerId,
          raw_query: rawQuery,
          target_sku: targetSku,
        }),
      });
    },
  };

  // =========================================================================
  // 6. Intelligent Ingestion API
  // =========================================================================
  const ingest = {
    submitDocument: async (file: File | Blob, filename: string) => {
      const formData = new FormData();
      formData.append("file", file, filename);
      const res = await fetch(`${baseUrl}/api/v1/ingestion/submit`, {
        method: "POST",
        headers: {
          ...config.headers,
        },
        credentials: "include",
        body: formData,
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        throw new ApiError(res.status, res.statusText, data);
      }
      return data as { job_id: string; status: string; format_detected: string };
    },
    getJobStatus: (jobId: string) => {
      return request<IngestionJobStatus>(`/api/v1/ingestion/jobs/${jobId}`);
    },
  };

  // =========================================================================
  // 7. Multi-Channel Chatbot Webhook APIs
  // =========================================================================
  const bot = {
    getStatus: () => request<{ telegram: Record<string, unknown>; zalo: Record<string, unknown> }>("/api/v1/bot/status"),
    linkTelegram: (telegramChatId: string, telegramUsername?: string) =>
      request<{ success: boolean; message: string }>("/api/v1/bot/telegram/link", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ telegram_chat_id: telegramChatId, telegram_username: telegramUsername }),
      }),
  };

  // =========================================================================
  // 8. ERP Outbox & Synchronization APIs
  // =========================================================================
  const erp = {
    getOutboxStatus: () => request<OutboxStats>("/api/v1/erp/outbox/status"),
    getOutboxEvents: (limit = 20) => request<Array<Record<string, unknown>>>(`/api/v1/erp/outbox/events?limit=${limit}`),
    processOutbox: (batchSize = 10) =>
      request<{ processed_count: number; results: Array<Record<string, unknown>> }>(
        `/api/v1/erp/outbox/process?batch_size=${batchSize}`,
        { method: "POST" },
      ),
    syncOrder: (orderId: number | string, adapter: ERPAdapterType = "SAP_S4HANA_MOCK") => {
      return request<ERPSyncResponse>(`/api/v1/erp/sync/${orderId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ adapter_name: adapter }),
      });
    },
  };

  // =========================================================================
  // 9. Enterprise B2B Contracts & Risk Master APIs
  // =========================================================================
  const b2b = {
    getPricing: (customerId: string) => request<CustomerPriceAgreement[]>(`/api/v1/b2b/pricing/${customerId}`),
    setPricing: (payload: CustomerPriceAgreement) =>
      request<{ success: boolean; message: string }>("/api/v1/b2b/pricing", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }),
    getCredit: (customerId: string) => request<CustomerCreditProfile>(`/api/v1/b2b/credits/${customerId}`),
    setCredit: (payload: CustomerCreditProfile) =>
      request<{ success: boolean; message: string }>("/api/v1/b2b/credits", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }),
    getUOM: (sku?: string) => {
      const q = sku ? `?sku=${encodeURIComponent(sku)}` : "";
      return request<UOMConversion[]>(`/api/v1/b2b/uom${q}`);
    },
    setUOM: (payload: UOMConversion) =>
      request<{ success: boolean; message: string }>("/api/v1/b2b/uom", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }),
  };

  // =========================================================================
  // 10. System Dashboard, Catalog, Rules & Health APIs
  // =========================================================================
  const dashboard = {
    getStats: () => request<DashboardStats>("/api/v1/dashboard/stats"),
  };

  const catalog = {
    list: () => request<CatalogItem[]>("/api/v1/catalog"),
    importCSV: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      const url = `${baseUrl}/api/v1/catalog/import`;
      const res = await fetch(url, {
        method: "POST",
        headers: {
          ...config.headers,
        },
        credentials: "include",
        body: formData,
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        throw new ApiError(res.status, res.statusText, data);
      }
      return data as { success: boolean; message: string; total_skus: number };
    },
  };

  const rules = {
    getConfig: () => request<RuleConfig>("/api/v1/rules"),
    updateConfig: (payload: Partial<RuleConfig>) =>
      request<{ success: boolean; message: string; policy: RuleConfig }>("/api/v1/rules", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }),
  };

  const customers = {
    list: (search?: string) =>
      request<CustomerMaster[]>(
        search ? `/api/v1/customers?search=${encodeURIComponent(search)}` : "/api/v1/customers",
      ),
    get: (code: string) =>
      request<
        CustomerMaster & {
          pricing?: CustomerPriceAgreement[];
          credit?: CustomerCreditProfile | null;
          recent_orders?: Array<{ id: number; po_number: string; status: string; total: number }>;
        }
      >(`/api/v1/customers/${encodeURIComponent(code)}`),
    create: (payload: { code: string; name: string; tax_code?: string; tier?: string; aliases?: string[] }) =>
      request<CustomerMaster>("/api/v1/customers", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }),
    update: (code: string, payload: { name?: string; tax_code?: string; tier?: string; aliases?: string[] }) =>
      request<CustomerMaster>(`/api/v1/customers/${encodeURIComponent(code)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }),
    delete: (code: string) =>
      request<void>(`/api/v1/customers/${encodeURIComponent(code)}`, {
        method: "DELETE",
      }),
    importCSV: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      const url = `${baseUrl}/api/v1/customers/import-csv`;
      const res = await fetch(url, {
        method: "POST",
        headers: {
          ...config.headers,
        },
        credentials: "include",
        body: formData,
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        throw new ApiError(res.status, res.statusText, data);
      }
      return data as { imported_count: number; errors: string[] };
    },
  };

  const system = {
    getModes: () => request<SystemModes>("/api/v1/system/modes"),
  };

  const health = {
    checkReady: () => request<{ status: string; database?: string }>("/health/ready"),
    checkLive: () => request<{ status: string }>("/health/live"),
  };

  function connectRealtimeStream(
    onEvent: (data: { event: string; data: Record<string, unknown>; timestamp?: number }) => void,
    onError?: (err: Event) => void,
  ): () => void {
    if (typeof window === "undefined" || !window.EventSource) {
      return () => {};
    }
    const eventSource = new EventSource(`${baseUrl}/api/v1/events/stream`, {
      withCredentials: true,
    });

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

  const users = {
    list: () => request<UserAccount[]>("/api/v1/users"),
    get: (username: string) => request<UserAccount>(`/api/v1/users/${encodeURIComponent(username)}`),
    create: (payload: CreateUserPayload) =>
      request<UserAccount>("/api/v1/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }),
    update: (username: string, payload: UpdateUserPayload) =>
      request<UserAccount>(`/api/v1/users/${encodeURIComponent(username)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }),
    delete: (username: string) =>
      request<{ success: boolean; message: string }>(`/api/v1/users/${encodeURIComponent(username)}`, {
        method: "DELETE",
      }),
    resetPassword: (username: string, newPassword: string) =>
      request<{ success: boolean; message: string }>(`/api/v1/users/${encodeURIComponent(username)}/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_password: newPassword }),
      }),
    unlock: (username: string) =>
      request<{ success: boolean; message: string }>(`/api/v1/users/${encodeURIComponent(username)}/unlock`, {
        method: "POST",
      }),
  };

  return {
    auth,
    orders,
    audit,
    agent,
    sku,
    rag: sku,
    ingest,
    bot,
    erp,
    b2b,
    dashboard,
    catalog,
    customers,
    users,
    rules,
    system,
    health,
    connectRealtimeStream,
  };
}

export const api = createApiClient();
