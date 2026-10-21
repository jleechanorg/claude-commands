#!/usr/bin/env bash
exec pi --provider openai-codex --model gpt-6-luna --thinking medium "$@"
