# P1: 创建 rule_query.py 查询脚本

## 任务目标

创建规则查询脚本，封装规则检索逻辑，输出指定场景的规则集合。

## 依赖任务

- P0: 创建共享规则文件

## 实现步骤

### Step 1: 创建脚本

**文件**: `scripts/rule_query.py`

```python
#!/usr/bin/env python3
"""
规则查询脚本
用法:
    python rule_query.py --query review
    python rule_query.py --query postmortem --category security
    python rule_query.py --query review --format json
"""

import argparse
import yaml
import json
import sys
from pathlib import Path

def load_rules(rules_file):
    """加载规则文件"""
    pass

def filter_rules(rules, scenario, category=None):
    """按场景和分类过滤规则"""
    pass

def format_output(rules, format_type):
    """格式化输出"""
    pass

def main():
    parser = argparse.ArgumentParser(description='查询代码质量规则')
    parser.add_argument('--query', required=True,
                        choices=['review', 'postmortem', 'refactor', 'research'],
                        help='查询场景')
    parser.add_argument('--category',
                        choices=['security', 'robustness', 'performance', 'maintainability'],
                        help='规则分类')
    parser.add_argument('--format', default='table',
                        choices=['table', 'json', 'markdown'],
                        help='输出格式')
    parser.add_argument('--rules-file', default='docs/RULES-CODE-QUALITY.md',
                        help='规则文件路径')

    args = parser.parse_args()
    # 实现查询逻辑
```

### Step 2: 实现核心功能

1. 解析 markdown 中的 YAML frontmatter 和规则列表
2. 按 applies_to 过滤
3. 支持多种输出格式

### 输出示例

**table 格式**:
```
ID    | Name         | Category   | Severity | Action
------|--------------|------------|----------|--------
S01   | SQL 注入     | security   | critical | 检查参数化查询
R01   | 空值处理     | robustness | high     | 检查 null check
```

**json 格式**:
```json
{
  "scenario": "review",
  "rules": [
    {"id": "S01", "name": "SQL 注入", ...}
  ]
}
```

**markdown 格式**:
```markdown
## Review 检查规则

### security
- [ ] S01: SQL 注入 - 检查参数化查询
```

## 涉及文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `scripts/rule_query.py` | 新建 | 规则查询脚本 |

## 验证方法

```bash
# 基本查询
python scripts/rule_query.py --query review
python scripts/rule_query.py --query postmortem

# 分类过滤
python scripts/rule_query.py --query review --category security

# JSON 输出
python scripts/rule_query.py --query review --format json | jq .
```

## 完成标准

- [ ] 创建 rule_query.py
- [ ] 支持 --query 参数
- [ ] 支持 --category 过滤
- [ ] 支持 table/json/markdown 输出格式
- [ ] 更新 task-status.json
