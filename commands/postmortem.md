---
description: "分析 bug/fix 提交，生成事故复盘报告"
argument-hint: "[jira-id | --select]"
---

执行 postmortem skill 进行事故复盘分析。

参数说明：
- 无参数: 自动扫描 git 历史中的 bug/fix 相关提交
- --select: 手动从最近的 commit 列表中选择
- <jira-id>: 通过 Jira ID 获取关联 commit 进行分析

报告输出到 `.claude/postmortem/<yymmdd-issue-short-description>/` 目录。

请调用 postmortem skill 来处理用户请求。
