# `/super` slash command + cross-machine (Mac vs jeff-ubuntu) shape

Companion to `SKILL.md`. The skill governs the **box dispatch** (preflight → handoff → follow loop → land); this file governs the **slash-command shape** users invoke to trigger that dispatch, plus the **Mac-only-by-design** constraint and the cross-machine sync model that any session editing slash commands needs to honor.

## The two slash commands (canonical, both machines, both must agree)

| Command | File | Bytes (Mac, 2026-07-20) | What it does |
|---|---|---|---|
| `/super` | `~/.claude/commands/super.md` | 8195 | **Cloud Build dispatch** — the box. Writes plan.md, runs preflight, hands off, follows loop, lands. |
| `/superlight` | `~/.claude/commands/superlight.md` | 3227 | **Legacy thin `claudeg` router** — local GLM-5.2 via `claudeg -p "$1"`. No box, no plan, no hermeticity gate. |

**History (verified 2026-07-20):** the original `/super` (created 2026-07-20 13:10 as a 2342-byte transitional shim) was a local `claudeg` router made during the "are `claudeg`/`claudek` both working?" verification thread. The user redirected the same day:

> "Wait `/super` shouldn't be using claudeg it should be using superpowers cloud"

The canonical `/super` was rewritten to dispatch to the actual box (8 steps mirroring `cloud-build/SKILL.md` phases 1-6 verbatim), and `/superlight` was created as the legacy escape hatch. **If a future session sees `/super` described as a thin `claudeg` router, that's stale — redirect to this reference.**

## What `/super` does, step-by-step

The full body is at `~/.claude/commands/super.md` on both machines; the high-level shape:

1. Resolve `$PROJECT` from `$PWD`; require current branch is under `private/*` — if not, STOP with "check out a private/* branch first"
2. Materialize `$ARGUMENTS` as a `plan.md` under the project (writing-plans skill format)
3. Ask the user once for `CLOUD_HERMETIC_CONFIRMED=1` — never auto-confirm hermeticity
4. `cd ~/superpowers-cloud-build-main/skills/cloud-build && bash scripts/preflight-local.sh "$PROJECT" "$plan_rel"`
5. Compute `run_id` + `run_sha` + `plan_rel`; call `cloud_build_handoff` (one unit: verify → push frozen branch → push control frame)
6. Follow loop every ~10 min via `cloud_build_fetch_status` / `cloud_build_check_heartbeat` / `cloud_build_status`
7. On `done`: `cloud_build_land_result` + `cloud_build_mk_pulled` ack
8. Hand off to `superpowers:finishing-a-development-branch` for PR shape

**Bounded retry:** only the literal server signal "build box failed to start" triggers a replay. Auth, host-key, every other failure is final.

**Critical:** do NOT re-run `cloud_build_handoff` yourself after a non-replay failure. Do NOT mint a new `run_id` unless the user explicitly says "retry from scratch."

## What `/super` does NOT do (so future sessions don't re-add it)

- ❌ Does NOT call `claudeg`. `claudeg` happens to use the same GLM-5.2 model the box uses, but the slash command is about **execution mode**, not model identity. The whole point of the 2026-07-20 redirect was to make the slash command dispatch to the **box**, not the local router.
- ❌ Does NOT silently substitute a different model (claudeor / claudek / claude).
- ❌ Does NOT auto-confirm hermeticity.
- ❌ Does NOT push to the work branch directly — the helper does, one unit.

## Mac-only-by-design constraint

The SSH identity, host-key pin, and enrollment state all live ONLY on the Mac:

| Asset | Mac path | jeff-ubuntu? |
|---|---|---|
| SSH identity | `~/.ssh/cloud-build/id_ed25519` | ❌ Not present |
| Host-key pin | `~/.ssh/cloud-build/known_hosts` | ❌ Not present |
| Enrollment state | `~/.config/cloud-build/state.json` (enrolled_fp_hash + host + port + identity) | ❌ Not present |
| Plugin source | `~/superpowers-cloud-build-main/skills/cloud-build/` | ❌ Not present |
| Plan dispatch entry point | `~/superpowers-cloud-build-main/skills/cloud-build/scripts/{preflight-local.sh,lib-client.sh}` | ❌ Not present |

**Rule:** `/super` works on the **Mac only**. From jeff-ubuntu, the user invokes the cloud-build skill directly via Claude Code's `/skill-name cloud-build` mechanism or by reading `~/.codex/superpowers/skills/cloud-build/SKILL.md` and running the script paths from there. The Linux box can reach `cloud.superpowers.build:22` over SSH, but it has no client identity and no host-key pin, so it can't open the door.

**Pitfall:** A user running `/super` from jeff-ubuntu will get a missing-state error. Do not try to scp the enrollment state across machines — the host-key pin is per-machine for a reason.

## Cross-machine sync model for slash-command files

`~/.claude/commands/*.md` files ARE inside the user's home dir on both machines, but the sync model is not guaranteed:

1. **Dropbox is the intended sync path** (most home dirs are Dropbox-backed on this fleet). `~/.claude/commands/super.md` will eventually appear on jeff-ubuntu, but Dropbox sync latency is seconds-to-minutes, not immediate.
2. **Verify sync explicitly** — never assume the rewrite reached the other machine. After editing a command file on the Mac, run:
   ```bash
   ssh -o ConnectTimeout=5 -o BatchMode=yes jeff-ubuntu \
     'stat -c "%s %y %n" /home/$USER/.claude/commands/super.md'
   ```
   If the mtime is older than the Mac edit or the size differs, **scp the file**:
   ```bash
   scp -o ConnectTimeout=5 ~/.claude/commands/super.md \
     jeff-ubuntu:/home/$USER/.claude/commands/super.md
   ```
3. **Verified failure mode (2026-07-20):** the Mac rewrite at 14:32 was NOT visible on jeff-ubuntu at 14:32 (still 2342 B from 2026-07-20 13:09). Dropbox hadn't propagated. `scp` fixed it in <1s.
4. **The `claude` binary PATH differs:**
   - Mac: `~/.local/bin/claude` (symlinked into npm-global)
   - jeff-ubuntu: `~/.npm-global/bin/claude` v2.1.198, NOT on default PATH
   - jeff-ubuntu's `~/.bashrc` line 166 does NOT add `.npm-global/bin` to PATH — but the `claudeg` function still finds it because of `nvm`-injected paths. If a session writes a shell snippet that calls `claude` directly (not via `claudeg`), it must prepend `~/.npm-global/bin` to PATH on jeff-ubuntu first.

## When `/superlight` is still the right answer (the legacy escape hatch)

The user-facing rule for choosing between `/super` and `/superlight`:

| Use `/superlight` when… | Use `/super` when… |
|---|---|
| Task is one-line / throwaway / exploratory | Task is a real feature or fix |
| Output should land inline in this session | Output should land as commits authored by `Cloud Build <supervisor@cloud-build.local>` |
| No commit attribution matters | Audit trail + hermeticity + retry budget matter |
| Branch doesn't matter | Work branch is under `private/*` and tests are hermetic |
| Sub-minute latency is fine (assuming OpenRouter has credits) | 60-300s box provisioning is acceptable |

**Current state (2026-07-20):** `/superlight` returns `API Error: 402 Insufficient credits` on BOTH machines because the OpenRouter account the key belongs to has zero balance. Single fix point — top up at https://openrouter.ai/settings/credits and both hosts light up simultaneously. **Do not silently swap to `claudek` / `claudeor` / `claude` — the user's `/super` rule explicitly forbids model substitution.**

## Anti-patterns called out

- ❌ **"Make `/super` call `claudeg` because it's faster"** — this was the 2026-07-20 13:10 mistake. Redirect target = box, not local router.
- ❌ **"Just edit the slash command on one machine"** — the user expects `/super` to behave identically on both Mac and jeff-ubuntu. Always verify + scp.
- ❌ **"Try `/super` from jeff-ubuntu"** — Mac-only by design; the box can't be reached without the Mac-side enrollment.
- ❌ **"Skip the hermeticity prompt because it's annoying"** — preflight is fail-closed for a reason; the operator's confirmation is the gate.
- ❌ **"Edit the cloud-build skill instead of the slash command"** — the skill is the source of truth; slash commands are thin wrappers. Edit the skill only when the underlying flow changes; edit the slash command when the trigger shape changes.

## Pair with

- `~/superpowers-cloud-build-main/skills/cloud-build/SKILL.md` — the canonical plugin docs (read this on every drive)
- `references/local-vs-cloud-decision-tree.md` — the 6-axis comparison + "when to use which" decision rule
- `~/.bashrc` `claudeg` function (line ~700 on jeff-ubuntu) — for `/superlight` direct invocation context
- `~/.config/cloud-build/state.json` — the canonical enrollment record (Mac only)
