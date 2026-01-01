"""Gemini code_execution evidence helpers.

Purpose:
- Provide server-verified detection of Gemini code_execution usage by inspecting
  the SDK response structure (not model self-reporting).
- Produce log-friendly summaries without leaking full prompts/responses.
"""

from __future__ import annotations

import ast
import io
import json
import re
import tokenize
from typing import Any

from mvp_site import logging_util

# RNG patterns to detect actual random number generation in code
_RNG_PATTERNS = (
    "random.randint",
    "random.choice",
    "random.random",
    "random.uniform",
    "random.randrange",
    "random.sample",
    "random.shuffle",
    "secrets.randbelow",
    "secrets.choice",
    "numpy.random.randint",
    "numpy.random.choice",
    "numpy.random.random",
    "numpy.random.uniform",
    "numpy.random.randrange",
    "numpy.random.sample",
    "numpy.random.shuffle",
    "numpy.random.integers",
    "numpy.random.permutation",
    "np.random.randint",
    "np.random.choice",
    "np.random.random",
    "np.random.uniform",
    "np.random.randrange",
    "np.random.sample",
    "np.random.shuffle",
    "np.random.integers",
    "np.random.permutation",
)
_RNG_FUNCTIONS_BY_MODULE = {
    "random": {
        "randint",
        "choice",
        "random",
        "uniform",
        "randrange",
        "sample",
        "shuffle",
    },
    "secrets": {"randbelow", "choice"},
    "numpy.random": {
        "randint",
        "choice",
        "random",
        "uniform",
        "randrange",
        "sample",
        "shuffle",
        "integers",
        "permutation",
    },
}
_SYSTEM_RANDOM_METHODS = {"randint", "randrange", "choice", "random", "uniform"}
_DEFAULT_RNG_METHODS = {"integers", "choice", "random", "uniform", "permutation"}
_RNG_FACTORIES = {"random.SystemRandom", "numpy.random.default_rng"}
_RNG_FALLBACK_REGEXES = (
    re.compile(
        r"\b(random|secrets|numpy\.random|np\.random|np|numpy)\."
        r"(randint|choice|random|uniform|randrange|sample|shuffle|randbelow|integers|permutation)\s*\(",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(random|numpy\.random|np\.random|np|numpy)\."
        r"(SystemRandom|default_rng)\s*\(\)\s*\."
        r"(randint|randrange|choice|random|uniform|integers|permutation)\s*\(",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(SystemRandom|default_rng)\s*\(\)\s*\."
        r"(randint|randrange|choice|random|uniform|integers|permutation)\s*\(",
        re.IGNORECASE,
    ),
)


def _get_call_target(func: ast.AST) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    if not isinstance(func, ast.Attribute):
        return None
    parts = []
    current = func
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    else:
        return None
    return ".".join(reversed(parts))


def _normalize_call_target(target: str, alias_map: dict[str, str]) -> str:
    if "." not in target:
        return target
    prefix, rest = target.split(".", 1)
    if prefix in alias_map:
        return f"{alias_map[prefix]}.{rest}"
    return target


def _strip_code_fences_and_magics(code_text: str) -> str:
    if not code_text:
        return ""
    cleaned_lines: list[str] = []
    for line in code_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            continue
        if stripped.startswith("!") or stripped.startswith("%"):
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def _strip_strings_and_comments(code_text: str) -> str:
    try:
        tokens = tokenize.generate_tokens(io.StringIO(code_text).readline)
    except Exception:
        return code_text
    parts: list[str] = []
    try:
        for tok in tokens:
            if tok.type in (tokenize.STRING, tokenize.COMMENT):
                continue
            parts.append(tok.string)
    except tokenize.TokenError:
        return code_text
    return "".join(parts)


def _regex_contains_rng(code_text: str) -> bool:
    if not code_text:
        return False
    cleaned = _strip_strings_and_comments(code_text)
    return any(pattern.search(cleaned) for pattern in _RNG_FALLBACK_REGEXES)


def _code_contains_rng(code_text: str) -> bool:
    """Check if Python code contains actual RNG calls (not fabricated print statements)."""
    if not code_text:
        return False
    cleaned_text = _strip_code_fences_and_magics(code_text)
    try:
        tree = ast.parse(cleaned_text)
    except SyntaxError:
        return _regex_contains_rng(cleaned_text)

    alias_map: dict[str, str] = {}
    imported_rng_names: set[str] = set()
    system_random_names: set[str] = set()
    default_rng_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if (
                    alias.name in {"random", "secrets", "numpy", "numpy.random"}
                    and alias.asname
                ):
                    alias_map[alias.asname] = alias.name
        elif isinstance(node, ast.ImportFrom):
            module = node.module
            if not module:
                continue
            for alias in node.names:
                name = alias.name
                asname = alias.asname or name
                if module in {"random", "secrets"}:
                    if name == "*":
                        imported_rng_names.update(
                            _RNG_FUNCTIONS_BY_MODULE.get(module, set())
                        )
                    elif name == "SystemRandom":
                        system_random_names.add(asname)
                    elif name in _RNG_FUNCTIONS_BY_MODULE.get(module, set()):
                        imported_rng_names.add(asname)
                elif module == "numpy":
                    if name == "random":
                        alias_map[asname] = "numpy.random"
                elif module == "numpy.random":
                    if name == "*":
                        imported_rng_names.update(
                            _RNG_FUNCTIONS_BY_MODULE.get(module, set())
                        )
                    elif name == "default_rng":
                        default_rng_names.add(asname)
                    elif name in _RNG_FUNCTIONS_BY_MODULE.get(module, set()):
                        imported_rng_names.add(asname)

    system_random_vars: set[str] = set()
    default_rng_vars: set[str] = set()

    def _record_factory_assign(targets: list[ast.AST], value: ast.AST | None) -> None:
        if not isinstance(value, ast.Call):
            return
        call_target = _get_call_target(value.func)
        if not call_target:
            return
        normalized = _normalize_call_target(call_target, alias_map)
        is_system_random = (
            normalized == "random.SystemRandom" or call_target in system_random_names
        )
        is_default_rng = (
            normalized == "numpy.random.default_rng" or call_target in default_rng_names
        )
        if not (is_system_random or is_default_rng):
            return
        for target in targets:
            if isinstance(target, ast.Name):
                if is_system_random:
                    system_random_vars.add(target.id)
                if is_default_rng:
                    default_rng_vars.add(target.id)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            _record_factory_assign(node.targets, node.value)
        elif isinstance(node, ast.AnnAssign):
            _record_factory_assign([node.target], node.value)
        if isinstance(node, ast.Call):
            target = _get_call_target(node.func)
            if not target:
                target = ""
            if target in imported_rng_names:
                return True
            if target:
                normalized = _normalize_call_target(target, alias_map)
                if normalized in _RNG_PATTERNS:
                    return True
                if normalized in _RNG_FACTORIES:
                    # Factory invocation alone doesn't prove RNG usage.
                    pass
            if isinstance(node.func, ast.Attribute):
                attr = node.func.attr
                if isinstance(node.func.value, ast.Call):
                    factory_target = _get_call_target(node.func.value.func)
                    if factory_target:
                        normalized_factory = _normalize_call_target(
                            factory_target, alias_map
                        )
                        if (
                            normalized_factory == "random.SystemRandom"
                            or factory_target in system_random_names
                        ) and attr in _SYSTEM_RANDOM_METHODS:
                            return True
                        if (
                            normalized_factory == "numpy.random.default_rng"
                            or factory_target in default_rng_names
                        ) and attr in _DEFAULT_RNG_METHODS:
                            return True
                elif isinstance(node.func.value, ast.Name):
                    base = node.func.value.id
                    if base in system_random_vars and attr in _SYSTEM_RANDOM_METHODS:
                        return True
                    if base in default_rng_vars and attr in _DEFAULT_RNG_METHODS:
                        return True
    return False


def extract_code_execution_evidence(response: Any) -> dict[str, int | bool | str]:
    """Best-effort detection of Gemini code_execution usage from a raw SDK response.

    We inspect response parts for code_execution artifacts (executable_code /
    code_execution_result) emitted by the Gemini API when the built-in tool is
    actually used.

    Per Consensus ML synthesis: Also validates stdout as JSON when present.

    GREEN FIX (Dec 2024): Now validates executable code contains actual RNG calls
    (random.randint, etc.) to prevent fabrication via direct print statements.
    """
    executable_code_parts = 0
    code_execution_result_parts = 0
    stdout_value = ""
    stdout_is_valid_json = False
    # NOTE: We treat RNG verification as satisfied if ANY executable code part
    # contains RNG usage. This avoids false negatives when separate code parts
    # only set up imports or helpers without directly rolling dice.
    code_contains_rng_call = False
    all_code_samples: list[str] = []

    try:
        candidates = getattr(response, "candidates", None) or []
        for cand in candidates:
            content = getattr(cand, "content", None)
            parts = getattr(content, "parts", None) if content is not None else None
            if not parts:
                continue
            for part in parts:
                executable = getattr(part, "executable_code", None)
                if executable is not None:
                    executable_code_parts += 1
                    # Extract actual code text for RNG validation
                    code_text = getattr(executable, "code", "")
                    if code_text:
                        all_code_samples.append(code_text)
                        if _code_contains_rng(code_text):
                            code_contains_rng_call = True

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
            "code_contains_rng": False,
            "rng_verified": False,
        }

    used = (executable_code_parts + code_execution_result_parts) > 0
    # RNG is verified only if code was executed AND contained actual RNG calls
    rng_verified = used and code_contains_rng_call

    # Log warning if code execution happened without RNG (potential fabrication)
    if used and not code_contains_rng_call:
        code_samples_preview = (
            " | ".join(all_code_samples)[:500] if all_code_samples else "empty"
        )
        logging_util.warning(
            logging_util.with_campaign(
                "🚨 CODE_EXEC_NO_RNG: Code executed but NO random.randint() detected! "
                "LLM may have fabricated dice values via direct print(). "
                f"stdout_is_valid_json={stdout_is_valid_json} "
                f"code_samples={code_samples_preview}"
            )
        )

    return {
        "code_execution_used": used,
        "executable_code_parts": executable_code_parts,
        "code_execution_result_parts": code_execution_result_parts,
        "stdout": stdout_value,
        "stdout_is_valid_json": stdout_is_valid_json,
        "code_contains_rng": code_contains_rng_call,
        "rng_verified": rng_verified,
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
    code_execution_used = False

    def _truncate(value: Any) -> str:
        try:
            text = str(value)
        except Exception:
            return "[unstringifiable]"
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "...(truncated)"

    def _get_part_attr(part: Any, attr: str) -> Any:
        if hasattr(part, "__dict__") and attr not in part.__dict__:
            return None
        return getattr(part, attr, None)

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
                executable = _get_part_attr(part, "executable_code")
                if executable is not None:
                    code_execution_used = True
                    if len(summary["executable_code_samples"]) < max_parts:
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

                result = _get_part_attr(part, "code_execution_result")
                if result is not None:
                    code_execution_used = True
                    if len(summary["code_execution_result_samples"]) < max_parts:
                        outcome = getattr(result, "outcome", None)
                        output = getattr(result, "output", None)
                        summary["code_execution_result_samples"].append(
                            {
                                "outcome": _truncate(outcome)
                                if outcome is not None
                                else "",
                                "output": _truncate(output)
                                if output is not None
                                else _truncate(result),
                            }
                        )
    except Exception:
        return summary

    summary["code_execution_used"] = code_execution_used
    return summary


def log_code_execution_parts(
    response: Any,
    *,
    model_name: str,
    context: str,
) -> dict[str, int | bool | str]:
    """Log Gemini code_execution evidence and executed code (always INFO)."""
    evidence = extract_code_execution_evidence(response)
    logging_util.info(
        logging_util.with_campaign(
            "GEMINI_CODE_EXECUTION_PARTS[%s]: model=%s evidence=%s"
        ),
        context,
        model_name,
        evidence,
    )
    # Always log executed code at INFO level (for /tmp logs and GCP)
    if evidence.get("code_execution_used"):
        detail = extract_code_execution_parts_summary(response, max_chars=2000)
        # Log each executed code sample
        for i, code_sample in enumerate(detail.get("executable_code_samples", [])):
            code_text = code_sample.get("code", "")
            if code_text:
                logging_util.info(
                    logging_util.with_campaign(
                        "GEMINI_EXECUTED_CODE[%s][%d]: model=%s\n%s"
                    ),
                    context,
                    i,
                    model_name,
                    code_text,
                )
        # Add executed code to evidence dict for Firestore storage
        evidence["executed_code"] = [
            sample.get("code", "") for sample in detail.get("executable_code_samples", [])
        ]
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
        if (
            notation is None
            or not isinstance(rolls, list)
            or not rolls
            or total is None
        ):
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
