.PHONY: dev demo test install clean

dev:
	@echo "🚀 Khởi động Web UI..."
	npm run dev

demo:
	@echo "🔍 Chạy demo phân tích đơn hàng..."
	./scripts/demo.sh

test:
	@echo "🧪 Chạy bộ kiểm thử tự động..."
	PYTHONPATH=src python3 -m unittest discover -s tests

install:
	@echo "📦 Cài đặt dependencies cho Python và Web..."
	pip install -e .
	cd apps/web && npm install

clean:
	@echo "🧹 Dọn dẹp file tạm..."
	rm -rf runtime/*.db .venv apps/web/dist apps/web/.next
