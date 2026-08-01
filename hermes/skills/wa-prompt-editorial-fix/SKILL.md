---
name: wa-prompt-editorial-fix
description: Edit $PROJECT_ROOT/prompts/*.md to fix LLM-spawned behavior surfaced by a campaign — minimal-diff PR against origin/main, no lore dumps, no content deletion. Use when the user reports "the AI keeps doing X" / "spawning Y" / "using Z archetype" / "ignoring setting lore" and you have evidence the issue is prompt-discipline, not code.
---

# Your Project — Prompt editorial fix

## When to use

User surfaces a behavior issue ("auditors keep spawning", "AI keeps calling it a mage tower", "NPCs all talk like modern cops") that the LLM produces during gameplay turns. Evidence class:

- Wiki / campaign log shows the unwanted behavior recurring across turns
- `grep -rn` against `$PROJECT_ROOT/prompts/` does NOT find the offending archetype as a literal prompt string
- Existing examples in the prompts file that LOOK like the issue are actually canonical in-world payloads (e.g. `caius_auditor_arrival` is the in-world Reaper / Prince Caius, not a generic archetype)

That combination means: **the LLM is inventing the archetype, not following prompt text**. Fix is **prompt discipline**, not a code guard. Adding backend enforcement is forbidden by `.claude/skills/root-cause-first/SKILL.md` unless the user explicitly approves it.

## Procedure

1. **Confirm the symptom class.** `grep -rn <term> $PROJECT_ROOT/prompts/`. If hits are mostly audit-trail JSON schema (`audit_events`, `audit_flags`, `dice_audit_events`) or single in-world example payloads, the term is a *symptom the LLM produced*, not prompt content. Stop and treat as prompt-discipline territory.

2. **Find the right rule neighborhood.** NPC-spawning rules live in `$PROJECT_ROOT/prompts/living_world_instruction.md` under `## Lore-Appropriate Enemy Detection` (rules #1–#4: Trigger Whitelist, Escalation Ladder, Name the Mechanism, Forbid Impossible Detection). A new anti-archetype rule belongs as **rule #5 in that section**, not as a new top-level section.

3. **Write the rule as a numbered addition, not a new file.** Match the existing tone (short, declarative, with named examples from the active setting). Reference canonical lore factions/characters so the LLM has concrete substitutes (Harpers, Zhentarim, Flaming Fist, City Watch, Night's Watch, Red Wizard of Thay, Sith, Corps of Discovery — whatever fits the active campaign family). DO NOT add a new file or a long lore appendix. New file creation requires explicit justification per `your-project.com/AGENTS.md` File Protocol.

4. **Leave existing in-world example payloads alone.** A literal `caius_auditor_arrival` in an example payload is NOT a generic archetype — it's a named in-world NPC (Prince Caius, the Reaper). The new rule must not "clean up" such references; doing so would break canonical examples and inflate the diff.

5. **Branch from `origin/main` per `.cursor/rules/pr-branch-from-main.mdc`.** Use `git worktree add -b fix/<topic>-<short-name> $HOME/projects/_wt-<topic> origin/main`. Verify with `git log --oneline origin/main..HEAD` that only your commit is on the branch before pushing.

6. **Commit message format:** `fix(prompts): <one-line summary>`. Body explains symptom + fix + why existing example payloads were left alone.

7. **PR body honesty about `/es` evidence.** Per `your-project.com/AGENTS.md` `## Evidence for mvp_site Production Changes`, prompt-only edits that change model-side behavior technically require `/es`. For +1–10 line editorial fixes with no test harness exercising the spawn path, state honestly in the PR body: "no real-server capture; +N line natural-language instruction; no harness asserts on spawned NPC identity." Offer to spin up a before/after capture if the user wants one. Do NOT fabricate evidence.

8. **Push and open PR.** `git push -u origin HEAD` + `gh pr create --base main --head <branch> --title ... --body ...`. Title MUST be a markdown link `[#<N>](https://github.com/...pull/<N>)` if you reference a PR number per `.cursor/rules/pr-hyperlink.mdc`.

## Pitfalls

- **Don't add backend enforcement.** `root-cause-first` discipline forbids server-side guards for what is fundamentally a prompt-instruction gap. Adding a regex ban on "auditor" / "inquisitor" would block legitimate canonical NPCs and is exactly the anti-pattern.
- **Don't delete content to "make space".** The user said "don't delete content to make space". Editorial additions only.
- **Don't create a new file unless absolutely necessary.** If the rule belongs in an existing section, add it there. New prompt files break the Gemini implicit-cache structure referenced in `your-project.com/AGENTS.md` "Prompt Duplication & Compression".
- **Don't write a lore dump.** Two lines of named-faction examples is enough. The LLM already has the canonical knowledge; it just needs permission to use it instead of inventing.
- **Don't open the PR on a non-main branch.** If you started work on `prXXXX-<topic>` (someone else's PR branch), `git checkout --` the unrelated file and start a fresh worktree off origin/main. Pushing onto someone else's PR head is the 2026-07-14 incident class (`never-push-onto-someone-elses-pr-head`).
- **Don't claim evidence you didn't produce.** Per `proof-before-claim` SOUL.md COMMIT, "want me to run a capture before merging?" is a valid offer but do NOT mark the PR complete-with-evidence.

## Verification

After pushing:

1. `gh pr view <N> --json additions,deletions,changedFiles,baseRefName,headRefName` → confirm `+N/-0`, 1 file, base=`main`.
2. `git log --oneline origin/main..HEAD` in the worktree → confirm only your commit is present.
3. `git status --short` in your **original** worktree → confirm you left no stray edits behind (`git checkout -- <file>` if needed).

## Reference

- [2026-07-24 audit/inquisitor fix — PR #8562](https://github.com/$GITHUB_REPOSITORY/pull/8562) (worked example: +2 lines, rule #5 in `living_world_instruction.md`, no `/es` capture offered honestly)