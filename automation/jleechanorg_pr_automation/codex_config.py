"""Shared configuration for Codex automation workflows."""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_ASSISTANT_HANDLE = "coderabbitai"


def compose_assistant_mentions(assistant_handle: str) -> str:
    """Return the canonical mention list for the supplied assistant handle."""

    return f"@codex @{assistant_handle} @copilot @cursor"


DEFAULT_ASSISTANT_MENTIONS = compose_assistant_mentions(DEFAULT_ASSISTANT_HANDLE)

CODEX_COMMENT_INTRO_BODY = (
    "[AI automation] Codex will implement the code updates while {review_assistants_clause} "
    "review support. Please make the following changes to this PR."
)

# Core instruction template with shared AI assistant intro text
CODEX_COMMENT_TEMPLATE = (
    "{comment_intro}\n\n"
    "Use your judgment to fix comments from everyone or explain why it should not be fixed. "
    'Follow binary response protocol - every comment needs "DONE" or "NOT DONE" classification '
    "explicitly with an explanation. Address all comments on this PR. Fix any failing tests and "
    "resolve merge conflicts. Push any commits needed to remote so the PR is updated."
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
    if not marker.startswith('<!--') or not marker.endswith('-->'):
        return None

    # Remove HTML comment markers (slice off "<!--" and "-->")
    content = marker[4:-3].strip()

    # Try new format first: workflow-automation-commit:agent:sha
    if '-automation-commit:' in content and content.count(':') == 2:
        parts = content.split(':')
        workflow = parts[0].replace('-automation-commit', '')
        return {
            'workflow': workflow,
            'agent': parts[1],
            'commit': parts[2]
        }

    # Legacy format: workflow-automation-commit:sha (no agent)
    if '-automation-commit:' in content and content.count(':') == 1:
        parts = content.split(':')
        workflow = parts[0].replace('-automation-commit', '')
        return {
            'workflow': workflow,
            'agent': 'unknown',
            'commit': parts[1]
        }

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
    return [
        token
        for token in tokens
        if token.startswith("@") and token.lower() != "@codex"
    ]


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
    if len(review_assistants) == 1:
        clause = f"{assistants_text} focuses on"
    else:
        clause = f"{assistants_text} focus on"
    intro_body = CODEX_COMMENT_INTRO_BODY.format(
        review_assistants_clause=clause
    )
    intro_prefix = f"{mentions} " if mentions else ""
    return f"{intro_prefix}{intro_body}"


def build_default_comment(assistant_handle: str | None = None) -> str:
    """Return the default Codex instruction text for the given handle."""

    return CODEX_COMMENT_TEMPLATE.format(
        comment_intro=build_comment_intro(assistant_handle=assistant_handle)
    )


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
