---
name: pairv2-usage
description: How to run pairv2 directly and via the benchmark script, including what "minimax" means as a CLI option
type: usage
scope: project
---

# pairv2 Usage Guide

## What is pairv2?

`pair_execute_v2.py` is a LangGraph-based pair-programming executor. It:
1. Generates left/right contracts (task spec + acceptance criteria) via LLM
2. Launches a **coder** agent to implement the task
3. Launches a **verifier** agent to review the implementation
4. Retries up to `--max-cycles` times if verification fails

Files:
- Executor: `.claude/pair/pair_execute_v2.py`
- Benchmark: `.claude/pair/benchmark_pair_executors.py`
- Contracts: `.claude/contracts/left_contract.template.json`, `right_contract.template.json`

---

## What "minimax" means as `--coder-cli` / `--verifier-cli`

**`minimax` is NOT a CLI binary.** There is no `minimax` command on PATH.

`--coder-cli minimax` means: run the **`claude` CLI binary** with the MiniMax API endpoint injected via environment variables.

The orchestration library (`orchestration/task_dispatcher.py`) handles this:

```python
"minimax": {
    "binary": "claude",           # still the claude CLI
    "env_set": {
        "ANTHROPIC_BASE_URL": "https://api.minimax.io/anthropic",
        "ANTHROPIC_MODEL": "MiniMax-M2.5",
        "ANTHROPIC_API_KEY": "<from MINIMAX_API_KEY>",
    },
    "env_unset": ["ANTHROPIC_AUTH_TOKEN", "CLAUDECODE"],
}
```

Auth is resolved automatically from `$MINIMAX_API_KEY` → `~/.bashrc` → `~/.automation_env`.

Other CLI options work similarly:
- `claude` — Claude Code CLI, direct Anthropic OAuth (no key needed)
- `codex` — OpenAI Codex CLI (`codex exec --yolo`)
- `gemini` — Gemini CLI (`gemini -m <model> --yolo`)
- `cursor` — Cursor CLI (`cursor-agent -f`)

---

## Running pairv2 Directly

```bash
venv/bin/python3 .claude/pair/pair_execute_v2.py \
  --coder-cli minimax \
  --verifier-cli minimax \
  --no-worktree \
  "Your task description here"
```

With explicit contracts:
```bash
venv/bin/python3 .claude/pair/pair_execute_v2.py \
  --coder-cli minimax \
  --verifier-cli codex \
  --left-contract .claude/contracts/left_contract.template.json \
  --right-contract .claude/contracts/right_contract.template.json \
  --no-worktree \
  --max-cycles 3 \
  "Your task description here"
```

Key flags:
| Flag | Default | Description |
|------|---------|-------------|
| `--coder-cli` | `minimax` | Agent that writes code |
| `--verifier-cli` | `codex` | Agent that reviews code |
| `--max-cycles` | `5` | Max retry loops |
| `--no-worktree` | off | Skip git worktree isolation |
| `--live-timeout` | `600` | Heartbeat timeout in seconds |
| `--fan-out` | `1` | Parallel coder attempts |
| `--validate-contracts-only` | off | Check contracts without running agents |

Output JSON is printed to stdout and saved to `--artifact-dir` (default: `/tmp/.../pairv2_latest/`).

---

## Running the Benchmark

The benchmark runs pairv2 (and optionally legacy pair executors) on a task and records timing/verdict.

**Current defaults** (as of Feb 2026):
- Task: "Write hello_world.py + test_hello_world.py"
- Executor set: `pairv2-only`
- Coder CLI: `minimax`
- Verifier CLI: `minimax`

```bash
# Run with all defaults (pairv2-only, minimax+minimax, hello world task)
venv/bin/python3 .claude/pair/benchmark_pair_executors.py

# Custom task
venv/bin/python3 .claude/pair/benchmark_pair_executors.py \
  --task "Implement a Python function that reverses a linked list"

# pairv2 vs legacy pair comparison
venv/bin/python3 .claude/pair/benchmark_pair_executors.py \
  --executor-set legacy-vs-v2 \
  --iterations 2

# All three executors in parallel
venv/bin/python3 .claude/pair/benchmark_pair_executors.py \
  --executor-set all \
  --parallel
```

Key output fields (from result JSON):
```json
{
  "mode": "pairv2_only",
  "pairv2_langgraph": { "avg_ms": 404900, "count": 1 },
  "pairv2_status_counts": { "completed": 1 },
  "pairv2_raw": [{ "verdict": "PASS", "cycle_count": 1, "duration_ms": 404900 }]
}
```

---

## Typical Run Time

- Hello world task: ~5-7 minutes (contract generation + coder + verifier)
- Complex task (800+ lines): ~20-40 minutes

The benchmark imposes a process-level timeout cap of 1800s (30 min).

---

## See Also

- `minimax.md` — MiniMax in the context of PR automation (pr-monitor, fixpr)
- `pair-benchmark-all-executors.md` — Benchmark executor-set reference
- `agents.md` — Agent orchestration patterns
