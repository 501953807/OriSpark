# 01 — 数据库Schema修复与基础表创建

**What to build:** 确保SQLite数据库与ORM模型完全同步，创建所有缺失的表和列，为后续数据注入提供坚实基础。

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

## 背景
当前数据库schema与代码模型不同步：
- users表缺少：bio, login_platform, participant_roles等列
- works表缺少：creator_id, import_mode等列
- 部分表根本不存在（如contract_instances, split_rules）

## 验收标准
- [ ] `python3 -c "from app.database import Base; from sqlalchemy import inspect; i=inspect(engine); print(f'Tables: {len(i.get_table_names())}')"` 输出表数量≥50
- [ ] users表包含所有ORM定义的列（通过`SELECT sql FROM sqlite_master WHERE type='table' AND name='users'`验证）
- [ ] works表包含creator_id和import_mode列
- [ ] contract_instances, split_rules, notary_records等关键表存在
- [ ] 运行`alembic check`无版本冲突
- [ ] 现有测试2014 passed不受影响

## 技术说明
- 使用`Base.metadata.create_all(engine)`创建缺失表
- 使用`ALTER TABLE ... ADD COLUMN`添加缺失列
- 不要删除现有数据（如有）
