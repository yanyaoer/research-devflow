---
task_id: "250113-phase1-core-skills"
---

# Phase 1: 开发核心流程 Skills - 共享上下文

## 项目背景

在 Phase 0 中完成了统一 meta schema，现在需要：
1. 创建共享规则文件，实现 review↔postmortem 规则统一
2. 创建查询脚本 rule_query.py 封装规则检索
3. 实现 review skill，与 postmortem 联动

## 设计决策

- 规则文件位置：`docs/RULES-*.md`
- 查询脚本：`scripts/rule_query.py --query <scenario>`
- 场景标签：`applies_to: [review, postmortem, refactor, research]`

## 规则文件结构

```yaml
# docs/RULES-CODE-QUALITY.md
---
id: code-quality-rules
version: "1.0"
---

rules:
  - id: S01
    name: SQL 注入检查
    category: security
    applies_to: [review, postmortem]
    review_action: "检查参数化查询"
    postmortem_action: "追溯注入路径"
    check_command: "rg 'execute\\(.*\\+' --type py"
```

## 查询脚本用法

```bash
# 查询 review 场景的规则
python scripts/rule_query.py --query review

# 查询特定分类
python scripts/rule_query.py --query review --category security

# 输出 JSON 格式
python scripts/rule_query.py --query review --format json
```

## 相关 Postmortem

_暂无，待后续积累_

## 构建命令

```bash
# 测试查询脚本
python scripts/rule_query.py --query review
python scripts/rule_query.py --query postmortem
```

## Git 提交规范

```bash
git add -A && git commit -m "feat(rules): <description>"
git add -A && git commit -m "feat(review): <description>"
```
