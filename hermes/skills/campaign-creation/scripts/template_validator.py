#!/usr/bin/env python3
"""
template_validator.py — Verify a campaign-bible Markdown file conforms to
the structure required by the two canonical Google Doc templates (Campaign
Template + Character Personality Template).

Runs with no LLM. Deterministic. Exits non-zero on any ERROR.

Usage:
    python3 template_validator.py <bible.md>
    python3 template_validator.py <bible.md> --campaign-template <path>
    python3 template_validator.py <bible.md> --personality-template <path>
    python3 template_validator.py <bible.md> --json

Exit codes:
    0  All required items pass
    1  One or more ERROR-level failures
    2  Invalid arguments / file not found
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path


# ---------------------------------------------------------------------------
# Required structure (derived verbatim from the two Google Doc templates)
# ---------------------------------------------------------------------------

# Section 1-9 of the Campaign Template. Each entry is the canonical heading
# phrasing (case-insensitive substring match in the bible).
CAMPAIGN_SECTIONS = [
    "Campaign Intro",
    "Character Personality",
    "Character Class",
    "Assets",
    "Family",
    "Factions",
    "World Lore",
    "Gazetteer",
    "Starting Scene",
]

# Sub-Template A — Standard Character Architecture (6 tiers)
SUBTEMPLATE_A_TIERS = [
    "Core Identity",
    "Psychology",
    "Behavior and Speech",
    "Backstory",
    "Persona vs",
    "Unconscious Beliefs",
]

# Sub-Template B — Faction Structural Profile (5 sections)
SUBTEMPLATE_B_SECTIONS = [
    "Nomenclature",
    "Infrastructure",
    "Leadership",
    "Internal Operational",
    "The Hook",
]

# Sub-Template C — Tactical Masterwork / Relic Framework (4 sections)
SUBTEMPLATE_C_SECTIONS = [
    "Item Name",
    "Aesthetic",
    "Mythic Origin",
    "System Metrics",
]

# Character Personality Template (Part 1, sections I-VI)
PERSONALITY_PART1 = [
    "Core Identity",
    "Psychology",
    "Behavior",
    "Backstory",
    "System Mechanics",
    "Psychological Deep Dive",
]

# Character Personality Template (Part 2, sections I-V)
PERSONALITY_PART2 = [
    "Core Attributes",
    "Combat",
    "Proficiencies",
    "Features, Traits",
    "Inventory",
]

# Psychological Deep Dive sub-sections (9 required)
PSYCHOLOGICAL_DEEP_DIVE_SUBSECTIONS = [
    "Portrait Summary",
    "Composite Psychological",
    "Social Persona vs",
    "Defense-Mechanism",
    "Relational Decoding",
    "Core Unconscious Beliefs",
    "Personal Myth",
    "Break-Point",
    "Closing Pulse",
]

# Family counts
REQUIRED_PARENTS = 2
REQUIRED_BROTHERS = 2
REQUIRED_SISTERS = 2

# Faction counts
REQUIRED_RULING_FACTIONS = 10
REQUIRED_FRIENDLY_FACTIONS = 10
REQUIRED_ANTAGONISTIC_FACTIONS = 10

# Panoply / Retinue
REQUIRED_PANOPLY_MIN = 3
REQUIRED_PANOPLY_MAX = 5
REQUIRED_RETINUE = 3

# Loot table
REQUIRED_LOOT_MIN = 8
REQUIRED_LOOT_MAX = 12


@dataclass
class CheckResult:
    name: str
    status: str  # PASS / FAIL / WARN
    severity: str  # ERROR / WARN / INFO
    message: str
    fix: str = ""


@dataclass
class ValidationReport:
    file: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(c.severity == "ERROR" and c.status == "FAIL" for c in self.checks)

    @property
    def has_warnings(self) -> bool:
        return any(c.severity == "WARN" and c.status == "FAIL" for c in self.checks)

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "pass": sum(1 for c in self.checks if c.status == "PASS"),
            "fail": sum(1 for c in self.checks if c.status == "FAIL"),
            "warn": sum(1 for c in self.checks if c.severity == "WARN" and c.status == "FAIL"),
            "error": sum(1 for c in self.checks if c.severity == "ERROR" and c.status == "FAIL"),
            "checks": [asdict(c) for c in self.checks],
        }


# ---------------------------------------------------------------------------
# Count helpers (regex-based, anchored to the bible text)
# ---------------------------------------------------------------------------

def count_panoply_items(text: str) -> int:
    """Count panoply items within Section 4 (Assets / Panoply).

    Heuristic: H3/H4 lines inside Section 4 that aren't Sub-Template C
    sub-headings ("Aesthetic", "Mythic Origin", etc.).
    """
    sub_template_c_subheadings = {
        "Item Name and Classification",
        "Aesthetic and Material",
        "Mythic Origin",
        "System Metrics",
        "Item Name",
        "Aesthetic",
        "Passive Property",
        "Active Tactical Feature",
        "Narrative Side Effect",
    }
    # Scope to Section 4 (Assets / Panoply)
    section_anchor = None
    for section_name in ["Section 4", "Assets and", "The Panoply"]:
        m = re.search(rf"^##\s+{re.escape(section_name)}", text, re.MULTILINE | re.IGNORECASE)
        if m:
            section_anchor = m.start()
            break
    if section_anchor is None:
        return 0
    # Find the next Section heading
    after = text[section_anchor:]
    next_section = re.search(r"^##\s+(?!#)", after[1:], re.MULTILINE)
    section_end = next_section.start() + 1 if next_section else len(after)
    section_text = after[:section_end]
    items: list[str] = []
    for line in section_text.splitlines():
        m = re.match(r"^#{3,4}\s+(.+)$", line)
        if not m:
            continue
        heading = m.group(1).strip()
        if heading in sub_template_c_subheadings:
            continue
        if heading and heading[0].isupper() and " " in heading and len(heading) < 100:
            items.append(heading)
    return len(items)


def count_section_table_rows(text: str, table_header: str) -> int:
    """Count rows in a Markdown table following the given header."""
    pattern = re.escape(table_header) + r"\s*\n\|[\s\-\|:]+\|"
    match = re.search(pattern, text)
    if not match:
        return 0
    # Count rows after the table header (lines starting with |)
    after = text[match.end():]
    rows = re.findall(r"^\|[^\n]+$", after, re.MULTILINE)
    # Subtract the separator if it leaked in
    return max(0, len(rows))


def count_subsections(text: str, anchor: str) -> int:
    """Count sub-sections under a given anchor section."""
    pattern = re.escape(anchor)
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return 0
    # Look for ### or #### after the anchor up to the next ##
    after = text[match.end():]
    next_section = re.search(r"^##\s", after, re.MULTILINE)
    chunk = after[: next_section.start()] if next_section else after
    subs = re.findall(r"^#{3,4}\s+[^\n]+$", chunk, re.MULTILINE)
    return len(subs)


def section_present(text: str, name: str) -> bool:
    """Case-insensitive substring match for section name."""
    return name.lower() in text.lower()


def all_tier_keywords_present(text: str, keywords: list[str]) -> dict[str, bool]:
    """Return per-keyword presence."""
    return {k: section_present(text, k) for k in keywords}


# ---------------------------------------------------------------------------
# Main validator
# ---------------------------------------------------------------------------

def validate(bible_path: Path) -> ValidationReport:
    report = ValidationReport(file=str(bible_path))
    text = bible_path.read_text(encoding="utf-8")

    # --- 9-section structure ---
    for i, section in enumerate(CAMPAIGN_SECTIONS, 1):
        present = section_present(text, section)
        report.checks.append(
            CheckResult(
                name=f"Section {i}: {section}",
                status="PASS" if present else "FAIL",
                severity="ERROR",
                message=f"Section heading for '{section}' is present"
                if present
                else f"Section heading for '{section}' is missing",
                fix=f"Add a heading like '## Section {i}: {section}' to your bible. Required by Campaign Template.",
            )
        )

    # --- Sub-Template A (used in Section 2 and Section 5 family) ---
    presence = all_tier_keywords_present(text, SUBTEMPLATE_A_TIERS)
    for tier, found in presence.items():
        report.checks.append(
            CheckResult(
                name=f"Sub-Template A tier: {tier}",
                status="PASS" if found else "FAIL",
                severity="ERROR",
                message=f"Tier '{tier}' keyword present"
                if found
                else f"Tier '{tier}' keyword missing — Sub-Template A was not fully applied",
                fix=f"Add a '### {tier}' subsection to Section 2 and Section 5 (family members).",
            )
        )

    # --- Sub-Template B (used in Section 6 ruling factions) ---
    presence = all_tier_keywords_present(text, SUBTEMPLATE_B_SECTIONS)
    for sec, found in presence.items():
        report.checks.append(
            CheckResult(
                name=f"Sub-Template B section: {sec}",
                status="PASS" if found else "WARN",
                severity="WARN",
                message=f"Faction section '{sec}' present"
                if found
                else f"Faction section '{sec}' not detected — Sub-Template B may be incomplete",
                fix="Each ruling faction needs: Nomenclature + Heraldry, Infrastructure + Domain, Leadership Dossier, Internal Operational Culture, The Hook.",
            )
        )

    # --- Sub-Template C (used in Section 4 panoply items) ---
    panoply_items = count_panoply_items(text)
    if panoply_items < REQUIRED_PANOPLY_MIN:
        report.checks.append(
            CheckResult(
                name="Panoply item count",
                status="FAIL",
                severity="ERROR",
                message=f"Detected {panoply_items} panoply items; need {REQUIRED_PANOPLY_MIN}-{REQUIRED_PANOPLY_MAX}",
                fix="Add ### Item Name headings for each panoply item (typically 3-5). Each must use Sub-Template C: Item Name, Aesthetic, Mythic Origin, System Metrics.",
            )
        )
    elif panoply_items > REQUIRED_PANOPLY_MAX:
        report.checks.append(
            CheckResult(
                name="Panoply item count",
                status="FAIL",
                severity="WARN",
                message=f"Detected {panoply_items} panoply items; template requires {REQUIRED_PANOPLY_MIN}-{REQUIRED_PANOPLY_MAX}",
                fix="Trim to 3-5 panoply items. The template explicitly bounds this.",
            )
        )
    else:
        report.checks.append(
            CheckResult(
                name="Panoply item count",
                status="PASS",
                severity="INFO",
                message=f"Detected {panoply_items} panoply items (target {REQUIRED_PANOPLY_MIN}-{REQUIRED_PANOPLY_MAX})",
            )
        )

    # --- Retinue count ---
    retinue = count_subsections(text, "Retinue")
    if retinue < REQUIRED_RETINUE:
        report.checks.append(
            CheckResult(
                name="Retinue member count",
                status="FAIL",
                severity="ERROR",
                message=f"Detected {retinue} retinue sub-sections; template requires exactly {REQUIRED_RETINUE}",
                fix="Add 3 retinue NPCs. Each must use Sub-Template A in full + explicit Loyalty Profile.",
            )
        )
    elif retinue > REQUIRED_RETINUE:
        report.checks.append(
            CheckResult(
                name="Retinue member count",
                status="WARN",
                severity="WARN",
                message=f"Detected {retinue} retinue sub-sections; template prefers exactly {REQUIRED_RETINUE}",
                fix="Trim to 3 retinue NPCs. The template explicitly bounds this.",
            )
        )
    else:
        report.checks.append(
            CheckResult(
                name="Retinue member count",
                status="PASS",
                severity="INFO",
                message=f"Detected {retinue} retinue sub-sections (target {REQUIRED_RETINUE})",
            )
        )

    # --- Personality Template Part 1 ---
    presence = all_tier_keywords_present(text, PERSONALITY_PART1)
    for sec, found in presence.items():
        report.checks.append(
            CheckResult(
                name=f"Personality Part 1: {sec}",
                status="PASS" if found else "FAIL",
                severity="ERROR",
                message=f"Part 1 section '{sec}' present"
                if found
                else f"Part 1 section '{sec}' missing — Personality Template Part 1 was not fully applied",
                fix=f"Add a '## {sec}' section to the Personality Template portion of your bible.",
            )
        )

    # --- Personality Template Part 2 ---
    presence = all_tier_keywords_present(text, PERSONALITY_PART2)
    for sec, found in presence.items():
        report.checks.append(
            CheckResult(
                name=f"Personality Part 2: {sec}",
                status="PASS" if found else "FAIL",
                severity="ERROR",
                message=f"Part 2 section '{sec}' present"
                if found
                else f"Part 2 section '{sec}' missing — Personality Template Part 2 was not fully applied",
                fix=f"Add a '## {sec}' section to the Personality Template Part 2 portion of your bible.",
            )
        )

    # --- Psychological Deep Dive sub-sections ---
    presence = all_tier_keywords_present(text, PSYCHOLOGICAL_DEEP_DIVE_SUBSECTIONS)
    for sec, found in presence.items():
        report.checks.append(
            CheckResult(
                name=f"Deep Dive: {sec}",
                status="PASS" if found else "WARN",
                severity="WARN",
                message=f"Deep dive subsection '{sec}' present"
                if found
                else f"Deep dive subsection '{sec}' missing — the 9 sub-sections of Part 1.VI are required",
                fix="Part 1.VI of the Personality Template has 9 required sub-sections: Portrait Summary, Composite Psychological Sketch, Social Persona vs Repressed Interior, Defense-Mechanism Diagnostics, Relational Decoding, Core Unconscious Beliefs, Personal Myth Narrative, Break-Point Scenario, Closing Pulse.",
            )
        )

    # --- Loot table ---
    loot_rows = count_section_table_rows(text, "| Tactic ")  # fall-back: any table
    # Better: look for explicit "Loot Table" heading
    if not section_present(text, "Loot Table"):
        report.checks.append(
            CheckResult(
                name="Loot Table section",
                status="FAIL",
                severity="WARN",
                message="Section 8 'Loot Table' not detected",
                fix="Add a '### Loot Table' subsection to Section 8 with 8-12 unique non-standard items.",
            )
        )

    # --- Word / line count sanity ---
    word_count = len(text.split())
    if word_count < 1500:
        report.checks.append(
            CheckResult(
                name="Bible length",
                status="FAIL",
                severity="WARN",
                message=f"Bible has {word_count} words; Campaign Template target is ~3,000+ words",
                fix="The Campaign Template specifies ~2,560 tokens / ~1,940 words minimum. Consider expanding sections that were abbreviated.",
            )
        )
    else:
        report.checks.append(
            CheckResult(
                name="Bible length",
                status="PASS",
                severity="INFO",
                message=f"Bible has {word_count} words (target 1,940+ words per Campaign Template)",
            )
        )

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("bible", type=Path, help="Path to the campaign bible Markdown file")
    parser.add_argument(
        "--campaign-template",
        type=Path,
        default=Path(__file__).parent.parent / "references" / "campaign_template.txt",
        help="Path to Campaign Template (cached locally)",
    )
    parser.add_argument(
        "--personality-template",
        type=Path,
        default=Path(__file__).parent.parent / "references" / "personality_template.txt",
        help="Path to Character Personality Template (cached locally)",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args(argv)

    if not args.bible.exists():
        print(f"ERROR: bible file not found: {args.bible}", file=sys.stderr)
        return 2

    report = validate(args.bible)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(f"\n=== Campaign Bible Validation Report ===")
        print(f"File: {report.file}\n")
        for c in report.checks:
            icon = "✓" if c.status == "PASS" else "✗" if c.severity == "ERROR" else "!"
            print(f"  [{icon}] {c.name}: {c.message}")
            if c.status != "PASS" and c.fix:
                print(f"        Fix: {c.fix}")
        print()
        summary = report.to_dict()
        print(
            f"Summary: {summary['pass']} pass, {summary['fail']} fail "
            f"({summary['error']} ERROR, {summary['warn']} WARN)"
        )

    return 1 if report.has_errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))