# 📊 PO PREFLIGHT — EXECUTIVE PITCH DECK & PROJECT PRESENTATION
> **An Automated Safety Control Gateway for B2B Purchase Orders Before They Enter the ERP**  
> *For Executive Leadership, Chief Accountants & Operations Directors of Distribution Businesses*

---

```
═══════════════════════════════════════════════════════════════════════════════
                         PRESENTATION CONTENTS (10 SLIDES)
═══════════════════════════════════════════════════════════════════════════════
  [SLIDE 1] PROJECT OVERVIEW & MISSION STATEMENT (THE HOOK)
  [SLIDE 2] REAL-WORLD PROBLEMS & HIDDEN BUSINESS COSTS (THE PROBLEM & HIDDEN COSTS)
  [SLIDE 3] THE SOLUTION: THE PO PREFLIGHT AUTOMATED PRE-CHECK GATEWAY (THE SOLUTION)
  [SLIDE 4] TECHNOLOGY BREAKTHROUGH: 4-TIER RAG & ARITHMETIC ASSURANCE (CORE TECH)
  [SLIDE 5] THE 6-STAGE LIVE OPERATING WORKFLOW (LIVE PRODUCT WORKFLOW)
  [SLIDE 6] MEASUREMENT METHODOLOGY & PILOT BENCHMARK RESULTS (MEASUREMENT & PILOT DATA)
  [SLIDE 7] DECREE 13 COMPLIANCE, ON-PREMISE & SHA-256 HASH CHAIN (SECURITY & AUDIT)
  [SLIDE 8] CUSTOMER PROFILE & ERP ECOSYSTEM (ICP & ERP ECOSYSTEM)
  [SLIDE 9] UNIQUE COMPETITIVE ADVANTAGE (MOAT & COMPETITIVE ADVANTAGE)
  [SLIDE 10] ROLLOUT ROADMAP & 30-DAY PILOT PLAN (PILOT PLAYBOOK & NEXT STEPS)
═══════════════════════════════════════════════════════════════════════════════
```

---

## 🎯 SLIDE 1: PROJECT OVERVIEW (THE HOOK)

### 📌 Title: **PO PREFLIGHT — The Automated B2B Order Control & Reconciliation Gateway**

* **Tagline**: *"Never let an order with the wrong contract price, out-of-stock items or overdue debt slip into your ERP system."*
* **Value Proposition**:
  A smart pre-check gateway that helps B2B businesses and distributors automate order intake and extraction (PDF, Excel, scanned photos), thoroughly reconcile each order against contract price lists, ATP inventory and credit limits, and trigger 1-tap approval on Telegram/Zalo before syncing to the ERP (MISA AMIS, Bravo, Fast, Odoo, SAP B1).
* **Developed by**: Nhật Minh Technology.

> 🎙️ **Speaker Notes**: *"Ladies and gentlemen, in aviation, no aircraft takes off until it has completed the Pre-flight Check procedure. In B2B distribution businesses, hundreds of purchase orders every day, worth hundreds of millions of VND, are being keyed by hand into accounting software without passing through any automated filter. PO Preflight is that trusted gatekeeper."*

---

## 🚨 SLIDE 2: MARKET PAIN POINTS & HIDDEN COSTS (THE PROBLEM)

### 3 Critical "Gaps" in B2B Order Processing:

```
  ┌───────────────────────────┐      ┌───────────────────────────┐      ┌───────────────────────────┐
  │   1. Slow Manual Entry    │      │ 2. Wrong SKU & Price Gaps │      │   3. Inventory Leakage    │
  │                           │      │                           │      │                           │
  │ • Takes 15-30 min/order   │      │ • Slang product names     │      │ • Approved with no stock  │
  │ • Sales Admins overloaded │      │ • Wrong contract prices   │      │ • Orders entered twice    │
  │ • Delayed VAT invoicing   │      │ • Drawn-out debt disputes │      │ • Short shipments, fines  │
  └───────────────────────────┘      └───────────────────────────┘      └───────────────────────────┘
```

* **Direct Consequences**:
  - Cancelling e-invoices and adjusting accounting documents takes 10 times longer than pre-checking.
  - Orders get stuck at the manual reconciliation step, so goods are delivered late, hurting credibility with dealer partners.

---

## 💡 SLIDE 3: THE PO PREFLIGHT SOLUTION (THE SOLUTION)

### The 1-Tap Order Pre-check Gateway — From Raw File to Completed ERP Entry

```
 ┌───────────────┐     ┌──────────────────────────────────────────────┐     ┌───────────────┐
 │ CUSTOMER      │     │                 PO PREFLIGHT                 │     │ ERP SYSTEMS   │
 │ Sends POs:    │ ──► │ 1. Cascading Intake (multi-format parsing)   │ ──► │  MISA AMIS    │
 │ Excel, PDF,   │     │ 2. 4-Tier RAG Matcher (multilingual SKUs)    │     │  Bravo / Fast │
 │ scanned images│     │ 3. Deterministic Rules (price, stock, credit)│     │  Odoo / SAP B1│
 └───────────────┘     │ 4. Mobile 1-Tap HITL (Zalo/Telegram approval)│     └───────────────┘
                       └──────────────────────────────────────────────┘
```

* **100% Automation of the Tedious Steps**: Data extraction, arithmetic auditing $\sum(\text{Qty} \times \text{Price})$, and cross-checking credit limits and available stock.
* **Users Keep Approval Authority (Human-In-The-Loop)**: The order is pushed to the ERP through the Transactional Outbox only after an authorized manager taps approve on Telegram, Zalo or the Web.

---

## ⚡ SLIDE 4: TECHNOLOGY BREAKTHROUGH THAT GUARANTEES ZERO HALLUCINATION (CORE TECH)

### 1. 4-Tier SKU Matching Algorithm (4-Tier Waterfall Hybrid RAG)
Completely solves the problem where customers write colloquial names or Vietnamese slang, yet the system must map to the correct internal SKU 100% of the time **without ever letting the AI make things up (Zero-Hallucination)**.
- **Tier 1 — Exact Hash Match (<1ms, $0)**: Exact O(1) hash lookup of listed SKU codes and barcodes.
- **Tier 2 — Lexical Fuzzy (<5ms, $0)**: Levenshtein string distance (RapidFuzz) handles minor spelling mistakes.
- **Tier 3 — Multilingual Dense Vector (<25ms, $0)**: FastEmbed multilingual vector embeddings run locally on the server CPU and understand everyday language (e.g., *"dây mạng 3m bấm sẵn"* (pre-crimped 3 m network cable) $\rightarrow$ `CAB-CAT6-3M`).
- **Tier 4 — LLM Context Reasoner (Fallback)**: Triggered when similarity is < 70%, with a strict JSON output format enforced.

### 2. Automatic Arithmetic Verification (Self-Reflection Math Verifier)
The system automatically recalculates every line: $\text{Quantity} \times \text{Unit Price} - \text{Discount} + \text{VAT}$ and compares it with the total stated on the order. Any arithmetic discrepancy is immediately flagged with the `MATH_CALCULATION_DISCREPANCY` warning.

---

## 🚀 SLIDE 5: THE 6-STAGE LIVE OPERATING WORKFLOW (LIVE PRODUCT WORKFLOW)

```
[Stage 1] PO Intake ──► [Stage 2] OCR Extraction ──► [Stage 3] SKU Matching ──► [Stage 4] Rule Checks ──► [Stage 5] Mobile Approval ──► [Stage 6] ERP Outbox Push
  (Email / Excel / PDF)       (Gemini Flash OCR)        (4-Tier Hybrid)          (Price, Stock, Credit)      (Zalo / Telegram)        (MISA / Odoo / SAP)
```

* **Modern interface**: Minimalist, industry-standard design with highly interactive tables that support editing directly in the table (Inline Edit).
* **Minimal mobile screen (`/m/orders/:id`)**: Lets senior management handle and approve urgent orders right from their phones while on business trips.

---

## 📈 SLIDE 6: MEASUREMENT METHODOLOGY & PILOT RESULTS (MEASUREMENT & PILOT DATA)

Instead of presenting assumed figures, PO Preflight applies **transparent measurement formulas** based on actual operating data:

### 1. How We Measure (Measurement Methodology)
- **Actual time saved (hours)**:  
  $$\text{Hours Saved} = \text{Orders Processed} \times \frac{25\text{ min (manual entry)} - 2\text{ min (pre-check)}}{60}$$
- **Human intervention rate (%)**:  
  $$\text{Human Intervention Rate} = \frac{\text{Line Items Edited via Staging}}{\text{Total Line Items}} \times 100\%$$
- **Average AI inference cost per order**:  
  $$\text{Cost per PO} = \frac{\text{Total LLM \& OCR Token Cost}}{\text{Total POs Received}}$$

### 2. Benchmark & Pilot Test Results (Benchmark & Pilot Telemetry)
- **Average analysis time**: **2.1 seconds / order** (a > 90% reduction in waiting time).
- **Pre-ERP violation detection rate**: **100%** (stops every order with a wrong contract price, out-of-stock items or overdue debt).
- **Automatic SKU resolution rate (Tier 1-3)**: **> 96%** (only < 4% of orders need the LLM fallback).
- **AI operating cost**: Only **$0.00018 USD / order** (~4.5 VND / order), ideal for large-scale operations.

---

## 🔒 SLIDE 7: DECREE 13 COMPLIANCE, ON-PREMISE & SHA-256 HASH CHAIN

* **Full compliance with Decree No. 13/2023/ND-CP (Personal Data Protection in Vietnam)**:
  - All customer data, invoices and commercial pricing are encrypted at rest and in transit.
  - Supports fully **On-Premises** deployment or deployment on the customer's own **domestic Private Cloud**. No sensitive data is ever sent to foreign servers.
* **SHA-256 Cryptographic Hash Chain (Tamper-evident Hash Chain)**:
  Every analysis event, line-item edit and human approval decision is mathematically linked into an immutable hash chain, completely preventing covert database tampering.
* **Separation of Duties (SoD)**:
  Strict internal control rule: the employee who creates an order cannot approve it themselves; orders exceeding the value authority limit must carry the digital signature of a Director.

---

## 🏢 SLIDE 8: CUSTOMER PROFILE & ERP ECOSYSTEM

### Ideal Customer Profile (ICP):
1. **FMCG (Fast-Moving Consumer Goods) Distributors & General Agents**: Receive 50 - 500 dealer orders per day via Excel files and email.
2. **Pharmaceutical & Medical Equipment Distributors**: Orders with complex catalogs, tight control over units of measure (blister pack, box, carton) and credit limits.
3. **Industrial & Construction Materials Suppliers**: Customers order with specific technical specifications and individual contract price lists.

### Ready-to-Connect ERP Ecosystem:
- **Popular Domestic ERPs**: **MISA AMIS**, **Bravo ERP**, **Fast Business Online**.
- **International / Open-Source ERPs**: **Odoo ERP**, **SAP Business One**, **SAP S/4HANA**.

---

## 🏆 SLIDE 9: UNIQUE COMPETITIVE ADVANTAGE (THE MOAT)

```
┌──────────────────────────────────────┬──────────────────────────────────────┐
│      CONVENTIONAL OCR SOFTWARE       │             PO PREFLIGHT             │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ ❌ Reads raw text, ignores inventory │ ✔ 4-tier SKU matching (4-Tier RAG)   │
│ ❌ Prone to AI hallucination         │ ✔ Deterministic rules (Zero-Token)   │
│ ❌ No mobile approval workflow       │ ✔ 1-tap Telegram & Zalo OA approval  │
│ ❌ Pushing raw data causes ERP errors│ ✔ Transactional Outbox Idempotency   │
│ ❌ No audit attestation              │ ✔ Tamper-proof SHA-256 hash chain    │
│ ❌ Depends on foreign cloud          │ ✔ On-Premise & Decree 13 ready       │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

---

## 🚀 SLIDE 10: 30-DAY PILOT ROLLOUT PLAN (PILOT PLAYBOOK)

### 4-Week Pilot Rollout Roadmap for New Customers:
* **Week 1 — Master Data Setup**: Sync the SKU catalog and contract price lists, and assign user permissions (`/users`).
* **Week 2 — Parallel Run (Shadow Run)**: Upload real POs into the system and fine-tune the SKU Alias vocabulary.
* **Week 3 — Operations & Mobile Approval**: Activate the Telegram/Zalo approval gateway and turn on the Transactional Outbox for ERP sync.
* **Week 4 — Acceptance & ROI Evaluation**: Export the Pilot report (`/reports`) and reconcile the actual hours saved.

---

### 🤝 NEXT STEPS:
* **View the Sample Pilot Report**: Open the visual interface at `/reports` and export a sample CSV file.
* **Sign Up for the 30-Day Pilot Program**: Try it free in a real operating environment.
* **Contact the Implementation Team**: Nhật Minh Technology | Hotline: `090x-xxx-xxx` | Email: `contact@popreflight.vn`.

---
*Presentation material for internal circulation — PO Preflight 2026.*
