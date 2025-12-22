"""Gemini code_execution evidence helpers.

Purpose:
- Provide server-verified detection of Gemini code_execution usage by inspecting
  the SDK response structure (not model self-reporting).
- Produce log-friendly summaries without leaking full prompts/responses.
"""

from __future__ import annotations

import json
from typing import Any

from mvp_site import logging_util


def extract_code_execution_evidence(response: Any) -> dict[str, int | bool | str]:
    """Best-effort detection of Gemini code_execution usage from a raw SDK response.

    We inspect response parts for code_execution artifacts (executable_code /
    code_execution_result) emitted by the Gemini API when the built-in tool is
    actually used.

    Per Consensus ML synthesis: Also validates stdout as JSON when present.
    """
    executable_code_parts = 0
    code_execution_result_parts = 0
    stdout_value = ""
    stdout_is_valid_json = False

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

                    # Extract and validate stdout as JSON (Consensus ML recommendation #3)
                    result = part.code_execution_result
                    output = getattr(result, "output", "")
                    if output:
                        stdout_value = output
                        try:
                            json.loads(output)
                            stdout_is_valid_json = True
                        except (json.JSONDecodeError, TypeError):
                            stdout_is_valid_json = False

    except Exception:
        # If the SDK shape changes, keep this non-fatal.
        return {
            "code_execution_used": False,
            "executable_code_parts": 0,
            "code_execution_result_parts": 0,
            "stdout": "",
            "stdout_is_valid_json": False,
        }

    used = (executable_code_parts + code_execution_result_parts) > 0
    return {
        "code_execution_used": used,
        "executable_code_parts": executable_code_parts,
        "code_execution_result_parts": code_execution_result_parts,
        "stdout": stdout_value,
        "stdout_is_valid_json": stdout_is_valid_json,
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
) -> dict[str, int | bool | str]:
    """Log Gemini code_execution evidence (always INFO, optional DEBUG detail)."""
    evidence = extract_code_execution_evidence(response)
    logging_util.info(
        logging_util.with_campaign(
            "GEMINI_CODE_EXECUTION_PARTS[%s]: model=%s evidence=%s"
        ),
        context,
        model_name,
        evidence,
    )
    if (
        logging_util.getLogger().isEnabledFor(logging_util.DEBUG)
        and evidence.get("code_execution_used")
    ):
        detail = extract_code_execution_parts_summary(response)
        logging_util.debug(
            logging_util.with_campaign(
                "GEMINI_CODE_EXECUTION_PARTS_DETAIL[%s]: model=%s detail=%s"
            ),
            context,
            model_name,
            detail,
        )
    _log_code_execution_dice_results(evidence)
    return evidence


def _log_code_execution_dice_results(evidence: dict[str, int | bool | str]) -> None:
    """Log dice results from Gemini code_execution stdout when JSON is valid."""
    stdout_value = evidence.get("stdout", "")
    if not stdout_value or not evidence.get("stdout_is_valid_json"):
        return

    try:
        parsed = json.loads(str(stdout_value))
    except (json.JSONDecodeError, TypeError, ValueError):
        return

    entries: list[dict[str, Any]] = []
    if isinstance(parsed, dict):
        entries = [parsed]
    elif isinstance(parsed, list):
        entries = [entry for entry in parsed if isinstance(entry, dict)]

    for entry in entries:
        notation = entry.get("notation")
        rolls = entry.get("rolls")
        modifier = entry.get("modifier")
        total = entry.get("total")
        label = entry.get("label")
        if notation is None or not isinstance(rolls, list) or not rolls or total is None:
            continue
        logging_util.info(
            logging_util.with_campaign(
                "DICE_CODE_EXEC_RESULT: notation=%s | rolls=%s | modifier=%s | total=%s | label=%s"
            ),
            notation,
            rolls,
            modifier,
            total,
            label,
        )
