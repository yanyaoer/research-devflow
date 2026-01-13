# Context 文件模板

## context-common.md 模板

```markdown
---
# context-common.md 不需要完整 meta，仅标识关联的 task
task_id: "yymmdd-task-slug"
---

# <任务名称> - 共享上下文

## 项目背景

<3-5行项目背景描述>

## 项目结构

\`\`\`
project/
├── src/
├── tests/
└── ...
\`\`\`

## 关键发现

### 问题根因

1. **问题1**: 描述
2. **问题2**: 描述

### 参考实现

| 项目 | 方案 | 核心技术 |
|------|------|----------|
| xxx | yyy | zzz |

## 相关 Postmortem

以下历史问题与本任务相关，请在开发过程中注意：

### 高相关（必读）

_检索命令: `rg "modules:.*<涉及模块>" .claude/postmortem/`_

- 无 / [报告链接](路径) - 简要说明

### 参考

- 无 / [报告链接](路径) - 关键词匹配

## 构建命令

\`\`\`bash
# 构建
./gradlew build

# 测试
./gradlew test
\`\`\`

## Git 提交规范

\`\`\`bash
git add -A && git commit -m "<type>(<scope>): <description>"
\`\`\`

类型: feat, fix, refactor, docs, chore

## 任务状态更新

完成任务后:
1. 更新 task-status.json
2. 发送通知: `osascript -e 'display notification "PX: 任务名 完成" with title "Research" sound name "Glass"'`
3. Git 提交
```

---

## context-pX-xxx.md 模板

```markdown
# PX: 任务名称

## 任务目标

一句话描述目标。

## 依赖任务

- 无
<!-- 或 -->
- P0: xxx
- P1: yyy

## 当前问题

**问题描述**:

<详细问题描述>

**代码位置**:

- `path/to/file.kt:123` - 问题点1
- `path/to/file2.kt:456` - 问题点2

## 解决方案

<方案概述>

## 实现步骤

### Step 1: 创建/修改 xxx

**文件**: `path/to/file.kt`

\`\`\`kotlin
// 代码示例
class Example {
    fun doSomething() {
        // 实现
    }
}
\`\`\`

### Step 2: 修改 yyy

**文件**: `path/to/file2.kt`

\`\`\`kotlin
// 修改前
val old = ...

// 修改后
val new = ...
\`\`\`

### Step 3: 添加测试

**文件**: `path/to/ExampleTest.kt`

\`\`\`kotlin
@Test
fun testExample() {
    // 测试代码
}
\`\`\`

## 涉及文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `path/to/file.kt` | 新建 | 核心实现 |
| `path/to/file2.kt` | 修改 | 集成调用 |
| `path/to/ExampleTest.kt` | 新建 | 单元测试 |

## 验证方法

1. **单元测试**:
   \`\`\`bash
   ./gradlew :module:test --tests "ExampleTest"
   \`\`\`

2. **手动验证**:
   - 步骤1: xxx
   - 步骤2: yyy
   - 预期结果: zzz

3. **构建验证**:
   \`\`\`bash
   ./gradlew assembleDebug
   \`\`\`

## 完成标准

- [ ] Step 1 完成: 创建 xxx
- [ ] Step 2 完成: 修改 yyy
- [ ] Step 3 完成: 添加测试
- [ ] 所有测试通过
- [ ] 构建成功
- [ ] 更新 task-status.json
- [ ] 发送完成通知
- [ ] Git 提交
```

---

## task-status.json 模板

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
    },
    "refs": {
      "jira": "",
      "commits": [],
      "related": []
    }
  },
  "task_name": "任务名称",
  "task_slug": "yymmdd-task-slug",
  "created_at": "2025-01-13",
  "base_branch": "main",
  "worktree_enabled": true,
  "merge_order": [],
  "tasks": [
    {
      "id": "p0",
      "name": "子任务0名称",
      "status": "pending",
      "dependencies": [],
      "context_file": "context-p0-xxx.md",
      "branch": "research/yymmdd-task-slug/p0",
      "worktree_path": "worktrees/p0",
      "merge_status": "pending",
      "completed_at": null,
      "merged_at": null,
      "notes": ""
    },
    {
      "id": "p1",
      "name": "子任务1名称",
      "status": "pending",
      "dependencies": [],
      "context_file": "context-p1-yyy.md",
      "branch": "research/yymmdd-task-slug/p1",
      "worktree_path": "worktrees/p1",
      "merge_status": "pending",
      "completed_at": null,
      "merged_at": null,
      "notes": ""
    },
    {
      "id": "p2",
      "name": "子任务2名称（依赖P0）",
      "status": "pending",
      "dependencies": ["p0"],
      "context_file": "context-p2-zzz.md",
      "branch": "research/yymmdd-task-slug/p2",
      "worktree_path": "worktrees/p2",
      "merge_status": "pending",
      "completed_at": null,
      "merged_at": null,
      "notes": ""
    }
  ]
}
```

### 字段说明

| 字段 | 说明 |
|------|------|
| `meta` | 统一 meta schema，用于 AI 检索 |
| `base_branch` | 基础分支，合并目标 |
| `worktree_enabled` | 是否启用 worktree 隔离 |
| `merge_order` | 合并顺序记录 `["p0", "p1", ...]` |
| `branch` | 任务分支名 |
| `worktree_path` | worktree 相对路径 |
| `merge_status` | `pending` / `merged` / `conflict` |
| `merged_at` | 合并完成时间 |

---

## 命名规范

### task-slug

- 格式: `yymmdd-kebab-case-description`
- 前缀为创建日期
- 描述性但简洁
- 示例: `250113-optimize-long-sentence`, `250113-add-dark-mode`, `250112-fix-memory-leak`

### context 文件名

- 格式: `context-pX-<简短描述>.md`
- 示例: `context-p0-engine-refactor.md`, `context-p1-dict-optimize.md`

### 子任务 ID

- 使用 `p0`, `p1`, `p2`... 顺序编号
- 按优先级或逻辑顺序排列
