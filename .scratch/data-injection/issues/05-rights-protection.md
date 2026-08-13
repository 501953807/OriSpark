# 05 — 权益保护：存证+监测+维权

**What to build:** 为已验证作品创建区块链存证，设置监测任务，模拟侵权发现与维权流程。

**Blocked by:** 04-works-upload-management

**Status:** ready-for-agent

## 背景
权益保护是OriStudio的核心价值主张，需要完整演示存证→监测→维权闭环。

## 数据规模
- 区块链存证：30个（works中is_verified=True的作品）
- 监测任务：20个（覆盖主要作品）
- 监测结果：30个（含侵权和误报）
- 维权行动：5个（从监测结果触发）
- 清白证明：10个

## 验收标准
- [ ] 存证记录包含platform（banquanjia/antchain/zhixinchain）
- [ ] 存证包含blockchain_tx_id和block_height
- [ ] 监测任务status为active/paused/completed
- [ ] 监测结果包含similarity（60-95分）
- [ ] 维权行动状态流转：pending_review→confirmed→resolved
- [ ] 清白证明可生成PDF报告
- [ ] 合约风险评估API正常工作

## API端点
- POST /api/notary/records — 创建存证
- POST /api/monitor/tasks — 创建监测任务
- GET /api/monitor/tasks/{id}/results — 查询结果
- POST /api/enforcement/actions — 创建维权行动
- POST /api/innocence-proofs — 生成清白证明
- POST /api/contract-risk/review — 合约风险评估
