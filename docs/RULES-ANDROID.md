---
id: android-rules
version: "1.1"
updated_at: "2026-01-20"
---

# Android 代码质量检查规则

## 支持的语言

| 语言 | 扩展名 | rg --type |
|------|--------|-----------|
| Java | java | java |
| Kotlin | kt, kts | kotlin |

### 快捷 Glob 模式

```bash
# Android 代码扫描
ANDROID_GLOB='*.{java,kt,kts}'

# 使用示例
rg "pattern" -g "$ANDROID_GLOB"
```

## 规则格式说明

```yaml
- id: 规则唯一标识 (A01-A17, AM01-AM17, AR19-AR30)
  name: 规则名称
  category: performance | robustness | security | permissions | resources | testing | maintainability
  severity: critical | high | medium | low
  applies_to: [review, postmortem]
  review_action: review 时的检查动作
  postmortem_action: postmortem 时的分析动作
  check_command: 检查命令
  fix_hint: 修复提示
```

---

## 性能类 (performance)

### 主线程与阻塞操作

```yaml
- id: A01
  name: 主线程阻塞操作
  category: performance
  severity: critical
  applies_to: [review, postmortem]
  review_action: 检查主线程中的 I/O、网络、数据库同步调用
  postmortem_action: 追溯 ANR 或卡顿的阻塞调用栈
  check_command: |
    rg "StrictMode|NetworkOnMainThreadException" -g '*.{java,kt}'
    rg "(FileInputStream|FileOutputStream|RandomAccessFile)\s*\(" -g '*.{java,kt}'
    rg "URLConnection|HttpURLConnection|OkHttpClient.*\.execute\(" -g '*.{java,kt}'
    rg "Room.*Dao.*\(\)(?!.*suspend)" -g '*.kt'
  fix_hint: 使用协程/RxJava 将阻塞操作移至后台线程，或使用 suspend 函数

- id: A02
  name: 重复计算与无效对象创建
  category: performance
  severity: high
  applies_to: [review, postmortem]
  review_action: 检查循环内的对象创建和字符串拼接
  postmortem_action: 分析 GC 日志和内存分配热点
  check_command: |
    rg "for\s*\([^)]+\)\s*\{[^}]*new\s+(String|StringBuilder|ArrayList|HashMap)" -g '*.{java,kt}'
    rg "while\s*\([^)]+\)\s*\{[^}]*new\s+" -g '*.{java,kt}'
    rg 'for\s*\([^)]+\)\s*\{[^}]*\+\s*"' -g '*.java'
  fix_hint: 将对象创建移至循环外，使用 StringBuilder 进行字符串拼接

- id: A03
  name: 隐式循环开销
  category: performance
  severity: medium
  applies_to: [review, postmortem]
  review_action: 检查 Stream/Sequence 的多次遍历
  postmortem_action: 分析性能 trace 中的迭代热点
  check_command: |
    rg "\.stream\(\).*\.collect\(.*\.stream\(\)" -g '*.java'
    rg "\.asSequence\(\).*\.toList\(\).*\.asSequence\(\)" -g '*.kt'
    rg "\.map\{.*\}\.filter\{.*\}\.map\{" -g '*.kt'
  fix_hint: 合并链式操作，避免中间集合创建

- id: A04
  name: Binder 慢调用
  category: performance
  severity: high
  applies_to: [review, postmortem]
  review_action: 检查主线程的系统服务同步调用
  postmortem_action: 追溯 Binder 调用耗时和阻塞点
  check_command: |
    rg "getSystemService\s*\(" -g '*.{java,kt}'
    rg "contentResolver\.(query|insert|update|delete)\s*\(" -g '*.{java,kt}'
    rg "packageManager\.(getPackageInfo|getInstalledPackages|resolveActivity)" -g '*.{java,kt}'
  fix_hint: 将系统服务调用移至后台线程，缓存服务实例

- id: A05
  name: 同步块中的慢操作
  category: performance
  severity: high
  applies_to: [review, postmortem]
  review_action: 检查 synchronized 块内的 I/O 和网络操作
  postmortem_action: 分析锁竞争导致的线程阻塞
  check_command: |
    rg "synchronized\s*\([^)]+\)\s*\{[^}]*(File|Stream|Socket|Http|Database)" -g '*.java'
    rg "@Synchronized[^}]*(File|Stream|Socket|Http|Database)" -g '*.kt'
  fix_hint: 缩小同步范围，将 I/O 操作移出同步块
```

### 渲染与 UI 链路

```yaml
- id: A06
  name: 过度 invalidate/requestLayout
  category: performance
  severity: high
  applies_to: [review, postmortem]
  review_action: 检查频繁调用 invalidate() 或 requestLayout()
  postmortem_action: 分析 Systrace 中的过度绘制
  check_command: |
    rg "invalidate\(\)|postInvalidate\(\)" -g '*.{java,kt}'
    rg "requestLayout\(\)" -g '*.{java,kt}'
    rg "for\s*\([^)]+\)\s*\{[^}]*(invalidate|requestLayout)" -g '*.{java,kt}'
  fix_hint: 合并多次刷新请求，使用局部刷新 invalidate(Rect)

- id: A07
  name: onDraw 耗时操作
  category: performance
  severity: critical
  applies_to: [review, postmortem]
  review_action: 检查绘制回调中的对象创建和耗时计算
  postmortem_action: 分析帧耗时和绘制性能
  check_command: |
    rg "onDraw\s*\([^)]*\)\s*\{[^}]*new\s+(Paint|Path|Rect|Matrix)" -g '*.{java,kt}'
    rg "onDraw\s*\([^)]*\)\s*\{[^}]*Bitmap" -g '*.{java,kt}'
    rg "override fun onDraw[^}]*=\s*\w+\(" -g '*.kt'
  fix_hint: 将 Paint/Path 等对象提升为成员变量，在构造函数中初始化

- id: A08
  name: 布局层级过深
  category: performance
  severity: medium
  applies_to: [review, postmortem]
  review_action: 检查多层嵌套的 LinearLayout/RelativeLayout
  postmortem_action: 分析布局渲染耗时
  check_command: |
    rg "<LinearLayout[^>]*>[^<]*<LinearLayout[^>]*>[^<]*<LinearLayout" -g '*.xml'
    rg "<RelativeLayout[^>]*>[^<]*<RelativeLayout" -g '*.xml'
    rg "layout_weight" -g '*.xml'
  fix_hint: 使用 ConstraintLayout 扁平化布局，避免嵌套 weight

- id: A09
  name: UI 状态渲染耦合
  category: performance
  severity: medium
  applies_to: [review, postmortem]
  review_action: 检查 LiveData/StateFlow 更新触发的全量重绘
  postmortem_action: 分析状态变更与 UI 刷新的关联
  check_command: |
    rg "\.observe\s*\([^)]+\)\s*\{[^}]*adapter\.notifyDataSetChanged" -g '*.{java,kt}'
    rg "\.collect\s*\{[^}]*notifyDataSetChanged" -g '*.kt'
    rg "setState\s*\{[^}]*copy\(" -g '*.kt'
  fix_hint: 使用 DiffUtil 进行差分更新，拆分细粒度状态
```

---

## 健壮性 (robustness)

### 内存与对象生命周期

```yaml
- id: A10
  name: 高频临时对象
  category: robustness
  severity: high
  applies_to: [review, postmortem]
  review_action: 检查 onDraw/onMeasure/onLayout 中的对象创建
  postmortem_action: 分析 GC 频率和内存抖动
  check_command: |
    rg "onDraw\s*\([^)]*\)\s*\{[^}]*new\s+" -g '*.{java,kt}'
    rg "onMeasure\s*\([^)]*\)\s*\{[^}]*new\s+" -g '*.{java,kt}'
    rg "onLayout\s*\([^)]*\)\s*\{[^}]*new\s+" -g '*.{java,kt}'
    rg "onBindViewHolder\s*\([^)]*\)\s*\{[^}]*new\s+" -g '*.{java,kt}'
  fix_hint: 复用对象，使用对象池或成员变量缓存

- id: A11
  name: 内存泄漏风险
  category: robustness
  severity: critical
  applies_to: [review, postmortem]
  review_action: 检查非静态内部类、Handler 泄漏、Context 泄漏
  postmortem_action: 分析 LeakCanary 或 MAT 报告
  check_command: |
    rg "class\s+\w+\s+extends\s+AsyncTask" -g '*.java'
    rg "new\s+Handler\s*\(\s*\)" -g '*.{java,kt}'
    rg "object\s*:\s*Runnable" -g '*.kt'
    rg "inner class.*:.*Callback|inner class.*:.*Listener" -g '*.kt'
  fix_hint: 使用静态内部类+WeakReference，或使用 lifecycleScope

- id: A12
  name: 缓存策略问题
  category: robustness
  severity: medium
  applies_to: [review, postmortem]
  review_action: 检查无界 HashMap 缓存和 LruCache 配置
  postmortem_action: 分析缓存膨胀导致的 OOM
  check_command: |
    rg "HashMap<.*>\s*\(\s*\)" -g '*.{java,kt}'
    rg "mutableMapOf<" -g '*.kt'
    rg "LruCache<[^>]+>\s*\([^)]*\)" -g '*.{java,kt}'
    rg "object\s*:\s*LinkedHashMap" -g '*.{java,kt}'
  fix_hint: 使用 LruCache 或 WeakHashMap，设置合理的缓存上限

- id: A13
  name: 生命周期泄漏
  category: robustness
  severity: critical
  applies_to: [review, postmortem]
  review_action: 检查 Activity/Fragment 引用泄漏
  postmortem_action: 分析生命周期与引用链
  check_command: |
    rg "companion object\s*\{[^}]*Activity|companion object\s*\{[^}]*Fragment" -g '*.kt'
    rg "static.*Activity|static.*Fragment|static.*Context" -g '*.java'
    rg "\.applicationContext|getApplicationContext\(\)" -g '*.{java,kt}'
  fix_hint: 使用 applicationContext 替代 Activity Context，避免静态持有
```

### 并发锁

```yaml
- id: A14
  name: 主线程持锁
  category: robustness
  severity: critical
  applies_to: [review, postmortem]
  review_action: 检查主线程的 synchronized 和 ReentrantLock
  postmortem_action: 分析 ANR trace 中的锁等待
  check_command: |
    rg "@MainThread[^}]*synchronized" -g '*.{java,kt}'
    rg "@UiThread[^}]*synchronized" -g '*.{java,kt}'
    rg "runOnUiThread\s*\{[^}]*synchronized" -g '*.kt'
    rg "Looper\.getMainLooper\(\)[^}]*lock\(" -g '*.{java,kt}'
  fix_hint: 避免在主线程持有锁，使用无锁数据结构或异步机制

- id: A15
  name: 锁粒度过大
  category: robustness
  severity: medium
  applies_to: [review, postmortem]
  review_action: 检查大范围同步块
  postmortem_action: 分析锁竞争和线程阻塞时间
  check_command: |
    rg "synchronized\s*\(this\)" -g '*.java'
    rg "@Synchronized\s+fun\s+\w+\([^)]*\)\s*\{" -g '*.kt'
    rg "ReentrantLock\(\)\.withLock\s*\{" -g '*.kt'
  fix_hint: 缩小同步范围，使用细粒度锁或并发集合

- id: A16
  name: 死锁风险
  category: robustness
  severity: high
  applies_to: [review, postmortem]
  review_action: 检查嵌套锁获取
  postmortem_action: 分析死锁时的线程 dump
  check_command: |
    rg "synchronized\s*\([^)]+\)\s*\{[^}]*synchronized\s*\(" -g '*.java'
    rg "lock\(\)[^}]*lock\(\)" -g '*.{java,kt}'
    rg "withLock\s*\{[^}]*withLock" -g '*.kt'
  fix_hint: 统一锁获取顺序，使用 tryLock 带超时，或重构避免嵌套锁

- id: A17
  name: 竞态条件
  category: robustness
  severity: high
  applies_to: [review, postmortem]
  review_action: 检查非线程安全集合的并发访问
  postmortem_action: 分析 ConcurrentModificationException 和数据不一致
  check_command: |
    rg "ArrayList<|HashMap<|HashSet<" -g '*.{java,kt}'
    rg "mutableListOf|mutableMapOf|mutableSetOf" -g '*.kt'
    rg "ConcurrentModificationException" -g '*.{java,kt}'
  fix_hint: 使用 ConcurrentHashMap、CopyOnWriteArrayList 或加锁保护
```

---

## 安全 (security)

```yaml
- id: AR19
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

- id: AR20
  name: Room SQL 注入风险
  category: security
  severity: critical
  applies_to: [review, postmortem]
  review_action: 检查 Room 原始 SQL 查询
  postmortem_action: 追溯注入路径
  check_command: |
    rg "@Query.*\$\{|@Query.*\+|rawQuery.*\$\{|rawQuery.*\+" -g '*.{java,kt}'
  fix_hint: 使用 Room 的 @Query 参数绑定或 ? 占位符

- id: AR21
  name: 非 HTTPS 网络请求
  category: security
  severity: high
  applies_to: [review, postmortem]
  review_action: 检查使用 HTTP 而非 HTTPS
  postmortem_action: 评估中间人攻击风险
  check_command: |
    rg "http://|BASE_URL\s*=\s*['\"]http:" -g '*.{java,kt,xml}'
  fix_hint: 使用 HTTPS，并配置网络安全策略

- id: AR22
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

- id: AR23
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

- id: AR24
  name: 未配置 ProGuard/R8
  category: security
  severity: medium
  applies_to: [review]
  review_action: 检查 release 构建是否启用代码混淆
  postmortem_action: N/A
  check_command: |
    rg "buildConfigField.*debuggable|buildTypes\s*\{[\s\S]{0,300}\}" -g '*.{kt,gradle}' | rg -v "minifyEnabled\s*true|isMinifyEnabled\s*true"
  fix_hint: release 构建启用 R8 minification 和 shrinkResources
```

---

## 权限 (permissions)

```yaml
- id: AR25
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

- id: AR26
  name: 敏感权限无说明
  category: maintainability
  severity: high
  applies_to: [review]
  review_action: 检查请求敏感权限前无说明
  postmortem_action: N/A
  check_command: |
    rg "requestPermissions\(" -g '*.{java,kt}' -B 5 | rg -v "shouldShowRequestPermissionRationale|beforeRequest|explain"
  fix_hint: 在请求 CAMERA/LOCATION 等敏感权限前显示说明
```

---

## 资源与国际化 (resources)

```yaml
- id: AR27
  name: 硬编码字符串
  category: maintainability
  severity: medium
  applies_to: [review]
  review_action: 检查 UI 文本硬编码
  postmortem_action: N/A
  check_command: |
    rg "(text|toast|alert|title|hint)\s*[=:]?\s*['\"][^'\"]{4,}['\"]" -i -g '*.{java,kt}' | rg -v "(R\.string\.|getString\()"
  fix_hint: 使用 string resources (R.string.xxx) 存储文本

- id: AR28
  name: 使用 PNG 而非 Vector Drawable
  category: maintainability
  severity: low
  applies_to: [review]
  review_action: 检查图标使用 PNG
  postmortem_action: N/A
  check_command: |
    rg "R\.drawable\.|srcCompat\s*=" -g '*.{java,kt,xml}' | rg "\.png|\.jpg|\.jpeg" -i
  fix_hint: 图标使用 Vector Drawables 可减小 APK 体积并适配多分辨率
```

---

## 架构与可维护性 (maintainability)

```yaml
- id: AM01
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

- id: AM02
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

- id: AM03
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

- id: AM04
  name: 使用 AsyncTask (已弃用)
  category: maintainability
  severity: high
  applies_to: [review]
  review_action: 检查是否使用已弃用的 AsyncTask
  postmortem_action: N/A
  check_command: |
    rg "AsyncTask|extends\s+AsyncTask" -g '*.{java,kt}'
  fix_hint: 使用 Kotlin Coroutines 或 WorkManager 替代 AsyncTask

- id: AM05
  name: 使用 findViewById
  category: maintainability
  severity: high
  applies_to: [review]
  review_action: 检查是否使用 findViewById (应为 ViewBinding)
  postmortem_action: N/A
  check_command: |
    rg "findViewById" -g '*.{java,kt}'
  fix_hint: 使用 ViewBinding 替代 findViewById，性能更好且类型安全

- id: AM06
  name: 未使用 Repository 模式
  category: maintainability
  severity: medium
  applies_to: [review]
  review_action: 检查 ViewModel 直接访问数据源
  postmortem_action: N/A
  check_command: |
    rg "class\s+\w+ViewModel" -g '*.{java,kt}' -A 20 | rg "(RoomDatabase|SQLiteDatabase|SharedPreferences|apiService|retrofit)" -i
  fix_hint: 使用 Repository 模式封装数据源，ViewModel 通过 Repository 访问数据

- id: AM07
  name: 未使用 StateFlow/SharedFlow
  category: maintainability
  severity: medium
  applies_to: [review]
  review_action: 检查是否使用 LiveData 而非 Flow
  postmortem_action: N/A
  check_command: |
    rg "LiveData<|MutableLiveData<" -g '*.{java,kt}'
  fix_hint: 新项目使用 StateFlow/SharedFlow，它们更符合 Kotlin 协程生态

- id: AM08
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

- id: AM09
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

- id: AM10
  name: 手动加载 Bitmap
  category: maintainability
  severity: medium
  applies_to: [review]
  review_action: 检查手动 Bitmap 加载和内存管理
  postmortem_action: 分析内存占用
  check_command: |
    rg "BitmapFactory\.|decode\(|Bitmap\.create|recycle\(\)" -g '*.{java,kt}'
  fix_hint: 使用 Glide 或 Coil 进行图片加载和缓存

- id: AM11
  name: 未使用对象池
  category: performance
  severity: low
  applies_to: [review]
  review_action: 检查频繁对象创建
  postmortem_action: N/A
  check_command: |
    rg "RecyclerView\.Adapter.*new\s+\w+ViewHolder|new\s+\w+Item\(\)" -g '*.{java,kt}'
  fix_hint: 对频繁创建的对象使用对象池

- id: AM12
  name: 主线程访问数据库
  category: robustness
  severity: critical
  applies_to: [review, postmortem]
  review_action: 检查在主线程执行数据库操作
  postmortem_action: 分析 ANR 来源
  check_command: |
    rg "(RoomDatabase|SQLiteOpenHelper|ContentResolver)\..*query|\.insert\(|\.update\(|\.delete\(" -i -g '*.{java,kt}'
  fix_hint: 使用 Room 的 suspend 函数或 Coroutines 在 IO 线程执行

- id: AM13
  name: N+1 查询问题
  category: performance
  severity: medium
  applies_to: [review, postmortem]
  review_action: 检查循环内数据库查询
  postmortem_action: 分析查询日志
  check_command: |
    rg "for\s*\(|forEach.*\{" -g '*.{java,kt}' -A 5 | rg "\.query\(|\.get\(|\.load\(|\.insert\(\)" -i
  fix_hint: 使用 Room @Relation 或 JOIN 查询替代循环查询

- id: AM14
  name: 未分页查询大数据集
  category: performance
  severity: low
  applies_to: [review]
  review_action: 检查一次性加载大量数据
  postmortem_action: N/A
  check_command: |
    rg "getAll\(\).*List<|query\(.*List<" -g '*.{java,kt}'
  fix_hint: 使用 Paging 3 分页加载大型数据集

- id: AM15
  name: 使用错误的 Coroutine Scope
  category: robustness
  severity: critical
  applies_to: [review, postmortem]
  review_action: 检查使用 GlobalScope 或不合适的 scope
  postmortem_action: 追溯协程泄漏
  check_command: |
    rg "GlobalScope\.|CoroutineScope\(Dispatchers\)|runBlocking" -g '*.{java,kt}'
  fix_hint: Activity/Fragment 使用 lifecycleScope，ViewModel 使用 viewModelScope

- id: AM16
  name: 不使用结构化并发
  category: robustness
  severity: high
  applies_to: [review, postmortem]
  review_action: 检查协程异常处理不完整
  postmortem_action: 分析异常传播
  check_command: |
    rg "launch\(.*\)\s*\{[\s\S]{0,200}" -g '*.{java,kt}' | rg -v "( supervisorScope| coroutineScope|try\s*{|try\s*\().*(launch|async)"
  fix_hint: 使用 coroutineScope 或 supervisorScope 处理协程异常

- id: AM17
  name: 错误的 Dispatcher 使用
  category: maintainability
  severity: medium
  applies_to: [review]
  review_action: 检查 Dispatcher 使用不当
  postmortem_action: N/A
  check_command: |
    rg "Dispatchers\.Default.*network|Dispatchers\.Default.*database|Dispatchers\.Default.*file" -i -g '*.{java,kt}'
  fix_hint: 文件/网络/数据库操作使用 Dispatchers.IO，CPU 密集操作使用 Dispatchers.Default
```

---

## 测试 (testing)

```yaml
- id: AR29
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

- id: AR30
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
# 获取所有 Android review 规则
python scripts/rule_query.py -r docs/RULES-ANDROID.md --query review

# 获取性能类规则
python scripts/rule_query.py -r docs/RULES-ANDROID.md --query review --category performance

# 获取健壮性规则
python scripts/rule_query.py -r docs/RULES-ANDROID.md --query review --category robustness
```

### Postmortem 场景

```bash
# 获取 ANR/卡顿分析规则
python scripts/rule_query.py -r docs/RULES-ANDROID.md --query postmortem --category performance

# 获取 OOM/内存泄漏分析规则
python scripts/rule_query.py -r docs/RULES-ANDROID.md --query postmortem --category robustness
```

### 执行检查

```bash
# 对 Android 代码执行性能检查
python scripts/rule_query.py -r docs/RULES-ANDROID.md --query review --category performance --format json | \
  jq -r '.rules[].check_command' | \
  while read cmd; do eval "$cmd"; done
```
