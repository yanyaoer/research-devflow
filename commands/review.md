# /review - 代码审查辅助

执行代码审查，检查变更代码的质量问题，并关联历史 postmortem。

## 用法

```
/review                     # 审查暂存区变更
/review <commit>            # 审查指定 commit
/review <branch>            # 审查分支与 main 的 diff
/review --pr <number>       # 审查 PR (需要 gh CLI)
```

## 执行流程

1. 读取 [Review Skill](../skills/review/SKILL.md)
2. 获取变更文件列表
3. 加载 [代码质量规则](../docs/RULES-CODE-QUALITY.md)
4. 检索相关 postmortem
5. 执行规则检查
6. 生成审查报告

## 输出

- 审查报告: `.claude/reviews/<yymmdd>-review-<target>/REPORT.md`
- 终端摘要: 风险等级统计和关键问题提示

## 示例

```bash
# 审查暂存区
/review

# 审查 PR
/review --pr 123

# 审查功能分支
/review feature/auth
```
