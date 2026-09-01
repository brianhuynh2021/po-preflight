.PHONY: dev api demo test test-be test-fe benchmark evals install clean help

PYTHON ?= $(shell which .venv/bin/python 2>/dev/null || which python3)
PORT ?= 8001

help:
	@echo "╔════════════════════════════════════════════════════════════════════╗"
	@echo "║                 🚀 PO PREFLIGHT COMMAND MENU                      ║"
	@echo "╠════════════════════════════════════════════════════════════════════╣"
	@echo "║  make dev         - Khởi động full-stack (FastAPI + Web UI)        ║"
	@echo "║  make api         - Khởi động FastAPI Gateway (cổng $(PORT))         ║"
	@echo "║  make demo        - Chạy demo trực quan 6 chặng                    ║"
	@echo "║  make test        - Chạy toàn bộ test (Backend + Frontend)         ║"
	@echo "║  make test-be     - Chạy kiểm thử Backend (Python unittest)        ║"
	@echo "║  make test-fe     - Chạy kiểm thử Frontend (Next.js / vinext)      ║"
	@echo "║  make benchmark   - Chạy kiểm tra hiệu năng 50 đơn hàng            ║"
	@echo "║  make evals       - Chạy bộ đánh giá AI độ chính xác 100%          ║"
	@echo "║  make install     - Cài đặt dependencies (Python & Node.js)        ║"
	@echo "║  make clean       - Dọn dẹp triệt để cache và file tạm             ║"
	@echo "╚════════════════════════════════════════════════════════════════════╝"

dev:
	@echo "🚀 Khởi động Full-Stack Devbox (FastAPI + Web UI)..."
	npm run dev

api:
	@echo "⚡ Khởi động FastAPI REST Gateway (http://localhost:$(PORT)/docs)..."
	PYTHONPATH=src $(PYTHON) -m uvicorn preflight.api.app:app --host 0.0.0.0 --port $(PORT) --reload

demo:
	@echo "🔍 Chạy kịch bản demo 6 chặng trực quan..."
	PYTHONPATH=src $(PYTHON) scripts/demo_e2e.py

test: test-be test-fe

test-be:
	@echo "🧪 Chạy bộ kiểm thử Backend..."
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests

test-fe:
	@echo "🌐 Chạy bộ kiểm thử Frontend..."
	npm --prefix apps/web test

benchmark:
	@echo "⚡ Chạy Benchmark 50 đơn hàng..."
	PYTHONPATH=src $(PYTHON) scripts/benchmark_50_orders.py

evals:
	@echo "🎯 Chạy AI Evaluations Suite..."
	PYTHONPATH=src $(PYTHON) scripts/run_evals.py

install:
	@echo "📦 Cài đặt dependencies cho Python và Web..."
	pip install -e .
	cd apps/web && npm install

clean:
	@echo "🧹 Dọn dẹp cache, file tạm và artifacts..."
	rm -rf runtime/*.db runtime/*.sqlite* runtime/uploads/* dist build apps/web/dist apps/web/.next apps/web/.vinext .next next-env.d.ts src/*.egg-info .pytest_cache
	touch runtime/uploads/.gitkeep
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.py[cod]" -delete 2>/dev/null || true
	find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@echo "✨ Hoàn tất dọn dẹp sạch sẽ!"
