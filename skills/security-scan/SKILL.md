# Security-Scan Skill

安全检查工具，复用共享规则进行安全扫描。

## 命令格式

```bash
/security-scan              # 全量扫描
/security-scan <file>       # 扫描指定文件
/security-scan <dir>        # 扫描指定目录
/security-scan --category <cat>  # 按分类扫描
```

## 支持的分类

| 分类 | 规则 ID | 说明 |
|------|---------|------|
| injection | S01, S03 | SQL 注入、命令注入 |
| xss | S02 | 跨站脚本 |
| auth | S04 | 认证绕过 |
| leak | S05 | 敏感信息泄露 |

## 共享规则引用

本 skill 复用以下共享规则：
- [代码质量规则 - 安全类](../../docs/RULES-CODE-QUALITY.md#安全类-security)

## 工作流程

```
Task Progress:
- [ ] 1. 加载安全类规则
- [ ] 2. 确定扫描范围
- [ ] 3. 执行规则检查命令
- [ ] 4. 检索相关安全类 postmortem
- [ ] 5. 生成安全报告
```

### Step 1: 加载安全类规则

```bash
# 获取所有安全类规则
python scripts/rule_query.py --query review --category security --format json

# 输出示例
{
  "scenario": "review",
  "count": 5,
  "rules": [
    {"id": "S01", "name": "SQL 注入", ...},
    {"id": "S02", "name": "XSS 跨站脚本", ...},
    ...
  ]
}
```

### Step 2: 执行规则检查

```bash
# 执行所有安全规则的检查命令
python scripts/rule_query.py --query review --category security --format json | \
  jq -r '.rules[].check_command' | \
  while read -r cmd; do
    eval "$cmd" 2>/dev/null
  done

# 或针对特定文件
python scripts/rule_query.py --query review --category security --format json | \
  jq -r '.rules[].check_command' | \
  while read -r cmd; do
    eval "$cmd" <file> 2>/dev/null
  done
```

### Step 3: 检索安全类 postmortem

```bash
# 按分类检索
rg "category: security" .claude/postmortem/*/REPORT.md -l

# 提取相关经验教训
rg "## 经验教训" -A 20 .claude/postmortem/*/REPORT.md

# 按具体类型检索
rg "root_cause:" -A 3 .claude/postmortem/ | rg "injection\|xss\|auth"
```

### Step 4: 生成安全报告

## 报告模板

```yaml
---
type: security-scan
id: "250113-security-scan"
created_at: "2025-01-13"
status: active
scope:
  files: ["src/**/*.ts", "src/**/*.py"]
keywords: [security, injection, xss, auth]
refs:
  related_postmortem: ["250110-sql-injection"]
risk_level: high
issues_count: 3
---
```

```markdown
# 安全扫描报告

## 扫描范围

| 类型 | 数量 |
|------|------|
| 扫描文件 | 150 |
| 检查规则 | 5 |
| 发现问题 | 3 |

## 发现问题

### Critical

#### S01: SQL 注入

| 位置 | 问题 | 建议 |
|------|------|------|
| src/api/user.ts:45 | 字符串拼接 SQL | 使用参数化查询 |

```typescript
// 问题代码
db.query(`SELECT * FROM users WHERE id = ${userId}`)

// 建议修复
db.query('SELECT * FROM users WHERE id = ?', [userId])
```

#### S03: 命令注入

| 位置 | 问题 | 建议 |
|------|------|------|
| src/utils/exec.ts:23 | shell 命令拼接 | 使用参数数组 |

### High

#### S05: 敏感信息泄露

| 位置 | 问题 | 建议 |
|------|------|------|
| src/config/db.ts:5 | 硬编码密码 | 使用环境变量 |

## 相关历史问题

以下 postmortem 与本次扫描发现相关：

| 问题 | 类型 | 相关发现 |
|------|------|----------|
| [250110-sql-injection](...) | S01 | src/api/user.ts:45 |

### 历史教训

来自 250110-sql-injection:
> 所有用户输入必须经过参数化处理，禁止直接拼接到 SQL 语句中。

## 风险摘要

| 风险等级 | 数量 | 说明 |
|----------|------|------|
| Critical | 2 | 必须立即修复 |
| High | 1 | 尽快修复 |
| Medium | 0 | - |
| Low | 0 | - |

## 修复建议

### 优先级 1: Critical

1. **S01 SQL 注入** - src/api/user.ts:45
   - 使用 ORM 或参数化查询
   - 验证所有用户输入

2. **S03 命令注入** - src/utils/exec.ts:23
   - 使用 execFile 替代 exec
   - 使用参数数组

### 优先级 2: High

1. **S05 敏感信息泄露** - src/config/db.ts:5
   - 移至环境变量
   - 使用密钥管理服务
```

## 输出位置

```
.claude/security-scan/
├── <yymmdd>-scan/
│   └── REPORT.md      # 安全扫描报告
```
