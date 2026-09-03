# PO Preflight — Hệ Thống Tiền Kiểm Đơn Hàng B2B Tự Động

> 🇻🇳 **Tài liệu tiếng Việt đầy đủ:** Xem chi tiết kiến trúc và phân tích nghiệp vụ tại [Mô tả dự án PO Preflight (Tiếng Việt)](docs/MO_TA_DU_AN.md) và [Cẩm nang Pilot](docs/PILOT_PLAYBOOK.md).

**PO Preflight** là cổng tiền kiểm soát và chuẩn hóa đơn đặt hàng (Purchase Orders) dành cho các doanh nghiệp B2B và nhà phân phối tại Việt Nam. Hệ thống tự động bóc tách đơn hàng từ nhiều định dạng, đối soát quy tắc nghiệp vụ theo thời gian thực (giá hợp đồng, hạn mức công nợ, tồn kho khả dụng ATP, quy cách đóng gói), và kích hoạt phê duyệt 1 chạm tức thì qua **Telegram, Zalo Official Account hoặc Web Portal** trước khi đồng bộ an toàn sang hệ thống ERP (MISA AMIS, Bravo, Fast, Odoo, SAP B1).

---

## 📊 Bảng Hiện Trạng Năng Lực Hệ Thống (System Status)

| Thành phần kỹ thuật | Công nghệ & Cơ chế | Trạng thái hiện tại |
|---|---|---|
| **Bóc tách đa định dạng (Multi-format Intake)** | Parser JSON, CSV, Text bảng + Gemini Flash Vision OCR cho ảnh scan/PDF | **Chạy thật (Production Ready)** |
| **Bảo đảm số học (Math Grounding)** | Self-Reflection Math Verifier (đối soát tổng tiền, thuế VAT, chiết khấu dòng) | **Chạy thật (Production Ready)** |
| **Bộ so khớp SKU 4-Tier Hybrid** | Tier 1 Exact Hash → Tier 2 Fuzzy → Tier 3 FastEmbed Vector → Tier 4 LLM | **Chạy thật (Production Ready)** |
| **Đồ thị điều phối luồng (Stateful Workflow)** | LangGraph StateGraph với SQLite/Postgres Checkpointer & ngắt chờ duyệt HITL | **Chạy thật (Production Ready)** |
| **Động cơ luật B2B (Rules Engine)** | Kiểm tra giá hợp đồng, hạn mức công nợ, tồn kho ATP, MOQ, quy cách đóng gói UOM | **Chạy thật (Production Ready)** |
| **Phê duyệt đa kênh di động (Mobile Approval)** | Telegram Bot Webhook + Zalo OA Rich Interactive Cards + Web `/m/orders/:id` | **Chạy thật (Production Ready)** |
| **Cổng kết nối ERP (ERP Outbox)** | Transactional Outbox Pattern với MISA AMIS Live, Odoo, SAP S/4HANA (Hỗ trợ Dry-run) | **Chạy thật (Production Ready)** |
| **Cơ sở dữ liệu kép (Dual-backend Storage)** | SQLite (WAL mode) cho Edge/On-premise và PostgreSQL cho Cloud với Alembic | **Chạy thật (Production Ready)** |
| **Nhật ký mật mã học (Audit Hash Chain)** | Chuỗi băm SHA-256 tuần tự chống sửa đổi (Tamper-evident Cryptographic Hash Chain) | **Chạy thật (Production Ready)** |
| **Email Intake Worker** | IMAP Poller với khóa phân tán chống xử lý trùng lặp và idempotency | **Chạy thật (Production Ready)** |
| **Kênh phụ trợ Slack & WeChat** | Slack App Block Kit & WeChat Work Webhook | **Kế hoạch mở rộng (Roadmap)** |

---

## 🚀 Hướng Dẫn Chạy Nhanh (Quick Start)

### 1. Khởi động Backend API & Chạy Kiểm Thử Đầy Đủ
```bash
# Kích hoạt môi trường Python (>= 3.12)
source .venv/bin/activate

# Chạy toàn bộ bộ kiểm thử tự động (270+ tests)
./scripts/test.sh

# Chạy kịch bản E2E Demo 6 giai đoạn
PYTHONPATH=src python3 -m preflight.cli demo
```

### 2. Khởi động Web Dashboard Khách Hàng (Next.js 16 + React 19 trên Vite)
```bash
cd apps/web
npm install
npm run dev
```
Truy cập `http://localhost:5173/` để xem giao diện Portal vận hành.

---

## 🏗 Kiến Trúc Kỹ Thuật (Architecture)

```text
[ Email (IMAP) / Excel / PDF / JSON ]
                  │
                  ▼
   ┌──────────────────────────────┐
   │ Cascading Ingestion Pipeline │ ── (Gemini Vision OCR fallback)
   └──────────────┬───────────────┘
                  │
                  ▼
   ┌──────────────────────────────┐
   │ 4-Tier Hybrid SKU Matcher    │ ── (Exact -> Fuzzy -> FastEmbed Vector -> LLM)
   └──────────────┬───────────────┘
                  │
                  ▼
   ┌──────────────────────────────┐
   │ LangGraph Stateful Graph     │ ── [Human Approval Checkpoint]
   │ Deterministic Rules Engine   │        │
   └──────────────┬───────────────┘        ├─► Telegram Bot (Inline Buttons)
                  │                        ├─► Zalo Official Account Card
                  │                        └─► Minimal Mobile Screen (/m/orders/:id)
                  ▼
   ┌──────────────────────────────┐
   │ Transactional ERP Outbox     │ ──► [ MISA AMIS / Odoo / SAP S/4HANA ]
   └──────────────┬───────────────┘
                  │
                  ▼
   ┌──────────────────────────────┐
   │ SHA-256 Audit Hash Chain     │ ──► [ Tamper-evident Audit Certificate ]
   └──────────────────────────────┘
```

---

## 🔒 Bảo Mật & Tuân Thủ (Security & Compliance)

- **Nghị định 13/2023/NĐ-CP**: Toàn bộ dữ liệu khách hàng được ẩn danh, mã hóa lưu trữ và hỗ trợ cài đặt hoàn toàn On-Premise hoặc Private Cloud tại Việt Nam.
- **Phân tách trách nhiệm (SoD)**: Ngăn chặn triệt để xung đột lợi ích — nhân viên Sales Admin không được tự duyệt đơn mình nộp; đơn hàng vượt hạn mức bắt buộc có xác nhận của Giám đốc (Director).
- **Tính toàn vẹn dữ liệu**: Chuỗi băm SHA-256 gắn chặt với từng hành động, tự động phát hiện nếu dữ liệu trong cơ sở dữ liệu bị chỉnh sửa trực tiếp.

---

## 📚 Tài Liệu Kỹ Thuật & Nghiệp Vụ
- [Cẩm nang Triển khai Pilot 30 Ngày (Pilot Playbook)](docs/PILOT_PLAYBOOK.md)
- [Mô tả chi tiết kiến trúc hệ thống (Tiếng Việt)](docs/MO_TA_DU_AN.md)
- [Sổ tay giải đáp An ninh & Bảo mật cho Kế toán & IT](docs/SECURITY_QA.md)
- [Mẫu Case Study Triển khai Khách hàng](docs/marketing/CASE_STUDY_TEMPLATE.md)
- [Hợp đồng dữ liệu Frontend (FE Data Contract)](docs/FE_DATA_CONTRACT.md)
- [Hướng dẫn Vận hành & Khôi phục sự cố (Runbook)](docs/RUNBOOK.md)
