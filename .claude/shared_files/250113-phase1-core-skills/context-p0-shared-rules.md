# P0: 创建共享规则文件 RULES-CODE-QUALITY.md

## 任务目标

创建代码质量检查规则文件，供 review 和 postmortem 共同使用。

## 依赖任务

- 无

## 实现步骤

### Step 1: 创建规则文件

**文件**: `docs/RULES-CODE-QUALITY.md`

规则结构：
```yaml
---
id: code-quality-rules
version: "1.0"
updated_at: "2025-01-13"
---

# 代码质量检查规则

## 规则格式说明

每条规则包含：
- id: 唯一标识
- name: 规则名称
- category: 分类 (security/robustness/performance/maintainability)
- severity: 严重程度 (critical/high/medium/low)
- applies_to: 适用场景 [review, postmortem]
- review_action: review 时的检查动作
- postmortem_action: postmortem 时的分析动作
- check_command: 检查命令 (rg/ast-grep)
- examples: 示例代码

## 规则列表

### 安全类 (security)

- id: S01 - SQL 注入
- id: S02 - XSS
- id: S03 - 命令注入
- id: S04 - 认证绕过
- id: S05 - 敏感信息泄露

### 健壮性 (robustness)

- id: R01 - 空值处理
- id: R02 - 边界条件
- id: R03 - 并发安全
- id: R04 - 异常处理
- id: R05 - 资源泄露

### 性能 (performance)

- id: P01 - N+1 查询
- id: P02 - 无限循环风险
- id: P03 - 内存泄漏

### 可维护性 (maintainability)

- id: M01 - 硬编码配置
- id: M02 - 魔法数字
- id: M03 - 过长函数
```

## 涉及文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `docs/RULES-CODE-QUALITY.md` | 新建 | 代码质量规则 |

## 验证方法

```bash
# 检查文件结构
head -50 docs/RULES-CODE-QUALITY.md

# 检查规则数量
rg "^- id:" docs/RULES-CODE-QUALITY.md | wc -l
```

## 完成标准

- [ ] 创建 RULES-CODE-QUALITY.md
- [ ] 包含安全/健壮性/性能/可维护性四类规则
- [ ] 每条规则有 applies_to 场景标签
- [ ] 每条规则有 check_command
- [ ] 更新 task-status.json
