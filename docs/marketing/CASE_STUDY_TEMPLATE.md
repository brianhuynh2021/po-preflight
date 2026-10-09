# REAL-WORLD DEPLOYMENT CASE STUDY TEMPLATE — PO PREFLIGHT

> **A representative case study document for the B2B Sales & Marketing team.**  
> Data and metrics are standardized from the results of the 30-day Pilot program (Telemetry KPIs per Prompt C7).

---

## 🏢 PILOT CLIENT OVERVIEW

- **Business name:** Công ty Cổ phần Phân phối Thiết bị & Vật tư Kỹ thuật Miền Bắc (Northern Technical Equipment & Supplies Distribution Joint Stock Company) (sample pilot customer).
- **Industry:** Master distribution warehouse for networking equipment, telecom cabling, and IT infrastructure solutions, serving 180 tier-2 dealers and construction projects.
- **Processing volume:** An average of 1,200 - 1,600 purchase orders (POs) per month from multiple channels: Email (PDF, Excel invoices) and Zalo photos from provincial dealers.
- **Software in use:** MISA AMIS accounting and an in-house warehouse management system.

---

## 🚨 BACKGROUND & CHALLENGES BEFORE DEPLOYMENT

Before adopting **PO Preflight**, the company's order processing relied 100% on people, with serious bottlenecks:

1. **Long processing times causing overload:**
   - Each PO has between 5 and 35 line items. A Sales Admin spent an average of **25 minutes per order** opening the file, looking up SKU codes in the catalog, opening contracts to check each dealer's individual pricing policy, checking inventory, and keying the order into MISA AMIS by hand.
   - During weekend or holiday peaks, the intake mailbox piled up with hundreds of POs, delaying deliveries by 1 - 2 days.
2. **Pricing errors and receivables disputes:**
   - Dealers often use colloquial names and abbreviations (for example, writing *"dây mạng 3m bấm sẵn"* (3m pre-terminated network cable) instead of the standard code `CAB-CAT6-3M`). New staff frequently picked the wrong product type or applied the wrong wholesale unit price.
   - Every month the company recorded 12 - 18 cases requiring the cancellation or adjustment of e-invoices because of wrong prices or wrong tiered discounts.
3. **Loss of control over credit limits:**
   - Many dealers had debts overdue by more than 30 days or had already hit their credit ceiling, yet their orders were still inadvertently created by staff and sent on for warehouse release, creating a major risk of tied-up capital.

---

## 💡 THE PO PREFLIGHT SOLUTION

The company deployed **PO Preflight** for 30 days as an independent intermediary pre-control gateway placed in front of MISA AMIS:

- **Template-independent multi-channel extraction:** Automatically ingests attachments from Email and the upload folder and accurately extracts every line item, with **automatic arithmetic reconciliation (Math Verifier)**.
- **4-Tier SKU Matcher (4-Tier RAG):** Automatically recognizes local names and abbreviations and maps them precisely to internal warehouse codes without editing the catalog table.
- **Real-time B2B rules engine:** Instantly checks 3 factors: the signed contract price, available-to-promise (ATP) stock, and the dealer's receivables status.
- **One-tap approval on Telegram & Zalo OA:** Orders found in violation are sent as alert cards directly to the Chief Operating Officer, who can approve or reject right on a mobile phone.
- **Transactional ERP Outbox:** Only validly approved orders are safely recorded into MISA AMIS, each with a unique transaction ID.

---

## 📊 MEASURED RESULTS AFTER THE 30-DAY PILOT

*(Figures extracted directly from the `/reports` Telemetry Operations Report and the reconciliation file `po_preflight_pilot_report.csv`)*

| Metric (KPI) | Before Preflight | After Preflight | Improvement |
|---|---|---|---|
| **Preflight time per order** | 25 minutes / order | **2.1 seconds (Extraction)** + < 2 minutes (Approval) | ⚡ **92% faster** |
| **Total working hours saved** | 0 hours | **575 working hours / month** | ⏱️ **Equivalent to 3 full-time staff** |
| **Automatic standardization rate** | 0% (100% manual entry) | **96.4%** clean orders | 🎯 **Eliminates typing errors** |
| **Pricing errors & bad debts blocked before the ERP** | 15 incidents slipping into the warehouse/month | **48 risky orders stopped** | 🛡️ **Protects VND 140+ million** |
| **Duplicate order rate** | 3 - 5 orders shipped in duplicate/quarter | **100% detected & prevented** | 🚫 **0 duplicate shipments** |
| **AI technology operating cost** | — | **$0.27 USD / 1,500 orders** (~6,800 VND) | 💰 **Near-zero cost** |

---

## 🗣️ TESTIMONIALS FROM THE TEAM ON THE GROUND

> *"In the past, the accounting department's biggest fear was a dealer disputing a unit price after the e-invoice had been issued and the goods delivered. Preparing adjustment records and explaining them to the tax authorities was exhausting. Since PO Preflight became our gatekeeper, 100% of orders entering MISA AMIS match the contract price list to the last dong, and we are assured that customers no longer carry bad debt. The SHA-256 hash chain gives us complete confidence during internal audits."*  
> **— Ms. Nguyễn Thị Mai, Chief Accountant**

> *"The Sales Admin team's workload has dropped noticeably. We no longer have to keep 4 screens open at once to track down each cable code or add up VAT on a calculator. The Vietnamese-language interface is very easy to use, and when a customer writes an unfamiliar abbreviation, the system automatically suggests the standard code along with a confidence level. We now have more time to look after customers instead of just keeping our heads down entering data."*  
> **— Ms. Lê Thu Trang, Sales Admin Team Lead**

> *"As an executive, I often travel to the provinces. In the past, every time I wanted to urgently approve an order for a regular customer, staff had to call me or send screenshots over Zalo, which was very fragmented. Now I just open Telegram or the mobile approval screen on my phone, see clearly where the warning is, and approve with one tap along with an explanatory note. Every decision is transparent and instant."*  
> **— Mr. Trần Đình Khang, Chief Operating Officer (COO)**

---

## 🎯 LESSONS LEARNED & SCALE-UP PLAN

1. **Master Data standardization is the key factor:** Preparing a clean SKU catalog and updating contract price lists from Week 1 let the automatic match rate exceed 95% from the very first day of operation.
2. **Signing the formal commercial contract:** After successfully accepting the 30-day Pilot program, the company formally signed an annual service contract for the **Growth ERP** package and is planning to extend connectivity to its southern branch.

---
*Document copyright belongs to the Enterprise Customer Division — Nhật Minh Technology.*
