#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

for script in "${repo_root}"/scripts/*.sh; do
  bash -n "${script}"
done

PYTHONPATH="${repo_root}/src" python3 -m unittest discover \
  -s "${repo_root}/tests" -v

if grep -RInE --exclude-dir=.git --exclude='*.example.*' \
  '(sk-ant-[A-Za-z0-9_-]{12,}|xox[baprs]-[A-Za-z0-9-]{12,}|BEGIN (RSA |OPENSSH )?PRIVATE KEY)' \
  "${repo_root}"; then
  echo "A string matching a secret pattern was found." >&2
  exit 1
fi

if LC_ALL=C grep -RIn --exclude-dir=.git '[^[:print:][:space:]]' \
  "${repo_root}/src" "${repo_root}/scripts" "${repo_root}/tests"; then
  echo "Non-ASCII source text found; product output must remain English-only." >&2
  exit 1
fi

echo "All checks passed."
