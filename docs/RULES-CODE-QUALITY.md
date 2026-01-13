---
id: code-quality-rules
version: "1.0"
updated_at: "2025-01-13"
---

# 代码质量检查规则

## 支持的语言

规则检查命令覆盖以下主流语言：
- TypeScript/JavaScript (ts, js)
- Python (py)
- Rust (rust)
- Java (java)
- Kotlin (kotlin)
- Go (go)

## 规则格式说明

```yaml
- id: 规则唯一标识
  name: 规则名称
  category: security | robustness | performance | maintainability
  severity: critical | high | medium | low
  applies_to: [review, postmortem]
  review_action: review 时的检查动作
  postmortem_action: postmortem 时的分析动作
  check_command: 检查命令
  fix_hint: 修复提示
```

---

## 安全类 (security)

```yaml
- id: S01
  name: SQL 注入
  category: security
  severity: critical
  applies_to: [review, postmortem]
  review_action: 检查是否使用参数化查询
  postmortem_action: 追溯注入路径和攻击向量
  check_command: |
    rg "execute\(.*\+|query\(.*\+|raw\(.*\+" --type py --type js --type ts --type java --type kotlin --type go
    rg "executeQuery.*\$\{|\.query.*\$\{|format!.*SELECT|fmt\.Sprintf.*SELECT" --type ts --type js --type rust --type go
    rg "createQuery\(.*\+|prepareStatement.*\+" --type java --type kotlin
  fix_hint: 使用参数化查询或 ORM

- id: S02
  name: XSS 跨站脚本
  category: security
  severity: critical
  applies_to: [review, postmortem]
  review_action: 检查用户输入是否转义输出
  postmortem_action: 分析攻击载荷和影响范围
  check_command: |
    rg "innerHTML\s*=|v-html|dangerouslySetInnerHTML" --type ts --type js
    rg "document\.write\(" --type js --type ts
    rg "html!|Html::raw|template\.HTML" --type rust --type go
  fix_hint: 使用 textContent 或框架的安全输出方式

- id: S03
  name: 命令注入
  category: security
  severity: critical
  applies_to: [review, postmortem]
  review_action: 检查 shell 命令拼接
  postmortem_action: 还原命令执行路径
  check_command: |
    rg "exec\(.*\+|spawn\(.*\+|system\(.*\+" --type py --type js --type ts --type java --type kotlin
    rg "subprocess\.(run|call|Popen).*shell=True" --type py
    rg "Runtime\.getRuntime\(\)\.exec|ProcessBuilder" --type java --type kotlin
    rg "Command::new.*arg\(.*format!|exec\.Command" --type rust --type go
  fix_hint: 使用参数数组而非字符串拼接

- id: S04
  name: 认证绕过
  category: security
  severity: critical
  applies_to: [review, postmortem]
  review_action: 检查认证逻辑完整性
  postmortem_action: 还原绕过路径
  check_command: |
    rg "isAuthenticated|isAuthorized|checkAuth|@PreAuthorize|@Secured" --type ts --type js --type py --type java --type kotlin
    rg "middleware.*auth|#\[authorize\]|RequireAuth" --type go --type rust
  fix_hint: 确保所有敏感路由都有认证检查

- id: S05
  name: 敏感信息泄露
  category: security
  severity: high
  applies_to: [review, postmortem]
  review_action: 检查硬编码密钥和日志输出
  postmortem_action: 评估泄露范围和影响
  check_command: |
    rg "(password|secret|key|token|api_key)\s*=\s*['\"][^'\"]+['\"]" -i --type py --type js --type ts --type java --type kotlin --type go --type rust
    rg "console\.(log|info|debug).*password|print.*password|log\.(info|debug|warn).*password|println.*password" -i
  fix_hint: 使用环境变量或密钥管理服务
```

---

## 健壮性 (robustness)

```yaml
- id: R01
  name: 空值处理缺失
  category: robustness
  severity: high
  applies_to: [review, postmortem]
  review_action: 检查可能为 null/undefined 的变量使用
  postmortem_action: 追溯空值来源和传播路径
  check_command: |
    rg "\.unwrap\(\)|\.expect\(" --type rust
    rg "NullPointerException|\.get\(\)\." --type java --type kotlin
    rg "Cannot read propert|undefined is not|null is not" --type ts --type js
    rg "AttributeError: 'NoneType'" --type py
  fix_hint: 使用可选链(?.)、Option/Result 或显式空值检查

- id: R02
  name: 边界条件未处理
  category: robustness
  severity: high
  applies_to: [review, postmortem]
  review_action: 检查数组索引和范围边界
  postmortem_action: 还原边界触发条件
  check_command: |
    rg "\[.*\]" --type ts --type js --type py --type java --type kotlin --type go --type rust
    rg "IndexOutOfBounds|index out of range|slice bounds" -i
  fix_hint: 添加边界检查，使用安全访问方法

- id: R03
  name: 并发竞态条件
  category: robustness
  severity: high
  applies_to: [review, postmortem]
  review_action: 检查共享状态的并发访问
  postmortem_action: 还原竞态时序
  check_command: |
    rg "async|await|Promise|setTimeout|setInterval" --type ts --type js
    rg "threading|asyncio|concurrent\.futures" --type py
    rg "synchronized|ReentrantLock|AtomicInteger" --type java --type kotlin
    rg "go\s+func|sync\.Mutex|chan\s+" --type go
    rg "Arc<Mutex|tokio::spawn|async fn" --type rust
  fix_hint: 使用锁、原子操作或不可变数据

- id: R04
  name: 异常处理不当
  category: robustness
  severity: medium
  applies_to: [review, postmortem]
  review_action: 检查 try-catch 覆盖和错误处理
  postmortem_action: 分析异常传播和吞没
  check_command: |
    rg "catch\s*\(\s*\w*\s*\)\s*\{\s*\}" --type ts --type js
    rg "except:$|except Exception:$" --type py
    rg "catch\s*\(.*\)\s*\{\s*\}" --type java --type kotlin
    rg "if err != nil \{\s*\}" --type go
    rg "\.unwrap_or\(\)" --type rust
  fix_hint: 记录错误详情，避免空 catch 块

- id: R05
  name: 资源泄露
  category: robustness
  severity: medium
  applies_to: [review, postmortem]
  review_action: 检查文件/连接是否正确关闭
  postmortem_action: 分析资源累积和系统影响
  check_command: |
    rg "open\(|createConnection|createPool|new FileInputStream|new BufferedReader" --type py --type ts --type js --type java --type kotlin
    rg "File::open|TcpStream::connect" --type rust
    rg "os\.Open|sql\.Open|net\.Dial" --type go
  fix_hint: 使用 try-finally、defer、use/with 或 RAII
```

---

## 性能 (performance)

```yaml
- id: P01
  name: N+1 查询问题
  category: performance
  severity: medium
  applies_to: [review, postmortem]
  review_action: 检查循环内的数据库查询
  postmortem_action: 分析查询日志和性能数据
  check_command: |
    rg "for.*\{" -A 5 | rg "\.find\(|\.query\(|SELECT|findById" --type ts --type js --type py --type java --type kotlin --type go --type rust
  fix_hint: 使用批量查询或 JOIN

- id: P02
  name: 无限循环风险
  category: performance
  severity: high
  applies_to: [review, postmortem]
  review_action: 检查循环终止条件
  postmortem_action: 还原循环卡死条件
  check_command: |
    rg "while\s*\(\s*true\s*\)|while\s*\(\s*1\s*\)|for\s*\(\s*;\s*;\s*\)|while True:|loop \{" --type ts --type js --type py --type java --type kotlin --type go --type rust
  fix_hint: 确保有明确的退出条件和超时机制

- id: P03
  name: 内存泄漏风险
  category: performance
  severity: medium
  applies_to: [review, postmortem]
  review_action: 检查事件监听器和定时器清理
  postmortem_action: 分析内存增长模式
  check_command: |
    rg "addEventListener|setInterval|setTimeout|subscribe\(" --type ts --type js
    rg "Box::leak|mem::forget|static mut" --type rust
    rg "addObserver|NotificationCenter" --type java --type kotlin
  fix_hint: 组件卸载时清理监听器和定时器
```

---

## 可维护性 (maintainability)

```yaml
- id: M01
  name: 硬编码配置
  category: maintainability
  severity: low
  applies_to: [review, postmortem]
  review_action: 检查硬编码的 URL、端口、路径
  postmortem_action: 分析配置错误影响
  check_command: |
    rg "http://localhost|127\.0\.0\.1|:3000|:8080|:8000" --type ts --type js --type py --type java --type kotlin --type go --type rust
    rg "hardcoded|HARDCODED|TODO.*config" -i
  fix_hint: 使用环境变量或配置文件

- id: M02
  name: 魔法数字
  category: maintainability
  severity: low
  applies_to: [review]
  review_action: 检查未命名的数字常量
  postmortem_action: N/A
  check_command: |
    rg "=\s*\d{2,}[^0-9]|>\s*\d{2,}[^0-9]|<\s*\d{2,}[^0-9]" --type ts --type js --type py --type java --type kotlin --type go --type rust
  fix_hint: 提取为命名常量

- id: M03
  name: 过长函数
  category: maintainability
  severity: low
  applies_to: [review]
  review_action: 检查函数行数是否超过阈值
  postmortem_action: N/A
  check_command: |
    # 使用 ast-grep 针对各语言查找函数
    ast-grep -p 'function $NAME($$$) { $$$BODY$$$ }' --lang typescript
    ast-grep -p 'fn $NAME($$$) { $$$BODY$$$ }' --lang rust
    ast-grep -p 'func $NAME($$$) { $$$BODY$$$ }' --lang go
  fix_hint: 拆分为多个职责单一的小函数
```

---

## 使用方式

### Review 场景

```bash
# 获取所有 review 规则
python scripts/rule_query.py --query review

# 获取特定分类
python scripts/rule_query.py --query review --category security
```

### Postmortem 场景

```bash
# 获取 postmortem 分析规则
python scripts/rule_query.py --query postmortem

# 按根因类型匹配规则
python scripts/rule_query.py --query postmortem --category robustness
```

### 执行检查

```bash
# 对变更文件执行所有检查命令
python scripts/rule_query.py --query review --format json | \
  jq -r '.rules[].check_command' | \
  while read cmd; do eval "$cmd"; done
```
