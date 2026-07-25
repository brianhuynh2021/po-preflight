#!/usr/bin/env bash
set -euo pipefail

skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
workspace_dir="$(cd "${skill_dir}/../.." && pwd)"
catalog_path="${PREFLIGHT_CATALOG:-${skill_dir}/assets/catalog.csv}"
db_path="${PREFLIGHT_DB:-${workspace_dir}/preflight-data/preflight.db}"

mkdir -p "$(dirname "${db_path}")"
PYTHONPATH="${skill_dir}/lib" exec python3 -m preflight \
  --catalog "${catalog_path}" \
  --db "${db_path}" \
  "$@"
