---
name: outbound-secret-redaction-gate
version: 1.0.0
description: "Prevent AI agents from publishing live credentials in outbound GitHub/Slack/email/gist artifacts. Trigger when an agent reads git remote -v, .git/config, gh auth status -t, env, printenv, cat ~/.bashrc, an AO runner yaml, the ao-go-daemon plist, or any disk_diagnosis report and pastes the raw output into a public artifact - especially after a GitHub Personal Access Token found in issue email or when the user says 'PAT in issue', 'secret leak', 'yet again', 'token exposed', 'credential in GitHub', 'rotate the PAT', or asks for a postmortem on a recurring credential leak. Verified 2026-07-17: jleechanorg/disk_magician issue 25 was opened by an AI disk/swarm run that pasted three live PATs copied verbatim from local .git/config remote URLs (one inline https://x-access-token:ghp_...@...git, two more PATs surfaced from disk-scan output). Same root cause as the 2026-07-12 incident - recurring 3rd+ time."
tags: [security, secrets, github, slack, public-artifact, redaction, gate, pat, credential, disk_magician]
---

# Outbound secret-redaction gate (class: PAT/API token leaks in public artifacts)

When an AI agent - Claude Code, Codex, local Hermes, AO worker - reads system state that contains credentials and pastes the raw output into any artifact that can leave the machine, the credentials leak. This skill is the canonical recipe to (a) scan the outbound body before send, (b) rotate every sink that holds a leaked credential in one pass, and (c) delete/rewrite the public artifact that already leaked.

## When to use this skill

- GitHub emailed Jeffrey "Personal Access Token found in issue" / "found in commit" / "found in gist" / "found in pull request".
- The user says "PAT in issue #N", "credential exposed", "rotate the PAT", "token leaked", "yet again", "how did this happen", "stop agents from leaking secrets".
- A disk-diagnosis / swarm / security-report agent is about to call `gh issue create`, `gh pr create`, `gh pr comment`, `gh gist create`, or `mcp__slack__conversations_add_message` with body content that includes `git remote -v`, `.git/config`, `gh auth status -t`, `env`, `printenv`, `cat ~/.bashrc`, an `ao runner *.yaml`, or any diagnostic that touches secrets.
- An issue body on any jleechanorg/* or Agnt-F/* repo contains or contained a live PAT (or Slack `xox[pabrs]-` token, AWS access key, etc.) - regardless of whether the agent that posted it is identifiable.
- The user explicitly invokes `/finish-the-job` for a secret-leak incident.

## Failure pattern (root cause)

Three gaps let the same leak recur across sessions:

1. **No outbound-side gate at the canonical send boundary.** Every report path (issue create, PR comment, Slack post, gist) re-derives the leak risk. Agents read `.git/config` legitimately, then paste it legitimately, then leak.
2. **One-shot "restore neutral URL" cleanup is not failure-safe.** If any agent later re-runs `git remote set-url origin https://x-access-token:***@...` (the 2026-07-12 session did exactly this to take a credential along for a single git push), the URL returns to disk and to the next report. The fix needs a pre-write check at the git layer too.
3. **PATs live in many sinks simultaneously.** Keychain, `~/.bashrc`, ezgha `~/.config/ezgha/gh_token`, `~/Library/LaunchAgents/ai.agento.ao-go-daemon.plist`, every `~/.config/ao-runner/<org>--<repo>.yaml`, plus any plaintext `~/.config/gh/hosts.yml.bak*`. Until ALL sinks are scrubbed in one pass, a single stale copy keeps the same credential alive. Future remediation must enumerate sinks in one pass.

## Exact-text Slack delivery verification

When a request requires an **exact** Slack body (especially reminders, compliance text, or quoted copy), treat the send receipt as necessary but not sufficient. Slack may normalize Unicode emoji into colon aliases and auto-link bare domains in API readback, so verify the stored message rather than trusting only the rendered client view.

1. Run the secret gate on the exact outbound body before transport.
2. Send once with `chat.postMessage` and capture the returned `channel` and `ts` immediately. Do not retry or delete based only on a later permalink failure.
3. Verify that exact `ts` with `conversations.history`, `conversations.replies`, or another read API. Compare the returned `text` to the requested body after accounting only for documented Slack canonicalization such as emoji aliases and URL auto-link wrappers.
4. If the response is missing, ambiguous, or appears under a different bot identity, report delivery as **unverified** and investigate the returned `ts` before claiming success. Never claim exact delivery from a channel-wide “latest message” scan.
5. Keep the user-facing report short: state `Delivered` only with the API receipt plus exact-message verification; otherwise state the precise verification blocker.

A session-specific failure transcript and comparison recipe live in `references/exact-text-slack-delivery.md`.

## Hard requirements (any artifact leaving the machine)

- **No live credential value** in any outbound artifact - issue body, PR body/comment, Slack post, gist, email. Redact to prefix+suffix (e.g. `ghp_abc…xyz`) or `[REDACTED]`. Block the send when a PAT/token regex matches.
- **No credentials embedded in HTTPS remotes** (`https://x-access-token:…@github.com/…` or `https://user:token@…`). Strip userinfo before send.
- **Reports name paths and token fingerprints only** (e.g. `ghp_a18781ec8718…`), never the token itself. Fingerprints must be at least 12 hex chars.
- **Synthetic tokens only in tests.** Fixtures must not contain real values.

## Mandatory canonical regex set

Every gate implementation MUST scan with these patterns:

| Pattern | Why |
|---|---|
| `ghp_[A-Za-z0-9_]{20,}` | GitHub classic PAT |
| `gho_[A-Za-z0-9_]{20,}` | GitHub OAuth token |
| `ghu_[A-Za-z0-9_]{20,}` | GitHub user token |
| `ghs_[A-Za-z0-9_]{20,}` | GitHub server-to-server |
| `ghr_[A-Za-z0-9_]{20,}` | GitHub refresh token |
| `github_pat_[A-Za-z0-9_]{20,}` | GitHub fine-grained PAT |
| `xox[abprs]-[A-Za-z0-9-]{10,}` | Slack tokens |
| `https?://[^/\s:@]+:[^/\s@]+@github\.com/` | Credentialed HTTPS remote |

The Python regex used in production (compiled and verified):

```python
import re
PAT_RE = re.compile(
    r"(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[abprs]-[A-Za-z0-9-]{10,}|"
    r"https?://[^/\s:@]+:[^/\s@]+@github\.com/[^\s'\"<>]+)"
)
```

Compile-test: `python3 -c "import re; re.compile(r'(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[abprs]-[A-Za-z0-9-]{10,}|https?://[^/\s:@]+:[^/\s@]+@github\.com/[^\s\'\"<>]+)')"` must succeed.

## Steps - incident response

### Phase 0 - Stop the bleed (do FIRST)

1. **Generate a new PAT through the GitHub web UI** (the user typed `/browser to get a new PAT` - they want this). Use the Aside MCP browser (or `gh auth login --web`); verify scopes (`repo`, `workflow`, `read:org`, `gist`, `notifications` for full macbook PATs).
2. **Install into gh keyring + macOS Keychain immediately** so the old PAT is not needed:
   ```bash
   NEW="$(security find-generic-password -s github.com -a jleechan2015 -w)"
   printf '%s' "$NEW" | env -u GH_TOKEN -u GITHUB_TOKEN gh auth login --hostname github.com --git-protocol https --with-token
   env -u GH_TOKEN -u GITHUB_TOKEN gh auth setup-git
   security add-generic-password -U -a jleechan2015 -s github.com -w "$NEW"
   env -i HOME="$HOME" PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/bin:/bin" \
     gh auth status --hostname github.com
   ```
3. **Delete the leaked public artifact** (issue, comment, gist) via `gh api -X DELETE` (or `gh issue delete --yes` if enabled). Verify with anonymous `curl -fsSI https://api.github.com/repos/<owner>/<repo>/issues/<N>` returning `HTTP/1.1 410 Gone`.

### Phase 1 - Enumerate the 8 sinks that hold a GitHub PAT on this host

Run the deterministic scrub in `scripts/scrub-pat-sinks.sh`. The canonical list (verified 2026-07-17):

| # | Sink | Notes |
|---|---|---|
| 1 | macOS Keychain `s/github.com/a/<user>` | Single source of truth for `gh` |
| 2 | `~/.config/gh/hosts.yml` | Written by `gh auth login` |
| 3 | `~/.config/gh/hosts.yml.bak*` | Plaintext backups - DELETE, do not edit |
| 4 | `~/.bashrc` exports of `GH_TOKEN` / `GITHUB_TOKEN` / `AO_BOT_GH_TOKEN` | Replace via in-place regex |
| 5 | `~/.config/ezgha/gh_token` | ezgha keychain mirror |
| 6 | `~/Library/LaunchAgents/ai.agento.ao-go-daemon.plist` | daemon env passthrough |
| 7 | `~/.config/ao-runner/<org>--<repo>.yaml` | 5 yamls on this host (jleechanclaw, worldai_claw, your-project.com, mctrl_test, ai_universe_living_blog) |
| 8 | Each repo's `.git/config` `remote.origin.url` if it contains an inline PAT userinfo | Strip userinfo → `https://github.com/<owner>/<repo>.git` |

Audit command (returns remaining sinks post-scrub):

```bash
python3 - <<'PY'
import os, re
PAT = re.compile(r"(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})")
paths = [
  os.path.expanduser("~/.bashrc"),
  os.path.expanduser("~/.config/gh/hosts.yml"),
  os.path.expanduser("~/.config/ezgha/gh_token"),
  os.path.expanduser("~/Library/LaunchAgents/ai.agento.ao-go-daemon.plist"),
]
aod = os.path.expanduser("~/.config/ao-runner")
if os.path.isdir(aod):
  paths += [os.path.join(aod, f) for f in os.listdir(aod) if f.endswith(".yaml")]
for p in paths:
  try: m = PAT.findall(open(p, errors="ignore").read())
  except: continue
  if m: print(f"  {p}: {len(m)} match(es)")
PY
```

Then scan `.git/config` files fleet-wide:

```bash
python3 - <<'PY'
import os, re
PAT = re.compile(r"(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})")
for base in [os.path.expanduser(b) for b in ["~/projects","~/projects_other","~/projects_reference","~/repos","~/agent-f","~/.worktrees"]]:
  if not os.path.isdir(base): continue
  for dp, dn, fn in os.walk(base):
    if ".git" in dn:
      p = os.path.join(dp, ".git", "config")
      try:
        if PAT.search(open(p, errors="ignore").read()):
          print(p)
      except: pass
      dn.remove(".git")
PY
```

For every hit, derive the neutral origin by stripping userinfo or re-deriving `https://github.com/<owner>/<repo>.git` from the URL:

```bash
for repo in <hits>; do
  url=$(git -C "$repo" remote get-url origin)
  neutral=$(echo "$url" | sed -E 's|^https://[^/@]+(:[^/@]+)?@github\.com/|https://github.com/|')
  git -C "$repo" remote set-url origin "$neutral"
done
```

### Phase 2 - Install the durable outbound gate (PR + code)

Dispatch an AO worker to land this in `jleechanclaw` per the harness-deploy-pipeline. Required deliverables for the worker:

1. **A new SOUL.md `## COMMIT:` rule** triggered on outbound public artifacts (issue create / PR create/comment / Slack post / gist create / email). Requires the canonical PAT regex to be applied to the actual outbound body; blocks the send when a match is detected and asks the user to redact before retrying.
2. **A shared sanitizer script** (`scripts/redact-secrets.py`) wired at the canonical send callers. The script MUST also redact credentialed HTTPS remote URLs and replace full tokens with prefix+suffix fingerprints.
3. **A `## COMMIT:` rule for `git remote set-url`** - if the new URL contains an inline credential, refuse the change and instruct the caller to use Keychain/gh instead.
4. **Regression tests** that reproduce the exact `disk_magician#25` body (with synthetic tokens only) and prove the public body is blocked or redacted. Include a test that scans `git remote -v` and `.git/config` output through the gate.
5. **Audit** of `disk_magician`, `swarm`, `disk diagnosis`, and report skills to confirm no raw `git remote -v`, `.git/config`, `env`, `gh auth status -t` output is sent to GitHub unfiltered. Wire the shared gate at the narrowest canonical caller(s).
6. **`/advice` second-opinion** before close. Reports must reference path + token fingerprint only, never the token itself.

Push to `origin/main` per `hermes-deploy-pipeline` (jleechanclaw has no branch protection - `git push origin HEAD:refs/heads/main`), verify remote SHA, run `~/.hermes/scripts/deploy.sh --skip-pull --skip-restart`.

### Phase 3 - Slack thread reply (deterministic contract)

Reply to the originating Slack thread with:
- The root-cause failure pattern (one paragraph, no jargon dump).
- A 🟢/🟡/🔴 status block: 🟢 immediate remediation done (Phase 0+1), 🟡 durable prevention in flight (Phase 2 worker + cron), 🔴 open risks (e.g. orgs not yet audited).
- Specific evidence: removed issue URL with status 410, fingerprint hashes of the new PAT in each sink, list of repos whose `.git/config` was neutralized.
- One `🧠 Memories used:` line. Redact all token-like strings; never print a credential value.
- Bead ID (e.g. `$USER-zae`) and AO session ID (e.g. `jleechanclaw-5`).
- Follow-up cron job ID for end-state verification (one-time, 20m, `--delete-after-run`).

## Wire-up summary for the AO worker brief

Brief template:

```
Incident: live GitHub PAT(s) leaked into <owner>/<repo> <artifact> #N on <date>.
Goal: implement a permanent outbound-side secret-redaction gate in jleechanclaw
so this class of leak stops recurring.

Deliverables (each item is a test or a SOUL.md `## COMMIT:` rule):
1) `scripts/redact-secrets.py` implementing the canonical PAT_RE.
   - Apply to: outbound gh-safe-publish issue create body, gh-safe-publish pr create body,
     gh-safe-publish pr comment body, gh-safe-publish gist create body,
     mcp__slack__conversations_add_message text.
   - Replace full tokens with prefix+suffix (first4 + last4 chars) or `[REDACTED]`.
   - Strip userinfo from credentialed HTTPS GitHub URLs.
   - Block send when match detected and ask the caller to redact before retry.
2) SOUL.md `## COMMIT: outbound-secret-redaction-gate` rule.
3) SOUL.md `## COMMIT: git-remote-set-url-credential-refusal` rule.
4) tests/test_redact_secrets.py with synthetic tokens reproducing the exact
   `disk_magician#25` body and proving the gate blocks/redacts it.
5) tests/test_git_remote_url_no_inline_credentials.py.
6) Audit disk_magician + swarm + disk-diagnosis skills for raw `git remote -v`,
   `.git/config`, `env`, `gh auth status -t` callers; wire the gate there too.
7) `/advice` second-opinion before closing.
8) Push to origin/main per hermes-deploy-pipeline. Verify remote SHA.
9) Use mid-tier model for any subagents.
10) NEVER put any real token in fixtures, logs, commits, PR bodies, or reports.
```

## Pitfalls

1. **`ao start --no-dashboard --no-open` is GONE on ao-go v1.x.** It now opens the desktop app and exits. The "background daemon" pattern from the old TS CLI does not apply. See `dispatch-task/references/ao-go-v1-cli-quirks.md`.
2. **`ao status --project <id>` is GONE on ao-go v1.x.** Use `ao status --json` and parse the JSON. The project-scoped status flag never made it to v1.
3. **`ao spawn --name` is ≤20 chars.** Anything longer returns `error: --name must be 20 characters or fewer` immediately.
4. **Plaintext `gh hosts.yml.bak*` files retain the OLD (revoked) credential forever.** Never edit these - `rm` them. `gh auth login` writes `hosts.yml`, not `hosts.yml.bak`, so the `.bak` is from a prior install.
5. **`security find-generic-password` may fail with `SecKeychainSearchCopyList: The specified item could not be found`** if you wrote a different `account` name. Probe with `security find-generic-password -s github.com -a jleechan2015 -w`. If `account` is `$USER-af` or another, update the call site AND scrub the wrong-named entry.
6. **`git remote -v` output contains the full PAT in the URL** even after you have rotated. Strip userinfo with `sed -E 's|^https://[^/@]+(:[^/@]+)?@github\.com/|https://github.com/|'` before displaying in any report. The `--get-url` form is identical to `-v`.
7. **The agent that opened the leak is often not the agent that should fix it.** A disk-diagnosis worker opened `disk_magician#25`; the fix lives in `jleechanclaw`'s harness. Don't try to patch `disk_magician` - that's the application code path. Patch the harness.
8. **Phase 1 must enumerate sinks IN ONE PASS.** Half-scrubbing (only Keychain, only `bashrc`) leaves a stale PAT alive. Use the audit script above; it returns `0 matches` only when every sink is clean.
9. **Don't paste the fingerprint hash list into Slack under `**bold**`** (Slack renders a stray `*` adjacent to URLs/identifiers). Paste on its own line.
9a. **Don't place a literal `*` adjacent to any URL or identifier in outbound Slack/Discord messages — Slack's mrkdwn renderer interprets `*foo*` as italic and silently breaks the clickable link.** Verified 2026-07-26, Slack `C0AH3RY3DK6/p1785122814.849319` (`github.com/$GITHUB_REPOSITORY/pull/8629*` rendered unclickable, agent had appended `*` after the URL). Defense in depth: `~/.claude/hooks/slack-trailing-asterisk-strip.sh` is registered as PreToolUse matcher `mcp__slack__conversations_add_message` in `~/.claude/settings.json` — strips adjacent `*` from any `https://github.com/...` substring before the message lands. Companion: SOUL.md `## COMMIT: no-trailing-asterisk-pr-urls` and the matching line in `~/.claude/CLAUDE.md` line 225. **Always verify your outbound `text` parameter contains no `*` adjacent to any `https://...` substring before posting, even with the hook in place.** The hook catches the most common case but does NOT strip leading bullet markers (`* foo https://...`) since those are legitimate lists.
10. **A `cronjob` follow-up must be one-time at `+20m` with `--delete-after-run`**, never `--every` (recurring cron leakage pattern, see SOUL.md `babysit-cron-self-cancel-discipline`).

## Provenance

- **Date verified:** 2026-07-17
- **Affected repo:** jleechanorg/disk_magician issue #25 (deleted; HTTP 410)
- **Bead:** $USER-zae
- **AO session:** jleechanclaw-5 (Codex mid-tier, `gpt-5.6-sol high`)
- **Prior art:** 2026-07-12 Claude Code session `6843df5e-…/line 2862` wrote inline-PAT REMOTE_URL via `git remote set-url`. The 2026-07-17 disk_magician run pasted the still-leaked URL into a public issue.
- **Sibling skill:** `home-config-backup-audit` (security/) - cron/push pipeline leaks to public repos; this skill covers agent-output leaks to public artifacts. Different surfaces, complementary.
- **Sibling skill:** `backup-folder-leak-purge` - force-purge a backup folder already leaked.
