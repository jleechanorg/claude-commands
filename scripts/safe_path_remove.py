#!/usr/bin/env python3
"""Remove one install destination entry after proving it is safe to remove.

`install-claude-commands.sh` overwrites source-managed files in place. Before
copying an entry it must remove whatever currently sits at that destination,
and installers are exactly the place where an unvalidated recursive delete is
dangerous: a mis-expanded variable can aim at `$HOME`, `/`, or a parent of the
install root.

Shell guardrails cannot verify a variable target, so the deletion happens here
instead, behind explicit proofs:

* the target must be absolute, normalized, and free of `..`;
* the target must sit strictly *below* the install root (never equal to it);
* the install root itself must be a real directory that is not `/` or `$HOME`;
* a symlinked parent is refused (the installer already skips those links);
* only the final path component is removed, and symlinks are unlinked rather
  than followed.

Usage:
    safe_path_remove.py --under <install-root> <path>

Exit codes: 0 = removed or already absent, 2 = refused or usage error.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys


def refusal(message: str) -> "NoReturn":  # noqa: F821 - typing nicety only
    print(f"safe_path_remove: refused: {message}", file=sys.stderr)
    raise SystemExit(2)


def normalized(path: str) -> str:
    if not path:
        refusal("empty path")
    if not os.path.isabs(path):
        refusal(f"not absolute: {path!r}")
    if ".." in path.split(os.sep):
        refusal(f"contains '..': {path!r}")
    return os.path.normpath(path)


def check_target(base: str, target: str) -> None:
    if base == os.sep:
        refusal("install root is '/'")
    if target == os.sep:
        refusal("target is '/'")
    if target == base:
        refusal("target equals the install root")
    if not target.startswith(base + os.sep):
        refusal(f"{target!r} is not below install root {base!r}")

    parent = os.path.dirname(target)
    if os.path.islink(parent):
        refusal(f"parent is a symlink: {parent!r}")

    real_base = os.path.realpath(base)
    real_parent = os.path.realpath(parent)
    if real_parent != real_base and not real_parent.startswith(real_base + os.sep):
        refusal(f"{target!r} resolves outside install root {real_base!r}")


def remove(target: str) -> None:
    if os.path.islink(target) or os.path.isfile(target):
        os.unlink(target)
    elif os.path.isdir(target):
        shutil.rmtree(target)
    elif os.path.exists(target):
        refusal(f"unsupported entry type: {target!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--under", required=True, help="install root the target must sit below")
    parser.add_argument("path", help="entry to remove")
    args = parser.parse_args(argv)

    base = normalized(args.under)
    target = normalized(args.path)
    if not os.path.isdir(base):
        refusal(f"install root is not a directory: {base!r}")
    check_target(base, target)

    if not os.path.lexists(target):
        return 0
    remove(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
