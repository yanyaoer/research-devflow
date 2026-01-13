# Phase 1 设计讨论: 工具组规范统一

## 问题分析

### 工具组关系

```
代码质量组                    任务拆解组
┌──────────┐                 ┌──────────┐
│ review   │ ←── 共享规则 ──→ │ refactor │
│ (事前)   │                 │ (代码)   │
└────┬─────┘                 └────┬─────┘
     │ 教训→检查规则              │ 是子任务
     ↓                           ↓
┌──────────┐                 ┌──────────┐
│postmortem│                 │ research │
│ (事后)   │                 │ (通用)   │
└──────────┘                 └──────────┘
```

### 需要统一的内容

1. **分析规则** - 代码风险检查项
2. **输出格式** - 报告结构
3. **检索逻辑** - 知识库查询方式
4. **工作流** - 执行步骤

## 设计方案

### 方案 A: 共享规则文件

创建共享规则文件，各 skill 引用：

```
skills/
├── _shared/                    # 共享组件
│   ├── rules/
│   │   ├── code-quality.md     # review + postmortem 共享
│   │   └── task-workflow.md    # refactor + research 共享
│   └── templates/
│       ├── risk-assessment.md  # 风险评估模板
│       └── impact-analysis.md  # 影响分析模板
├── review/
│   └── SKILL.md               # 引用 _shared/rules/code-quality.md
├── postmortem/
│   └── SKILL.md               # 引用 _shared/rules/code-quality.md
├── refactor/
│   └── SKILL.md               # 引用 _shared/rules/task-workflow.md
└── research/
    └── SKILL.md               # 引用 _shared/rules/task-workflow.md
```

**优点**: 规则集中管理，修改一处同步多处
**缺点**: 需要约定引用机制

### 方案 B: 继承式 Skill

定义 base skill，其他 skill 继承扩展：

```yaml
# skills/review/SKILL.md
---
name: review
extends: _shared/code-quality-base
scenario: pre-merge
---
# 仅定义 review 特有的部分
```

**优点**: 结构清晰
**缺点**: Claude Code 不原生支持继承，需要约定处理

### 方案 C: 规则索引 + 场景标签 (推荐)

创建统一规则索引，使用场景标签区分：

```yaml
# docs/RULES-INDEX.md
rules:
  - id: null-check
    applies_to: [review, postmortem]  # 适用场景
    severity: high
    check: "检查空值/未定义处理"

  - id: impact-analysis
    applies_to: [refactor, research]
    check: "分析变更影响范围"
```

各 skill 根据 `applies_to` 标签加载相关规则。

**优点**: 灵活、可扩展、易于查询
**缺点**: 需要额外的规则索引文件

## 具体设计

### 1. 代码质量规则 (review + postmortem)

```yaml
# docs/RULES-CODE-QUALITY.md
---
id: code-quality-rules
version: "1.0"
---

# 代码质量检查规则

## 安全类 (security)

| ID | 规则 | review 检查 | postmortem 分析 |
|----|------|------------|-----------------|
| S01 | SQL 注入 | 检查参数化查询 | 追溯注入路径 |
| S02 | XSS | 检查输出编码 | 分析攻击向量 |
| S03 | 认证绕过 | 检查权限校验 | 还原绕过过程 |

## 健壮性 (robustness)

| ID | 规则 | review 检查 | postmortem 分析 |
|----|------|------------|-----------------|
| R01 | 空值处理 | 检查 null check | 追溯空指针来源 |
| R02 | 边界条件 | 检查数组越界 | 分析边界触发 |
| R03 | 并发安全 | 检查锁和竞态 | 还原竞态时序 |

## 检索命令

```bash
# review 时按规则类型检索历史 postmortem
rg "root_cause:.*type: null_check" .claude/postmortem/

# postmortem 时检查是否有对应的 review 规则
rg "R01|null" docs/RULES-CODE-QUALITY.md
```
```

### 2. 任务工作流 (refactor + research)

```yaml
# docs/RULES-TASK-WORKFLOW.md
---
id: task-workflow-rules
version: "1.0"
---

# 任务拆解工作流规则

## 影响分析 (共享)

| 步骤 | research | refactor |
|------|----------|----------|
| 1. 识别范围 | 人工定义 | ast-grep 自动分析 |
| 2. 依赖分析 | 模块级别 | 函数调用级别 |
| 3. 风险评估 | 参考 postmortem | 参考 postmortem + review |

## refactor 专用: 代码分析命令

```bash
# 查找函数调用点
ast-grep -p '$FUNC($$$)' --lang <lang>

# 查找类型引用
ast-grep -p 'type $TYPE = $_' --lang typescript

# 查找接口实现
ast-grep -p 'class $_ implements $INTERFACE' --lang typescript
```

## research 通用: 任务拆分原则

- 每个子任务 1-2 小时可完成
- 最小化依赖关系
- 明确输入输出
```

### 3. Skill 特化定义

各 skill 引用共享规则，并添加场景特化：

```markdown
# skills/review/SKILL.md

## 规则引用

本 skill 使用以下共享规则:
- [代码质量规则](../../docs/RULES-CODE-QUALITY.md) - 全部检查项
- [任务工作流](../../docs/RULES-TASK-WORKFLOW.md) - 影响分析部分

## review 特化

### 检查时机
- PR 提交后
- 合并前

### 输出格式
- 风险等级: low/medium/high/critical
- 建议类型: must-fix/should-fix/consider

### 与 postmortem 联动
执行 review 时自动检索相关 postmortem:
```bash
rg "modules:.*<changed-module>" .claude/postmortem/
```
```

## 文件结构

```
research-devflow/
├── docs/
│   ├── META-SCHEMA.md              # 统一 meta 规范
│   ├── RULES-CODE-QUALITY.md       # 代码质量规则 (新)
│   └── RULES-TASK-WORKFLOW.md      # 任务工作流规则 (新)
├── skills/
│   ├── review/SKILL.md             # 引用共享规则 + 特化
│   ├── postmortem/SKILL.md         # 引用共享规则 + 特化
│   ├── refactor/SKILL.md           # 引用共享规则 + 特化
│   └── research/SKILL.md           # 引用共享规则 + 特化
└── ...
```

## 待确认

1. 采用哪个方案？(推荐 C: 规则索引 + 场景标签)
2. 规则文件放在 `docs/` 还是 `skills/_shared/`？
3. 先实现哪个 skill？(建议 review，与 postmortem 联动最紧密)
