# Hermes — How to Find the Actually-Running Gateway Source

**Read this before "deploy it" / "is the fix live?" / "did the merge land in prod?"**

The umbrella `hermes-deploy-pipeline` SKILL.md documents the **staging → prod sync direction** (write to `~/.hermes/`, then `cp` to `~/.hermes_prod/`, restart). This reference covers the **reverse direction** — when a user asks whether a change is live, the right answer depends on *which* code path is actually serving requests, and the answer is **not always** `~/.hermes_prod/`.

## The 3-place Hermes source layout (verified 2026-06-13)

| Path | Role | Loaded by gateway? |
|------|------|--------------------|
| `~/.hermes/` (`jleechanorg/jleechanclaw` fork checkout, origin `jleechanclaw`) | Staging / git-tracked source of truth | **No** — staging only, not the runtime |
| `~/.hermes_prod/` | Prod runtime dir (launchd `WorkingDirectory` + `HERMES_HOME`), but only holds state, logs, db files, no `gateway/run.py` | **Partially** — gateway reads config + state from here, but the actual code is imported from a different path |
| `~/projects_other/hermes-agent/` (`jleechanorg/hermes-agent` fork, pip-installed editable) | The live `hermes-agent` Python package; running gateway imports `hermes_cli.*` and `gateway.*` from here | **Yes** — this is what the running gateway PID 1328 imports. The `/opt/homebrew/bin/hermes` entry script is a pip-installed shim that resolves to this source. |

**The trap:** a fresh agent reading `~/.hermes/SOUL.md` and the deploy-pipeline skill will assume `~/.hermes/` is the source of truth and `~/.hermes_prod/` is the runtime target. Both are wrong for Hermes Agent core code (gateway/run.py, hermes_cli/*, agent/*). The actual source of truth is the **pip-installed editable package at `~/projects_other/hermes-agent/`**, which has its own `git remote` setup (`fork` + `jleechanorg` → `jleechanorg/hermes-agent`, `origin` → `NousResearch/hermes-agent`).

This means: "is PR #27 live?" requires `cd ~/projects_other/hermes-agent && git log --oneline -1`, not `cd ~/.hermes`.

## The universal probe (copy-pasteable)

Before claiming any Hermes gateway change is "live", run this 5-step probe:

```bash
# 1. What is the live hermes entry point?
which hermes
# → /opt/homebrew/bin/hermes  (a Python shim)

# 2. What is the running gateway PID, and what does it import from?
ps aux | grep -E 'hermes.*gateway.*run' | grep -v grep
# → /opt/homebrew/Cellar/python@3.14/.../Python /opt/homebrew/bin/hermes gateway run
# (PID 1328 in the 2026-06-13 instance)

# 3. Where does the pip-installed package source actually live?
pip3 show -f hermes-agent | grep -E '^(Name|Version|Location)'
# → Location: $HOME/projects_other/hermes-agent
# → Version: 0.16.0  (the wheel's reported version — may differ from the source's __version__)

# 4. Is the installed package editable? (If yes, source == live.)
pip3 show hermes-agent | grep -E 'Editable project location'
# → If present, confirms the pip install is editable (changes to the source take effect on next process start, no reinstall needed)

# 5. What is the source's HEAD SHA, and does it contain the fix?
cd $HOME/projects_other/hermes-agent
git log --oneline -3
# → 42aff5b47 fix(slack): carry reply-anchor thread_id in _status_thread_metadata
# → 748a8cdee feat(merge-train): make all file domains advisory
# → c9f9690d8 chore: gitignore merge_train install-generated hook configs
```

If step 5 shows the fix commit on HEAD, **the fix is live** (assuming the gateway was restarted after the source change — for `gateway/run.py` changes, a restart is required; for prompt-only or config changes, a restart may not be needed). If the fix commit is on `origin/main` of `jleechanorg/hermes-agent` but not in the local source, it has NOT been deployed.

## Comparison with `git log f4841cc3 42aff5b47` to confirm a squashed fix is content-equivalent

When the local source has a squashed version of an upstream PR, `git diff` the two SHAs against the fix files to confirm the content is identical:

```bash
cd $HOME/projects_other/hermes-agent
git diff f4841cc3ff45a8cebd0e0ded96c49408bafb4d19 42aff5b47 \
  -- gateway/run.py tests/gateway/test_slack_thread_survives_compression.py
# Empty diff = content-identical, even if the SHAs and commit messages differ.
```

This was the proof that the "PR #27 deploy" was a no-op in the 2026-06-13 session: the local source's `42aff5b47` was the squashed equivalent of the upstream merge `f4841cc3` (verified via empty diff on the two fix files).

## Common pitfalls

1. **Trusting `pip3 show`'s "Version: 0.16.0".** The wheel's reported version may be one release behind the source's actual `__version__` (e.g. source `__init__.py` says `0.13.0` while pip reports `0.16.0`). The `__version__` in the source tree is the truthful one; trust `git log` over `pip3 show` for "is the fix here?".

2. **Assuming `~/.hermes/gateway/run.py` is the live code.** It's a stale, out-of-tree copy from an older install. The live `gateway/run.py` is at `~/projects_other/hermes-agent/gateway/run.py`. Patches to the staging copy will NOT be picked up by the running gateway.

3. **Forgetting to restart the gateway after a code change.** Editing `~/projects_other/hermes-agent/gateway/run.py` does not auto-reload the gateway process. The running PID 1328 still has the old `run.py` in memory. After editing, restart via launchd:
   ```bash
   DOMAIN="gui/$(id -u)"
   LABEL="ai.hermes.prod"
   PID="$(launchctl print "${DOMAIN}/${LABEL}" 2>/dev/null | grep '^ *pid' | awk '{print $3}' || true)"
   [ -n "$PID" ] && kill -TERM "$PID" 2>/dev/null
   # launchd respawns within ~10s; verify with:
   curl -sf http://127.0.0.1:8642/health
   ```

4. **Confusing `jleechanorg/jleechanclaw` (origin of `~/.hermes`) with `jleechanorg/hermes-agent` (origin of `~/projects_other/hermes-agent`).** These are **two different forks** in the same GitHub org. PRs to one do NOT auto-merge to the other. The slack-thread-routing PR #27 was filed against `jleechanorg/hermes-agent`, which is the correct repo for Hermes Agent core code; it would have been wrong against `jleechanorg/jleechanclaw`.

## When this probe is mandatory

Run the 5-step probe before ANY of these:
- Claiming a code change is "live" or "deployed"
- Telling the user "no restart needed" after editing a `*.py` file under the live source
- Saying "the fix is in main" without confirming the local source has it
- Recommending `git pull` on `~/.hermes/` when the actual fix is in `~/projects_other/hermes-agent/`

If the probe shows the source is in a different fork than you assumed, **say so explicitly** before taking action. The user would rather hear "the source-of-truth is at a different path than I expected" than watch you make 3 wrong edits in a row.

## Cross-references

- `hermes-deploy-pipeline/SKILL.md` — the umbrella skill, which this reference extends. The umbrella documents the staging → prod sync direction; this reference covers the reverse (what is live → which tree to write to).
- `references/actual-deploy-state-2026-06-09.md` — older diagnosis of the staging/prod drift issue, focused on the manual-cp sync procedure and the (then-missing) `deploy.sh` script. This reference is the 2026-06-13 update that adds the third source-of-truth (`~/projects_other/hermes-agent`).
- `references/deploy-script-port-drift-pitfall.md` — gateway port canary pitfalls (`scripts/deploy.sh` hard-codes 8643, config says 8642). Different angle from this reference; read both if "deploy failed" + "is the fix live?" both fire.
- `slack-thread-routing-investigation/SKILL.md` — the canonical place for Slack thread routing diagnosis; this reference is mentioned there under "Patches / known followups" because the 2026-06-13 "is the fix live?" session was triggered by the slack-thread-routing-bug callback.
