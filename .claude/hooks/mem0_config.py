#!/usr/bin/env python3
"""Shared mem0 config for Claude Code hooks.

Mirrors the openclaw-mem0 plugin settings (collection, embedder, LLM).
Import this in mem0_recall.py and mem0_save.py to keep config in sync.
"""
from __future__ import annotations

import os

MEM0_CONFIG = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": "127.0.0.1",
            "port": 6333,
            "collection_name": "openclaw_mem0",
            "embedding_model_dims": 768,
        },
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "nomic-embed-text",
            "ollama_base_url": "http://localhost:11434",
        },
    },
    "llm": {
        "provider": "groq",
        "config": {
            "model": "llama-3.3-70b-versatile",
            "api_key": os.environ.get("GROQ_API_KEY", ""),
        },
    },
    "version": "v1.1",
}

USER_ID = os.environ.get("USER", "default_user")
