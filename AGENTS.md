# 📚 Reference Export - Agents Configuration

**Note**: This is a reference export from a working Claude Code project. These agent
configurations and guidelines may contain project-specific references that need adaptation.

Customize the following for your project:
- Project-specific paths ($PROJECT_ROOT/ → your main source directory)
- Repository and domain references
- CI commands and test runner paths

---

# jleechanclaw Repo — Agent Guidelines

> **This file is used by agents working on `jleechanorg/jleechanclaw`.**
> The sections below the divider are upstream openclaw/openclaw guidelines (kept for reference).

Before concluding that a Claude command, workflow, or helper is missing, check both repo-local `.claude/` and home `~/.claude/`; prefer repo-local assets for repo-specific work.

## MiniMax Agent — No Separate Binary

`minimax` is NOT a standalone binary. It uses the `claude` CLI with `ANTHROPIC_BASE_URL=https://api.minimax.io/anthropic`.
`which minimax` returning nothing is **expected** — do not switch to codex/claude as a workaround.

Full details: `~/.claude/skills/minimax.md`

## Config-First Principle (jleechanclaw-specific)

This repo's primary job is **configuring openclaw**, not building new software.

**Before writing any code**, ask: can this be done by editing `openclaw-config/`?

| Goal | Prefer |
|---|---|
| Change jleechanclaw behavior | Edit `openclaw-config/SOUL.md` |
| Change tool access | Edit `openclaw-config/TOOLS.md` or `openclaw.json` |
| Change memory/history behavior | Edit `openclaw.json` (memorySearch, dmHistoryLimit) |
| Change agent identity | Edit `openclaw-config/USER.md` |
| Add cron/scheduled tasks (Slack, backup, memory) | Edit `openclaw-config/cron/` |
| Add/change **PR automation** jobs | Edit `~/.openclaw/cron/jobs.json` directly (exception — not tracked in repo) |
| Genuinely new orchestration capability | `src/orchestration/` Python — last resort only |

## Slack — Posting as $USER (not the bot)

To post to Slack **as $USER** (not as the openclaw bot):

```bash
source ~/.profile   # loads SLACK_USER_TOKEN — not in env by default in Claude sessions
curl -s -X POST "https://slack.com/api/chat.postMessage" \
  -H "Authorization: Bearer $SLACK_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"channel": "CHANNEL_ID", "text": "your message"}'
```

- `SLACK_USER_TOKEN` (`xoxp-...`) lives in `~/.profile`; run `source ~/.profile` before use.
- `OPENCLAW_SLACK_BOT_TOKEN` (`xoxb-...`) is already in env but posts as `openclaw` bot — wrong for "post as me".
- No Slack MCP server needed. Channel IDs: `#ai-slack-test` → `C0AKALZ4CKW`.
- Confirm identity: `auth.test` should return `"user":"$USER"`.

## Testing Philosophy — Real Over Fake

When testing the mctrl dispatch loop, **always run a real test**: real Slack trigger, real ai_orch spawn, real supervisor notification. Do NOT use fake registry entries with dead sessions — that only tests the reconciler in isolation, not the full system.

For any suite or artifact under `testing_*/`, the rule is stricter: **no fakes, no mocks, no monkeypatching, no simulated registry/outbox/session state, and no code/config mutation of the system under test.** `testing_*` is reserved for black-box, observe-only verification. The harness may inject a real trigger (for example, post to Slack as $USER) and then only observe logs, Slack, OpenClaw-visible outputs, and other externally visible evidence.

Anything that replaces tmux/git/OpenClaw/Slack behavior with controlled outcomes is not a `testing_*` test in this repo. Put that coverage in `src/tests/` and label it as unit/integration/simulated coverage instead of E2E.

Real mctrl test checklist:
1. `source ~/.profile` — get `SLACK_USER_TOKEN`
2. Post trigger to `#ai-slack-test` as $USER, capture `trigger_ts`
3. Create a real bead: `bd create ...`
4. Run `PYTHONPATH=src python -m orchestration.dispatch_task --bead-id ... --task "..." --slack-trigger-ts <trigger_ts>`
5. Wait for `ai.mctrl.supervisor` to detect session exit (≤60s after agent finishes)
6. Confirm real thread reply appears under trigger, real DM received

## Scheduling Guardrail (jleechanclaw-specific)

- Forbidden: editing system `crontab` for OpenClaw reminder, scheduling, or automation jobs.
- Required: use OpenClaw gateway cron workflow only (`openclaw cron ...` subcommands and `openclaw-config/cron/` config).

**The test:** if the change could be expressed as a sentence in SOUL.md, it belongs in SOUL.md.

See `roadmap/NATURAL_LANGUAGE_DISPATCH.md` for the design rationale and `CLAUDE.md` for full project rules.

### Where PR automation jobs run

Automated PR comments (comment-validation, fixpr, fix-comment, codex-update) come from `jleechanorg-pr-monitor` running via the **openclaw gateway's built-in cron scheduler**. On macOS, these jobs do not appear in `crontab -l`. On Linux setups bootstrapped with `scripts/claude_start.sh`, a fallback crontab entry may still exist — check both.

- Job definitions (live): `~/.openclaw/cron/jobs.json` — **not** tracked in `openclaw-config/cron/` (that file contains only Slack check-ins and backup jobs)
- To modify: edit `~/.openclaw/cron/jobs.json` directly
- Binary: `/opt/homebrew/bin/jleechanorg-pr-monitor` (`pip install jleechanorg-automation`)
- Source: `~/projects/your-project.com/automation/`
- Executor: `ai.openclaw.gateway` launchd service (the cron scheduler is built into the gateway process)

## Durable Behavior Goal (Non-Oneoff)

Jeffrey's operating goal for OpenClaw is deterministic behavior:
- He should be able to talk to OpenClaw the same way repeatedly and get the right behavior every time.
- Fixes must be systemic (policy/config/workflow/contracts), not incident-by-incident patches.

When implementing behavior changes, apply these rules:
1. Prefer global defaults in `openclaw-config/` over per-thread/per-PR exceptions.
2. Encode routing/endpoint/repo rules as explicit guardrails (deny-by-default on ambiguity).
3. Add prevention checks (CI/policy checks, preflight validation, or launchd/runtime checks) so regressions fail closed.
4. For any one-off hotfix, also add a follow-up durable guardrail before considering the work complete.
5. Validate by replaying the same request pattern in multiple contexts (not just the original failing thread).

---

# Repository Guidelines (openclaw/openclaw upstream reference)

- Repo: https://github.com/openclaw/openclaw
- GitHub issues/comments/PR comments: use literal multiline strings or `-F - <<'EOF'` (or $'...') for real newlines; never embed "\\n".

## Critical Rules

| Rule | Requirement |
|------|-------------|
| **CI test failures are BLOCKERS** | **ALL failing tests in PRs must be fixed - NEVER merge with failing CI checks** |
| **No unrelated deletions** | **NEVER delete content from origin/main unrelated to current task** |
| No false checkmarks | Only mark items complete when 100% verified |
| Test failures | Fix ALL failures, no excuses, no "pre-existing" excuses |
| Integration verification | Verify config + trigger + logs with evidence |
| No fake code | Audit existing code before writing new implementations |
| Code centralization | Search for existing code/utilities before writing new ones |
| PR merges | Never merge without explicit user approval |
| No bash arguments | NEVER pass bash arguments in commands without explicit user approval |

## LLM Architecture Principles

### Core Rule: LLM Decides, Server Executes

For AI-driven features (content generation, analysis, decisions):
- **LLM gets full context** - Don't strip information "to optimize"
- **LLM makes decisions** - Don't pre-compute what the LLM should decide
- **Server executes actions** - Tools and state changes happen server-side
- **LLM incorporates results** - Final output uses real data from tool execution

### Anti-Patterns (BANNED)

- Keyword-based intent detection to bypass LLM judgment
- Stripping tool definitions based on predicted need
- Pre-computing results the LLM should request
- "Optimizations" that reduce information available to the LLM
- Disabled-by-default env-var feature flags for user-requested functionality
- Creating new env vars without clear justification (use constants; env vars only for credentials/URLs)

### Error Handling Philosophy

Warnings only - no silent fixes with fallback generation. When LLM output is missing expected fields or violates requirements, log warnings and let validation/invariant checks surface the issue. Never silently fix with default content.

## File Protocols

### New File Creation — Extreme Anti-Creation Bias

**Default: NO NEW FILES.** Prove why integration is impossible.

**Integration hierarchy:** existing similar file → utility file → existing module → existing class method → config file → last resort: new file

Before creating a new file:
1. Search for existing similar functionality
2. Try integrating into existing files
3. Only create new file if integration is truly impossible
4. Document justification for the new file

### File Deletion Protocol

**CRITICAL:** Never delete unrelated content from origin/main

Before deleting any file:
1. Search all imports/references to it across the repo
2. Fix/update all references
3. Verify no broken dependencies (run tests, type checks)
4. Delete only after the above is complete
5. NEVER delete: LLM prompts/schemas, user docs, test infrastructure without approval

**When in doubt: ASK first**

### File Placement

- TypeScript/Source → `src/`
- Scripts → `scripts/`
- Tests → colocated `*.test.ts`
- Docs → `docs/`
- No `_v2`, `_new`, `_backup` files - edit existing files instead

## Project Structure & Module Organization

- Source code: `src/` (CLI wiring in `src/cli`, commands in `src/commands`, web provider in `src/provider-web.ts`, infra in `src/infra`, media pipeline in `src/media`).
- Tests: colocated `*.test.ts`.
- Docs: `docs/` (images, queue, Pi config). Built output lives in `dist/`.
- Plugins/extensions: live under `extensions/*` (workspace packages). Keep plugin-only deps in the extension `package.json`; do not add them to the root `package.json` unless core uses them.
- Plugins: install runs `npm install --omit=dev` in plugin dir; runtime deps must live in `dependencies`. Avoid `workspace:*` in `dependencies` (npm install breaks); put `openclaw` in `devDependencies` or `peerDependencies` instead (runtime resolves `openclaw/plugin-sdk` via jiti alias).
- Installers served from `https://openclaw.ai/*`: live in the sibling repo `../openclaw.ai` (`public/install.sh`, `public/install-cli.sh`, `public/install.ps1`).
- Messaging channels: always consider **all** built-in + extension channels when refactoring shared logic (routing, allowlists, pairing, command gating, onboarding, docs).
  - Core channel docs: `docs/channels/`
  - Core channel code: `src/telegram`, `src/discord`, `src/slack`, `src/signal`, `src/imessage`, `src/web` (WhatsApp web), `src/channels`, `src/routing`
  - Extensions (channel plugins): `extensions/*` (e.g. `extensions/msteams`, `extensions/matrix`, `extensions/zalo`, `extensions/zalouser`, `extensions/voice-call`)
- When adding channels/extensions/apps/docs, update `.github/labeler.yml` and create matching GitHub labels (use existing channel/extension label colors).

## Docs Linking (Mintlify)

- Docs are hosted on Mintlify (docs.openclaw.ai).
- Internal doc links in `docs/**/*.md`: root-relative, no `.md`/`.mdx` (example: `[Config](/configuration)`).
- When working with documentation, read the mintlify skill.
- Section cross-references: use anchors on root-relative paths (example: `[Hooks](/configuration#hooks)`).
- Doc headings and anchors: avoid em dashes and apostrophes in headings because they break Mintlify anchor links.
- When Peter asks for links, reply with full `https://docs.openclaw.ai/...` URLs (not root-relative).
- When you touch docs, end the reply with the `https://docs.openclaw.ai/...` URLs you referenced.
- README (GitHub): keep absolute docs URLs (`https://docs.openclaw.ai/...`) so links work on GitHub.
- Docs content must be generic: no personal device names/hostnames/paths; use placeholders like `user@gateway-host` and “gateway host”.

## Docs i18n (zh-CN)

- `docs/zh-CN/**` is generated; do not edit unless the user explicitly asks.
- Pipeline: update English docs → adjust glossary (`docs/.i18n/glossary.zh-CN.json`) → run `scripts/docs-i18n` → apply targeted fixes only if instructed.
- Translation memory: `docs/.i18n/zh-CN.tm.jsonl` (generated).
- See `docs/.i18n/README.md`.
- The pipeline can be slow/inefficient; if it’s dragging, ping @jospalmbier on Discord instead of hacking around it.

## exe.dev VM ops (general)

- Access: stable path is `ssh exe.dev` then `ssh vm-name` (assume SSH key already set).
- SSH flaky: use exe.dev web terminal or Shelley (web agent); keep a tmux session for long ops.
- Update: `sudo npm i -g openclaw@latest` (global install needs root on `/usr/lib/node_modules`).
- Config: use `openclaw config set ...`; ensure `gateway.mode=local` is set.
- Discord: store raw token only (no `DISCORD_BOT_TOKEN=` prefix).
- Restart: stop old gateway and run:
  `pkill -9 -f openclaw-gateway || true; nohup openclaw gateway run --bind loopback --port 18789 --force > /tmp/openclaw-gateway.log 2>&1 &`
- Verify: `openclaw channels status --probe`, `ss -ltnp | rg 18789`, `tail -n 120 /tmp/openclaw-gateway.log`.

## Build, Test, and Development Commands

- Runtime baseline: Node **22+** (keep Node + Bun paths working).
- Install deps: `pnpm install`
- If deps are missing (for example `node_modules` missing, `vitest not found`, or `command not found`), run the repo’s package-manager install command (prefer lockfile/README-defined PM), then rerun the exact requested command once. Apply this to test/build/lint/typecheck/dev commands; if retry still fails, report the command and first actionable error.
- Pre-commit hooks: `prek install` (runs same checks as CI)
- Also supported: `bun install` (keep `pnpm-lock.yaml` + Bun patching in sync when touching deps/patches).
- Prefer Bun for TypeScript execution (scripts, dev, tests): `bun <file.ts>` / `bunx <tool>`.
- Run CLI in dev: `pnpm openclaw ...` (bun) or `pnpm dev`.
- Node remains supported for running built output (`dist/*`) and production installs.
- Mac packaging (dev): `scripts/package-mac-app.sh` defaults to current arch. Release checklist: `docs/platforms/mac/release.md`.
- Type-check/build: `pnpm build`
- TypeScript checks: `pnpm tsgo`
- Lint/format: `pnpm check`
- Format check: `pnpm format` (oxfmt --check)
- Format fix: `pnpm format:fix` (oxfmt --write)
- Tests: `pnpm test` (vitest); coverage: `pnpm test:coverage`

## Coding Style & Naming Conventions

- Language: TypeScript (ESM). Prefer strict typing; avoid `any`.
- Formatting/linting via Oxlint and Oxfmt; run `pnpm check` before commits.
- Add brief code comments for tricky or non-obvious logic.
- Keep files concise; extract helpers instead of “V2” copies. Use existing patterns for CLI options and dependency injection via `createDefaultDeps`.
- Aim to keep files under ~700 LOC; guideline only (not a hard guardrail). Split/refactor when it improves clarity or testability.
- Naming: use **OpenClaw** for product/app/docs headings; use `openclaw` for CLI command, package/binary, paths, and config keys.

## Release Channels (Naming)

- stable: tagged releases only (e.g. `vYYYY.M.D`), npm dist-tag `latest`.
- beta: prerelease tags `vYYYY.M.D-beta.N`, npm dist-tag `beta` (may ship without macOS app).
- dev: moving head on `main` (no tag; git checkout main).

## Testing Guidelines

- Framework: Vitest with V8 coverage thresholds (70% lines/branches/functions/statements).
- Naming: match source names with `*.test.ts`; e2e in `*.e2e.test.ts`.
- Run `pnpm test` (or `pnpm test:coverage`) before pushing when you touch logic.
- Do not set test workers above 16; tried already.
- Live tests (real keys): `CLAWDBOT_LIVE_TEST=1 pnpm test:live` (OpenClaw-only) or `LIVE=1 pnpm test:live` (includes provider live tests). Docker: `pnpm test:docker:live-models`, `pnpm test:docker:live-gateway`. Onboarding Docker E2E: `pnpm test:docker:onboard`.
- Full kit + what’s covered: `docs/testing.md`.
- Changelog: user-facing changes only; no internal/meta notes (version alignment, appcast reminders, release process).
- Pure test additions/fixes generally do **not** need a changelog entry unless they alter user-facing behavior or the user asks for one.
- Mobile: before using a simulator, check for connected real devices (iOS + Android) and prefer them when available.

## Commit & Pull Request Guidelines

**Full maintainer PR workflow (optional):** If you want the repo's end-to-end maintainer workflow (triage order, quality bar, rebase rules, commit/changelog conventions, co-contributor policy, and the `review-pr` > `prepare-pr` > `merge-pr` pipeline), see `.agents/skills/PR_WORKFLOW.md`. Maintainers may use other workflows; when a maintainer specifies a workflow, follow that. If no workflow is specified, default to PR_WORKFLOW.

### PR & Merge Protocols

- **NEVER merge PRs without explicit user approval**
- **MANDATORY: ALL CI tests must pass before merge** - Any failing test is a blocker, no exceptions
  - `mergeable: "MERGEABLE"` only means no conflicts - does NOT mean tests pass
  - Always check `statusCheckRollup` for failing checks before declaring PR ready
  - If ANY required check shows `conclusion: "FAILURE"`, the PR is NOT ready to merge
- Verify agent work: file existence check, `git diff --stat`, `git status`
- `/pr` commands must create actual PR with working URL - never give manual steps

### PR Description Requirements

**Required sections:**
- Summary (1-4 bullets highlighting key changes)
- Changes (what changed, before → after → why for significant modifications)
- Testing (verification approach, evidence if applicable)
- Known Limitations (pre-existing issues, out of scope items)

**Format:** Clear, concise, with specific function/variable names where relevant

### CodeRabbit Review Protocol
After pushing fixes that address review comments authored by `coderabbitai`:
1. Post a PR comment: `@coderabbitai all good?`
2. This triggers CodeRabbit to re-review and verify the fixes are resolved.

Do NOT ping CodeRabbit on a timer or without a preceding push. Only trigger after a fresh commit lands on the PR branch.

### Commit Guidelines

- Create commits with `scripts/committer "<msg>" <file...>`; avoid manual `git add`/`git commit` so staging stays scoped.
- Follow concise, action-oriented commit messages (e.g., `CLI: add verbose flag to send`).
- Group related changes; avoid bundling unrelated refactors.
- PR submission template (canonical): `.github/pull_request_template.md`
- Issue submission templates (canonical): `.github/ISSUE_TEMPLATE/`
- **MUST READ BEFORE SUBMITTING PR OR ISSUE:** [Agent Submission Control Policy](.agents/AGENT_SUBMISSION_CONTROL_POLICY.md)

## Shorthand Commands

- `sync`: if working tree is dirty, commit all changes (pick a sensible Conventional Commit message), then `git pull --rebase`; if rebase conflicts and cannot resolve, stop; otherwise `git push`.

## Git Notes

- If `git branch -d/-D <branch>` is policy-blocked, delete the local ref directly: `git update-ref -d refs/heads/<branch>`.

## Security & Configuration Tips

- Web provider stores creds at `~/.openclaw/credentials/`; rerun `openclaw login` if logged out.
- Pi sessions live under `~/.openclaw/sessions/` by default; the base directory is not configurable.
- Environment variables: see `~/.profile`.
- Never commit or publish real phone numbers, videos, or live configuration values. Use obviously fake placeholders in docs, tests, and examples.
- Release flow: always read `docs/reference/RELEASING.md` and `docs/platforms/mac/release.md` before any release work; do not ask routine questions once those docs answer them.

## Troubleshooting

- Rebrand/migration issues or legacy config/service warnings: run `openclaw doctor` (see `docs/gateway/doctor.md`).

## Agent-Specific Notes

- Vocabulary: "makeup" = "mac app".
- Never edit `node_modules` (global/Homebrew/npm/git installs too). Updates overwrite. Skill notes go in `tools.md` or `AGENTS.md`.
- When adding a new `AGENTS.md` anywhere in the repo, also add a `CLAUDE.md` symlink pointing to it (example: `ln -s AGENTS.md CLAUDE.md`).
- Signal: "update fly" => `fly ssh console -a flawd-bot -C "bash -lc 'cd /data/clawd/openclaw && git pull --rebase origin main'"` then `fly machines restart e825232f34d058 -a flawd-bot`.
- When working on a GitHub Issue or PR, print the full URL at the end of the task.
- When answering questions, respond with high-confidence answers only: verify in code; do not guess.
- Never update the Carbon dependency.
- Any dependency with `pnpm.patchedDependencies` must use an exact version (no `^`/`~`).
- Patching dependencies (pnpm patches, overrides, or vendored changes) requires explicit approval; do not do this by default.
- CLI progress: use `src/cli/progress.ts` (`osc-progress` + `@clack/prompts` spinner); don’t hand-roll spinners/bars.
- Status output: keep tables + ANSI-safe wrapping (`src/terminal/table.ts`); `status --all` = read-only/pasteable, `status --deep` = probes.
- Gateway currently runs only as the menubar app; there is no separate LaunchAgent/helper label installed. Restart via the OpenClaw Mac app or `scripts/restart-mac.sh`; to verify/kill use `launchctl print gui/$UID | grep openclaw` rather than assuming a fixed label. **When debugging on macOS, start/stop the gateway via the app, not ad-hoc tmux sessions; kill any temporary tunnels before handoff.**
- macOS logs: use `./scripts/clawlog.sh` to query unified logs for the OpenClaw subsystem; it supports follow/tail/category filters and expects passwordless sudo for `/usr/bin/log`.
- If shared guardrails are available locally, review them; otherwise follow this repo's guidance.
- SwiftUI state management (iOS/macOS): prefer the `Observation` framework (`@Observable`, `@Bindable`) over `ObservableObject`/`@StateObject`; don’t introduce new `ObservableObject` unless required for compatibility, and migrate existing usages when touching related code.
- Connection providers: when adding a new connection, update every UI surface and docs (macOS app, web UI, mobile if applicable, onboarding/overview docs) and add matching status + configuration forms so provider lists and settings stay in sync.
- Version locations: `package.json` (CLI), `apps/android/app/build.gradle.kts` (versionName/versionCode), `apps/ios/Sources/Info.plist` + `apps/ios/Tests/Info.plist` (CFBundleShortVersionString/CFBundleVersion), `apps/macos/Sources/OpenClaw/Resources/Info.plist` (CFBundleShortVersionString/CFBundleVersion), `docs/install/updating.md` (pinned npm version), `docs/platforms/mac/release.md` (APP_VERSION/APP_BUILD examples), Peekaboo Xcode projects/Info.plists (MARKETING_VERSION/CURRENT_PROJECT_VERSION).
- "Bump version everywhere" means all version locations above **except** `appcast.xml` (only touch appcast when cutting a new macOS Sparkle release).
- **Restart apps:** “restart iOS/Android apps” means rebuild (recompile/install) and relaunch, not just kill/launch.
- **Device checks:** before testing, verify connected real devices (iOS/Android) before reaching for simulators/emulators.
- iOS Team ID lookup: `security find-identity -p codesigning -v` → use Apple Development (…) TEAMID. Fallback: `defaults read com.apple.dt.Xcode IDEProvisioningTeamIdentifiers`.
- A2UI bundle hash: `src/canvas-host/a2ui/.bundle.hash` is auto-generated; ignore unexpected changes, and only regenerate via `pnpm canvas:a2ui:bundle` (or `scripts/bundle-a2ui.sh`) when needed. Commit the hash as a separate commit.
- Release signing/notary keys are managed outside the repo; follow internal release docs.
- Notary auth env vars (`APP_STORE_CONNECT_ISSUER_ID`, `APP_STORE_CONNECT_KEY_ID`, `APP_STORE_CONNECT_API_KEY_P8`) are expected in your environment (per internal release docs).
- **Multi-agent safety:** do **not** create/apply/drop `git stash` entries unless explicitly requested (this includes `git pull --rebase --autostash`). Assume other agents may be working; keep unrelated WIP untouched and avoid cross-cutting state changes.
- **Multi-agent safety:** when the user says "push", you may `git pull --rebase` to integrate latest changes (never discard other agents' work). When the user says "commit", scope to your changes only. When the user says "commit all", commit everything in grouped chunks.
- **Multi-agent safety:** do **not** create/remove/modify `git worktree` checkouts (or edit `.worktrees/*`) unless explicitly requested.
- **Multi-agent safety:** do **not** switch branches / check out a different branch unless explicitly requested.
- **Multi-agent safety:** running multiple agents is OK as long as each agent has its own session.
- **Multi-agent safety:** when you see unrecognized files, keep going; focus on your changes and commit only those.
- Lint/format churn:
  - If staged+unstaged diffs are formatting-only, auto-resolve without asking.
  - If commit/push already requested, auto-stage and include formatting-only follow-ups in the same commit (or a tiny follow-up commit if needed), no extra confirmation.
  - Only ask when changes are semantic (logic/data/behavior).
- Lobster seam: use the shared CLI palette in `src/terminal/palette.ts` (no hardcoded colors); apply palette to onboarding/config prompts and other TTY UI output as needed.
- **Multi-agent safety:** focus reports on your edits; avoid guard-rail disclaimers unless truly blocked; when multiple agents touch the same file, continue if safe; end with a brief “other files present” note only if relevant.
- Bug investigations: read source code of relevant npm dependencies and all related local code before concluding; aim for high-confidence root cause.
- Code style: add brief comments for tricky logic; keep files under ~500 LOC when feasible (split/refactor as needed).
- Tool schema guardrails (google-antigravity): avoid `Type.Union` in tool input schemas; no `anyOf`/`oneOf`/`allOf`. Use `stringEnum`/`optionalStringEnum` (Type.Unsafe enum) for string lists, and `Type.Optional(...)` instead of `... | null`. Keep top-level tool schema as `type: "object"` with `properties`.
- Tool schema guardrails: avoid raw `format` property names in tool schemas; some validators treat `format` as a reserved keyword and reject the schema.
- When asked to open a “session” file, open the Pi session logs under `~/.openclaw/agents/<agentId>/sessions/*.jsonl` (use the `agent=<id>` value in the Runtime line of the system prompt; newest unless a specific ID is given), not the default `sessions.json`. If logs are needed from another machine, SSH via Tailscale and read the same path there.
- Do not rebuild the macOS app over SSH; rebuilds must be run directly on the Mac.
- Never send streaming/partial replies to external messaging surfaces (WhatsApp, Telegram); only final replies should be delivered there. Streaming/tool events may still go to internal UIs/control channel.
- Voice wake forwarding tips:
  - Command template should stay `openclaw-mac agent --message "${text}" --thinking low`; `VoiceWakeForwarder` already shell-escapes `${text}`. Don’t add extra quotes.
  - launchd PATH is minimal; ensure the app’s launch agent PATH includes standard system paths plus your pnpm bin (typically `$HOME/Library/pnpm`) so `pnpm`/`openclaw` binaries resolve when invoked via `openclaw-mac`.
- For manual `openclaw message send` messages that include `!`, use the heredoc pattern noted below to avoid the Bash tool’s escaping.
- Release guardrails: do not change version numbers without operator’s explicit consent; always ask permission before running any npm publish/release step.

## NPM + 1Password (publish/verify)

- Use the 1password skill; all `op` commands must run inside a fresh tmux session.
- Sign in: `eval "$(op signin --account my.1password.com)"` (app unlocked + integration on).
- OTP: `op read 'op://Private/Npmjs/one-time password?attribute=otp'`.
- Publish: `npm publish --access public --otp="<otp>"` (run from the package dir).
- Verify without local npmrc side effects: `npm view <pkg> version --userconfig "$(mktemp)"`.
- Kill the tmux session after publish.

<!-- BEGIN BEADS INTEGRATION -->
## Issue Tracking with bd (beads)

**IMPORTANT**: This project uses **bd (beads)** for ALL issue tracking. Do NOT use markdown TODOs, task lists, or other tracking methods.

### Why bd?

- Dependency-aware: Track blockers and relationships between issues
- Git-friendly: Auto-syncs to JSONL for version control
- Agent-optimized: JSON output, ready work detection, discovered-from links
- Prevents duplicate tracking systems and confusion

### Quick Start

**Check for ready work:**

```bash
bd ready --json
```

**Create new issues:**

```bash
bd create "Issue title" --description="Detailed context" -t bug|feature|task -p 0-4 --json
bd create "Issue title" --description="What this issue is about" -p 1 --deps discovered-from:bd-123 --json
```

**Claim and update:**

```bash
bd update bd-42 --status in_progress --json
bd update bd-42 --priority 1 --json
```

**Complete work:**

```bash
bd close bd-42 --reason "Completed" --json
```

### Issue Types

- `bug` - Something broken
- `feature` - New functionality
- `task` - Work item (tests, docs, refactoring)
- `epic` - Large feature with subtasks
- `chore` - Maintenance (dependencies, tooling)

### Priorities

- `0` - Critical (security, data loss, broken builds)
- `1` - High (major features, important bugs)
- `2` - Medium (default, nice-to-have)
- `3` - Low (polish, optimization)
- `4` - Backlog (future ideas)

### Workflow for AI Agents

1. **Check ready work**: `bd ready` shows unblocked issues
2. **Claim your task**: `bd update <id> --status in_progress`
3. **Work on it**: Implement, test, document
4. **Discover new work?** Create linked issue:
   - `bd create "Found bug" --description="Details about what was found" -p 1 --deps discovered-from:<parent-id>`
5. **Complete**: `bd close <id> --reason "Done"`

### Auto-Sync

bd automatically syncs with git:

- Exports to `.beads/issues.jsonl` after changes (5s debounce)
- Imports from JSONL when newer (e.g., after `git pull`)
- No manual export/import needed!

### Important Rules

- ✅ Use bd for ALL task tracking
- ✅ Always use `--json` flag for programmatic use
- ✅ Link discovered work with `discovered-from` dependencies
- ✅ Check `bd ready` before asking "what should I work on?"
- ❌ Do NOT create markdown TODO lists
- ❌ Do NOT use external issue trackers
- ❌ Do NOT duplicate tracking systems

For more details, see README.md and docs/QUICKSTART.md.

<!-- END BEADS INTEGRATION -->

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
