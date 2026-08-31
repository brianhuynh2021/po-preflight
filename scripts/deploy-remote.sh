#!/usr/bin/env bash
set -euo pipefail

release_dir="${1:-}"
if [[ -z "${release_dir}" || ! -d "${release_dir}/src/preflight" ]]; then
  echo "Usage: deploy-remote.sh <release-directory>" >&2
  exit 1
fi

"${release_dir}/scripts/test.sh"
echo "Deployment verification successful."
