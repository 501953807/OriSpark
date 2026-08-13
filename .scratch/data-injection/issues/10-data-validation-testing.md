# 10 — 数据验证与测试回归

**What to build:** 验证注入数据的完整性，确保所有测试通过，无回归。

**Blocked by:** 04-works-upload-management, 05-rights-protection, 06-contract-trading, 07-writer-specific-features

**Status:** ready-for-agent

## 背景
数据注入完成后需要验证完整性和测试回归。

## 验证查询
```sql
-- 基础数据量
SELECT COUNT(*) FROM users;  -- 应为48
SELECT COUNT(*) FROM works;  -- 应为150
SELECT COUNT(*) FROM books;  -- 应为5
SELECT COUNT(*) FROM contracts; -- 应为10

-- 按类型统计
SELECT creator_type, COUNT(*) FROM users GROUP BY creator_type;
SELECT creator_type, COUNT(*) FROM works GROUP BY creator_type;
```

## 验收标准
- [ ] 用户数=48（6类型×5 + 7角色×3）
- [ ] 作品数=150（6类型×5账号×5作品）
- [ ] 书籍数=5（文字作者）
- [ ] 合约数=10
- [ ] 所有后端测试2014 passed
- [ ] 前端测试209 passed
- [ ] TypeScript 0 errors
- [ ] 构建通过（frontend-web + frontend-nuxt）
- [ ] 无新增warning

## 回归测试命令
```bash
cd backend && python3 -m pytest tests/ --tb=short -q
cd frontend-web && npm run test
npx vue-tsc --noEmit
npm run build
```
