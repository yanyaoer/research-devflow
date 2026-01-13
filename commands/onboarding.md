# /onboarding - 新人指南

聚合项目文档生成上手指南。

## 用法

```
/onboarding                 # 生成项目上手指南
/onboarding <module>        # 生成模块指南
/onboarding --quick         # 快速入门版本
```

## 执行流程

1. 读取 [Onboarding Skill](../skills/onboarding/SKILL.md)
2. 分析项目结构
3. 聚合 ADR 和架构决策
4. 提取常见问题 (from postmortem)
5. 生成上手指南

## 输出

- 项目指南: `.claude/onboarding/GUIDE.md`
- 模块指南: `.claude/onboarding/<module>/GUIDE.md`

## 示例

```bash
# 生成完整上手指南
/onboarding

# 生成认证模块指南
/onboarding auth

# 快速入门
/onboarding --quick
```
