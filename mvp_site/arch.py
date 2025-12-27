"""
Lightweight architecture analysis helpers used by architectural decision tests.

These helpers provide simple, deterministic analysis for local files without
relying on external tooling. They surface key metadata and formatted summaries
expected by the test suite.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent


def analyze_file_architecture(filepath: str) -> dict:
    """Analyze a file and return basic metadata used by tests.

    The implementation intentionally keeps the analysis lightweight: it reads
    the file contents, captures a short preview, and returns counts that act as
    proxies for "patterns" without performing heavyweight static analysis.
    """

    path = Path(filepath)
    if not path.exists():
        return {"filepath": str(path), "error": f"File not found: {path}"}

    try:
        content = path.read_text()
    except OSError as exc:  # pragma: no cover - surfaced as an error payload
        return {"filepath": str(path), "error": str(exc)}

    size_chars = len(content)
    fake_patterns = content.count("def ")
    fake_details = {"function_defs": fake_patterns}
    content_preview = content[:200]

    return {
        "filepath": str(path),
        "size_chars": size_chars,
        "fake_patterns": fake_patterns,
        "fake_details": fake_details,
        "content_preview": content_preview,
        "analysis_scope": "single_file",
    }


def format_architecture_report(scope_data: dict, dual_analysis: dict) -> str:
    """Format a simple architecture report string for display."""

    header = "ARCHITECTURE REVIEW REPORT"
    scope_lines = [
        f"Scope: {scope_data.get('analysis_scope', 'unknown')}",
        f"Branch: {scope_data.get('branch', 'n/a')}",
        f"Files: {', '.join(scope_data.get('changed_files', [])) or 'none'}",
    ]
    analysis_lines = [
        f"Claude: {dual_analysis.get('claude_analysis', '').strip()}",
        f"LLM: {dual_analysis.get('llm_analysis', '').strip()}",
    ]

    body = "\n".join(scope_lines + ["", *analysis_lines])
    return dedent(
        f"""
        {header}
        -------------------------
        {body}
        """
    ).strip()
