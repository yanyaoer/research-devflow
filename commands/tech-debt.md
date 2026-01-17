# /tech-debt - 技术债务追踪

扫描和管理代码中的技术债务。

## 用法

```
/tech-debt                  # 列出所有债务
/tech-debt scan             # 扫描代码中的 TODO/FIXME/HACK
/tech-debt add <desc>       # 记录新债务
/tech-debt report           # 生成债务报告
```

## 执行流程

1. 读取 [Tech-Debt Skill](../skills/tech-debt/SKILL.md)
2. 扫描代码中的债务标记
3. 检索相关 postmortem
4. 生成债务报告

## 输出

- 债务报告: `<project-root>/.claude/tech-debt/REPORT.md`
- 手动记录: `<project-root>/.claude/tech-debt/manual.md`

## 示例

```bash
# 扫描当前项目
/tech-debt scan

# 添加新债务
/tech-debt add "需要重构支付模块"

# 生成完整报告
/tech-debt report
```
