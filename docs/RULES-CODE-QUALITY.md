---
id: code-quality-rules
version: "1.1"
updated_at: "2025-01-13"
---

# 代码质量检查规则

## 支持的语言

规则检查命令覆盖以下主流语言：

| 语言 | 扩展名 | rg --type |
|------|--------|-----------|
| TypeScript/JavaScript | ts, tsx, js, jsx | ts, js |
| Python | py | py |
| Rust | rs | rust |
| Go | go | go |
| Java | java | java |
| Kotlin | kt, kts | kotlin |
| Swift | swift | swift |
| C/C++ | c, cpp, cc, h, hpp | c, cpp |

### 快捷 Glob 模式

```bash
# 全语言扫描
CODE_GLOB='*.{ts,tsx,js,jsx,py,rs,go,java,kt,swift,c,cpp,cc,h,hpp}'

# 使用示例
rg "pattern" -g "$CODE_GLOB"
```

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
    rg "execute\(.*\+|query\(.*\+|raw\(.*\+|executeQuery.*\$\{|\.query.*\$\{" -g '*.{ts,js,py,java,kt,go,swift}'
    rg "format!.*SELECT|fmt\.Sprintf.*SELECT" -g '*.{rs,go}'
    rg "stringWithFormat.*SELECT|NSString.*SELECT" -g '*.{swift,m,mm}'
  fix_hint: 使用参数化查询或 ORM

- id: S02
  name: XSS 跨站脚本
  category: security
  severity: critical
  applies_to: [review, postmortem]
  review_action: 检查用户输入是否转义输出
  postmortem_action: 分析攻击载荷和影响范围
  check_command: |
    rg "innerHTML\s*=|v-html|dangerouslySetInnerHTML|document\.write\(" -g '*.{ts,tsx,js,jsx}'
    rg "html!|Html::raw" -g '*.rs'
    rg "template\.HTML" -g '*.go'
  fix_hint: 使用 textContent 或框架的安全输出方式

- id: S03
  name: 命令注入
  category: security
  severity: critical
  applies_to: [review, postmortem]
  review_action: 检查 shell 命令拼接
  postmortem_action: 还原命令执行路径
  check_command: |
    rg "exec\(.*\+|spawn\(.*\+|system\(.*\+" -g '*.{ts,js,py,java,kt,swift,c,cpp}'
    rg "subprocess\.(run|call|Popen).*shell=True" -g '*.py'
    rg "Runtime\.getRuntime\(\)\.exec|ProcessBuilder" -g '*.{java,kt}'
    rg "Command::new.*format!|std::process::Command" -g '*.rs'
    rg "exec\.Command|os/exec" -g '*.go'
    rg "Process\(|NSTask|launchPath" -g '*.swift'
    rg "popen|execvp|execl" -g '*.{c,cpp,cc}'
  fix_hint: 使用参数数组而非字符串拼接

- id: S04
  name: 认证绕过
  category: security
  severity: critical
  applies_to: [review, postmortem]
  review_action: 检查认证逻辑完整性
  postmortem_action: 还原绕过路径
  check_command: |
    rg "isAuthenticated|isAuthorized|checkAuth|@PreAuthorize|@Secured|RequireAuth" -g '*.{ts,js,py,java,kt,go,rs,swift}'
    rg "middleware.*auth|#\[authorize\]" -g '*.{go,rs}'
  fix_hint: 确保所有敏感路由都有认证检查

- id: S05
  name: 敏感信息泄露
  category: security
  severity: high
  applies_to: [review, postmortem]
  review_action: 检查硬编码密钥和日志输出
  postmortem_action: 评估泄露范围和影响
  check_command: |
    rg "(password|secret|api_key|apikey|token)\s*[:=]\s*['\"][^'\"]{8,}['\"]" -i -g '*.{ts,js,py,java,kt,go,rs,swift,c,cpp}'
    rg "(print|log|console)\w*\(.*password" -i -g '*.{ts,js,py,java,kt,go,rs,swift}'
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
    rg "\.unwrap\(\)|\.expect\(" -g '*.rs'
    rg "NullPointerException|\.get\(\)\." -g '*.{java,kt}'
    rg "Cannot read propert|undefined is not|null is not" -g '*.{ts,js}'
    rg "AttributeError: 'NoneType'" -g '*.py'
    rg "nil pointer|invalid memory address" -g '*.go'
    rg "unexpectedly found nil|fatal error: unexpectedly found nil" -g '*.swift'
    rg "nullptr|NULL|segmentation fault" -i -g '*.{c,cpp,cc}'
  fix_hint: 使用可选链(?.)、Option/Result 或显式空值检查

- id: R02
  name: 边界条件未处理
  category: robustness
  severity: high
  applies_to: [review, postmortem]
  review_action: 检查数组索引和范围边界
  postmortem_action: 还原边界触发条件
  check_command: |
    rg "IndexOutOfBounds|index out of range|slice bounds|ArrayIndexOutOfBoundsException" -i -g '*.{ts,js,py,java,kt,go,rs,swift,c,cpp}'
  fix_hint: 添加边界检查，使用安全访问方法

- id: R03
  name: 并发竞态条件
  category: robustness
  severity: high
  applies_to: [review, postmortem]
  review_action: 检查共享状态的并发访问
  postmortem_action: 还原竞态时序
  check_command: |
    rg "async|await|Promise\.|setTimeout|setInterval" -g '*.{ts,js}'
    rg "threading|asyncio|concurrent\.futures" -g '*.py'
    rg "synchronized|ReentrantLock|Atomic" -g '*.{java,kt}'
    rg "go\s+func|sync\.(Mutex|RWMutex)|<-\s*chan" -g '*.go'
    rg "Arc<Mutex|tokio::spawn|async fn" -g '*.rs'
    rg "DispatchQueue|@MainActor|actor\s+" -g '*.swift'
    rg "pthread_|std::mutex|std::thread" -g '*.{c,cpp,cc}'
  fix_hint: 使用锁、原子操作或不可变数据

- id: R04
  name: 异常处理不当
  category: robustness
  severity: medium
  applies_to: [review, postmortem]
  review_action: 检查 try-catch 覆盖和错误处理
  postmortem_action: 分析异常传播和吞没
  check_command: |
    rg "catch\s*\([^)]*\)\s*\{\s*\}" -g '*.{ts,js,java,kt,cpp}'
    rg "except:\s*$|except Exception:\s*(pass|\.\.\.)" -g '*.py'
    rg "if err != nil \{\s*\}" -g '*.go'
    rg "\.unwrap_or\(\)|\.unwrap_or_default\(\)" -g '*.rs'
    rg "catch\s*\{\s*\}" -g '*.swift'
  fix_hint: 记录错误详情，避免空 catch 块

- id: R05
  name: 资源泄露
  category: robustness
  severity: medium
  applies_to: [review, postmortem]
  review_action: 检查文件/连接是否正确关闭
  postmortem_action: 分析资源累积和系统影响
  check_command: |
    rg "open\(|createConnection|createPool|new FileInputStream" -g '*.{py,ts,js,java,kt}'
    rg "File::open|TcpStream::connect" -g '*.rs'
    rg "os\.Open|sql\.Open|net\.Dial" -g '*.go'
    rg "FileHandle|URLSession|InputStream" -g '*.swift'
    rg "fopen|malloc|new\s+\w+\[" -g '*.{c,cpp,cc}'
  fix_hint: 使用 try-finally、defer、use/with、RAII 或 ARC
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
    rg "for.*(find|query|fetch|select)" -i -g '*.{ts,js,py,java,kt,go,rs,swift}'
  fix_hint: 使用批量查询或 JOIN

- id: P02
  name: 无限循环风险
  category: performance
  severity: high
  applies_to: [review, postmortem]
  review_action: 检查循环终止条件
  postmortem_action: 还原循环卡死条件
  check_command: |
    rg "while\s*\(\s*(true|1|YES)\s*\)|for\s*\(\s*;;\s*\)|while\s+True:|loop\s*\{" -g '*.{ts,js,py,java,kt,go,rs,swift,c,cpp}'
  fix_hint: 确保有明确的退出条件和超时机制

- id: P03
  name: 内存泄漏风险
  category: performance
  severity: medium
  applies_to: [review, postmortem]
  review_action: 检查事件监听器和定时器清理
  postmortem_action: 分析内存增长模式
  check_command: |
    rg "addEventListener|setInterval|subscribe\(" -g '*.{ts,js}'
    rg "Box::leak|mem::forget|static mut" -g '*.rs'
    rg "addObserver|NotificationCenter" -g '*.{java,kt,swift}'
    rg "malloc|realloc|new\s+\w+\[" -g '*.{c,cpp,cc}'
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
    rg "http://localhost|127\.0\.0\.1|:3000|:8080|:8000" -g '*.{ts,js,py,java,kt,go,rs,swift,c,cpp}'
  fix_hint: 使用环境变量或配置文件

- id: M02
  name: 魔法数字
  category: maintainability
  severity: low
  applies_to: [review]
  review_action: 检查未命名的数字常量
  postmortem_action: N/A
  check_command: |
    rg "[=<>]\s*\d{3,}[^0-9]" -g '*.{ts,js,py,java,kt,go,rs,swift,c,cpp}'
  fix_hint: 提取为命名常量

- id: M03
  name: 过长函数
  category: maintainability
  severity: low
  applies_to: [review]
  review_action: 检查函数行数是否超过阈值
  postmortem_action: N/A
  check_command: |
    ast-grep -p 'function $NAME($$$) { $$$BODY$$$ }' --lang typescript
    ast-grep -p 'fn $NAME($$$) { $$$BODY$$$ }' --lang rust
    ast-grep -p 'func $NAME($$$) { $$$BODY$$$ }' --lang go
    ast-grep -p 'func $NAME($$$) { $$$BODY$$$ }' --lang swift
  fix_hint: 拆分为多个职责单一的小函数
```

---

## Android 专用规则

以下规则专用 Android 平台的 Java/Kotlin 代码检查。

### 生命周期管理

```yaml
- id: A01
  name: Context 泄漏
  category: robustness
  severity: critical
  applies_to: [review, postmortem]
  review_action: 检查是否将 Activity/Fragment context 存储在静态字段
  postmortem_action: 追溯 Context 引用的传播路径
  check_command: |
    rg "static\s+(Context|Activity|Fragment|View)\s+\w+" -i -g '*.{java,kt}'
    rg "companion\s+object\s*\{\s*var\s+(context|sContext|activity)" -i -g '*.kt'
  fix_hint: 使用 Application context (context.getApplicationContext()) 或弱引用

- id: A02
  name: 主线程 UI 更新违规
  category: robustness
  severity: critical
  applies_to: [review, postmortem]
  review_action: 检查是否在后台线程更新 UI
  postmortem_action: 还原线程调用栈
  check_command: |
    rg "runOnUiThread|Handler\(\)|post\(|view\.|textView\(|imageView\(" -g '*.{java,kt}' | rg -v "withContext.*Main|Dispatchers\.Main|@UiThread|runOnUiThread"
    rg "network|apiService\.\w+|\.get\(|\.post\(" -i -g '*.{java,kt}' -A 2 | rg "view\.|\.setText|\.imageView"
  fix_hint: 使用 withContext(Dispatchers.Main) 或 runOnUiThread 包装 UI 操作

- id: A03
  name: ViewModel 引用 View/Activity
  category: robustness
  severity: critical
  applies_to: [review, postmortem]
  review_action: 检查 ViewModel 是否持有 View/Activity 引用
  postmortem_action: 分析内存泄漏根源
  check_command: |
    rg "class\s+\w+ViewModel.*Context|Activity|View|Fragment" -g '*.{java,kt}'
    rg "class\s+\w+ViewModel" -g '*.{java,kt}' -A 10 | rg "(Context|Activity|View|Fragment)\s+\w+"
  fix_hint: ViewModel 不应持有 View/Activity 引用，使用 Application context 或传递必要参数

- id: A04
  name: 使用 AsyncTask (已弃用)
  category: maintainability
  severity: high
  applies_to: [review]
  review_action: 检查是否使用已弃用的 AsyncTask
  postmortem_action: N/A
  check_command: |
    rg "AsyncTask|extends\s+AsyncTask" -g '*.{java,kt}'
  fix_hint: 使用 Kotlin Coroutines 或 WorkManager 替代 AsyncTask

- id: A05
  name: 使用 findViewById
  category: maintainability
  severity: high
  applies_to: [review]
  review_action: 检查是否使用 findViewById (应为 ViewBinding)
  postmortem_action: N/A
  check_command: |
    rg "findViewById" -g '*.{java,kt}'
  fix_hint: 使用 ViewBinding 替代 findViewById，性能更好且类型安全

### 架构与 Jetpack

```yaml
- id: A06
  name: 未使用 Repository 模式
  category: maintainability
  severity: medium
  applies_to: [review]
  review_action: 检查 ViewModel 直接访问数据源
  postmortem_action: N/A
  check_command: |
    rg "class\s+\w+ViewModel" -g '*.{java,kt}' -A 20 | rg "(RoomDatabase|SQLiteDatabase|SharedPreferences|apiService|retrofit)" -i
  fix_hint: 使用 Repository 模式封装数据源，ViewModel 通过 Repository 访问数据

- id: A07
  name: 未使用 StateFlow/SharedFlow
  category: maintainability
  severity: medium
  applies_to: [review]
  review_action: 检查是否使用 LiveData 而非 Flow
  postmortem_action: N/A
  check_command: |
    rg "LiveData<|MutableLiveData<" -g '*.{java,kt}'
  fix_hint: 新项目使用 StateFlow/SharedFlow，它们更符合 Kotlin 协程生态

- id: A08
  name: 未使用依赖注入
  category: maintainability
  severity: low
  applies_to: [review]
  review_action: 检查手动创建依赖对象
  postmortem_action: N/A
  check_command: |
    rg "val\s+\w+\s*=\s*\w+ViewModel\(\)|val\s+\w+\s*=\s*\w+Repository\(\)" -g '*.kt'
    rg "\w+\s+\w+\s*=\s*new\s+\w+ViewModel\(\)|\w+\s+\w+\s*=\s*new\s+\w+Repository\(\)" -g '*.java'
  fix_hint: 使用 Hilt 或 Dagger 进行依赖注入

### 内存管理

```yaml
- id: A09
  name: 静态引用 View/Activity
  category: robustness
  severity: critical
  applies_to: [review, postmortem]
  review_action: 检查静态字段存储 View/Activity
  postmortem_action: 追溯内存泄漏路径
  check_command: |
    rg "static\s+(View|Activity|Fragment)\s+\w+" -g '*.{java,kt}'
    rg "companion\s+object\s*\{\s*var\s+\w+:\s*(View|Activity|Fragment)" -g '*.kt'
  fix_hint: 避免静态引用 View/Activity，使用弱引用或 Application context

- id: A10
  name: 手动加载 Bitmap
  category: maintainability
  severity: medium
  applies_to: [review]
  review_action: 检查手动 Bitmap 加载和内存管理
  postmortem_action: 分析内存占用
  check_command: |
    rg "BitmapFactory\.|decode\(|Bitmap\.create|recycle\(\)" -g '*.{java,kt}'
  fix_hint: 使用 Glide 或 Coil 进行图片加载和缓存

- id: A11
  name: 未使用对象池
  category: performance
  severity: low
  applies_to: [review]
  review_action: 检查频繁对象创建
  postmortem_action: N/A
  check_command: |
    rg "RecyclerView\.Adapter.*new\s+\w+ViewHolder|new\s+\w+Item\(\)" -g '*.{java,kt}'
  fix_hint: 对频繁创建的对象使用对象池

### 数据库

```yaml
- id: A12
  name: 主线程访问数据库
  category: robustness
  severity: critical
  applies_to: [review, postmortem]
  review_action: 检查在主线程执行数据库操作
  postmortem_action: 分析 ANR 来源
  check_command: |
    rg "(RoomDatabase|SQLiteOpenHelper|ContentResolver)\..*query|\.insert\(|\.update\(|\.delete\(" -i -g '*.{java,kt}'
  fix_hint: 使用 Room 的 suspend 函数或 Coroutines 在 IO 线程执行

- id: A13
  name: N+1 查询问题
  category: performance
  severity: medium
  applies_to: [review, postmortem]
  review_action: 检查循环内数据库查询
  postmortem_action: 分析查询日志
  check_command: |
    rg "for\s*\(|forEach.*\{" -g '*.{java,kt}' -A 5 | rg "\.query\(|\.get\(|\.load\(|\.insert\(\)" -i
  fix_hint: 使用 Room @Relation 或 JOIN 查询替代循环查询

- id: A14
  name: 未分页查询大数据集
  category: performance
  severity: low
  applies_to: [review]
  review_action: 检查一次性加载大量数据
  postmortem_action: N/A
  check_command: |
    rg "getAll\(\).*List<|query\(.*List<" -g '*.{java,kt}'
  fix_hint: 使用 Paging 3 分页加载大型数据集

### 协程与线程

```yaml
- id: A15
  name: 使用错误的 Coroutine Scope
  category: robustness
  severity: critical
  applies_to: [review, postmortem]
  review_action: 检查使用 GlobalScope 或不合适的 scope
  postmortem_action: 追溯协程泄漏
  check_command: |
    rg "GlobalScope\.|CoroutineScope\(Dispatchers\)|runBlocking" -g '*.{java,kt}'
  fix_hint: Activity/Fragment 使用 lifecycleScope，ViewModel 使用 viewModelScope

- id: A16
  name: 不使用结构化并发
  category: robustness
  severity: high
  applies_to: [review, postmortem]
  review_action: 检查协程异常处理不完整
  postmortem_action: 分析异常传播
  check_command: |
    rg "launch\(.*\)\s*\{[\s\S]{0,200}" -g '*.{java,kt}' | rg -v "( supervisorScope| coroutineScope|try\s*{|try\s*\().*(launch|async)"
  fix_hint: 使用 coroutineScope 或 supervisorScope 处理协程异常

- id: A17
  name: 错误的 Dispatcher 使用
  category: maintainability
  severity: medium
  applies_to: [review]
  review_action: 检查 Dispatcher 使用不当
  postmortem_action: N/A
  check_command: |
    rg "Dispatchers\.Default.*network|Dispatchers\.Default.*database|Dispatchers\.Default.*file" -i -g '*.{java,kt}'
  fix_hint: 文件/网络/数据库操作使用 Dispatchers.IO，CPU 密集操作使用 Dispatchers.Default

### 安全

```yaml
- id: A18
  name: 硬编码 API 密钥
  category: security
  severity: critical
  applies_to: [review, postmortem]
  review_action: 检查硬编码的密钥和凭证
  postmortem_action: 评估泄露风险
  check_command: |
    rg "(api_key|apikey|secret|token|password|credential)\s*[=:].*['\"][^'\"]{8,}['\"]" -i -g '*.{java,kt,xml,gradle}'
    rg "API_KEY|SECRET_KEY|AUTH_TOKEN" -g '*.{java,kt,xml,gradle}' -A 1 | rg "[=:].*['\"][^'\"]"
  fix_hint: 使用 local.properties 或 secure storage 存储密钥

- id: A19
  name: Room SQL 注入风险
  category: security
  severity: critical
  applies_to: [review, postmortem]
  review_action: 检查 Room 原始 SQL 查询
  postmortem_action: 追溯注入路径
  check_command: |
    rg "@Query.*\$\{|@Query.*\+|rawQuery.*\$\{|rawQuery.*\+" -g '*.{java,kt}'
  fix_hint: 使用 Room 的 @Query 参数绑定或 ? 占位符

- id: A20
  name: 非 HTTPS 网络请求
  category: security
  severity: high
  applies_to: [review, postmortem]
  review_action: 检查使用 HTTP 而非 HTTPS
  postmortem_action: 评估中间人攻击风险
  check_command: |
    rg "http://|BASE_URL\s*=\s*['\"]http:" -g '*.{java,kt,xml}'
  fix_hint: 使用 HTTPS，并配置网络安全策略

- id: A21
  name: 日志输出敏感信息
  category: security
  severity: critical
  applies_to: [review, postmortem]
  review_action: 检查日志输出密码、token 等敏感信息
  postmortem_action: 分析日志泄露范围
  check_command: |
    rg "Log\.\w*\(.*(password|token|secret|credential|ssn|credit)" -i -g '*.{java,kt}'
    rg "println\(.*(password|token|secret)" -i -g '*.{java,kt}'
  fix_hint: 删除敏感信息日志输出

- id: A22
  name: 未使用 EncryptedSharedPreferences
  category: security
  severity: medium
  applies_to: [review, postmortem]
  review_action: 检查存储敏感数据到普通 SharedPreferences
  postmortem_action: 分析数据泄露风险
  check_command: |
    rg "SharedPreferences\.get|PreferenceManager\.getDefaultSharedPreferences" -g '*.{java,kt}'
    rg "getString\(.*(password|token|secret|auth|session)" -i -g '*.{java,kt}'
  fix_hint: 敏感数据使用 EncryptedSharedPreferences 或 Keystore 加密存储

- id: A23
  name: 未配置 ProGuard/R8
  category: security
  severity: medium
  applies_to: [review]
  review_action: 检查 release 构建是否启用代码混淆
  postmortem_action: N/A
  check_command: |
    rg "buildConfigField.*debuggable|buildTypes\s*\{[\s\S]{0,300}\}" -g '*.{kt,gradle}' | rg -v "minifyEnabled\s*true|isMinifyEnabled\s*true"
  fix_hint: release 构建启用 R8 minification 和 shrinkResources

### 权限

```yaml
- id: A24
  name: 未检查运行时权限
  category: robustness
  severity: critical
  applies_to: [review, postmortem]
  review_action: 检查敏感操作前未检查权限
  postmortem_action: 分析权限拒绝导致的崩溃
  check_command: |
    rg "(LocationManager|checkSelfPermission|requestPermissions)" -g '*.{java,kt}'
    rg "(location|camera|storage|contact|phone)\s*\." -i -g '*.{java,kt}' -B 2 | rg -v "checkSelfPermission"
  fix_hint: 使用 ContextCompat.checkSelfPermission 检查权限后再操作

- id: A25
  name: 敏感权限无说明
  category: maintainability
  severity: high
  applies_to: [review]
  review_action: 检查请求敏感权限前无说明
  postmortem_action: N/A
  check_command: |
    rg "requestPermissions\(" -g '*.{java,kt}' -B 5 | rg -v "shouldShowRequestPermissionRationale|beforeRequest|explain"
  fix_hint: 在请求 CAMERA/LOCATION 等敏感权限前显示说明

### 资源与国际化

```yaml
- id: A26
  name: 硬编码字符串
  category: maintainability
  severity: medium
  applies_to: [review]
  review_action: 检查 UI 文本硬编码
  postmortem_action: N/A
  check_command: |
    rg "(text|toast|alert|title|hint)\s*[=:]?\s*['\"][^'\"]{4,}['\"]" -i -g '*.{java,kt}' | rg -v "(R\.string\.|getString\()"
  fix_hint: 使用 string resources (R.string.xxx) 存储文本

- id: A27
  name: 使用 PNG 而非 Vector Drawable
  category: maintainability
  severity: low
  applies_to: [review]
  review_action: 检查图标使用 PNG
  postmortem_action: N/A
  check_command: |
    rg "R\.drawable\.|srcCompat\s*=" -g '*.{java,kt,xml}' | rg "\.png|\.jpg|\.jpeg" -i
  fix_hint: 图标使用 Vector Drawables 可减小 APK 体积并适配多分辨率

### 测试

```yaml
- id: A28
  name: ViewModel/Repository 缺少单元测试
  category: maintainability
  severity: low
  applies_to: [review]
  review_action: 检查核心业务逻辑是否有测试覆盖
  postmortem_action: N/A
  check_command: |
    rg "class\s+\w+ViewModel|class\s+\w+Repository" -g '*.{java,kt}'
    rg "test.*ViewModel|test.*Repository" -g '*Test.{java,kt}' --count
  fix_hint: 为 ViewModel 和 Repository 编写单元测试

- id: A29
  name: 无 UI 测试
  category: maintainability
  severity: low
  applies_to: [review]
  review_action: 检查关键用户流程是否有 UI 测试
  postmortem_action: N/A
  check_command: |
    rg "Espresso|ComposeTestRule|@UiTest" -g '*Test.{java,kt}' --count
  fix_hint: 为关键用户流程编写 Espresso 或 Compose UI 测试
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
