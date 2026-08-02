# Bashrc global `ANTHROPIC_MODEL` leaks into wrapper shims (and why v1.5.0 dropped the shim entirely)

> Session lesson from the v1.5.0 patch (PR [#800](https://github.com/jleechanorg/jleechanclaw/pull/800), 2026-07-28). The v1.1.0–v1.4.0 era had a `~/bin/claudem` binary shim that DRIFTED from the bashrc function because of the leak pattern documented here. v1.5.0 dropped the binary entirely so there is no longer any surface to drift.

## The bug (v1.1.0–v1.4.0 era)

`~/.bashrc:939` runs `export ANTHROPIC_MODEL="sonnet"` globally so the bare `claude` command defaults to sonnet. This is intentional — `claude --model MiniMax-M3` would otherwise persist MiniMax into `~/.claude/settings.json` and pollute every subsequent bare `claude` run.

The bashrc `claudem()` function (lines 1063-1071 in v1.5.0) is unaffected because shell functions run inline and their env-var prefixes **override** the inherited global at function-call scope.

But `~/bin/claudem` (the binary shim that mirrored the function for subprocess callers in v1.1.0–v1.4.0) had:

```bash
export ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-MiniMax-M3}"   # WRONG
```

When invoked from a pytest subprocess that inherits the parent's `ANTHROPIC_MODEL=sonnet`, the bash default expansion returned `"sonnet"` — the shim exported `"sonnet"` to the wrapped `claude`, the upstream MiniMax-compatible endpoint accepted the model id, and the wrapper answered as `claude-sonnet-5`.

## Reproduction (verified live 2026-07-28, with the v1.1.0–v1.4.0 binary)

```bash
# Parent shell that has sourced bashrc — will print ANTHROPIC_MODEL=sonnet
$ env | grep ^ANTHROPIC_MODEL=
ANTHROPIC_MODEL=sonnet

# With the buggy shim — exit 0 but wrong model identity
$ ANTHROPIC_MODEL=sonnet claudem -p "Output exactly one line: model=<your model>" --max-turns 3 --output-format text 2>&1 \
  | grep -v '^⚠' | grep -v 'claude.ai'
model: claude-sonnet-5          # ← WRONG

# After fixing the shim (replace default-if-unset with force) — exit 0 and correct identity
$ ANTHROPIC_MODEL=sonnet claudem -p "Output exactly: HERMES_CLAUDEM_PR800_GREEN_<ts>" --max-turns 3
HERMES_CLAUDEM_PR800_GREEN_1785279055   # ← actual M3 round-trip
```

## How the test caught it

`tests/test_claude_code_claudem.py::test_claudem_routes_to_minimax_m3` ran `subprocess.run(['claudem', '-p', 'Output exactly one line: model=<your ANTHROPIC_MODEL>', '--max-turns', '3'])`. With the buggy shim, the wrapper inherited `ANTHROPIC_MODEL=sonnet` from the bashrc-sourced shell that launched pytest, and the upstream endpoint answered with `claude-sonnet-5` (which the test correctly rejected via the `if "minimax-m3" in body.lower()` assertion).

Before the fix, the test passed only when pytest was launched from a shell that did NOT export `ANTHROPIC_MODEL` — i.e., the test was *positionally* green but *behaviourally* lying about M3 routing.

## The fix that landed (commit ec72d638c8, v1.4.0)

**File:** `~/bin/claudem` — replace default-if-unset with force:

```diff
-export ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL:-https://api.minimax.io/anthropic}"
+export ANTHROPIC_BASE_URL="https://api.minimax.io/anthropic"
 export ANTHROPIC_AUTH_TOKEN="${MINIMAX_API_KEY}"
 export ANTHROPIC_API_KEY="${MINIMAX_API_KEY}"
-export ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-MiniMax-M3}"
+# Force the model — do NOT inherit ANTHROPIC_MODEL from the parent shell.
+export ANTHROPIC_MODEL="MiniMax-M3"
 export CLAUDE_CODE_ENABLE_EXPERIMENTAL_ADVISOR_TOOL=0
```

`ANTHROPIC_AUTH_TOKEN` and `ANTHROPIC_API_KEY` are intentionally NOT changed — they're keys, not model identities, and bashrc doesn't set them globally (the lines 928-933 block `unset`s them).

## v1.5.0 — drop the binary entirely

After the v1.4.0 fix, the binary was technically correct, but two issues remained:

1. **It still needed to be kept in sync with the bashrc function** every time either changed. The "binary regenerator" script (`scripts/ensure-claudem-binary.sh`) added operational complexity.
2. **It was redundant for every non-interactive caller on this host** — `bash -lic 'claudem …'` sources the bashrc and makes the function visible. There is no caller that genuinely requires a binary.

The v1.5.0 cleanup is therefore to **drop the binary entirely**:

- `~/bin/claudem` is gone (trashed 2026-07-28).
- `~/bin/claude_minimax` and `~/bin/claude_minimaxc` symlinks are gone.
- `scripts/ensure-claudem-binary.sh` and `scripts/verify-claudem-shim-not-leaking.sh` are no longer needed and have been removed from the live skillify.
- The new `claudeminimax` (no underscore, matches the bashrc family) is a pure bashrc function — `claudeminimax() { claudem "$@"; }` — same env vars, same flags, same model.
- All non-interactive callers (pytest, launchd, AO workers, GitHub Actions) use `bash -lic 'claudem …'` so the bashrc is sourced and the function is visible.

## Audit one-liner — find any future shim with the same bug class

```bash
# Find every ~/bin/<wrapper> shim that uses default-if-unset for ANTHROPIC_MODEL
# (silent cross-talk risk if a parent shell exports ANTHROPIC_MODEL=sonnet):
rg --hidden -l 'ANTHROPIC_MODEL=.\$\{ANTHROPIC_MODEL:-' ~/bin 2>/dev/null
# Each hit needs the same fix, or just delete the shim and use bash -lic.
```

Verified clean as of 2026-07-28: zero hits in `~/bin/` because the shim is gone. The `claude-codex-provider-routing/templates/openrouter-claude-shim.sh` template has a similar `${ANTHROPIC_MODEL_OVERRIDE:-<DEFAULT_MODEL>}` form (intentional, but a foot-gun if `ANTHROPIC_MODEL_OVERRIDE` is unset in the parent and the parent's `ANTHROPIC_MODEL=sonnet` global is then inherited by mistake). The umbrella skill `claude-codex-provider-routing` documents this at the class level.

## Verification probe (post-v1.5.0)

```bash
# From a bashrc-sourced shell, must show "model=MiniMax-M3":
bash -lic 'claudem -p "Output exactly one line: model=<your model>" --max-turns 3 --output-format text' 2>&1 \
  | grep -v '^⚠' | grep -v 'claude.ai'

# Plus the canonical marker probe:
bash -lic 'claudem -p "Output exactly: HERMES_CLAUDEM_TEST_$(date +%s)" --max-turns 3'
# Exit 0, marker echoed verbatim.

# And the spelled-out alias:
bash -lic 'claudeminimax -p "Output exactly: HERMES_CLAUDEMINIMAX_TEST_$(date +%s)" --max-turns 3'
# Same result — pure bashrc alias, same env vars, same model.
```

## See also

- SKILL.md pitfall "Subprocess vs interactive-shell behaviour" — the user-facing version of this reference.
- `claude-codex-provider-routing/SKILL.md` pitfall "`ANTHROPIC_MODEL=\"sonnet\"` default protects the bare `claude`" — documents the design intent of the bashrc global.
- `references/subprocess-vs-interactive-shell.md` — the inverse direction (bashrc function invisible to subprocess). This file is about the reverse leak: parent's bashrc global visible to the binary shim.
- `tests/test_claude_code_claudem.py::test_claudem_routes_to_minimax_m3` — the load-bearing contract test that catches this bug.
