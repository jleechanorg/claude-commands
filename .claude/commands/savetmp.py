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
    """Run a git command and return stripped stdout or None on failure.

    Returns:
        str: The stripped stdout (can be empty string if command succeeded but no output).
        None: If the command failed (CalledProcessError, FileNotFoundError, TimeoutExpired).
    """
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
    return result.stdout.strip()


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

    Edge Cases:
    - origin/main missing: base_ref is None, changed_files is empty (warning printed).
    - HEAD == origin/main: changed_files is empty (no changes).
    - Detached HEAD: branch="detached".
    - Shallow clones: fallback mechanics apply, might result in empty changed_files.
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

    # Determine a base ref for changed files
    # Prefer origin/main to capture full branch diff, fall back to upstream for nonstandard repos
    # This ensures changed_files shows all changes relative to main branch
    base_ref = results.get("origin_main") or results.get("upstream")
    changed_files_output: Optional[str] = None

    if not base_ref:
        print("⚠️  No base ref found (origin/main or upstream) - changed_files will be empty", file=sys.stderr)
    elif base_ref == results.get("head_commit"):
        # HEAD is at base ref, no changes to report
        changed_files_output = ""
    else:
        # Try three-dot first (commits unique to HEAD)
        changed_files_output = _run_git_command(
            ["diff", "--name-only", f"{base_ref}...HEAD"], timeout=10
        )
        # If command failed (None) or returned empty string (no changes found by 3-dot),
        # try two-dot (all differences) just in case, though 3-dot is standard for PRs.
        # Note: _run_git_command returns None for failures, empty string for "no changes"
        if changed_files_output is None or changed_files_output == "":
            two_dot_output = _run_git_command(
                ["diff", "--name-only", f"{base_ref}..HEAD"], timeout=10
            )
            # Use two-dot output if three-dot failed or was empty, but only if two-dot succeeded
            if two_dot_output is not None:
                changed_files_output = two_dot_output

        # Warn if both git diff attempts failed (result is still None)
        if changed_files_output is None:
            print(f"⚠️  Git diff commands failed for base_ref={base_ref} - changed_files will be empty", file=sys.stderr)

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
    """Write checksums for an artifact file or all files within a directory.

    Skips files that already end with .sha256 to prevent checksum pollution
    (creating .sha256.sha256 files).
    """
    # Skip if path itself is a checksum file
    if path.suffix == ".sha256":
        return []

    if path.is_file():
        return [_write_checksum(path, base_dir)]

    checksum_paths: List[Path] = []
    if path.is_dir():
        for file_path in sorted(path.rglob("*")):
            # Skip existing .sha256 files to prevent .sha256.sha256 pollution
            if file_path.is_file() and file_path.suffix != ".sha256":
                checksum_paths.append(_write_checksum(file_path, base_dir))
    return checksum_paths


def _looks_like_absolute_path(value: str) -> bool:
    if not value:
        return False
    if value.startswith("file://"):
        return True
    if "://" in value:
        return False
    if value.startswith("~"):
        return True
    if re.match(r"^[A-Za-z]:\\\\", value):
        return True
    return Path(value).is_absolute()


def _collect_absolute_paths(
    data: object,
    current_path: str,
    found: List[Tuple[str, str]],
    limit: int = 50,
) -> None:
    if len(found) >= limit:
        return
    if isinstance(data, dict):
        for key, value in data.items():
            next_path = f"{current_path}.{key}" if current_path else str(key)
            _collect_absolute_paths(value, next_path, found, limit)
    elif isinstance(data, list):
        for idx, value in enumerate(data):
            next_path = f"{current_path}[{idx}]" if current_path else f"[{idx}]"
            _collect_absolute_paths(value, next_path, found, limit)
    elif isinstance(data, str):
        if _looks_like_absolute_path(data):
            found.append((current_path or "<root>", data))


def _json_has_llm_claims(data: object) -> bool:
    llm_keys = {
        "models",
        "raw_responses",
        "request_responses",
        "llm_provider",
        "llm_model",
        "system_instruction_text",
        "system_instruction_files",
        "system_instruction_char_count",
        "raw_response_text",
    }
    if isinstance(data, dict):
        for key, value in data.items():
            key_lower = str(key).lower()
            if key_lower in llm_keys:
                return True
            if key_lower == "debug_info" and isinstance(value, dict):
                debug_keys = {
                    "llm_provider",
                    "llm_model",
                    "system_instruction_text",
                    "system_instruction_files",
                    "system_instruction_char_count",
                    "raw_response_text",
                }
                if any(k in value for k in debug_keys):
                    return True
            if _json_has_llm_claims(value):
                return True
    elif isinstance(data, list):
        for value in data:
            if _json_has_llm_claims(value):
                return True
    return False


def _text_mentions_llm(text: str) -> bool:
    lowered = text.lower()
    return any(
        token in lowered
        for token in ("llm", "prompt", "system instruction", "model", "api behavior")
    )


def _validate_bundle(run_dir: Path, llm_claims: bool) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    all_files = [p for p in run_dir.rglob("*") if p.is_file()]

    # Missing checksums
    missing_checksums = []
    for file_path in all_files:
        if file_path.suffix == ".sha256":
            continue
        checksum_path = Path(str(file_path) + ".sha256")
        if not checksum_path.exists():
            missing_checksums.append(str(file_path))
    if missing_checksums:
        errors.append(
            "Missing .sha256 files:\n  " + "\n  ".join(sorted(missing_checksums))
        )

    # JSON portability checks + LLM claim detection
    absolute_paths: List[Tuple[str, str]] = []
    llm_detected = False
    json_files = [p for p in all_files if p.suffix == ".json"]
    for json_path in json_files:
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as exc:
            warnings.append(f"Could not parse JSON: {json_path} ({exc})")
            continue
        if not llm_detected and _json_has_llm_claims(data):
            llm_detected = True
        _collect_absolute_paths(data, "", absolute_paths, limit=50)

    if absolute_paths:
        sample = [
            f"{path_key} = {value}" for path_key, value in absolute_paths[:10]
        ]
        warnings.append(
            "Absolute paths found in JSON (portability risk):\n  "
            + "\n  ".join(sample)
        )

    if not llm_claims:
        llm_claims = llm_detected

    # Heuristic text scan if still undecided
    if not llm_claims:
        for text_file in ("methodology.md", "evidence.md", "notes.md"):
            text_path = run_dir / text_file
            if text_path.exists():
                text = text_path.read_text(encoding="utf-8")
                if _text_mentions_llm(text):
                    llm_claims = True
                    break

    if llm_claims:
        has_request_responses = any(
            p.name == "request_responses.jsonl" for p in all_files
        )
        if not has_request_responses:
            errors.append(
                "LLM/API behavior claims detected but request_responses.jsonl is missing."
            )

    return errors, warnings


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
    parser.add_argument(
        "--clean-checksums",
        action="store_true",
        help="Remove existing .sha256 files from artifacts before packaging to prevent checksum layering.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the bundle for missing checksums, portability issues, and required files.",
    )
    parser.add_argument(
        "--llm-claims",
        action="store_true",
        help="Declare LLM/API behavior claims (requires request_responses.jsonl).",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Run git resolution (skip for speed if --skip-git)
    repo_name, branch, git_provenance = _resolve_repo_info(
        skip_git=args.skip_git
    )
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
        # Clean existing checksums from source if --clean-checksums is set
        if args.clean_checksums and src_path.exists():
            if src_path.is_dir():
                for sha_file in list(src_path.rglob("*.sha256")):
                    try:
                        sha_file.unlink()
                    except OSError:
                        pass  # Ignore if can't delete
            elif src_path.suffix == ".sha256":
                continue  # Skip .sha256 files entirely in clean mode
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

    validation_errors: List[str] = []
    validation_warnings: List[str] = []
    if args.validate:
        validation_errors, validation_warnings = _validate_bundle(
            run_dir, llm_claims=args.llm_claims
        )

        if validation_warnings:
            print("⚠️  Validation warnings:")
            for warning in validation_warnings:
                print(f"  - {warning}")

        if validation_errors:
            print("❌ Validation errors:")
            for error in validation_errors:
                print(f"  - {error}")

    # Compact output for speed
    print(f"✅ Evidence archived → {run_dir}")
    if git_provenance:
        head_commit = git_provenance.get("head_commit")
        if head_commit:
            print(f"   Git: {str(head_commit)[:8]}")
    print(f"   Checksums: {len(checksum_files)} files")

    if validation_errors:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
