# Onboarding Skill

新人指南生成工具，聚合项目文档生成上手指南。

## 命令格式

```bash
/onboarding                 # 生成项目上手指南
/onboarding <module>        # 生成模块指南
/onboarding --quick         # 快速入门版本
```

## 工作流程

```
Task Progress:
- [ ] 1. 分析项目结构
- [ ] 2. 提取关键文档
- [ ] 3. 聚合 ADR 和架构决策
- [ ] 4. 提取常见问题 (from postmortem)
- [ ] 5. 生成上手指南
```

### Step 1: 分析项目结构

```bash
# 获取目录结构
tree -L 2 -d

# 识别主要模块
fd -t d -d 1 . src/

# 分析技术栈
test -f package.json && jq '.dependencies | keys' package.json
test -f go.mod && rg "require" go.mod
test -f Cargo.toml && rg "^\[dependencies\]" -A 20 Cargo.toml
```

### Step 2: 提取关键文档

```bash
# README 和文档
fd README.md
fd -e md . docs/

# API 文档
fd -e yaml -e json . | rg "openapi\|swagger"

# 配置文件说明
fd -e example -e sample
```

### Step 3: 聚合架构决策

```bash
# ADR 列表 (如有)
fd ADR.md .claude/adr/

# 提取决策摘要
rg "## 决策" -A 5 .claude/adr/*/ADR.md

# 重要技术选型
rg "decision_status: accepted" .claude/adr/
```

### Step 4: 提取常见问题

```bash
# 高频 postmortem 类型
rg "category:" .claude/postmortem/ | sort | uniq -c | sort -rn

# 提取经验教训
rg "## 经验教训" -A 10 .claude/postmortem/*/REPORT.md

# 常见错误模式
rg "root_cause:" -A 3 .claude/postmortem/
```

## 指南模板

```yaml
---
type: onboarding
id: "250113-onboarding-guide"
created_at: "2025-01-13"
status: active
scope:
  modules: ["*"]
keywords: [onboarding, guide, getting-started]
---
```

```markdown
# 项目上手指南

## 快速开始

### 环境要求

| 工具 | 版本 |
|------|------|
| Node.js | >= 18 |
| pnpm | >= 8 |

### 安装步骤

```bash
# 克隆仓库
git clone <repo>

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

## 项目结构

```
src/
├── api/          # API 端点
├── auth/         # 认证模块
├── components/   # UI 组件
├── services/     # 业务逻辑
└── utils/        # 工具函数
```

## 技术栈

| 类型 | 技术 |
|------|------|
| 框架 | React 18 |
| 状态管理 | Zustand |
| API | REST + GraphQL |
| 数据库 | PostgreSQL |

## 核心模块

### 认证模块 (src/auth/)

负责用户认证和会话管理。

**关键文件**:
- `token.ts` - Token 管理
- `session.ts` - 会话管理

**相关文档**:
- [ADR-003: JWT vs Session](../.claude/adr/250105-jwt-session/ADR.md)

### API 模块 (src/api/)

RESTful API 实现。

**关键文件**:
- `user.ts` - 用户 API
- `auth.ts` - 认证 API

## 架构决策

以下是重要的架构决策，建议新人阅读：

| ADR | 标题 | 状态 |
|-----|------|------|
| ADR-001 | 选择 React 框架 | accepted |
| ADR-003 | JWT vs Session | accepted |
| ADR-005 | OAuth2 实现 | accepted |

## 常见问题

### 基于历史 Postmortem

以下是历史上常见的问题，请注意避免：

#### 1. Token 刷新竞态

**问题**: 并发请求同时刷新 token 导致认证失败

**避免方法**: 使用 `refreshToken` 时添加锁机制

**详情**: [Postmortem-250110](../.claude/postmortem/250110-token-race/REPORT.md)

#### 2. SQL 注入

**问题**: 字符串拼接 SQL 语句

**避免方法**: 始终使用参数化查询

**检查规则**: S01 in [RULES-CODE-QUALITY](../docs/RULES-CODE-QUALITY.md)

## 开发规范

### 代码风格

- 使用 ESLint + Prettier
- 遵循 Conventional Commits

### 提交前检查

```bash
# 运行 lint
pnpm lint

# 运行测试
pnpm test

# 安全扫描
/security-scan
```

### 代码审查

提交 PR 前请运行：
```bash
/review --staged
```

## 有用的命令

| 命令 | 说明 |
|------|------|
| `/review` | 代码审查 |
| `/tech-debt scan` | 扫描技术债务 |
| `/security-scan` | 安全检查 |
| `/test-strategy <module>` | 生成测试策略 |

## 联系方式

- 技术负责人: @lead
- Slack: #dev-team
```

## 输出位置

```
.claude/onboarding/
├── GUIDE.md            # 完整上手指南
└── <module>/
    └── GUIDE.md        # 模块指南
```
