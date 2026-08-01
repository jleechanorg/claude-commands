# Subprocess vs Interactive Shell — Why `claudem` fails in pytest/launchd (and how `bash -lic` fixes it)

> Session lesson from the v1.5.0 patch (PR [#800](https://github.com/jleechanorg/jleechanclaw/pull/800), 2026-07-28). v1.1.0 had a `~/bin/claudem` binary shim that bridged the gap; v1.5.0 removed it because (a) it drifted from the bashrc function and (b) `bash -lic` solves the same problem without a second source of truth.

## The failure mode

```bash
$ claudem --version
2.1.220 (Claude Code)             # works — interactive bashrc-sourced shell

$ python3 -c "import subprocess; subprocess.run(['claudem','--version'], capture_output=True)"
FileNotFoundError: [Errno 2] No such file or directory: 'claudem'
# FAILS — Python subprocess inherits the *outer process's* PATH, not the parent shell's function table
```

This is the #1 gotcha when a bashrc function exists. `bash -lic 'claudem …'` works because `-l` (login) forces `~/.bashrc` to source, making the shell function visible inside the spawned `bash`. `python3 -c …` does NOT source any rc file.

## The canonical fix: `bash -lic`

The v1.5.0 solution is to use `bash -lic` from any non-interactive caller. The `-l` (login) flag forces `~/.bashrc` to source inside the spawned bash, which makes the `claudem` function visible:

```bash
# Test from a Python subprocess — replaces subprocess.run(['claudem', ...])
subprocess.run(['bash', '-lic', 'claudem --version'])

# Test from a shell script — replaces claudem --version
bash -lic 'claudem --version'

# From launchd — replace claudem with bash -lic 'claudem …'
# (and use launchd-env-wrapper.sh to inject MINIMAX_API_KEY)

# From a GitHub Actions runner
- run: bash -lic 'claudem -p "..."'
  env:
    MINIMAX_API_KEY: ${{ secrets.MINIMAX_API_KEY }}
```

## Who bites (now that there's no binary)

| Caller | Sees bashrc functions? | Pattern |
|---|---|---|
| Interactive terminal (`bash -i`) | Yes | `claudem --version` |
| `bash -lic '…'` (login shell) | Yes | `bash -lic 'claudem …'` — the canonical pattern |
| `pytest` (`subprocess.run`) | **No** | `subprocess.run(['bash', '-lic', 'claudem …'])` |
| `subprocess.run([...])` from Python/Node/Go | **No** | `subprocess.run(['bash', '-lic', 'claudem …'])` |
| launchd plist (no rc sourcing by default) | **No** | `bash -lic 'claudem …'` + `launchd-env-wrapper.sh` to inject `MINIMAX_API_KEY` |
| AO worker (via `agent-minimax` plugin) | Plugin sets env directly | Plugin path |
| GitHub Actions runner (clean container) | **No** | `bash -lic 'claudem …'` |

## Why not just rename `claudem` to `claudeminimax`?

User asked: "maybe we should use /bin/claudem or have that and it conflicts with bashrc function maybe we just source bashrc or call it bin/claude_minimax or claudeminimax"

The chosen answer was:

1. **Drop the binary entirely.** It drifted from the bashrc function (default-if-unset vs force — see `references/bashrc-global-leak.md`). Single source of truth is better than two sources that have to stay in sync.
2. **Add `claudeminimax` as a bashrc function** (no underscore, matches the `claudeg`/`claudek`/`claudeds`/`claudegz` family form). The function is `claudem "$@"` — pure delegation, no second wrapper.
3. **All non-interactive callers use `bash -lic 'claudem …'`** so the bashrc is sourced and the function is visible. This is what the contract tests in `tests/test_claude_code_claudem.py` do.

The pure-alias contract is enforced by `test_claudeminimax_alias_resolves_to_claudem`; if a future change accidentally makes `claudeminimax` a real second wrapper, the test fails on `'claudem "$@"' not in body`.

## What NOT to do (anti-patterns from this session)

- **DO NOT** ship a `~/bin/claudem` binary. It will drift from the bashrc function, exactly as the v1.1.0–v1.4.0 era proved.
- **DO NOT** set `ANTHROPIC_BASE_URL` / `ANTHROPIC_MODEL` by hand in a wrapper script — always go through `claudem` so the env var scope stays consistent across all callers.
- **DO NOT** clear `CLAUDEM_MODE=1` from a downstream tool — it's the marker that lets downstream code know it's running under the wrapper (not first-party Anthropic).
- **DO NOT** make `claudeminimax` a second wrapper. It must always be `claudem "$@"` (pure bashrc alias).
- **DO NOT** add a binary for `claude_minimax` (with underscore) — use `claudeminimax` (no underscore) to match the family convention.

## See also

- `references/bashrc-global-leak.md` — why the binary drifted and what to do if the bashrc global leaks again.
- `skills/ao-spawn-minimax-worker/SKILL.md` — the AO plugin path (`agent-minimax`) sets env directly without needing bashrc sourcing.
- `skills/claude-code/SKILL.md` (bundled) — the upstream skill body the wrapper thin-clones.
- `hermes-deploy-pipeline/references/launchd-env-injection-and-wrapper.md` — how launchd plists inject the same env vars without sourcing bashrc.
