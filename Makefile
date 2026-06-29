.PHONY: help dev backend frontend install test clean

help: ## 显示帮助信息
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## 安装所有依赖
	@echo "安装后端依赖..."
	cd backend && pip install -r requirements.txt
	@echo "安装前端依赖..."
	cd frontend && npm install
	@echo "依赖安装完成!"

dev: ## 启动开发环境 (后端 + 前端)
	@echo "启动后端 (端口 8765)..."
	cd backend && uvicorn app.main:app --port 8765 --reload &
	@echo "启动前端 (端口 5173)..."
	cd frontend && npm run dev

backend: ## 仅启动后端开发服务器
	cd backend && uvicorn app.main:app --port 8765 --reload

frontend: ## 仅启动前端开发服务器
	cd frontend && npm run dev

db-init: ## 初始化数据库
	cd backend && python -m app.database --init

db-migrate: ## 运行数据库迁移
	cd backend && alembic upgrade head

db-revision: ## 创建新的迁移脚本
	cd backend && alembic revision --autogenerate -m "$(msg)"

test: ## 运行所有测试
	cd backend && pytest tests/ -v
	cd frontend && npx vitest run

test-backend: ## 运行后端测试
	cd backend && pytest tests/ -v

test-frontend: ## 运行前端测试
	cd frontend && npx vitest run

lint: ## 代码检查
	cd backend && ruff check app/
	cd frontend && npx eslint src/

format: ## 代码格式化
	cd backend && ruff format app/
	cd frontend && npx prettier --write src/

clean: ## 清理构建产物
	rm -rf backend/__pycache__ backend/app/__pycache__
	rm -rf frontend/dist frontend/.vite
	rm -rf backend/data/certificates/*
	@echo "清理完成."

docker-build: ## 构建 Docker 镜像
	docker-compose build

docker-up: ## 启动 Docker 服务
	docker-compose up -d

docker-down: ## 停止 Docker 服务
	docker-compose down
