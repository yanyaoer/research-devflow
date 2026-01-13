# Test-Strategy Skill

测试策略生成工具，为功能生成测试计划，关联 postmortem 复现步骤。

## 命令格式

```bash
/test-strategy <feature>    # 为功能生成测试策略
/test-strategy <file>       # 为文件生成测试策略
/test-strategy --coverage   # 分析测试覆盖
/test-strategy --gaps       # 识别测试缺口
```

## 工作流程

```
Task Progress:
- [ ] 1. 分析目标功能/文件
- [ ] 2. 检索相关 postmortem 的复现步骤
- [ ] 3. 分析现有测试覆盖
- [ ] 4. 识别测试缺口
- [ ] 5. 生成测试策略
- [ ] 6. 输出测试计划
```

### Step 1: 分析目标功能

```bash
# 分析文件结构
ast-grep -p 'function $NAME($$$) { $$$BODY$$$ }' --lang typescript <file>
ast-grep -p 'def $NAME($$$):' --lang python <file>

# 提取导出的函数/类
rg "^export (function|class|const)" --type ts <file>
rg "^def |^class " --type py <file>
```

### Step 2: 检索 postmortem 复现步骤

```bash
# 按模块检索相关 postmortem
rg "scope:" -A 10 .claude/postmortem/*/REPORT.md | rg "<module>"

# 提取复现步骤作为测试用例参考
rg "## 复现步骤" -A 20 .claude/postmortem/*/REPORT.md

# 提取边界条件
rg "### 触发条件" -A 10 .claude/postmortem/*/REPORT.md
```

### Step 3: 分析现有测试覆盖

```bash
# 查找测试文件
fd -e test.ts -e spec.ts -e test.tsx -e spec.tsx
fd -e test.js -e spec.js
fd -e _test.go
fd -e test_.py -e _test.py

# 分析测试用例
ast-grep -p 'describe($NAME, $$$)' --lang typescript
ast-grep -p 'it($NAME, $$$)' --lang typescript
ast-grep -p 'test($NAME, $$$)' --lang typescript

# Python
ast-grep -p 'def test_$NAME($$$):' --lang python

# Go
ast-grep -p 'func Test$NAME($$$) { $$$BODY$$$ }' --lang go
```

### Step 4: 识别测试缺口

对比源码和测试：
- 哪些函数没有对应测试
- 哪些分支没有覆盖
- 哪些边界条件未测试

```bash
# 提取源码函数
rg "^export function (\w+)" -o --type ts <file> | sort > /tmp/funcs.txt

# 提取测试覆盖
rg "describe\(['\"](\w+)" -o --type ts <test-file> | sort > /tmp/tests.txt

# 对比缺口
comm -23 /tmp/funcs.txt /tmp/tests.txt
```

## 测试策略模板

```yaml
---
type: test-strategy
id: "250113-test-strategy-auth"
created_at: "2025-01-13"
status: active
scope:
  modules: ["src/auth/"]
  functions: ["validateToken", "refreshToken"]
keywords: [test, auth, token]
refs:
  related_postmortem: ["250110-token-expired"]
---
```

```markdown
# 测试策略: Auth 模块

## 目标

为 `src/auth/` 模块生成完整测试策略。

## 现有覆盖

| 文件 | 测试文件 | 覆盖率 |
|------|----------|--------|
| src/auth/token.ts | src/auth/token.test.ts | 60% |
| src/auth/session.ts | - | 0% |

## 测试缺口

### 未覆盖函数

| 函数 | 文件 | 优先级 |
|------|------|--------|
| refreshToken | src/auth/token.ts | high |
| validateSession | src/auth/session.ts | high |

### 未覆盖分支

| 位置 | 分支 | 说明 |
|------|------|------|
| token.ts:45 | token expired | 来自 postmortem 250110 |
| session.ts:23 | null user | 边界条件 |

## 来自 Postmortem 的测试用例

以下测试用例来自历史问题的复现步骤：

### 250110-token-expired

**复现步骤**:
1. 用户登录获取 token
2. 等待 token 过期
3. 同时发起多个请求刷新 token

**建议测试**:
```typescript
it('should handle concurrent token refresh', async () => {
  // 模拟并发刷新
  const results = await Promise.all([
    refreshToken(expiredToken),
    refreshToken(expiredToken),
  ]);
  // 验证只有一次刷新成功
  expect(results.filter(r => r.success)).toHaveLength(1);
});
```

## 测试计划

### 单元测试

| 测试 | 优先级 | 状态 |
|------|--------|------|
| validateToken - valid token | high | TODO |
| validateToken - expired token | high | TODO |
| refreshToken - success | high | TODO |
| refreshToken - concurrent | critical | TODO |

### 集成测试

| 测试 | 优先级 | 状态 |
|------|--------|------|
| auth flow - login to refresh | high | TODO |
| auth flow - session timeout | medium | TODO |

### 边界条件测试

| 测试 | 来源 | 状态 |
|------|------|------|
| null user handling | postmortem | TODO |
| empty token | static analysis | TODO |
```

## 输出位置

```
.claude/test-strategy/
├── <yymmdd>-<module>/
│   ├── STRATEGY.md      # 测试策略文档
│   └── test-cases.md    # 生成的测试用例
```
