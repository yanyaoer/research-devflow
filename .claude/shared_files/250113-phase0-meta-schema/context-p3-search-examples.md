# P3: 添加检索命令示例到各 skill

## 任务目标

在各 skill 的 SKILL.md 中添加标准化的检索命令示例，使 AI 能够正确检索相关知识。

## 依赖任务

- P2: 创建 META-SCHEMA.md 文档

## 实现步骤

### Step 1: 更新 research/SKILL.md

在 "Postmortem 扫描" 章节添加完整的检索命令：

```markdown
## 知识库检索

执行任务前，检索相关知识文档：

### 检索命令

```bash
# 按涉及的模块检索
rg "modules:.*<module>" .claude/postmortem/ .claude/adr/

# 按关键词检索
rg "keywords:.*<keyword>" .claude/

# 按文件路径检索
rg "files:.*<file-pattern>" .claude/

# 提取匹配文档的 frontmatter
fd REPORT.md .claude/postmortem/ -x sed -n '/^---$/,/^---$/p' {}
```

### 匹配规则

1. scope.modules/files/functions 与任务涉及范围有交集 → 高相关
2. keywords 有交集 → 中相关
3. relevance.must_read 条件命中 → 必读
```

### Step 2: 更新 postmortem/SKILL.md

添加历史 postmortem 检索章节：

```markdown
## 历史问题检索

分析新问题前，检索类似历史问题：

```bash
# 按根因类型检索
rg "root_cause:" -A 2 .claude/postmortem/ | rg "<type>"

# 按影响模块检索
rg "modules:.*<module>" .claude/postmortem/

# 按严重程度检索
rg "severity: P0" .claude/postmortem/
```
```

### Step 3: 创建通用检索模板

在 docs/META-SCHEMA.md 中添加检索命令速查表。

## 涉及文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `skills/research/SKILL.md` | 修改 | 添加检索命令 |
| `skills/postmortem/SKILL.md` | 修改 | 添加历史检索 |
| `docs/META-SCHEMA.md` | 修改 | 添加检索速查表 |

## 验证方法

```bash
# 检查 research 检索命令
rg "知识库检索|检索命令" skills/research/SKILL.md

# 检查 postmortem 检索命令
rg "历史问题检索" skills/postmortem/SKILL.md

# 测试检索命令是否可用
rg "scope:" .claude/ 2>/dev/null || echo "暂无知识文档"
```

## 完成标准

- [ ] research/SKILL.md 包含检索命令章节
- [ ] postmortem/SKILL.md 包含历史检索章节
- [ ] docs/META-SCHEMA.md 包含检索速查表
- [ ] 更新 task-status.json
- [ ] Git 提交
