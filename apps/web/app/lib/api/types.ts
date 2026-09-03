/**
 * TypeScript Data Models for PO Preflight REST API Gateway (:8001)
 */

export type OrderStatus =
  | "ready_for_approval"
  | "review_required"
  | "blocked"
  | "approved"
  | "rejected"
  | "needs_changes"
  | "extraction_review"
  | "received";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";

export type SeverityLevel = "error" | "warning" | "info";

export type LineVerificationStatus = "MATCHED" | "MISMATCH" | "UNKNOWN";

export type StockStatus = "IN_STOCK" | "LOW_STOCK" | "OUT_OF_STOCK";

export type DecisionType = "approved" | "rejected" | "needs_changes";

export interface Finding {
  code: "PRICE_MISMATCH" | "INSUFFICIENT_STOCK" | "UNKNOWN_SKU" | "INACTIVE_SKU" | "DUPLICATE_PO" | string;
  severity: SeverityLevel;
  message: string;
  sku?: string | null;
  evidence?: string | null;
}

export interface LineItem {
  line_number: number;
  sku: string;
  name: string;
  quantity: number;
  unit_price: number | string;
  catalog_unit_price?: number | string | null;
  price_diff_percent?: number | null;
  stock_available?: number | null;
  stock_status?: StockStatus | null;
  status: LineVerificationStatus;
}

export interface DecisionRecord {
  id: number;
  po_number: string;
  decision: DecisionType;
  actor: string;
  note?: string | null;
  created_at: string;
}

export interface OrderSummary {
  id: number;
  po_number: string;
  customer: string;
  status: OrderStatus;
  risk_level: RiskLevel;
  total: number;
  currency: string;
  items_count: number;
  findings_count: number;
  created_at: string;
}

export interface OrderDetail {
  id: number;
  po_number: string;
  customer: string;
  status: OrderStatus;
  risk_level: RiskLevel;
  total: number;
  currency: string;
  source_file: string;
  created_at: string;
  items: LineItem[];
  findings: Finding[];
  decisions: DecisionRecord[];
}

export interface DecisionRequest {
  decision: DecisionType;
  actor: string;
  note?: string;
}

export interface DecisionResponse {
  success: boolean;
  id: number;
  po_number: string;
  decision: string;
  actor: string;
  note: string;
  created_at: string;
}

export interface ConfirmExtractionItem {
  sku: string;
  quantity: number;
  unit_price: number | string;
}

export interface ConfirmExtractionRequest {
  po_number?: string | null;
  customer?: string | null;
  items: ConfirmExtractionItem[];
  currency?: string;
}

export interface AuthUser {
  user: string;
  role: "ADMIN" | "MANAGER" | "AUDITOR" | "VIEWER" | string;
  role_id: number;
  api_key_id?: string | null;
}

export interface AuditEvent {
  id: string;
  event_type: string;
  timestamp: string;
  po_number: string;
  action: string;
  actor: string;
  detail: string;
  hash?: string | null;
}

export interface SystemModes {
  company_name: string;
  database: string;
  ocr: string;
  telegram: string;
  zalo: string;
  erp: {
    adapter: string;
    mode: string;
  };
  fx: string;
  environment: string;
  auth_required: boolean;
  sse?: string;
  queue?: string;
  rate_limiter?: string;
}

export interface DashboardStats {
  total_orders: number;
  ready_count: number;
  review_required_count: number;
  blocked_count: number;
  approved_count: number;
  approved_today?: number;
  avg_decision_minutes?: number | null;
  orders_last_7_days?: number[];
  straight_through_rate?: number;
  pass_rate_percent: number;
  total_pipeline_value: number;
  violations_breakdown: Array<{
    code: string;
    count: number;
    percentage: number;
  }>;
  recent_orders: Array<Record<string, unknown>>;
}

export interface CatalogItem {
  sku: string;
  name: string;
  unit_price: number | string;
  stock: number;
  active: boolean;
  base_uom?: string;
  moq?: number;
  pack_size?: number;
  category?: string | null;
  barcode?: string | null;
  on_hand?: number | string | null;
  reserved_erp?: number | string | null;
  allocated_local?: number | string | null;
  atp?: number | string | null;
  as_of?: string | null;
  is_stale?: boolean;
}

export interface RuleConfig {
  price_tolerance_percent: number;
  stock_safety_margin: number;
  allow_inactive_sku: boolean;
  auto_approve_ready: boolean;
}

// ---------------------------------------------------------------------------
// RAG & Ingestion Schemas
// ---------------------------------------------------------------------------
export interface SKUMatchCandidate {
  sku: string;
  name: string;
  confidence_score: number;
  match_tier: "EXACT_HASH" | "LEXICAL_FUZZY" | "SEMANTIC_VECTOR" | "LLM_FALLBACK";
  is_active: boolean;
  unit_price: number;
  stock: number;
}

export interface SKUMatchResult {
  raw_query: string;
  matched_sku?: string | null;
  name?: string | null;
  unit_price?: number | null;
  stock?: number | null;
  active?: boolean;
  confidence_score: number;
  tier_used: string;
  is_confident: boolean;
  candidates: SKUMatchCandidate[];
  explanation: string;
}

export interface BotConfigStatus {
  telegram_enabled: boolean;
  telegram_chat_id?: string | null;
  zalo_enabled: boolean;
  webhook_url: string;
}


export interface MathVerificationResult {
  is_valid: boolean;
  calculated_items_total: number;
  declared_subtotal: number;
  difference: number;
  discrepancy_detected: boolean;
  message: string;
}

export interface ExtractedOrder {
  header: {
    po_number: string;
    customer: string;
    order_date?: string | null;
    currency: string;
    subtotal: number;
    tax_amount: number;
    grand_total: number;
    notes?: string | null;
  };
  items: Array<{
    sku: string;
    description: string;
    quantity: number;
    unit_price: number;
    amount: number;
  }>;
  raw_text?: string | null;
  confidence_score: number;
  extractor_used: "DETERMINISTIC_PARSER" | "GEMINI_FLASH_VISION" | "HYBRID_FALLBACK";
  document_type: string;
  math_verification: MathVerificationResult;
}

// ---------------------------------------------------------------------------
// LangGraph Stateful Workflow Schemas
// ---------------------------------------------------------------------------
export interface AgentRunRequest {
  po_number: string;
  customer: string;
  line_items: Array<{
    sku: string;
    quantity: number;
    unit_price: number;
  }>;
  thread_id?: string | null;
}

export interface AgentRunResponse {
  thread_id: string;
  status: OrderStatus;
  risk_level: RiskLevel;
  findings_count: number;
  findings: Finding[];
  matched_skus: Record<string, unknown>;
  is_interrupted: boolean;
  waiting_for_nodes: string[];
  erp_synced: boolean;
  erp_tx_id?: string | null;
  audit_trail: string[];
}

export interface IngestionJobStatus {
  job_id: string;
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
  extracted_order?: ExtractedOrder | null;
  error?: string | null;
}

// ---------------------------------------------------------------------------
// ERP & Outbox Schemas
// ---------------------------------------------------------------------------
export type ERPAdapterType =
  | "MOCK_SAP"
  | "SAP_S4HANA_MOCK"
  | "MOCK_ODOO"
  | "ODOO_LIVE"
  | "SAP_ODATA_LIVE"
  | "MISA_AMIS_LIVE";

export interface ERPSyncResponse {
  success: boolean;
  transaction_id?: string | null;
  adapter_type: ERPAdapterType;
  idempotency_key: string;
  timestamp: number;
  error_message?: string | null;
}

export interface OutboxStats {
  pending_count: number;
  processing_count: number;
  sent_count: number;
  failed_count: number;
  total_events: number;
}

// ---------------------------------------------------------------------------
// Enterprise B2B Contracts & Risk Master Schemas
// ---------------------------------------------------------------------------
export interface CustomerPriceAgreement {
  customer_id: string;
  sku: string;
  contract_price: number;
  min_quantity: number;
  discount_percent: number;
  valid_from?: string | null;
  valid_to?: string | null;
}

export interface CustomerCreditProfile {
  customer_id: string;
  credit_limit: number;
  outstanding_balance: number;
  overdue_balance: number;
  oldest_overdue_days: number;
  status: "ACTIVE" | "ON_HOLD" | "BLOCKED";
}

export interface UOMConversion {
  sku: string;
  uom_code: string;
  base_uom: string;
  conversion_factor: number;
}

export interface CustomerMaster {
  id?: number | null;
  code: string;
  name: string;
  normalized_name?: string;
  tax_code?: string | null;
  tier?: "VIP" | "PLATINUM" | "GOLD" | "STANDARD" | string;
  aliases?: string[];
  created_at?: string | null;
}

export interface UserAccount {
  id?: number | null;
  org_id?: string;
  username: string;
  display_name: string;
  email: string;
  role: "viewer" | "auditor" | "sales_admin" | "manager" | "director" | "admin" | string;
  is_active: boolean;
  failed_attempts?: number;
  locked_until?: string | null;
  created_at?: string;
}

export interface CreateUserPayload {
  username: string;
  display_name: string;
  email: string;
  password: string;
  role?: string;
  org_id?: string;
}

export interface UpdateUserPayload {
  display_name?: string;
  email?: string;
  role?: string;
  is_active?: boolean;
}

