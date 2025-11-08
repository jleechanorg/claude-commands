#!/usr/bin/env python3
"""Utility for /savetmp command to archive evidence under /tmp."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set


def _run_git_command(args: List[str]) -> Optional[str]:
    """Run a git command and return stripped stdout or None on failure."""
    try:
        result = subprocess.run(
            ["git", *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return result.stdout.strip() or None


def _resolve_repo_info() -> tuple[str, str]:
    """Return (repo_name, branch_name) with sensible fallbacks."""
    repo_root = _run_git_command(["rev-parse", "--show-toplevel"])
    branch = _run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])

    if repo_root:
        repo_name = Path(repo_root).name
    else:
        repo_name = Path.cwd().name

    if not branch:
        branch = "detached"

    return repo_name, branch


def _read_optional_file(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    expanded = Path(path).expanduser()
    if not expanded.exists():
        print(f"⚠️  Skipping missing file referenced at {expanded}", file=sys.stderr)
        return None
    return expanded.read_text(encoding="utf-8")


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


def _sanitize_work_name(raw: str) -> str:
    """Return a filesystem-safe work name constrained to a single path segment."""

    cleaned = raw.strip()
    if not cleaned:
        raise ValueError("work name must not be empty")

    forbidden_separators = {"/", "\\", os.sep}
    if os.path.altsep:
        forbidden_separators.add(os.path.altsep)
    if any(sep and sep in cleaned for sep in forbidden_separators if sep):
        raise ValueError("work name must not contain path separators")

    if cleaned in {".", ".."}:
        raise ValueError("work name must not be '.' or '..'")

    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", cleaned).strip("-_")
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
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    repo_name, branch = _resolve_repo_info()
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

    for name, file_path, initial_text in file_sections:
        combined = initial_text.strip()
        file_content = _read_optional_file(file_path)
        if file_content:
            if combined:
                combined += "\n\n"
            combined += file_content.strip()
        section_path = _write_section(run_dir / f"{name}.md", combined)
        saved_sections[name] = str(section_path) if section_path else None

    copied_artifacts: List[Dict[str, str]] = []
    reserved_targets: Set[Path] = set()
    for artifact in args.artifacts:
        src_path = Path(artifact).expanduser().resolve()
        dest_path = _copy_artifact(
            src_path, artifacts_dir, timestamp, reserved_targets
        )
        if dest_path:
            copied_artifacts.append(
                {"source": str(src_path), "destination": str(dest_path)}
            )

    metadata = {
        "repo": repo_name,
        "branch": branch,
        "work_name": work_name,
        "work_name_input": args.work_name,
        "timestamp_utc": timestamp,
        "run_directory": str(run_dir),
        "sections": saved_sections,
        "artifacts": copied_artifacts,
    }
    (run_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    summary_lines = [
        "# Evidence Package",
        "",
        f"- Repository: {repo_name}",
        f"- Branch: {branch}",
        f"- Work: {args.work_name}",
        f"- Created: {timestamp}",
        "",
    ]

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

    (run_dir / "README.md").write_text("\n".join(summary_lines), encoding="utf-8")

    print("✅ Evidence archived")
    print(f"Base directory: {base_dir}")
    print(f"Run directory:  {run_dir}")
    if copied_artifacts:
        print("Copied artifacts:")
        for artifact_entry in copied_artifacts:
            print(
                f"  - {artifact_entry['source']} → {artifact_entry['destination']}"
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
