"""Shared CLI argument coercion helpers.

These helpers normalize heterogeneous CLI argument inputs into a token list, with
robust fallback behavior when shell-style quoting is malformed.
"""

from __future__ import annotations

import shlex
from typing import Any


def coerce_cli_args(value: Any) -> list[str]:
    """Normalize CLI arg input into a list of string tokens.

    Supported input types:
    - list/tuple: each element converted to str
    - bytes: decoded as UTF-8 with replacement and parsed as CLI text
    - str: parsed via shlex; malformed quoting falls back to simple split
    - other scalar values: converted to a single string token
    """
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        raw_text = value.strip()
        if not raw_text:
            return []
        try:
            return [token for token in shlex.split(raw_text) if token.strip()]
        except ValueError:
            return [token for token in raw_text.split() if token.strip()]
    normalized = str(value)
    return [normalized] if normalized.strip() else []
