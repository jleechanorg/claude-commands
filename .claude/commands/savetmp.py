#!/usr/bin/env python3
"""Utility for /savetmp command to archive evidence under /tmp.

Follows evidence standards from .claude/skills/evidence-standards.md:
- SHA256 checksums for all evidence files
- Git provenance capture (HEAD, origin/main, changed files)
- Structured evidence directory layout
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Pre-compile regex for performance
_SANITIZE_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")

# Evidence standards file locations (checked in order)
_EVIDENCE_STANDARDS_PATHS = [
    ".claude/skills/evidence-standards.md",  # Project-local
    "~/.claude/skills/evidence-standards.md",  # User global
]


def _find_evidence_standards() -> str:
    """Find evidence-standards.md, checking project-local first then ~/.claude/.

    Returns:
        Path to evidence-standards.md if found, otherwise the default local path.
    """
    for path_str in _EVIDENCE_STANDARDS_PATHS:
        path = Path(path_str).expanduser()
        if path.exists():
            return str(path)
    # Default to local path even if not found (for documentation purposes)
    return _EVIDENCE_STANDARDS_PATHS[0]


def _run_git_command(args: List[str], timeout: int = 5) -> Optional[str]:
    """Run a git command and return stripped stdout or None on failure."""
    try:
        result = subprocess.run(
            ["git", *args],
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        return None
    return result.stdout.strip() or None


def _run_git_commands_parallel(
    commands: Dict[str, List[str]],
) -> Dict[str, Optional[str]]:
    """Run multiple git commands in parallel for speed."""
    results: Dict[str, Optional[str]] = {}
    with ThreadPoolExecutor(max_workers=min(len(commands), 8)) as executor:
        futures = {
            executor.submit(_run_git_command, args): name
            for name, args in commands.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            results[name] = future.result()
    return results


def _resolve_repo_info(
    skip_git: bool = False,
) -> Tuple[str, str, Optional[Dict[str, Optional[str]]]]:
    """Return (repo_name, branch_name, git_provenance) with sensible fallbacks.

    Git provenance follows evidence-standards.md requirements.
    If skip_git=True, returns simplified info without running git commands.
    """
    if skip_git:
        # Fast path: no git commands, use simple defaults
        return "evidence", "local", None

    # Run all git commands in parallel for speed
    git_commands = {
        "repo_root": ["rev-parse", "--show-toplevel"],
        "branch": ["rev-parse", "--abbrev-ref", "HEAD"],
        "head_commit": ["rev-parse", "HEAD"],
        "origin_main": ["rev-parse", "origin/main"],
        "upstream": ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
    }

    results = _run_git_commands_parallel(git_commands)

    repo_root = results.get("repo_root")
    branch = results.get("branch")

    if repo_root:
        repo_name = Path(repo_root).name
    else:
        repo_name = Path.cwd().name

    if not branch:
        branch = "detached"

    # Determine a base ref for changed files with fallbacks
    # Use origin/main as baseline, with two-dot diff for merge commits
    base_ref = results.get("origin_main")
    changed_files_output: Optional[str] = None
    if base_ref and base_ref != results.get("head_commit"):
        # Try three-dot first (commits unique to HEAD)
        changed_files_output = _run_git_command(
            ["diff", "--name-only", f"{base_ref}...HEAD"], timeout=10
        )
        # If empty, fall back to two-dot (all differences)
        if not changed_files_output:
            changed_files_output = _run_git_command(
                ["diff", "--name-only", f"{base_ref}..HEAD"], timeout=10
            )

    # Build git provenance per evidence-standards.md
    git_provenance = {
        "head_commit": results.get("head_commit"),
        "origin_main_commit": results.get("origin_main"),
        "branch": branch,
        "changed_files": changed_files_output.split("\n")
        if changed_files_output
        else [],
    }

    return repo_name, branch, git_provenance


def _read_optional_file(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    expanded = Path(path).expanduser()
    if not expanded.exists():
        print(f"⚠️  Skipping missing file referenced at {expanded}", file=sys.stderr)
        return None
    return expanded.read_text(encoding="utf-8")


def _compute_sha256(path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def _write_checksum(path: Path, base_dir: Optional[Path] = None) -> Path:
    """Write SHA256 checksum file per evidence-standards.md.

    Uses filename-only for checksums to ensure sha256sum -c works from any directory.
    """
    checksum = _compute_sha256(path)
    checksum_path = Path(str(path) + ".sha256")
    # Use filename only for portable verification (sha256sum -c works in same dir)
    path_str = path.name
    checksum_path.write_text(f"{checksum}  {path_str}\n", encoding="utf-8")
    return checksum_path


def _write_section(path: Path, content: Optional[str]) -> Optional[Path]:
    if not content:
        return None
    cleaned = content.strip()
    if not cleaned:
        return None
    path.write_text(cleaned + "\n", encoding="utf-8")
    return path


def _unique_target_path(
    dest_dir: Path, src: Path, timestamp: str, reserved: Set[Path]
) -> Path:
    """Return a target path that will not overwrite or collide with prior copies."""

    base = dest_dir / src.name
    if not base.exists() and base not in reserved:
        reserved.add(base)
        return base

    suffix = "".join(src.suffixes) if src.is_file() else ""
    stem = src.name[: -len(suffix)] if suffix else src.name

    counter = 0
    while True:
        counter += 1
        candidate = dest_dir / f"{stem}_{timestamp}_{counter}{suffix}"
        if not candidate.exists() and candidate not in reserved:
            reserved.add(candidate)
            return candidate


def _copy_artifact(
    src: Path, dest_dir: Path, timestamp: str, reserved: Set[Path]
) -> Optional[Path]:
    if not src.exists():
        print(f"⚠️  Artifact not found: {src}", file=sys.stderr)
        return None

    target = _unique_target_path(dest_dir, src, timestamp, reserved)
    if src.is_dir():
        shutil.copytree(src, target, dirs_exist_ok=False)
        return target

    shutil.copy2(src, target)
    return target


def _write_artifact_checksums(
    path: Path, base_dir: Optional[Path] = None
) -> List[Path]:
    """Write checksums for an artifact file or all files within a directory."""
    if path.is_file():
        return [_write_checksum(path, base_dir)]

    checksum_paths: List[Path] = []
    if path.is_dir():
        for file_path in sorted(path.rglob("*")):
            if file_path.is_file():
                checksum_paths.append(_write_checksum(file_path, base_dir))
    return checksum_paths


def _sanitize_work_name(raw: str) -> str:
    """Return a filesystem-safe work name constrained to a single path segment."""
    cleaned = raw.strip()
    if not cleaned:
        raise ValueError("work name must not be empty")

    # Fast check using set membership
    if "/" in cleaned or "\\" in cleaned or os.sep in cleaned:
        raise ValueError("work name must not contain path separators")
    if os.path.altsep and os.path.altsep in cleaned:
        raise ValueError("work name must not contain path separators")

    if cleaned in {".", ".."}:
        raise ValueError("work name must not be '.' or '..'")

    # Use pre-compiled regex for performance
    sanitized = _SANITIZE_PATTERN.sub("-", cleaned).strip("-_")
    if not sanitized:
        raise ValueError("work name must include alphanumeric characters")

    return sanitized


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Archive testing notes and artifacts under /tmp/<repo>/<branch>/<work>/",
    )
    parser.add_argument(
        "work_name",
        help="Name for the current work item (used as subdirectory under /tmp).",
    )
    parser.add_argument(
        "--methodology",
        help="Testing methodology description. Use @file syntax or --methodology-file for large content.",
    )
    parser.add_argument(
        "--methodology-file",
        help="Path to file containing methodology details (appended after --methodology text if both provided).",
    )
    parser.add_argument(
        "--evidence",
        help="Evidence summary text.",
    )
    parser.add_argument(
        "--evidence-file",
        help="Path to file whose contents should be appended to the evidence summary.",
    )
    parser.add_argument(
        "--notes",
        help="Additional notes or context to include in notes.md.",
    )
    parser.add_argument(
        "--notes-file",
        help="Path to file containing additional notes to append.",
    )
    parser.add_argument(
        "--artifact",
        action="append",
        dest="artifacts",
        default=[],
        help="File or directory to copy into the artifacts/ folder (can be provided multiple times).",
    )
    parser.add_argument(
        "--skip-git",
        action="store_true",
        help="Skip git commands for faster execution. Uses /tmp/evidence/local/<work>/ path.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Run git resolution (skip for speed if --skip-git)
    repo_name, branch, git_provenance = _resolve_repo_info(skip_git=args.skip_git)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    try:
        work_name = _sanitize_work_name(args.work_name)
    except ValueError as exc:
        print(f"❌ Invalid work name: {exc}", file=sys.stderr)
        return 1

    base_dir = Path("/tmp") / repo_name / branch / work_name
    run_dir = base_dir / timestamp
    artifacts_dir = run_dir / "artifacts"
    os.makedirs(artifacts_dir, exist_ok=True)

    methodology_text = args.methodology or ""
    evidence_text = args.evidence or ""
    notes_text = args.notes or ""

    file_sections = [
        ("methodology", args.methodology_file, methodology_text),
        ("evidence", args.evidence_file, evidence_text),
        ("notes", args.notes_file, notes_text),
    ]

    saved_sections: Dict[str, Optional[str]] = {}
    checksum_files: List[Path] = []

    for name, file_path, initial_text in file_sections:
        combined = initial_text.strip()
        file_content = _read_optional_file(file_path)
        if file_content:
            if combined:
                combined += "\n\n"
            combined += file_content.strip()
        section_path = _write_section(run_dir / f"{name}.md", combined)
        saved_sections[name] = str(section_path) if section_path else None
        # Write SHA256 checksum per evidence-standards.md
        if section_path:
            checksum_files.append(_write_checksum(section_path, run_dir))

    copied_artifacts: List[Dict[str, str]] = []
    reserved_targets: Set[Path] = set()
    for artifact in args.artifacts:
        src_path = Path(artifact).expanduser().resolve()
        dest_path = _copy_artifact(src_path, artifacts_dir, timestamp, reserved_targets)
        if dest_path:
            copied_artifacts.append(
                {"source": str(src_path), "destination": str(dest_path)}
            )
            checksum_files.extend(_write_artifact_checksums(dest_path, run_dir))

    # Metadata includes git provenance per evidence-standards.md (if available)
    metadata = {
        "repo": repo_name,
        "branch": branch,
        "work_name": work_name,
        "work_name_input": args.work_name,
        "timestamp_utc": timestamp,
        "run_directory": str(run_dir),
        "sections": saved_sections,
        "artifacts": copied_artifacts,
        "evidence_standards": _find_evidence_standards(),
    }
    if git_provenance:
        metadata["git_provenance"] = git_provenance
    metadata_path = run_dir / "metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    # Checksum for metadata.json
    checksum_files.append(_write_checksum(metadata_path, run_dir))

    summary_lines = [
        "# Evidence Package",
        "",
        f"- Repository: {repo_name}",
        f"- Branch: {branch}",
        f"- Work: {args.work_name}",
        f"- Created: {timestamp}",
    ]

    # Git provenance in README per evidence-standards.md (if available)
    if git_provenance:
        head_commit = git_provenance.get("head_commit")
        if head_commit and head_commit != "None":
            summary_lines.append(f"- Commit: {head_commit}")
        origin_main = git_provenance.get("origin_main_commit")
        if origin_main and origin_main != "None":
            summary_lines.append(f"- Origin/main: {origin_main}")
    summary_lines.append("")

    if copied_artifacts:
        summary_lines.append("## Artifacts")
        for artifact_entry in copied_artifacts:
            summary_lines.append(
                f"- {artifact_entry['source']} → {artifact_entry['destination']}"
            )
        summary_lines.append("")

    for section, path_str in saved_sections.items():
        if path_str:
            summary_lines.append(f"- {section}.md saved at {path_str}")
    summary_lines.append("")

    readme_path = run_dir / "README.md"
    readme_path.write_text("\n".join(summary_lines), encoding="utf-8")
    # Checksum for README.md
    checksum_files.append(_write_checksum(readme_path, run_dir))

    # Compact output for speed
    print(f"✅ Evidence archived → {run_dir}")
    if git_provenance:
        head_commit = git_provenance.get("head_commit")
        if head_commit:
            print(f"   Git: {str(head_commit)[:8]}")
    print(f"   Checksums: {len(checksum_files)} files")

    return 0


if __name__ == "__main__":
    sys.exit(main())
