# 06 — 商业撮合：合约挂牌与交易

**What to build:** 创建10个合约实例，演示完整的合约生命周期（draft→listed→subscribed→escrowed→completed）。

**Blocked by:** 04-works-upload-management

**Status:** ready-for-agent

## 背景
合约市场是OriSpark交易后台的核心功能，需要演示完整的交易流程。

## 合约状态分布
| 状态 | 数量 | 说明 |
|-----|------|------|
| listed | 3 | 已挂牌待认购 |
| active | 2 | 交易中 |
| subscribed | 2 | 已认购待托管 |
| escrowed | 1 | 资金托管中 |
| insured | 1 | 已承保 |
| completed | 1 | 已完成 |

## 分润规则
每个合约包含4条SplitRule：
- creator: 70%
- operator: 15%
- legal_rep: 5%
- tax_agent: 5%

## 验收标准
- [ ] 10个合约实例全部创建成功
- [ ] 每个合约关联一个work_id和creator_id
- [ ] 合约状态符合状态机定义
- [ ] 分润规则percentage总和=1.0
- [ ] 合约列表按状态筛选正常
- [ ] 合约时间线查询正常

## API端点
- POST /api/contract — 创建合约
- GET /api/contract — 列表查询
- GET /api/contract/{id} — 详情
- POST /api/contract/{id}/publish — 挂牌
- POST /api/contract/{id}/subscribe — 认购
- POST /api/contract/{id}/escrow/initiate — 托管
- POST /api/contract/{id}/complete — 完成
