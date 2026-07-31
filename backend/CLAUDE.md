# OriStudio Backend - 启动指南

## 前置检查

启动前确认：

1. `.env` 文件存在且包含 `SECRET_KEY`
2. 端口未被占用（默认 `8001`）
3. 数据库目录 `data/` 可写

## 正确启动命令

**必须在 `backend/` 目录下执行**（`.env` 由 pydantic-settings 相对路径加载）：

```bash
cd /path/to/OriSpark/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

或后台运行：
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 > /tmp/backend.log 2>&1 &
```

## 启动失败排查

| 错误 | 原因 | 解决 |
|------|------|------|
| `KeyError: 'SECRET_KEY'` | 未在 `.env` 中设置或未从 backend 目录启动 | 检查 `backend/.env`，确保从 backend 目录运行 |
| `no such column: watermark_presets.position` | 旧版模型表与新迁移不一致 | `sqlite3 data/oristudio.db "DROP TABLE IF EXISTS watermark_presets;"` 后执行 `alembic upgrade wmk_preset_1` |
| `Multiple head revisions` | 多个迁移头未合并 | 指定目标版本：`alembic upgrade <revision_id>` |
| `Connection refused` | 端口已被占用 | `netstat -ano | findstr :8001` 查占用进程，或改用其他端口 |
| `ImportError` / `ModuleNotFoundError` | 缺少依赖 | `pip install -r requirements.txt` |

## 环境变量来源

- `backend/.env`（优先，由 pydantic-settings 自动加载）
- 系统环境变量（可选覆盖）

`.env` 关键项：
```
SECRET_KEY=<随机32字符hex>
DATABASE_URL=sqlite+aiosqlite:///./data/oristudio.db
PORT=8001
HOST=127.0.0.1
```

## 常用命令

```bash
# 检查迁移状态
cd backend && alembic history

# 查看当前版本
cd backend && alembic current

# 创建新迁移（仅在修改模型后）
cd backend && alembic revision --autogenerate -m "描述"

# 应用迁移
cd backend && alembic upgrade head
```
