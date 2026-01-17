# Tech-Debt Skill

技术债务追踪工具，扫描和管理代码中的技术债务。

## 命令格式

```bash
/tech-debt                  # 列出所有债务
/tech-debt scan             # 扫描代码中的 TODO/FIXME/HACK
/tech-debt add <desc>       # 记录新债务
/tech-debt report           # 生成债务报告
```

## 工作流程

```
Task Progress:
- [ ] 1. 解析参数确定操作模式
- [ ] 2. 扫描代码中的债务标记
- [ ] 3. 读取已有债务记录
- [ ] 4. 分类和优先级排序
- [ ] 5. 生成/更新债务报告
```

### Step 1: 扫描代码债务标记

```bash
# 扫描 TODO/FIXME/HACK/XXX 标记
rg "TODO|FIXME|HACK|XXX" \
  --type ts --type js --type py --type go --type rust --type java --type kotlin \
  -n --column

# 带上下文扫描
rg "TODO|FIXME|HACK|XXX" \
  --type ts --type js --type py --type go --type rust --type java --type kotlin \
  -B 1 -A 2
```

### Step 2: 分类债务

| 标记 | 分类 | 优先级 |
|------|------|--------|
| FIXME | bug | high |
| HACK | workaround | high |
| TODO | feature | medium |
| XXX | attention | medium |

### Step 3: 检索相关 postmortem

```bash
# 检索因技术债务导致的事故
rg "root_cause:" -A 3 .claude/postmortem/ | rg "tech.debt\|workaround\|temporary"

# 检索相关改进建议
rg "## 长期改进" -A 10 .claude/postmortem/*/REPORT.md
```

### Step 4: 生成报告

输出到：`<project-root>/.claude/tech-debt/REPORT.md`

## 债务记录格式

```yaml
---
type: tech-debt
id: "250113-tech-debt-report"
created_at: "2025-01-13"
updated_at: "2025-01-13"
status: active
scope:
  files: ["src/**/*.ts", "src/**/*.py"]
keywords: [tech-debt, todo, fixme, hack]
---
```

## 报告模板

```markdown
# 技术债务报告

## 概览

| 分类 | 数量 | 高优先级 |
|------|------|----------|
| FIXME | 5 | 5 |
| HACK | 3 | 3 |
| TODO | 20 | 0 |
| XXX | 2 | 0 |
| **合计** | **30** | **8** |

## 高优先级债务

### FIXME

| 位置 | 内容 | 建议 |
|------|------|------|
| src/auth/token.ts:45 | FIXME: race condition | 添加锁机制 |
| src/api/user.ts:123 | FIXME: SQL injection risk | 使用参数化查询 |

### HACK

| 位置 | 内容 | 建议 |
|------|------|------|
| src/utils/cache.ts:89 | HACK: temporary workaround | 重构缓存策略 |

## TODO 列表

| 位置 | 内容 | 关联 |
|------|------|------|
| src/components/Form.tsx:12 | TODO: add validation | - |
| src/services/email.ts:56 | TODO: implement retry | - |

## 相关历史问题

以下 postmortem 与技术债务相关：

| 问题 | 根因 | 相关债务 |
|------|------|----------|
| [250110-race-condition](...) | 临时方案未清理 | src/auth/token.ts:45 |

## 改进建议

基于历史 postmortem 的长期改进建议：
1. 定期清理 FIXME 和 HACK
2. TODO 超过 30 天自动升级优先级
3. 新增债务必须关联 Jira ticket
```

## 手动添加债务

```bash
/tech-debt add "重构用户认证模块，当前实现过于复杂"
```

添加到 `.claude/tech-debt/manual.md`:

```yaml
- id: TD-001
  created_at: "2025-01-13"
  description: "重构用户认证模块，当前实现过于复杂"
  priority: medium
  related_files: ["src/auth/"]
  status: open
```

## 输出位置

```
<project-root>/.claude/tech-debt/
├── REPORT.md           # 自动生成的债务报告
├── manual.md           # 手动添加的债务记录
└── history/            # 历史报告存档
    └── 250113-report.md
```
