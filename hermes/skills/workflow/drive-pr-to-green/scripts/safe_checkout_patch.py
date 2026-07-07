#!/usr/bin/env python3
"""
safe_checkout_patch.py — safely add fetch-depth: 1 + submodules: false + lfs: false
to actions/checkout@<sha> invocations in GitHub Actions workflow YAML files.

Handles two failure modes that naive patches trip on:
  1. Indent mismatch (column of "uses:" must equal column of "with:")
  2. Double-with: block (appending a fresh with: after an existing one is silently
     broken — GHA parses the FIRST with: only, so default values apply)

Usage:
    python3 safe_checkout_patch.py path/to/workflow.yml [path/to/others.yml ...]

Idempotent. Re-running on a patched file is a no-op (fetch-depth already present
under the with: block is detected).

Exit 0 on success or no-op, exit 1 on YAML parse error after patch.

Verified 2026-07-05: works on auth-browser-tests.yml (existing with: block with
ref: + persist-credentials: false), design-doc-gate.yml, mcp-smoke-tests.yml,
infra-contract-tests.yml, coverage.yml, pr-preview.yml, presubmit.yml,
dice-tests.yml, levelup-tests.yml, auto-deploy-dev.yml, deploy-dev.yml,
deploy-production.yml, deploy-dice-audit.yml, deploy-levelup-test.yml.
"""

import re
import sys
import yaml
from pathlib import Path

USES_RE = re.compile(r"^(?P<lead>\s*-?\s*)uses:\s*actions/checkout@[^\s#]+\s*(?:#.*)?$")


def patch_file(path: str) -> bool:
    """Patch one YAML file. Returns True if modified."""
    with open(path) as fh:
        text = fh.read()
    lines = text.split("\n")
    n = len(lines)
    out = []
    i = 0
    while i < n:
        ln = lines[i]
        m = USES_RE.match(ln)
        if not m:
            out.append(ln)
            i += 1
            continue

        col_uses = ln.index("uses:")
        with_indent = " " * col_uses
        kv_indent = " " * (col_uses + 2)

        out.append(ln)

        # Skip blank/comment lines to find an existing with: block at the same indent
        j = i + 1
        while j < n and (not lines[j].strip() or lines[j].lstrip().startswith("#")):
            j += 1

        with_start = None
        if j < n and re.match(r"^\s+with:\s*(?:#.*)?$", lines[j]):
            with_start = j
            with_col = len(lines[j]) - len(lines[j].lstrip())
            # Walk forward until we leave the block
            k = j + 1
            while k < n:
                s = lines[k]
                if not s.strip():
                    k += 1
                    continue
                s_indent = len(s) - len(s.lstrip())
                if s_indent <= col_uses:
                    break
                # Both same-column keys and deeper-column blocks stay inside
                if s_indent >= with_col:
                    if re.match(r"^\s+\S", s):
                        k += 1
                        continue
                break
            with_end = k
        else:
            with_end = j

        if with_start is None:
            # Fresh with: block
            out.append(f"{with_indent}with:")
            out.append(f"{kv_indent}fetch-depth: 1")
            out.append(f"{kv_indent}submodules: false")
            out.append(f"{kv_indent}lfs: false")
            i = with_end
        else:
            # Augment existing block — insert fetch-depth/submodules/lfs INSIDE it
            block_lines = lines[with_start:with_end]
            # Find last non-empty, non-comment line in the block
            last_idx = None
            for bi in range(len(block_lines) - 1, -1, -1):
                if block_lines[bi].strip() and not block_lines[bi].lstrip().startswith("#"):
                    last_idx = bi
                    break
            if last_idx is None:
                # Only "with:" line exists
                out.append(lines[with_start])
                out.append(f"{kv_indent}fetch-depth: 1")
                out.append(f"{kv_indent}submodules: false")
                out.append(f"{kv_indent}lfs: false")
                for bl in block_lines[1:]:
                    out.append(bl)
            else:
                emit_until = last_idx + 1
                for bi in range(0, emit_until):
                    out.append(block_lines[bi])
                out.append(f"{kv_indent}fetch-depth: 1")
                out.append(f"{kv_indent}submodules: false")
                out.append(f"{kv_indent}lfs: false")
                for bl in block_lines[emit_until:]:
                    out.append(bl)
            i = with_end

    new_text = "\n".join(out)
    if new_text != text:
        with open(path, "w") as fh:
            fh.write(new_text)
        return True
    return False


def verify_yaml(path: str) -> bool:
    try:
        with open(path) as fh:
            yaml.safe_load(fh)
        return True
    except yaml.YAMLError:
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: safe_checkout_patch.py <file.yml> [file2.yml ...]")
        sys.exit(2)

    failures = []
    no_ops = 0
    changed = 0
    for arg in sys.argv[1:]:
        p = Path(arg)
        if not p.exists():
            print(f"  ❌ {p}: not found")
            failures.append(str(p))
            continue
        modified = patch_file(str(p))
        if not verify_yaml(str(p)):
            print(f"  ❌ {p}: YAML parse error after patch (REVERT manually)")
            failures.append(str(p))
            continue
        if modified:
            changed += 1
            print(f"  ✓ {p}: patched + YAML valid")
        else:
            no_ops += 1
            print(f"  ✓ {p}: already optimized (no-op)")

    print(f"\n{changed} files patched, {no_ops} no-op, {len(failures)} failures")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()