#!/usr/bin/env python3
"""Shared mem0 config for Claude Code hooks.

Mirrors the hermes-mem0 plugin settings (collection, embedder, LLM).
Import this in mem0_recall.py and mem0_save.py to keep config in sync.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Match ~/.hermes/hermes.json plugins.entries.hermes-mem0.config.oss
_OLLAMA_BASE = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
_DEFAULT_OLLAMA_LLM = os.environ.get("MEM0_OLLAMA_LLM_MODEL", "gemma2:2b")

_CAMEL_TO_SNAKE = {
    "apiKey": "api_key",
    "modelName": "model_name",
    "embeddingDims": "embedding_dims",
    "embeddingModelDims": "embedding_model_dims",
    "collectionName": "collection_name",
    "ollamaBaseUrl": "ollama_base_url",
}


def _expand_env_vars(v: str) -> str:
    """Expand environment variables in a string. Returns empty if unexpanded."""
    if not v:
        return v
    expanded = os.path.expandvars(v)
    # If expansion failed (remains $VAR or ${VAR}), treat as empty to avoid
    # using literal "$KEY" as an actual API key.
    if "$" in expanded and re.match(r"^\$[A-Za-z0-9_]+$|^\$\{[A-Za-z0-9_]+\}$", expanded):
        return ""
    return expanded


def _hermes_config_path() -> Path:
    raw = os.environ.get("HERMES_CONFIG_PATH")
    if raw:
        return Path(os.path.expanduser(raw))
    return Path.home() / ".hermes" / "hermes.json"


def _normalize_embedder_block(emb: dict) -> dict | None:
    """Map hermes `oss.embedder` (camelCase ok) to mem0 Memory embedder dict."""
    if not emb or not isinstance(emb, dict):
        return None
    prov = (emb.get("provider") or "").strip()
    raw_cfg = emb.get("config") or {}
    if not isinstance(raw_cfg, dict):
        raw_cfg = {}
    cfg: dict = {}
    for k, v in raw_cfg.items():
        kk = _CAMEL_TO_SNAKE.get(k, k)
        if isinstance(v, str):
            v = _expand_env_vars(v)
        cfg[kk] = v
    if not prov:
        return None
    return {"provider": prov, "config": cfg}


def _merge_mem0_from_hermes_json() -> None:
    """Override MEM0_CONFIG embedder (and Qdrant dims) from hermes.json when present.

    Keeps hooks aligned with scripts/mem0_shared_client.py and the gateway.
    """
    global MEM0_CONFIG
    try:
        path = _hermes_config_path()
        if not path.is_file():
            mem0_path = Path.home() / ".hermes" / "mem0.json"
            if not mem0_path.is_file():
                return
            data = json.loads(mem0_path.read_text(encoding="utf-8"))
            MEM0_CONFIG["embedder"] = {
                "provider": "ollama",
                "config": {
                    "model": data.get("embedder_model", "nomic-embed-text"),
                    "ollama_base_url": data.get("ollama_base", _OLLAMA_BASE),
                    "embedding_dims": int(data.get("embedder_dims", 768)),
                },
            }
            MEM0_CONFIG["llm"] = {
                "provider": "ollama",
                "config": {
                    "model": data.get("llm_model", _DEFAULT_OLLAMA_LLM),
                    "ollama_base_url": data.get("ollama_base", _OLLAMA_BASE),
                    "temperature": 0,
                },
            }
            MEM0_CONFIG["vector_store"]["config"].update(
                {
                    "host": str(data.get("qdrant_host", "localhost")).replace("http://", "").replace("https://", ""),
                    "port": int(data.get("qdrant_port", 6333)),
                    "collection_name": data.get("collection", "hermes_mem0"),
                    "embedding_model_dims": int(data.get("embedder_dims", 768)),
                }
            )
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        oss = (
            data.get("plugins", {})
            .get("entries", {})
            .get("hermes-mem0", {})
            .get("config", {})
            .get("oss")
        )
        if not isinstance(oss, dict):
            return
        ne = _normalize_embedder_block(oss.get("embedder") or {})
        if ne:
            MEM0_CONFIG["embedder"] = ne
        vs = oss.get("vectorStore") or oss.get("vector_store")
        if isinstance(vs, dict):
            vcfg = vs.get("config") or {}
            dst = MEM0_CONFIG["vector_store"]["config"]
            for src_key, dst_key in (
                ("host", "host"),
                ("port", "port"),
                ("collectionName", "collection_name"),
                ("collection_name", "collection_name"),
                ("embeddingModelDims", "embedding_model_dims"),
                ("embedding_model_dims", "embedding_model_dims"),
            ):
                if src_key not in vcfg or vcfg[src_key] is None:
                    continue
                value = vcfg[src_key]
                if isinstance(value, str):
                    value = _expand_env_vars(value)
                if dst_key in {"port", "embedding_model_dims"}:
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        continue
                dst[dst_key] = value
    except Exception as exc:
        if os.environ.get("MEM0_HOOKS_DEBUG") == "1":
            print(f"[mem0_config] Failed to merge hermes config: {exc}", file=sys.stderr)


MEM0_CONFIG = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": "127.0.0.1",
            "port": 6333,
            "collection_name": "hermes_mem0",
            "embedding_model_dims": 768,
        },
    },
    # Gateway uses OpenAI text-embedding-3-small @ 768 dims (same Qdrant collection)
    "embedder": {
        "provider": "openai",
        "config": {
            "model": "text-embedding-3-small",
            "api_key": os.environ.get("OPENAI_API_KEY", ""),
            "embedding_dims": 768,
        },
    },
    "llm": {
        "provider": "ollama",
        "config": {
            "model": _DEFAULT_OLLAMA_LLM,
            "ollama_base_url": _OLLAMA_BASE,
            "temperature": 0,
        },
    },
    "version": "v1.3",
}

USER_ID = "$USER"


def mem0_hooks_enabled() -> bool:
    """Whether Claude Code hooks should invoke mem0 (recall / save).

    Ollama LLM needs no API key. OpenAI embedder needs OPENAI_API_KEY (or api_key in config).
    """
    llm = MEM0_CONFIG.get("llm", {})
    lprov = (llm.get("provider") or "").lower()
    if lprov != "ollama":
        lcfg = llm.get("config") or {}
        if not (lcfg.get("api_key") or "").strip():
            return False

    emb = MEM0_CONFIG.get("embedder", {})
    eprov = (emb.get("provider") or "").lower()
    ecfg = emb.get("config") or {}
    if eprov == "ollama":
        return True
    if eprov == "openai":
        key = (ecfg.get("api_key") or os.environ.get("OPENAI_API_KEY", "") or "").strip()
        return bool(key)
    key = (ecfg.get("api_key") or "").strip()
    return bool(key)


_merge_mem0_from_hermes_json()
