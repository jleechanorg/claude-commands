# Pair Benchmark Presets

This directory is the canonical source of truth for pair benchmark task
definitions:

- `benchmark_tasks.json` — task descriptions, expected files, and test commands used by:
  - `.claude/pair/benchmark_pair_executors.py`
  - `testing_llm/pair/run_pair_benchmark.py`

For large benchmarks, long prompts can be moved to dedicated markdown specs in this
directory and referenced through the `spec_file` field in `benchmark_tasks.json`.
When `spec_file` is provided, the loader hydrates the prompt from that file.

When adding/updating pair benchmark tasks, update this file and treat
`testing_llm/pair/benchmark_tasks.json` as a legacy compatibility artifact.
