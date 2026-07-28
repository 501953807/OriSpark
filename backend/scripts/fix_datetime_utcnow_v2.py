#!/usr/bin/env python3
"""批量修复 datetime.utcnow() 为 timezone-aware 的 datetime.now(timezone.utc)

安全、可逆地替换所有 utcnow 调用，同时添加必要的 timezone 导入。
"""

import os
import re
from pathlib import Path

BACKEND_DIR = Path("/Users/tangxiaochuan/AIWorkspace/ClaudeWorkspace/OriSpark/backend")
APP_DIR = BACKEND_DIR / "app"


def has_datetime_timezone_import(content):
    """检查是否已有 from datetime import ... timezone 或 import datetime + timezone 引入"""
    if re.search(r'from\s+datetime\s+import\s+\w*\,\s*timezone\b', content):
        return True
    if re.search(r'import\s+datetime\s+.*\s+timezone', content):
        return True
    # 检查是否有 'import datetime' 且文件中后续使用了 datetime.timezone
    if 'import datetime' in content and 'datetime.timezone' in content:
        return True
    return False


def ensure_datetime_timezone_import(content, filepath):
    """确保文件中包含了 datetime 和 timezine 的导入"""
    lines = content.splitlines(keepends=True)

    # 检查是否已有 from datetime import ... timezone
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("from datetime import"):
            # 检查是否已包含 timezone
            if "timezone" not in line:
                # 在现有导入中添加 timezone
                parts = stripped.split("from datetime import ", 1)
                if len(parts) == 2:
                    imports = [imp.strip() for imp in parts[1].split(",")]
                    if "timezone" not in imports:
                        imports.append("timezone")
                        new_line = f"from datetime import {', '.join(imports)}\n"
                        lines[i] = new_line
                        print(f"   ➕ 已追加 timezone 到 {filepath}")
                        return "".join(lines)
            return content

    # 检查是否有单纯 import datetime
    for i, line in enumerate(lines):
        if line.strip().startswith("import datetime"):
            # 需要额外 import timezone
            lines.insert(i + 1, "from datetime import timezone\n")
            print(f"   ➕ 已添加 from datetime import timezone 到 {filepath}")
            return "".join(lines)

    # 如果没有 datetime 导入，插入到文件顶部附近
    insert_pos = 0
    for i, line in enumerate(lines):
        if line.strip() and not line.strip().startswith("#"):
            insert_pos = i
            break
    lines.insert(insert_pos, "from datetime import datetime, timezone\n")
    print(f"   ➕ 已在 {filepath} 添加 from datetime import datetime, timezone")
    return "".join(lines)


def replace_datetime_utcnow_in_line(line):
    """对一行内的 datetime.utcnow() 进行安全替换"""
    def replacer(match):
        full_match = match.group(0)
        # 捕获后面可能跟的点号和方法
        # 使用简单替换：datetime.utcnow() -> datetime.now(timezone.utc)
        # 这已经足够安全，因为 utcnow() 总是带括号
        return "datetime.now(timezone.utc)"

    # 使用正则匹配完整的 datetime.utcnow() 调用
    # 模式：datetime\.utcnow()，但单词边界保证不匹配其他内容
    return re.sub(r'\bdatetime\.utcnow\(\)', 'datetime.now(timezone.utc)', line)


def fix_file(filepath):
    """修复单个文件，返回 (是否修改，行数变化)"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            original_content = f.read()
    except Exception as e:
        print(f"⚠️ 读取失败 {filepath}: {e}")
        return False, 0

    content = original_content

    # 步骤 1: 确保有正确的导入
    if not has_datetime_timezone_import(content):
        content = ensure_datetime_timezone_import(content, filepath)

    # 步骤 2: 处理 __import__('datetime').datetime.utcnow() 的特殊情况
    # 这种写法通常出现在 supply.py，需要先转换为标准形式再替换
    dynamic_pattern = r"__import__\(['\"]datetime[']\)\.datetime\.utcnow\(\)"
    # 先检测是否存在动态导入的 utcnow
    if re.search(dynamic_pattern, content):
        # 将这种写法替换为直接使用 datetime.utcnow()（因为后续有标准导入）
        # 然后步骤 2 会统一替换为 timezone-aware
        # 实际上更简单的做法：直接替换整个表达式
        content = re.sub(dynamic_pattern, 'datetime.utcnow()', content)
        # 由于已经添加了导入，步骤 3 的 regex 会自动把它变成 timezone-aware

    # 步骤 3: 逐行替换所有 datetime.utcnow()
    lines = content.splitlines(keepends=True)
    modified_lines = False
    for i in range(len(lines)):
        old_line = lines[i]
        new_line = replace_datetime_utcnow_in_line(old_line)
        if new_line != old_line:
            lines[i] = new_line
            modified_lines = True

    if modified_lines:
        new_content = "".join(lines)
        if new_content != original_content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"✅ {filepath.relative_to(BACKEND_DIR)}: 已修复")
            return True, sum(1 for a, b in zip(original_content.splitlines(), new_content.splitlines()) if a != b)

    return False, 0


def main():
    print("=" * 60)
    print("批量修复 datetime.utcnow() → datetime.now(timezone.utc)")
    print("=" * 60)

    # 扫描所有 Python 文件（跳过测试目录和 alembic）
    files_to_fix = []
    for root, dirs, files in os.walk(APP_DIR):
        # 跳过 test 相关目录
        dirs[:] = [d for d in dirs if "test" not in d.lower()]
        if "alembic" in root.lower():
            continue

        for f in files:
            if f.endswith(".py"):
                filepath = Path(root) / f
                files_to_fix.append(filepath)

    print(f"\n🔍 检查 {len(files_to_fix)} 个 Python 文件...")

    fixes_made = 0
    total_changes = 0

    for filepath in sorted(files_to_fix):
        # 快速检查是否包含需要修复的内容
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            if "datetime.utcnow()" not in content:
                continue
        except Exception as e:
            print(f"⚠️ 无法读取 {filepath}: {e}")
            continue

        print(f"🔎 检测到 {filepath.relative_to(BACKEND_DIR)} 包含 datetime.utcnow()")

        made_changes, line_changes = fix_file(filepath)
        if made_changes:
            fixes_made += 1
            total_changes += line_changes
        else:
            print(f"   ⚠️ 但无实际变化（可能是重复修复或格式特殊）")

    print("\n" + "=" * 60)
    print(f"📊 修复完成: {fixes_made} 个文件, {total_changes} 处更改")
    print("=" * 60)

    return fixes_made


if __name__ == "__main__":
    main()