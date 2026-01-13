# /test-strategy - 测试策略生成

为功能生成测试策略，关联 postmortem 复现步骤。

## 用法

```
/test-strategy <feature>    # 为功能生成测试策略
/test-strategy <file>       # 为文件生成测试策略
/test-strategy --coverage   # 分析测试覆盖
/test-strategy --gaps       # 识别测试缺口
```

## 执行流程

1. 读取 [Test-Strategy Skill](../skills/test-strategy/SKILL.md)
2. 分析目标功能/文件
3. 检索相关 postmortem 复现步骤
4. 分析现有测试覆盖
5. 生成测试策略

## 输出

- 测试策略: `.claude/test-strategy/<yymmdd>-<module>/STRATEGY.md`
- 测试用例: `.claude/test-strategy/<yymmdd>-<module>/test-cases.md`

## 示例

```bash
# 为认证模块生成测试策略
/test-strategy src/auth/

# 分析测试覆盖
/test-strategy --coverage

# 识别测试缺口
/test-strategy --gaps
```
