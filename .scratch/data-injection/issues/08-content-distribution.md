# 08 — 内容分发：平台账号绑定

**What to build:** 为创作者绑定多平台社交账号，创建定时发布计划。

**Blocked by:** 03-creator-account-registration

**Status:** ready-for-agent

## 背景
内容分发是创作者扩大影响力的关键功能。

## 平台映射（根据creator_type）
| 创作者类型 | 默认平台 |
|-----------|---------|
| illustrator | xiaohongshu, zcool, bilibili |
| photographer | xiaohongshu, instagram, weibo |
| video_creator | bilibili, douyin, youtube |
| crafter | xiaohongshu, etsy, instagram |
| musician | bilibili, douyin, spotify |
| writer | wechat, xiaohongshu, qidian |

## 数据规模
- 平台账号：30个（平均每个创作者绑定1-2个平台）
- 分发计划：10个（含定时和重复发布）

## 验收标准
- [ ] 每个创作者类型有对应的平台账号绑定
- [ ] 平台账号包含account_name和follower_count
- [ ] 定时发布计划包含scheduled_at和is_recurring
- [ ] 平台账号列表按用户过滤正常

## API端点
- POST /api/content-pipeline/accounts — 绑定平台账号
- GET /api/content-pipeline/accounts — 账号列表
- POST /api/content-pipeline/schedules — 创建分发计划
- GET /api/content-pipeline/schedules — 计划列表
