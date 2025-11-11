#!/usr/bin/env python3
"""Construct a second opinion MCP request with full PR delta context."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        print(
            f"Warning: invalid integer for {name}='{value}', using default {default}",
            file=sys.stderr,
        )
        return default


def run_git(args: list[str], *, strip: bool = False) -> tuple[str, str | None]:
    """Run a git command and return stdout plus stderr on failure."""

    proc = subprocess.run(["git", *args], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        return "", proc.stderr.strip() or None
    output = proc.stdout
    if strip:
        output = output.strip()
    return output, None


def truncate_text(text: str, limit: int, *, label: str, notices: list[str]) -> str:
    if limit <= 0 or len(text) <= limit:
        return text
    truncated = text[:limit]
    if not truncated.endswith("\n"):
        truncated += "\n"
    removed = len(text) - limit
    message = f"{label} truncated by {removed} characters (limit {limit})."
    notices.append(message)
    truncated += f"...[{message}]\n"
    return truncated


def parse_changed_files(raw: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for line in raw.splitlines():
        if not line:
            continue
        parts = line.split("\t")
        status = parts[0]
        if len(parts) == 1:
            print(
                f"Warning: malformed git status line with no path: '{line}'",
                file=sys.stderr,
            )
            continue
        if status.startswith(("R", "C")) and len(parts) >= 3:
            entries.append({"status": status, "path": parts[2], "previousPath": parts[1]})
        else:
            entries.append({"status": status, "path": parts[-1]})
    return entries


def build_git_context(base_ref: str, *, max_files: int, diff_limit: int, patch_limit: int) -> tuple[dict[str, Any], list[str]]:
    notices: list[str] = []

    branch, _ = run_git(["rev-parse", "--abbrev-ref", "HEAD"], strip=True)
    repo_root, _ = run_git(["rev-parse", "--show-toplevel"], strip=True)
    remote_url, _ = run_git(["config", "--get", "remote.origin.url"], strip=True)
    status, _ = run_git(["status", "--short"], strip=False)
    diffstat, _ = run_git(["diff", f"{base_ref}...HEAD", "--stat"], strip=False)
    diff_full, diff_err = run_git(["diff", f"{base_ref}...HEAD"], strip=False)
    if diff_err:
        notices.append(f"git diff {base_ref}...HEAD error: {diff_err}")
    diff_full = truncate_text(diff_full, diff_limit, label=f"git diff {base_ref}...HEAD", notices=notices) if diff_full else ""

    commits, _ = run_git(["log", f"{base_ref}..HEAD", "--oneline", "--no-decorate"], strip=False)

    changed_raw, changed_err = run_git(["diff", f"{base_ref}...HEAD", "--name-status"], strip=False)
    if changed_err:
        notices.append(f"git diff --name-status error: {changed_err}")
    changed_entries = parse_changed_files(changed_raw)

    patches: dict[str, str] = {}
    captured = 0
    for entry in changed_entries:
        if captured >= max_files:
            break
        path = entry.get("path") or entry.get("previousPath")
        if not path:
            continue
        patch, patch_err = run_git(["diff", f"{base_ref}...HEAD", "--", path], strip=False)
        if patch_err:
            notices.append(f"git diff for {path} error: {patch_err}")
            continue
        if not patch:
            continue
        patches[path] = truncate_text(patch, patch_limit, label=f"diff for {path}", notices=notices)
        captured += 1

    if len(changed_entries) > max_files:
        notices.append(
            f"Captured patches for first {max_files} files out of {len(changed_entries)} changed files."
        )

    context: dict[str, Any] = {
        "branch": branch or "<unknown>",
        "base": base_ref,
        "repoRoot": repo_root if repo_root is not None else None,
        "remote": remote_url if remote_url is not None else None,
        "status": status,
        "diffstat": diffstat,
        "diff": diff_full,
        "recentCommits": commits,
        "changedFiles": changed_entries,
        "patches": patches,
        "limits": {
            "maxFiles": max_files,
            "diffCharLimit": diff_limit,
            "patchCharLimit": patch_limit,
        },
    }

    # Remove None values for cleanliness while preserving meaningful empty strings
    context = {k: v for k, v in context.items() if v is not None}

    return context, notices


def main(argv: list[str]) -> int:
    if len(argv) != 5:
        print("Usage: build_second_opinion_request.py OUTPUT_PATH QUESTION MAX_OPINIONS BASE_REF", file=sys.stderr)
        return 1

    output_path = Path(argv[1])
    question = argv[2]
    try:
        max_opinions = int(argv[3])
    except ValueError:
        print("MAX_OPINIONS must be an integer", file=sys.stderr)
        return 1
    base_ref = argv[4]

    diff_limit = env_int("SECOND_OPINION_MAX_DIFF_CHARS", 24000)
    patch_limit = env_int("SECOND_OPINION_MAX_PATCH_CHARS", 6000)
    max_files = env_int("SECOND_OPINION_MAX_FILES", 20)

    git_context, notices = build_git_context(
        base_ref,
        max_files=max_files,
        diff_limit=diff_limit,
        patch_limit=patch_limit,
    )

    payload: dict[str, Any] = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "agent.second_opinion",
            "arguments": {
                "question": question,
                "maxOpinions": max_opinions,
                "gitContext": git_context,
            },
        },
        "id": 1,
    }

    if notices:
        payload["params"]["arguments"]["gitContextNotices"] = notices

    try:
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    except OSError as e:
        print(f"Error: failed to write output to {output_path}: {e}", file=sys.stderr)
        return 1

    changed_files = git_context.get("changedFiles", [])
    patches = git_context.get("patches", {})

    print(f"  ↳ Branch: {git_context.get('branch')} (base: {base_ref})")
    print(f"  ↳ Changed files detected: {len(changed_files)}")
    print(f"  ↳ Patches attached: {len(patches)} (limit {max_files})")
    if notices:
        for note in notices:
            print(f"    · {note}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
