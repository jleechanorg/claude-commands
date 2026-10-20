---
name: linux-remote
description: "Steering work on $USER's Ubuntu machine (jeff-ubuntu) via SSH. Use when asked to run commands, install software, check services, or manage files on the Ubuntu box."
---

# Linux Remote — jeff-ubuntu SSH Steering

## Retained review integrations

The shared catalog preserves host-installed `/advice` and `/web-advice` integrations instead of installing them. Before invoking either, resolve its `../advice/SKILL.md` or `../web-advice/SKILL.md` relative to this package and read the existing skill. For a remote invocation, check the corresponding skill on the target host. If absent, report that integration as `UNAVAILABLE` and identify the missing package; do not invent a replacement runner, claim an approval, or treat a required gate as passed. Continue independent authorized work, but leave any dependent readiness or plan-approval gate unmet. Existing review quorum, external-disclosure authorization, and optional-review rules still apply.


## Connection

```bash
ssh jeff-ubuntu          # alias in ~/.ssh/config → $USER@<ubuntu-lan-ip>
```

- **Host:** `jeff-ubuntu` / `<ubuntu-lan-ip>` (LAN only)
- **User:** `$USER`
- **Key:** `~/.ssh/id_jeff_ubuntu` (passwordless, no `-i` flag needed via alias)
- **OS:** Ubuntu 24.04, kernel 6.17, x86_64
- **sudo password:** stored in user's head — prompt user if needed, or use `expect` if already known in context

## Off-LAN fallback: Tailscale, then Slack

If `ssh jeff-ubuntu` times out or is refused (off home LAN, traveling, or the LAN link is just down — happens occasionally even at home), use the dedicated Tailscale alias instead — proven working 2026-09-16/17, including with the LAN link fully down:

```bash
ssh jeff-ubuntu-ts '<command>'
```

`jeff-ubuntu-ts` is a real `~/.ssh/config` stanza (same `IdentityFile` as the LAN alias) — no manual `-i`/IP lookup needed, it just works as a drop-in replacement for `jeff-ubuntu` in every command in this skill. `ssh jeff-ubuntu` does **not** fail over to it automatically; try the LAN alias first (fast when it works), fall to `-ts` on failure. Re-verify the IP with `tailscale status | grep ubuntu` if it ever seems dead — Tailscale IPs are stable per-device but not guaranteed forever.

If both the LAN alias and `jeff-ubuntu-ts` fail, see [cross-machine-ssh-tier](../cross-machine-ssh-tier/SKILL.md) for the Tier 3 messaging-gateway fallback and its debugging caveats (OAuth-scope-vs-connection, bot-message filtering) — that skill is the shared source of truth for this whole ladder, used identically by `mac-remote`, `linux-mirror`, and `mac-mirror`.

## Cloud capability gaps: Dot-first recovery and escalation

When `/dot` cannot perform a required action on its cloud computer (for
example, a test runner, package, browser, service, login, or permission is
missing), keep the task moving through this bounded recovery loop:

1. Confirm the exact gap on the target host with a read-only probe before
   proposing a fix: record the host, repository/worktree, branch or SHA, exact
   command, exit status, missing binary/package/service, and the artifact the
   command was expected to produce. Do not call a generic cloud failure a
   blocker when SSH can answer the question.
2. Send `/dot` a self-contained remediation request naming the gap and the
   acceptance check. Ask Dot to install or set up the missing tool, retry the
   login through its approved interactive flow, or request the specific
   permission it lacks. Dot must use the existing host/account profiles and
   credential boundaries; never copy cookies, tokens, passwords, or browser
   profiles, and never treat a requested permission as granted.
3. If setup needs `sudo`, an external account, MFA, an OAuth scope, or another
   user-controlled approval, pause only that dependent action and request the
   missing approval through the authorized flow. Continue independent
   read-only checks and preparation. Record `REQUESTED`, `GRANTED`,
   `DENIED`, or `UNCONFIRMED` separately; a successful install command or a
   live process is not proof that the needed login or permission works.
4. Re-run the exact acceptance command on the same host and verify its output
   or artifact at the source. Report the command, result, SHA, and artifact;
   Dot's queued message, setup claim, or transport success is not completion.
5. If Dot remains unable after the authorized install/setup/login/permission
   attempt, report the precise blocker immediately in the current chat and
   notify the user through the configured Slack text transport, with the
   `[AI Terminal: <workspace-name>]` identity prefix and a delivery receipt.
   The `/slack` command is the canonical media workflow; use the configured
   text transport (for example, the Slack conversation message capability)
   for a text alert. Use an approved outbound email capability only after
   verifying that it is configured and that delivery succeeded. The installed
   `/gmail` skill is read/search guidance, not proof of an email sender; if no
   approved email sender is available, report `EMAIL UNAVAILABLE` in chat and
   Slack rather than fabricating a send or handling credentials. Each
   notification must include the host, exact command or artifact, Dot's
   remediation attempt, current permission state, blocker, and the concrete
   unblock action.

This escalation supplements the [Dot skill](../dot/SKILL.md), the SSH tier
ladder above, and the existing agent response-proof contract below. It does
not authorize credential handling, broad package changes, destructive actions,
or a host replacement. Preserve the exact failing instruction and continue
any safe independent work while the user-controlled dependency is pending.

## How to run commands

Always use `ssh jeff-ubuntu '<command>'` for one-liners:

```bash
ssh jeff-ubuntu 'sudo apt update && sudo apt install -y <pkg>'
ssh jeff-ubuntu 'systemctl status <service>'
ssh jeff-ubuntu 'cat /var/log/syslog | tail -50'
```

For multi-line scripts, pipe via heredoc:

```bash
ssh jeff-ubuntu 'bash -s' << 'EOF'
sudo apt update
sudo apt install -y openssh-server
sudo systemctl enable --now ssh
EOF
```

## Independent Dot sessions

Follow the installed [Dot skill](../dot/SKILL.md) for browser setup and login.
Deploy the same reviewed Dot package on each host, then authenticate each configured
account independently in its own dedicated persistent browser profile on that host.
Never copy or sync cookies, browser profiles, Chrome `Local State`, or authentication
state between hosts, accounts, or the user's real browser and Dot. Separate profile
directories alone do not prove separate login sessions.

Verify the installed Dot package prevents source-browser credential imports before
opening a profile. For an existing shared session, preserve the profile and pause
only its owned reminder timer while preparing a clean replacement; preserve timer
enablement and do not log out, revoke, or reset the user's real-browser sessions.
Enter known account identifiers, then let the user complete password or MFA entry
in the dedicated browser. Never recover a failed login by importing credentials.

Before switching the configured profile or resuming reminders, verify the expected
nonempty `user.email` from `/api/auth/session` and a successful normal Dot read for
each account. `/backend-api/me` or HTTP 200 alone is not authentication proof.
Verify independent session provenance without exposing cookie or token values.
Report each account's actual result and any remaining authentication boundary;
an installed package or enabled timer does not prove usable independent sessions.

## Agent submission and response proof — mandatory

For every instruction sent to an interactive agent, including initial launches,
resumed sessions, follow-ups, and existing composer drafts:

1. Resolve the exact tmux pane or cmux surface and verify its foreground application
   and screen before typing. Capture a baseline and retain the intended instruction.
   Never send agent prose to a shell, trust dialog, or unknown foreground process.
   Preserve unrelated composer text and queued work.
2. Submit explicitly using the application's current controls. In Codex, a busy
   composer displaying “tab to queue message” requires Tab to queue; an idle
   composer uses Enter to submit. Send text and the submit key in separate calls
   after verifying the text arrived. Inspect other CLIs' actual controls rather
   than assuming Enter submits. Initial prompt argv still requires response proof.
3. Re-read after submission. Text remaining in the editable composer is NOT
   submitted. A queue entry proves only QUEUED, not received or acted upon.
   Do not resend queued instructions or interrupt active work merely to obtain
   acknowledgment. Inspect the queue and transcript before retrying uncertain
   submissions to avoid duplicate execution.
4. Wait for a fresh agent-authored response attributable to that instruction.
   Request a brief acknowledgment naming the task or a unique dispatch marker
   when composing new instructions. Verify chronology against the baseline and
   inspect the actual transcript when screen output is ambiguous. Echoed input,
   prompts, spinners, process liveness, transport exit status, READY/RESUMED, and
   queue entries are never substitutes for an agent response.
5. Echo the actual response excerpt into the calling/main terminal and the
   user-facing update, labeled with host, session/pane or surface, observation time,
   and instruction or dispatch marker. Redact secrets. Report ACKNOWLEDGED only
   when that response exists; acknowledgment proves delivery, not task completion.
   Validate completion claims against the requested artifacts or checks.
6. Continue monitoring with bounded asynchronous waits and regular progress
   updates. Set a response deadline appropriate to the active job. If it expires
   or the agent fails, report QUEUED/UNCONFIRMED/BLOCKED with the observed reason,
   preserve the instruction, and perform scoped recovery. Never claim success
   from submitted text alone.

This contract applies through SSH, tmux, cmux, and terminals such as Warp.

## sudo with known password

If the user's password is in context (currently: ask user), use `expect`:

```bash
expect -c "
spawn ssh jeff-ubuntu sudo <command>
expect {
  \"password\" { send \"<password>\r\"; exp_continue }
  eof
}
"
```

Or pass via stdin:
```bash
echo '<password>' | ssh jeff-ubuntu 'sudo -S <command>'
```

## File transfer

```bash
scp /local/file jeff-ubuntu:/remote/path      # local → remote
scp jeff-ubuntu:/remote/file /local/path      # remote → local
rsync -avz /local/ jeff-ubuntu:/remote/       # sync directory
```

## Common tasks

| Task | Command |
|------|---------|
| Check disk | `ssh jeff-ubuntu 'df -h'` |
| Running services | `ssh jeff-ubuntu 'systemctl list-units --state=running'` |
| Installed packages | `ssh jeff-ubuntu 'dpkg -l \| grep <pkg>'` |
| Tail a log | `ssh jeff-ubuntu 'sudo journalctl -fu <service>'` |
| Advice Review | `ssh jeff-ubuntu '~/.claude/commands/advice.md'` (or execute `~/.claude/skills/advice/SKILL.md`) |
| Web Advice Review | `ssh jeff-ubuntu '~/.claude/commands/web-advice.md'` (or execute `~/.claude/skills/web-advice/SKILL.md`) |
| Reboot | `ssh jeff-ubuntu 'sudo reboot'` (warn user first) |

## Caveats

- Machine is LAN-only (<lan-subnet>) — not reachable when off same network; use the Tailscale fallback above when off-LAN
- If SSH fails, check if machine is on via `ping <ubuntu-lan-ip>`, then try Tailscale before assuming it's down
- RustDesk (peer ID `406402544`) is the fallback for GUI access if SSH is down
- Always prefer SSH over RustDesk for CLI work — RustDesk CLI steering is not possible headlessly on macOS without Accessibility permission
