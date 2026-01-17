---
id: lsp-configuration-rules
version: "1.0"
updated_at: "2026-01-16"
---

# LSP 配置与检查指南

## 概述

LSP (Language Server Protocol) 提供语义级代码理解能力，在代码审查和复盘中显著优于文本搜索：
- **定义跳转**: 准确追踪代码实现。
- **引用查找**: 快速评估变更影响范围。
- **类型信息**: 明确变量与函数签名。

## 1. 使用方式

**直接调用 LSP 工具**，无需预先检查配置：
- 调用 `definition`、`references`、`hover` 等 LSP 操作
- 如调用成功，继续使用 LSP 进行分析
- 如调用失败，自动降级到 `ast-grep` 或 `rg`

**安装 LSP Plugin** (如需)：请参考 [README 安装指南](../README.md#claude-code-extra-configuration)。

## 2. Java (jdtls) 配置详解

将以下配置加入 `.claude/settings.json` 的 `lsp` 字段。

**必要参数**:
- `command`: `jdtls` 可执行文件路径 (推荐绝对路径)。
- `java.home`: JDK 安装路径。

```json
{
  "lsp": {
    "java": {
      "command": "/path/to/jdtls",
      "args": [
        "-data", "/tmp/jdtls-workspace"
      ],
      "rootMarkers": ["pom.xml", "build.gradle", "build.gradle.kts", ".project"],
      "initializationOptions": {
        "settings": {
          "java": {
            "home": "/Library/Java/JavaVirtualMachines/jdk-17.jdk/Contents/Home",
            "format": { "enabled": true }
          }
        }
      }
    }
  }
}
```

## 3. 最佳实践

**降级策略**: 分析代码时，按以下优先级选择工具：
1. **LSP 工具**: `definition`, `references` (准确度最高)。
2. **结构化搜索**: `ast-grep` (基于语法树)。
3. **文本搜索**: `git grep`, `rg` (最通用但易误报)。
