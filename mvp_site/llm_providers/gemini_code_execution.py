"""Gemini code_execution evidence helpers.

Purpose:
- Provide server-verified detection of Gemini code_execution usage by inspecting
  the SDK response structure (not model self-reporting).
- Produce log-friendly summaries without leaking full prompts/responses.
"""

from __future__ import annotations

from typing import Any

from mvp_site import logging_util


def extract_code_execution_evidence(response: Any) -> dict[str, int | bool]:
    """Best-effort detection of Gemini code_execution usage from a raw SDK response.

    We inspect response parts for code_execution artifacts (executable_code /
    code_execution_result) emitted by the Gemini API when the built-in tool is
    actually used.
    """
    executable_code_parts = 0
    code_execution_result_parts = 0

    try:
        candidates = getattr(response, "candidates", None) or []
        for cand in candidates:
            content = getattr(cand, "content", None)
            parts = getattr(content, "parts", None) if content is not None else None
            if not parts:
                continue
            for part in parts:
                if getattr(part, "executable_code", None) is not None:
                    executable_code_parts += 1
                if getattr(part, "code_execution_result", None) is not None:
                    code_execution_result_parts += 1
    except Exception:
        # If the SDK shape changes, keep this non-fatal.
        return {
            "code_execution_used": False,
            "executable_code_parts": 0,
            "code_execution_result_parts": 0,
        }

    used = (executable_code_parts + code_execution_result_parts) > 0
    return {
        "code_execution_used": used,
        "executable_code_parts": executable_code_parts,
        "code_execution_result_parts": code_execution_result_parts,
    }


def extract_code_execution_parts_summary(
    response: Any,
    *,
    max_parts: int = 5,
    max_chars: int = 500,
) -> dict[str, Any]:
    """Extract a compact, log-friendly summary of code_execution parts.

    This is intended for diagnostics only. It avoids logging full prompts or
    full response text; it only captures code_execution-specific artifacts.
    """
    summary: dict[str, Any] = {
        "candidates": 0,
        "parts": 0,
        "executable_code_samples": [],
        "code_execution_result_samples": [],
    }

    def _truncate(value: Any) -> str:
        try:
            text = str(value)
        except Exception:
            return "[unstringifiable]"
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "...(truncated)"

    try:
        candidates = getattr(response, "candidates", None) or []
        summary["candidates"] = len(candidates)
        for cand in candidates:
            content = getattr(cand, "content", None)
            parts = getattr(content, "parts", None) if content is not None else None
            if not parts:
                continue
            for part in parts:
                summary["parts"] += 1
                if len(summary["executable_code_samples"]) < max_parts:
                    executable = getattr(part, "executable_code", None)
                    if executable is not None:
                        # SDK shape varies; capture common fields if present.
                        lang = getattr(executable, "language", None)
                        code = getattr(executable, "code", None)
                        summary["executable_code_samples"].append(
                            {
                                "language": _truncate(lang) if lang is not None else "",
                                "code": _truncate(code)
                                if code is not None
                                else _truncate(executable),
                            }
                        )

                if len(summary["code_execution_result_samples"]) < max_parts:
                    result = getattr(part, "code_execution_result", None)
                    if result is not None:
                        outcome = getattr(result, "outcome", None)
                        output = getattr(result, "output", None)
                        summary["code_execution_result_samples"].append(
                            {
                                "outcome": _truncate(outcome) if outcome is not None else "",
                                "output": _truncate(output)
                                if output is not None
                                else _truncate(result),
                            }
                        )
    except Exception:
        return summary

    return summary


def log_code_execution_parts(
    response: Any,
    *,
    model_name: str,
    context: str,
) -> dict[str, int | bool]:
    """Log Gemini code_execution evidence (always INFO, optional DEBUG detail)."""
    evidence = extract_code_execution_evidence(response)
    logging_util.info(
        "GEMINI_CODE_EXECUTION_PARTS[%s]: model=%s evidence=%s",
        context,
        model_name,
        evidence,
    )
    if logging_util.isEnabledFor(10) and evidence.get("code_execution_used"):
        detail = extract_code_execution_parts_summary(response)
        logging_util.debug(
            "GEMINI_CODE_EXECUTION_PARTS_DETAIL[%s]: model=%s detail=%s",
            context,
            model_name,
            detail,
        )
    return evidence

