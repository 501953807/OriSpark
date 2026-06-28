# Phase 0 实施设计 — 权益保护基础

> **日期**: 2026-06-28
> **基于**: 2026-06-25 创作者权益保护平台设计文档
> **范围**: 4 个子任务全部实现 — 风险预警引擎 + AI创作会话 + C2PA + 多平台存证
> **前置**: 用户确认 Phase 0 四项全做 + 风险预警四维度全做 + AI会话含前端

---

## 一、风险预警引擎

### 1.1 数据模型

**新表**: `risk_warnings`

```sql
CREATE TABLE risk_warnings (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    work_id TEXT REFERENCES works(id),
    warning_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    matched_entity TEXT,
    confidence FLOAT,
    suggestion TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    dismissed BOOLEAN DEFAULT 0,
    dismissed_at DATETIME
);
CREATE INDEX idx_risk_work ON risk_warnings(work_id);
CREATE INDEX idx_risk_type ON risk_warnings(warning_type);
CREATE INDEX idx_risk_severity ON risk_warnings(severity);
```

### 1.2 四个检测维度

| 维度 | 实现方式 | 依赖 |
|------|---------|------|
| 提示词侵权检测 | 本地 TF-IDF + 关键词库匹配 | 内置关键词库 (商标名/IP名/艺术家风格) |
| 参考图相似度 | 感知哈希 (pHash) + 余弦相似度 | 扩展现有 `hasher.py` |
| LoRA 权属检查 | 查询 Civitai/HuggingFace API | 外部 API |
| 商标碰撞 | 查询 CNIPA/USPTO/WIPO | 网关适配器 `TrademarkGateway` |

### 1.3 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/risk-warning/check | 统一检测入口 (body: {work_id, prompt?, reference_images[]?, model_name?}) |
| GET | /api/risk-warning/work/{work_id} | 获取作品的预警记录 |
| PATCH | /api/risk-warning/{id}/dismiss | 标记已查看 |
| GET | /api/risk-warning/keywords | 获取关键词库统计 |

### 1.4 前端组件

- `RiskWarningView.vue` — 风险预警中心页面，展示所有预警记录
- `RiskWarningPanel.vue` — 嵌入作品创建流程的 Step 0 内联面板

---

## 二、AI 创作会话记录

### 2.1 数据模型

**扩展 works 表**:
```sql
ALTER TABLE works ADD COLUMN ai_assisted BOOLEAN DEFAULT 0;
ALTER TABLE works ADD COLUMN ai_tools_used JSON;
ALTER TABLE works ADD COLUMN creator_type TEXT DEFAULT 'illustrator';
```

**新表**: `ai_creation_sessions`

```sql
CREATE TABLE ai_creation_sessions (
    id TEXT PRIMARY KEY,
    work_id TEXT NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL,
    tool_version TEXT,
    prompt TEXT NOT NULL,
    prompt_history JSON,
    seed INTEGER,
    parameters JSON,
    negative_prompt TEXT,
    model_name TEXT,
    lora_names JSON,
    output_images JSON,
    human_interventions JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_ai_session_work ON ai_creation_sessions(work_id);
```

### 2.2 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/works/{id}/ai-session | 记录创作会话 |
| GET | /api/works/{id}/ai-sessions | 获取时间线 |
| PATCH | /api/works/{id}/ai-session/{sid} | 编辑会话 |
| DELETE | /api/works/{id}/ai-session/{sid} | 删除会话 |

### 2.3 前端组件

- `AiSessionPanel.vue` — 作品详情页内的 AI 会话记录面板
- 支持手动录入 + API 自动采集

---

## 三、C2PA 内容凭证（扩展现有服务）

### 3.1 现有基础

- `backend/app/services/c2pa_service.py` 已存在
- 需扩展 manifest 生成逻辑，加入 AI 创作会话摘要

### 3.2 变更

| 文件 | 变更 |
|------|------|
| `c2pa_service.py` | manifest 加入 `ai_session_summary` + `creation_timeline` |
| `notary.py` 路由 | 新增 `/api/notary/c2pa/{work_id}` 端点 |
| `NotaryPanel.vue` | 增加 C2PA 凭证标签页 |

### 3.3 数据模型

**新表**: `c2pa_manifests`

```sql
CREATE TABLE c2pa_manifests (
    id TEXT PRIMARY KEY,
    work_id TEXT NOT NULL UNIQUE REFERENCES works(id),
    manifest_json TEXT NOT NULL,
    embedded_path TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 四、多平台存证扩展

### 4.1 变更

| 文件 | 变更 |
|------|------|
| `notary_records` 表 | 扩展 `blockchain_type`, `c2pa_manifest_path`, `timestamp_token_path` |
| `notary.py` 路由 | 新增 Polygon 存证 + DigiCert TSA 端点 |
| `gateway/digicert_tsa.py` | 新建 DigiCert TSA 网关 |
| `gateway/polygon.py` | 新建 Polygon 存证网关 |
| `services/timestamp_service.py` | 新建时间戳服务 |

### 4.2 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/notary/polygon | Polygon 公链存证 |
| POST | /api/notary/timestamp | DigiCert RFC 3161 时间戳 |
| GET | /api/notary/records/{work_id} | 获取作品所有存证记录 |

---

## 五、文件清单汇总

### 新建文件 (11 个)

| 文件 | 用途 |
|------|------|
| `backend/app/models/risk_warning.py` | 风险预警数据模型 |
| `backend/app/models/ai_session.py` | AI创作会话数据模型 |
| `backend/app/models/c2pa_records.py` | C2PA凭证数据模型 |
| `backend/app/services/risk_warning_service.py` | 风险预警引擎服务 |
| `backend/app/services/timestamp_service.py` | 时间戳服务 |
| `backend/app/gateway/trademark.py` | 商标数据库网关 |
| `backend/app/gateway/model_source.py` | LoRA来源查询网关 |
| `backend/app/gateway/digicert_tsa.py` | DigiCert TSA网关 |
| `backend/app/gateway/polygon.py` | Polygon存证网关 |
| `frontend/src/views/RiskWarningView.vue` | 风险预警页面 |
| `frontend/src/components/AiSessionPanel.vue` | AI会话记录面板 |

### 修改文件 (7 个)

| 文件 | 变更 |
|------|------|
| `backend/app/models/work.py` | 扩展: ai_assisted, ai_tools_used, creator_type |
| `backend/app/models/base.py` | 注册新模型 |
| `backend/app/models/__init__.py` | 导入新模型 |
| `backend/app/routers/notary.py` | 扩展: C2PA + Polygon + TSA |
| `backend/app/routers/risk_warning.py` | (新建) |
| `backend/app/routers/ai_session.py` | (新建) |
| `backend/app/services/c2pa_service.py` | 扩展: manifest 加入 AI 会话摘要 |
| `frontend/src/views/NotaryPanel.vue` | 扩展: C2PA + 多平台存证 |

---

## 六、实施顺序

```
Step 1: 数据模型层 (3 新 + 2 改)
  ├── risk_warning.py
  ├── ai_session.py
  ├── c2pa_records.py
  ├── work.py 扩展
  └── base.py / __init__.py 注册

Step 2: 网关适配层 (3 新)
  ├── trademark.py
  ├── model_source.py
  └── digicert_tsa.py + polygon.py

Step 3: 服务层 (2 新 + 1 改)
  ├── risk_warning_service.py
  ├── timestamp_service.py
  └── c2pa_service.py 扩展

Step 4: 路由层 (2 新 + 1 改)
  ├── risk_warning.py
  ├── ai_session.py
  └── notary.py 扩展

Step 5: 前端层 (2 新 + 1 改)
  ├── RiskWarningView.vue
  ├── AiSessionPanel.vue
  └── NotaryPanel.vue 扩展
```

---

## 七、关键技术决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 提示词检测 | 本地关键词库 + TF-IDF | 不依赖外部 API，速度快 |
| 参考图相似度 | pHash + 余弦相似度 | 扩展现有 hasher.py，零新增依赖 |
| LoRA 权属 | Civitai API (默认) + HuggingFace | 覆盖面最广 |
| 商标碰撞 | CNIPA (首选) + USPTO (备选) | 国内创作者主要市场 |
| C2PA | Adobe content-auth SDK | 已有服务骨架，继续扩展 |
| 国际存证 | Polygon (ERC-725) | Gas 费低，国际认可 |
| 时间戳 | DigiCert TSA (RFC 3161) | 行业标准 |
