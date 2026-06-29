# [7] 系统基础设施 — 详细功能设计 v3

> **定位**: 支撑所有业务模块的基础设施层。统一字典数据中心、多平台联合认证、数据备份恢复、系统运行监控、审计日志、插件扩展框架、Onboarding向导、免责声明管理。
> **最后更新**: 2026-06-12 (Stage 2修订: 大文件存储策略、免责声明管理机制、Onboarding数据持久化)

---

## 一、统一字典数据中心

### 核心理念
任何被多个模块重复定义的枚举/配置/常量，只在一个地方维护。前端通过API动态获取，后端通过dict_service统一引用。

### 字典分组体系 (60+分组)

| 模块 | 字典分组 | 示例值 |
|------|---------|--------|
| 01-创意资产 | file_types | image/audio/video/document/code/design |
| | process_stages_image | inspiration/sketch/lineart/coloring/detail/final/exports |
| | process_stages_video | script/storyboard/roughcut/finecut/colorgrade/final |
| | process_stages_audio | idea/arrangement/recording/mixing/mastering/release |
| | process_stages_document | outline/draft/revision/final/formatting/publish |
| | import_modes | hash-only/lowres/full |
| | license_types | cc_by_4.0/cc_by_sa_4.0/cc_by_nc_4.0/cc0/all_rights_reserved/custom |
| 02-权利保护 | notary_platforms | banquanjia/antchain/zhixinchain/local |
| | monitor_platforms | baidu/google |
| | monitor_result_statuses | pending_review/infringing/ignored/whitelisted |
| 03-IP登记 | ip_types | copyright/trademark/design_patent/utility_patent |
| | jurisdictions | cn/us/eu/jp/kr/wipo |
| | registration_statuses | draft/filed/under_review/registered/rejected/expired |
| | disclaimer_types | no_attorney_relationship/no_legal_advice/no_guarantee/pod_ip_warning/ai_content_label/monitor_limitation/jurisdiction_limitation |
| 04-商业转化 | monetization_paths | pod/digital/crowdfunding/licensing/custom_mfg |
| | material_categories | paper/textile/hard_goods/digital/handcraft |
| | product_categories | t_shirt/hoodie/tote_bag/mug/phone_case/sticker/poster/... (60+) |
| | campaign_statuses | draft/launching/funded/successful/failed/fulfilling/completed |
| | license_types_biz | single_use/multi_use/commercial_extended/buyout |
| | pod_platforms | printful/printify/redbubble/yingge/society6/gelato |
| 05-内容分发 | publish_platforms | xiaohongshu/zcool/weibo/bilibili/douyin/instagram/youtube/wechat |
| | publish_platforms_future | spotify/qqmusic/netease/applemusic/qidian/jinjiang/kdp/etsy |
| | ai_style_templates | xiaohongshu/zcool/weibo/bilibili/douyin/instagram |
| 06-经营管理 | partner_types | supplier/factory/pod_platform/client/licensee |
| | order_statuses | pending/confirmed/in_production/shipped/completed/cancelled |
| 07-系统 | languages | zh-CN/en-US/ja-JP |
| | themes | light/dark/auto |
| | creator_types | illustrator/photographer/video/craft/music/writer |
| | onboarding_steps | select_type/import_works/quick_start |

### 数据模型

```
dictionary_groups: id, group_key, group_name, module, description, is_extensible, sort_order
dictionary_items: id, group_id(FK), item_key, item_value, item_value_en, sort_order, is_active, is_custom(user_added)
```

### 前端字典获取
- useDictStore: `const dictStore = useDictStore(); await dictStore.init();`
- 使用: `dictStore.getItems('file_types')` → [{item_key:'image', item_value:'图片'}, ...]
- 动态过滤下拉: 从字典获取而非硬编码

---

## 二、Onboarding 向导与数据持久化

### 2.1 3步引导流程 (UX规范设计)

**Step 1: 选择创作者类型**
- 3列x2行卡片网格
- v1: 插画师卡片视觉突出（大尺寸 + 闪光渐变边框 + "推荐"徽章）
- 其余5类标注能力状态: "基础导入可用，专属工作流规划中"
- 选择持久化到 `users.creator_type`

**Step 2: 导入第一批作品**
- 大面积友好拖拽区域 + 支持格式图标说明
- 拖拽文件夹时自动按子文件夹名称创建项目组
- "跳过，稍后导入" 链接

**Step 3: 快速上手引导**
- 成功仪式感 + 简化3步路径可视化 (🎨管理作品 → 🛡️保护版权 → 💰开始变现)
- "开始使用"按钮 → 进入首页
- 持久化到 `system_settings.onboarding_completed = true`

### 2.2 数据持久化方案

| 数据项 | 存储位置 | 字段 |
|--------|---------|------|
| 创作者类型 | users表 | `creator_type` (新增: illustrator/photographer/video/craft/music/writer) |
| Onboarding完成状态 | system_settings表 | `onboarding_completed` (boolean) |
| 默认变现路径 | system_settings表 | 从creator_type推导，写入system_settings |
| 推荐分发平台(前3) | system_settings表 | 从creator_type推导，写入system_settings |
| 产品品类过滤 | — | 前端根据creator_type动态过滤，无需存储 |

### 2.3 Onboarding触发的系统自动配置

| 选择类型 | 自动配置 |
|----------|---------|
| 插画师 | 过程阶段=插画师7阶段, 首页推荐=POD渠道管理, 默认平台=小红书/站酷/B站 |
| 摄影师(规划中) | 过程阶段=摄影8阶段, 首页推荐=POD渠道管理, 默认平台=小红书/Instagram/微博 |
| 其他类型(规划中) | 过程阶段=通用6阶段, 首页推荐=基础功能引导 |

---

## 三、免责声明管理机制

### 3.1 免责声明数据模型

```
disclaimers: id, disclaimer_key, title, content, category, priority, is_required, is_active
disclaimer_acceptances: id, user_id, disclaimer_id, accepted_at, accepted_version, context(trigger_page)
```

### 3.2 7项免责声明清单

| Key | 标题 | 触发场景 | 必须确认 |
|-----|------|---------|---------|
| no_attorney_relationship | 不构成律师-客户关系 | 首次进入IP登记 | 是 |
| no_legal_advice | 不构成法律建议 | IP登记/类别推荐/费用计算 | 是 |
| no_guarantee | 不保证注册成功 | IP登记/类别推荐 | 是 |
| pod_ip_warning | POD平台IP条款警告 | POD渠道管理 | 否(Banner) |
| ai_content_label | AI内容标注要求 | AI文案生成 | 否(底部标注) |
| monitor_limitation | 侵权监测局限性 | 侵权监测页面 | 否(Banner) |
| jurisdiction_limitation | 司法管辖区限制 | IP登记 | 否(Banner) |

### 3.3 展示策略

| 场景 | 展示方式 | 交互 |
|------|---------|------|
| 首次进入IP登记模块 | 全屏Modal | 必须点击"我已阅读并理解"→记录acceptance |
| 类别推荐结果 | 底部Banner | 黄色警告条，不可折叠 |
| 费用计算结果 | 底部小字 | 灰色文字 |
| 导出材料 | 页脚声明 | 灰色文字 |
| 侵权监测页面 | 顶部Banner | 黄色警告条，不可折叠 |
| AI文案结果 | 底部标注 | 灰色文字 |
| POD渠道管理 | 顶部Banner | 黄色警告条，关闭后7天再显示 |

---

## 四、多平台联合认证

### 4.1 认证方式

| 方式 | 说明 | 配置要求 |
|------|------|----------|
| 本地免登录 | 默认模式，自动创建本地用户 | 无需配置 |
| Google One Tap | Google OAuth2.0 | GOOGLE_CLIENT_ID+SECRET |
| 微信扫码 | 微信OAuth2.0 | WECHAT_APP_ID+SECRET |
| 邮箱+密码 | 传统注册登录 | SMTP配置 |

### 4.2 用户账号中心
- 多平台身份绑定: 一个用户可关联 Google+微信+邮箱
- Profile: 显示名称/简介/头像/联系方式 + **creator_type 字段**
- 数据导出: 一键导出所有个人数据(JSON/CSV)
- 账户注销

### 4.3 API (已有)
- POST /api/auth/register — 注册
- POST /api/auth/login — 登录
- GET /api/auth/me — 当前用户信息
- PATCH /api/auth/me — 更新Profile (含 creator_type)
- GET /api/auth/google/url — Google OAuth URL
- POST /api/auth/google/callback — Google回调
- GET /api/auth/wechat/qrcode — 微信扫码URL
- POST /api/auth/wechat/callback — 微信回调
- POST /api/auth/bind/{provider} — 绑定平台账号
- DELETE /api/auth/unbind/{provider} — 解绑

---

## 五、大文件存储策略 (新增)

### 5.1 问题背景

- 视频文件: 100MB+ 常见, 版本快照会导致存储爆炸
- 摄影RAW: 每张50MB+, 一个拍摄64GB
- 当前系统: 无磁盘配额/清理机制

### 5.2 存储策略设计

| 维度 | 策略 |
|------|------|
| 文件存储 | `data/workspace/{uuid前2位}/{uuid}/` — 保持原设计 |
| 版本快照 | **非文件全量快照**: 仅记录 metadata+hash+file_path引用，不复制原始文件 |
| 缩略图 | 独立存储，`data/thumbnails/{uuid前2位}/{uuid}_thumb.jpg` |
| 磁盘配额 | 默认 5GB/用户 (可配置)，可通过系统设置调整 |
| 配额告警 | 80% 阈值 → 通知提醒 / 95% → 阻止新导入 |
| 清理机制 | 回收站30天自动清理 (Celery Beat) |
| 大文件导入提示 | >100MB: "此文件较大({size})，建议确认您的存储空间" |
| 存储趋势 | 系统监控页面展示存储使用趋势图 |

### 5.3 实现要点

- `users.storage_used` 字段: 跟踪用户已用存储空间
- `system_settings.storage_quota_mb` 配置: 默认 5120 (5GB)
- 导入前检查: `if storage_used + file_size > quota: 拒绝导入`
- 缩略图不计入配额(系统生成)

---

## 六、数据备份恢复

### 6.1 备份类型

| 类型 | 说明 | 实现 |
|------|------|------|
| 标准备份 | 数据库+配置文件打包 | SQLite dump + tar.gz |
| 加密备份 | AES-256加密 | 加密后打包，密码保护 |
| 定时备份 | Cron自动执行 | Celery Beat |

### 6.2 功能
- 创建备份: 标准/加密
- 备份列表: 文件名/大小/时间/类型/加密状态
- 恢复: 上传备份文件 → 确认 → 恢复
- 定时备份配置: 每日/每周/每月
- 备份保留策略: 保留最近N个备份

### 6.3 API (已有)
- POST /api/system/backup — 创建备份
- GET /api/system/backups — 备份列表
- POST /api/system/backup/restore — 恢复备份
- DELETE /api/system/backups/{id} — 删除备份
- GET/PATCH /api/system/settings — 系统设置(含备份schedule)

---

## 七、运行监控

### 7.1 监控指标

| 指标 | 来源 | 展示 |
|------|------|------|
| CPU使用率 | psutil | 百分比+进度条 |
| 内存使用 | psutil | 已用/总量+进度条 |
| 磁盘使用 | psutil | 可用/总量+进度条 |
| 数据库大小 | SQLite文件大小 | MB |
| 缩略图文件夹大小 | du | MB |
| 用户存储使用 | users.storage_used | 按用户汇总 |
| 服务状态 | Celery/WebSocket/数据库 | 在线/离线 |
| 存储趋势 | 历史记录 | 折线图 |

### 7.2 API (已有)
- GET /api/system/health — 健康检查
- GET /api/system/health/detailed — 详细监控数据

---

## 八、审计日志

### 8.1 记录内容
- 用户操作: 谁/什么时间/做了什么/IP地址
- CRUD操作: 新建作品/编辑/删除/存证/扫描
- 系统事件: 启动/关闭/备份/恢复/错误
- **免责声明操作**: 谁/什么时间/接受了哪个声明/触发页面

### 8.2 API (已有)
- GET /api/system/audit-logs — 审计日志列表(?page=&user=&action=&date_from=&date_to=&search=)
- 全文搜索+导出

---

## 九、插件/扩展框架

定义标准接口，允许第三方扩展系统功能:
```
plugins: id, name, display_name, version, description, hooks(JSON), enabled, created_at
```

支持的Hook点: on_startup, on_product_create, on_work_import, on_certificate_generate, on_publish

---

## 十、前端实现

### SettingsView.vue — 保持现有10分区:
1. 👤 个人资料 (Profile) + creator_type 显示
2. 🔒 账号安全 (密码修改/二因素) (新增)
3. 🔗 关联账号 (Google/微信绑定)
4. 🔔 通知偏好 (渠道/频率设置) (新增)
5. 🎨 外观设置 (暗色/语言)
6. 💾 数据管理 (备份/恢复/存储配额)
7. 📚 字典管理 (字典浏览器+编辑器)
8. 📊 系统健康 (CPU/内存/磁盘/存储仪表盘)
9. 📋 审计日志 (日志列表+搜索+导出)
10. ℹ️ 关于 (版本/许可信息)

### OnboardingWizard.vue (新建)
- 3步向导组件
- Step1: 创作者类型选择卡片 (插画师突出)
- Step2: 导入区域 (拖拽+文件夹支持+跳过)
- Step3: 完成仪式+快速路径指引
- 数据持久化到 users.creator_type + system_settings.onboarding_completed

### DisclaimerBanner.vue (新建)
- 可复用免责声明组件
- 支持多种展示模式: 全屏Modal / Banner / 底部小字
- Props: disclaimerKey, mode(modal/banner/footer), dismissible

### 补充前端组件规格

**DictBrowser.vue** — 字典管理器

Props: `{}`

```
┌────────────────────────────────────────────────────────┐
│ 📚 字典管理                                            │
├────────────────────────────────────────────────────────┤
│ 分组: [file_types ▼] [全部 ▼]                          │
│                                                        │
│ ┌──────────┬──────────┬──────────┬────────┬──────────┐ │
│ │ 键       │ 值       │ 值(英文) │ 排序   │ 激活   │ 操作  │ │
│ ├──────────┼──────────┼──────────┼────────┼──────────┤ │
│ │ image    │ 图片     │ Image    │ 1      │ ☑      │ ✏️ 🗑 │ │
│ │ audio    │ 音频     │ Audio    │ 2      │ ☑      │ ✏️ 🗑 │ │
│ │ video    │ 视频     │ Video    │ 3      │ ☑      │ ✏️ 🗑 │ │
│ │ document│ 文档     │ Document │ 4      │ ☑      │ ✏️ 🗑 │ │
│ └──────────┴──────────┴──────────┴────────┴──────────┘ │
│                                                        │
│ [+ 添加新项]  [导入JSON]  [导出JSON]                   │
└────────────────────────────────────────────────────────┘
```

**BackupManager.vue** — 备份管理

Props: `{}`

```
┌────────────────────────────────────────────────────────┐
│ 💾 数据备份                                            │
├────────────────────────────────────────────────────────┤
│ 存储使用: 2.3 GB / 5 GB (46%)                          │
│                                                        │
│ 创建新备份:                                            │
│ [标准备份] [加密备份]                                   │
│                                                        │
│ 备份历史:                                              │
│ ┌────────────────────────────────────────────────────┐ │
│ │ 2026-06-24 02:00  标准  156MB  ✅ 自动             │ │
│ │ 2026-06-23 02:00  标准  154MB  ✅ 自动             │ │
│ │ 2026-06-20 14:30  加密  148MB  ✅ 手动             │ │
│ └────────────────────────────────────────────────────┘ │
│                                                        │
│ [恢复备份] [删除选中] [设置保留策略]                    │
└────────────────────────────────────────────────────────┘
```

**AuthLoginView.vue** — 登录页面

Props: `{}`

```
┌────────────────────────────────────────────────────────┐
│                    OriStudio                           │
├────────────────────────────────────────────────────────┤
│                                                        │
│  邮箱: [________________________]                      │
│  密码: [________________________]                      │
│                                                        │
│  ☑ 记住我     [忘记密码?]                              │
│                                                        │
│  [登录]                                                │
│                                                        │
│  ─────── 或 ───────                                    │
│                                                        │
│  [🔵 Google 登录]  [💚 微信登录]                       │
│                                                        │
│  还没有账号? [注册]                                    │
└────────────────────────────────────────────────────────┘
```

Events: `@login(email, password, remember)`, `@google-login`, `@wechat-login`, `@forgot-password`, `@register`

**AuthRegisterView.vue** — 注册页面

Props: `{}`

```
┌────────────────────────────────────────────────────────┐
│                    OriStudio — 注册                     │
├────────────────────────────────────────────────────────┤
│                                                        │
│  邮箱: [________________________]                      │
│  密码: [________________________]                      │
│  确认密码: [________________________]                  │
│  显示名称: [________________________]                  │
│                                                        │
│  [注册]                                                │
│                                                        │
│  已有账号? [登录]                                      │
└────────────────────────────────────────────────────────┘
```

**AccountSecurityView.vue** — 账号安全 (SettingsView 分区 2)

Props: `{}`

- 密码修改: 旧密码 + 新密码 + 确认新密码
- 二因素认证: 启用/禁用 (TOTP)
- 登录设备管理: 设备列表 + 远程登出

**NotificationPreferencesView.vue** — 通知偏好 (SettingsView 分区 4)

Props: `{}`

- 通知渠道: [WebSocket ✅] [邮件 ☐] [微信 ☐]
- 通知频率: [实时] [每小时汇总] [每日汇总]
- 通知类型开关:
  - 存证完成: [✅ 开启]
  - 侵权扫描结果: [✅ 开启]
  - 维权行动状态: [✅ 开启]
  - 风险预警: [✅ 开启]
  - 系统更新: [✅ 开启]

---

## 十一、API汇总

| 模块 | 端点数 | 路由前缀 |
|------|--------|----------|
| 字典 | 8+ | /api/system/dictionary-groups, /api/system/dictionary-items |
| 认证 | 14 | /api/auth/* |
| 通知 | 4 | /api/notifications/* |
| 系统 | 50 | /api/system/* |
| WebSocket | 1 | /ws/notify |
| Onboarding | 2 (新增) | /api/auth/complete-onboarding, /api/system/onboarding-status |
| 免责声明 | 3 (新增) | /api/system/disclaimers, /api/system/disclaimers/accept |

---

## 十二、AI Agent 编排与风险预警 (新增 v1)

### 12.1 Agent 编排架构

所有 AI Agent 通过 Celery 异步编排，对外表现为"自动化"：

| Agent | 触发方式 | 职责 | 编排逻辑 |
|-------|---------|------|---------|
| **RiskWarningAgent** | 作品创建/更新时 | 运行 4 维风险检测 | 提示词检测 → 参考图检测 → LoRA 检查 → 商标碰撞 → 写入 RiskWarning |
| **EnforcementAgent** | monitor_results 状态变为 confirmed | 启动维权流水线 | 构建证据包 → 选择投诉模板 → 提交投诉 → 追踪状态 → 写入 EnforcementAction |
| **InnocenceProofAgent** | 收到 incoming_complaint 事件 | 构建清白证据 | 收集创作证据 → 生成排除报告 → 生成 PDF 反证报告 → 写入 InnocenceProof |
| **NotaryAgent** | 用户触发存证 | 多平台存证 | 并行调用各平台 NotaryGateway → 汇总结果 → 写入 NotaryRecord |
| **MonitorAgent** | Celery Beat 定时调度 | 全网监测 | 按作品重要度选择频率 → 调用 SearchGateway → 写入 MonitorResult |

### 12.2 MCP 协议集成

系统通过 MCP (Model Context Protocol) 连接外部智能体服务：

| MCP 服务 | 用途 | 配置方式 |
|----------|------|---------|
| **Ollama** | 本地 AI 文案/风险检测 | `OLLAMA_HOST=http://localhost:11434` |
| **CNIPA Adapter** | 商标/专利查询 | CNIPA Gateway 适配器 |
| **Legal Knowledge Base** | 法律知识问答 | 本地向量数据库 + MCP |
| **Google Vision** | 图像分析 (参考图检测) | API Key 配置 |
| **TinEye** | 以图搜图 (侵权监测) | API Key 配置 |

### 12.3 Celery Beat 定时任务

| 任务 | 调度 | 说明 |
|------|------|------|
| `monitor_task` | 按作品重要度 (日/3天/月) | 全网侵权监测 |
| `notary_batch_task` | 手动触发 | 批量存证 |
| `enforcement_followup` | 每日 | 检查未解决的维权行动 |
| `risk_warning_batch` | 手动触发 | 批量风险预警 |
| `work_priority_recalc` | 每周 | 重新计算作品重要度 |
| `backup_task` | 每日/每周/每月 | 自动备份 |
| `cleanup_recycle_bin` | 每日 | 清理回收站过期文件 |
