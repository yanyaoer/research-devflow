---
name: postmortem
description: "分析 bug/fix 相关提交，生成事故复盘报告。使用场景：用户说'复盘'、'事故分析'、'postmortem'，或需要分析线上问题、总结修复经验。"
---

# Postmortem - 事故复盘与根因分析

## 快速开始

```bash
/postmortem                    # 自动分析 git 历史中的 bug/fix 提交
/postmortem --select           # 手动选择 commit 进行分析
/postmortem <jira-id>          # 通过 Jira ID 获取关联 commit 进行分析
```

## 核心工作流

```
Task Progress:
- [ ] 1. 解析参数，确定分析模式
- [ ] 2. 获取待分析的 commit 列表
- [ ] 3. 检查 jira_issue_analyzer 可用性（如有 Jira ID）
- [ ] 4. 提取 Jira 信息（如适用）
- [ ] 5. 分析代码变更（逐行追踪）
- [ ] 6. 分析函数调用链和影响范围
- [ ] 7. 进行安全性和健壮性评估
- [ ] 8. 综合分析生成事故报告
- [ ] 9. 总结经验教训和改进建议
- [ ] 10. 写入报告文件
```

## 参数解析

### 模式 1: 自动扫描（默认）

无参数时，扫描 git 历史中包含以下关键词的提交：
- `fix`, `bug`, `hotfix`, `patch`
- `issue`, `error`, `crash`, `fault`
- `revert`, `rollback`

```bash
git log --oneline --all --grep="fix\|bug\|hotfix\|patch\|issue\|error\|crash\|revert" -50
```

列出匹配的 commit，使用 AskUserQuestion 让用户选择要分析的提交。

### 模式 2: 手动选择（--select）

```bash
git log --oneline -30
```

使用 AskUserQuestion 提供最近 30 个 commit 供多选。

### 模式 3: Jira 关联

检查 `jira_issue_analyzer` skill 是否可用：
```bash
# 检查 skill 是否存在
ls ~/.claude/plugins/*/skills/jira_issue_analyzer/SKILL.md 2>/dev/null || \
ls ./.claude-plugin/../skills/jira_issue_analyzer/SKILL.md 2>/dev/null
```

如果可用，调用：
```
jira_issue_analyzer:root-cause <jira-id>
```

提取信息：
- Jira 问题描述
- 问题隔离过程
- 日志信息
- 评论中的分析过程
- 关联的 commit ID

## 输出目录

报告写入：`.claude/postmortem/<yymmdd-issue-short-description>/`

```
.claude/postmortem/
└── 250113-fix-auth-token-expired/
    ├── REPORT.md           # 主报告
    ├── code-analysis.md    # 代码变更详细分析
    ├── call-chain.md       # 函数调用链分析
    └── commits.json        # 分析的 commit 元数据
```

## 共享规则引用

本 skill 使用以下共享规则进行根因分类：
- [代码质量规则](../../docs/RULES-CODE-QUALITY.md)

### 加载规则

```bash
# 获取 postmortem 适用的规则
python scripts/rule_query.py --query postmortem --format json

# 按分类获取
python scripts/rule_query.py --query postmortem --category security --format json
```

### 根因分类映射

| 规则 ID | 根因类型 | 分析重点 |
|---------|----------|----------|
| S01-S05 | security | 追溯攻击路径 |
| R01-R05 | robustness | 还原触发条件 |
| P01-P03 | performance | 分析性能瓶颈 |

## 代码分析流程

### Step 1: 提取变更信息

```bash
# 获取每个 commit 的详细变更
git show <commit-id> --stat
git show <commit-id> -p --no-color
```

### Step 2: 逐行追踪

对每个修改的文件：

```bash
# 查看文件修改历史
git log --oneline -p -S "<changed-function-name>" -- <file>

# 查看特定行的 blame
git blame -L <start>,<end> <file>
```

### Step 3: 函数调用链分析

识别所有被修改的函数，分析：
- 该函数被哪些地方调用（上游影响）
- 该函数调用了哪些其他函数（下游依赖）
- 修改是否影响函数签名或返回值

```bash
# 使用 ast-grep 或 grep 查找调用点
ast-grep -p '<function-name>($$$)' --lang <language>
rg '<function-name>\s*\(' --type <filetype>
```

### Step 4: 安全性和健壮性评估

检查项：
- [ ] 输入验证是否完整
- [ ] 边界条件是否处理
- [ ] 错误处理是否充分
- [ ] 资源释放是否正确
- [ ] 并发安全是否保证
- [ ] 敏感数据是否保护

### Step 5: 规则匹配分析

对每个问题代码片段，检查匹配的规则：

```bash
# 获取所有规则的检查命令
python scripts/rule_query.py --query postmortem --format json | \
  jq -r '.rules[] | .check_command'

# 在问题文件上执行检查
<check_command> <file>
```

匹配规则后：
1. 记录规则 ID 到报告的 `matched_rules` 字段
2. 使用规则的 `postmortem_action` 指导深入分析
3. 关联已有的 review 发现（如有）

## 报告格式

### REPORT.md 模板

```markdown
---
# === 基础信息 ===
type: postmortem
id: "250113-fix-auth-token-expired"
created_at: "2025-01-13"
updated_at: "2025-01-13"
status: active
author: "username"

# === 影响范围 (AI 检索核心) ===
scope:
  modules: ["src/auth/", "src/middleware/"]
  functions: ["validateToken", "refreshAuthToken", "AuthMiddleware.verify"]
  files: ["src/auth/**/*.ts", "src/services/user*.ts"]
  apis: ["POST /api/auth/refresh", "GET /api/user/*"]
  tables: ["user_sessions", "auth_tokens"]

# === 语义匹配 ===
keywords: [token, authentication, session, JWT, expiry, refresh]

# === 相关性判断 ===
relevance:
  must_read: ["修改 token 验证或刷新逻辑", "修改认证中间件"]
  consider: ["添加新的认证保护端点"]
  skip_if: ["仅修改 UI 样式", "与认证无关的业务逻辑"]

# === 关联引用 ===
refs:
  jira: "PROJ-1234"
  commits: ["abc1234", "def5678"]
  related: []

# === Postmortem 特有字段 ===
severity: P1
category: security
root_cause:
  type: race_condition
  pattern: "async token refresh without lock"
  matched_rules: ["R03"]

# === Review 关联 ===
related_reviews:
  - id: "250110-review-pr-120"
    finding: "R03 检查未通过但被忽略"
---

# 事故复盘报告

## 基本信息

| 字段 | 值 |
|------|-----|
| 报告日期 | YYYY-MM-DD |
| 事故级别 | P0/P1/P2/P3 |
| 影响范围 | 描述受影响的功能/用户 |
| Jira ID | （如有）|
| 相关 Commits | commit1, commit2, ... |

## 事故时间线

| 时间 | 事件 |
|------|------|
| YYYY-MM-DD HH:MM | 问题首次发现 |
| YYYY-MM-DD HH:MM | 修复提交 |
| ... | ... |

## 事故描述

### 现象
[用户视角的问题表现]

### 根本原因
[技术层面的根因分析]

### 触发条件
[什么情况下会触发此问题]

## 代码分析

### 问题代码

```<language>
// 问题代码片段
```

### 修复代码

```<language>
// 修复后的代码片段
```

### 变更影响分析

[对函数调用链和系统的影响分析]

## 复现步骤

1. Step 1
2. Step 2
3. ...

## 修复方案

### 即时修复
[已实施的修复措施]

### 长期改进
[需要后续跟进的改进项]

## 经验教训

### 问题根源

- [ ] 代码设计缺陷
- [ ] 测试覆盖不足
- [ ] 代码审查遗漏
- [ ] 文档不完善
- [ ] 其他: ___

### 对 AI 编码工具的建议

[针对 Claude Code 等 AI 编码助手的改进建议]

### 对人工编码的建议

[针对人类开发者的改进建议]

### 流程改进

[对开发、测试、发布流程的改进建议]

## 预防措施

| 措施 | 责任人 | 截止日期 | 状态 |
|------|--------|----------|------|
| 添加单元测试 | - | - | TODO |
| 更新文档 | - | - | TODO |
| ... | - | - | TODO |

## 附录

- [代码变更详细分析](./code-analysis.md)
- [函数调用链分析](./call-chain.md)
```

## 事故级别定义

| 级别 | 描述 | 示例 |
|------|------|------|
| P0 | 核心功能完全不可用 | 登录失败、支付崩溃 |
| P1 | 核心功能严重受损 | 数据丢失、安全漏洞 |
| P2 | 非核心功能异常 | 报表延迟、UI 错位 |
| P3 | 体验问题 | 性能下降、文案错误 |

## Jira 集成

当提供 Jira ID 且 `jira_issue_analyzer` 可用时：

```
调用: jira_issue_analyzer:root-cause <jira-id>

提取内容:
- description: Jira 问题描述
- isolation: 问题隔离过程
- logs: 相关日志信息
- comments: 评论中的分析过程
- commits: 关联的 commit 列表
```

将提取的信息整合到报告的对应章节。

## 分析深度要求

### 代码层面
1. **变更内容**: 逐行分析每个修改
2. **历史追溯**: 该代码之前的演变过程
3. **作者追踪**: 相关代码的贡献者
4. **测试覆盖**: 是否有对应的测试用例

### 系统层面
1. **影响范围**: 修改影响的模块和功能
2. **调用链路**: 上下游依赖关系
3. **数据流向**: 数据如何在系统中流转
4. **边界条件**: 极端情况的处理

### 安全层面
1. **注入风险**: SQL/命令/XSS 等注入
2. **认证授权**: 身份验证和权限控制
3. **数据保护**: 敏感信息的处理
4. **并发安全**: 竞态条件和死锁

## 质量保证

- 报告必须基于实际代码分析，不能凭空推测
- 所有引用的代码片段必须是真实的
- 事故级别评估要客观准确
- 改进建议要具体可执行
- 对 AI 和人类开发者的建议要有区分度

## 历史问题检索

分析新问题前，检索类似历史问题避免重复：

```bash
# 按影响模块检索
rg "modules:.*<module>" .claude/postmortem/

# 按关键词检索
rg "keywords:.*<keyword>" .claude/postmortem/

# 按根因类型检索
rg "root_cause:" -A 2 .claude/postmortem/ | rg "<type>"

# 按严重程度检索
rg "severity: P0" .claude/postmortem/
rg "severity: P1" .claude/postmortem/

# 按分类检索
rg "category: security" .claude/postmortem/

# 提取所有 postmortem 的 frontmatter
fd REPORT.md .claude/postmortem/ -x sed -n '/^---$/,/^---$/p' {}
```

**检索时机**:
- 开始分析新问题前
- 识别到相似模式时
- 撰写改进建议时参考历史教训

## 通知

分析完成后发送系统通知：

```bash
osascript -e 'display notification "Postmortem 报告已生成" with title "Postmortem Complete" sound name "Glass"'
```
