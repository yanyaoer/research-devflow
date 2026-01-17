#!/usr/bin/env python3
"""
规则查询脚本 - 查询代码质量检查规则

用法:
    python rule_query.py --query review
    python rule_query.py --query postmortem --category security
    python rule_query.py --query review --format json
    python rule_query.py --query review --format markdown

默认加载规则文件:
    - docs/RULES-*.md (框架内置规则)
    - <project-root>/.claude/docs/RULES-*.md (项目自定义规则，可选)
"""

import argparse
import glob
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Optional


def get_project_root() -> Optional[Path]:
    """获取项目根目录 (通过 git 或当前工作目录)"""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True, text=True, check=True
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path.cwd()


def discover_rules_files(script_dir: Path) -> List[Path]:
    """发现所有可用的规则文件"""
    files = []

    # 1. 框架内置规则: docs/RULES-*.md
    framework_docs = script_dir.parent / 'docs'
    if framework_docs.exists():
        for f in framework_docs.glob('RULES-*.md'):
            files.append(f)

    # 2. 项目自定义规则: <project-root>/.claude/docs/RULES-*.md
    project_root = get_project_root()
    if project_root:
        project_rules_dir = project_root / '.claude' / 'docs'
        if project_rules_dir.exists():
            for f in project_rules_dir.glob('RULES-*.md'):
                files.append(f)

    return files


def parse_rules_file(file_path: str) -> List[Dict]:
    """解析规则文件，提取所有规则"""
    rules = []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 匹配 YAML 格式的规则块
    # 规则格式: - id: XXX ... 直到下一个 - id: 或 --- 或文件结束
    # 只匹配真实规则 ID (S01, R01, P01, M01 等格式)
    pattern = r'- id:\s*([A-Z]\d+)\s*\n(.*?)(?=\n- id:|\n---|\Z)'
    matches = re.findall(pattern, content, re.DOTALL)

    for rule_id, rule_body in matches:
        rule = {'id': rule_id}

        # 解析各字段
        field_patterns = {
            'name': r'name:\s*(.+?)(?:\n|$)',
            'category': r'category:\s*(\S+)',
            'severity': r'severity:\s*(\S+)',
            'review_action': r'review_action:\s*(.+?)(?:\n\s{2}\S|\n-|\Z)',
            'postmortem_action': r'postmortem_action:\s*(.+?)(?:\n\s{2}\S|\n-|\Z)',
            'fix_hint': r'fix_hint:\s*(.+?)(?:\n\s{2}\S|\n-|\Z)',
        }

        for field, pat in field_patterns.items():
            match = re.search(pat, rule_body, re.DOTALL)
            if match:
                rule[field] = match.group(1).strip()

        # 解析 applies_to 列表
        applies_match = re.search(r'applies_to:\s*\[([^\]]+)\]', rule_body)
        if applies_match:
            rule['applies_to'] = [s.strip() for s in applies_match.group(1).split(',')]

        # 解析 check_command (可能是多行)
        cmd_match = re.search(r'check_command:\s*\|?\s*\n((?:\s{4}.+\n?)+)', rule_body)
        if cmd_match:
            commands = cmd_match.group(1).strip()
            rule['check_command'] = '\n'.join(line.strip() for line in commands.split('\n') if line.strip())

        rules.append(rule)

    return rules


def filter_rules(rules: List[Dict], scenario: str, category: Optional[str] = None) -> List[Dict]:
    """按场景和分类过滤规则"""
    filtered = []

    for rule in rules:
        # 检查场景匹配
        applies_to = rule.get('applies_to', [])
        if scenario not in applies_to:
            continue

        # 检查分类匹配
        if category and rule.get('category') != category:
            continue

        filtered.append(rule)

    return filtered


def format_table(rules: List[Dict], scenario: str) -> str:
    """表格格式输出"""
    if not rules:
        return f"No rules found for scenario: {scenario}"

    # 表头
    action_field = 'review_action' if scenario == 'review' else 'postmortem_action'
    lines = [
        f"{'ID':<6} | {'Name':<20} | {'Category':<15} | {'Severity':<10} | Action",
        f"{'-'*6} | {'-'*20} | {'-'*15} | {'-'*10} | {'-'*30}"
    ]

    for rule in rules:
        action = rule.get(action_field, 'N/A')
        if len(action) > 30:
            action = action[:27] + '...'
        lines.append(
            f"{rule['id']:<6} | {rule.get('name', ''):<20} | {rule.get('category', ''):<15} | {rule.get('severity', ''):<10} | {action}"
        )

    return '\n'.join(lines)


def format_json(rules: List[Dict], scenario: str) -> str:
    """JSON 格式输出"""
    output = {
        'scenario': scenario,
        'count': len(rules),
        'rules': rules
    }
    return json.dumps(output, ensure_ascii=False, indent=2)


def format_markdown(rules: List[Dict], scenario: str) -> str:
    """Markdown 格式输出 (适合作为 checklist)"""
    if not rules:
        return f"No rules found for scenario: {scenario}"

    action_field = 'review_action' if scenario == 'review' else 'postmortem_action'

    lines = [f"## {scenario.title()} 检查规则", ""]

    # 按分类分组
    categories = {}
    for rule in rules:
        cat = rule.get('category', 'other')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(rule)

    for cat, cat_rules in categories.items():
        lines.append(f"### {cat}")
        lines.append("")
        for rule in cat_rules:
            action = rule.get(action_field, 'N/A')
            lines.append(f"- [ ] **{rule['id']}**: {rule.get('name', '')} - {action}")
        lines.append("")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='查询代码质量规则',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  %(prog)s --query review                    # 查询 review 场景规则 (加载所有规则文件)
  %(prog)s --query postmortem --category security  # 查询安全类规则
  %(prog)s --query review --format json      # JSON 格式输出
  %(prog)s --query review --format markdown  # Markdown checklist 输出
  %(prog)s -r docs/RULES-ANDROID.md --query review  # 仅加载指定规则文件

默认加载:
  - docs/RULES-*.md (框架内置规则)
  - <project-root>/.claude/docs/RULES-*.md (项目自定义规则，可选)
'''
    )

    parser.add_argument(
        '--query', '-q',
        required=True,
        choices=['review', 'postmortem', 'refactor', 'research'],
        help='查询场景'
    )

    parser.add_argument(
        '--category', '-c',
        choices=['security', 'robustness', 'performance', 'maintainability'],
        help='规则分类过滤'
    )

    parser.add_argument(
        '--format', '-f',
        default='table',
        choices=['table', 'json', 'markdown'],
        help='输出格式 (default: table)'
    )

    parser.add_argument(
        '--rules-file', '-r',
        action='append',
        dest='rules_files',
        help='规则文件路径，可多次指定。未指定时自动发现所有规则文件'
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    all_rules = []

    if args.rules_files:
        # 用户指定了规则文件
        for rf in args.rules_files:
            rules_file = Path(rf)
            if not rules_file.exists():
                # 尝试从脚本所在目录的上级查找
                rules_file = script_dir.parent / rf
            if not rules_file.exists():
                print(f"Error: Rules file not found: {rf}", file=sys.stderr)
                sys.exit(1)
            all_rules.extend(parse_rules_file(str(rules_file)))
    else:
        # 自动发现所有规则文件
        discovered = discover_rules_files(script_dir)
        if not discovered:
            print("Error: No rules files found", file=sys.stderr)
            sys.exit(1)
        for rules_file in discovered:
            all_rules.extend(parse_rules_file(str(rules_file)))

    # 过滤规则
    filtered = filter_rules(all_rules, args.query, args.category)

    # 格式化输出
    if args.format == 'table':
        print(format_table(filtered, args.query))
    elif args.format == 'json':
        print(format_json(filtered, args.query))
    elif args.format == 'markdown':
        print(format_markdown(filtered, args.query))


if __name__ == '__main__':
    main()
