# Research Skill

拆解复杂任务为可并行执行的子任务，支持 Git Worktree 隔离开发。

## ⚠️ 强制执行规则

**执行任何任务前，必须完成以下门禁检查点：**

1. **[GATE-1]** 创建任务目录 `<project-root>/.claude/shared_files/<yymmdd-task-slug>/`
2. **[GATE-2]** 创建 `task-status.json`
3. **[GATE-3]** 创建 `context-common.md`
4. **[GATE-4]** 使用 AskUserQuestion 确认执行方式

**🚫 禁止在未完成门禁检查前启动 Task agent 进行调研或开发**

## 功能特性

- **任务拆解**: 将复杂任务分解为独立的子任务
- **并行执行**: 支持多个 Subagent 后台并行执行
- **Git Worktree**: 每个子任务在独立分支开发，避免冲突
- **状态追踪**: task-status.json 记录任务进度
- **系统通知**: 任务完成时发送 macOS 通知
- **自动合并**: 按完成顺序合并分支，处理冲突

## 使用

```bash
# 调研新方案，创建子任务
/research <query>

# 选择已有任务或新建
/research
```

## 文件结构

```
skills/research/
├── SKILL.md              # 主 Skill 定义
├── WORKFLOW.md           # 详细工作流程
├── EXECUTION-MODES.md    # 执行模式详解
├── TEMPLATES.md          # 文件模板
└── README.md             # 本文件

scripts/
├── setup-worktrees.sh    # 初始化 worktree
├── merge.sh              # 合并分支
└── notify.sh             # 发送通知
```

## 工作流

```
1. /research <query>     调研任务
2. [GATE-1] 创建任务目录
3. [GATE-2] 创建 task-status.json
4. [GATE-3] 创建 context 文件
5. [GATE-4] 询问用户执行方式
6. setup-worktrees.sh    创建独立工作分支（开发型任务）
7. 并行执行子任务         在各自 worktree 中开发
8. 完成通知              每个任务完成时通知
9. merge.sh              合并所有分支
```

## 执行模式

| 模式 | 适用场景 |
|------|----------|
| Subagent 后台并行 | 无依赖的独立任务 |
| 多终端手动启动 | 需要 MCP 或交互 |
| 当前进程顺序 | 简单任务或强依赖 |

详见 [EXECUTION-MODES.md](./EXECUTION-MODES.md)

## 脚本使用

```bash
# 初始化 worktree
./scripts/setup-worktrees.sh .claude/shared_files/<task>

# 任务通知
./scripts/notify.sh done p0 "任务名" "修改内容"
./scripts/notify.sh fail p0 "任务名" "错误信息"

# 合并分支
./scripts/merge.sh .claude/shared_files/<task>
```

## 输出目录

任务上下文写入：`<project-root>/.claude/shared_files/<yymmdd-task-slug>/`

```
<project-root>/.claude/shared_files/250113-my-task/
├── task-status.json      # 任务状态和元信息
├── context-common.md     # 共享上下文
├── context-p0-xxx.md     # 子任务 P0 上下文
├── context-p1-xxx.md     # 子任务 P1 上下文
└── ...
```
