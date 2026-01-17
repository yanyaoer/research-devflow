# research-devflow 架构设计 & 实施计划

> 恢复上下文: 本项目是 Claude Code 插件，目标是将开发流程各环节抽象为 skill 工具，通过知识沉淀提高团队效率。
> 当前状态: 已完成 research 和 postmortem skill，正在规划统一架构和后续 skill。

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

### 已完成
- [x] research - 任务拆解与并行开发
- [x] postmortem - 事故复盘

### 第一优先级: 开发核心流程
| Skill | 用途 | 触发检索 |
|-------|------|----------|
| **adr** | 架构决策记录 | 设计新功能时检索历史决策 |
| **review** | 代码审查辅助 | 审查时检索相关 postmortem/adr |
| **refactor** | 重构分析 | 分析影响范围，检索相关文档 |

### 第二优先级: 质量保障
| Skill | 用途 | 触发检索 |
|-------|------|----------|
| **tech-debt** | 技术债务追踪 | 新增债务时检索已有记录 |
| **test-strategy** | 测试策略生成 | 检索相关 postmortem 的复现步骤 |
| **security-scan** | 安全检查 | 检索安全类 postmortem |

### 第三优先级: 持续改进
| Skill | 用途 | 触发检索 |
|-------|------|----------|
| **dependency** | 依赖升级分析 | - |
| **release** | 发布 changelog | 聚合 commits 和相关文档 |
| **onboarding** | 上手指南生成 | 聚合项目所有文档 |

---

## 实施任务清单

### Phase 0: 基础设施 (当前)

#### P0.1 统一现有 skill 的 meta 格式
- [ ] 更新 `postmortem/SKILL.md` 的报告模板，使用统一 schema
- [ ] 更新 `research/SKILL.md` 的 task-status.json，添加 meta 字段
- [ ] 创建 `docs/META-SCHEMA.md` 文档说明

**涉及文件**:
```
skills/postmortem/SKILL.md
skills/research/SKILL.md
skills/research/TEMPLATES.md
docs/META-SCHEMA.md (新建)
```

**验证**:
```bash
# 检查 frontmatter 格式一致性
rg "^---" -A 30 skills/*/SKILL.md | head -100
```

#### P0.2 创建检索工具函数
- [ ] 在 SKILL.md 中定义标准检索流程
- [ ] 添加检索命令示例到各 skill

**检索命令参考**:
```bash
# 扫描所有知识文档
fd -e md . .claude/ | xargs rg -l "^type:"

# 按 scope.modules 匹配
rg "modules:.*src/auth" .claude/

# 按 keywords 匹配
rg "keywords:.*\[.*token.*\]" .claude/

# 提取 frontmatter (使用 sed)
sed -n '/^---$/,/^---$/p' .claude/postmortem/*/REPORT.md

# 使用 ast-grep 查找函数调用
ast-grep -p 'validateToken($$$)' --lang typescript
```

---

### Phase 1: 开发核心流程 Skills

#### P1.1 ADR (架构决策记录)
- [ ] 创建 `skills/adr/SKILL.md`
- [ ] 创建 `commands/adr.md`
- [ ] 定义 ADR 模板 (使用统一 meta)

**功能**:
```
/adr                     # 列出所有 ADR
/adr new <title>         # 创建新 ADR
/adr search <keyword>    # 搜索相关决策
```

**输出目录**: `<project-root>/.claude/adr/<yymmdd-decision-title>/`

**触发检索**: 创建新 ADR 时检索相关历史决策

#### P1.2 Review (代码审查辅助)
- [ ] 创建 `skills/review/SKILL.md`
- [ ] 创建 `commands/review.md`

**功能**:
```
/review <commit|branch|PR>  # 审查指定变更
/review --staged            # 审查暂存区
```

**触发检索**:
- 检索变更文件相关的 postmortem
- 检索相关 ADR
- 检索 tech-debt 记录

**输出**: 审查报告 + 风险提示

#### P1.3 Refactor (重构分析)
- [ ] 创建 `skills/refactor/SKILL.md`
- [ ] 创建 `commands/refactor.md`

**功能**:
```
/refactor <file|function>   # 分析重构影响
/refactor --plan            # 生成重构计划
```

**分析内容**:
```bash
# 查找函数调用点
ast-grep -p '$FUNC($$$)' --lang <lang>
rg '$FUNC\s*\(' --type <type>

# 查找类型引用
ast-grep -p 'type $TYPE' --lang typescript

# 影响范围分析
git log --oneline -p -S "$FUNC" -- '*.ts'
```

---

### Phase 2: 质量保障 Skills

#### P2.1 Tech-Debt (技术债务追踪)
- [ ] 创建 `skills/tech-debt/SKILL.md`
- [ ] 创建 `commands/tech-debt.md`

**功能**:
```
/tech-debt                  # 列出所有债务
/tech-debt add <desc>       # 记录新债务
/tech-debt scan             # 扫描代码中的 TODO/FIXME/HACK
```

**扫描命令**:
```bash
rg "TODO|FIXME|HACK|XXX" --type-add 'code:*.{ts,js,py,go,rs,kt,java}' -t code
```

**输出目录**: `<project-root>/.claude/tech-debt/`

#### P2.2 Test-Strategy (测试策略)
- [ ] 创建 `skills/test-strategy/SKILL.md`
- [ ] 创建 `commands/test-strategy.md`

**功能**:
```
/test-strategy <feature>    # 为功能生成测试策略
/test-strategy --coverage   # 分析测试覆盖
```

**触发检索**: 检索相关 postmortem 的复现步骤作为测试用例参考

#### P2.3 Security-Scan (安全检查)
- [ ] 创建 `skills/security-scan/SKILL.md`
- [ ] 创建 `commands/security-scan.md`

**功能**:
```
/security-scan              # 全量扫描
/security-scan <file>       # 扫描指定文件
```

**检查项**:
```bash
# SQL 注入
rg "execute\(.*\+.*\)|query\(.*\+.*\)" --type-add 'code:*.{ts,js,py}'

# 硬编码密钥
rg "(password|secret|key|token)\s*=\s*['\"][^'\"]+['\"]" -i

# 不安全的 eval
rg "eval\(|exec\(" --type py --type js
```

---

### Phase 3: 持续改进 Skills

#### P3.1 Dependency (依赖管理)
- [ ] 创建 `skills/dependency/SKILL.md`
- [ ] 创建 `commands/dependency.md`

**功能**:
```
/dependency                 # 分析依赖状态
/dependency upgrade <pkg>   # 升级影响分析
/dependency audit           # 安全漏洞检查
```

#### P3.2 Release (发布管理)
- [ ] 创建 `skills/release/SKILL.md`
- [ ] 创建 `commands/release.md`

**功能**:
```
/release changelog          # 生成 changelog
/release notes <version>    # 生成发布说明
```

**聚合内容**: commits + postmortem + ADR

#### P3.3 Onboarding (新人指南)
- [ ] 创建 `skills/onboarding/SKILL.md`
- [ ] 创建 `commands/onboarding.md`

**功能**:
```
/onboarding                 # 生成项目上手指南
/onboarding <module>        # 生成模块指南
```

**聚合内容**: 项目结构 + 关键 ADR + 常见 postmortem

---

## 任务进度追踪

```
恢复命令: 阅读此文件，继续未完成的任务
项目路径: /Users/yanyao/Projects/side/research-devflow
```

### 总体进度

| Phase | 状态 | 完成度 |
|-------|------|--------|
| Phase 0: 基础设施 | 待开始 | 0/3 |
| Phase 1: 开发核心 | 待开始 | 0/3 |
| Phase 2: 质量保障 | 待开始 | 0/3 |
| Phase 3: 持续改进 | 待开始 | 0/3 |

### 详细任务状态

```
Phase 0: 基础设施
- [ ] P0.1 统一现有 skill 的 meta 格式
- [ ] P0.2 创建检索工具函数

Phase 1: 开发核心流程
- [ ] P1.1 ADR (架构决策记录)
- [ ] P1.2 Review (代码审查辅助)
- [ ] P1.3 Refactor (重构分析)

Phase 2: 质量保障
- [ ] P2.1 Tech-Debt (技术债务追踪)
- [ ] P2.2 Test-Strategy (测试策略)
- [ ] P2.3 Security-Scan (安全检查)

Phase 3: 持续改进
- [ ] P3.1 Dependency (依赖管理)
- [ ] P3.2 Release (发布管理)
- [ ] P3.3 Onboarding (新人指南)
```

### 下次继续点

**当前任务**: Phase 0 - P0.1 统一现有 skill 的 meta 格式

**待执行**:
1. 更新 postmortem REPORT.md 模板
2. 更新 research task-status.json 格式
3. 创建 META-SCHEMA.md 文档

---

## 附录: 关键文件路径

```
项目根目录: /Users/yanyao/Projects/side/research-devflow

已有文件:
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── commands/
│   ├── research.md
│   └── postmortem.md
├── skills/
│   ├── research/
│   │   ├── SKILL.md
│   │   ├── WORKFLOW.md
│   │   ├── EXECUTION-MODES.md
│   │   └── TEMPLATES.md
│   └── postmortem/
│       └── SKILL.md
└── scripts/
    ├── setup-worktrees.sh
    ├── merge.sh
    └── notify.sh

待创建:
├── docs/
│   └── META-SCHEMA.md
├── skills/
│   ├── adr/SKILL.md
│   ├── review/SKILL.md
│   ├── refactor/SKILL.md
│   ├── tech-debt/SKILL.md
│   ├── test-strategy/SKILL.md
│   ├── security-scan/SKILL.md
│   ├── dependency/SKILL.md
│   ├── release/SKILL.md
│   └── onboarding/SKILL.md
└── commands/
    ├── adr.md
    ├── review.md
    ├── refactor.md
    ├── tech-debt.md
    ├── test-strategy.md
    ├── security-scan.md
    ├── dependency.md
    ├── release.md
    └── onboarding.md
```
