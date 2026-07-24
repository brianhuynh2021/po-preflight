#!/usr/bin/env bash
set -euo pipefail

skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
workspace_dir="$(cd "${skill_dir}/../.." && pwd)"
catalog_path="${ORDERFLOW_CATALOG:-${skill_dir}/assets/catalog.csv}"
db_path="${ORDERFLOW_DB:-${workspace_dir}/orderflow-data/orderflow.db}"

mkdir -p "$(dirname "${db_path}")"
PYTHONPATH="${skill_dir}/lib" exec python3 -m orderflow \
  --catalog "${catalog_path}" \
  --db "${db_path}" \
  "$@"
