#!/usr/bin/env python3
"""
Test documentation file sizes and performance to prevent API timeouts.
"""

import os
import sys
import time

# Configuration
MAX_FILE_SIZE_LINES = 1500  # Maximum recommended lines for reliable API reading
WARNING_FILE_SIZE_LINES = 1000  # Warning threshold
OPTIMAL_FILE_SIZE_LINES = 700  # Optimal size for fast reads
MAX_READ_TIME_SECONDS = 2.0  # Maximum time to read a file

# Files to test (excluding archives folder)
DOCUMENTATION_FILES = [
    ".cursor/rules/rules.mdc",
    ".cursor/rules/lessons.mdc",
    ".cursor/rules/project_overview.md",
    ".cursor/rules/planning_protocols.md",
    ".cursor/rules/documentation_map.md",
    ".cursor/rules/quick_reference.md",
    ".cursor/rules/progress_tracking.md",
    "CLAUDE.md",
]


def get_project_root():
    """Get the project root directory."""
    current = os.path.dirname(os.path.abspath(__file__))
    while current != "/":
        if os.path.exists(os.path.join(current, ".cursor")):
            return current
        current = os.path.dirname(current)
    return None


def test_file_size(filepath):
    """Test if a file is within acceptable size limits."""
    try:
        with open(filepath, encoding="utf-8") as f:
            lines = f.readlines()
            line_count = len(lines)
            char_count = sum(len(line) for line in lines)

        status = "✅ OK"
        if line_count > MAX_FILE_SIZE_LINES:
            status = "❌ TOO LARGE"
        elif line_count > WARNING_FILE_SIZE_LINES:
            status = "⚠️  WARNING"
        elif line_count <= OPTIMAL_FILE_SIZE_LINES:
            status = "✨ OPTIMAL"

        return {
            "file": filepath,
            "lines": line_count,
            "chars": char_count,
            "status": status,
            "needs_reduction": line_count > MAX_FILE_SIZE_LINES,
        }
    except FileNotFoundError:
        return {
            "file": filepath,
            "lines": 0,
            "chars": 0,
            "status": "⏭️  NOT FOUND",
            "needs_reduction": False,
        }


def test_read_performance(filepath):
    """Test how long it takes to read a file."""
    if not os.path.exists(filepath):
        return None

    start_time = time.time()
    try:
        with open(filepath, encoding="utf-8") as f:
            f.read()
    except Exception:
        return None

    return time.time() - start_time


def simulate_api_read(filepath, chunk_lines=2000):
    """Simulate API-style chunked reading.

    Args:
        filepath: Path to the file to read
        chunk_lines: Number of lines per chunk (default: 2000)

    Returns:
        List of chunk information dictionaries
    """
    if not os.path.exists(filepath):
        return []

    chunks = []
    try:
        with open(filepath, encoding="utf-8") as f:
            lines = f.readlines()

        # Simulate reading in chunks
        for i in range(0, len(lines), chunk_lines):
            chunk = lines[i : i + chunk_lines]
            chunks.append(
                {
                    "start_line": i + 1,
                    "end_line": min(i + chunk_lines, len(lines)),
                    "size": len("".join(chunk)),
                }
            )
    except (OSError, FileNotFoundError) as e:
        print(f"⚠️  Warning: Could not read file for chunking: {e}")

    return chunks


def main():
    """Run all documentation performance tests."""
    project_root = get_project_root()
    if not project_root:
        print("❌ Could not find project root")
        return 1

    print("📊 Documentation Performance Test Report")
    print("=" * 80)
    print(f"Project root: {project_root}")
    print(f"Maximum recommended size: {MAX_FILE_SIZE_LINES} lines")
    print(f"Warning threshold: {WARNING_FILE_SIZE_LINES} lines")
    print(f"Optimal size: {OPTIMAL_FILE_SIZE_LINES} lines")
    print()

    # Test file sizes
    print("📏 File Size Analysis:")
    print("-" * 80)
    print(f"{'File':<50} {'Lines':>8} {'Chars':>10} {'Status':<15}")
    print("-" * 80)

    results = []
    total_lines = 0
    problematic_files = []

    for doc_file in DOCUMENTATION_FILES:
        filepath = os.path.join(project_root, doc_file)
        result = test_file_size(filepath)
        results.append(result)

        if result["lines"] > 0:
            total_lines += result["lines"]

        if result["needs_reduction"]:
            problematic_files.append(result)

        print(
            f"{doc_file:<50} {result['lines']:>8} {result['chars']:>10,} {result['status']:<15}"
        )

    print("-" * 80)
    print(f"{'TOTAL':<50} {total_lines:>8} lines")
    print()

    # Test read performance
    print("⏱️  Read Performance Test:")
    print("-" * 80)

    slow_files = []
    for doc_file in DOCUMENTATION_FILES:
        filepath = os.path.join(project_root, doc_file)
        if os.path.exists(filepath):
            read_time = test_read_performance(filepath)
            if read_time is not None:
                status = "✅ Fast" if read_time < MAX_READ_TIME_SECONDS else "⚠️  Slow"
                print(f"{doc_file:<50} {read_time:>6.3f}s {status}")

                if read_time > MAX_READ_TIME_SECONDS:
                    slow_files.append((doc_file, read_time))

    print()

    # Simulate API chunking
    print("🔄 API Chunking Simulation (2000 lines per chunk):")
    print("-" * 80)

    for doc_file in DOCUMENTATION_FILES:
        filepath = os.path.join(project_root, doc_file)
        chunks = simulate_api_read(filepath)
        if chunks:
            print(f"{doc_file}: {len(chunks)} chunks needed")
            if len(chunks) > 1:
                print("  ⚠️  Multiple reads required - potential timeout risk")

    print()

    # Summary and recommendations
    print("📋 Summary & Recommendations:")
    print("=" * 80)

    if problematic_files:
        print("❌ FILES REQUIRING IMMEDIATE ATTENTION:")
        for file_info in problematic_files:
            reduction_needed = file_info["lines"] - MAX_FILE_SIZE_LINES
            print(
                f"  - {file_info['file']}: {file_info['lines']} lines (reduce by {reduction_needed} lines)"
            )
        print()

    if slow_files:
        print("⚠️  SLOW READING FILES:")
        for filename, read_time in slow_files:
            print(f"  - {filename}: {read_time:.3f}s")
        print()

    # Overall status
    if not problematic_files and not slow_files:
        print("✅ All documentation files are within acceptable limits!")
        print("   No timeout risks detected.")
    else:
        print("⚠️  Some files may cause API timeouts or slow performance.")
        print("   Consider splitting or reducing the files listed above.")

    # Best practices
    print()
    print("💡 Best Practices:")
    print("  - Keep documentation files under 1,000 lines for best performance")
    print("  - Archive old content to separate files")
    print("  - Use concise bullet points instead of verbose descriptions")
    print("  - Extract patterns from detailed incidents")

    return 0 if not problematic_files else 1


if __name__ == "__main__":
    sys.exit(main())
