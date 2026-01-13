# Release Skill

发布管理工具，生成 changelog 和发布说明。

## 命令格式

```bash
/release changelog          # 生成 changelog
/release notes <version>    # 生成发布说明
/release diff <v1> <v2>     # 版本差异分析
```

## 工作流程

```
Task Progress:
- [ ] 1. 分析 commit 历史
- [ ] 2. 提取变更类型
- [ ] 3. 聚合相关文档
- [ ] 4. 生成 changelog/发布说明
```

### Step 1: 分析 commit 历史

```bash
# 获取版本间的 commits
git log <v1>..<v2> --oneline --no-merges

# 按类型分类 (Conventional Commits)
git log <v1>..<v2> --oneline | rg "^[a-f0-9]+ (feat|fix|docs|style|refactor|perf|test|chore):"

# 获取详细信息
git log <v1>..<v2> --pretty=format:"%h|%s|%an|%ad" --date=short
```

### Step 2: 提取变更类型

| 前缀 | 类型 | 说明 |
|------|------|------|
| feat | Features | 新功能 |
| fix | Bug Fixes | 错误修复 |
| docs | Documentation | 文档更新 |
| perf | Performance | 性能优化 |
| refactor | Refactoring | 代码重构 |
| test | Tests | 测试相关 |
| chore | Chores | 构建/工具 |

### Step 3: 聚合相关文档

```bash
# 检索相关 postmortem
rg "refs:" -A 5 .claude/postmortem/ | rg "commits:.*<commit>"

# 检索相关 ADR (如有)
rg "refs:" -A 5 .claude/adr/ | rg "commits:.*<commit>"

# 检索相关 review
rg "refs:" -A 5 .claude/reviews/ | rg "commits:.*<commit>"
```

### Step 4: Breaking Changes 检测

```bash
# 检查 commit message
git log <v1>..<v2> --oneline | rg -i "breaking|BREAKING"

# 检查 API 变更
git diff <v1>..<v2> -- '*.ts' '*.py' '*.go' | rg "^[-+].*export|^[-+].*def |^[-+].*func "
```

## Changelog 模板

```markdown
# Changelog

## [1.2.0] - 2025-01-13

### Features

- **auth**: Add OAuth2 support (#123)
- **api**: New user management endpoints (#125)

### Bug Fixes

- **auth**: Fix token refresh race condition (#124)
  - Related: [postmortem-250110](../.claude/postmortem/250110-token-race/REPORT.md)

### Performance

- **cache**: Optimize query caching (#126)

### Breaking Changes

- **api**: Remove deprecated `/v1/users` endpoint
  - Migration: Use `/v2/users` instead

### Related Documents

- [ADR-005: OAuth2 Implementation](../.claude/adr/250108-oauth2/ADR.md)
- [Postmortem: Token Race Condition](../.claude/postmortem/250110-token-race/REPORT.md)
```

## 发布说明模板

```markdown
# Release Notes v1.2.0

## Highlights

- OAuth2 authentication support
- New user management API
- Performance improvements

## What's New

### OAuth2 Support

Now supports OAuth2 authentication with major providers:
- Google
- GitHub
- Microsoft

### Improved Performance

Query caching optimized, reducing API response time by 40%.

## Breaking Changes

### Deprecated API Removal

The `/v1/users` endpoint has been removed. Please migrate to `/v2/users`.

**Before:**
```bash
curl /api/v1/users
```

**After:**
```bash
curl /api/v2/users
```

## Bug Fixes

- Fixed token refresh race condition that could cause authentication failures

## Upgrade Guide

1. Update OAuth config in `.env`
2. Migrate API calls from v1 to v2
3. Test authentication flow

## Contributors

- @developer1
- @developer2
```

## 输出位置

```
.claude/release/
├── CHANGELOG.md        # 完整 changelog
└── <version>/
    └── NOTES.md        # 版本发布说明
```
