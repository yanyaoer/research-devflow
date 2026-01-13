# 执行模式详解

## 前置准备：创建 Git Worktree

**并行执行前必须先创建 worktree**:

```bash
# 创建 worktrees 目录
mkdir -p .claude/shared_files/<yymmdd-task-slug>/worktrees

# 为每个并行任务创建独立 worktree
git worktree add .claude/shared_files/<yymmdd-task-slug>/worktrees/p0 -b research/<yymmdd-task-slug>/p0
git worktree add .claude/shared_files/<yymmdd-task-slug>/worktrees/p1 -b research/<yymmdd-task-slug>/p1
git worktree add .claude/shared_files/<yymmdd-task-slug>/worktrees/p2 -b research/<yymmdd-task-slug>/p2
```

## 模式选择流程

```
任务有依赖关系？
├─ 是 → 需要 MCP/交互？
│        ├─ 是 → 模式 C: 多终端手动
│        └─ 否 → 模式 B: Subagent 链式
└─ 否 → 需要 MCP/交互？
         ├─ 是 → 模式 C: 多终端手动
         └─ 否 → 模式 A: Subagent 后台并行
```

---

## 模式 A: Subagent 后台并行

**适用**: 无依赖的独立任务

**前置**: 已创建 worktree（见上文）

**实现**: 在同一消息中发送多个 Task 调用，每个任务指定自己的 worktree 目录

```
Task(
  description = "执行 P0 任务",
  prompt = "
1. cd .claude/shared_files/<yymmdd-task-slug>/worktrees/p0
2. 阅读 ../context-common.md 和 ../context-p0-xxx.md
3. 在当前 worktree 目录完成开发
4. git add -A && git commit -m 'feat: ...'
5. 更新 ../task-status.json
6. 发送通知: osascript -e 'display notification \"P0 完成\" with title \"Research\"'
",
  subagent_type = "general-purpose",
  run_in_background = true
)

Task(
  description = "执行 P1 任务",
  prompt = "
1. cd .claude/shared_files/<yymmdd-task-slug>/worktrees/p1
2. 阅读 ../context-common.md 和 ../context-p1-xxx.md
3. 在当前 worktree 目录完成开发
4. git add -A && git commit -m 'feat: ...'
5. 更新 ../task-status.json
6. 发送通知
",
  subagent_type = "general-purpose",
  run_in_background = true
)
```

**所有任务完成后，主进程负责合并**:
```bash
# 回到主项目目录
cd <project_root>
git checkout main

# 按完成顺序合并（检查 task-status.json 的 completed_at）
git merge research/<yymmdd-task-slug>/p0 --no-ff
git merge research/<yymmdd-task-slug>/p1 --no-ff  # 解决冲突如有
git merge research/<yymmdd-task-slug>/p2 --no-ff  # 解决冲突如有

# 清理
git worktree remove .claude/shared_files/<yymmdd-task-slug>/worktrees/p0
git worktree remove .claude/shared_files/<yymmdd-task-slug>/worktrees/p1
```

**特点**:
- 多个 Subagent 并发运行
- 自动继承父级权限
- 结果汇总到主对话

**限制**:
- Subagent 不能嵌套
- 后台任务不支持 MCP 工具
- 自动拒绝未预批准的操作

**快捷键**: `Ctrl+B` 将前台任务切换到后台

---

## 模式 B: Subagent 链式执行

**适用**: 有依赖关系的任务

**执行顺序**:
```
1. 并行执行所有无依赖任务 (P0, P1)
2. 等待完成
3. 执行依赖 P0 的任务 (P2)
4. 执行依赖 P0+P1 的任务 (P3)
```

**实现**:

```
# 第一批: 无依赖任务
Task(prompt="执行 P0", run_in_background=true)
Task(prompt="执行 P1", run_in_background=true)

# 等待第一批完成后
TaskOutput(task_id="<p0_id>", block=true)
TaskOutput(task_id="<p1_id>", block=true)

# 第二批: 依赖任务
Task(prompt="执行 P2 (依赖 P0)")
Task(prompt="执行 P3 (依赖 P0, P1)")
```

**Resume 继续执行**:

如果任务中断，可以使用 resume 参数继续:
```
Task(
  resume = "<previous_agent_id>",
  prompt = "继续完成任务"
)
```

---

## 模式 C: 多终端手动启动

**适用**: 需要 MCP 工具或交互式操作

**前置**: 已创建 worktree

**命令模板**:

```bash
# 终端 1 - P0 (在 worktree 中开发)
cd <project_dir>
claude "
1. cd .claude/shared_files/<yymmdd-task-slug>/worktrees/p0
2. 阅读上级目录的 context-common.md 和 context-p0-xxx.md
3. 在当前 worktree 完成所有开发
4. git add -A && git commit -m 'feat: ...'
5. 更新 ../task-status.json
6. osascript -e 'display notification \"P0 完成\" with title \"Research\" sound name \"Glass\"'
"

# 终端 2 - P1 (在 worktree 中开发)
claude "
1. cd .claude/shared_files/<yymmdd-task-slug>/worktrees/p1
2. 阅读上级目录的 context-common.md 和 context-p1-xxx.md
3. 在当前 worktree 完成所有开发
4. git add -A && git commit -m 'feat: ...'
5. 更新 ../task-status.json
6. osascript -e 'display notification \"P1 完成\" with title \"Research\" sound name \"Glass\"'
"
```

**所有任务完成后，手动合并**:
```bash
cd <project_dir>
git checkout main
git merge research/<yymmdd-task-slug>/p0 --no-ff
git merge research/<yymmdd-task-slug>/p1 --no-ff  # 谨慎解决冲突
```

**特点**:
- 完全独立的会话
- 支持交互式权限确认
- 支持 MCP 工具
- 需要手动监控状态

---

## 模式 D: 当前进程顺序执行

**适用**: 简单任务或强依赖链

**执行**:
```
我将在当前进程按以下顺序执行:
1. P0: <任务名>
2. P1: <任务名>
3. P2: <任务名> (依赖 P0)
...

每个任务完成后更新状态并发送通知。
```

**特点**:
- 无并行开销
- 完整上下文保留
- 适合调试和验证

---

## 通知命令参考

**成功通知**:
```bash
osascript -e 'display notification "P0: <任务名> 完成\n修改: file1, file2" with title "Research Task Done" sound name "Glass"'
```

**失败通知**:
```bash
osascript -e 'display notification "P0: <任务名> 失败\n原因: <错误信息>" with title "Research Task Failed" sound name "Basso"'
```

**全部完成通知**:
```bash
osascript -e 'display notification "所有任务已完成！" with title "Research Complete" sound name "Hero"'
```

---

## 状态监控

**检查任务状态**:
```bash
cat .claude/shared_files/<yymmdd-task-slug>/task-status.json | jq '.tasks[] | {id, name, status}'
```

**统计完成情况**:
```bash
cat .claude/shared_files/<yymmdd-task-slug>/task-status.json | jq '[.tasks[] | select(.status == "completed")] | length'
```

---

## 故障恢复

### Subagent 任务失败

1. 检查 output_file 获取错误信息
2. 使用 resume 参数继续
3. 或者切换到手动模式

### 依赖死锁

1. 检查循环依赖
2. 手动标记跳过的任务
3. 重新规划依赖关系

### 状态不一致

1. 手动检查实际完成情况
2. 修正 task-status.json
3. 重新发送通知
