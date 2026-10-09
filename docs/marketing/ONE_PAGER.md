# PO PREFLIGHT — ONE-PAGER: B2B ORDER AUTOMATION & CONTROL SOLUTION

---

## 1. THE REAL PAIN POINTS OF B2B DISTRIBUTION & WHOLESALE BUSINESSES

At distribution, manufacturing, and wholesale companies in Vietnam, Sales Admin teams (CS/data entry) spend **30 - 45 minutes on every order**, and the business faces 4 major risks:

1. **Many formats, exhausting manual processing:** POs arrive via Zalo and Email in every form: blurry scanned PDFs, custom Excel forms, flat CSV tables, photos taken on a phone. Manual entry is both slow and prone to missed lines.
2. **SKU errors & local product names:** Customers use abbreviations (*"dây mạng 3m bấm sẵn"* (3m pre-terminated network cable), *"màn 27 inch 4k"* (27-inch 4K monitor), outdated codes that have since been replaced). Looking up price lists takes tens of minutes, and a mistyped code leads to the wrong goods being shipped and contract penalties.
3. **Contract price deviations & receivables leakage:** There is no time to cross-check prices against the master agreement and the customer's credit limit, leading to selling below the floor price or extending credit beyond the ceiling.
4. **Garbage-In, Garbage-Out ERP:** Entering wrong orders directly into SAP / Odoo / MISA creates waves of adjustment documents (Credit/Debit Notes), and accounting and the warehouse are in constant conflict.

---

## 2. THE SOLUTION: PO PREFLIGHT — AN AUTOMATED B2B ORDER CONTROL ASSISTANT

**PO Preflight** is an intelligent intermediary control gateway (B2B Pre-ERP Control Gateway) that automates 100% of the process from receiving the PO file to pushing a clean order into the ERP:

- 📑 **Ultra-accurate multi-format extraction:** Instantly reads scanned PDFs, images, Excel forms, or flat tables, with a self-auditing arithmetic mechanism (Self-Reflection Math Verifier) that eliminates hallucination 100%.
- 🧠 **4-tier RAG that decodes Vietnamese-native SKUs:** Finds the right ERP code in 15ms across 4 tiers (Exact $\rightarrow$ Fuzzy $\rightarrow$ Vietnamese semantic Vector $\rightarrow$ LLM Context), automatically recognizing industry slang.
- 🛡️ **Real-time business rules engine:** Automatic 3-way checks: per-customer price list (B2B Price Agreement), credit limit & overdue debt (Credit Profile), and safety stock & UoM conversion (Case $\leftrightarrow$ Piece).
- 📱 **One-tap approval on Telegram & Zalo:** Department heads approve exceptions right on their phones while traveling, without opening a computer or logging into a cumbersome ERP.
- ⚡ **ACID-compliant ERP sync with Transactional Outbox:** Once approved, a Sales Order is created automatically in SAP S/4HANA, Odoo, or MISA AMIS, with a hash-based attestation (SHA-256 Audit Certificate).

---

## 3. HOW IT WORKS (A CLOSED-LOOP 4-STEP WORKFLOW)

```
[1. Receive PO] ──▶ [2. Analyze & Match] ──▶ [3. Control & Approve] ──▶ [4. ERP Sync]
(PDF, Excel,        (OCR + 4-Tier RAG        (Check Price, Stock,      (Create Sales Order SAP/
 Zalo/Email)         hallucination-proof)     Receivables + Mobile HITL) Odoo/MISA + Audit Log)
```

1. **Intake & Extraction (3s):** Staff drag and drop a PO or receive it automatically via Zalo/Email Webhook. The system standardizes the information immediately.
2. **Matching & Risk Assessment (5s):** Risk is classified into 3 levels: `Ready` (Meets standards), `Review required` (Needs review), `Blocked` (Blocked due to bad debt / out of stock).
3. **Human-controlled approval (Human-In-The-Loop):** Managers review the original file and the extracted data side by side (Side-by-Side) and approve quickly via Telegram/Zalo.
4. **Pushing clean orders into the ERP (2s):** The Transactional Outbox automatically creates the order in the ERP and writes to a tamper-proof compliance journal that cannot be edited or deleted.

---

## 4. MEASURABLE RESULTS RIGHT AWAY (ROI)

| Metric | Before PO Preflight | After PO Preflight | Improvement |
| :--- | :--- | :--- | :--- |
| **Order processing time** | 30 - 45 minutes / order | **1 - 2 minutes / order** | **95% reduction** |
| **SKU/Price error rate** | 3 - 5% of total orders | **< 0.1%** | **98% reduction** |
| **Admin staffing cost** | 3 - 5 CS/data-entry staff | 1 staff member handling exceptions | **Saves ~VND 300 million/year** |
| **Go-Live time** | ERP customization takes 3 - 6 months | **Plug-and-play in 3 days** | **30x faster** |

---

## 5. PILOT PROGRAM & EXCLUSIVE OFFERS FOR THE FIRST 10 BUSINESSES

Reserved exclusively for the **first 10 B2B Distribution / Wholesale Businesses**:

- 🎁 **100% free initial survey & integration costs** (valued at VND 25,000,000).
- 🎁 **30 days of full-feature trial (Full-feature Pilot)** with 1,000 of your business's real orders.
- 🎁 **RAG training to recognize your business's own keyword set / SKUs** with accuracy >98%.
- 🛡️ **Risk-free commitment:** No modification of the Core ERP, and data is stored entirely on the business's own servers (On-premise / Private Cloud).

**Contact us to register for the Pilot today:**  
- **Website:** https://po-preflight.vn  
- **Hotline / Zalo:** 09xx-xxx-xxx  
- **Email:** pilot@po-preflight.vn
