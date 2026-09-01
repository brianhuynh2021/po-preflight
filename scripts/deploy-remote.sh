#!/usr/bin/env bash
set -euo pipefail

release_dir="${1:-}"
if [[ -z "${release_dir}" || ! -d "${release_dir}/src/preflight" ]]; then
  echo "Usage: deploy-remote.sh <release-directory>" >&2
  exit 1
fi

"${release_dir}/scripts/test.sh"

# If systemd service exists on remote host, restart and verify health
if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet po-preflight; then
  echo "Restarting po-preflight systemd service..."
  sudo systemctl restart po-preflight
  sleep 3
  curl -fsS http://127.0.0.1:8000/health/ready || (echo "Health check failed after restart!" >&2 && exit 1)
fi

echo "Deployment verification successful."

