# P1: 创建 test-strategy skill

## 任务目标

创建测试策略生成工具，为功能生成测试计划，关联 postmortem 复现步骤。

## 功能设计

```bash
/test-strategy <feature>    # 为功能生成测试策略
/test-strategy --coverage   # 分析测试覆盖
/test-strategy --gaps       # 识别测试缺口
```

## 实现步骤

### Step 1: 创建 SKILL.md

**文件**: `skills/test-strategy/SKILL.md`

核心工作流：
```
Task Progress:
- [ ] 1. 分析目标功能/文件
- [ ] 2. 检索相关 postmortem 的复现步骤
- [ ] 3. 分析现有测试覆盖
- [ ] 4. 生成测试策略
- [ ] 5. 输出测试计划
```

### Step 2: 检索 postmortem 复现步骤

```bash
# 按模块检索相关 postmortem
rg "scope:" -A 10 .claude/postmortem/*/REPORT.md | rg "<module>"

# 提取复现步骤
rg "## 复现步骤" -A 20 .claude/postmortem/*/REPORT.md
```

### Step 3: 分析测试覆盖

```bash
# 查找测试文件
fd -e test.ts -e spec.ts -e test.js -e spec.js -e _test.go -e _test.py

# 分析测试与源码对应关系
ast-grep -p 'describe($NAME, $$$)' --lang typescript
ast-grep -p 'def test_$NAME($$$):' --lang python
```

## 涉及文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `skills/test-strategy/SKILL.md` | 新建 | Test-strategy skill 定义 |
| `commands/test-strategy.md` | 新建 | 命令入口 |

## 完成标准

- [ ] 创建 skills/test-strategy/SKILL.md
- [ ] 创建 commands/test-strategy.md
- [ ] 检索 postmortem 复现步骤作为测试用例参考
- [ ] 分析现有测试覆盖
- [ ] 生成测试策略文档
- [ ] 更新 task-status.json
