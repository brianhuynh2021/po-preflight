#!/usr/bin/env bash
set -euo pipefail

release_dir="${1:-.}"
PORT="${PORT:-8001}"

echo "🚀 Deploying PO Preflight to target directory: ${release_dir} (Port: ${PORT})..."

cd "${release_dir}"

# If docker-compose is available and configured
if command -v docker >/dev/null 2>&1 && [[ -f "docker-compose.yml" ]]; then
  echo "📦 Updating containers via Docker Compose..."
  docker compose pull || true
  docker compose up -d --build
  echo "⏳ Waiting for health check on port ${PORT}..."
  sleep 4
  curl -fsS "http://127.0.0.1:${PORT}/health/ready" || (echo "Docker health check failed!" >&2 && exit 1)
elif command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet po-preflight; then
  echo "🔄 Restarting po-preflight systemd service..."
  sudo systemctl restart po-preflight
  sleep 3
  curl -fsS "http://127.0.0.1:${PORT}/health/ready" || (echo "Systemd health check failed after restart!" >&2 && exit 1)
fi

echo "✔ Deployment verification successful on port ${PORT}."
