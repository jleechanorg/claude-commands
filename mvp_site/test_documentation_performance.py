#!/usr/bin/env python3
"""
Documentation Performance Test
Tests documentation file sizes to prevent API timeouts

This script checks documentation files against size thresholds and provides
detailed reporting for files that may cause performance issues.

Usage: python3 mvp_site/test_documentation_performance.py
"""

import os
import sys

# Define thresholds (keep in sync with monitor_doc_sizes.sh)
MAX_LINES = 1500
WARNING_LINES = 1000


def get_file_size_info(filepath):
    """Get detailed size information for a file"""
    if not os.path.exists(filepath):
        return {
            "exists": False,
            "lines": 0,
            "chars": 0,
            "size_kb": 0,
            "status": "not_found",
        }

    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
            lines = len(content.splitlines())
            chars = len(content)
            size_kb = os.path.getsize(filepath) / 1024

            if lines > MAX_LINES:
                status = "exceeds_limit"
            elif lines > WARNING_LINES:
                status = "warning"
            else:
                status = "ok"

            return {
                "exists": True,
                "lines": lines,
                "chars": chars,
                "size_kb": size_kb,
                "status": status,
            }
    except Exception as e:
        return {
            "exists": True,
            "lines": 0,
            "chars": 0,
            "size_kb": 0,
            "status": "error",
            "error": str(e),
        }


def check_documentation_files():
    """Check all documentation files for size issues"""

    # List of files to check (keep in sync with monitor_doc_sizes.sh)
    files_to_check = [
        ".cursor/rules/rules.mdc",
        ".cursor/rules/lessons.mdc",
        ".cursor/rules/project_overview.md",
        ".cursor/rules/planning_protocols.md",
        ".cursor/rules/documentation_map.md",
        ".cursor/rules/quick_reference.md",
        ".cursor/rules/progress_tracking.md",
        "CLAUDE.md",
    ]

    print("📊 Documentation Performance Analysis")
    print("=" * 50)
    print(f"Thresholds: Warning={WARNING_LINES} lines, Max={MAX_LINES} lines")
    print()

    results = {}
    total_issues = 0

    for filepath in files_to_check:
        info = get_file_size_info(filepath)
        results[filepath] = info

        if not info["exists"]:
            print(f"⏭️  {filepath}: not found")
            continue

        if info["status"] == "error":
            print(f"❌ {filepath}: error reading file - {info.get('error', 'unknown')}")
            total_issues += 1
            continue

        status_icon = {"ok": "✅", "warning": "⚠️ ", "exceeds_limit": "❌"}.get(
            info["status"], "❓"
        )

        print(
            f"{status_icon} {filepath}: {info['lines']} lines, {info['chars']} chars, {info['size_kb']:.1f}KB"
        )

        if info["status"] in ["warning", "exceeds_limit"]:
            if info["status"] == "exceeds_limit":
                total_issues += 1
                print("   ⚡ CRITICAL: File may cause API timeouts")
            else:
                print("   ⚠️  Consider reducing size for better performance")

    print()
    print("=" * 50)

    if total_issues > 0:
        print(f"❌ FAILED: {total_issues} file(s) exceed size limits")
        print()
        print("🔧 Recommendations:")
        for filepath, info in results.items():
            if info["status"] == "exceeds_limit":
                reduction_needed = info["lines"] - MAX_LINES
                print(f"   • {filepath}: Reduce by ~{reduction_needed} lines")
        print()
        print("💡 Consider:")
        print("   • Move detailed examples to separate files")
        print("   • Archive old lessons to lessons_archive_YYYY.mdc")
        print("   • Break large sections into focused files")
        print("   • Use references instead of inline documentation")

        return False

    print("✅ SUCCESS: All documentation files within acceptable limits")
    return True


def main():
    """Main execution function"""
    success = check_documentation_files()

    if not success:
        print()
        print("Run this script regularly to monitor documentation size")
        print("Large files can cause API timeouts and performance issues")
        sys.exit(1)
    else:
        print()
        print("Documentation performance is optimal!")
        sys.exit(0)


if __name__ == "__main__":
    main()
