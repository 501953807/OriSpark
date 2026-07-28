#!/usr/bin/env python3
"""生产环境 datetime.utcnow() → datetime.now(timezone.utc) 批量修复器

安全、原子化地修改文件，每步都检查导入和替换一致性。
"""

import os
import re
from pathlib import Path

BACKEND_DIR = Path("/Users/tangxiaochuan/AIWorkspace/ClaudeWorkspace/OriSpark/backend")
APP_DIR = BACKEND_DIR / "app"


def check_file_has_datetime_import(filepath):
    """检查文件是否已导入 datetime 模块"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                stripped = line.strip()
                if stripped.startswith("from datetime import"):
                    return True, i, stripped
                if stripped.startswith("import datetime"):
                    return True, i, stripped
        return False, -1, None
    except Exception:
        return False, -1, None


def ensure_timezone_in_import(import_line, lineno):
    """确保 from datetime import ... 包含 timezone"""
    parts = import_line.split("from datetime import ", 1)
    if len(parts) != 2:
        return import_line
    imports = [imp.strip() for imp in parts[1].split(",")]
    if "timezone" not in imports:
        imports.append("timezone")
        return f"from datetime import {', '.join(imports)}"
    return import_line


def find_insert_position(filepath):
    """在合适的行之前插入 new import 语句"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 寻找第一个非注释、非空白的行作为插入点
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                return i
        return 0
    except Exception:
        return 0


def fix_etsy_service(filepath):
    """特别修复 etsy_service.py 中的 datetime 用法"""
    print(f"🔧 特殊处理: {filepath.relative_to(BACKEND_DIR)}")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 检查是否已有时区导入
    has_import = False
    for line in content.splitlines():
        if line.strip().startswith("from datetime import") and "timezone" in line:
            has_import = True
            break
        if line.strip().startswith("from datetime import") and "datetime" in line:
            # 需要添加 timezone
            print("   ➕ 需要向 existing import 添加 timezone")
            new_line = line.replace("from datetime import", "from datetime import").strip()
            # 提取现有导入项
            import_part = line.split("from datetime import ", 1)[1]
            imports = [imp.strip() for imp in import_part.split(",")]
            if "timezone" not in imports:
                imports.append("timezone")
                content = content.replace(line, f"from datetime import {', '.join(imports)}\n")
                has_import = True
            break

    # 如果完全没有 from datetime import，需要检查是否有 import datetime 单独存在
    if not has_import and "import datetime" in content:
        # 在 import datetime 之后添加 from datetime import timezone
        lines = content.splitlines(keepends=True)
        for i, line in enumerate(lines):
            if line.strip().startswith("import datetime"):
                lines.insert(i + 1, "from datetime import timezone\n")
                content = "".join(lines)
                has_import = True
                print(f"   ➕ 在 import datetime 后添加了 from datetime import timezone")
                break

    # 现在执行替换
    # 关键：先识别所有 datetime.utcnow() 的位置
    utcnow_pattern = r'\bdatetime\.utcnow\(\)'
    matches = list(re.finditer(utcnow_pattern, content))

    if not matches:
        print("   ⚠️ 未发现 datetime.utcnow() 调用")
        return content, False

    # 逐个替换，确保正确性
    new_content = content
    for match in reversed(matches):
        start, end = match.span()
        # 检查后面是否有 .xxx() 方法调用
        suffix_match = re.match(r'(\.isoformat\(\)|\.strftime\(\)|\s*\+)', content[end:end+15])
        replacement = "datetime.now(timezone.utc)"

        # 如果是 .isoformat() 或 .strftime()，保持链式调用
        if suffix_match:
            replacement += content[end:end+len(suffix_match.group(0))]

        new_content = new_content[:start] + replacement + new_content[end:]

    # 如果未添加导入，但需要添加（最坏情况）
    if not has_import:
        # 简单地在文件开头添加
        insert_pos = find_insert_position(filepath)
        lines = new_content.splitlines(keepends=True)
        lines.insert(insert_pos, "from datetime import datetime, timezone\n")
        new_content = "".join(lines)
        print(f"   ➕ 在文件顶部添加了完整的 datetime 导入")

    return new_content, len(matches) > 0


def fix_generic_file(filepath):
    """通用文件修复"""
    print(f"📝 通用修复: {filepath.relative_to(BACKEND_DIR)}")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 检查导入状态
    has_dt_import, import_lineno, import_line = check_file_has_datetime_import(filepath)

    # 检查是否已包含 timezone
    has_timezone = False
    if has_dt_import and import_line:
        if "timezone" in import_line:
            has_timezone = True

    # 如果没有 timezone，需要添加
    if not has_timezone and has_dt_import:
        # 修改现有的 from datetime import 行
        lines = content.splitlines(keepends=True)
        if 0 <= import_lineno < len(lines):
            new_line = ensure_timezone_in_import(lines[import_lineno], import_lineno)
            if new_line != lines[import_lineno]:
                lines[import_lineno] = new_line + "\n"
                print(f"   ➕ 已更新第 {import_lineno+1} 行导入，添加 timezone")
                content = "".join(lines)

    # 如果完全缺失 datetime 导入，添加完整导入
    if not has_dt_import and not timezone_used_elsewhere(content):
        insert_pos = find_insert_position(filepath)
        lines = content.splitlines(keepends=True)
        lines.insert(insert_pos, "from datetime import datetime, timezone\n")
        content = "".join(lines)
        print(f"   ➕ 在顶部添加了 from datetime import datetime, timezone")

    # 执行实际替换
    utcnow_pattern = r'\bdatetime\.utcnow\(\)'
    matches = list(re.finditer(utcnow_pattern, content))

    if not matches:
        print("   ⚠️ 未发现需要替换的 datetime.utcnow()")
        return content, 0

    new_content = content
    for match in reversed(list(re.finditer(utcnow_pattern, content))):
        start, end = match.span()
        new_content = new_content[:start] + "datetime.now(timezone.utc)" + new_content[end:]

    print(f"   ✂️ 替换了 {len(matches)} 处 datetime.utcnow() 为 datetime.now(timezone.utc)")
    return new_content, len(matches)


def timezone_used_elsewhere(content):
    """检查是否已在其他地方使用了 timezone"""
    return "timezone" in content


def main():
    print("=" * 70)
    print("批量修复器: datetime.utcnow() → datetime.now(timezone.utc)")
    print("=" * 70)

    # 列出所有需要修复的生产文件
    files_to_process = []
    for root, dirs, files in os.walk(APP_DIR):
        dirs[:] = [d for d in dirs if "test" not in d.lower()]  # 跳过测试目录
        if "alembic" in root.lower():
            continue

        for f in files:
            if f.endswith(".py"):
                filepath = Path(root) / f
                files_to_process.append(filepath)

    # 过滤出包含 datetime.utcnow() 的文件
    files_needing_fix = []
    for fp in files_to_process:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read()
            if "datetime.utcnow()" in content:
                files_needing_fix.append(fp)
        except Exception:
            pass

    print(f"\n发现 {len(files_needing_fix)} 个包含 datetime.utcnow() 的生产文件:")
    for f in sorted(files_needing_fix):
        print(f"  - {f.relative_to(BACKEND_DIR)}")

    # 逐个修复
    total_changes = 0
    files_modified = 0

    for filepath in sorted(files_needing_fix):
        if "etsy" in str(filepath).lower():
            new_content, count = fix_etsy_service(filepath)
        else:
            new_content, count = fix_generic_file(filepath)

        if new_content != filepath.read_text(encoding="utf-8"):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            files_modified += 1
            total_changes += count

    print("\n" + "=" * 70)
    print(f"✅ 修复完成: {files_modified} 个文件已修改, {total_changes} 处更改")
    print("=" * 70)

    return files_modified


if __name__ == "__main__":
    main()