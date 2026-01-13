# P2: 创建 security-scan skill

## 任务目标

创建安全检查工具，复用共享规则进行安全扫描。

## 功能设计

```bash
/security-scan              # 全量扫描
/security-scan <file>       # 扫描指定文件
/security-scan --category   # 按分类扫描 (injection, auth, leak)
```

## 实现步骤

### Step 1: 创建 SKILL.md

**文件**: `skills/security-scan/SKILL.md`

核心工作流：
```
Task Progress:
- [ ] 1. 加载安全类规则 (rule_query --category security)
- [ ] 2. 确定扫描范围
- [ ] 3. 执行规则检查命令
- [ ] 4. 检索相关安全类 postmortem
- [ ] 5. 生成安全报告
```

### Step 2: 复用共享规则

```bash
# 获取所有安全类规则
python scripts/rule_query.py --query review --category security --format json

# 执行检查命令
python scripts/rule_query.py --query review --category security --format json | \
  jq -r '.rules[].check_command' | while read cmd; do eval "$cmd"; done
```

### Step 3: 检索安全类 postmortem

```bash
# 按分类检索
rg "category: security" .claude/postmortem/*/REPORT.md -l

# 提取相关经验教训
rg "## 经验教训" -A 20 .claude/postmortem/*/REPORT.md
```

## 涉及文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `skills/security-scan/SKILL.md` | 新建 | Security-scan skill 定义 |
| `commands/security-scan.md` | 新建 | 命令入口 |

## 完成标准

- [ ] 创建 skills/security-scan/SKILL.md
- [ ] 创建 commands/security-scan.md
- [ ] 复用 RULES-CODE-QUALITY.md 的安全类规则
- [ ] 检索安全类 postmortem 作为参考
- [ ] 生成安全扫描报告
- [ ] 更新 task-status.json
