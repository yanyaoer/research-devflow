# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

**Research DevFlow** 是一个将软件工程流程（规划、开发、复盘）转化为 AI 可执行任务的自动化框架。核心理念是 **"质量闭环"**：
1.  **Research**: 任务拆解与规划
2.  **Review**: 代码质量审查
3.  **Postmortem**: 事故根因分析与知识沉淀

## 核心架构

*   **Skills (`skills/`)**: AI 能力单元。每个目录（如 `postmortem`, `review`）包含 `SKILL.md`，定义工作流、Prompt 模板和执行步骤。
*   **规范文档 (`docs/`)**:
    *   `META-SCHEMA.md`: **元数据标准**。所有 AI 生成文档必须严格遵守此 Schema，以支持语义检索。
    *   `RULES-CODE-QUALITY.md`: **通用代码质量规则库**。包含可执行的 CLI 检查命令（`rg`, `ast-grep`）。
    *   `RULES-ANDROID.md`: **Android 代码质量规则库**。针对 Android 系统研发的性能和健壮性规则。
*   **资产存储 (`<project-root>/.claude/`)**: 所有知识资产（复盘报告、审查记录等）均以 Markdown/JSON 形式本地存储于目标项目的 `<project-root>/.claude/` 目录下。

## 设计原则与约束

1.  **严格遵守 Meta Schema**: 生成文档（Plan, Report, ADR）时，**必须** 包含 `docs/META-SCHEMA.md` 定义的 YAML Frontmatter。这是 AI 检索系统的基础。
2.  **本地化资产**: 仅使用文件系统存储状态，不引入外部数据库。
3.  **工具化分析**: 优先使用 CLI 工具（`rg`, `fd`, `ast-grep`）进行客观验证，减少 LLM 主观臆断。
4.  **KISS**: 保持轻量，拒绝过度设计。

## 常用开发命令

### 规则查询
获取特定场景的检查规则：
```bash
# 获取 Review 场景的所有规则
python scripts/rule_query.py --query review

# 获取 Postmortem 场景的安全类规则
python scripts/rule_query.py --query postmortem --category security

# 获取 Android 性能规则
python scripts/rule_query.py -r docs/RULES-ANDROID.md --query review --category performance

# 获取 Android 健壮性规则 (内存泄漏、并发等)
python scripts/rule_query.py -r docs/RULES-ANDROID.md --query postmortem --category robustness
```

### 知识库检索
检索历史沉淀（复盘、审查、ADR）：
```bash
# 按模块检索
rg "modules:.*src/auth" .claude/

# 按关键词检索
rg "keywords:.*token" .claude/
```

### 新增 Skill 流程
1.  创建 `skills/<new-skill>/SKILL.md`。
2.  定义工作流与 Prompt 模板。
3.  **关键**: 确保产出文档符合 `docs/META-SCHEMA.md`。
4.  在 `README.md` 中注册新 Skill。
