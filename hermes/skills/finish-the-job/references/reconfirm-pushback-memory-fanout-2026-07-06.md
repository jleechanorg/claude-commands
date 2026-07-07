# Reconfirm & pushback handling — 9-store memory fan-out

**Originating incident:** 2026-07-06, ez-gh-actions PR #9 (`https://github.com/jleechanorg/ez-gh-actions/pull/9`).
**Thread:** Slack `C09GRLXF9GR` (`#all-$USER-ai`), parent message `1783279897.083129`, reconfirm pushback `1783288882.941819`.
**Fix landed in:** commit `055ff319b4e351d2f2119e3c4a4035edbc7c3247` (PR #9 follow-up).
**Skill updated:** `finish-the-job` v1.2.0.

---

## The pattern

When the user replies with any of:

- "I thought it was X" / "isn't this X?" / "shouldn't this be X?"
- "there was supposed to be Y" / "what happened to Y" / "where is Y"
- "reconfirm" / "recheck" / "are you sure"
- "Run /history and /ms" / "search your memories" / "look it up"
- "why does X say no when the wiki says yes?"

…they are pointing at a memory artifact, not asking the agent to re-derive the answer from source code. The instinct to re-read `DESIGN.md` + `src/*.rs` + the PR body is **wrong** — that round-trip is what produced the contradiction in the first place. The user is testing whether the agent's terminology matches the project's own canonical terminology.

**Code is truth for behavior. The user's memory stores are truth for what the strategy is called.**

## The 9-store fan-out

Run all 9 in parallel. For Hermes sessions, use `delegate_task` to dispatch one task per store. For Claude Code / Codex, type `/ms <query>`. Total budget: ~6–10 tool calls, ~5–15 seconds wall-clock when parallel.

```bash
# 1. ~/roadmap — project learnings, decisions
grep -rnE "VM.in.VM|nested.virtualization|ezgha" ~/roadmap/ 2>/dev/null

# 2. beads — issue/bead tracking
br search "ezgha VM" 2>&1; br search "nested VM" 2>&1

# 3. ~/.claude/projects/*/memory/ — per-project session memory
grep -rlnE "VM.in.VM|nested|ezgha" ~/.claude/projects/*/memory/ 2>/dev/null | head -5

# 4. ~/.hermes/state.db — messages + FTS5 trigram index
#    (session_search is the high-level interface; raw FTS5 also works)
session_search "ezgha VM-in-VM" --limit 5

# 5. ~/.hermes/memory/briefing-*.md + mcp-mail-ack-log.md
grep -lnE "ezgha|VM" ~/.hermes/memory/briefing-*.md ~/.hermes/memory/mcp-mail-ack-log.md 2>/dev/null

# 6. ~/.hermes/MEMORY.md — the agent's curated long-term
grep -niE "ezgha|ez-gh-actions|VM.in.VM|nested VM" ~/MEMORY.md 2>/dev/null

# 7. ~/llm_wiki/ — the canonical knowledge wiki
find ~/llm_wiki/wiki -type f -name "*.md" 2>/dev/null | xargs grep -lE "VM.in.VM|ezgha" 2>/dev/null | head -5

# 8. ~/.claude/projects/*/*.jsonl — history (2-phase grep, never read raw)
grep -lE "ezgha.{0,200}VM.in.VM|VM.in.VM.{0,200}ezgha" ~/.claude/projects/*/*.jsonl 2>/dev/null | head -3

# 9. Slack — search the channels the user DMs from
mcp__slack__conversations_search_messages(
  channels=["C09GRLXF9GR", "<user-dm-channel>"],
  query="ezgha VM-in-VM",
  limit=10
)
```

Plus two extra checks the agent's instinct skips:

```bash
# 10. Original proposal / gist / RFC — fetch via web_extract and check whether the
#     original wording contradicts the current implementation.
curl -fsSL "https://gist.githubusercontent.com/jleechan2015/<gist-id>/raw" > /tmp/original-gist.md
grep -niE 'vm.{0,3}in.{0,3}vm|nested' /tmp/original-gist.md

# 11. Open + closed PRs — search bodies for the same terminology
gh pr list --repo OWNER/REPO --state all --limit 20 --json number,title,body,headRefName \
  | python3 -c "
import json, sys
for p in json.load(sys.stdin):
    if 'VM-in-VM' in p.get('body',''): print(f\"#{p['number']}: {p['title']}\")"
```

## Reconciliation: 4 checks that distinguish "user is right" from "user is misremembering"

When memory stores and source code disagree on the meaning of a term, run these 4 checks:

| # | Check | "User is right" | "User is misremembering" |
|---|---|---|---|
| 1 | Does the term appear in 2+ memory stores (wiki, roadmap, project memory)? | YES | NO |
| 2 | Does the deployed behavior match one of the two interpretations? | YES (the one memory describes) | NO |
| 3 | Was the term used in the original proposal / gist? | YES (or omitted but implied) | NO |
| 4 | Did any prior PR/issue explicitly use the term? | YES | NO |

If checks 1–2 pass, ship a correction: amend the prior PR + add a terminology-disambiguation paragraph + reply with the memory evidence. If checks 3–4 fail, gently explain that the user's memory may be from a different project or a pre-v1 design, and offer to update the memory stores to match the current terminology.

## Original ez-gh-actions incident transcript

### Turn 1 (user, 2026-07-05 22:01 UTC)

> Review readme and update as needed and lets add an architecture diagram and lets reconfirm if its doing a VM inside VM strategy to isolate the workers https://github.com/jleechanorg/ez-gh-actions

### Turn 2 (assistant — WRONG answer)

Agent read `README.md` (8 KB) + `DESIGN.md` (9.6 KB) + `src/backend.rs`. Concluded "no VM-in-VM, three valid topologies (container-on-host, container-in-VM via Colima/Lima/Docker Desktop kernel mismatch, container-in-dedicated-VM via Tart/libvirt in M2)". Opened PR #9 with title "Isolation model — not VM-in-VM" in DESIGN.md, committed `28ecb74ef5184ed17f9a7ce8445b5536d6031e76`. **Did NOT run /ms or /history.**

### Turn 3 (user, 2026-07-05 22:01 UTC — pushback)

> Run /history and /ms there was supposed to be vm inside vm, what happened

### Turn 4 (assistant — corrected via fan-out)

`delegate_task` with 1 task that fan-out across 9 memory stores + the gist + open PRs. Found:

| Source | Evidence |
|---|---|
| `$HOME/llm_wiki/wiki/concepts/vm-within-vm-isolation.md` | Canonical page defining VM-within-VM as container-in-VM-in-host 3-layer stack. |
| `$HOME/roadmap/learnings-2026-07.md:267` | "Rust ezgha daemon, JIT registration, VM-within-VM isolation" |
| `$HOME/.claude/projects/.../memory/project_2026-07-05_ezgha_supersedes_self_hosted_oss.md:44` | "VM-within-VM isolation. Linux containers in a Colima/Lima VM on the Mac; Linux host's qemu microVMs on jeff-ubuntu." |

**Reconciliation:**
- Wiki + roadmap + project memory all use "VM-within-VM" to mean container-in-VM-in-host 3-layer stack.
- Source code (`DESIGN.md` + `src/backend.rs`) uses "VM" to mean any VM backend — ambiguous between nested-backends and 3-layer-stacks.
- Deployed reality on Mac (container → Docker daemon → Colima Lima VM → Darwin host) and jeff-ubuntu (container → Docker daemon → QEMU microVM → Ubuntu host) **IS** the 3-layer stack. ✅

→ The user was right. The first commit's framing was wrong: it rejected the nested-VM-backend interpretation (a non-goal) without affirming the 3-layer-stack interpretation (the actual strategy).

### Turn 5 (assistant — correction shipped)

Follow-up commit `055ff31` reframes README + DESIGN.md + `docs/architecture.svg` to lead with VM-within-VM as the canonical strategy, then disambiguate nested-VM-backend as the actual non-goal. PR body updated. Reply in thread with the corrected answer + memory evidence.

## Cost / benefit

- **Fan-out budget:** ~6–10 tool calls, ~5–15 seconds wall-clock.
- **Re-do cost avoided:** the alternative was a second PR + another round-trip; saved ~30+ tool calls and 1 user-pushback round-trip.
- **Memory evidence quality:** 3 sources (wiki + roadmap + project memory) all agreeing on the same term definition = high-confidence "user is right".

## Related skills to update together

- `finish-the-job` (this skill) — Phase 0 row added for "reconfirm / pushback", anti-pattern pitfall added.
- `memory-search` (Hermes overlay) — no change needed; the 9-store recipe is already canonical there.

## Pre-flight check before shipping a correction

```bash
# 1. Confirm the fan-out evidence is consistent across ≥2 sources
echo "Sources mentioning VM-within-VM:"
grep -rln "VM-within-VM\|VM.in.VM" \
  ~/llm_wiki/wiki ~/roadmap \
  ~/.claude/projects/*/memory/ ~/.hermes/memory/ ~/MEMORY.md \
  2>/dev/null | wc -l
# → should be ≥ 2

# 2. Confirm the source code does NOT explicitly reject the term
grep -niE "VM.in.VM is.{0,30}non.goal|nested VM.{0,30}not.{0,30}implement" \
  ~/path/to/repo/README.md ~/path/to/repo/DESIGN.md 2>/dev/null
# → if matches exist, they may be the wrong framing the user is pushing back on

# 3. Confirm the deployed topology matches the memory description
# (run `docker info` on the target host and compare `KernelVersion` to `uname -r`;
#  mismatch = container-in-VM-in-host = the 3-layer stack)
```

If all 3 checks pass, the correction is the right move. Ship it.