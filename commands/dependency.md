# /dependency - 依赖管理

分析依赖状态、升级影响和安全漏洞。

## 用法

```
/dependency                 # 分析依赖状态
/dependency upgrade <pkg>   # 升级影响分析
/dependency audit           # 安全漏洞检查
/dependency outdated        # 列出过时依赖
```

## 执行流程

1. 读取 [Dependency Skill](../skills/dependency/SKILL.md)
2. 检测项目类型和包管理器
3. 分析依赖状态
4. 检查安全漏洞
5. 生成依赖报告

## 输出

- 依赖报告: `.claude/dependency/REPORT.md`

## 示例

```bash
# 分析依赖状态
/dependency

# 检查安全漏洞
/dependency audit

# 分析升级 react 的影响
/dependency upgrade react
```
