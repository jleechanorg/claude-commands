#!/usr/bin/env python3
"""
Find workflows that use actions/checkout without fetch-depth:, submodules:false, lfs:false.

Usage: python3 find-workflows-missing-fetch-depth.py <workflows_dir>
       (default: .github/workflows)

Exit codes:
  0 = all workflows have fetch-depth optimization
  1 = at least one workflow is missing it (printed to stdout)

The script reports workflows in this priority order:
  1. Missing fetch-depth entirely (largest savings, target first)
  2. Has fetch-depth but missing submodules:false / lfs:false (smaller savings)

For each file, prints path + checkout-count + missing keys.
"""

import re
import sys
import os
from pathlib import Path

USES_RE = re.compile(r"^\s*-?\s*uses:\s*actions/checkout@[^\s#]+\s*(?:#.*)?$")


def scan_file(path: Path):
    """Return (total_checkouts, missing_keys) for this workflow file."""
    text = path.read_text()
    checkout_count = text.count("uses: actions/checkout@")
    if checkout_count == 0:
        return None  # no checkout step in this file

    has_fetch_depth = "fetch-depth:" in text
    has_submodules = "submodules: false" in text
    has_lfs = "lfs: false" in text

    missing = []
    if not has_fetch_depth:
        missing.append("fetch-depth")
    if not has_submodules:
        missing.append("submodules:false")
    if not has_lfs:
        missing.append("lfs:false")
    return (checkout_count, missing)


def main():
    workflows_dir = Path(sys.argv[1] if len(sys.argv) > 1 else ".github/workflows")
    if not workflows_dir.exists():
        print(f"ERROR: {workflows_dir} does not exist", file=sys.stderr)
        return 2

    files = sorted(workflows_dir.glob("*.yml"))
    needs_fix = []
    for f in files:
        result = scan_file(f)
        if result is None:
            continue
        count, missing = result
        if missing:
            needs_fix.append((f.name, count, missing))

    if not needs_fix:
        print(f"OK: all {len(files)} workflows have fetch-depth optimization")
        return 0

    print(f"❌ {len(needs_fix)} workflows missing fetch-depth optimization:")
    for name, count, missing in needs_fix:
        print(f"  {name:<35} {count} checkout(s) — missing: {', '.join(missing)}")
    print()
    print("Fix template (add to each checkout step's with: block):")
    print("  with:")
    print("    fetch-depth: 1")
    print("    submodules: false")
    print("    lfs: false")
    return 1


if __name__ == "__main__":
    sys.exit(main())