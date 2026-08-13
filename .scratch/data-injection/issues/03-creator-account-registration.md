# 03 — 创作者账号注册与Onboarding

**What to build:** 通过API创建48个用户账号（6种创作者×5 + 7种角色×3），完成Onboarding流程。

**Blocked by:** 01-database-schema-fix, 02-media-file-generator

**Status:** ready-for-agent

## 背景
系统需要多角色用户支撑完整业务链测试。

## 用户矩阵
| 类型 | 数量 | 账号示例 | 关键属性 |
|-----|------|---------|---------|
| illustrator | 5 | 插画师_1~5 | creator_type="illustrator" |
| photographer | 5 | 摄影师_1~5 | creator_type="photographer" |
| video_creator | 5 | 视频创作者_1~5 | creator_type="video_creator" |
| crafter | 5 | 手工艺人_1~5 | creator_type="crafter" |
| musician | 5 | 音乐人_1~5 | creator_type="musician" |
| writer | 5 | 文字作者_1~5 | creator_type="writer" |
| operator | 3 | 运营方_1~3 | participant_roles=["operator"] |
| legal_rep | 3 | 法务代表_1~3 | participant_roles=["legal_rep"] |
| tax_agent | 3 | 税务代理_1~3 | participant_roles=["tax_agent"] |
| logistics | 3 | 物流方_1~3 | participant_roles=["logistics"] |
| insurer | 3 | 保险方_1~3 | participant_roles=["insurer"] |
| trader | 3 | 采购方_1~3 | participant_roles=["trader"] |

## 验收标准
- [ ] 通过POST /api/auth/register创建创作者账号
- [ ] 通过POST /api/auth/complete-onboarding完成Onboarding
- [ ] 创作者账号creator_type正确设置
- [ ] 非创作者账号participant_roles正确设置
- [ ] 总计48个用户全部创建成功
- [ ] 每个用户可成功登录并获取token
- [ ] GET /api/auth/me返回正确的用户信息

## API端点
- POST /api/auth/register
- POST /api/auth/register/creator
- POST /api/auth/complete-onboarding
- POST /api/auth/login
- GET /api/auth/me
