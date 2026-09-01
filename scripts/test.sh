#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

for script in "${repo_root}"/scripts/*.sh; do
  bash -n "${script}"
done

PYTHON_BIN="python3"
if [[ -n "${VIRTUAL_ENV:-}" ]] && [[ -x "${VIRTUAL_ENV}/bin/python" ]]; then
  PYTHON_BIN="${VIRTUAL_ENV}/bin/python"
elif [[ -x "${repo_root}/.venv/bin/python" ]]; then
  PYTHON_BIN="${repo_root}/.venv/bin/python"
fi

PYTHONPATH="${repo_root}/src" "${PYTHON_BIN}" -m unittest discover \
  -s "${repo_root}/tests" -v

if grep -RInE --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=.wrangler --exclude='*.example.*' \
  '(sk-ant-[A-Za-z0-9_-]{12,}|xox[baprs]-[A-Za-z0-9-]{12,}|BEGIN (RSA |OPENSSH )?PRIVATE KEY)' \
  "${repo_root}"; then
  echo "A string matching a secret pattern was found." >&2
  exit 1
fi

echo "All checks passed."
