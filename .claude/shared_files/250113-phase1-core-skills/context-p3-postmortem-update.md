# P3: 更新 postmortem 引用共享规则

## 任务目标

更新 postmortem skill，引用共享规则文件，实现与 review 的规则同步。

## 依赖任务

- P2: 创建 review skill

## 实现步骤

### Step 1: 更新 SKILL.md 添加规则引用

**文件**: `skills/postmortem/SKILL.md`

在适当位置添加：

```markdown
## 共享规则引用

本 skill 使用以下共享规则进行根因分类：
- [代码质量规则](../../docs/RULES-CODE-QUALITY.md)

### 加载规则

```bash
# 获取 postmortem 适用的规则
python scripts/rule_query.py --query postmortem --format json
```

### 根因分类映射

| 规则 ID | 根因类型 | 分析重点 |
|---------|----------|----------|
| S01-S05 | security | 追溯攻击路径 |
| R01-R05 | robustness | 还原触发条件 |
| P01-P03 | performance | 分析性能瓶颈 |
```

### Step 2: 更新分析流程

在代码分析流程中添加规则检查：

```markdown
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
1. 记录规则 ID 到报告
2. 使用规则的 postmortem_action 指导分析
3. 关联已有的 review 发现（如有）
```

### Step 3: 更新报告模板

在 REPORT.md 模板中添加规则关联字段：

```yaml
# 在 root_cause 下添加
root_cause:
  type: race_condition
  pattern: "..."
  matched_rules: ["R03"]  # 新增：匹配的规则 ID

# 新增 review 关联
related_reviews:
  - id: "250113-review-pr-120"
    finding: "R03 检查未通过但被忽略"
```

## 涉及文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `skills/postmortem/SKILL.md` | 修改 | 添加规则引用和匹配逻辑 |

## 验证方法

```bash
# 检查规则引用
rg "RULES-CODE-QUALITY" skills/postmortem/SKILL.md

# 检查 rule_query 调用
rg "rule_query.py" skills/postmortem/SKILL.md
```

## 完成标准

- [ ] 添加共享规则引用章节
- [ ] 添加规则加载命令
- [ ] 更新分析流程添加规则匹配
- [ ] 更新报告模板添加 matched_rules 字段
- [ ] 添加 review 关联字段
- [ ] 更新 task-status.json
