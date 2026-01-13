# Dependency Skill

依赖管理工具，分析依赖状态、升级影响和安全漏洞。

## 命令格式

```bash
/dependency                 # 分析依赖状态
/dependency upgrade <pkg>   # 升级影响分析
/dependency audit           # 安全漏洞检查
/dependency outdated        # 列出过时依赖
```

## 工作流程

```
Task Progress:
- [ ] 1. 检测项目类型和包管理器
- [ ] 2. 分析依赖状态
- [ ] 3. 检查安全漏洞
- [ ] 4. 分析升级影响
- [ ] 5. 生成依赖报告
```

### Step 1: 检测项目类型

```bash
# Node.js
test -f package.json && echo "nodejs"

# Python
test -f requirements.txt && echo "python-pip"
test -f pyproject.toml && echo "python-poetry"
test -f Pipfile && echo "python-pipenv"

# Go
test -f go.mod && echo "go"

# Rust
test -f Cargo.toml && echo "rust"

# Java/Kotlin
test -f pom.xml && echo "maven"
test -f build.gradle && echo "gradle"
```

### Step 2: 分析依赖状态

```bash
# Node.js
npm outdated --json
npm ls --json

# Python
pip list --outdated --format=json
pip-audit --format=json

# Go
go list -m -u all
go mod graph

# Rust
cargo outdated --format json
cargo tree
```

### Step 3: 安全漏洞检查

```bash
# Node.js
npm audit --json

# Python
pip-audit --format=json
safety check --json

# Go
govulncheck ./...

# Rust
cargo audit --json
```

### Step 4: 升级影响分析

```bash
# 查找依赖使用位置
rg "from ['\"]<pkg>['\"]" --type ts --type js
rg "import.*<pkg>" --type py
rg "<pkg>" go.mod Cargo.toml

# 检索相关 postmortem
rg "keywords:.*<pkg>" .claude/postmortem/
```

## 报告模板

```yaml
---
type: dependency
id: "250113-dependency-report"
created_at: "2025-01-13"
status: active
scope:
  files: ["package.json", "go.mod"]
keywords: [dependency, upgrade, security]
---
```

```markdown
# 依赖分析报告

## 项目概览

| 指标 | 值 |
|------|-----|
| 包管理器 | npm |
| 直接依赖 | 45 |
| 间接依赖 | 320 |
| 过时依赖 | 12 |
| 安全漏洞 | 3 |

## 安全漏洞

| 包 | 当前版本 | 修复版本 | 严重程度 | CVE |
|----|----------|----------|----------|-----|
| lodash | 4.17.15 | 4.17.21 | high | CVE-2021-23337 |

## 过时依赖

| 包 | 当前版本 | 最新版本 | 类型 |
|----|----------|----------|------|
| react | 17.0.2 | 18.2.0 | major |
| axios | 0.21.1 | 1.6.0 | major |

## 升级建议

### 优先级 1: 安全修复

| 包 | 操作 | 风险 |
|----|------|------|
| lodash | 升级到 4.17.21 | 低 |

### 优先级 2: 主版本升级

| 包 | 操作 | 影响范围 |
|----|------|----------|
| react | 17 → 18 | 需要代码迁移 |
```

## 输出位置

```
.claude/dependency/
├── REPORT.md           # 依赖分析报告
└── audit.json          # 详细审计数据
```
