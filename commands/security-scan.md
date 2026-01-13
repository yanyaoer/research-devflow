# /security-scan - 安全检查

复用共享规则进行安全扫描。

## 用法

```
/security-scan              # 全量扫描
/security-scan <file>       # 扫描指定文件
/security-scan <dir>        # 扫描指定目录
/security-scan --category <cat>  # 按分类扫描 (injection, xss, auth, leak)
```

## 执行流程

1. 读取 [Security-Scan Skill](../skills/security-scan/SKILL.md)
2. 加载安全类规则
3. 执行规则检查命令
4. 检索相关安全类 postmortem
5. 生成安全报告

## 输出

- 安全报告: `.claude/security-scan/<yymmdd>-scan/REPORT.md`

## 示例

```bash
# 全量扫描
/security-scan

# 扫描 API 目录
/security-scan src/api/

# 只检查注入类问题
/security-scan --category injection
```
