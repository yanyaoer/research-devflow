# Research DevFlow

将传统软件工程的规划、开发、测试、发布流程抽象为 AI 可执行的自动化任务。

每个任务执行时自动检索历史沉淀的故障复盘、代码规则、技术决策等知识，

避免重复踩坑，持续提升团队交付效率和质量。

## TL;DR

```
规划设计 ──► 开发实现 ──► 质量保障 ──► 发布运维 ──► 知识沉淀
   │            │            │            │            │
/research    /review     /security    /release    /postmortem
/onboarding  /tech-debt  /test-strategy /dependency
```

| 阶段 | Skill | 一句话用法 |
|------|-------|-----------|
| 规划 | `/research <任务描述>` | 拆解任务，并行开发 |
| 审查 | `/review` | 检查暂存区代码质量 |
| 复盘 | `/postmortem` | 分析 bug 根因，沉淀经验 |
| 债务 | `/tech-debt scan` | 扫描 TODO/FIXME/HACK |
| 测试 | `/test-strategy <module>` | 生成模块测试策略 |
| 安全 | `/security-scan` | 检查注入/泄露风险 |
| 依赖 | `/dependency audit` | 检查依赖漏洞 |
| 发布 | `/release changelog` | 生成变更日志 |
| 上手 | `/onboarding` | 生成项目指南 |

## 安装

```bash
# 添加 marketplace
/plugin marketplace add https://github.com/yanyaoer/research-devflow

# 安装
/plugin install research-devflow@yanyaoer-plugins
```

<details>
<summary>其他安装方式</summary>

### 本地安装

```bash
git clone https://github.com/yanyaoer/research-devflow ~/Projects/research-devflow
/plugin marketplace add ~/Projects/research-devflow
```

### 配置文件

```json
{
  "enabledPlugins": {
    "research-devflow@yanyaoer-plugins": true
  },
  "extraKnownMarketplaces": {
    "yanyaoer-plugins": {
      "source": { "source": "directory", "path": "/path/to/research-devflow" }
    }
  }
}
```

</details>

---

## 最佳实践

### 1. 积累项目资产，加速迭代

**目标**: 让每次开发都能复用历史经验，避免重复踩坑。

```bash
# 开发完成后，审查代码
/review

# 发现 bug 后，复盘根因
/postmortem

# 定期扫描技术债务
/tech-debt scan
```

**资产沉淀结构**:
```
.claude/
├── postmortem/           # 事故复盘 → 避免重蹈覆辙
│   └── 250113-auth-bug/
│       └── REPORT.md     # 根因、修复、教训
├── reviews/              # 审查记录 → 追溯决策
├── tech-debt/            # 债务清单 → 持续改进
└── shared_files/         # 任务上下文 → 恢复工作
```

**迭代复用**:
```bash
# review 时自动检索相关 postmortem
/review --pr 123
# → 发现: 本次修改涉及 src/auth/，关联历史问题 250113-auth-bug

# 新任务自动关联历史上下文
/research 优化认证性能
# → 加载: 相关 postmortem 和 tech-debt 记录
```

---

### 2. 新项目规划与架构设计

**目标**: 从 0 到 1 建立项目结构，沉淀关键决策。

#### Step 1: 拆解大任务

```bash
/research 搭建电商后台系统
```

自动生成任务结构:
```
.claude/shared_files/250113-ecommerce-backend/
├── task-status.json      # 任务状态追踪
├── context-common.md     # 技术选型、架构约定
├── context-p0-auth.md    # 子任务: 认证模块
├── context-p1-product.md # 子任务: 商品模块
└── context-p2-order.md   # 子任务: 订单模块
```

#### Step 2: 并行开发

```bash
# 各子任务独立分支开发
./scripts/setup-worktrees.sh .claude/shared_files/250113-ecommerce-backend

# 完成后合并
./scripts/merge.sh .claude/shared_files/250113-ecommerce-backend
```

#### Step 3: 安全与质量检查

```bash
# 代码审查
/review

# 安全扫描
/security-scan

# 测试策略
/test-strategy src/
```

#### Step 4: 沉淀架构决策

在开发过程中遇到的重要决策，通过 postmortem 或独立文档记录:
- 为什么选择 JWT 而不是 Session？
- 为什么使用 PostgreSQL 而不是 MongoDB？
- 微服务边界如何划分？

---

### 3. 新人快速上手

**目标**: 新人 Day 1 即可产出，降低质量风险。

#### 生成上手指南

```bash
/onboarding
```

自动聚合:
- 项目结构和技术栈
- 关键架构决策 (ADR)
- 常见问题 (来自 postmortem)
- 开发规范和检查命令

#### 新人开发流程

```bash
# 1. 阅读上手指南
cat .claude/onboarding/GUIDE.md

# 2. 领取任务后，查看相关上下文
/research --list  # 查看进行中的任务

# 3. 提交前自检
/review --staged  # 代码审查
/security-scan    # 安全检查

# 4. 遇到问题，查阅历史
rg "关键词" .claude/postmortem/  # 搜索历史问题
```

#### 质量保障闭环

```
新人提交 PR
     │
     ▼
/review ──► 发现风险 ──► 关联 postmortem ──► 学习历史教训
     │
     ▼
通过检查 ──► 合并 ──► 积累新的审查记录
```

---

## Skills 详情

### 开发核心

| Skill | 命令 | 说明 |
|-------|------|------|
| [research](skills/research/) | `/research <query>` | 任务拆解，并行开发 |
| [postmortem](skills/postmortem/) | `/postmortem` | 事故复盘，根因分析 |
| [review](skills/review/) | `/review [target]` | 代码审查，风险检测 |

### 质量保障

| Skill | 命令 | 说明 |
|-------|------|------|
| [tech-debt](skills/tech-debt/) | `/tech-debt scan` | 债务追踪，清理提醒 |
| [test-strategy](skills/test-strategy/) | `/test-strategy <module>` | 测试策略，覆盖分析 |
| [security-scan](skills/security-scan/) | `/security-scan` | 安全扫描，漏洞检测 |

### 持续改进

| Skill | 命令 | 说明 |
|-------|------|------|
| [dependency](skills/dependency/) | `/dependency audit` | 依赖分析，漏洞检查 |
| [release](skills/release/) | `/release changelog` | 变更日志，发布说明 |
| [onboarding](skills/onboarding/) | `/onboarding` | 上手指南，知识聚合 |

## 共享资源

| 文件 | 说明 |
|------|------|
| [docs/META-SCHEMA.md](docs/META-SCHEMA.md) | 统一文档元信息格式 |
| [docs/RULES-CODE-QUALITY.md](docs/RULES-CODE-QUALITY.md) | 通用代码质量规则 (16 条，9 种语言) |
| [docs/RULES-ANDROID.md](docs/RULES-ANDROID.md) | Android 代码质量规则 (18 条，性能/健壮性) |
| [scripts/rule_query.py](scripts/rule_query.py) | 规则查询工具 (支持自动发现多规则文件) |

## 依赖工具

Skills 使用以下工具进行代码分析，建议提前安装：

```bash
# macOS (Homebrew)
brew install ripgrep fd ast-grep jq

# Ubuntu/Debian
sudo apt install ripgrep fd-find jq
# ast-grep 需要 cargo 安装
cargo install ast-grep

# Arch Linux
sudo pacman -S ripgrep fd ast-grep jq
```

| 工具 | 用途 | 必需 |
|------|------|------|
| [ripgrep](https://github.com/BurntSushi/ripgrep) (rg) | 代码搜索、规则检查 | ✓ |
| [fd](https://github.com/sharkdp/fd) | 快速文件查找 | ✓ |
| [ast-grep](https://github.com/ast-grep/ast-grep) | AST 结构搜索 | 推荐 |
| [jq](https://github.com/jqlang/jq) | JSON 处理 | 推荐 |

## Claude Code Extra Configuration

为了启用高级代码智能分析 (Code Intelligence) 和 LSP 支持，提升 `research`、`review` 和 `postmortem` 的效果，建议添加以下 LSP 配置。

### 1. LSP Plugin 安装

对于大多数语言，使用 Claude Code Plugin 即可一键安装：

```bash
# Go
/plugin add gopls-lsp

# Python
/plugin add pyright-lsp

# TypeScript / JavaScript
/plugin add typescript-lsp

# Rust
/plugin add rust-analyzer-lsp
```

*注意：上述插件依赖系统 PATH 中已安装对应的 Language Server CLI (如 `gopls`, `pyright`, `rust-analyzer`)。*

### 2. Java 支持 (jdtls)

Java 支持需要手动配置 `jdtls`。请将以下内容添加到你的 `.claude/settings.json`：

```json
{
  "lsp": {
    "java": {
      "command": "/path/to/jdtls",
      "args": [
        "-data", "/tmp/jdtls-workspace"
      ],
      "rootMarkers": ["pom.xml", "build.gradle", "build.gradle.kts", ".project"],
      "initializationOptions": {
        "settings": {
          "java": {
            "home": "/path/to/jdk-home",
            "format": { "enabled": true }
          }
        }
      }
    }
  }
}
```

更多配置详情请参考 [LSP 配置指南](docs/common-lsp.md)。

## 推荐搭配

- [claude-hud](https://github.com/jarrodwatts/claude-hud) - 状态栏显示任务进度，实时监控 Subagent 执行状态

## License

MIT
