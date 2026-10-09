# 60-SECOND DEMO VIDEO SCRIPT — PO PREFLIGHT (REAL DATA)

> **Format:** A real screen recording (Screencast) on a live system + voice-over narration + sound effects (the narration column below is the English script; the Vietnamese cut is `apps/web/public/demo/po_preflight_demo_60s_vi.mp4` with `subtitles_vi.vtt`)  
> **Script basis:** The real integration-tested business flow A7 / C6 / C7 (Real file extraction → Staging inline edit → SoD authorization → Telegram/Zalo mobile approval → Transactional ERP Outbox → Pilot report).

---

## 🎬 DETAILED STORYBOARD & TIMELINE

| Duration | Visuals & Real On-Screen Actions (Visual) | Voice-Over Script (Audio) | Sound & Notes |
| :---: | :--- | :--- | :--- |
| **00:00 - 00:09** *(9s)* | **Scene 1: The pain of manual reconciliation**<br>- Open the email inbox and Zalo messages carrying PO files photographed at a tilt and Excel files with misaligned columns.<br>- A Sales Admin opens multiple windows to manually reconcile each line against the price list and the ERP software. | *"Every day, distribution businesses receive hundreds of purchase orders via Email and Zalo: Excel files with misaligned columns, scanned images, misspelled product codes. A Sales Admin spends 25 minutes manually reviewing each order — one wrong price or one missed overdue debt, and the business suffers a major loss."* | Frantic keyboard typing, constant Zalo notification chimes. |
| **00:09 - 00:22** *(13s)* | **Scene 2: Intake & self-reflective arithmetic extraction**<br>- Switch to the PO Preflight `/orders` interface.<br>- Drag and drop the Excel file `PO-FPT-7788.xlsx` into the upload area.<br>- Within 2 seconds, the system completes extraction and the Staging table appears, with status automatically recalculating $\sum(\text{Qty} \times \text{Price})$ without a single dong of discrepancy. | *"Let **PO Preflight** do it in just 2 seconds. Drag and drop an Excel file or a scanned PDF. The engine automatically extracts each line item and self-audits the arithmetic, eliminating hallucination 100%."* | A smooth *Whoosh*, a green success icon lights up. |
| **00:22 - 00:36** *(14s)* | **Scene 3: 4-tier SKU matching & 3-way rule alerts**<br>- Close-up on the line item with the slang name *"dây mạng 3m bấm sẵn"* (3m pre-terminated network cable); the system maps it exactly to `CAB-CAT6-3M` with 100% confidence thanks to FastEmbed vectors.<br>- Line items with a contract price deviation or insufficient ATP stock are immediately tagged with orange-yellow bordered warning cards `PRICE_MISMATCH` and `INSUFFICIENT_STOCK`. | *"Customers call products by colloquial names? The 4-tier matcher accurately identifies the internal warehouse code. The system cross-checks three ways: contract price list, actual stock, and receivables credit limit, to stop every risk before it reaches the ERP."* | An electronic radar sweep (*Scan beep*), the amber warning card is clearly highlighted. |
| **00:36 - 00:48** *(12s)* | **Scene 4: One-tap mobile approval & ERP Outbox sync**<br>- An iPhone screen receives a Telegram / Zalo OA message summarizing the order's risks with interactive buttons (or opens `/m/orders/PO-10428`).<br>- The director taps the **[✅ Duyệt Đơn]** (Approve Order) button.<br>- Instantly on the web, the order changes to **Approved**, and the Transactional Outbox sends the payload to MISA AMIS / SAP S/4HANA with an immutable Transaction ID. | *"Managers can approve exceptions with one tap right on Telegram, Zalo, or the mobile screen while on a business trip. A validly approved order is pushed instantly into MISA AMIS or SAP with a cryptographic SHA-256 signature that guards against forgery."* | A *Ping* notification, the tap of a button, the stamp of a successful certification. |
| **00:48 - 01:00** *(12s)* | **Scene 5: Pilot measurement report & call to action**<br>- Open the `/reports` page: it shows an SVG chart of time saved, a 96% automation rate, and the export button for `po_preflight_pilot_report.csv`.<br>- Display the Call To Action message. | *"Cut pre-check time by 90%, protect cash flow, and keep accounting data clean. Register for the 30-day Pilot trial program for your business today at po-preflight.vn!"* | Driving, upbeat tech background music, a professional finish. |

---

## 🛠 SCREEN RECORDING GUIDE ON REAL DATA

1. **Prepare the environment:**
   - Run the backend server: `PYTHONPATH=src ./.venv/bin/python -m preflight.cli run`
   - Run the web interface: `cd apps/web && npm run dev`
   - Set the browser to the standard `1920x1080` resolution (100% zoom).
2. **Screens to record:**
   - **Segment 1 (0:10):** Upload a file at `http://localhost:5173/orders` (or `/staging`).
   - **Segment 2 (0:24):** Open `/staging` and click a line item to show the quick-edit feature (Inline Edit) and the SKU code suggestions from the RAG.
   - **Segment 3 (0:38):** Open the mobile approval screen at `http://localhost:5173/m/orders/PO-10428`, review the warnings, and click **[Approve]** along with an exception reason.
   - **Segment 4 (0:45):** Open `/erp-sync` to see the Transactional Outbox event change to `EXPORTED` with the MISA/SAP reconciliation code.
   - **Segment 5 (0:52):** Open `/reports`, close in on the 4 KPI cards for working hours saved, and click the **"Xuất CSV Báo cáo"** (Export Report CSV) button.
