---
name: pair-benchmark-all-executors
description: Run one benchmark script that compares pairv2, pair via Claude Teams, and pair via direct Python
type: usage
scope: project
---

# Pair Benchmark (All Executors)

## Purpose
Use one script to benchmark all pair executors:
- `pairv2` (`.claude/pair/pair_execute_v2.py`)
- `/pair` via Claude Teams prompt path
- `/pair` via direct Python (`.claude/pair/pair_execute.py`)

## Script
`./vpython .claude/pair/benchmark_pair_executors.py`

## Quick Start
Run all three executors in one benchmark:

```bash
./vpython .claude/pair/benchmark_pair_executors.py \
  --executor-set all \
  --iterations 1 \
  --timeout-seconds 180 \
  --teams-command "claude --print" \
  --artifact /tmp/{repo}/{branch}/pair/all_three.json
```

Run all three in parallel:

```bash
./vpython .claude/pair/benchmark_pair_executors.py \
  --executor-set all \
  --parallel \
  --iterations 1 \
  --timeout-seconds 180 \
  --teams-command "claude --print" \
  --artifact /tmp/{repo}/{branch}/pair/all_three_parallel.json
```

## Executor Modes
- `--executor-set all`: pair python + pair teams + pairv2
- `--executor-set legacy-vs-v2`: pair python vs pairv2
- `--executor-set teams-vs-v2`: pair teams vs pairv2
- `--executor-set pairv2-only`: pairv2 only

## Key Output Fields
- `pair_python`, `pair_python_status_counts`, `pair_python_raw`
- `pair_claude_teams`, `pair_teams_status_counts`, `pair_teams_raw`
- `pairv2_langgraph`, `pairv2_status_counts`, `pairv2_raw`
- `speedup_ratio_pair_python_over_v2`
- `speedup_ratio_pair_teams_over_v2`
- `speedup_ratio_pair_python_over_teams`

## Notes
- `pairv2` is LangGraph-based (`.claude/pair/pair_execute_v2.py`).
- Artifacts default to `/tmp/{repo}/{branch}/pair/<timestamp>/pair_executor_benchmark.json` when `--artifact` is omitted.
- Use `--coder-cli` and `--verifier-cli` to align model/runtime choices across runs.
