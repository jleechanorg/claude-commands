#!/usr/bin/env python3
"""Standardize slash command markdown files with execution workflows."""
from __future__ import annotations

from collections import OrderedDict
import argparse
from pathlib import Path
import re
from typing import Any, Iterable, List, Sequence, Tuple

import yaml

PHASE_KEYWORDS = ["phase"]
WORKFLOW_KEYWORDS = [
    "workflow",
    "execution",
    "step",
    "steps",
    "checklist",
    "protocol",
    "runbook",
    "todo",
    "procedure",
    "action",
]
EXCLUDE_KEYWORDS = [
    "example",
    "examples",
    "sample",
    "reference",
    "documentation",
    "notes",
    "background",
    "overview",
    "characteristics",
    "protocol",
    "details",
    "context",
    "history",
]

EXCLUDE_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(word) for word in EXCLUDE_KEYWORDS) + r")\b"
)

HEADING_RE = re.compile(r"^#{1,6}\s+.*$", re.MULTILINE)
CODE_FENCE_RE = re.compile(r"^[ \t]{0,3}(```|~~~).*$", re.MULTILINE)
PHASE_PREFIX_RE = re.compile(r"^phase\s*-?\d+\s*[:\-]\s*", re.IGNORECASE)
PHASE_NUMBER_RE = re.compile(r"^phase\s*(?P<num>-?\d+)", re.IGNORECASE)

EXECUTION_HEADER = (
    "## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE\n"
    "**When this command is invoked, YOU (Claude) must execute these steps immediately:**\n"
    "**This is NOT documentation - these are COMMANDS to execute right now.**\n"
    "**Use TodoWrite to track progress through multi-phase workflows.**\n\n"
)


def parse_frontmatter(text: str) -> Tuple[dict, str]:
    """
    Parse YAML frontmatter delimited by lines that contain only '---'.
    Supports LF/CRLF and ignores trailing spaces.
    """
    # Match frontmatter with anchored regex: start of file, ---, content, --- on own line
    # Support consistent CRLF throughout by using \r?\n in all positions
    pattern = r'^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n'
    match = re.match(pattern, text, re.DOTALL)
    if match:
        fm_text = match.group(1)
        rest = text[match.end():]
        try:
            data = yaml.safe_load(fm_text) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid frontmatter YAML: {e}") from e
        return data, rest.lstrip("\n\r")
    return {}, text


def format_value(value: Any) -> str:
    if isinstance(value, str):
        if not value:
            return "''"
        dumped = (
            yaml.safe_dump(
                value, default_flow_style=True, explicit_end=False, allow_unicode=True
            )
            .strip()
        )
        stripped_dumped = dumped
        if (
            (stripped_dumped.startswith('"') and stripped_dumped.endswith('"'))
            or (stripped_dumped.startswith("'") and stripped_dumped.endswith("'"))
        ):
            stripped_dumped = stripped_dumped[1:-1]
        if stripped_dumped != value:
            return dumped
        return value
    return (
        yaml.safe_dump(
            value, default_flow_style=True, explicit_end=False, allow_unicode=True
        )
        .strip()
    )


def format_frontmatter(data: dict) -> str:
    ordered = OrderedDict()
    ordered["description"] = data.get("description", "")
    ordered["type"] = data.get("type", "llm-orchestration")
    ordered["execution_mode"] = data.get("execution_mode", "immediate")
    for key, value in data.items():
        if key not in ordered:
            ordered[key] = value
    lines = ["---"]
    for key, value in ordered.items():
        lines.append(f"{key}: {format_value(value)}")
    lines.append("---\n")
    return "\n".join(lines)


def find_code_fence_ranges(text: str) -> List[Tuple[int, int]]:
    """
    Detect fenced code blocks (``` or ~~~), allowing up to 3 spaces indent.
    Ensures the closing fence matches the opening marker type.
    """
    ranges: List[Tuple[int, int]] = []
    open_start: int | None = None
    open_marker: str | None = None
    for match in CODE_FENCE_RE.finditer(text):
        marker = match.group(1)  # Extract the marker type (``` or ~~~)
        if open_marker is None:
            # Opening fence
            open_marker = marker
            open_start = match.start()
        elif marker == open_marker:
            # Closing fence (matches opening marker type)
            end = text.find("\n", match.end())
            end = len(text) if end == -1 else end + 1
            if open_start is not None:
                ranges.append((open_start, end))
            open_marker = None
            open_start = None
        # else: wrong marker type, ignore (keeps looking for matching close)
    # Unclosed fence extends to end of file
    if open_start is not None:
        ranges.append((open_start, len(text)))
    return ranges


def is_in_code_fence(position: int, ranges: Sequence[Tuple[int, int]]) -> bool:
    for start, end in ranges:
        if start <= position < end:
            return True
    return False


def extract_sections(text: str) -> Tuple[str, List[dict]]:
    sections: List[dict] = []
    matches = list(HEADING_RE.finditer(text))
    code_ranges = find_code_fence_ranges(text)
    filtered_matches = [m for m in matches if not is_in_code_fence(m.start(), code_ranges)]
    preface = text[: filtered_matches[0].start()] if filtered_matches else text
    for idx, match in enumerate(filtered_matches):
        level = len(match.group().split()[0])
        heading_line = match.group()
        heading_text = (
            heading_line[level + 1 :].strip()
            if len(match.group()) > level
            else heading_line.strip("# ").strip()
        )
        start = match.end()
        end = (
            filtered_matches[idx + 1].start()
            if idx + 1 < len(filtered_matches)
            else len(text)
        )
        content = text[start:end]
        sections.append(
            {
                "level": level,
                "heading_line": heading_line,
                "heading_text": heading_text,
                "content": content,
            }
        )
    return preface, sections


def convert_bullets(content: str) -> str:
    lines = content.strip("\n").splitlines()
    if not lines:
        return ""
    number = 1
    converted = []
    last_indent = -1
    for line in lines:
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if stripped.startswith("**Action Steps:**"):
            converted.append("**Action Steps:**")
            number = 1  # Reset counter after "Action Steps:" header
            last_indent = -1
            continue
        # Reset counter when returning to top level from nested content
        if indent <= 2 and last_indent > 2:
            number = 1
        if indent <= 2 and (stripped.startswith("- ") or stripped.startswith("* ")):
            converted.append(" " * indent + f"{number}. {stripped[2:].strip()}")
            number += 1
            last_indent = indent
        elif indent <= 2 and re.match(r"\d+\.\s", stripped):
            # Extract content after first ". " to preserve periods in content
            match = re.match(r"\d+\.\s+(.*)$", stripped)
            if match:
                converted.append(" " * indent + f"{number}. {match.group(1)}")
            else:
                converted.append(" " * indent + f"{number}. {stripped.split('.', 1)[1].strip()}")
            number += 1
            last_indent = indent
        else:
            converted.append(line)
            last_indent = indent
    return "\n".join(converted)


def derive_description(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return fallback


def should_exclude(heading_lower: str) -> bool:
    return bool(EXCLUDE_PATTERN.search(heading_lower))


def classify_sections(preface: str, sections: Iterable[dict]) -> Tuple[list, list, str]:
    phase_sections = []
    other_sections = []
    for idx, sec in enumerate(sections):
        heading_lower = sec["heading_text"].lower()
        is_phase = any(key in heading_lower for key in PHASE_KEYWORDS)
        if is_phase:
            phase_sections.append((idx, sec))
            continue
        if should_exclude(heading_lower):
            other_sections.append((idx, sec))
            continue
        is_workflow = is_phase or any(key in heading_lower for key in WORKFLOW_KEYWORDS)
        if is_workflow and sec["level"] >= 2:
            if "workflow phases" in heading_lower:
                other_sections.append((idx, sec))
            elif sec["content"].lstrip().startswith("###"):
                other_sections.append((idx, sec))
            else:
                phase_sections.append((idx, sec))
        else:
            other_sections.append((idx, sec))
    if not phase_sections and preface.strip():
        if other_sections:
            idx, sec = other_sections.pop(0)
            phase_sections.append((idx, sec))
        else:
            synthetic = {
                "level": 3,
                "heading_line": "### Phase 1: Execute Documented Workflow",
                "heading_text": "Phase 1: Execute Documented Workflow",
                "content": preface,
            }
            phase_sections.append((-1, synthetic))
            preface = ""
    phase_sections.sort(key=lambda item: item[0])
    return phase_sections, other_sections, preface


def build_workflow(phase_sections: List[Tuple[int, dict]]) -> Tuple[str, set[int]]:
    workflow_parts: List[str] = []
    phase_counter = 1
    if phase_sections:
        first_heading = phase_sections[0][1]["heading_text"]
        match = PHASE_NUMBER_RE.match(first_heading)
        if match and match.group("num") == "0":
            phase_counter = 0
    used_indices: set[int] = set()
    for original_idx, sec in phase_sections:
        used_indices.add(original_idx)
        heading_text = sec["heading_text"].strip()
        stripped_heading = PHASE_PREFIX_RE.sub("", heading_text, count=1).strip()
        if not stripped_heading:
            stripped_heading = heading_text
        title = f"Phase {phase_counter}: {stripped_heading}"
        phase_heading = f"### {title}"
        phase_counter += 1
        content = sec["content"].strip("\n")
        if content:
            converted = convert_bullets(content)
            if not converted.startswith("**Action Steps:**"):
                converted = "**Action Steps:**\n" + converted
        else:
            converted = (
                "**Action Steps:**\n1. Review the reference documentation below and execute the detailed steps."
            )
        workflow_parts.append(phase_heading)
        workflow_parts.append(converted)
    if not workflow_parts:
        workflow_parts.append("### Phase 1: Execute Documented Workflow")
        workflow_parts.append(
            "**Action Steps:**\n1. Review the reference documentation below and execute the detailed steps sequentially."
        )
    workflow_text = "\n\n".join(workflow_parts).strip() + "\n"
    return workflow_text, used_indices


def build_reference(preface: str, other_sections: list, used_indices: set) -> str:
    reference_parts = []
    if preface.strip():
        reference_parts.append(preface.strip("\n"))
    for idx, sec in other_sections:
        if idx in used_indices:
            continue
        reference_parts.append(sec["heading_line"].strip("\n"))
        content = sec["content"].strip("\n")
        if content:
            reference_parts.append(content)
    if reference_parts:
        return "\n\n".join(reference_parts).strip() + "\n"
    return "_No additional reference documentation provided._\n"


def _is_already_standardized(body: str) -> bool:
    """Check if file already has standardized structure."""
    return "## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE" in body and "## 🚨 EXECUTION WORKFLOW" in body


def process_file(path: Path, *, force: bool = False, dry_run: bool = False) -> bool:
    original_text = path.read_text()
    fm, body = parse_frontmatter(original_text)

    # Skip if already standardized (unless force flag is set)
    if not force and _is_already_standardized(body):
        return False
    if "description" not in fm or fm["description"] is None:
        fm["description"] = derive_description(body, path.stem.replace("_", " "))
    fm.setdefault("type", "llm-orchestration")
    fm.setdefault("execution_mode", "immediate")

    preface, sections = extract_sections(body)
    phase_sections, other_sections, preface = classify_sections(preface, sections)
    workflow_text, used_indices = build_workflow(phase_sections)
    reference_text = build_reference(preface, other_sections, used_indices)

    body_output = (
        EXECUTION_HEADER
        + "## 🚨 EXECUTION WORKFLOW\n\n"
        + workflow_text
        + "\n## 📋 REFERENCE DOCUMENTATION\n\n"
        + reference_text
    )
    new_text = format_frontmatter(fm) + body_output
    if not force and new_text == original_text:
        return False
    if dry_run:
        print(f"[dry-run] {path}")
        return new_text != original_text
    path.write_text(new_text)
    return new_text != original_text


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Standardize slash command markdown files."
    )
    parser.add_argument(
        "--base",
        type=Path,
        default=Path(".claude/commands"),
        help="Base directory containing markdown command files.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rewrite files even if the generated output matches the existing content.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show files that would change without writing updates.",
    )
    args = parser.parse_args()

    base = args.base
    if not base.exists():
        raise SystemExit(f"Base directory '{base}' does not exist.")
    if not base.is_dir():
        raise SystemExit(f"Base path '{base}' is not a directory.")

    changed = 0
    scanned = 0
    for path in sorted(base.rglob('*.md')):
        scanned += 1
        if process_file(path, force=args.force, dry_run=args.dry_run):
            changed += 1
    print(f"[standardize] scanned={scanned} changed={changed}")


if __name__ == "__main__":
    main()
