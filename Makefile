.PHONY: dev api demo test install clean

dev:
	@echo "🚀 Khởi động Web UI..."
	npm run dev

PORT ?= 8001

api:
	@echo "⚡ Khởi động FastAPI REST Gateway (http://localhost:$(PORT)/docs)..."
	PYTHONPATH=src .venv/bin/uvicorn preflight.api.app:app --host 0.0.0.0 --port $(PORT) --reload

demo:
	@echo "🔍 Chạy demo phân tích đơn hàng..."
	./scripts/demo.sh

test:
	@echo "🧪 Chạy bộ kiểm thử tự động..."
	PYTHONPATH=src $(shell [ -f .venv/bin/python ] && echo .venv/bin/python || echo python3) -m unittest discover -s tests

install:
	@echo "📦 Cài đặt dependencies cho Python và Web..."
	pip install -e .
	cd apps/web && npm install

clean:
	@echo "🧹 Dọn dẹp file tạm..."
	rm -rf runtime/*.db .venv apps/web/dist apps/web/.next
