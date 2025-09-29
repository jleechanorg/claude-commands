"""Shared configuration for Codex automation workflows."""

from __future__ import annotations

from dataclasses import dataclass


DEFAULT_ASSISTANT_HANDLE = "coderabbitai"

# Core instruction template that both shell and Python tooling rely on.
# The assistant handle is injected at runtime so operators can override it
# through the ASSISTANT_HANDLE environment variable.
CODEX_COMMENT_TEMPLATE = (
    "@{assistant_handle} use your judgment to fix comments from everyone or explain "
    "why it should not be fixed. Follow binary response protocol every comment "
    "needs done or not done classification explicitly with an explanation. Push "
    "any commits needed to remote so the PR is updated."
)

CODEX_COMMIT_MARKER_PREFIX = "<!-- codex-automation-commit:"
CODEX_COMMIT_MARKER_SUFFIX = "-->"


def normalise_handle(assistant_handle: str | None) -> str:
    """Return a sanitized assistant handle without a leading '@'."""

    if assistant_handle is None:
        return DEFAULT_ASSISTANT_HANDLE

    # Treat an empty string as "unspecified" so we fall back to the default
    # handle rather than emitting a bare "@" mention in comments.
    cleaned = assistant_handle.lstrip("@")
    return cleaned or DEFAULT_ASSISTANT_HANDLE


def build_default_comment(assistant_handle: str | None = None) -> str:
    """Return the default Codex instruction text for the given handle."""

    handle = normalise_handle(assistant_handle)
    return CODEX_COMMENT_TEMPLATE.format(assistant_handle=handle)


@dataclass(frozen=True)
class CodexConfig:
    """Convenience container for sharing Codex automation constants."""

    assistant_handle: str
    comment_text: str
    commit_marker_prefix: str = CODEX_COMMIT_MARKER_PREFIX
    commit_marker_suffix: str = CODEX_COMMIT_MARKER_SUFFIX

    @classmethod
    def from_env(cls, assistant_handle: str | None) -> "CodexConfig":
        handle = normalise_handle(assistant_handle)
        return cls(
            assistant_handle=handle,
            comment_text=build_default_comment(handle),
        )

