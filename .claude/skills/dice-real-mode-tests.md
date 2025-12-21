# Dice Real-Mode Tests (MCP)

Use this when validating **dice integrity** end-to-end with real services.

## Script Location

- `testing_mcp/test_dice_rolls_comprehensive.py`

## Required Evidence Standard

Follow `.claude/skills/evidence-standards.md` (Three‑Evidence Rule).

## Preview Server (real mode)

```bash
python testing_mcp/test_dice_rolls_comprehensive.py \
  --server-url https://<preview-app>.run.app/mcp \
  --evidence \
  --evidence-dir /tmp/<your-evidence-dir> \
  --models gemini-3-flash-preview,qwen-3-235b-a22b-instruct-2507
```

Notes:
- Distribution tests will skip if `roll_dice` tool is unavailable on preview.
- Qwen/native_two_phase uses **server tool_results** as authoritative; mismatches are overridden.

## Local MCP (real services)

```bash
python testing_mcp/test_dice_rolls_comprehensive.py \
  --start-local --real-services --evidence --enable-dice-tool \
  --models gemini-3-flash-preview,qwen-3-235b-a22b-instruct-2507 \
  --evidence-dir /tmp/<your-evidence-dir>
```

Outputs:
- `run.json` (scenario results, tool_results, dice_audit_events, warnings)
- `local_mcp_*.log` (server logs)
- `raw_*.txt` (raw model responses when enabled)

## What This Covers

- **Gemini code_execution** path (dice_audit_events source=code_execution).
- **native_two_phase** path (Qwen/Cerebras tool_results).
- **Distribution** tests (1d6 / 1d20) when roll_dice tool is available.
- **Edge cases** (invalid notation, 1d0+5).

## Common Expectations

- `DICE_ROLLS_MISMATCH` / `DICE_AUDIT_MISMATCH` warnings can appear; server overrides with tool_results.
- Final `run.json` should show aligned totals across `dice_rolls`, `dice_audit_events`, and `tool_results`.

## Troubleshooting

- If native_two_phase fails: ensure tool_results are present in responses.
- If mismatch errors appear in `run.json`: check the log and confirm override occurred.
- If distribution tests skip on preview: expected unless `roll_dice` tool is exposed.
