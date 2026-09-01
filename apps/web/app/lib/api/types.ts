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
  | "extraction_review";

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

export interface DashboardStats {
  total_orders: number;
  ready_count: number;
  review_required_count: number;
  blocked_count: number;
  approved_count: number;
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
  unit_price: number;
  stock: number;
  active: boolean;
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
  query_sku: string;
  matched_sku?: string | null;
  name?: string | null;
  confidence_score: number;
  tier_used: string;
  is_confident: boolean;
  candidates: SKUMatchCandidate[];
  explanation: string;
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

// ---------------------------------------------------------------------------
// ERP & Outbox Schemas
// ---------------------------------------------------------------------------
export interface ERPSyncResponse {
  success: boolean;
  transaction_id?: string | null;
  adapter_type: "MOCK_SAP" | "MOCK_ODOO";
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
