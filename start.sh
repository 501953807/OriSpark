#!/bin/bash
# OriStudio 一键启动脚本
# 用法: ./start.sh [--frontend-port 5173] [--backend-port 8765]
# 或:  前端端口=5173 后端端口=8765 ./start.sh

set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$DIR/backend"
FRONTEND_DIR="$DIR/frontend"

# ---------- 默认端口 ----------
FRONTEND_PORT="${FRONTEND_PORT:-5174}"
BACKEND_PORT="${BACKEND_PORT:-8766}"

# ---------- 解析命令行参数 ----------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --frontend-port|-fp)
            FRONTEND_PORT="$2"; shift 2 ;;
        --backend-port|-bp)
            BACKEND_PORT="$2"; shift 2 ;;
        *)
            echo "未知参数: $1"
            echo "用法: $0 [--frontend-port 端口] [--backend-port 端口]"
            exit 1
            ;;
    esac
done

echo "🚀 OriStudio 启动中..."
echo "   前端端口: $FRONTEND_PORT"
echo "   后端端口: $BACKEND_PORT"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 请先安装 Python 3.11+"
    exit 1
fi

# 检查 Node
if ! command -v node &> /dev/null; then
    echo "❌ 请先安装 Node.js 18+"
    exit 1
fi

# 安装后端依赖
if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo "📦 创建 Python 虚拟环境..."
    python3 -m venv "$BACKEND_DIR/venv"
fi
source "$BACKEND_DIR/venv/bin/activate"
pip install -q -r "$BACKEND_DIR/requirements.txt"

# 安装前端依赖
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "📦 安装前端依赖..."
    cd "$FRONTEND_DIR" && npm install --silent
fi

# 启动后端
echo "▶️  启动后端 (http://localhost:$BACKEND_PORT)..."
cd "$BACKEND_DIR"
python3 -c "from app.database import engine, Base; from app.models.base import target_metadata; Base.metadata.create_all(bind=engine)" 2>/dev/null || true
echo ""

# 启动前端 dev server（后台运行）
echo "🌐 启动前端 (http://localhost:$FRONTEND_PORT)..."
cd "$FRONTEND_DIR"
FRONTEND_PORT="$FRONTEND_PORT" BACKEND_PORT="$BACKEND_PORT" npx vite --port "$FRONTEND_PORT" &
FRONTEND_PID=$!

echo ""
echo "✅ OriStudio 已启动!"
echo "   前端: http://localhost:$FRONTEND_PORT"
echo "   后端: http://localhost:$BACKEND_PORT"
echo "   API 文档: http://localhost:$BACKEND_PORT/docs"
echo ""

# 等待后端先启动
sleep 2

# 启动后端
cd "$BACKEND_DIR"
uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" &

# 捕获退出信号，一起清理子进程
trap "kill $FRONTEND_PID $! 2>/dev/null; exit" INT TERM EXIT

wait
