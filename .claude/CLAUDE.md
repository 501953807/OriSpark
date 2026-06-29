<!-- OMC:START -->
<!-- OMC:VERSION:4.14.6 -->

# oh-my-claudecode - Intelligent Multi-Agent Orchestration

You are running with oh-my-claudecode (OMC), a multi-agent orchestration layer for Claude Code.
Coordinate specialized agents, tools, and skills so work is completed accurately and efficiently.

<operating_principles>
- Delegate specialized work to the most appropriate agent.
- Prefer evidence over assumptions: verify outcomes before claims.
- Choose the lightest-weight path that preserves quality.
- Consult official docs before implementing with SDKs/frameworks/APIs.
</operating_principles>

<delegation_rules>
Delegate for: multi-file changes, refactors, debugging, reviews, planning, research, verification.
Work directly for: trivial ops, small clarifications, single commands.
Route code to `executor` (use `model=opus` for complex work). Uncertain SDK usage → `document-specialist` (repo docs first; Context Hub / `chub` when available, graceful web fallback otherwise).
</delegation_rules>

<model_routing>
`haiku` (quick lookups), `sonnet` (standard), `opus` (architecture, deep analysis).
Direct writes OK for: `~/.claude/**`, `.omc/**`, `.claude/**`, `CLAUDE.md`, `AGENTS.md`.
</model_routing>

<skills>
Invoke via `/oh-my-claudecode:<name>`. Trigger patterns auto-detect keywords.
Tier-0 workflows include `autopilot`, `ultrawork`, `ralph`, `team`, and `ralplan`.
Keyword triggers: `"autopilot"→autopilot`, `"ralph"→ralph`, `"ulw"→ultrawork`, `"ccg"→ccg`, `"ralplan"→ralplan`, `"deep interview"→deep-interview`, `"deslop"`/`"anti-slop"`→ai-slop-cleaner, `"deep-analyze"`→analysis mode, `"tdd"`→TDD mode, `"deepsearch"`→codebase search, `"ultrathink"`→deep reasoning, `"cancelomc"`→cancel.
Team orchestration is explicit via `/team`.
</skills>

<verification>
Verify before claiming completion. Size appropriately: small→haiku, standard→sonnet, large/security→opus.
If verification fails, keep iterating.
</verification>

<execution_protocols>
Broad requests: explore first, then plan. 2+ independent tasks in parallel. `run_in_background` for builds/tests.
Keep authoring and review as separate passes: writer pass creates or revises content, reviewer/verifier pass evaluates it later in a separate lane.
Never self-approve in the same active context; use `code-reviewer` or `verifier` for the approval pass.
Before concluding: zero pending tasks, tests passing, verifier evidence collected.
</execution_protocols>

<hooks_and_context>
Hooks inject `<system-reminder>` tags. Key patterns: `hook success: Success` (proceed), `[MAGIC KEYWORD: ...]` (invoke skill), `The boulder never stops` (ralph/ultrawork active).
Persistence: `<remember>` (7 days), `<remember priority>` (permanent).
Kill switches: `DISABLE_OMC`, `OMC_SKIP_HOOKS` (comma-separated).
</hooks_and_context>

<cancellation>
`/oh-my-claudecode:cancel` ends execution modes. Cancel when done+verified or blocked. Don't cancel if work incomplete.
</cancellation>

<worktree_paths>
State: `.omc/state/`, `.omc/state/sessions/{sessionId}/`, `.omc/notepad.md`, `.omc/project-memory.json`, `.omc/plans/`, `.omc/research/`, `.omc/logs/`
</worktree_paths>

## Setup

Say "setup omc" or run `/oh-my-claudecode:omc-setup`.

<!-- OMC:END -->

---

# OriStudio 项目文档

## 文档结构

```
docs/
├── DESIGN.md          # 系统设计总纲 — 产品定位、需求范围、版本路线图、模块全景、API/模型统计
├── UX.md              # UX 交互设计规范 — Onboarding、空状态、术语优化、交互规范
├── ARCHITECTURE.md    # 技术架构 — 可行性评估、架构图链接、实施计划
├── modules-v3/        # 7 个模块详细设计 (5000+ 行)
│   ├── README.md      # 模块索引 + 端点统计
│   ├── 01-creative-assets.md
│   ├── 02-rights-protection.md
│   ├── 03-ip-registration.md
│   ├── 04-monetization-engine.md
│   ├── 05-content-distribution.md
│   ├── 06-business-management.md
│   └── 07-system-infra.md
└── .archive/          # 过期文档（历史参考，已被 DESIGN.md 等合并）
```

## 知识图谱 (Understand Anything)

```
.understand-anything/
├── knowledge-graph.json     # 最终知识图谱 (1537 节点, 2063 边)
├── config.json              # 配置 (outputLanguage: zh)
└── intermediate/
    ├── assembled-graph.json # 组装后的图谱（与 knowledge-graph.json 相同）
    ├── layers.json          # 11 个架构层
    └── tour.json            # 14 步引导学习之旅
```

**知识图谱状态**：
- 1537 节点（366 file, 699 function, 232 class, 144 config, 88 document, 4 service, 4 schema）
- 2063 边（930 contains, 724 exports, 278 imports, 49 depends_on, 57 documents, 14 tested_by）
- 11 个架构层：API Layer, Service Layer, Data Model Layer, Backend Foundation, UI Component Layer, State Management Layer, Frontend Types & API, Test Layer, Infrastructure, Documentation, Configuration
- 14 步中文引导学习之旅

**启动 Dashboard**：`/understand-dashboard`

## 开发流程

1. **修改代码前**：查阅 `docs/DESIGN.md` 了解模块定位，`docs/modules-v3/` 了解详细设计
2. **新增功能**：确认是否属于 v1 范围（插画师/AIGC），非 v1 功能标注"规划中"
3. **遵循代码为准**：API 端点 334+ 个、数据模型 102+ 个，以实际代码为准
4. **UPL 合规**：7 项免责声明、CNIPA 律师审核步骤不可绕过

## 文档管理规范

### 基本原则
1. **禁止新建文档**：所有变更必须整合到现有文档体系 (DESIGN.md / ARCHITECTURE.md / modules-v3/)
2. **三大架构图同步更新**：每次文档更新必须同步更新业务架构图、技术架构图、功能架构图
3. **模块设计可开发程度**：每个模块设计必须细化到数据模型 SQL + API 端点表 + 前端组件规格 + 状态机/流程图
4. **命名一致性**：模块更名 (权利保护→权益保护、商业转化→商业撮合) 必须贯穿所有文档
5. **版本控制**：每个模块文档顶部标注版本号 + 最后更新日期 + 变更摘要

### 文档更新检查清单
- [ ] 三大架构图是否已同步更新
- [ ] 数据模型 SQL 是否完整 (含 CREATE TABLE + 字段说明 + 索引)
- [ ] API 端点表是否完整 (方法 + 路径 + 请求体 + 响应 + 说明)
- [ ] 前端组件规格是否完整 (组件名 + Props + Events)
- [ ] v1/v2/v3/v4 版本边界是否清晰标注
- [ ] 模块命名是否一致 (权益保护/商业撮合等)
- [ ] 上下游数据流是否已更新
- [ ] 免责声明是否已嵌入相关流程

### 国际大公司文档标准参照
- 模块设计达到可开发测试程度 (类似 Atlassian Confluence 规范)
- 架构图采用 ASCII 设计图形式 (类似 Google SRE 文档)
- 状态机/流程序列图 (类似 Stripe API 文档)
- 版本路线图 (类似 Microsoft Azure 产品路线图)
