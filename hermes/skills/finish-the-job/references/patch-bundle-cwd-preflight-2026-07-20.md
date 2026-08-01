# Patch-bundle cwd pre-flight (added 2026-07-20)

**Trigger:** user uploads a `.patch` / `.diff` / `git format-patch` series and asks to apply, review, or `/super`-dispatch it. The artifact comes from outside the repo (Slack attachment, `~/Downloads`, a sibling repo).

**The failure mode (verified 2026-07-20, jleechanai thread `C09GRLXF9GR/p1784582518.247009`):**

```
$ cd $HOME && git apply --stat infra03q-inpipeline-receipt.patch
... (silently returns success — missing-file errors look like warnings at the parent level)
$ cd $HOME/repos/jleechanorg/dark-factory && git apply --check infra03q-inpipeline-receipt.patch
error: snap_factory/engine.py: No such file or directory
error: patch failed: tests/test_engine.py:2738
error: tests/test_engine.py: patch does not apply
```

When `git apply --stat` runs from a directory that does NOT contain the patch's target tree (e.g. `$HOME` when the patch targets `dark-factory/snap_factory/engine.py`), git reports the missing file as a warning rather than an error and the dry-run exits 0. The agent posts "On it — applying" based on the false green check, then burns reviewer time + quota discovering the patch targets a non-existent path.

## Mandatory pre-flight (run BEFORE acking the user)

```bash
# 1. Identify the target repo by walking up from cwd OR by inspecting
#    the patch's `+++ b/...` headers
grep -E '^diff --git' /path/to/patch.patch | head -5

# 2. Resolve the correct repo path. If the patch references a subpath
#    that exists in $HOME/repos/jleechanorg/<repo> or
#    $HOME/projects/<repo>, cd there.
REPO=$HOME/repos/jleechanorg/dark-factory   # ← the path that ACTUALLY contains the files

# 3. Run BOTH checks from the correct repo root — --stat (shows hunk
#    intent) AND --check (rejects on missing files / non-applicable hunks).
cd "$REPO" && git apply --stat /path/to/patch.patch
cd "$REPO" && git apply --check /path/to/patch.patch   # ← THIS is the gating signal
```

**The `--check` exit code is the only authoritative signal.** `--stat` is informational.

## When `--check` fails: surface the failure before acking

If `git apply --check` exits non-zero, do NOT post "On it — applying the patch" — the patch cannot land as-is. The right ack shape is:

> 🟡 Blocked before /super can dispatch.
> `git apply --check` fails:
> ```
> error: <path>: No such file or directory
> error: <hunk>: patch does not apply
> ```
> The patch targets `<missing-path>` which does not exist in this checkout. Three options:
> - A. Find the repo where this path DOES exist (`gh repo list` + local checkouts)
> - B. Rewrite the patch with corrected paths (`sed -e 's|<old-path>|<new-path>|g'`)
> - C. Drop / aar-triage the offending hunks

## Related pitfalls

- **`/super` = Superpowers Cloud Build dispatch (verified 2026-07-20), NOT a local GLM-5.2 router.** Earlier session memory may still cite the legacy definition (`claudeg`-backed). Always verify against `~/.claude/commands/super.md` before answering `/super` questions — the file was rewritten 2026-07-20 13:10 to point at the remote box. See `~/.claude/projects/-Users-$USER/memory/feedback_2026-07-20_superpowers_cloud_build_install_and_differences.md`.
- **`/aar` = `/accept-adapt-reject`** — feedback triage, not "apply patch". For patch-driven apply, `/aar` is optional; the gate is `/advice` (does this belong?) → path-validity pre-flight → `/super` (or inline).
- **`claude -p` rate-limit** — when Reviewer A subagent + `claude -p` fallback both fail, the `/advice` fan-out silently degrades. Verify `claude -p` first (5s test prompt); if it returns "weekly limit hit", surface the blocker instead of fanning out to no-op reviewers.

## Distinguishing cwd failure from cross-fork misroute (added 2026-07-20)

When `git apply --check` fails with `No such file or directory`, it can mean TWO different things:

| Failure mode | Root cause | Diagnostic |
|---|---|---|
| **cwd preflight** | Agent ran `git apply` from a directory that does not contain the patch's target tree | `cd <repo-with-target-tree> && git apply --check <patch>` now passes |
| **cross-fork misroute** | Patch was generated from a different repo entirely (different org, different email, different fork) | Cwd preflight still fails. Run the misroute-detection probes below. |

Verified 2026-07-20: agent spent significant budget porting `infra03q-inpipeline-receipt.patch` (from `$USER@snapchat.com`, Snapchat-internal `snap-factory`) onto `jleechanorg/dark-factory` before discovering the cross-fork mismatch. The cwd preflight alone would not have caught this — `cd ~/projects/dark-factory && git apply --check` failed identically. The disambiguating signal was the **author email domain**, the **target repo's github existence**, and the **patch base SHA's github presence**.

## Cross-fork misroute probes (run AFTER `--check` fails, BEFORE ack)

```bash
# Probe 1: Patch base SHA exists on target repo?
gh api repos/<owner>/<repo>/commits/<base-sha-from-From:-header> 2>&1 | head -5
# 422 / "No commit found" = patch from a different fork.

# Probe 2: Patch author email domain matches target repo owner?
grep "^From: " /path/to/patch.patch | head -1
gh repo view <owner>/<repo> --json owner --jq '.owner.login'
# Mismatch = likely misroute.

# Probe 3: Patch's source repo (from `+++ b/...` headers or author email) exists on github?
gh repo view <source-repo> 2>&1 | head -3
# 404 = patch from a non-public fork.

# Probe 4: Each `diff --git` path actually exists in target repo HEAD?
for p in $(grep -oE '^diff --git a/[^ ]+ b/[^ ]+' /path/to/patch.patch | awk '{print $3}' | sed 's|b/||'); do
  gh api repos/<owner>/<repo>/contents/$p 2>&1 | grep -q '"name"' && echo "FOUND: $p" || echo "MISSING: $p"
done
# ALL MISSING = misroute, not just stale paths.
```

**Decision rule:** If ANY probe signals misroute, do NOT fabricate a port by mapping symbols to superficially-similar target-repo functions. The `runner/handler_codergen.py::_codergen` ↔ `snap_factory/engine.py::_run_llm` mapping looked plausible but was wrong: dark-factory's `_codergen` is a totally different abstraction (subprocess-backed claude/codex invocation), not a renamed `_run_llm`. Verified zero hits: `runner/handler_codergen.py` and `runner/handler_verdict.py` contain zero matches for `_finalize_review_status`, `_is_review_node`, `_reproduction_receipt_gaps`, or `commands_run.md`.

## Right ack shape on cross-fork misroute

DO NOT post "On it — applying the patch" or "On it — porting". Post:

> 🛑 **Patch misroute — cannot port as-is.**
> Probe results (terminal-verified):
> - patch author `$USER@snapchat.com` ≠ repo owner `jleechanorg` (different org)
> - `gh repo view jleechanorg/snap-factory` → 404 (repo does not exist on github)
> - patch base SHA `bcdf87c5c19d…` → 422 No commit found on `jleechanorg/dark-factory`
> - 4 of 5 `diff --git` paths reference `snap_factory/` which does not exist in this fork
>
> The patch targets Snapchat-internal `snap-factory`, not `jleechanorg/dark-factory`. Two paths forward:
> - A. Confirm the patch is for a different repo by mistake — close this thread as misrouted.
> - B. If the underlying intent (reproduction-receipt gate on review nodes) is desired on `dark-factory`, treat as a NEW design task — write a fresh patch against `runner/handler_verdict.py`. Different effort, not a port.

## Cleanup after detecting misroute

If the agent has already created issue + bead + branch + worktree artifacts on the target repo before discovering the misroute, clean them up before posting the final reply:

```bash
gh issue close <N> --repo <owner>/<repo> --comment "Closing: patch is misrouted (author email / base SHA / target paths all inconsistent with this repo)."
br close <bead-id> --reason "patch is misrouted (snapchat-internal snap-factory, not <owner>/<repo>)"
git worktree remove --force --force /path/to/worktree    # need -f -f for "locked" state
rm -rf /path/to/worktree <repo>/.git/worktrees/<worktree-name>
git worktree prune
git branch -D feat/<topic>
git am --abort || true
rm -rf <repo>/.git/rebase-apply
# verify: git status --short (empty) + git worktree list (no stale entries)
```

## Cross-references

- Companion: `dispatch-task` skill — needs a parallel patch-validity pitfall in the spawn-preflight section.
- Companion: `advice/SKILL.md` Phase -0 state-corruption pre-flight (`md5 + size + mtime` of every file the patch targets) — applies here too. Take the cheap check first (file existence + `git apply --check`), then the full state-corruption probe if the cheap check passes.
- `references/wrong-target-removal-stop-X-from-Y-2026-07-20.md` — companion disambiguation pattern: when symptom noun ≠ source noun, trace provenance before actioning. Same shape as the misroute-detection here: probe before you act.
- `superpowers-cloud-build` skill — `/super` should not be invoked on a misrouted patch (the box would attempt to apply it and fail with the same error class as `git apply --check`).
- Provenance: Slack thread `C09GRLXF9GR/p1784582518.247009` (infra03q in-pipeline receipt patch bundle — verified misroute from `$USER@snapchat.com` Snapchat-internal `snap-factory` to `jleechanorg/dark-factory`).
