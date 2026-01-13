# /release - 发布管理

生成 changelog 和发布说明。

## 用法

```
/release changelog          # 生成 changelog
/release notes <version>    # 生成发布说明
/release diff <v1> <v2>     # 版本差异分析
```

## 执行流程

1. 读取 [Release Skill](../skills/release/SKILL.md)
2. 分析 commit 历史
3. 聚合相关文档 (postmortem, ADR, review)
4. 生成 changelog/发布说明

## 输出

- Changelog: `.claude/release/CHANGELOG.md`
- 发布说明: `.claude/release/<version>/NOTES.md`

## 示例

```bash
# 生成 changelog
/release changelog

# 生成 v1.2.0 发布说明
/release notes v1.2.0

# 对比两个版本
/release diff v1.1.0 v1.2.0
```
