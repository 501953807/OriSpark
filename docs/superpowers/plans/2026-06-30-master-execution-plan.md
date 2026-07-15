# OriStudio 全版本功能实施总计划

> **Goal:** 按版本顺序完成摄影师(v2)、视频(v3a)、手工(v3b)、音乐(v4a)、文字(v4b)全部创作者类型的功能实现
> **Architecture:** 每个版本独立实施，从后端模型→API→Store→API→视图→组件的顺序
> **Tech Stack:** Vue 3 + TypeScript + Pinia + Vite (FE), FastAPI + SQLAlchemy + PostgreSQL (BE)

## 实施顺序

```
Phase 1: 商单工作流 (跨版本，最高优先级)
    ↓
Phase 2: v2 摄影师
    ↓
Phase 3: v3a 视频创作者 + 视频指纹
    ↓
Phase 4: v3b 手工艺人
    ↓
Phase 5: v4a 音乐人
    ↓
Phase 6: v4b 文字作者
    ↓
Phase 7: 创作者类型系统完善 (切换器 + 动态菜单)
```

## 详细计划文档

每个 Phase 有独立的详细计划文档：

1. [商单工作流](./2026-06-30-commission-workflow.md) — Task 1-6，~5天
2. [摄影师 v2](./2026-06-30-photographer-v2.md) — Task 1-5，~5天
3. [视频 v3a](./2026-06-30-video-v3a.md) — Task 1-3，~4天
4. [手工艺人 v3b](./2026-06-30-craftsman-v3b.md) — Task 1-4，~5天
5. [音乐人 v4a](./2026-06-30-musician-v4a.md) — Task 1-3，~4天
6. [文字作者 v4b](./2026-06-30-writer-v4b.md) — Task 1-3，~4天
7. 创作者类型系统 — 路由/侧边栏/Onboarding 适配，~2天

**总计: ~29天 (约6周)**

## 前置条件

- v1 功能必须保持正常 (不得破坏现有插画师/AIGC 功能)
- 所有新模型需要 Alembic 迁移
- 需要申请的第三方 API 账号提前准备:
  - 500px Developer (摄影师)
  - 图虫 Developer (摄影师)
  - Etsy Developer (手工艺人)
  - DistroKid/TuneCore API (音乐人)
  - Turnitin/Grammarly API (文字作者)
  - B站/抖音/YouTube API (视频创作者)

## 风险缓解

- ffmpeg/libraw 等系统依赖通过 Docker 镜像预装
- 第三方 API 未获批前，使用 Mock 服务替代
- 每个 Phase 独立部署测试，互不影响
