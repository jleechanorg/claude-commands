"""Shared configuration for Codex automation workflows."""

from __future__ import annotations

import re
from dataclasses import dataclass

DEFAULT_ASSISTANT_HANDLE = "coderabbitai"
AUTOMATION_MARKER_NEW_FORMAT_COLONS = 2
AUTOMATION_MARKER_LEGACY_FORMAT_COLONS = 1

# Centralized list of ALL automation workflow names.
# These are used in commit message patterns like [workflow-actor-automation-commit]
# CRITICAL: When adding a new workflow, add it here to automatically enable
# commit message detection across all detection points.
AUTOMATION_WORKFLOW_NAMES: tuple[str, ...] = (
    "codex",
    "fixpr",
    "fixcomment",
    "comment-validation",
)

# Centralized list of ALL automation actor keywords (CLI tools).
# These are the actors that can run automation workflows.
AUTOMATION_ACTOR_KEYWORDS: tuple[str, ...] = (
    "codex",
    "gemini",
    "cursor",
    "copilot",
    "claude",
    "minimax",
    "coderabbit",
    "coderabbitai",
)


def build_automation_commit_message_pattern() -> re.Pattern[str]:
    """Build a centralized regex pattern that matches ALL automation commit message markers.

    Matches patterns like:
    - [codex-automation-commit]
    - [fixpr-automation-commit]
    - [fixcomment-automation-commit]
    - [comment-validation-automation-commit]
    - [fixpr gemini-automation-commit]  (workflow with actor)
    - [codex cursor-automation-commit]

    Returns:
        Compiled regex pattern for matching automation commit messages.
    """
    # Build pattern to match all automation commit message formats:
    # - [codex-automation-commit]         (actor only)
    # - [fixpr-automation-commit]         (workflow only)
    # - [fixcomment-automation-commit]    (workflow only)
    # - [comment-validation-automation-commit] (workflow only)
    # - [fixpr codex-automation-commit]   (workflow + actor)
    # - [fixpr gemini-automation-commit]  (workflow + actor)
    # Combine actors and workflows into one list for simpler matching
    # Use a set to remove duplicates (e.g., 'codex' appears in both), and sort for deterministic regex output.
    all_keywords_list = sorted(set(list(AUTOMATION_ACTOR_KEYWORDS) + list(AUTOMATION_WORKFLOW_NAMES)))
    all_keywords = "|".join(re.escape(kw) for kw in all_keywords_list)

    # Pattern: [ (optional keyword1) (optional keyword2) ... -automation-commit]
    # The key insight is we just need to match ANY of the keywords followed eventually by -automation-commit
    # This handles all formats: [codex-], [fixpr-], [fixpr codex-], [fixpr gemini-], etc.
    pattern_str = rf"\[(?:\s*(?:{all_keywords})\s*)+\s*-automation-commit\]"

    return re.compile(pattern_str, re.IGNORECASE)


# Pre-compiled pattern for performance
AUTOMATION_COMMIT_MESSAGE_PATTERN = build_automation_commit_message_pattern()


def is_automation_commit_message(message: str | None) -> bool:
    """Check if a commit message contains any automation marker.

    This is the centralized function for detecting automation-authored commits
    via their commit messages.

    Args:
        message: The commit message to check.

    Returns:
        True if the message contains an automation marker, False otherwise.
    """
    if message is None or not isinstance(message, str):
        return False
    return AUTOMATION_COMMIT_MESSAGE_PATTERN.search(message) is not None


def compose_assistant_mentions(assistant_handle: str) -> str:
    """Return the canonical mention list for the supplied assistant handle."""

    return f"@codex @{assistant_handle} @cursor @copilot"


DEFAULT_ASSISTANT_MENTIONS = compose_assistant_mentions(DEFAULT_ASSISTANT_HANDLE)

CODEX_COMMENT_INTRO_BODY = (
    "[AI automation] Codex will implement the code updates while {review_assistants_clause} "
    "review support. Please make the following changes to this PR."
)

# Shared tracking instruction text (used in both comment templates and monitor functions)
CODEX_TRACKING_INSTRUCTION = (
    "For comment tracking and auditability, include html_url for each response item in responses.json and "
    "generate a [codex-automation-commit] tracking commit message that separates FIXED vs CONSIDERED "
    "(ACKNOWLEDGED/DEFERRED/NOT_DONE) comment URLs."
)

# Core instruction template with shared AI assistant intro text
CODEX_COMMENT_TEMPLATE = (
    "{comment_intro}\n\n"
    "Use your judgment to fix comments from everyone or explain why it should not be fixed. "
    "Use /commentreply to post ONE consolidated summary with all responses (avoids GitHub rate limits). "
    "Address all comments on this PR. Fix any failing tests and "
    "resolve merge conflicts. Push any commits needed to remote so the PR is updated.\n\n"
    f"{CODEX_TRACKING_INSTRUCTION}"
)

CODEX_COMMIT_MARKER_PREFIX = "<!-- codex-automation-commit:"
CODEX_COMMIT_MARKER_SUFFIX = "-->"
FIX_COMMENT_MARKER_PREFIX = "<!-- fix-comment-automation-commit:"
FIX_COMMENT_MARKER_SUFFIX = "-->"
# Updated to match new format from build_automation_marker()
FIX_COMMENT_RUN_MARKER_PREFIX = "<!-- fix-comment-run-automation-commit:"
FIX_COMMENT_RUN_MARKER_SUFFIX = "-->"
# Updated to match new format from build_automation_marker()
FIXPR_MARKER_PREFIX = "<!-- fixpr-run-automation-commit:"
FIXPR_MARKER_SUFFIX = "-->"
COMMENT_VALIDATION_MARKER_PREFIX = "<!-- comment-validation-commit:"
COMMENT_VALIDATION_MARKER_SUFFIX = "-->"

# Centralized tuple of ALL automation marker prefixes.
# CRITICAL: When adding a new marker, add it here to automatically enable
# feedback loop prevention across all detection points.
ALL_AUTOMATION_MARKER_PREFIXES: tuple[str, ...] = (
    CODEX_COMMIT_MARKER_PREFIX,
    FIX_COMMENT_MARKER_PREFIX,
    FIX_COMMENT_RUN_MARKER_PREFIX,
    FIXPR_MARKER_PREFIX,
    COMMENT_VALIDATION_MARKER_PREFIX,
)


def is_automation_comment(body: str | None) -> bool:
    """Check if a comment body contains any automation marker.

    This is the single source of truth for automation comment detection.
    Use this function instead of manually checking individual markers.

    Args:
        body: Comment body text (can be None)

    Returns:
        True if the comment contains any automation marker prefix
    """
    if not body:
        return False
    return any(prefix in body for prefix in ALL_AUTOMATION_MARKER_PREFIXES)


def build_automation_marker(workflow: str, agent: str, commit_sha: str) -> str:
    """Build enhanced automation marker with workflow, agent, and commit info.

    Args:
        workflow: Workflow type (e.g., 'fix-comment-run', 'fixpr-run', 'codex')
        agent: Agent/CLI name (e.g., 'gemini', 'codex', 'claude')
        commit_sha: Git commit SHA

    Returns:
        HTML comment marker with format: <!-- workflow-automation-commit:agent:sha -->

    Example:
        >>> build_automation_marker('fix-comment-run', 'gemini', 'abc123')
        '<!-- fix-comment-run-automation-commit:gemini:abc123-->'
    """
    return f"<!-- {workflow}-automation-commit:{agent}:{commit_sha}-->"


def parse_automation_marker(marker: str) -> dict[str, str] | None:
    """Parse automation marker to extract workflow, agent, and commit.

    Args:
        marker: Automation marker string

    Returns:
        Dict with 'workflow', 'agent', 'commit' keys, or None if invalid

    Example:
        >>> parse_automation_marker('<!-- fix-comment-automation-commit:gemini:abc123-->')
        {'workflow': 'fix-comment', 'agent': 'gemini', 'commit': 'abc123'}
    """
    if not marker.startswith("<!--") or not marker.endswith("-->"):
        return None

    # Remove HTML comment markers (slice off "<!--" and "-->")
    content = marker[4:-3].strip()

    # Try new format first: workflow-automation-commit:agent:sha
    if "-automation-commit:" in content and content.count(":") == AUTOMATION_MARKER_NEW_FORMAT_COLONS:
        parts = content.split(":")
        workflow = parts[0].replace("-automation-commit", "")
        return {"workflow": workflow, "agent": parts[1], "commit": parts[2]}

    # Legacy format: workflow-automation-commit:sha (no agent)
    if "-automation-commit:" in content and content.count(":") == AUTOMATION_MARKER_LEGACY_FORMAT_COLONS:
        parts = content.split(":")
        workflow = parts[0].replace("-automation-commit", "")
        return {"workflow": workflow, "agent": "unknown", "commit": parts[1]}

    return None


def normalise_handle(assistant_handle: str | None) -> str:
    """Return a sanitized assistant handle without a leading '@'."""

    if assistant_handle is None:
        return DEFAULT_ASSISTANT_HANDLE

    # Treat an empty string as "unspecified" so we fall back to the default
    # handle rather than emitting a bare "@" mention in comments.
    cleaned = assistant_handle.lstrip("@")
    return cleaned or DEFAULT_ASSISTANT_HANDLE


def _extract_review_assistants(assistant_mentions: str) -> list[str]:
    """Return the assistant mentions that participate in review support."""

    tokens = assistant_mentions.split()
    return [token for token in tokens if token.startswith("@") and token.lower() != "@codex"]


def _format_review_assistants(review_assistants: list[str]) -> str:
    """Return a human readable list of review assistants for prose usage."""

    if not review_assistants:
        return "the review assistants"

    # Strip leading "@" handles so we don't ping reviewers twice inside the prose.
    prose_names = [assistant.lstrip("@") or assistant for assistant in review_assistants]

    if len(prose_names) == 1:
        return prose_names[0]

    if len(prose_names) == 2:
        return f"{prose_names[0]} and {prose_names[1]}"

    return ", ".join(prose_names[:-1]) + f", and {prose_names[-1]}"


def build_comment_intro(
    assistant_mentions: str | None = None,
    assistant_handle: str | None = None,
) -> str:
    """Return the shared Codex automation intro text for comment bodies."""

    mentions = assistant_mentions
    if mentions is None:
        mentions = compose_assistant_mentions(normalise_handle(assistant_handle))
    review_assistants = _extract_review_assistants(mentions)
    assistants_text = _format_review_assistants(review_assistants)
    clause = f"{assistants_text} focuses on" if len(review_assistants) == 1 else f"{assistants_text} focus on"
    intro_body = CODEX_COMMENT_INTRO_BODY.format(review_assistants_clause=clause)
    intro_prefix = f"{mentions} " if mentions else ""
    return f"{intro_prefix}{intro_body}"


def build_default_comment(assistant_handle: str | None = None) -> str:
    """Return the default Codex instruction text for the given handle."""

    return CODEX_COMMENT_TEMPLATE.format(comment_intro=build_comment_intro(assistant_handle=assistant_handle))


@dataclass(frozen=True)
class CodexConfig:
    """Convenience container for sharing Codex automation constants."""

    assistant_handle: str
    comment_text: str
    commit_marker_prefix: str = CODEX_COMMIT_MARKER_PREFIX
    commit_marker_suffix: str = CODEX_COMMIT_MARKER_SUFFIX

    @classmethod
    def from_env(cls, assistant_handle: str | None) -> CodexConfig:
        handle = normalise_handle(assistant_handle)
        return cls(
            assistant_handle=handle,
            comment_text=build_default_comment(handle),
        )
