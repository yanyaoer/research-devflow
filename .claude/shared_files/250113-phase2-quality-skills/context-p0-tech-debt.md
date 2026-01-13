# P0: 创建 tech-debt skill

## 任务目标

创建技术债务追踪工具，扫描和管理代码中的技术债务。

## 功能设计

```bash
/tech-debt                  # 列出所有债务
/tech-debt add <desc>       # 记录新债务
/tech-debt scan             # 扫描代码中的 TODO/FIXME/HACK
/tech-debt report           # 生成债务报告
```

## 实现步骤

### Step 1: 创建 SKILL.md

**文件**: `skills/tech-debt/SKILL.md`

核心工作流：
```
Task Progress:
- [ ] 1. 解析参数确定操作模式
- [ ] 2. 扫描代码中的债务标记
- [ ] 3. 读取已有债务记录
- [ ] 4. 分类和优先级排序
- [ ] 5. 生成/更新债务报告
```

### Step 2: 扫描命令

```bash
# 扫描 TODO/FIXME/HACK/XXX
rg "TODO|FIXME|HACK|XXX" --type-add 'code:*.{ts,js,py,go,rs,kt,java}' -t code -n

# 提取带上下文
rg "TODO|FIXME|HACK|XXX" -B 1 -A 2 --type ts --type js --type py --type go --type rust --type java --type kotlin
```

### Step 3: 报告格式

```yaml
---
type: tech-debt
id: "250113-tech-debt-report"
created_at: "2025-01-13"
status: active
scope:
  files: ["src/**/*.ts"]
keywords: [tech-debt, todo, fixme]
---
```

## 涉及文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `skills/tech-debt/SKILL.md` | 新建 | Tech-debt skill 定义 |
| `commands/tech-debt.md` | 新建 | 命令入口 |

## 验证方法

```bash
# 测试扫描命令
rg "TODO|FIXME" --type ts --type js -c

# 检查目录结构
ls skills/tech-debt/
```

## 完成标准

- [ ] 创建 skills/tech-debt/SKILL.md
- [ ] 创建 commands/tech-debt.md
- [ ] 支持扫描 TODO/FIXME/HACK 标记
- [ ] 支持手动添加债务记录
- [ ] 生成结构化债务报告
- [ ] 更新 task-status.json
