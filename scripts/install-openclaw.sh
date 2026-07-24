#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
openclaw_workspace="${OPENCLAW_WORKSPACE:-${HOME}/.openclaw/workspace}"
skill_target="${openclaw_workspace}/skills/orderflow"

command -v openclaw >/dev/null 2>&1 || {
  echo "OpenClaw is not installed." >&2
  exit 1
}

mkdir -p "${skill_target}/scripts" "${skill_target}/assets" "${skill_target}/lib"
rsync -a --delete "${repo_root}/src/orderflow/" "${skill_target}/lib/orderflow/"
install -m 0644 \
  "${repo_root}/workspace/skills/orderflow/SKILL.md" \
  "${skill_target}/SKILL.md"
install -m 0755 \
  "${repo_root}/workspace/skills/orderflow/scripts/orderflow.sh" \
  "${skill_target}/scripts/orderflow.sh"
install -m 0644 \
  "${repo_root}/examples/catalog.csv" \
  "${skill_target}/assets/catalog.csv"

openclaw skills info orderflow
echo "OrderFlow was installed into ${skill_target}"
