---
id: android-rules
version: "1.0"
updated_at: "2026-01-17"
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
- id: 规则唯一标识 (A01-A18)
  name: 规则名称
  category: performance | robustness
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
  name: Bitmap 内存管理
  category: robustness
  severity: high
  applies_to: [review, postmortem]
  review_action: 检查大图加载和 Bitmap 回收
  postmortem_action: 分析 OOM 时的 Bitmap 内存占用
  check_command: |
    rg "BitmapFactory\.decode" -g '*.{java,kt}'
    rg "Bitmap\.createBitmap" -g '*.{java,kt}'
    rg "inSampleSize|inJustDecodeBounds" -g '*.{java,kt}'
  fix_hint: 使用 Glide/Coil 等图片库，配置适当的采样率

- id: A13
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

- id: A14
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
- id: A15
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

- id: A16
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

- id: A17
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

- id: A18
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
