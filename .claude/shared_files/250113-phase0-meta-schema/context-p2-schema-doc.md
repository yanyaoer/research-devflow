# P2: 创建 META-SCHEMA.md 文档

## 任务目标

创建统一 meta schema 的规范文档，供所有 skill 开发参考。

## 依赖任务

- P0: 统一 postmortem 报告模板的 meta 格式
- P1: 统一 research task-status.json 的 meta 格式

## 实现步骤

### Step 1: 创建 docs 目录

```bash
mkdir -p docs
```

### Step 2: 创建 META-SCHEMA.md

**文件**: `docs/META-SCHEMA.md`

```markdown
# 统一 Meta Schema 规范

## 概述

所有 skill 产出的文档使用统一的 meta schema，支持 AI 检索和知识关联。

## 基础字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | ✓ | 文档类型: postmortem, task, adr, review, ... |
| id | string | ✓ | 唯一标识: yymmdd-short-description |
| created_at | string | ✓ | 创建日期: YYYY-MM-DD |
| updated_at | string | ✓ | 更新日期: YYYY-MM-DD |
| status | string | ✓ | 状态: active, archived, deprecated |
| author | string | | 作者 |

## 影响范围 (scope)

用于 AI 检索时判断相关性。

| 字段 | 类型 | 说明 |
|------|------|------|
| modules | string[] | 受影响的模块/目录 |
| functions | string[] | 受影响的函数名 |
| files | string[] | 受影响的文件 (支持 glob) |
| apis | string[] | 受影响的 API 端点 |
| tables | string[] | 受影响的数据库表 |

## 语义匹配 (keywords)

用于语义检索的关键词列表。

## 相关性判断 (relevance)

| 字段 | 说明 |
|------|------|
| must_read | 必须阅读的条件 |
| consider | 建议参考的条件 |
| skip_if | 可以跳过的条件 |

## 关联引用 (refs)

| 字段 | 说明 |
|------|------|
| jira | 关联的 Jira ID |
| commits | 关联的 commit hash |
| related | 关联的其他文档 ID |

## Skill 特有字段

各 skill 可在基础字段之后添加特有字段。

### postmortem

- severity: P0/P1/P2/P3
- category: security/data/performance/logic/ui/config
- root_cause: { type, pattern }

### adr

- decision_status: proposed/accepted/deprecated
- supersedes: 被替代的 ADR ID

## 示例

见各 skill 的模板文档。
```

## 涉及文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `docs/META-SCHEMA.md` | 新建 | 统一 schema 规范文档 |

## 验证方法

```bash
# 确认文档创建
cat docs/META-SCHEMA.md
```

## 完成标准

- [ ] 创建 docs/META-SCHEMA.md
- [ ] 包含所有字段说明
- [ ] 包含各 skill 特有字段
- [ ] 更新 task-status.json
- [ ] Git 提交
