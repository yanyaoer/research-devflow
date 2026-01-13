# Phase 0: 基础设施 - 共享上下文

## 项目背景

research-devflow 是一个 Claude Code 插件，目标是将开发流程各环节抽象为 skill 工具，通过知识沉淀提高团队效率。当前已完成 research 和 postmortem skill，需要统一 meta schema 以支持 AI 检索。

## 项目结构

```
research-devflow/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── commands/
│   ├── research.md
│   └── postmortem.md
├── skills/
│   ├── research/
│   │   ├── SKILL.md
│   │   ├── WORKFLOW.md
│   │   ├── EXECUTION-MODES.md
│   │   └── TEMPLATES.md
│   └── postmortem/
│       └── SKILL.md
├── scripts/
│   ├── setup-worktrees.sh
│   ├── merge.sh
│   └── notify.sh
└── TODO.md
```

## 统一 Meta Schema (已确认)

所有 skill 产出文档使用统一的 YAML frontmatter:

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

# === Skill 特有字段 (按类型扩展) ===
# postmortem 特有:
severity: P1
category: security
root_cause:
  type: race_condition
  pattern: "..."
---
```

## 检索命令参考

```bash
# 扫描所有知识文档
fd -e md . .claude/ | xargs rg -l "^type:"

# 按 scope.modules 匹配
rg "modules:.*src/auth" .claude/

# 按 keywords 匹配
rg "keywords:.*\[.*token.*\]" .claude/

# 提取 frontmatter
sed -n '/^---$/,/^---$/p' .claude/postmortem/*/REPORT.md
```

## 构建命令

无需构建，直接编辑 markdown 文件。

## Git 提交规范

```bash
git add -A && git commit -m "docs(meta-schema): <description>"
```

## 任务状态更新

完成任务后:
1. 更新 task-status.json
2. 发送通知: `osascript -e 'display notification "PX: 任务名 完成" with title "Phase0" sound name "Glass"'`
3. Git 提交
