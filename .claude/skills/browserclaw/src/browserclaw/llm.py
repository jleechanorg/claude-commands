from __future__ import annotations

import json
import os
from typing import Any

import httpx

from .models import BrowserStep, EndpointCatalog


def _extract_json_blob(text: str) -> Any:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()
    start = min(index for index in (text.find("{"), text.find("[")) if index != -1)
    end = max(text.rfind("}"), text.rfind("]"))
    return json.loads(text[start : end + 1])


def _prompt_for_catalog(catalog: EndpointCatalog, goal: str | None = None) -> str:
    payload = json.dumps(catalog.to_dict(), indent=2)
    goal_line = f"Goal: {goal}\n" if goal else ""
    return (
        "You are refining a browser traffic catalog.\n"
        f"{goal_line}"
        "Return strict JSON with keys: notes (list[str]), endpoint_descriptions (object mapping endpoint name to description).\n"
        "Do not invent endpoints. Improve names only through descriptions, not by changing identifiers.\n"
        "Catalog:\n"
        f"{payload}"
    )


def _prompt_for_steps(url: str, goal: str) -> str:
    return (
        "You are planning deterministic browser automation steps.\n"
        "Return strict JSON array using only these actions:\n"
        "- goto {url}\n"
        "- click {selector}\n"
        "- fill {selector, value}\n"
        "- press {selector, value}\n"
        "- wait_for_timeout {milliseconds}\n"
        "- wait_for_url {value}\n"
        "Keep the plan short, and do not include any login or CAPTCHA bypass steps.\n"
        f"Start URL: {url}\n"
        f"Goal: {goal}\n"
    )


def _anthropic_request(prompt: str, model: str, api_key: str) -> str:
    response = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    return "".join(block.get("text", "") for block in payload.get("content", []))


def _openai_request(prompt: str, model: str, api_key: str) -> str:
    response = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"authorization": f"Bearer {api_key}", "content-type": "application/json"},
        json={
            "model": model,
            "temperature": 0,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    return payload["choices"][0]["message"]["content"]


def _gemini_request(prompt: str, model: str, api_key: str) -> str:
    response = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        params={"key": api_key},
        headers={"content-type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    return payload["candidates"][0]["content"]["parts"][0]["text"]


def _run_prompt(prompt: str, provider: str, model: str) -> str:
    provider = provider.lower()
    if provider == "anthropic":
        api_key = os.environ["ANTHROPIC_API_KEY"]
        return _anthropic_request(prompt, model, api_key)
    if provider == "openai":
        api_key = os.environ["OPENAI_API_KEY"]
        return _openai_request(prompt, model, api_key)
    if provider == "gemini":
        api_key = os.environ["GEMINI_API_KEY"]
        return _gemini_request(prompt, model, api_key)
    raise ValueError(f"Unsupported provider: {provider}")


def enrich_catalog(catalog: EndpointCatalog, provider: str, model: str, goal: str | None = None) -> EndpointCatalog:
    prompt = _prompt_for_catalog(catalog, goal=goal)
    payload = _extract_json_blob(_run_prompt(prompt, provider, model))
    description_map = payload.get("endpoint_descriptions", {})
    for endpoint in catalog.endpoints:
        if endpoint.name in description_map:
            endpoint.description = str(description_map[endpoint.name])
    catalog.notes.extend(str(item) for item in payload.get("notes", []))
    catalog.llm_provider = provider
    catalog.llm_model = model
    return catalog


def plan_steps(url: str, goal: str, provider: str, model: str) -> list[BrowserStep]:
    prompt = _prompt_for_steps(url, goal)
    raw_steps = _extract_json_blob(_run_prompt(prompt, provider, model))
    return [BrowserStep(**step) for step in raw_steps]

