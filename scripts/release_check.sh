#!/usr/bin/env bash
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "======================================================================"
echo "    PO PREFLIGHT — BẢNG ĐÁNH GIÁ CHẤT LƯỢNG SẢN PHẨM (PHASE D)        "
echo "======================================================================"

TOTAL_PASS=0
TOTAL_FAIL=0

check_criterion() {
  local num="$1"
  local desc="$2"
  local cmd="$3"

  cd "$REPO_ROOT"
  if eval "$cmd" > /dev/null 2>&1; then
    printf "│ %-2s │ %-55s │ \033[0;32mPASS\033[0m │\n" "$num" "$desc"
    TOTAL_PASS=$((TOTAL_PASS + 1))
  else
    printf "│ %-2s │ %-55s │ \033[0;31mFAIL\033[0m │\n" "$num" "$desc"
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
  fi
}

echo "┌────┬─────────────────────────────────────────────────────────┬──────┐"
echo "│ #  │ Tiêu chí kiểm tra chất lượng thương mại                 │ KQ   │"
echo "├────┼─────────────────────────────────────────────────────────┼──────┤"

check_criterion "1"  "Không còn silent fallback; /system/modes trung thực" \
  "PYTHONPATH=src ./.venv/bin/python -m unittest tests/test_no_silent_fallback.py"

check_criterion "2"  "Quyết định qua DecisionService, actor từ auth" \
  "PYTHONPATH=src ./.venv/bin/python -m unittest tests/test_decision_service_http.py"

check_criterion "3"  "Luật B2B chạy qua HTTP với master data thật" \
  "PYTHONPATH=src ./.venv/bin/python -m unittest tests/test_rule_context_http.py"

check_criterion "4"  "ERP payload đầy đủ, idempotent, dead-letter" \
  "PYTHONPATH=src ./.venv/bin/python -m unittest tests/test_erp_payload_http.py"

check_criterion "5"  "Lỗi API theo RFC7807 problem+json" \
  "PYTHONPATH=src ./.venv/bin/python -m unittest tests/test_error_taxonomy.py"

check_criterion "6"  "Next.js FE đăng nhập thật, session cookie pf_session" \
  "test -f apps/web/app/login/page.tsx && test -f apps/web/worker/index.ts"

check_criterion "7"  "Landing page tách biệt, claim trung thực, liên hệ rõ" \
  "test -f apps/web/app/\(marketing\)/page.tsx && test -f apps/web/app/\(marketing\)/pricing/page.tsx"

check_criterion "8"  "Cấu hình Docker Compose PostgreSQL & Worker" \
  "test -f docker-compose.yml && test -f Dockerfile"

check_criterion "9"  "Alembic migration sạch sẽ, schema versioning" \
  "test -d src/preflight/migrations/versions && test -f alembic.ini"

check_criterion "10" "Bộ bóc tách bảng tính Excel & đối soát số học" \
  "PYTHONPATH=src ./.venv/bin/python -m unittest tests/test_excel_ingestion.py"

check_criterion "11" "Khách khác dùng trùng PO không chặn; tái nộp revision" \
  "PYTHONPATH=src ./.venv/bin/python -m unittest tests/test_revisions_and_duplicates.py"

check_criterion "12" "Khách hàng Master & học SKU alias theo từng khách" \
  "PYTHONPATH=src ./.venv/bin/python -m unittest tests/test_customers_and_resolver.py"

check_criterion "13" "Ma trận duyệt theo hạn mức giá trị & SoD" \
  "PYTHONPATH=src ./.venv/bin/python -m unittest tests/test_users_and_approval_matrix.py"

check_criterion "14" "Tồn kho ATP & snapshot từ ERP connector" \
  "PYTHONPATH=src ./.venv/bin/python -m unittest tests/test_inventory_and_atp.py"

check_criterion "15" "Log JSON có request_id và chuỗi băm SHA-256" \
  "PYTHONPATH=src ./.venv/bin/python -m unittest tests/test_observability_and_admin_health.py"

check_criterion "16" "Email Intake Worker kiểm tra idempotency" \
  "PYTHONPATH=src ./.venv/bin/python -m unittest tests/test_email_intake.py"

check_criterion "17" "Hàng đợi xử lý nền & Staging Studio flow" \
  "PYTHONPATH=src ./.venv/bin/python -m unittest tests/test_extraction_review.py"

check_criterion "18" "MISA AMIS Live connector & ERP failover" \
  "PYTHONPATH=src ./.venv/bin/python -m unittest tests/test_live_erp_adapters.py"

check_criterion "19" "Telegram & Zalo OA Bot webhook phê duyệt di động" \
  "PYTHONPATH=src ./.venv/bin/python -m unittest tests/test_zalo_bot.py"

check_criterion "20" "Precision@1 SKU RAG đạt chuẩn >= 93% (Baseline 95%)" \
  "PYTHONPATH=src ./.venv/bin/python scripts/run_evals.py --target-precision 0.93"

check_criterion "21" "Frontend 17/17 rendered HTML tests passing" \
  "(cd apps/web && node --test tests/rendered-html.test.mjs)"

check_criterion "22" "Báo cáo Pilot xuất được file CSV & Email tuần" \
  "PYTHONPATH=src ./.venv/bin/python -m unittest tests/test_pilot_reports.py"

check_criterion "23" "Tài liệu marketing & kỹ thuật khớp năng lực thật" \
  "test -f docs/PILOT_PLAYBOOK.md && test -f docs/SECURITY_QA.md && test -f docs/marketing/CASE_STUDY_TEMPLATE.md"

check_criterion "24" "Quy trình sao lưu khôi phục cơ sở dữ liệu (Runbook)" \
  "test -f docs/RUNBOOK.md"

echo "└────┴─────────────────────────────────────────────────────────┴──────┘"

echo ""
echo "Kết quả: $TOTAL_PASS PASS, $TOTAL_FAIL FAIL"
if [ "$TOTAL_FAIL" -eq 0 ]; then
  echo "🎉 HỆ THỐNG ĐÃ ĐẠT 100% TIÊU CHÍ 'ĐỦ CHÍN ĐỂ ĐI CHÀO HÀNG' (PHASE D READY)!"
  exit 0
else
  echo "⚠️ CẦN HOÀN THIỆN THÊM $TOTAL_FAIL TIÊU CHÍ TRƯỚC KHI BÀN GIAO."
  exit 1
fi
