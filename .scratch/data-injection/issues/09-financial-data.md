# 09 — 财务数据：发票+委托项目+收入追踪

**What to build:** 创建发票、委托项目和收入记录，支撑财务流转演示。

**Blocked by:** 06-contract-trading

**Status:** ready-for-agent

## 背景
财务数据是商业撮合的自然延伸，需要发票和收入追踪支撑。

## 数据规模
- 发票：5张（关联合约成交）
- 委托项目：8个（创作者与运营方的合作）
- 收入记录：20条（多渠道收入汇总）

## 验收标准
- [ ] 发票包含invoice_number、amount_yuan、status
- [ ] 委托项目包含payment_terms（里程碑付款）
- [ ] 收入记录按渠道分类（合约/委托/其他）
- [ ] 发票状态可更新（pending→paid）

## API端点
- POST /api/invoice — 创建发票
- POST /api/commission/projects — 创建委托项目
- GET /api/revenue/summary — 收入汇总
