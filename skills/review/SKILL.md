---
name: review
description: "代码审查辅助工具，实现事前代码质量检查，与 postmortem 联动。"
---

```yaml:skill-config
name: review
version: "1.0"
description: "代码审查辅助工具"

triggers:
  commands: ["/review"]
  keywords: ["审查", "review", "检查代码", "代码审查"]

steps:
  - id: get_changes
    name: "获取变更文件"
    type: command
    command: "git diff --cached --name-only"
    description: "获取暂存区变更文件列表"

  - id: load_rules
    name: "加载审查规则"
    type: command
    command: "python scripts/rule_query.py --query review --format json 2>/dev/null || echo '[]'"
    description: "加载适用的代码质量规则"

  - id: search_postmortem
    name: "检索相关 Postmortem"
    type: command
    command: "fd REPORT.md .claude/postmortem/ 2>/dev/null || echo 'No postmortem'"
    description: "检索与变更相关的历史问题"

  - id: analyze_code
    name: "分析代码变更"
    type: prompt
    prompt_ref: "#analyze-code-prompt"
    dependencies: [get_changes, load_rules, search_postmortem]
    description: "逐文件分析代码质量问题"

  - id: generate_report
    name: "生成审查报告"
    type: prompt
    prompt_ref: "#generate-report-prompt"
    dependencies: [analyze_code]
    description: "生成结构化审查报告"

  - id: gate_critical_issues
    name: "[GATE] 检查 Critical 问题"
    type: gate_check
    validation: "echo 'Review completed - check report for critical issues'"
    on_failure: skip
    dependencies: [generate_report]
    description: "提示用户检查报告中的 Critical 问题"
    optional: true
```

# Review Skill

代码审查辅助工具，实现事前代码质量检查，与 postmortem 联动。

## 命令格式

```bash
/review                     # 审查暂存区变更
/review <commit>            # 审查指定 commit
/review <branch>            # 审查分支与 main 的 diff
/review --pr <number>       # 审查 PR (需要 gh CLI)
```

## 共享规则引用

本 skill 使用以下共享规则：
- [代码质量规则](../../docs/RULES-CODE-QUALITY.md): 用于代码检查
- [LSP 配置指南](../../docs/common-lsp.md): 用于辅助分析

### 加载规则

```bash
# 获取 review 适用的规则
python scripts/rule_query.py --query review --format json

# 按分类获取
python scripts/rule_query.py --query review --category security --format json
```

## 工作流程

```
Task Progress:
- [ ] 1. 获取变更文件列表
- [ ] 2. 加载适用规则
- [ ] 3. 检索相关 postmortem
- [ ] 4. 逐文件执行检查
- [ ] 5. 生成审查报告
- [ ] 6. 输出风险提示
```

### Step 1: 获取变更文件列表

根据输入参数获取变更：

```bash
# 暂存区变更
git diff --cached --name-only

# 指定 commit
git diff-tree --no-commit-id --name-only -r <commit>

# 分支对比
git diff --name-only main...<branch>

# PR (需要 gh CLI)
gh pr diff <number> --name-only
```

### Step 2: 加载适用规则

```bash
# 获取所有 review 规则
RULES=$(python scripts/rule_query.py --query review --format json)

# 按严重程度排序检查
# critical > high > medium > low
```

### Step 3: 检索相关 postmortem

检索与变更文件相关的历史问题：

```bash
# 按文件路径匹配
for file in <changed_files>; do
  rg "modules:.*$(dirname $file)" .claude/postmortem/*/REPORT.md
  rg "files:.*$file" .claude/postmortem/*/REPORT.md
done

# 按关键词匹配 (从变更内容提取)
rg "keywords:.*<keyword>" .claude/postmortem/*/REPORT.md
```

### Step 4: 逐文件执行检查

对每个变更文件，执行规则的 check_command。

**LSP 辅助建议**: 在检查复杂逻辑时，优先使用 LSP 工具 (`definition`, `references`) 评估影响。要求**至少追踪上下游各 2 层**调用关系，以确保覆盖潜在副作用。

降级使用 `ast-grep` 或 `grep`。

```bash
# 获取规则的检查命令并执行
python scripts/rule_query.py --query review --format json | \
  jq -r '.rules[].check_command' | \
  while read -r cmd; do
    eval "$cmd" <file>
  done
```

检查时记录：
- 规则 ID
- 匹配位置 (文件:行号)
- 匹配内容
- 建议修复 (fix_hint)

### Step 5: 生成审查报告

输出结构化报告，格式见下方 [报告模板](#报告模板)。

### Step 6: 输出风险提示

```
## 风险摘要

| 风险等级 | 数量 | 说明 |
|----------|------|------|
| Critical | 1 | 必须修复后才能合并 |
| High | 2 | 强烈建议修复 |
| Medium | 0 | 建议修复 |
| Low | 3 | 可选修复 |

### 相关历史问题

以下 postmortem 与本次变更相关，请注意避免重蹈覆辙：
- [250110-sql-injection](.claude/postmortem/250110-sql-injection/REPORT.md) - 同类问题
```

## 报告模板

```yaml
---
type: review
id: "<yymmdd>-review-<target>"
created_at: "<date>"
status: active
scope:
  files: ["src/auth/login.ts", "src/api/user.ts"]
  functions: ["validateUser", "createSession"]
keywords: [auth, session, login]
refs:
  pr: "123"
  commits: ["abc1234"]
risk_level: medium
issues_count: 3
---
```

```markdown
# 代码审查报告

## 变更概览

| 文件 | 新增 | 删除 | 风险 |
|------|------|------|------|
| src/auth/login.ts | +50 | -10 | high |
| src/api/user.ts | +20 | -5 | medium |

## 检查结果

### Critical (必须修复)

- **S01: SQL 注入风险** @ src/api/user.ts:45
  ```typescript
  // 问题代码
  db.query(`SELECT * FROM users WHERE id = ${userId}`)
  ```
  **建议**: 使用参数化查询
  ```typescript
  db.query('SELECT * FROM users WHERE id = ?', [userId])
  ```

### High (应该修复)

- **R01: 空值处理缺失** @ src/auth/login.ts:23
  ```typescript
  const user = await findUser(id)
  return user.name  // user 可能为 null
  ```
  **建议**: 添加空值检查或使用可选链

### Medium (建议修复)

(无)

### Low (可选修复)

- **M01: 硬编码配置** @ src/auth/login.ts:5
  ```typescript
  const API_URL = 'http://localhost:3000'
  ```
  **建议**: 使用环境变量

## 相关 Postmortem

以下历史问题与本次变更相关：

| 问题 | 影响范围 | 相关性 |
|------|----------|--------|
| [250110-sql-injection](.claude/postmortem/250110-sql-injection/REPORT.md) | src/api/ | 同类型问题 |

## 总结

| 风险等级 | 数量 |
|----------|------|
| Critical | 1 |
| High | 1 |
| Medium | 0 |
| Low | 1 |

**建议**: 修复 Critical 和 High 级别问题后再合并。
```

## 输出位置

审查报告输出到：`<project-root>/.claude/reviews/<yymmdd>-review-<target>/REPORT.md`

例如：
- `<project-root>/.claude/reviews/250113-review-pr-123/REPORT.md`
- `<project-root>/.claude/reviews/250113-review-feature-auth/REPORT.md`

---

## Prompts

```markdown:analyze-code-prompt
你是一个代码审查专家。请分析以下代码变更。

**变更文件列表**:
${changed_files}

**适用规则**:
${rules}

**相关历史问题**:
${postmortem_refs}

**分析要求**:
1. 逐文件检查，应用适用规则
2. 使用 LSP 工具追踪调用关系（至少上下游各 2 层）
3. 对照历史问题，检查是否有类似风险

**对每个问题记录**:
- 规则 ID
- 文件:行号
- 问题代码片段
- 风险等级 (critical/high/medium/low)
- 建议修复

将分析结果存储到 context 变量 ${analysis_results} 中。
```

```markdown:generate-report-prompt
基于代码分析结果，生成结构化审查报告。

**分析结果**: ${analysis_results}
**变更文件**: ${changed_files}
**项目根目录**: ${project_root}

**报告格式要求**:

1. YAML Frontmatter:
   ```yaml
   ---
   type: review
   id: "${task_slug}"
   created_at: "${date}"
   status: active
   scope:
     files: [变更文件列表]
     functions: [涉及函数]
   keywords: [关键词]
   risk_level: [最高风险等级]
   issues_count: [问题总数]
   ---
   ```

2. 报告内容:
   - 变更概览表格
   - 按风险等级分类的问题列表
   - 相关 Postmortem 引用
   - 风险摘要

**输出位置**:
${project_root}/.claude/reviews/${task_slug}/REPORT.md

**执行要求**:
1. 生成完整的 Markdown 报告内容
2. **必须**使用 `write_file` 工具将报告写入上述输出位置
3. 统计 critical 和 high 问题数量

**可用工具**:
- `write_file(file_path, content)`: 写入文件，自动创建父目录
```
