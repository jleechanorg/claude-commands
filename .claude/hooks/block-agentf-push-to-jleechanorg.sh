#!/usr/bin/env bash
# block-agentf-push-to-jleechanorg.sh — PreToolUse(Bash) guard.
#
# Invariant: nothing containing Agnt-F / agent-f / agentf / agf- / Agnt-F
# specifics may be pushed to the jleechanorg GitHub org.
#
# Scope is intentionally narrow to avoid false positives:
#   - fires only on `git push` to a jleechanorg/<repo> remote
#   - inspects the commits about to be pushed (commit msg + author + diff)
#     for Agnt-F telltales
#   - fires for `git push origin <branch>` and `git push jleechanorg <branch>`
#     alike, as long as the target resolves to github.com/jleechanorg
#   - does NOT block pushes to other remotes (Agnt-F, origin of a different
#     org, or local file:// remotes)
#
# Patterns checked (case-insensitive):
#   - agnt-f                            (the Agnt-F org, e.g. github.com/Agnt-F/)
#   - agent-f followed by a non-letter  (the repo/dir name and jeffrey@agent-f.com;
#     the token boundary is what prevents matching camelCase / hyphenated
#     identifiers like AgentFactory, TestGetAgentForInput, agent-framework)
#   - agf-                              (the Agnt-F repo prefix: agf-api, agf-infra)
#   - $USER-af                       (the Agnt-F GitHub user)
#
# NOTE: a bare "agentf" substring is deliberately NOT matched — it false-positived
# on unrelated camelCase tokens (AgentFactory, getAgentForInput, task-agentfoo)
# that merely happen to contain the letters. Every real Agnt-F telltale carries a
# hyphen (agent-f, agnt-f, agf-) or the $USER-af handle, so we key off those.
#
# Exits 0 on every non-push or non-jleechanorg push.
# Exits 2 with a diagnostic on stderr when a violation is detected.
set -uo pipefail

input="$(cat 2>/dev/null || true)"
[ -z "$input" ] && exit 0

# Fast bail: only fire on git push invocations.
case "$input" in *push*) : ;; *) exit 0 ;; esac

# Parse the command with a real tokenizer so we correctly handle git global
# options BEFORE the subcommand (e.g. `git -C <dir> push`, `git -c k=v push`),
# which a naive `git[[:space:]]+push` regex misses entirely. We resolve:
#   IS_PUSH  — whether a real `git ... push` runs (subcommand, not a substring)
#   EFF_CWD  — the repo the push runs in: the `-C <dir>` value when the command
#              supplies one, otherwise the tool-reported cwd / shell PWD. Honoring
#              -C is what fixes the false positive where the harness reports cwd as
#              one repo (e.g. ~/.hermes) while the command pushes from a worktree
#              of a different repo — the old code inspected the wrong repo's history.
#   REMOTE   — the first non-flag positional after `push` (the target remote)
# NOTE: the JSON arrives via the INPUT env var, NOT stdin — the heredoc below
# already occupies python's stdin with the script body (`python3 - <<'PY'`), so
# `json.load(sys.stdin)` would read the (already-consumed) script and fail open.
eval "$(INPUT="$input" python3 - "${PWD:-}" <<'PY'
import json, os, shlex, sys
pwd = sys.argv[1] if len(sys.argv) > 1 else ''
def emit(p, r, c):
    print("IS_PUSH=%d" % p)
    print("REMOTE=%s" % shlex.quote(r))
    print("EFF_CWD=%s" % shlex.quote(c))
try:
    d = json.loads(os.environ.get('INPUT', ''))
except Exception:
    emit(0, '', ''); sys.exit(0)
cmd = (d.get('tool_input', {}) or {}).get('command', '') or ''
cwd = d.get('cwd', '') or pwd
try:
    toks = shlex.split(cmd)
except Exception:
    toks = cmd.split()
is_push, gitdir, remote = 0, '', ''
i, n = 0, len(toks)
while i < n:
    if toks[i].rsplit('/', 1)[-1] == 'git':
        j, gd = i + 1, ''
        while j < n:
            a = toks[j]
            if a == '-C' and j + 1 < n:
                gd = toks[j + 1]; j += 2; continue
            if a.startswith('-C') and len(a) > 2:
                gd = a[2:]; j += 1; continue
            if a in ('-c', '--namespace', '--git-dir', '--work-tree', '--exec-path') and j + 1 < n:
                j += 2; continue
            if a.startswith('-'):
                j += 1; continue
            break
        if j < n and toks[j] == 'push':
            is_push, gitdir = 1, gd
            k = j + 1
            while k < n:
                if toks[k] == '--' or toks[k].startswith('-'):
                    k += 1; continue
                remote = toks[k]; break
            break
    i += 1
emit(is_push, remote, gitdir if gitdir else cwd)
PY
)"
[ "${IS_PUSH:-0}" = "1" ] || exit 0
# Ignore dry runs / help.
case "$input" in *"--dry-run"*|*"--help"*) exit 0 ;; esac

# Resolve the working dir; fall back to shell PWD.
cwd="${EFF_CWD:-${PWD:-}}"
remote="${REMOTE:-}"
[ -d "$cwd" ] || exit 0

# $remote (the target remote) is already resolved by the tokenizer above; an
# empty value means `git push` with no positional → fall back to branch upstream.
remote_url=""
if [ -n "$remote" ] && [ "$remote" != "--" ]; then
  remote_url=$(git -C "$cwd" config --get "remote.$remote.url" 2>/dev/null || echo "")
fi
if [ -z "$remote_url" ]; then
  # No explicit remote: check the upstream of the current branch.
  branch=$(git -C "$cwd" symbolic-ref --short HEAD 2>/dev/null || echo "")
  if [ -n "$branch" ]; then
    upstream=$(git -C "$cwd" rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>/dev/null || echo "")
    if [ -n "$upstream" ]; then
      upstream_remote="${upstream%%/*}"
      remote_url=$(git -C "$cwd" config --get "remote.$upstream_remote.url" 2>/dev/null || echo "")
    fi
  fi
fi
[ -z "$remote_url" ] && exit 0

# Normalize the remote URL — only block when it points at jleechanorg.
# Accepts https://github.com/jleechanorg/<x>.git,
#          git@github.com:jleechanorg/<x>.git,
#          ssh://git@github.com/jleechanorg/<x>.git,
#          and the user-and-token-prefixed variants.
# bash `case` only takes a single glob per arm, so we use grep -E.
normalized=$(printf '%s' "$remote_url" | tr '[:upper:]' '[:lower:]')
printf '%s' "$normalized" | grep -Eq \
  'github\.com[/:]jleechanorg/' || exit 0

# Resolve the commits the push will ACTUALLY transmit — reachable from HEAD but
# not already present on the target remote. We prefer `--not --remotes=<remote>`
# whenever the remote has tracking refs, which excludes already-merged ancestors.
# That fixes the false positive where already-pushed content (a commit merged to
# the remote's main, or content a merge commit drags in from main) carries an
# agent-f telltale that the branch merely inherits. Fall back to HEAD~1..HEAD only
# when no remote-tracking refs exist to compare against (defensive — worst case we
# block on something benign and the human unblocks).
range_desc=""
rev_args=()
if [ -n "$remote" ] && \
   [ -n "$(git -C "$cwd" for-each-ref --count=1 "refs/remotes/${remote}/" 2>/dev/null)" ]; then
  # Remote has tracking refs (the common case, whether or not <remote>/<branch>
  # exists yet): inspect only commits reachable from HEAD but NOT from ANY ref
  # already on this remote — its main, the branch's own pushed tip, sibling
  # branches. This is exactly the object set the push will transmit.
  #
  # Crucially this also drops content a MERGE commit drags in from the remote's
  # main: those underlying commits are reachable from <remote>/main, so
  # `--not --remotes` excludes them and `git log --patch` shows no diff for the
  # (excluded) merge. The older "<remote>/<branch>..HEAD" range did NOT exclude
  # them — merging main into a feature branch re-introduced every already-pushed
  # .beads identifier into the range, re-flagging it on every subsequent push.
  range_desc="HEAD --not --remotes=${remote}"
  rev_args=( HEAD --not --remotes="${remote}" )
else
  # No remote-tracking refs to compare against — fall back conservatively to the
  # single most recent commit.
  range_desc="HEAD~1..HEAD"
  rev_args=( "HEAD~1..HEAD" )
fi

# Now grep the commit metadata and diff for the telltales. We do this with a
# single pass of `git log` to keep the hook fast.
matches=$(
  git -C "$cwd" log "${rev_args[@]}" \
      --pretty=format:'COMMIT_MSG:%s%nCOMMIT_BODY:%b%nAUTHOR_NAME:%an%nAUTHOR_EMAIL:%ae' \
      --stat=200,200 \
      --patch 2>/dev/null \
    | grep -nEi 'agnt-f|agent-f([^a-z]|$)|agf-|$USER-af' \
    | head -40
)

# Self-exemption: if the push ONLY modifies this hook (or its test), allow it.
# Without this, the hook blocks its own first push, because the test file
# legitimately contains "Agnt-F" as test input. Bootstrap problem.
self_changed=$(git -C "$cwd" log "${rev_args[@]}" --name-only --pretty=format: 2>/dev/null \
  | sort -u)
if [ -n "$self_changed" ]; then
  all_self=1
  for f in $self_changed; do
    case "$f" in
      */block-agentf-push-to-jleechanorg.sh|block-agentf-push-to-jleechanorg.sh|\
      */test_block_agentf_push_hook.sh|test_block_agentf_push_hook.sh) : ;;
      *) all_self=0; break ;;
    esac
  done
  if [ "$all_self" = "1" ]; then
    exit 0
  fi
fi

if [ -n "$matches" ]; then
  {
    echo "BLOCKED by block-agentf-push-to-jleechanorg:"
    echo "  Push target: $remote_url  (resolved range: $range_desc)"
    echo "  Detected Agnt-F / agent-f content in the commits about to be pushed:"
    echo "----"
    printf '%s\n' "$matches" | sed 's/^/  /'
    echo "----"
    echo "Fix one of:"
    echo "  • Move the work to the Agnt-F org: gh repo create Agnt-F/<repo> --source=<local>"
    echo "  • Re-author the commits to a non-agentf user: git commit --amend --reset-author"
    echo "  • If this is a false positive, switch gh accounts first:"
    echo "      gh auth switch --user $USER-af"
    echo "    then push from outside Claude (the user-scope hook will be bypassed"
    echo "    in non-Claude shells)."
  } >&2
  exit 2
fi

exit 0
