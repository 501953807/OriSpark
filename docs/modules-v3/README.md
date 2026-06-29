# OriStudio v3 模块功能设计索引

> **版本**: v3 | **日期**: 2026-06-12 | **基于**: `docs/requirements-v3-final.md`
> **v1 定位**: 聚焦插画师/AIGC艺术家，其他创作者类型标注"规划中"

---

## 设计文档

| 编号 | 模块 | 文件 | 行数 | 状态 | v1支持范围 |
|------|------|------|------|------|-----------|
| 1 | 创意资产中心 | [01-creative-assets.md](01-creative-assets.md) | 1300+ | ✅ 已验证 | 图片完整支持，其他基础导入，视频缩略图30%已实现 |
| 2 | 权利保护中心 | [02-rights-protection.md](02-rights-protection.md) | 450+ | ✅ 已验证 | 存证+监测完整支持，C2PA v1不实现 |
| 3 | IP登记工作站 | [03-ip-registration.md](03-ip-registration.md) | 350+ | ✅ 已验证 | 多推荐+置信度已实现，lawyer_consulted+免责声明API已添加 |
| 4 | 商业转化引擎 | [04-monetization-engine.md](04-monetization-engine.md) | 1370+ | ✅ 已验证 | POD渠道管理+Canvas预览，Printful Mockup端点已添加 |
| 5 | 内容分发中心 | [05-content-distribution.md](05-content-distribution.md) | 630+ | ✅ 已验证 | 平台列表，AI文案引擎已实现 |
| 6 | 经营管理中心 | [06-business-management.md](06-business-management.md) | 490+ | ✅ 已验证 | 空状态+CSV导入，Partner/Order模型已实现 |
| 7 | 系统基础设施 | [07-system-infra.md](07-system-infra.md) | 300+ | 🔧 修订中 | Onboarding API+creator_type+免责声明表已添加 |
| **合计** | | | **5000+** | | |

## 其他设计文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 最终需求文档 | [../requirements-v3-final.md](../requirements-v3-final.md) | v1聚焦插画师，POD诚实声明，UPL合规 |
| 原始需求分析 | [../requirements-v3-full.md](../requirements-v3-full.md) | 6类创作者完整需求分析 (365行) |
| 系统总纲 | [../master-design-v3.md](../master-design-v3.md) | 模块全景、232端点、49模型、创作者类型矩阵 |
| 模块索引 | [../modules/README.md](../modules/README.md) | 模块间数据流、API统计、模型索引 |
| PM启动报告 | [../pm-startup-report.md](../pm-startup-report.md) | P0/P1/P2问题清单、任务分配矩阵、8个关键决策点 |
| UX设计规范 | [../ux-design-spec.md](../ux-design-spec.md) | Onboarding 3步向导、10空状态、9术语优化、移动端适配 |
| 实施计划 | [../OriStudio-完整实施计划.md](../OriStudio-完整实施计划.md) | 4 Phase 重规划 |
| 建设方案 | [../OriStudio-完整建设方案.html](../OriStudio-完整建设方案.html) | 完整HTML建设方案 (待更新) |
| 功能架构图 | [../OriStudio-功能架构图.html](../OriStudio-功能架构图.html) | SVG架构图 (待更新) |
| 技术架构图 | [../OriStudio-技术架构图.html](../OriStudio-技术架构图.html) | SVG架构图 (待更新) |
| 多角色评估报告 | [../agent-evaluation-report.md](../agent-evaluation-report.md) | 9角色独立评估 |
| 用户手册 | [../用户手册.md](../用户手册.md) | 用户操作指南 |

## 关键设计决策 (Stage 2 已确认)

1. **v1聚焦插画师** — 非插画类型专属功能标注"规划中"，基础导入可用
2. **POD渠道管理** — 重命名自"POD对接"，明确手动上架+URL记录
3. **Canvas三层方案** — 默认扁平叠加 / Printful Mockup API增强 / PSD模板规划
4. **UPL合规** — 7项免责声明 + 尼斯多推荐+置信度 + CNIPA律师审核步骤(不可绕过)
5. **文档以代码为准** — 232端点、49模型

## API端点统计 (以代码实际为准)

| 模块 | 端点数 |
|------|--------|
| [1] 创意资产中心 | 32 (works 18 + batch_works 6 + versions 8) |
| [2] 权利保护中心 | 49 (notary 18 + monitor 31) |
| [3] IP登记工作站 | 24 |
| [4] 商业转化引擎 | 42 |
| [5] 内容分发中心 | 17 |
| [6] 经营管理中心 | 2 (dashboard) |
| [7] 系统基础设施 | 66 (system 50 + auth 14 + ws 1 + main 1) |
| **总计** | **232** |
