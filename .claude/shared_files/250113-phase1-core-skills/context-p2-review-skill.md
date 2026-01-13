# P2: 创建 review skill

## 任务目标

创建代码审查 skill，实现事前代码质量检查，与 postmortem 联动。

## 依赖任务

- P1: 创建 rule_query.py 查询脚本

## 功能设计

```bash
/review                     # 审查暂存区变更
/review <commit>            # 审查指定 commit
/review <branch>            # 审查分支与 main 的 diff
/review --pr <number>       # 审查 PR (需要 gh CLI)
```

## 实现步骤

### Step 1: 创建 SKILL.md

**文件**: `skills/review/SKILL.md`

核心工作流：
```
Task Progress:
- [ ] 1. 获取变更文件列表
- [ ] 2. 加载适用规则 (rule_query.py --query review)
- [ ] 3. 检索相关 postmortem
- [ ] 4. 逐文件执行检查
- [ ] 5. 生成审查报告
- [ ] 6. 输出风险提示
```

### Step 2: 报告格式

```markdown
---
type: review
id: "250113-review-pr-123"
created_at: "2025-01-13"
status: active
scope:
  files: ["src/auth/login.ts", "src/api/user.ts"]
  functions: ["validateUser", "createSession"]
keywords: [auth, session, login]
refs:
  pr: "123"
  commits: ["abc1234"]

# review 特有
risk_level: medium
issues_count: 3
---

# 代码审查报告

## 变更概览

| 文件 | 新增 | 删除 | 风险 |
|------|------|------|------|
| src/auth/login.ts | +50 | -10 | high |

## 检查结果

### Critical (必须修复)

- **S01: SQL 注入风险** @ src/api/user.ts:45
  ```typescript
  // 问题代码
  db.query(`SELECT * FROM users WHERE id = ${userId}`)
  ```
  建议: 使用参数化查询

### High (应该修复)

- **R01: 空值处理缺失** @ src/auth/login.ts:23
  ...

## 相关 Postmortem

以下历史问题与本次变更相关：
- [250110-sql-injection-incident](.claude/postmortem/250110-sql-injection-incident/REPORT.md)
  - 影响: src/api/
  - 注意: 同类型问题

## 总结

| 风险等级 | 数量 |
|----------|------|
| Critical | 1 |
| High | 2 |
| Medium | 0 |
| Low | 0 |
```

### Step 3: 创建 command

**文件**: `commands/review.md`

## 涉及文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `skills/review/SKILL.md` | 新建 | Review skill 定义 |
| `commands/review.md` | 新建 | 命令入口 |

## 验证方法

```bash
# 测试规则加载
python scripts/rule_query.py --query review --format markdown

# 测试变更获取
git diff --name-only HEAD~1

# 测试 postmortem 检索
rg "modules:.*src/auth" .claude/postmortem/
```

## 完成标准

- [ ] 创建 skills/review/SKILL.md
- [ ] 创建 commands/review.md
- [ ] 支持多种输入方式 (staged/commit/branch/pr)
- [ ] 集成 rule_query.py 获取规则
- [ ] 自动检索相关 postmortem
- [ ] 生成结构化审查报告
- [ ] 更新 task-status.json
