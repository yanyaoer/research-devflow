# P1: 统一 research task-status.json 的 meta 格式

## 任务目标

为 research skill 的 task-status.json 和 context 文件添加统一 meta 字段支持。

## 依赖任务

- 无

## 当前状态

research 的 task-status.json 模板位于 `skills/research/TEMPLATES.md:172-222`

**当前格式**:
```json
{
  "task_name": "任务名称",
  "task_slug": "yymmdd-task-slug",
  "created_at": "2025-01-12",
  "base_branch": "main",
  ...
}
```

**目标格式** (添加 meta 字段):
```json
{
  "meta": {
    "type": "task",
    "id": "yymmdd-task-slug",
    "created_at": "2025-01-13",
    "updated_at": "2025-01-13",
    "status": "active",
    "author": "username",
    "scope": {
      "modules": [],
      "functions": [],
      "files": []
    },
    "keywords": [],
    "relevance": {
      "must_read": [],
      "consider": [],
      "skip_if": []
    }
  },
  "task_name": "任务名称",
  "task_slug": "yymmdd-task-slug",
  ...
}
```

## 实现步骤

### Step 1: 更新 TEMPLATES.md 中的 task-status.json 模板

**文件**: `skills/research/TEMPLATES.md`

在 JSON 顶层添加 `meta` 对象。

### Step 2: 更新 SKILL.md 中的 task-status.json 示例

**文件**: `skills/research/SKILL.md`

同步更新关键文件格式部分的示例。

### Step 3: 更新 context-common.md 模板

**文件**: `skills/research/TEMPLATES.md`

在 context-common.md 模板头部添加 YAML frontmatter。

## 涉及文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `skills/research/TEMPLATES.md` | 修改 | 更新 task-status.json 和 context 模板 |
| `skills/research/SKILL.md` | 修改 | 同步更新示例 |

## 验证方法

```bash
# 检查 task-status.json 模板
rg -A 30 "task-status.json 模板" skills/research/TEMPLATES.md

# 检查 context 模板
rg -A 20 "context-common.md 模板" skills/research/TEMPLATES.md
```

## 完成标准

- [ ] task-status.json 模板包含 meta 对象
- [ ] context-common.md 模板包含 YAML frontmatter
- [ ] SKILL.md 中的示例同步更新
- [ ] 更新 task-status.json
- [ ] Git 提交
