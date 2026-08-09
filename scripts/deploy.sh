#!/bin/bash
# OriStudio 一键部署脚本

set -e

echo "🚀 OriStudio 部署脚本"
echo "===================="

# 检查环境变量
if [ -z "$SECRET_KEY" ]; then
    echo "❌ 请设置 SECRET_KEY 环境变量"
    exit 1
fi

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装"
    exit 1
fi

echo "✅ 环境检查通过"

# 创建 .env 文件
if [ ! -f .env ]; then
    echo "📝 生成 .env 文件..."
    cat > .env << ENVEOF
SECRET_KEY=${SECRET_KEY}
DATABASE_URL=postgresql://oristudio:password@db:5432/oristudio
REDIS_URL=redis://redis:6379/0
ENVEOF
fi

# 启动服务
echo "📦 启动服务..."
docker-compose -f docker-compose.prod.yml up -d

echo "⏳ 等待服务启动..."
sleep 10

# 健康检查
echo "🏥 健康检查..."
if curl -sf http://localhost:8001/health > /dev/null; then
    echo "✅ 后端服务正常"
else
    echo "⚠️ 后端服务可能未就绪"
fi

if curl -sf http://localhost/ > /dev/null; then
    echo "✅ 前端服务正常"
else
    echo "⚠️ 前端服务可能未就绪"
fi

echo ""
echo "🎉 部署完成!"
echo ""
echo "访问地址:"
echo "  - 前端: http://localhost"
echo "  - 后端 API: http://localhost:8001"
echo "  - API 文档: http://localhost:8001/docs"
echo ""
echo "查看日志:"
echo "  docker-compose -f docker-compose.prod.yml logs -f"
