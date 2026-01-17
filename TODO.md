# research-devflow 架构设计 & 实施计划

> 恢复上下文: 本项目是 Claude Code 插件，目标是将开发流程各环节抽象为 skill 工具，通过知识沉淀提高团队效率。
> 当前状态: 已完成所有核心 skill，正在优化执行流程。

## 决策记录 (已确认)

### Checkpoint 1: 知识沉淀架构 ✓
按 skill 类型分目录:
```
.claude/
├── shared_files/     # research 任务上下文
├── postmortem/       # 事故复盘
├── adr/              # 架构决策记录 (future)
├── reviews/          # 代码审查记录 (future)
└── ...
```

### Checkpoint 2: AI 检索机制 ✓
- 统一 meta schema
- 触发时机由各 skill 定义
- 使用 `rg`/`grep`/`ast-grep` 全文检索

### Checkpoint 3: 团队协作流程
**状态**: TODO - 后续讨论

### Checkpoint 4: 工具集成 ✓
- 定位: 工作流调度中心，将工程维护信息结构化
- 触发: 先手动调用，CI hook 后续按环境配置

---

## 统一 Meta Schema (已确认)

所有 skill 产出文档使用统一的 YAML frontmatter:

```yaml
---
# === 基础信息 ===
type: postmortem | task | adr | review | tech-debt | ...
id: "yymmdd-short-description"
created_at: "2025-01-13"
updated_at: "2025-01-13"
status: active | archived | deprecated
author: "username"

# === 影响范围 (AI 检索核心) ===
scope:
  modules: ["src/auth/", "src/middleware/"]
  functions: ["validateToken", "refreshAuth"]
  files: ["src/auth/**/*.ts"]
  apis: ["POST /api/auth/*"]
  tables: ["user_sessions"]

# === 语义匹配 ===
keywords: [token, auth, session, JWT]

# === 相关性判断 ===
relevance:
  must_read: ["修改认证逻辑时"]
  consider: ["添加新 API 端点时"]
  skip_if: ["仅修改 UI"]

# === 关联引用 ===
refs:
  jira: "PROJ-1234"
  commits: ["abc1234"]
  related: ["250110-another-issue"]

# === Skill 特有字段 (按类型扩展) ===
# postmortem 特有:
severity: P1
category: security
root_cause:
  type: race_condition
  pattern: "..."

# adr 特有:
decision_status: proposed | accepted | deprecated
supersedes: "yymmdd-old-adr"
---
```

---

## 检索流程设计

```
┌─────────────────────────────────────────────────────┐
│  Skill 触发检索                                      │
│  (如: research 创建任务时, refactor 分析代码时)       │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│  Step 1: 确定检索范围                                │
│  - 当前任务涉及的 files/modules/functions            │
│  - 任务描述中的关键词                                │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│  Step 2: 扫描知识库                                  │
│  rg -l "scope:" .claude/*/                          │
│  提取所有文档的 frontmatter                          │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│  Step 3: 匹配计算                                    │
│  - scope 交集 → 高相关                               │
│  - keywords 交集 → 中相关                            │
│  - relevance.must_read 命中 → 必读                   │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│  Step 4: 输出结果                                    │
│  - 必读文档: 完整引用到 context                       │
│  - 参考文档: 列出链接                                │
└─────────────────────────────────────────────────────┘
```

---

## Skill 规划 (按优先级)

### 已完成 ✓
- [x] research - 任务拆解与并行开发
- [x] postmortem - 事故复盘
- [x] review - 代码审查辅助
- [x] tech-debt - 技术债务追踪
- [x] test-strategy - 测试策略生成
- [x] security-scan - 安全检查
- [x] dependency - 依赖管理
- [x] release - 发布管理
- [x] onboarding - 新人指南

### 规则库扩展 ✓
- [x] RULES-CODE-QUALITY.md - 通用规则 (16 条)
- [x] RULES-ANDROID.md - Android 规则 (18 条)
- [x] rule_query.py 支持多规则文件自动发现

### 待优化
| 任务 | 优先级 | 说明 |
|------|--------|------|
| Skill 脚本化封装 | P0 | 将文本 skill 封装为脚本，确保子任务按流程执行 |
| ADR 支持 | P1 | 架构决策记录 skill |
| Refactor 支持 | P1 | 重构分析 skill |
| CI 集成 | P2 | Git hooks / CI pipeline 自动触发 |

---

## 实施任务清单

### Phase 0: 基础设施 ✓

#### P0.1 统一现有 skill 的 meta 格式 ✓
- [x] 更新 `postmortem/SKILL.md` 的报告模板，使用统一 schema
- [x] 更新 `research/SKILL.md` 的 task-status.json，添加 meta 字段
- [x] 创建 `docs/META-SCHEMA.md` 文档说明

#### P0.2 创建检索工具函数 ✓
- [x] 创建 `scripts/rule_query.py` 规则查询工具
- [x] 支持多规则文件自动发现

---

### Phase 1: 开发核心流程 Skills ✓

- [x] P1.1 Review (代码审查辅助)
- [ ] P1.2 ADR (架构决策记录) - 待开发
- [ ] P1.3 Refactor (重构分析) - 待开发

---

### Phase 2: 质量保障 Skills ✓

- [x] P2.1 Tech-Debt (技术债务追踪)
- [x] P2.2 Test-Strategy (测试策略)
- [x] P2.3 Security-Scan (安全检查)

---

### Phase 3: 持续改进 Skills ✓

- [x] P3.1 Dependency (依赖管理)
- [x] P3.2 Release (发布管理)
- [x] P3.3 Onboarding (新人指南)

---

### Phase 4: 执行流程优化 (当前)

#### P4.1 Skill 脚本化封装 (P0 优先级)
**目标**: 将文本 skill 封装为脚本调用各个步骤，确保子任务按流程执行

**问题**: 当前 skill 以 Markdown 文本形式定义，依赖 LLM 理解和执行，存在：
- 步骤可能被跳过或乱序执行
- 缺乏强制性的 gate check
- 无法程序化追踪执行进度

**方案设计**:
```
scripts/
├── skill-runner.py          # 统一 skill 执行器
├── skills/
│   ├── research.py           # research skill 脚本化
│   ├── review.py             # review skill 脚本化
│   ├── postmortem.py         # postmortem skill 脚本化
│   └── ...
└── lib/
    ├── step_executor.py      # 步骤执行器
    ├── gate_checker.py       # Gate check 验证
    └── context_manager.py    # 上下文管理
```

**执行流程**:
```
/skill <name> <args>
      │
      ▼
skill-runner.py
      │
      ├── 1. 加载 skill 定义
      ├── 2. 初始化上下文
      ├── 3. 按序执行步骤
      │      ├── Step N: 执行
      │      ├── Gate Check: 验证
      │      └── 失败则中断
      └── 4. 输出结果
```

**待实现**:
- [ ] 设计 skill 脚本接口规范
- [ ] 实现 skill-runner.py 核心框架
- [ ] 迁移 research skill 作为 MVP
- [ ] 迁移其他 skill

#### P4.2 CI 集成
- [ ] pre-commit hook 自动 review
- [ ] CI pipeline 集成 security-scan

---

## 任务进度追踪

```
恢复命令: 阅读此文件，继续未完成的任务
项目路径: /Users/yanyao/Projects/side/research-devflow
```

### 总体进度

| Phase | 状态 | 完成度 |
|-------|------|--------|
| Phase 0: 基础设施 | ✓ 完成 | 2/2 |
| Phase 1: 开发核心 | 部分完成 | 1/3 |
| Phase 2: 质量保障 | ✓ 完成 | 3/3 |
| Phase 3: 持续改进 | ✓ 完成 | 3/3 |
| Phase 4: 执行优化 | 进行中 | 0/2 |

### 下次继续点

**当前任务**: Phase 4 - P4.1 Skill 脚本化封装

**待执行**:
1. 设计 skill 脚本接口规范
2. 实现 skill-runner.py 核心框架
3. 迁移 research skill 作为 MVP

---

## 附录: 关键文件路径

```
项目根目录: /Users/yanyao/Projects/side/research-devflow

已有文件:
├── .claude-plugin/
│   ├── plugin.json (v1.2.1)
│   └── marketplace.json
├── commands/
│   ├── research.md
│   ├── postmortem.md
│   ├── review.md
│   ├── tech-debt.md
│   ├── test-strategy.md
│   ├── security-scan.md
│   ├── dependency.md
│   ├── release.md
│   └── onboarding.md
├── skills/
│   ├── research/
│   ├── postmortem/
│   ├── review/
│   ├── tech-debt/
│   ├── test-strategy/
│   ├── security-scan/
│   ├── dependency/
│   ├── release/
│   └── onboarding/
├── docs/
│   ├── META-SCHEMA.md
│   ├── RULES-CODE-QUALITY.md (16 条通用规则)
│   ├── RULES-ANDROID.md (18 条 Android 规则)
│   └── common-lsp.md
└── scripts/
    ├── setup-worktrees.sh
    ├── merge.sh
    ├── notify.sh
    └── rule_query.py

待创建 (Phase 4):
├── scripts/
│   ├── skill-runner.py
│   ├── skills/
│   │   ├── research.py
│   │   ├── review.py
│   │   └── ...
│   └── lib/
│       ├── step_executor.py
│       ├── gate_checker.py
│       └── context_manager.py
└── skills/
    ├── adr/SKILL.md
    └── refactor/SKILL.md
```
