# Phase 2: 质量保障 Skills

## 目标

创建三个质量保障相关的 skill：
1. **tech-debt**: 技术债务追踪
2. **test-strategy**: 测试策略生成
3. **security-scan**: 安全检查

## 依赖

- Phase 1 的共享规则文件 `docs/RULES-CODE-QUALITY.md`
- Phase 1 的规则查询脚本 `scripts/rule_query.py`

## 设计原则

- 与 review/postmortem 形成闭环
- 复用共享规则进行检查
- 输出结构化报告便于 AI 检索
