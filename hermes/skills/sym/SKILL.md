---
name: sym
version: 1.0.0
description: Route tasks to the launchd-managed Symphony daemon when the user says "sym".
---

# sym

Use this skill when the user's message contains the word **sym**.

## Goal

Dispatch coding tasks through the local Symphony daemon instead of mctrl/agento.

## Commands

Freeform task dispatch:

```bash
scripts/sym-dispatch.sh "<task text>"
```

Plugin dispatch:

```bash
scripts/sym-dispatch.sh --plugin <plugin_name> <input_json>
```

Install or repair daemon:

```bash
scripts/install-symphony-daemon.sh
```

## Plugin examples

```bash
scripts/sym-send-5-leetcode-hard.sh
scripts/sym-send-5-swebench-verified.sh
```

## Behavior contract

1. Parse the task text that follows `sym`.
2. Run `scripts/sym-dispatch.sh` with that task.
3. Reply with a concrete dispatch result (plugin, issue count, queue status).
4. If daemon metadata is missing, install daemon first via `scripts/install-symphony-daemon.sh`.
5. `memory_tracker_issues` RPC enqueue is benchmark-only by default for direct `enqueue-symphony-tasks.sh` calls (`SYMPHONY_MEMORY_QUEUE_MODE=benchmark-only`), while freeform `scripts/sym-dispatch.sh "<task>"` sets `SYMPHONY_MEMORY_QUEUE_MODE=always` unless explicitly overridden.

## Post-merge

After editing this `hermes-config` file, sync it to `~/.hermes/` and reload the gateway:

```bash
kill -HUP $(pgrep -f hermes gateway)
```

This is required for live routing changes used by `scripts/install-symphony-daemon.sh` and `scripts/sym-dispatch.sh`.
