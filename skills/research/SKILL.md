---
name: research
description: "拆解复杂任务为可并行执行的子任务。使用场景：用户说'研究'、'调研'、'拆解任务'、'并行处理'，或需要将大任务分解为多个独立步骤。"
---

# Research - 复杂任务拆解与并行处理

## 快速开始

```bash
/research <query>     # 调研新方案，创建子任务
/research             # 选择已有任务或新建
```

## ⚠️ 强制执行规则

**你必须严格按顺序执行以下流程，不得跳过任何步骤。**

### 门禁检查点（Gate Checks）

在执行任何调研任务之前，你 **必须** 完成以下步骤：

1. **[GATE-1] 创建任务目录** - 在 `<project-root>/.claude/shared_files/<yymmdd-task-slug>/` 创建目录
2. **[GATE-2] 创建 task-status.json** - 写入任务元数据和子任务列表
3. **[GATE-3] 创建 context-common.md** - 写入项目背景和公共上下文
4. **[GATE-4] 询问用户执行方式** - 使用 AskUserQuestion 确认执行模式

**🚫 禁止行为：**
- 禁止在未创建 task-status.json 前启动 Task agent 进行调研
- 禁止跳过 AskUserQuestion 直接执行子任务
- 禁止使用 Task agent 做"快速调研"而不记录到任务文档

**✅ 正确流程：**
1. 先创建文档结构
2. 再询问用户确认
3. 最后执行调研任务

### 验证命令

每个门禁完成后，执行验证：

```bash
# GATE-1 验证
ls -la .claude/shared_files/<yymmdd-task-slug>/

# GATE-2 验证
cat .claude/shared_files/<yymmdd-task-slug>/task-status.json | jq '.tasks | length'

# GATE-3 验证
head -20 .claude/shared_files/<yymmdd-task-slug>/context-common.md
```

## 核心工作流

使用 TodoWrite 工具跟踪进度（必需）：

```
Task Progress:
- [ ] 1. 分析任务，识别可并行的子任务
- [ ] 2. 扫描相关 postmortem 报告
- [ ] 3. [GATE-1] 创建共享文件目录
- [ ] 4. [GATE-2] 创建 task-status.json
- [ ] 5. [GATE-3] 写入 context-common.md
- [ ] 6. 写入各子任务的 context-pX-xxx.md
- [ ] 7. 创建 Git Worktree（./scripts/setup-worktrees.sh）
- [ ] 8. [GATE-4] 询问用户选择执行方式（AskUserQuestion）
- [ ] 9. 执行任务（每个任务在自己的 worktree 中）
- [ ] 10. 每个子任务完成时发送系统通知
- [ ] 11. 合并所有分支（./scripts/merge.sh）
- [ ] 12. 清理 worktree
```

## 任务类型判断

在开始执行前，先判断任务类型：

| 类型 | 特征 | 是否需要 worktree | 是否需要任务文档 |
|------|------|------------------|-----------------|
| **调研型** | 技术方案对比、可行性分析 | ❌ 不需要 | ✅ **必需** |
| **开发型** | 需要修改代码、创建文件 | ✅ 需要 | ✅ **必需** |
| **混合型** | 先调研后开发 | ✅ 需要 | ✅ **必需** |

### 调研型任务简化流程

对于纯调研类任务（如"对比方案 A 和 B 的优劣"），可跳过 worktree 相关步骤，但**仍必须创建任务文档**：

```
调研型任务流程:
- [ ] 1. 分析任务，识别调研维度
- [ ] 2. [GATE-1] 创建共享文件目录
- [ ] 3. [GATE-2] 创建 task-status.json（type: "research"）
- [ ] 4. [GATE-3] 创建 context-common.md
- [ ] 5. [GATE-4] 询问用户执行方式
- [ ] 6. 执行调研（Task agent 并行）
- [ ] 7. 汇总调研结果到 REPORT.md
- [ ] 8. 更新 task-status.json 状态为 completed
```

### 调研型 task-status.json 模板

```json
{
  "meta": {
    "type": "research",
    "id": "yymmdd-task-slug"
  },
  "task_name": "调研任务名称",
  "task_type": "research",
  "worktree_enabled": false,
  "tasks": [
    {
      "id": "r0",
      "name": "调研维度 A",
      "status": "pending",
      "output_file": "findings-r0.md"
    }
  ]
}
```

## Postmortem 扫描

在创建 context 文件前，扫描 `.claude/postmortem/` 目录，匹配相关报告：

### 检索命令

```bash
# 列出所有 postmortem 报告
fd REPORT.md .claude/postmortem/

# 按涉及模块检索
rg "modules:.*<module>" .claude/postmortem/

# 按涉及函数检索
rg "functions:.*<function>" .claude/postmortem/

# 按涉及文件检索
rg "files:.*<pattern>" .claude/postmortem/

# 按关键词检索
rg "keywords:.*<keyword>" .claude/postmortem/

# 提取所有 frontmatter 用于批量分析
fd REPORT.md .claude/postmortem/ -x sed -n '/^---$/,/^---$/p' {}
```

### 匹配规则

读取每个报告的 YAML frontmatter，按以下规则判断：

1. **scope 匹配** - 任务涉及的文件/模块/函数与报告 scope 重叠
2. **keywords 匹配** - 任务关键词与报告 keywords 交集
3. **relevance.must_read** - 任务描述命中 must_read 条件

### 匹配结果处理

| 相关性 | 判断条件 | 处理方式 |
|--------|----------|----------|
| 高 | scope 命中 | 必须在 context-common.md 中引用 |
| 中 | keywords 命中 | 在 context-common.md 中提及 |
| 低 | 仅 consider 命中 | 可选引用 |

## 目录结构

创建位置：`<project-root>/.claude/shared_files/<yymmdd-task-slug>/`

```
<yymmdd-task-slug>/
├── task-status.json      # 状态跟踪（必需）
├── context-common.md     # 公共背景（必需）
├── context-p0-xxx.md     # 子任务上下文
├── context-p1-xxx.md
├── worktrees/            # Git worktree 目录（并行开发时创建）
│   ├── p0/               # P0 的独立工作目录
│   └── p1/               # P1 的独立工作目录
└── ...
```

## Git Worktree 隔离开发

**并行任务必须使用 worktree 隔离**，避免代码冲突：

```bash
# 创建 worktree（每个子任务一个）
git worktree add .claude/shared_files/<yymmdd-task-slug>/worktrees/p0 -b research/<yymmdd-task-slug>/p0
git worktree add .claude/shared_files/<yymmdd-task-slug>/worktrees/p1 -b research/<yymmdd-task-slug>/p1
```

**子任务在各自 worktree 中开发**:
```bash
cd .claude/shared_files/<yymmdd-task-slug>/worktrees/p0
# 在此目录完成 P0 任务的所有修改
```

**完成后合并回主分支**（按完成顺序）:
```bash
# 第一个完成的任务直接合并
git checkout main
git merge research/<yymmdd-task-slug>/p0

# 后完成的任务需要处理冲突
git merge research/<yymmdd-task-slug>/p1
# 如有冲突，谨慎解决后继续
```

详见 [WORKFLOW.md](WORKFLOW.md) 的 Git Worktree 章节

## 关键文件格式

**task-status.json**（严格遵循）:
```json
{
  "meta": {
    "type": "task",
    "id": "yymmdd-task-slug",
    "created_at": "2025-01-13",
    "updated_at": "2025-01-13",
    "status": "active",
    "scope": { "modules": [], "functions": [], "files": [] },
    "keywords": [],
    "relevance": { "must_read": [], "consider": [], "skip_if": [] }
  },
  "task_name": "任务名称",
  "task_slug": "yymmdd-task-slug",
  "created_at": "2025-01-13",
  "tasks": [
    {
      "id": "p0",
      "name": "子任务名称",
      "status": "pending|in_progress|completed",
      "dependencies": [],
      "context_file": "context-p0-xxx.md",
      "completed_at": null,
      "notes": ""
    }
  ]
}
```

**context-common.md** 必须包含:
- 项目背景（3-5行）
- 项目结构
- 关键发现/根因分析
- 构建命令
- Git 提交规范
- 相关 Postmortem（如有匹配）

**Postmortem 引用格式**:
```markdown
## 相关 Postmortem

以下历史问题与本任务相关，请在开发过程中注意：

### 高相关（必读）
- [250110-fix-auth-token-expired](.claude/postmortem/250110-fix-auth-token-expired/REPORT.md)
  - 影响: src/auth/, src/middleware/
  - 根因: race_condition - async token refresh without lock
  - 注意: 修改 token 验证或刷新逻辑时必读

### 参考
- [250105-user-session-timeout](.claude/postmortem/250105-user-session-timeout/REPORT.md)
  - 关键词匹配: session, timeout
```

**context-pX-xxx.md** 必须包含:
- 任务目标
- 依赖任务（如有）
- 实现步骤（详细代码示例）
- 涉及文件清单
- 验证方法
- 完成标准（checklist）

## 执行方式选择

完成文件创建后，使用 AskUserQuestion 询问：

| 方式 | 适用场景 |
|------|----------|
| Subagent 后台并行 | 无依赖的独立任务 |
| 多终端手动启动 | 需要 MCP 或交互 |
| 当前进程顺序 | 简单任务或强依赖 |

详见 [EXECUTION-MODES.md](EXECUTION-MODES.md)

## 子任务完成通知

**每个子任务完成时必须发送系统通知**:

```bash
osascript -e 'display notification "P0: <任务名> 已完成" with title "Research Task Done" sound name "Glass"'
```

## 状态更新规范

子任务完成后**立即**更新 task-status.json:
1. 将 status 改为 "completed"
2. 填写 completed_at
3. 在 notes 中记录关键修改
4. 发送系统通知

## 无输入时：选择模式

扫描已有任务目录，列出选项供用户选择。详见 [WORKFLOW.md](WORKFLOW.md)

## 质量保证

- 每个子任务应能独立完成
- context 文件包含足够信息，无需额外探索
- 验证方法明确可执行
- 完成后立即发送通知

## 参考文件

- [WORKFLOW.md](WORKFLOW.md) - 详细工作流程
- [EXECUTION-MODES.md](EXECUTION-MODES.md) - 执行模式详解
- [TEMPLATES.md](TEMPLATES.md) - 文件模板

## 脚本工具

```bash
# 初始化 worktree（创建完 task-status.json 后执行）
./scripts/setup-worktrees.sh .claude/shared_files/<yymmdd-task-slug>

# 任务完成通知
./scripts/notify.sh done p0 "任务名称" "修改: file1, file2"
./scripts/notify.sh fail p0 "任务名称" "错误信息"
./scripts/notify.sh all_done

# 合并所有完成的分支（所有任务完成后执行）
./scripts/merge.sh .claude/shared_files/<yymmdd-task-slug>
./scripts/merge.sh .claude/shared_files/<yymmdd-task-slug> --dry-run  # 预览
```
