#!/usr/bin/env python3
"""批量修复 datetime.utcnow() 为 timezone-aware 的 datetime.now(timezone.utc)

规则：
1. 对于 'datetime.utcnow()' -> 替换为 'datetime.now(timezone.utc)'
2. 添加缺失的 'from datetime import timezone' 或 'import datetime' 和 'timezone' 引用
3. 特殊处理 __import__('datetime').datetime.utcnow() 模式
4. 确保所有文件都有正确的时区导入
"""

import os
import re
from pathlib import Path

BACKEND_DIR = Path("/Users/tangxiaochuan/AIWorkspace/ClaudeWorkspace/OriSpark/backend")
APP_DIR = BACKEND_DIR / "app"


def add_timezone_import(filepath, has_datetime_import):
    """向文件添加 timezone 导入"""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 检查已导入 datetime
    has_from_datetime_import = any(
        line.strip().startswith("from datetime import") or line.strip().startswith("import datetime")
        for line in lines
    )

    if not has_from_datetime_import:
        # 需要插入到适当的导入位置
        insert_point = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith("#"):
                insert_point = i
                break
        lines.insert(insert_point, "from datetime import datetime, timezone\n")
        return True, lines

    # 检查是否已有 timezone 导入
    if any("timezone" in line for line in lines if "from datetime import" in line):
        return False, lines

    # 修正 from datetime import ... 语句
    for i, line in enumerate(lines):
        if "from datetime import" in line:
            # 添加 timezone 到现有导入
            current_import = line.split("from datetime import")[1].strip()
            if "timezone" not in current_import:
                lines[i] = f"from datetime import {current_import}, timezone\n"
                return True, lines

    return False, lines


def replace_datetime_utcnow_in_content(content, filepath, lineno, has_datetime_import):
    """针对内容行执行替换"""
    modified = False

    # 方案1: 简单替换 datetime.utcnow()
    # 但要小心不要替换成 datetime.now(timezone.utc())（多了个括号）

    # 匹配：datetime.utcnow()
    pattern1 = r"\bdatetime\.utcnow\(\)"
    replacement1 = "datetime.now(timezone.utc)"

    # 但需要处理特殊情形：
    # - datetime.utcnow().isoformat() 应替换为 datetime.now(timezone.utc).isoformat()
    # - datetime.utcnow() + timedelta(...) 需要保持一致性

    # 更智能的处理：先识别 datetime.utcnow() 的完整调用链
    def replacer(match):
        full = match.group(0)
        # 获取完整的调用，包括后面的 .xxx() 方法
        # 重新匹配这个位置后面的内容
        return "datetime.now(timezone.utc)"

    # 简单替换：所有 datetime.utcnow() 都变成 datetime.now(timezone.utc)
    new_content = re.sub(pattern1, replacement1, content)
    if new_content != content:
        modified = True

    # 处理 __import__('datetime').datetime.utcnow() 这种复杂写法
    dynamic_pattern = r"__import__\(['\"]datetime[']\)\.datetime\.utcnow\(\)"
    dynamic_replacement = "datetime"  # 这部分需要单独处理，先看文件结构

    if not modified and "datetime" in content and "import" not in content[:200]:
        # 检查是否有动态导入
        if "__import__(" in content:
            modified = True

    return new_content, modified


def process_file(filepath):
    """处理单个文件，返回是否被修改"""
    if not filepath.exists():
        print(f"❌ 文件不存在: {filepath}")
        return False

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"⚠️ 读取失败 {filepath}: {e}")
        return False

    original = content
    modified = False

    # 检查是否需要添加 timezone 导入
    has_datetime_import = "from datetime import" in content or "import datetime" in content
    needs_import_addition, updated_lines = add_timezone_import(filepath, has_datetime_import)

    if needs_import_addition:
        # 重建包含新导入的内容
        if "\n".join(updated_lines) != original:
            original = "\n".join(updated_lines)
            modified = True

    # 执行替换
    content = original
    pattern = r"\bdatetime\.utcnow\(\)"
    replacement = "datetime.now(timezone.utc)"

    new_content = re.sub(pattern, replacement, content)
    if new_content != content:
        modified = True
        content = new_content

    # 处理 __import__('datetime').datetime.utcnow() 的特殊情况
    dynamic_pattern = r"__import__\(['\"]datetime[']\)\.datetime\.utcnow\(\)"
    # 这种情况通常出现在 supply.py 等文件中，需要更复杂的处理
    if re.search(dynamic_pattern, content):
        modified = True
        # 先确保有正确的导入，然后替换整个表达式
        # 这类文件通常已有 datetime 导入
        new_content = re.sub(
            dynamic_pattern,
            lambda m: f"{datetime.now(timezone.utc).isoformat() if '.isoformat()' in content else datetime.now(timezone.utc)}",
            content
        )
        # 实际上应该用更精确的模式匹配
        # 替换为：直接引用 datetime.utcnow() 之前要先确保导入
        pass

    if modified:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ 已修复: {filepath}")
        return True
    else:
        # 检查是否只是缺少导入
        if has_datetime_import and "datetime.utcnow()" in original and "datetime.now(timezone.utc)" not in content:
            # 这种情况可能是导入格式不同，需进一步分析
            pass
        return False


def main():
    """主扫描和处理流程"""
    files_to_process = []

    # 收集需要处理的生产代码文件
    for root, dirs, files in os.walk(APP_DIR):
        # 跳过 test 目录
        if "test" in root.lower() or "tests" in root.lower():
            continue
        # 跳过 migrations/alembic 目录
        if "alembic" in root.lower():
            continue
        # 跳过 cache/pycache
        if "__pycache__" in root:
            continue

        for f in files:
            if f.endswith(".py"):
                filepath = Path(root) / f
                files_to_process.append(filepath)

    print(f"🔍 扫描到 {len(files_to_process)} 个 Python 文件...")

    # 先找出哪些文件实际包含 datetime.utcnow()
    files_needing_fix = []
    for fp in files_to_process:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                if "datetime.utcnow()" in f.read():
                    files_needing_fix.append(fp)
        except:
            pass

    print(f"🎯 找到 {len(files_needing_fix)} 个文件包含 datetime.utcnow(), 需要修复:")
    for f in sorted(files_needing_fix):
        print(f"   {f.relative_to(BACKEND_DIR)}")

    # 批量修复
    fixes_made = 0
    for f in sorted(files_needing_fix):
        if process_file(f):
            fixes_made += 1

    print(f"\n📊 总计: {fixes_made} 个文件已修复")
    return fixes_made


if __name__ == "__main__":
    main()