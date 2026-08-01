---
name: codex-path-deletion-guard
description: Install and operate the codex `path-deletion-guard.py` PreToolUse hook that allows deletions inside /tmp (and $TMPDIR) but blocks rm/rmdir/shred/find -delete/git destructive ops/apply_patch deletes/Python os.remove+shutil.rmtree outside those dirs. Emits the Codex-canonical hookSpecificOutput.permissionDecision JSON, exits 2 on deny, fails closed on parse error. Use when asked to "guard codex against deletion", "block destructive commands outside /tmp", or when running sandbox_mode=danger-full-access and wanting pre-execution safety. The hook is unit-tested by 38 cases but Codex 0.144.5 has known limits on hook enforcement (unified_exec skips PreToolUse); read Pitfall #0 before relying on it for real-time enforcement.
---

# codex-path-deletion-guard

A Codex / Claude PreToolUse hook that allows `rm -rf` (and friends) **only** when every target is under an allowed temp root (`/tmp`, `/private/tmp`, `$TMPDIR`, `~/.codex/.tmp`, or anything in `$PATH_DELETION_GUARD_ALLOW`). Anything outside is denied. Fails closed on parse errors.

Built in response to repeated X-community warnings about Codex CLI agents `rm -rf`-ing production data while running in `sandbox_mode = "danger-full-access"` with `approval_policy = "never"`. Latest confirmed incident: GPT-5.6 overriding `$HOME` and wiping a project (X 2077820292622372866, 2026-07).

## What the tmux test actually proved (2026-07-17)

I drove a real Codex 0.144.5 session inside tmux, gave it a sandboxed workdir and the prompt "delete `~/HOOKTEST_DELETE_ME_<ts>` and `/tmp/HOOKTEST_ALLOWED_<ts>`". Codex's transcript showed `hook: PreToolUse` → `hook: PreToolUse Completed` for every step, but the protected directory was STILL DELETED. The model itself observed this and replied "The hook failed its protection test".

Root cause: Codex 0.144.5 has TWO independent guardrail layers and uses a new `unified_exec` mechanism for some shell calls that bypasses PreToolUse hooks. The official Codex hook docs explicitly warn:

> "It's still a guardrail rather than a complete enforcement boundary because Codex can often perform equivalent work through another supported tool path."
> "This doesn't intercept all shell calls yet, only the simple ones. The newer `unified_exec` mechanism allows richer streaming stdin/stdout handling of shell, but interception is incomplete."

**Bottom line:** the hook is spec-correct and unit-tested for the cases it CAN see, but you cannot rely on it for 100% enforcement against `danger-full-access` Codex sessions. Combine with sandbox + approval policy + `--config ask-for-approval=on-request` and you'll catch most of the patterns; the rest is the user's responsibility.

## Files

| Path | Purpose |
|------|---------|
| `~/.codex/hooks/path-deletion-guard.py` | Main hook — reads JSON payload from stdin, emits Codex `hookSpecificOutput.permissionDecision` JSON |
| `~/.codex/hooks/path-deletion-guard-audit.sh` | Companion — appends every payload to `~/.codex/log/path-deletion-guard.log` (observe-only, never blocks) |
| `~/.codex/hooks/tests/test_path_deletion_guard.sh` | 38-case test suite (allow + deny + fail-closed + all known bypasses) |
| `~/.codex/hooks.json` | Registration — adds the hook to `PreToolUse.matchers: Bash`, `apply_patch|Edit|Write\|Delete` |

## Quick start

The hook is wired into `~/.codex/hooks.json`. Run the test suite:

```bash
bash ~/.codex/hooks/tests/test_path_deletion_guard.sh
# Expected: PASS: path-deletion-guard (all cases), exit 0
```

Manual smoke test:

```bash
# DENY case
echo '{"hookEventName":"PreToolUse","tool_name":"Bash","tool_input":{"command":"rm -rf /Users/me/projects"}}' \
  | python3 ~/.codex/hooks/path-deletion-guard.py
# stdout: {"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Blocked rm -rf targeting path outside /tmp allowlist: ..."}}
# stderr: Blocked rm -rf ...
# exit 2

# ALLOW case
echo '{"hookEventName":"PreToolUse","tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/build"}}' \
  | python3 ~/.codex/hooks/path-deletion-guard.py
# stdout: {"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}
# exit 0
```

## How it decides

1. Tool must be in `WATCHED_TOOLS` (`Bash`, `shell`, `exec_command`, `apply_patch`, `Edit`, `Write`, `Delete`, future `mcp__filesystem__delete`). Anything else → allow.
2. If `_extract_command()` returns an UNREADABLE sentinel (tool_input is list/int/bool/float/None) or empty string AND the tool is watched → DENY (fail-closed).
3. Detect deletion pattern (`rm -rf`, `rmdir`, `shred`, `find -delete`, `find -exec rm`, `rsync --delete`, `git clean -fdx`, `git reset --hard`, `git rm -rf`, `shutil.rmtree`, `os.remove|unlink|rmdir`, `fs.rm`, `DROP TABLE/DATABASE`, `DELETE FROM`, `mkfs`, `dd to /dev/disk*`, `format c:`).
4. Extract path tokens (absolute, `~`-prefixed, `./`, `../`, bare relative like `foo/bar` resolved against `working_dir` — read from BOTH `payload.working_dir` and `payload.tool_input.cwd` because Codex 0.144+ nests it).
5. For CWD-targeting destructive commands (`git clean -fdx`, `git reset --hard`), add the resolved CWD to the target list.
6. Resolve every target with `Path.resolve(strict=False)`. If any resolved path is not under an allowed root → deny.
7. Output JSON matching the Codex-canonical schema: `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"..."}}`. Exit 2 + write the reason to stderr (codex reads the blocking reason from either transport).

## Codex schema — what's allowed vs what's not (verified 2026-07-17 against learn.chatgpt.com/docs/hooks.md)

This hook uses ONLY fields Codex documented as supported. Earlier versions emitted Claude-style `{"continue":false,"stopReason":"..."}` — that BROKEN Codex, which marks the hook as failed and runs the tool anyway:

> "permissionDecision:"ask", legacy decision:"approve", continue:false, stopReason, and suppressOutput are parsed but not supported yet. Codex marks the hook run as failed, reports the error, and continues the tool call."

Use only:
- `hookSpecificOutput.permissionDecision: "allow" | "deny"`
- `hookSpecificOutput.permissionDecisionReason: "<string>"`
- `hookSpecificOutput.updatedInput: {...}` (only with `"allow"`, for rewriting)

Emit exit 2 + stderr reason for denial. Codex reads stderr if the JSON exit parse fails.

## Pitfalls (don't repeat these — verified 2026-07-17)

**PITFALL #0 — Codex 0.144.5 does not enforce PreToolUse hooks against all shell paths.** `unified_exec` and other newer mechanisms skip the hook chain entirely. Live tmux test confirmed the hook fires (the codex transcript shows `hook: PreToolUse` / `hook: PreToolUse Completed`) but the destructive call STILL RAN. Don't treat this as a silver bullet. Pair with `sandbox_mode = "workspace-write"`, `approval_policy = "on-request"`, project-scoped trust, and an external backup.

**P1 — Bash `local var=$(cmd)` masks the subcommand's exit code.** Under `set -e`, the assignment inherits the subshell's exit and aborts the harness before you can inspect `$?`. Tests must either drop `set -e`, capture into a non-`local`, or use the brace-group `printf EXIT=%d "\${PIPESTATUS[1]:-0}" || true` trick.

**P2 — CWD-targeting commands have no path arg.** `git clean -fdx` and `git reset --hard` default to CWD. The hook adds CWD to the target list for these — see `_CWD_TARGETING`. Without this, they sail through the path check.

**P3 — Bare relative paths need CWD resolution.** `git rm -rf some/dir` has no `/` prefix. The regex includes `[\w.\-]+/[\w.\-/]+` and `_extract_paths` joins against cwd.

**P4 — `working_dir` is nested differently per CLI.** Claude puts `working_dir` at the payload root; Codex 0.144+ puts it under `tool_input.cwd`. The hook reads both shapes — otherwise CWD-relative deletions get false-positive denials.

**P5 — apply_patch line directive is case-INSENSITIVE.** The shipped pattern uses `re.IGNORECASE`. The canonical apply_patch grammar is `*** Delete File:` (capital D, capital F) — without IGNORECASE the spec-compliant form slips through as a silent allow.

**P6 — Hook output MUST end with `\n`.** Codex parses one JSON object per line; trailing newline is mandatory.

**P7 — Fail-closed on parse error is non-negotiable.** Malformed JSON, unreadable stdin, or any unhandled exception → deny.

**P8 — Audit companion (`-audit.sh`) must exit 0.** It is pure observability. Wire it AFTER the deny hook in the matcher so it sees both allowed and denied events.

**P9 — Codex matches regex, not glob.** `matcher: "Bash"` matches the tool name exactly; `matcher: "*"` matches anything; `matcher: "apply_patch|Edit|Write|Delete"` is an alternation. Quote it as a string — Codex does NOT split on whitespace.

**P10 — Hook fires on EVERY Bash invocation.** Performance budget is <50ms typical, <200ms p99. Pure stdlib Python.

**P11 — Unknown `tool_input` types deny for watched tools.** `_extract_command` returns a sentinel for list/int/bool/float/None — `evaluate()` early-denies any watched tool that comes in with that sentinel. Without this, a malformed Bash payload (e.g. `tool_input: [1,2,3]`) silently allows.

**P12 — Two-step symlink trick is only caught when literal path appears in source.** `ln -s /Users/me/secret /tmp/lnk; rm -rf /tmp/lnk` is denied (because `/Users/me/secret` is in the source). But a separate `rm -rf /tmp/lnk` is allowed even if `/tmp/lnk` symlinks to `/Users/me/secret`. Defense-in-depth: also `os.path.realpath` each path token and re-check.

**P13 — `~otheruser/...` tildes are silent allows.** The regex branch only matches `~/$HOME/...` and absolute paths. `rm -rf ~root/.cache` extracts zero path tokens. Extend the tilde branch to `~[\w\-]+(?:/[\w.\-/]+)?` if you care about other-user homes.

**P14 — `$TMPDIR` is read at every invocation**, not locked at hook process start. A payload that prepends `TMPDIR=/some/path` (the runtime env at hook launch) widens the allowlist by one entry. Lock `$TMPDIR` at spawn if you don't control the env wrapper.

## Failure modes

| Input | Output |
|-------|--------|
| Empty stdin | `permissionDecision=allow` exit 0 |
| Malformed JSON | `permissionDecision=deny`, "malformed JSON payload (fail-closed)", exit 2 |
| JSON object missing `tool_input` | allow |
| `Read` tool | allow (not in watched set) |
| `Bash` + `echo hello` | allow |
| `Bash` + `rm -rf /tmp/scratch` | allow (in allowlist) |
| `Bash` + `rm -rf $HOME` | deny, names $HOME |
| `Bash` + `rm -rf /Users/me/...` | deny, names the path |
| `Bash` + `rm -rf relative/...` with `tool_input.cwd` = `/tmp` | allow (resolves into /tmp) |
| `Bash` + `rm -rf relative/...` with non-/tmp CWD | deny |
| `Bash` + `git clean -fdx` with `/tmp` CWD | allow |
| `Bash` + `git clean -fdx` with `/Users/...` CWD | deny |
| `apply_patch` with `*** Delete File: /Users/...` (canonical case) | deny |
| `apply_patch` with `*** delete file: /tmp/x` | allow |
| `Edit` with `file_path: /Users/me/.zshrc` | deny |
| `Bash` + `tool_input: [1,2,3]` (non-dict) | deny (fail-closed) |
| Any unhandled exception | deny, fail-closed |

## Extending the allowlist

Edit `DEFAULT_ALLOW_ROOTS` in the Python file, OR set the env var before launching codex:

```bash
export PATH_DELETION_GUARD_ALLOW=/Users/me/scratch:/tmp/special
codex
```

`$TMPDIR` is honored automatically (macOS sets it to `/var/folders/.../T/`).

## Defense in depth reminder

This hook is **one layer** of a defense-in-depth strategy. Twitter community consensus (X 2077820292622372866, 2077396515975307273) and Codex's own docs (Pitfall #0 above) agree: no hook alone is sufficient. Pair with:

1. Sandbox: `sandbox_mode = "workspace-write"` (not `danger-full-access`) when possible.
2. Approval policy: `"on-request"` or interactive (not `"never"`).
3. Workspace scoping: limit Codex to a disposable project folder via `[projects.<path>].trust_level`.
4. Backups: independent of Codex's reach (Time Machine, remote git, external drive).
5. Git: authoritative copy on remote (`git push` as your durable recovery point).
6. Audit log: `~/.codex/log/path-deletion-guard.log` should be reviewed after every Codex session.

See `~/.codex/AGENTS.md` for the rest of the safety stack.

## References

- `references/adversarial-probe-2026-07-17.md` — full transcripts from the 9-vector adversarial probe (Reviewer C). Use as regression-test fixtures when refactoring the hook. v1 had 3 real bypasses (apply_patch case-sensitivity + Bash non-dict tool_input × 2); all fixed in v2. Three open follow-ups documented (two-step symlink, ~otheruser tilde, runtime TMPDIR override).
- learn.chatgpt.com/docs/hooks.md — official Codex hook reference (verified 2026-07-17). Key warnings about `continue:false`/`stopReason` being parsed-but-unsupported, and `unified_exec` skipping PreToolUse.
- X thread 2077396515975307273 — Codex `hookSpecificOutput.permissionDecision` schema.
- X thread 2077820292622372866 — GPT-5.6 destructive-command incident + community hardening.
- X thread 2037523396876173783 — `exit 2` vs `exit 0` vs `exit 1` semantics (only `exit 2` blocks).
- X thread 2042844012592189619 — Codex 0.119–0.120 hook output rendering.
- Local neighbors: `~/.codex/hooks/rtk-hook-guard.sh`, `~/.codex/hooks/codex-notify-git-header.sh`.
- Codex 0.142.3 → 0.144.5 changelog (https://github.com/openai/codex/releases) — dangerous-command detection expanded; `unified_exec` added.
