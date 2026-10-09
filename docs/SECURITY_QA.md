# SECURITY & TECHNICAL Q&A — PO PREFLIGHT

> **Audience:** Chief Accountants, IT Directors (CIO/CTO), Heads of Internal Control and Information Security Specialists.  
> **Purpose:** Honest, transparent answers to the 20 key questions on security, confidentiality, data integrity and ERP connectivity of the **PO Preflight** system.

---

## 🔒 GROUP 1: SECURITY, PRIVACY & LEGAL COMPLIANCE (DECREE 13 & ON-PREMISE)

### Question 1: Are our orders, customer information and price lists sent to overseas servers (OpenAI/Google Cloud)?
**Honest answer:**  
**No.** PO Preflight is designed around a local-first processing principle:
- All B2B business-rule reconciliation (contract prices, ATP stock, credit limits, packaging specifications) runs on deterministic Python code (Deterministic Zero-Token) on an internal server.
- The multilingual SKU semantic search (Tier 3 Semantic Vector) uses the `FastEmbed` library with the local embedding model `paraphrase-multilingual-MiniLM-L12-v2`, which runs directly on the server's CPU and calls no external API.
- Only when a document is a low-quality scanned image that requires OCR, or a product name is too complex (Tier 4 LLM fallback, accounting for < 4% of orders), does the system send an anonymized text excerpt to the Gemini API under an Enterprise agreement with no retention of training data (Zero Data Retention). For the Enterprise On-Premise plan, the entire OCR model is replaced by an internal engine, ensuring that 100% of the data never leaves the LAN.

### Question 2: How does the system comply with Decree 13/2023/ND-CP on Personal Data Protection in Vietnam?
**Honest answer:**  
The system strictly complies with the provisions of Decree 13/2023/ND-CP:
1. **Data classification and minimization (Data Minimization):** The system extracts only the data fields needed for a commercial purchase order (company name, tax code, delivery address, SKU code, unit price, quantity). No unrelated sensitive information is stored.
2. **Role-based access control (RBAC):** Order data is shown only to users with an assigned authority (`SALES_ADMIN`, `MANAGER`, `DIRECTOR`, `AUDITOR`).
3. **Right to be forgotten & anonymization:** Supports a process for anonymizing personally identifiable information (PII Scrubber) once an order's retention period under accounting law has expired.

### Question 3: Can our company deploy the solution entirely On-Premises on our own servers?
**Honest answer:**  
**Yes.** PO Preflight is fully packaged as Docker Compose or a Kubernetes Helm Chart for standalone deployment inside an internal network (On-Premises) or a Private Cloud (Viettel IDC, VNPT, FPT Cloud):
- Supports a lightweight SQLite database (WAL mode) for Edge deployment, or a PostgreSQL cluster for heavy workloads.
- No continuous Internet connection is required, except when you want notifications via Telegram/Zalo Bot (which can be replaced by an internal Webhook or internal Email).

### Question 4: What algorithms encrypt order data at rest (At-Rest) and in transit (In-Transit)?
**Honest answer:**  
- **In transit (In-Transit):** All communication between browsers, mobile apps and the API Gateway must go through **TLS 1.3** with a strong cipher suite (ECDHE-RSA-AES128-GCM-SHA256).
- **At rest (At-Rest):** The database and attachments are encrypted at the storage level with **AES-256**. User passwords are one-way hashed with **Argon2id**, currently the most advanced crack-resistant algorithm, together with a random salt (Salt).

### Question 5: Does the software vendor still have access to our orders after handover?
**Honest answer:**  
**Absolutely not.** In the On-Premise or Dedicated Cloud model handed over to the customer:
- All credentials for the highest-level administrator account (`admin`) are held by the customer, who can change the password immediately after handover.
- The JWT secret key (`SECRET_KEY`) and the database connection string live in environment variables on the customer's server. Our engineering team accesses the system for support only with written consent and under live supervision through a secure session (SSH/AnyDesk with recording).

---

## 📜 GROUP 2: DATA INTEGRITY & ACCOUNTING AUDIT (AUDIT TRAIL & SOD)

### Question 6: How does the SHA-256 hash chain (Cryptographic Hash Chain) prove that data has not been secretly altered?
**Honest answer:**  
Each time an important event occurs (order intake, line-item extraction, a manager's approval decision, an export command to the ERP), the system computes a hash value using the formula:
$$\text{Block\_Hash}_n = \text{SHA256}(\text{Block\_Hash}_{n-1} + \text{Timestamp} + \text{Actor\_ID} + \text{Payload\_Content})$$
Each data block is tightly chained to the block immediately before it. This creates an immutable cryptographic certificate chain: any secret edit to the content of any past order will invalidate the hashes of all subsequent blocks and is detected immediately when the system runs its integrity scan (`verify_chain`).

### Question 7: If an internal IT administrator tampers directly with the SQL database to change an amount, how does the system detect it?
**Honest answer:**  
When an auditor or chief accountant opens the **Audit Log Certificate** page (`/audit-certificate`, or calls the API `GET /api/v1/audit/verify`), the system walks sequentially from the first block to the newest block:
- If someone runs a command such as `UPDATE analyses SET total = ...` directly in SQL, the SHA-256 hash of that block will no longer match the actual data.
- The system immediately raises a red alert: `"Data was tampered with without authorization at block #ID!"` and points to the exact data row that was modified.

### Question 8: How does the Separation of Duties (SoD) mechanism prevent internal fraud?
**Honest answer:**  
The system enforces strict SoD rules at the API layer (`src/preflight/security/rbac.py`):
- **Rule 1 (Self-approval):** The employee who creates an order (`sales_admin`) can never approve an order they created themselves (`403 Forbidden: Creator cannot approve their own submission`).
- **Rule 2 (Approval authority limits):** Orders worth less than 50 million VND are approved by a `MANAGER`. Orders of 50 million VND or more, or with a bad-debt exception, must be approved at the `DIRECTOR` level.
- **Rule 3 (Blocked orders):** An order classified as `Blocked` (a serious violation) is hard-locked; no role can approve it directly until its line items have been properly corrected in Staging.

### Question 9: Can a Sales Admin employee "bypass" the system to approve orders for a familiar dealer?
**Honest answer:**  
**No.** Every approval action must go through the API gateway `/api/v1/orders/{id}/decide`. This gateway checks the login session and the RBAC role, and records the approver's identity into the SHA-256 hash chain. If the account lacks sufficient authority, the system returns a `403 Forbidden` error and writes a security log entry.

### Question 10: How can a chief accountant or an independent auditor export an explanation file for a specific order?
**Honest answer:**  
At any time, the accountant can:
1. Open the order details in the Web Portal and click the **"Export Audit Certificate"** button.
2. Download the digital certificate containing the entire history from the original PO file, the extraction snapshot, the list of violation warnings, and the approver's identity with a SHA-256 hash signature.
3. Or download the consolidated reconciliation file `po_preflight_pilot_report.csv` from the `/reports` page for tax audit purposes.

---

## ⚙️ GROUP 3: ERP INTEGRATION & OPERATIONAL RELIABILITY (INTEGRATION & RELIABILITY)

### Question 11: If the Internet connection or the ERP server (MISA/Odoo/SAP) drops suddenly, will orders be lost?
**Honest answer:**  
**Never.** PO Preflight uses the enterprise-standard architectural pattern **Transactional Outbox Pattern**:
- When an order is approved, a goods-issue event is saved to the `erp_outbox` table within the same local database transaction, with the status `PENDING`.
- A background process periodically scans the queue and sends events to the ERP. If the ERP is temporarily unreachable, the system triggers an automatic retry mechanism with exponential backoff (Exponential Backoff with Jitter) up to 5 times.
- The data stays safe on the Preflight system until it receives a successful transaction confirmation code from the ERP.

### Question 12: How do you guarantee that an order is never recorded twice in the ERP?
**Honest answer:**  
The system uses a **Distributed Lock & Duplicate-Prevention Key (Idempotency Key)** mechanism:
- Each ERP synchronization event carries a unique key generated from the order number and the approval cycle: `hash(po_number + approval_timestamp)`.
- If the ERP Adapter finds that this key has already been recorded in the `erp_sync_history` table, the system immediately returns the successful result of the earlier transaction without creating any new document.

### Question 13: Does the software interfere directly with the ERP's native database structure (for example by running SQL commands directly)?
**Honest answer:**  
**Absolutely not.** We follow the software-safety principle: never interfere directly (Direct DB Write) with the SQL tables of accounting software such as MISA AMIS, Bravo, Fast or SAP.
- Every interaction goes through the **official interface (OpenAPI / REST API / SDK)** provided by the ERP vendors and granted under separate permissions.
- This completely eliminates the risk of corrupting financial data, breaking foreign keys (Foreign Key) or violating the ERP vendor's warranty policy.

### Question 14: If a customer sends 2 duplicate emails with the same PO file within 5 minutes, how does the system handle it?
**Honest answer:**  
The preflight engine has 2 layers of duplicate blocking:
1. **Layer 1 (Exact PO Match):** If the PO number already exists in the database, the system automatically raises a critical-severity violation flag `DUPLICATE_PO` and moves the status to `Blocked`.
2. **Layer 2 (Fuzzy Duplicate):** If the order numbers differ but the customer, order date and total amount all match within 24 hours, the system raises a warning flag `POSSIBLE_DUPLICATE` so the manager takes note before clicking approve.

### Question 15: What is the average speed of extraction and rule reconciliation? Does it bottleneck when receiving orders in bulk?
**Honest answer:**  
- For Excel or JSON/CSV files: processing time is **0.5 to 2.1 seconds per order**.
- For scanned PDF files / invoice photos: extraction via Vision OCR takes **3 to 5 seconds per order**.
- The system supports asynchronous queue processing with Redis/Celery or a SQLite worker, and can process hundreds of orders in parallel without freezing or bottlenecking the user interface.

---

## 🧠 GROUP 4: ARTIFICIAL INTELLIGENCE & BUSINESS ACCURACY (RAG & ZERO-HALLUCINATION)

### Question 16: Does the AI ever "make up" a product code (Hallucination) when it meets an unfamiliar product name or a customer's misspelling?
**Honest answer:**  
**Never.** PO Preflight eliminates hallucination (Zero-Hallucination) with 2 control mechanisms:
1. **Closed-World Catalog Validation:** Whatever code the AI model suggests, the system must check whether that code exists in the business's Master Catalog. If it is not in the catalog, the product code is immediately flagged as `UNKNOWN_SKU`.
2. **Strict confidence threshold (Confidence Threshold):** If the matching confidence is below 70%, the system does not pick arbitrarily but moves to the `Review required` status and asks the Sales Admin employee to choose the standard code in the Staging interface with just 1 mouse click.

### Question 17: How does the 4-tier matcher (4-Tier RAG) handle Vietnamese slang or colloquial product names?
**Honest answer:**  
The system runs a 4-tier cascading mechanism:
- **Tier 1 (Exact Hash):** 100% match on the listed SKU code or Barcode (latency <1ms).
- **Tier 2 (Lexical Fuzzy):** Uses the `RapidFuzz` algorithm to catch letter typos, missing hyphens, and confusion between the digit 0 and the letter O (latency ~5ms).
- **Tier 3 (Semantic Vector):** Uses the multilingual `FastEmbed` model, which understands Vietnamese semantics (for example: a dealer writes *"dây mạng 3m bấm sẵn"* (pre-crimped 3 m network cable); vector search reconciles it and matches it to the standard code `CAB-CAT6-3M` with 100% confidence).
- **Tier 4 (LLM Reasoning):** Triggered when the tiers above fail, to read the context surrounding the line item.

### Question 18: How does the system detect VAT miscalculations or arithmetic errors on the customer's side?
**Honest answer:**  
The system integrates a **Self-Reflection Math Verifier** module:
- After extraction, the system recomputes: $\text{Line Total} = \text{Quantity} \times \text{Unit Price} - \text{Discount}$.
- It sums all lines, calculates VAT at the applicable rate (8% or 10%), and compares the result with the total payable amount that the customer wrote on the PO.
- If there is a discrepancy of even 1,000 VND, the system raises the warning `MATH_CALCULATION_DISCREPANCY`, helping the accountant catch the dealer's miscalculation immediately, before issuing the invoice.

### Question 19: If my company's contract pricing policy or tiered discounts change mid-month, how do I update them?
**Honest answer:**  
Very simple and instant:
- An administrator or the Head of Sales can upload a new price-list Excel file in **Settings → Contract Price Lists** (`/rules` or `/customers`).
- Or the system automatically synchronizes the price list from the ERP on a schedule.
- Immediately after the update, every order received from that point on is reconciled against the newly effective price list, with no need to restart the software.

### Question 20: What are the backup, disaster recovery (Disaster Recovery) and SLA commitment policies?
**Honest answer:**  
- **Automatic backup:** The database and original PO files are backed up automatically every day (Daily Snapshot) and stored distributed across 2 independent geographic regions.
- **Recovery objectives (RTO & RPO):**
  - Service recovery time (RTO): Under **30 minutes**.
  - Maximum data loss (RPO): Under **5 minutes**, thanks to the Write-Ahead Logging (WAL) mechanism.
- **Service commitment (SLA):** Guaranteed uptime of **99.5%** for the Standard (Growth) plan and **99.9%** for the Enterprise (Enterprise Dedicated) plan. The technical support team is available online 24/7 for critical-severity (P1) incidents.

---
*Issued by the Technology & Information Security Department — PO Preflight / Nhật Minh Technology.*
