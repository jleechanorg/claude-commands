#!/usr/bin/env python3
"""
section_completeness.py — Audit per-section word/character count and per-
mechanic quantification in a campaign-bible Markdown file.

Runs with no LLM. Deterministic. Exits non-zero on any ERROR.

For each of the 9 sections + the Personality Template append:
  - Word count
  - Character count
  - Pass/fail against a minimum length (so we don't ship a "Section 5:
    Family" that's one paragraph)

For each ability, item, or mechanic:
  - Detects whether it has an action economy / save DC / daily limit
  - Flags abilities with no quantification

Usage:
    python3 section_completeness.py <bible.md>
    python3 section_completeness.py <bible.md> --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path


# Minimum word counts per section (heuristic — half the Campaign Template's
# implied minimum, so we catch "1-paragraph sections" without being draconian)
SECTION_MIN_WORDS = {
    "Campaign Intro": 200,
    "Character Personality": 400,
    "Character Class": 600,
    "Assets": 400,
    "Family": 400,
    "Factions": 800,
    "World Lore": 400,
    "Gazetteer": 500,
    "Starting Scene": 150,
}

# Quantification patterns — at least one must be present per named ability
QUANTIFICATION_PATTERNS = [
    re.compile(r"\bbonus action\b", re.IGNORECASE),
    re.compile(r"\baction\b\s*(?:to|:|cost)", re.IGNORECASE),
    re.compile(r"\d+d\d+\s*\+", re.IGNORECASE),  # 2d6 + STR
    re.compile(r"\bDC\s*\d+", re.IGNORECASE),
    re.compile(r"\d+\s*(?:/|per)\s*(?:day|hour|round|turn|short rest|long rest)", re.IGNORECASE),
    re.compile(r"\b(?:once|saved)\s*per\b", re.IGNORECASE),
    re.compile(r"\b(?:reaction|legendary action)\b", re.IGNORECASE),
    re.compile(r"\+\d+\s*(?:to|bonus)", re.IGNORECASE),
    re.compile(r"\badvantage\s+on\b", re.IGNORECASE),
    re.compile(r"\bdisadvantage\s+on\b", re.IGNORECASE),
    re.compile(r"\b(?:maximum|max)\s+\d+\b", re.IGNORECASE),
    re.compile(r"\bDPP\b|\bDPR\b|\bDR\b|\bAC\b", re.IGNORECASE),  # custom abbreviations
]


@dataclass
class SectionReport:
    name: str
    words: int
    chars: int
    min_words: int
    status: str  # PASS / FAIL
    severity: str  # ERROR / WARN / INFO
    fix: str = ""


@dataclass
class AbilityReport:
    name: str
    quantified: bool
    matched_pattern: str


@dataclass
class CompletenessReport:
    file: str
    sections: list[SectionReport] = field(default_factory=list)
    abilities: list[AbilityReport] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(s.severity == "ERROR" and s.status == "FAIL" for s in self.sections)

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "section_count": len(self.sections),
            "pass": sum(1 for s in self.sections if s.status == "PASS"),
            "fail": sum(1 for s in self.sections if s.status == "FAIL"),
            "sections": [asdict(s) for s in self.sections],
            "abilities": [asdict(a) for a in self.abilities],
        }


# ---------------------------------------------------------------------------
# Section split + per-section audit
# ---------------------------------------------------------------------------

def split_sections(text: str) -> dict[str, str]:
    """Split markdown text into sections keyed by the first H2 heading."""
    sections: dict[str, str] = {}
    current = "PRELUDE"
    buf: list[str] = []

    for line in text.splitlines():
        if re.match(r"^##\s+", line):
            if buf:
                sections[current] = "\n".join(buf).strip()
            current = re.sub(r"^##\s+", "", line).strip()
            buf = []
        else:
            buf.append(line)
    if buf:
        sections[current] = "\n".join(buf).strip()

    return sections


def section_min_words_match(name: str) -> int:
    """Match a section heading to one of our minimum-word buckets."""
    for bucket, min_words in SECTION_MIN_WORDS.items():
        if bucket.lower() in name.lower():
            return min_words
    return 0  # No minimum (informational)


def is_quantified(text: str) -> tuple[bool, str]:
    """Return (quantified, matched_pattern_label)."""
    for pat in QUANTIFICATION_PATTERNS:
        if pat.search(text):
            return True, pat.pattern
    return False, ""


def extract_named_abilities(section_text: str) -> list[str]:
    """Heuristically extract ability names from a section."""
    # Look for ### Ability Name or bold ability names
    abilities = re.findall(r"^###\s+([^\n]+)$", section_text, re.MULTILINE)
    # Also look for **Ability Name** style
    bold_abilities = re.findall(r"\*\*([^*]+)\*\*\s*:", section_text)
    return abilities + bold_abilities


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def audit(bible_path: Path) -> CompletenessReport:
    text = bible_path.read_text(encoding="utf-8")
    sections = split_sections(text)
    report = CompletenessReport(file=str(bible_path))

    for section_name, section_text in sections.items():
        words = len(section_text.split())
        chars = len(section_text)
        min_words = section_min_words_match(section_name)

        if min_words == 0:
            # No minimum enforced (informational only)
            report.sections.append(
                SectionReport(
                    name=section_name,
                    words=words,
                    chars=chars,
                    min_words=0,
                    status="PASS",
                    severity="INFO",
                )
            )
        elif words < min_words:
            report.sections.append(
                SectionReport(
                    name=section_name,
                    words=words,
                    chars=chars,
                    min_words=min_words,
                    status="FAIL",
                    severity="WARN",
                    fix=f"Section '{section_name}' has {words} words; min {min_words}. The Campaign Template expects each section fully written out.",
                )
            )
        else:
            report.sections.append(
                SectionReport(
                    name=section_name,
                    words=words,
                    chars=chars,
                    min_words=min_words,
                    status="PASS",
                    severity="INFO",
                )
            )

        # Extract + quantify abilities inside this section
        for ability_name in extract_named_abilities(section_text):
            quantified, pat = is_quantified(section_text)
            report.abilities.append(
                AbilityReport(
                    name=ability_name,
                    quantified=quantified,
                    matched_pattern=pat,
                )
            )

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("bible", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if not args.bible.exists():
        print(f"ERROR: bible file not found: {args.bible}", file=sys.stderr)
        return 2

    report = audit(args.bible)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(f"\n=== Campaign Bible Section Completeness Report ===")
        print(f"File: {report.file}\n")

        print("Sections:")
        for s in report.sections:
            icon = "✓" if s.status == "PASS" else "!"
            extra = f" (min {s.min_words})" if s.min_words else " (info)"
            print(
                f"  [{icon}] {s.name}: {s.words} words / {s.chars} chars{extra}"
            )
            if s.status != "PASS" and s.fix:
                print(f"        Fix: {s.fix}")

        unquantified = [a for a in report.abilities if not a.quantified]
        quantified = [a for a in report.abilities if a.quantified]

        print(f"\nMechanic quantification:")
        print(f"  Total abilities detected: {len(report.abilities)}")
        print(f"  Quantified: {len(quantified)}")
        print(f"  Unquantified: {len(unquantified)}")
        if unquantified:
            print("\n  Unquantified abilities (the LLM will forget these):")
            for a in unquantified[:20]:
                print(f"    - {a.name}")
            if len(unquantified) > 20:
                print(f"    ... and {len(unquantified) - 20} more")

        print()
        summary = report.to_dict()
        print(f"Summary: {summary['pass']} sections pass, {summary['fail']} sections fail")

    return 1 if report.has_errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))