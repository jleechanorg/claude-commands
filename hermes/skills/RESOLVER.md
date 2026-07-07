# Hermes Skills Resolver

Routes user phrases to skill entries. Each section is a skill with its canonical trigger phrases.

---

## skillify — skillify this, make this proper, add tests and evals, run skillify workflow

**File:** `skills/skillify/SKILL.md`

## sk — /sk, /skillify, skillify this, alias for skillify

**File:** `skills/sk/SKILL.md`
**Triggers:** /sk, /sk this, /sk the workflow, /sk the recipe, skillify alias
**Note:** Thin pointer to the canonical `skillify` skill. Resolves to the same 10-item checklist and the same Hermes self-mod Phase 0 contract.

## agento

**File:** `skills/agento/SKILL.md`
**Triggers:** agento, ao, agent orchestrator

## agento_report

**File:** `skills/agento_report/SKILL.md`
**Triggers:** agento report, ao report, agent orchestrator status

## antigravity-computer-use

**File:** `skills/antigravity-computer-use/SKILL.md`
**Triggers:** antigravity, control google, automate google

## bidi-cmux-alignment

**File:** `skills/bidi-cmux-alignment/SKILL.md`
**Triggers:** steer ao-primary, bidi cmux, bidirectional alignment, operator prompts

## browser-headless-default

**File:** `skills/browser-headless-default/SKILL.md`
**Triggers:** headless browser, hide browser, browser mode, chrome mode, headed mode forbidden, show browser denied, browser headless policy, no visible chrome

## browserclaw

**File:** `skills/browserclaw/SKILL.md`
**Triggers:** browserclaw, capture browser traffic, playwright

## cmux

**File:** `skills/cmux/SKILL.md`
**Triggers:** cmux, terminal multiplexer, send to terminal, send key, workspace surface, capture pane, read screen, list workspaces

## cmux-codex-autoapprove

**File:** `skills/cmux-codex-autoapprove/SKILL.md`
**Triggers:** autoapprove, approval worker, scan approvals, cmux approval

## cmux-surface-report-4h

**File:** `skills/cmux-surface-report-4h/SKILL.md`
**Triggers:** cmux surface report, cmux 4h report, cmux inventory, cmux health digest, 4h cmux check, what is cmux doing, cmux status

## daily-task-prep

**File:** `skills/daily-task-prep/SKILL.md`
**Triggers:** daily task prep, prepare today's tasks, morning task list, today's tasks

## download-campaign

**File:** `skills/download-campaign/SKILL.md`
**Triggers:** download campaign, fetch this campaign, pull from firestore, ingest campaign, get campaign by id, copy campaign X, batch download recent campaigns, scan last N days, scan for >50 entries, last 2 weeks of campaigns, walk a WA campaign, pull Vespera Thul, pull Itachi, download this gem, single campaign download, get the campaign

## dispatch-task

**File:** `skills/dispatch-task/SKILL.md`
**Triggers:** dispatch, ao spawn, ao send, delegate to agent

## dogfood

**File:** `skills/dogfood/SKILL.md`
**Triggers:** dogfood, exploratory qa, test this app, qa test

## dropped-messages

**File:** `skills/dropped-messages/SKILL.md`
**Triggers:** dropped messages, missed messages, lost messages, no response

## executive-assistant

**File:** `skills/executive-assistant/SKILL.md`
**Triggers:** executive assistant, morning sweep, daily briefing

## humanizer

**File:** `skills/humanizer/SKILL.md`
**Triggers:** humanize, remove ai writing, make it sound human

## llm-narration-format-clarifier

**File:** `skills/llm-narration-format-clarifier/SKILL.md`
**Triggers:** llm dropped, llm invents the format, narration drift, show both, show all, format hint needed, add a worked example, prompt is too vague, llm paraphrase, never abbreviate, the narrative is missing, the roll is missing, narration too terse, format hint, make the llm consistently format, /narration-clarify

## meeting-prep

**File:** `skills/meeting-prep/SKILL.md`
**Triggers:** meeting prep, prepare for meeting, briefing for meeting, who is meeting

## sym

**File:** `skills/sym/SKILL.md`
**Triggers:** sym, symphony daemon

## todoist-due-drafts

**File:** `skills/todoist-due-drafts/SKILL.md`
**Triggers:** todoist due, due drafts, process email tasks

## finish-the-job

**File:** `skills/finish-the-job/SKILL.md`
**Triggers:** finish the job, finish it, finish this, finish that, drive to conclusion, see this through, take it all the way, don't stop halfway, why did you stop, hands off mode, hands-off mode, fullsend, full send, take it from here, i started but didn't finish, work started but didn't finish, stalled thread, threads that stalled, threads i started but didn't finish, skillify hermes to be hands off, make hermes hands off, /finish, /auto, auto, automate this, do it autonomously, your call, handle it, ship it, merge it

## finish — slash command (/finish)

**File:** `.claude/commands/finish.md`
**Triggers:** /finish, /finish <goal>

## auto — slash command alias (/auto)

**File:** `.claude/commands/auto.md`
**Triggers:** /auto, /auto <goal>, auto, make it autonomous, hands off

## launchd-autonomy-report — slash command (/launchd-autonomy-report)

**File:** `.claude/commands/launchd-autonomy-report.md`
**Triggers:** /launchd-autonomy-report, score hermes on the left/right-shift tenet, tenet violation detector, autonomy report run, signals A–F, 48h lookback + slack search + /ms cross-reference


## always-pr-never-local-edit

**File:** `skills/workflow/always-pr-never-local-edit/SKILL.md`
**Triggers:** make a PR, open a PR, create a PR, where is the PR, did you make the PR, push the branch, stop doing local changes, never leave local changes, always PR, open the PR, ship it, local edits hanging, dangling commit, push and open the PR, local commit ask then push, stop doing stuff without making a PR

## drive-pr-to-green

**File:** `skills/workflow/drive-pr-to-green/SKILL.md`
**Triggers:** green this PR, /green, green up, drive to green, stop stopping halfway, why did you stop halfway, dont ask me just finish, next time finish the work, actually fix and then merge, do it directly, self merge the PR, fix coderabbit and merge, fix PR comments and merge, finish the PR

## ao-babysit

**File:** `skills/ao-babysit/SKILL.md`
**Triggers:** babysit, watch ao worker, monitor agent, ao session died, keep watch on agent, steer agent

## ao-spawn-minimax-worker

**File:** `skills/ao-spawn-minimax-worker/SKILL.md`
**Triggers:** spawn minimax worker, use minimax CLI, use M3 model, use MiniMax M3, ao spawn minimax, minimax agent, use minimax for AO, M3 worker, minimax PR, minimax branch

## x-to-skill

**File:** `skills/x-to-skill/SKILL.md`

## slack-thread-routing-investigation

**File:** `skills/devops/slack-thread-routing-investigation/SKILL.md`
**Triggers:** slack thread, wrong thread, self-rooted, self threaded, thread routing, thread_ts broken, slack mcp, conversations_add_message, use slack mcp, post not in thread, reply went to wrong thread, /learn slack, /skillify slack mcp, slack formatting broken, emoji fragmented, block kit fragment
**Triggers:** x-to-skill, turn tweet into skill, tweet to skill, share tweet

## wa-prod-data-query

**File:** `skills/wa-prod-data-query/SKILL.md`
**Triggers:** wa prod data, wa retention, wa real users, wa last week, wa this week, who played wa, wa active users, wa signup to first turn, wa engagement, review wa real users, analyze wa retention, real user firestore wa, wa campaigns from real users, real user activity wa, find real wa users, wa user count, wa bounce rate, wa funnel, last week real users

## reddit-competitor-complaints

**File:** `skills/reddit-competitor-complaints/SKILL.md`
**Triggers:** reddit competitor monitor, track reddit complaints, reddit sentiment, daily reddit digest, monitor ai dungeon on reddit, launchd reddit job, competitor reddit intel, pullpush.io, pullpush monitor, reddit complaint digest, ai text rpg reddit, friends and fables reddit, voyage reddit, set up daily reddit digest, /learn reddit monitor

## test-tui-claude-feature-via-cmux

**File:** `skills/test-tui-claude-feature-via-cmux/SKILL.md`
**Triggers:** test claude code feature, verify /, does / work, is the slash command working, slash command test, claude code picker, advisor picker, model picker, --print isnt available, /advisor isnt available, /feature isnt available, tui feature, interactive feature, test tui, cmux test claude, dialog picker, claude code dialog, claude code menu, status indicator, advisor model, opus advisor, sonnet advisor
**Common Confusions:**
- **vs `cmux`** — `cmux` is the general TUI multiplexer skill; this one is specifically for testing Claude Code TUI features (slash commands, pickers, dialogs). Load `cmux` to learn the primitives; load this when the question is "does Claude Code feature X work in the TUI."
- **vs `claude-code`** — `claude-code` is the general Claude Code skill; this one is the narrow "TUI test path" skill, with a script (`scripts/test-tui-feature.sh`) and the rule that `--print` is invalid evidence for TUI features.
- **Anti-pattern: `claude --print "/feature"`** — always returns "isn't available in this environment" for TUI slash commands, which is a non-interactive mode response, NOT a feature-gate failure. The only authoritative test is a real interactive session spawned in cmux.

## qa-test-failure-dismissal-anti-pattern

**File:** `skills/qa-test-failure-dismissal-anti-pattern/SKILL.md`
**Triggers:** pre-existing on main, pre-existing check, is this pre-existing, not blocking, this also fails on main, the suite is already red, flaky test, related failure, same component, ci dismissal, pre-existing verification, pr-introduced vs pre-existing, dismiss a ci failure, bring-to-green dismissal, same test name rule, same-name check, category error dismissal
**Common Confusions:**
- **vs `pr-bring-to-green-inline-cookbook`** — the cookbook has the recipe (`references/pre-existing-vs-pr-introduced-diagnostic.md`); this skill is the anti-pattern card that any agent should load BEFORE writing a dismissal. Use the cookbook to do the work; load this skill to gate the dismissal.
- **vs `production-vs-main-drift`** — the drift skill is for "PR is merged but the bug still reproduces in production"; this skill is for "this PR has a CI failure that looks pre-existing" — the entry point is the PR failure, not a production observation.
- **Anti-pattern: "this also fails on main, not the PR's fault"** — without the four same-name checks, this is a category error. Load this skill before writing that sentence.

## github-api-fallback
GitHub API rate-limit fallback — switch between GraphQL and REST buckets (which drain independently at 5000/hr each), diagnose which bucket is exhausted, avoid the false 'rate-limited' trap when one still has headroom. Triggers: "rate limit exceeded", "HTTP 403", "API rate limit exceeded for user ID", "gh dual-bucket", "fallback to REST", "quota exhausted", "gh api rate_limit", "polling-heavy PR fan-out".

## social-poster
**File:** `skills/social-poster/SKILL.md`
**Triggers:** draft a social post, draft a post, post to social, post to linkedin, post to hacker news, post to reddit, post to twitter, post to threads, post to facebook, post to instagram, draft linkedin post, draft hacker news post, draft reddit post, draft tweet, draft twitter thread, draft instagram caption, draft threads post, show hn, social poster, /social
**Slash alias:** `/social` (file: `~/.claude/commands/social.md`). Drafts social-media posts for 9 platforms (LinkedIn, Hacker News, Twitter/X, Reddit, Threads, Facebook, Instagram, Mastodon, Dev.to), stages them in Aside browser tabs + screenshots, and only posts after the user types "POST APPROVED". Pure template logic by default — no LLM call unless `--use-llm`. Instagram has no web compose; surface caption + mobile instructions instead.
**Common Confusions:**
- **vs `email-drafting`** — `email-drafting` is for Gmail drafts (also gated); `social-poster` is for social platforms + uses Aside instead of gog gmail.
- **vs `reddit-competitor-complaints`** — `reddit-competitor-complaints` is a read-only daily digest job; `social-poster` is a write tool gated by POST APPROVED.
- **Anti-pattern: auto-posting without `POST APPROVED`** — `post_approved.py` hard-exits code 2 without the token. There is NO bypass.
- **Anti-pattern: using Playwright MCP for compose tabs** — Aside is the canonical browser (signed-in `$USER@gmail.com` session); Playwright spawns a fresh context per call and loses cookies.

## harness-postmortem
**File:** `skills/harness-postmortem/SKILL.md`
**Triggers:** autonomy violation, hermes refused, agent refused, agent stopped halfway, stopped halfway, why did hermes stop, why did the agent stop, agent didn't do its job, hermes didn't do its job, you didn't do your job, fix the agent, fix hermes behavior, fix the harness not the task, meta skill, /meta, run meta, harness postmortem, harness retro, harness audit, harness fix, agent failure analysis, run harness postmortem on
**Slash alias:** `/meta` (file: `~/.claude/commands/meta.md`). Internal skill name is `harness-postmortem` to avoid collision with `meta-prompting` (Anthropic/LangGPT/SkillMD), `meta-harness` (ruflo, Nx), and `MetaGPT`. Both names resolve to the same skill file at `skills/harness-postmortem/SKILL.md`.
**Note:** Scope-locked to agent-behavior failures. NEVER investigates the underlying task. Phase 0 anchored on MAST taxonomy (Cemri et al., arXiv:2503.13657) + ETCLOVG layer model (Chen et al., arXiv:2606.06324). Phase 1 uses Observe → Isolate → Simulate → Evaluate 4-step spine (5-Whys retained as Simulate-phase heuristic). Lands fix in SOUL.md / new skill / new test, not the project code path the agent was attempting. Auto-fires on user correction phrases; manual invocation via `/meta <input>` (Slack URL, pasted conversation, or freeform description).
**Common Confusions:**
- **vs `finish-the-job`** — `finish-the-job` drives the *original* task to a verifiable conclusion (green PR / local state / dry-run). `harness-postmortem` is meta: it analyzes the agent's failure to do `finish-the-job`-style work and patches the harness so the failure class stops recurring.
- **vs `harness-engineering`** — `harness-engineering` is the umbrella / reference (SOUL.md rules, never-rewrite pitfalls, verify-CLI-before-quoting). `harness-postmortem` is the per-incident executor: input → MAST+ETCLOVG → Observe→Isolate→Simulate→Evaluate → fix. `harness-postmortem` calls `/harness` (`~/.claude/commands/harness.md`) for the protocol steps.
- **vs `Refinex-Space harness-fix`** — Refinex's `harness-fix` covers bug/regression/incident debugging in general software; `harness-postmortem` is Hermes-runtime-specific (SOUL.md/skills/tests). Prior art is cited in the SKILL.md body, not duplicated.
- **Anti-pattern: "fix the underlying task too while I'm at it"** — `harness-postmortem` is scope-locked. The underlying task is a separate `dispatch-task` job. Do not absorb it under any framing.
