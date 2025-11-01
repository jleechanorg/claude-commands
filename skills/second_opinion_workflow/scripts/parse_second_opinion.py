#!/usr/bin/env python3
"""Parse AI Universe second opinion responses and print a concise summary."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from textwrap import indent


def load_payload(path: Path) -> dict:
    raw_text = path.read_text()
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to parse JSON from {path}: {exc}") from exc

    if isinstance(data, dict):
        result = data.get("result")
        if isinstance(result, dict):
            content_list = result.get("content")
            if isinstance(content_list, list):
                if not content_list:
                    raise SystemExit("Response contains no content entries to parse.")
                inner = content_list[0]
                if not isinstance(inner, dict):
                    raise SystemExit("Unexpected content entry structure.")
                inner_text = inner.get("text")
                if inner_text is None:
                    raise SystemExit("First content entry is missing 'text'.")
                try:
                    return json.loads(inner_text)
                except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                    raise SystemExit("Embedded JSON payload could not be decoded.") from exc

        if {"primary", "summary"}.issubset(data):
            return data

    raise SystemExit("Unrecognized response format; expected MCP result JSON or parsed payload.")


def summarize(payload: dict) -> str:
    summary = payload.get("summary", {})
    lines = []
    total_models = summary.get("totalModels", "?")
    successful = summary.get("successfulResponses")
    if successful is not None:
        lines.append(f"Models: {total_models} (successful: {successful})")
    else:
        lines.append(f"Models: {total_models}")

    total_tokens = summary.get("totalTokens")
    if total_tokens is not None:
        lines.append(f"Tokens: {total_tokens:,}")

    total_cost = summary.get("totalCost")
    if total_cost is not None:
        lines.append(f"Cost: ${total_cost:.4f}")

    primary = payload.get("primary", {})
    primary_model = primary.get("model", "unknown")
    primary_tokens = primary.get("tokens")
    primary_cost = primary.get("cost")
    header = f"Primary ({primary_model})"
    details = []
    if primary_tokens is not None:
        details.append(f"tokens={primary_tokens:,}")
    if primary_cost is not None:
        details.append(f"cost=${primary_cost:.4f}")
    if details:
        header += f" [{' | '.join(details)}]"
    lines.append("\n" + header)
    response_text = primary.get("response", "<no response>")
    lines.append(indent(response_text.strip(), "  "))

    synthesis = payload.get("synthesis")
    if synthesis is not None:
        synth_model = synthesis.get("model", "synthesis")
        lines.append("\nSynthesis (" + synth_model + ")")
        synth_text = synthesis.get("response", "<no response>")
        lines.append(indent(synth_text.strip(), "  "))

    secondary = payload.get("secondaryOpinions")
    if isinstance(secondary, list) and secondary:
        lines.append("\nSecondary opinions:")
        for opinion in secondary:
            model = opinion.get("model", "unknown")
            resp = opinion.get("response", "<no response>")
            tokens = opinion.get("tokens")
            cost = opinion.get("cost")
            meta = []
            if tokens is not None:
                meta.append(f"tokens={tokens:,}")
            if cost is not None:
                meta.append(f"cost=${cost:.4f}")
            label = f"- {model}"
            if meta:
                label += " (" + ", ".join(meta) + ")"
            lines.append(label)
            lines.append(indent(resp.strip(), "    "))

    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: parse_second_opinion.py PATH_TO_RESPONSE_JSON", file=sys.stderr)
        return 1

    path = Path(argv[1])
    if not path.exists():
        print(f"Error: {path} does not exist.", file=sys.stderr)
        return 1

    payload = load_payload(path)
    print(summarize(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
