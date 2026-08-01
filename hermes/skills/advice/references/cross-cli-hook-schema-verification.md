---
name: cross-cli-hook-schema-verification
description: Provenance record for the 2026-07-15 /advice verification of cross-CLI hook payload field names (Codex / Claude / Gemini / Cursor / OpenCode). Used by `advice` SKILL.md's "Cross-CLI hook schema verification recipe" — re-run the curl loop, do NOT trust this transcript verbatim.
date: 2026-07-15
pr: jleechanorg/merge_train#43
---

# Cross-CLI Hook Schema Verification — 2026-07-15 transcript

This is the cached evidence supporting the `/advice` skill's hook-schema verification recipe. **Do not cite it as fresh evidence.** Re-run the curl loop in `~/.hermes/skills/advice/SKILL.md` and use the new hit/miss counts.

## URLs fetched

| URL | Status | Bytes | Notes |
|---|---|---|---|
| `https://learn.chatgpt.com/docs/hooks.md` | 200 | 30,584 | Codex hook docs |
| `https://geminicli.com/docs/hooks/reference/` | 200 | 119,914 | Gemini hook reference |
| `https://geminicli.com/docs/hooks/best-practices/` | 200 | 119,946 | Gemini best practices |
| `https://opencode.ai/docs/tools/` | 200 | 101,084 | OpenCode tool docs |

## Field-name hit counts

| Field | learn.chatgpt.com | geminicli.com (ref) | geminicli.com (bp) | opencode.ai |
|---|---|---|---|---|
| `write_to_file` | MISS | MISS | MISS | MISS |
| `write_file` | MISS | MISS | MISS | MISS |
| `replace` | HIT @ 1707 | HIT @ 2882 (in JS bundle, not docs) | n/a | HIT @ 3840 (in JS bundle, not docs) |
| `apply_patch` | HIT @ 10185 | MISS | MISS | HIT @ 38423 (TOC anchor) |
| `patchText` | MISS | MISS | MISS | HIT @ 70477 |
| `additionalContext` | HIT @ 14996 | HIT (in nav chrome) | MISS | MISS |
| `permissionDecisionReason` | HIT @ 18198 | MISS | MISS | MISS |
| `statusMessage` | HIT @ 3647 | MISS | MISS | MISS |
| `timeout` | HIT @ 5173 | HIT (in nav chrome) | MISS | MISS |

## Decision points

- `write_to_file` is NOT documented as a hook-layer tool name in any of the four fetched vendor doc sets. Antigravity / AGY exposes `write_to_file` at the **application layer**, not the hook layer. Do NOT add it to `_MUTATION_TOOLS` on the strength of Antigravity docs alone — there is no hook-level evidence it ever fires.
- `apply_patch` paths in OpenCode come from `patchText`, NOT `command`. The `opencode-conflict-plugin.js` reads `args.patchText` first, which is correct.
- Codex rejects legacy top-level `decision:"approve"`. Use `hookSpecificOutput.permissionDecision` only. Confirmed at learn.chatgpt.com/docs/hooks.md line 14996+ (additionalContext) and line 18198 (permissionDecisionReason).
- Codex `timeout` default is 600s (HIT @ 5173). The PR uses 15s (Codex) and 15000ms (Gemini). Both well under the documented cap, both safe.

## Reviewer B confidence downgrade

Reviewer B's "medium confidence" verdict in the 2026-07-15 synthesis was driven specifically by the fact that `write_to_file` / `apply_patch` schema-version drift could not be externally verified beyond the four URLs above. Future reviews should re-run the curl loop and check for new field names before quoting this transcript.

## Reproducibility

```bash
mkdir -p /tmp/advice-hooks && cd /tmp/advice-hooks
for url in \
  "https://learn.chatgpt.com/docs/hooks.md" \
  "https://geminicli.com/docs/hooks/reference/" \
  "https://geminicli.com/docs/hooks/best-practices/" \
  "https://opencode.ai/docs/tools/"; do
  fname=$(echo "$url" | sed -E 's|https?://([^/]+)/.*|\1|; s|\.|_|g').txt
  curl -fsS "$url" -o "$fname" || echo "FAIL $url"
done
```

If any URL returns non-200, drop it from the table and note the gap in the reviewer's confidence rating — do not extrapolate.
