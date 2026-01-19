---
name: postmortem
description: "分析 bug/fix 相关提交，生成事故复盘报告。使用场景：用户说'复盘'、'事故分析'、'postmortem'，或需要分析线上问题、总结修复经验。"
---

```yaml:skill-config
name: postmortem
version: "1.0"
description: "分析 bug/fix 相关提交，生成事故复盘报告"

triggers:
  commands: ["/postmortem"]
  keywords: ["复盘", "事故分析", "postmortem", "根因分析"]

steps:
  - id: select_mode
    name: "选择分析模式"
    type: user_input
    options:
      - id: auto
        label: "自动扫描"
        description: "扫描 git 历史中的 bug/fix 提交"
      - id: select
        label: "手动选择"
        description: "从最近 30 个 commit 中选择"
      - id: jira
        label: "Jira 关联"
        description: "通过 Jira ID 获取关联 commit"
    description: "确定分析模式"

  - id: get_commits
    name: "获取 Commit 列表"
    type: command
    command: "git log --oneline --all --grep='fix\\|bug\\|hotfix\\|patch\\|issue\\|error\\|crash\\|revert' -50"
    dependencies: [select_mode]
    description: "获取待分析的 commit 列表"

  - id: select_commits
    name: "选择要分析的 Commits"
    type: user_input
    options: []
    dependencies: [get_commits]
    description: "让用户选择要分析的提交"

  - id: load_rules
    name: "加载分析规则"
    type: command
    command: "python scripts/rule_query.py --query postmortem --format json 2>/dev/null || echo '[]'"
    dependencies: [select_commits]
    description: "加载 postmortem 适用的规则"

  - id: analyze_changes
    name: "分析代码变更"
    type: prompt
    prompt_ref: "#analyze-changes-prompt"
    dependencies: [select_commits, load_rules]
    description: "逐行追踪代码变更"

  - id: backtrack_root_cause
    name: "回溯根因"
    type: prompt
    prompt_ref: "#backtrack-root-cause-prompt"
    dependencies: [analyze_changes]
    description: "找到引入问题的原始 commit"

  - id: analyze_call_chain
    name: "分析调用链"
    type: prompt
    prompt_ref: "#analyze-call-chain-prompt"
    dependencies: [analyze_changes]
    description: "分析函数调用链和影响范围"

  - id: security_assessment
    name: "安全性评估"
    type: prompt
    prompt_ref: "#security-assessment-prompt"
    dependencies: [analyze_call_chain]
    description: "进行安全性和健壮性评估"

  - id: generate_report
    name: "生成复盘报告"
    type: prompt
    prompt_ref: "#generate-postmortem-report-prompt"
    dependencies: [backtrack_root_cause, analyze_call_chain, security_assessment]
    description: "综合分析生成事故报告"

  - id: gate_report_complete
    name: "[GATE] 验证报告生成"
    type: gate_check
    validation: "test -f .claude/postmortem/${task_slug}/REPORT.md"
    on_failure: abort
    dependencies: [generate_report]
    description: "确保报告文件已生成"

  - id: send_notification
    name: "发送完成通知"
    type: command
    command: "osascript -e 'display notification \"Postmortem 报告已生成\" with title \"Postmortem Complete\" sound name \"Glass\"'"
    dependencies: [gate_report_complete]
    description: "发送系统通知"
```

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
- [ ] 0. 确认工具使用策略 (LSP > ast-grep > rg)
- [ ] 1. 解析参数，确定分析模式
- [ ] 2. 获取待分析的 commit 列表
- [ ] 3. 提取 Jira 信息（如适用，调用 jira_issue_analyzer）
- [ ] 4. 分析代码变更（逐行追踪）
- [ ] 4a. 回溯引入问题的 Commit (Root Cause Backtracking)
- [ ] 5. 分析函数调用链和影响范围
- [ ] 6. 进行安全性和健壮性评估
- [ ] 7. 综合分析生成事故报告 (区分主要/次要原因)
- [ ] 8. 总结经验教训和改进建议
- [ ] 9. 写入报告文件
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
- 直接尝试调用 `jira_issue_analyzer:root-cause <jira-id>`
- 如调用失败或提示 skill 不存在，跳过 Jira 信息提取步骤

如果可用，调用会返回：

提取信息：
- Jira 问题描述
- 问题隔离过程
- 日志信息
- 评论中的分析过程
- 关联的 commit ID

## 输出目录

报告写入：`<project-root>/.claude/postmortem/<yymmdd-issue-short-description>/`

```
<project-root>/.claude/postmortem/
└── 250113-fix-auth-token-expired/
    ├── REPORT.md           # 主报告
    ├── code-analysis.md    # 代码变更详细分析
    ├── call-chain.md       # 函数调用链分析
    └── commits.json        # 分析的 commit 元数据
```

## 共享规则引用

本 skill 使用以下共享规则：
- [代码质量规则](../../docs/RULES-CODE-QUALITY.md): 用于根因分类
- [LSP 配置指南](../../docs/common-lsp.md): 用于环境检查和工具配置

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

### Step 0: 工具使用策略

分析代码时，按以下优先级尝试工具（无需预先检查配置）：
1. **LSP**: 直接调用 `definition`、`references`、`hover`，失败则降级
2. **ast-grep**: 结构化语法匹配
3. **rg/grep**: 文本搜索兜底

**安装 LSP Plugin** (如需)：请参考 [README 安装指南](../../README.md#claude-code-extra-configuration)。

### Step 1: 提取变更信息

```bash
# 获取每个 commit 的详细变更
git show <commit-id> --stat
git show <commit-id> -p --no-color
```

### Step 2: 逐行追踪

对每个修改的文件，优先使用 LSP 工具理解上下文，准确度优于 grep。

**工具优先级**:
1. **LSP**: 使用 `definition` 查看函数实现，`references` 评估影响，`hover` 确认类型。
2. **CLI**: 降级使用 `git grep` 或 `ast-grep`。

```bash
# 查看文件修改历史
git log --oneline -p -S "<changed-function-name>" -- <file>

# 查看特定行的 blame
git blame -L <start>,<end> <file>
```

### Step 2.5: 回溯根因 (Root Cause Backtracking)

定位到 Fix 代码所修改的原始逻辑后，需要找到是谁、在什么 commit 中引入了这段问题代码。

```bash
# 1. 找到 fix commit 的 parent commit（即问题存在的状态）
git rev-parse <fix-commit>^

# 2. 在 parent commit 中对被修改行进行 blame
git blame <parent-commit> -L <start>,<end> -- <file>
```

对于识别出的 "Trying-to-fix" 或 "引入 Bug" 的 commit (Introducing Commit)：
1. 查看该 commit 的提交信息：`git show -s <intro-commit>`
2. 查看该 commit 的完整变更：`git show <intro-commit>`
3. 分析当时这样写的意图（是设计缺陷还是疏忽？）

这用于区分报告中的 `primary_cause` (根本原因) 和 `secondary_causes` (诱因)。

### Step 3: 函数调用链分析

识别所有被修改的函数，优先使用 LSP 工具分析上下游依赖，准确性显著优于 grep。

**LSP 方式 (推荐)**:
1. 对修改的函数名使用 `references` 查找所有上游调用点。
2. 对函数体内调用的外部函数使用 `definition` 理解下游依赖。

**Regex/AST 方式 (降级)**:
如果 LSP 不可用，使用 ast-grep 或 grep：

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
# === Postmortem 特有字段 ===
severity: P1
category: security
primary_cause:
  type: race_condition
  summary: "Token 刷新逻辑在并发请求下未加锁，导致旧 Token 失效后新请求仍使用旧 Token"
  introducing_commit: "abc1234 (2024-11-20)"
secondary_causes:
  - type: logic_error
    summary: "前端重试机制过于激进，加剧了并发竞争"
  - type: insufficient_testing
    summary: "缺乏并发场景的集成测试"
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

### 根本原因 (Primary Cause)
[直接导致问题的技术根因]

**引入 Commit**: `hash` (Title)
**引入原因分析**: [分析引入该代码时的上下文/意图]

### 次要原因 (Secondary Causes)
- [诱因 1]
- [环境因素/配置问题]

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

---

## Prompts

```markdown:analyze-changes-prompt
你是一个代码分析专家。请分析以下 commit 的代码变更。

**待分析 Commits**: ${selected_commits}
**适用规则**: ${rules}

**分析要求**:
1. 对每个 commit 执行 `git show <commit-id> -p --no-color` 获取详细变更
2. 逐行追踪每个修改，理解变更意图
3. 使用 LSP 工具（优先）或 ast-grep/rg（降级）理解上下文
4. 记录所有被修改的函数和文件

**工具使用优先级**:
1. LSP: definition, references, hover
2. ast-grep: 结构化语法匹配
3. rg: 文本搜索兜底

**输出**:
- 将变更分析结果存入 ${change_analysis}
- 将修改的函数列表存入 ${modified_functions}
- 将修改的文件列表存入 ${modified_files}
```

```markdown:backtrack-root-cause-prompt
基于代码变更分析，回溯找到引入问题的原始 commit。

**变更分析**: ${change_analysis}
**Fix Commits**: ${selected_commits}

**回溯步骤**:
1. 找到 fix commit 的 parent: `git rev-parse <fix-commit>^`
2. 在 parent 中对被修改行进行 blame: `git blame <parent> -L <start>,<end> -- <file>`
3. 识别 "Introducing Commit" - 引入问题代码的原始提交
4. 分析引入时的上下文和意图

**输出**:
- introducing_commit: 引入问题的 commit hash
- introducing_date: 引入日期
- introducing_reason: 当时为什么这样写（设计缺陷/疏忽/需求变更）
- primary_cause: 根本原因类型 (race_condition/logic_error/null_pointer/etc)
- secondary_causes: 次要原因列表

将结果存入 ${root_cause_analysis}
```

```markdown:analyze-call-chain-prompt
分析被修改函数的调用链和影响范围。

**修改的函数**: ${modified_functions}
**修改的文件**: ${modified_files}

**分析要求**:

使用 LSP 工具（优先）或 CLI 工具：

1. **上游调用**: 使用 `references` 查找所有调用点（至少 2 层）
2. **下游依赖**: 使用 `definition` 理解调用的外部函数
3. **数据流**: 追踪数据在函数间的流转

如果 LSP 不可用，降级使用:
```bash
ast-grep -p '<function-name>($$$)' --lang <language>
rg '<function-name>\s*\(' --type <filetype>
```

**输出**:
- 调用链图（文本格式）
- 影响范围评估
- 潜在的副作用

将结果存入 ${call_chain_analysis}
```

```markdown:security-assessment-prompt
对代码变更进行安全性和健壮性评估。

**变更分析**: ${change_analysis}
**调用链分析**: ${call_chain_analysis}
**适用规则**: ${rules}

**检查清单**:
- [ ] 输入验证是否完整
- [ ] 边界条件是否处理
- [ ] 错误处理是否充分
- [ ] 资源释放是否正确
- [ ] 并发安全是否保证
- [ ] 敏感数据是否保护

**规则匹配**:
对每个问题代码片段，匹配适用规则：
- 记录规则 ID 到 matched_rules
- 使用规则的 postmortem_action 指导分析

**输出**:
- 安全问题列表
- 健壮性问题列表
- 匹配的规则 ID 列表

将结果存入 ${security_assessment}
```

```markdown:generate-postmortem-report-prompt
综合所有分析结果，生成完整的事故复盘报告。

**输入数据**:
- 变更分析: ${change_analysis}
- 根因分析: ${root_cause_analysis}
- 调用链分析: ${call_chain_analysis}
- 安全评估: ${security_assessment}
- 任务标识: ${task_slug}

**报告结构**:

1. YAML Frontmatter（严格遵循 META-SCHEMA）:
   - type: postmortem
   - id, created_at, status, author
   - scope: modules, functions, files, apis, tables
   - keywords
   - relevance: must_read, consider, skip_if
   - refs: jira, commits, related
   - severity, category
   - primary_cause, secondary_causes
   - matched_rules

2. 报告正文:
   - 基本信息表格
   - 事故时间线
   - 事故描述（现象、根本原因、次要原因、触发条件）
   - 代码分析（问题代码、修复代码、影响分析）
   - 复现步骤
   - 修复方案（即时修复、长期改进）
   - 经验教训（对 AI/人类的建议）
   - 预防措施

**输出位置**:
.claude/postmortem/${task_slug}/REPORT.md
.claude/postmortem/${task_slug}/code-analysis.md
.claude/postmortem/${task_slug}/call-chain.md
.claude/postmortem/${task_slug}/commits.json

确保目录存在后写入文件。
```
