#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runtime_dir="${repo_root}/runtime"
db_path="${runtime_dir}/demo.db"

mkdir -p "${runtime_dir}"
rm -f "${db_path}"

run_order() {
  local order_file="$1"
  set +e
  PYTHONPATH="${repo_root}/src" python3 -m orderflow \
    --catalog "${repo_root}/examples/catalog.csv" \
    --db "${db_path}" \
    analyze "${repo_root}/${order_file}"
  local exit_code=$?
  set -e
  if [[ ${exit_code} -ne 0 && ${exit_code} -ne 2 ]]; then
    exit "${exit_code}"
  fi
  printf '\n'
}

run_order "examples/orders/po-clean.json"
run_order "examples/orders/po-review.json"
run_order "examples/orders/po-blocked.txt"

echo "Demo audit database: ${db_path}"
