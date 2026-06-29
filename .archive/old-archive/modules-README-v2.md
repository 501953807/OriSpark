# OriStudio 模块功能详细设计

> **当前版本**: v3 (Stage 2 修订) | **最后更新**: 2026-06-12 | **设计文档**: docs/modules-v3/

## 版本说明

本文档已升级为 v3 Stage 2 修订版。**v1 聚焦插画师/AIGC 艺术家**，其他创作者类型(摄影师/视频/手工/音乐/文字)标注为"规划中"。

**v3 设计文档目录**: `docs/modules-v3/`

---

## 设计原则

1. **v1聚焦插画师** — 做深做透单一创作者类型的完整工作流
2. **诚实声明能力边界** — 每个功能标注创作者类型适用范围
3. **UPL法律合规** — 7项免责声明 + 多分类推荐 + CNIPA律师步骤
4. **文档以代码为准** — 232端点、49模型
5. **不重复造轮子** — 对接成熟平台和标准协议

---

## 一、模块全景图

```
┌──────────────────────────────────────────────────────────────┐
│                     OriStudio v3                              │
│                                                              │
│  创作完成 → [1]创意资产中心 → 资产管理+自动元数据+版本         │
│                 │          │          │                       │
│                 ▼          ▼          ▼                       │
│            [2]权利保护  [4]商业转化  [5]内容分发               │
│            存证+维权    IP→产品→收入  多平台推广               │
│                 │          │          │                       │
│                 └──────────┼──────────┘                       │
│                            ▼                                  │
│                       [6]经营管理中心                          │
│                      收入+伙伴+通知+分析                       │
│                            │                                  │
│                       [7]系统基础设施                          │
│                      字典+认证+备份+Onboarding                 │
│                                                              │
│  [3] IP登记工作站 ← 贯穿全流程: 版权/商标/外观/专利信息参考    │
└──────────────────────────────────────────────────────────────┘
```

---

## 二、创作者类型支持矩阵

| 创作者类型 | v1 (当前) | v2 (规划) | v3+ (愿景) |
|-----------|-----------|-----------|------------|
| **插画师/AIGC艺术家** | ✅ 完整支持 | ✅ 持续增强 | ✅ 持续增强 |
| **摄影师** | 🔵 基础导入 | ✅ 完整支持 | ✅ 持续增强 |
| **短视频/动画** | 🔵 基础导入 | 🔵 增强导入 | ⏳ 完整支持 |
| **手工艺人** | 🔵 基础导入 | 🔵 增强导入 | ⏳ 完整支持 |
| **音乐人** | 🔵 基础导入 | 🔬 研究阶段 | ⏳ 完整支持 |
| **文字作者** | 🔵 基础导入 | 🔬 研究阶段 | ⏳ 完整支持 |

---

## 三、模块设计文档清单

| 编号 | 模块 | v3设计文档 | 定位 |
|------|------|-----------|------|
| 1 | 创意资产中心 | [01-creative-assets.md](../modules-v3/01-creative-assets.md) (300+行) | 图片资产统一管理，自动元数据+批量导入 |
| 2 | 权利保护中心 | [02-rights-protection.md](../modules-v3/02-rights-protection.md) (220+行) | 存证+侵权监测一体化，C2PA诚实边界说明 |
| 3 | IP登记工作站 | [03-ip-registration.md](../modules-v3/03-ip-registration.md) (350+行) | 信息参考工具，多分类推荐+律师审核，7项免责 |
| 4 | 商业转化引擎 | [04-monetization-engine.md](../modules-v3/04-monetization-engine.md) (350+行) | POD渠道管理，三层预览，规格校验+定价计算 |
| 5 | 内容分发中心 | [05-content-distribution.md](../modules-v3/05-content-distribution.md) (300+行) | 16平台列表(8完整+8规划中)，AI文案+影响力 |
| 6 | 经营管理中心 | [06-business-management.md](../modules-v3/06-business-management.md) (220+行) | 收入CSV导入+空状态设计+Partner/Order已确认 |
| 7 | 系统基础设施 | [07-system-infra.md](../modules-v3/07-system-infra.md) (280+行) | Onboarding+大文件存储+免责声明管理机制 |

---

## 四、模块间完整数据流

### 创意资产中心 → 各模块

| 输出字段 | → 权利保护 | → 商业转化 | → 内容分发 | → IP登记 |
|----------|-----------|-----------|-----------|----------|
| work.id | 存证对象ID | 产品设计来源 | 发布内容溯源 | 预填关联 |
| work.sha256 | 存证核心数据 | — | — | 补充材料 |
| work.thumbnail_url | 证书缩略图 | 设计稿预览 | 配图 | — |
| work.title | 证书标题 | 产品标题建议 | 文案输入 | 申请表预填 |
| work.file_path | 扫描源 | 效果图设计稿 | 发布原图 | — |
| work.rights | 权利引用 | 许可来源 | 署名/水印 | 权利人预填 |
| work.tags | — | 品类推荐 | 话题标签 | 类别推荐 |
| work.synopsis | — | 产品描述 | 文案输入 | 创作说明书 |

### 商业转化引擎 → 内容分发中心

| 输出字段 | 用途 |
|----------|------|
| product.id + 效果图路径 | 产品推广素材 |
| product.title + price | 定价信息展示 |
| product.description | AI文案输入 |

### 权利保护中心 → 商业转化/内容分发

| 输出字段 | 用途 |
|----------|------|
| certificate.id + qr_code | Verified徽章 |
| evidence_package | 维权证据(转化线索) |

---

## 五、全局 API 端点统计 (以代码为准)

| 模块 | 端点数 | 路由文件 |
|------|--------|----------|
| [1] 创意资产中心 | 32 | works.py(18) + batch_works.py(6) + versions.py(8) |
| [2] 权利保护中心 | 49 | notary.py(18) + monitor.py(31) |
| [3] IP登记工作站 | 24 | ipr.py(24) |
| [4] 商业转化引擎 | 42 | supply.py(42) |
| [5] 内容分发中心 | 17 | publish.py(17) |
| [6] 经营管理中心 | 2 | dashboard.py(2) |
| [7] 系统基础设施 | 66 | system.py(50) + auth.py(14) + ws(1) + main(1) |
| **总计** | **232** | 13个路由文件 |

> 注: 经营管理中心的收入/合作伙伴/订单/通知端点物理上位于 supply.py(42) 中。

---

## 六、全局数据模型索引 (以代码为准)

| 模型文件 | 模型数 | 模型类 |
|----------|--------|--------|
| app/models/work.py | 4 | Work, WorkVersion, WorkTag, Project |
| app/models/system.py | 11 | SystemSetting, AuditLog, BackupRecord, DictionaryGroup, DictionaryItem, User, UserLoginHistory, Notification, Plugin, EmailVerification, PasswordReset |
| app/models/supply.py | 6 | Partner, PartnerQualification, Order, OrderPayment, OrderCommunication, Reminder |
| app/models/publish.py | 4 | Product, ProductPublishing, VerifiedMark, RevenueRecord |
| app/models/monitor.py | 4 | MonitorTask, MonitorResult, EvidencePackage, ScanSchedule |
| app/models/monitor_ext.py | 5 | LocalFingerprint, BrandWatch, BrandScanResult, DomainWatch, WhitelistSuggestion |
| app/models/ipr.py | 7 | IPRegistration, TrademarkClass, CopyrightRegistration, TrademarkRegistration, TrademarkMonitoring, ApplicationTemplate, NiceClassification |
| app/models/notary.py | 4 | NotaryRecord, Certificate, C2PARecord, NotaryAuditTrail |
| app/models/monetization.py | 4 | ProductTemplate, MonetizationChannel, Campaign, License |
| **合计** | **49** | 9个模型文件 |

> 注: Partner/Order/OrderPayment 模型已确认存在于 supply.py 中。

---

## 七、v2 → v3 核心变化

| v2模块 | v3模块 | 变化 |
|--------|--------|------|
| 作品管理 | 创意资产中心 | 扩大: 自动元数据提取+批量导入+存证状态优化 |
| 存证确权+侵权监测 | 权利保护中心 | 合并: 存证维权一体化 + C2PA诚实边界 + 侵权监测免责 |
| IP登记 | IP登记工作站 | UPL合规改造: 多分类推荐+置信度+律师审核+7项免责 |
| 供应链 | 商业转化引擎 | 重构: POD渠道管理(诚实声明)+三层预览方案+规格定价 |
| 发布变现 | 内容分发中心 | 重构: 平台列表补全+Onboarding预设 |
| (无) | 经营管理中心 | 新增: 收入CSV导入+空状态设计+Partner/Order确认 |
| 系统管理 | 系统基础设施 | 增强: Onboarding持久化+大文件存储+免责声明管理 |

---

## 八、实施计划

详见: [OriStudio-完整实施计划.md](../OriStudio-完整实施计划.md)

基于 Stage 2 修订重规划为 4 Phase:
1. **Phase 0** (P0): 合规修复 — 7项免责声明、IP登记合规、创作者类型选择器
2. **Phase 1** (P0): 核心能力 — 自动元数据、批量导入、POD渠道管理、Canvas三层预览
3. **Phase 2** (P1): 用户体验 — Onboarding、空状态、术语优化、视觉调整
4. **Phase 3** (P2): 文档同步 — API/模型统计修正、模块边界调整

## 九、相关文档

| 文档 | 说明 |
|------|------|
| [最终需求文档](../requirements-v3-final.md) | v1聚焦插画师，POD诚实声明，UPL合规，功能需求清单 |
| [系统总纲](../master-design-v3.md) | 模块全景、232端点、49模型、创作者类型矩阵 |
| [PM启动报告](../pm-startup-report.md) | P0/P1/P2问题清单、任务分配矩阵、8个关键决策点 |
| [UX设计规范](../ux-design-spec.md) | Onboarding 3步向导、10空状态、9术语优化、移动端适配 |
| [多角色评估报告](../agent-evaluation-report.md) | 9角色独立评估，问题来源追溯 |
