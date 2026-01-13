# 统一 Meta Schema 规范

## 概述

所有 skill 产出的文档使用统一的 meta schema，支持 AI 检索和知识关联。

## Schema 结构

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

# === Skill 特有字段 ===
# (见下文各 skill 定义)
---
```

## 字段说明

### 基础信息

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | ✓ | 文档类型 |
| `id` | string | ✓ | 唯一标识: `yymmdd-short-description` |
| `created_at` | string | ✓ | 创建日期: `YYYY-MM-DD` |
| `updated_at` | string | ✓ | 更新日期: `YYYY-MM-DD` |
| `status` | string | ✓ | 状态: `active`, `archived`, `deprecated` |
| `author` | string | | 作者 |

### 影响范围 (scope)

用于 AI 检索时判断相关性。

| 字段 | 类型 | 说明 |
|------|------|------|
| `modules` | string[] | 受影响的模块/目录路径 |
| `functions` | string[] | 受影响的函数名 |
| `files` | string[] | 受影响的文件路径 (支持 glob) |
| `apis` | string[] | 受影响的 API 端点 |
| `tables` | string[] | 受影响的数据库表 |

### 语义匹配 (keywords)

用于语义检索的关键词列表。建议包含：
- 功能领域关键词
- 技术栈关键词
- 业务概念关键词

### 相关性判断 (relevance)

帮助 AI 快速判断是否需要阅读完整文档。

| 字段 | 说明 |
|------|------|
| `must_read` | 必须阅读的条件列表 |
| `consider` | 建议参考的条件列表 |
| `skip_if` | 可以跳过的条件列表 |

### 关联引用 (refs)

| 字段 | 类型 | 说明 |
|------|------|------|
| `jira` | string | 关联的 Jira ID |
| `commits` | string[] | 关联的 commit hash |
| `related` | string[] | 关联的其他文档 ID |

## Skill 特有字段

### postmortem

```yaml
severity: P0 | P1 | P2 | P3
category: security | data | performance | logic | ui | config
root_cause:
  type: null_check | race_condition | boundary | type_error | config | dependency
  pattern: "问题模式描述"
```

### task (research)

task-status.json 使用 JSON 格式，meta 作为顶层对象：

```json
{
  "meta": {
    "type": "task",
    "id": "...",
    ...
  },
  "task_name": "...",
  ...
}
```

### adr (架构决策记录)

```yaml
decision_status: proposed | accepted | deprecated | superseded
supersedes: "yymmdd-old-adr-id"
superseded_by: "yymmdd-new-adr-id"
```

### review (代码审查)

```yaml
review_type: pr | commit | branch
target: "PR#123 | commit-hash | branch-name"
risk_level: low | medium | high | critical
```

### tech-debt (技术债务)

```yaml
debt_type: code | test | doc | infra
priority: low | medium | high
effort: small | medium | large
```

## 检索命令速查

```bash
# === 扫描知识库 ===

# 列出所有知识文档
fd -e md . .claude/ | xargs rg -l "^type:"

# 按类型筛选
rg "^type: postmortem" .claude/ -l
rg "^type: task" .claude/ -l

# === 按 scope 检索 ===

# 按模块路径匹配
rg "modules:.*src/auth" .claude/

# 按函数名匹配
rg "functions:.*validateToken" .claude/

# 按文件路径匹配
rg "files:.*\.ts" .claude/

# === 按 keywords 检索 ===

rg "keywords:.*token" .claude/
rg "keywords:.*\[.*auth.*\]" .claude/

# === 按特有字段检索 ===

# 高优先级 postmortem
rg "severity: P0" .claude/postmortem/
rg "severity: P1" .claude/postmortem/

# 按根因类型
rg "type: race_condition" .claude/postmortem/

# === 提取 frontmatter ===

# 提取单个文件的 frontmatter
sed -n '/^---$/,/^---$/p' <file>

# 批量提取
fd REPORT.md .claude/postmortem/ -x sed -n '/^---$/,/^---$/p' {}
```

## 匹配算法

AI 检索时按以下规则判断相关性：

```
1. scope 交集判断
   - modules/files/functions 与当前任务有交集 → 高相关

2. keywords 交集判断
   - keywords 与任务描述有交集 → 中相关

3. relevance 条件判断
   - must_read 条件命中 → 必读
   - consider 条件命中 → 建议参考
   - skip_if 条件命中 → 可跳过

4. 输出结果
   - 必读文档：完整内容引用到 context
   - 参考文档：仅列出链接和摘要
```

## 示例

见各 skill 的 SKILL.md 模板部分：
- [postmortem/SKILL.md](../skills/postmortem/SKILL.md)
- [research/TEMPLATES.md](../skills/research/TEMPLATES.md)
