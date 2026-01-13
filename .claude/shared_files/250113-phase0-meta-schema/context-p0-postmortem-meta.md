# P0: 统一 postmortem 报告模板的 meta 格式

## 任务目标

更新 postmortem SKILL.md 中的 REPORT.md 模板，使其使用统一的 meta schema。

## 依赖任务

- 无

## 当前状态

postmortem 报告模板已有部分 meta 字段，但需要与统一 schema 对齐：

**当前格式** (`skills/postmortem/SKILL.md:139-168`):
```yaml
---
id: "250113-fix-auth-token-expired"
severity: P1
category: security
status: resolved
jira: "PROJ-1234"
commits: ["abc1234", "def5678"]

scope:
  modules: [...]
  functions: [...]
  ...
```

**目标格式**:
```yaml
---
type: postmortem              # 新增
id: "250113-fix-auth-token-expired"
created_at: "2025-01-13"      # 新增
updated_at: "2025-01-13"      # 新增
status: resolved              # 已有，改为 active|archived|deprecated
author: "username"            # 新增

scope: ...                    # 已有
keywords: [...]               # 已有
relevance: ...                # 已有
refs:                         # 重构
  jira: "PROJ-1234"
  commits: [...]
  related: [...]

# postmortem 特有
severity: P1
category: security
root_cause: ...
---
```

## 实现步骤

### Step 1: 更新 REPORT.md 模板

**文件**: `skills/postmortem/SKILL.md`

找到 `### REPORT.md 模板` 部分，更新 frontmatter 为统一格式。

### Step 2: 确保字段顺序一致

按照统一 schema 的顺序排列：
1. 基础信息 (type, id, created_at, updated_at, status, author)
2. 影响范围 (scope)
3. 语义匹配 (keywords)
4. 相关性判断 (relevance)
5. 关联引用 (refs)
6. Skill 特有字段 (severity, category, root_cause)

## 涉及文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `skills/postmortem/SKILL.md` | 修改 | 更新 REPORT.md 模板部分 |

## 验证方法

```bash
# 检查更新后的模板
rg -A 40 "### REPORT.md 模板" skills/postmortem/SKILL.md
```

## 完成标准

- [ ] REPORT.md 模板包含所有统一 schema 基础字段
- [ ] 字段顺序符合规范
- [ ] postmortem 特有字段保留在最后
- [ ] 更新 task-status.json
- [ ] Git 提交
