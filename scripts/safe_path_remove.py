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
* the install root must be a real directory that is not `/` or `$HOME`, and must
  not itself be a symlink;
* deletion is anchored to an ``O_NOFOLLOW`` descriptor for the root: every path
  component is opened relative to its already-open parent with ``O_NOFOLLOW``, so
  swapping any component (including an intermediate one, or an alias of the root)
  for a symlink cannot redirect the delete outside the root;
* only the final path component is removed, and symlinks are unlinked rather
  than followed.

Usage:
    safe_path_remove.py --under <install-root> <path>

Exit codes: 0 = removed or already absent, 2 = refused or usage error.
"""

from __future__ import annotations

import argparse
import os
import stat
import sys
from pathlib import Path


def refusal(message: str) -> None:
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


def check_root(base: str) -> None:
    if base == os.sep:
        refusal("install root is '/'")
    if base == os.path.expanduser("~") or os.path.realpath(base) == os.path.realpath(
        os.path.expanduser("~")
    ):
        refusal("install root is the home directory")
    if os.path.islink(base):
        refusal(f"install root is a symlink: {base!r}")
    if not os.path.isdir(base):
        refusal(f"install root is not a directory: {base!r}")


def check_target(base: str, target: str) -> None:
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


def remove_at(dir_fd: int, name: str) -> None:
    """Delete ``name`` relative to an already-open directory descriptor."""
    info = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
    if stat.S_ISDIR(info.st_mode):
        child_fd = os.open(
            name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=dir_fd
        )
        try:
            for child in os.listdir(child_fd):
                remove_at(child_fd, child)
        finally:
            os.close(child_fd)
        os.rmdir(name, dir_fd=dir_fd)
    else:
        os.unlink(name, dir_fd=dir_fd)


def open_no_follow(parts: list[str], start_fd: int | None = None) -> int:
    """Open ``parts`` from ``/`` (or ``start_fd``) without following any symlink.

    Anchoring at the filesystem root closes the remaining gap: opening an
    absolute path such as ``/tmp/anchor/root`` follows a symlink in its *parent*
    components, so a swap there redirected earlier versions of this helper.
    """
    fd = os.open(os.sep, os.O_RDONLY | os.O_DIRECTORY) if start_fd is None else os.dup(start_fd)
    try:
        for part in parts:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
    except OSError as error:
        os.close(fd)
        refusal(f"cannot open {os.sep.join(parts)!r} without following a symlink: {error}")
    return fd


def walk_and_remove(root_fd: int, components: list[str]) -> None:
    """Descend from the root descriptor, then remove the final component.

    Every intermediate directory is opened relative to its already-open parent
    with O_NOFOLLOW, so no path component can be swapped for a symlink between
    validation and deletion.
    """
    dir_fd = os.dup(root_fd)
    try:
        for component in components[:-1]:
            next_fd = os.open(
                component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=dir_fd
            )
            os.close(dir_fd)
            dir_fd = next_fd
        remove_at(dir_fd, components[-1])
    finally:
        os.close(dir_fd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--under", required=True, help="install root the target must sit below")
    parser.add_argument("path", help="entry to remove")
    args = parser.parse_args(argv)

    base = normalized(args.under)
    target = normalized(args.path)
    check_root(base)
    check_target(base, target)

    if not os.path.lexists(target):
        return 0

    # Lexical relationship first: the final component may legitimately be a
    # symlink the installer is replacing, so it must not be resolved. Every
    # intermediate component is later opened with O_NOFOLLOW, so a symlinked
    # ancestor is refused rather than followed.
    relative = os.path.relpath(target, base)
    components = [part for part in Path(relative).parts if part not in ("", os.curdir)]
    if not components or components[0] == os.pardir:
        refusal(f"{target!r} is not below install root {base!r}")

    real_base = os.path.realpath(base)
    root_parts = [part for part in Path(real_base).parts if part not in (os.sep, "")]

    expected = os.stat(real_base)
    root_fd = open_no_follow(root_parts)
    try:
        opened = os.fstat(root_fd)
        if (opened.st_dev, opened.st_ino) != (expected.st_dev, expected.st_ino):
            refusal(f"install root changed between validation and open: {base!r}")
        walk_and_remove(root_fd, components)
    finally:
        os.close(root_fd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
