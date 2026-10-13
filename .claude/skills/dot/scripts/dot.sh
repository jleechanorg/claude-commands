#!/usr/bin/env bash
# Talk to the user's ChatGPT "dot" assistant.
# Platform-aware architecture: macOS and Linux each use local headless Chrome and dedicated account profiles.
# Usage: dot.sh [--account <name>] [--url <url>] read [chars]        print tail of conversation (default 5000 chars)
#        dot.sh [--account <name>] [--url <url>] send <message-file> send file contents; while composer holds peer draft,
#                                                                    retry every DOT_RETRY_SECS (60) up to DOT_WAIT_SECS (1800)
#        dot.sh [--account <name>] [--url <url>] send-once <file>    single attempt, no retry
#        dot.sh [--account <name>] login|auth                        launch visible Chrome window on account profile for manual sign-in
# DOT_ACCOUNT selects account (configured in ~/.config/dot/config.json or custom identifier).
# DOT_BACKEND=chrome forces backend. DOT_DRY_RUN=1 (chrome send): type, verify, clear, never send.
# Exit codes: 0 ok, 2 usage/error, 3 composer still busy after the wait, 4 send not verified, 5 usage limit reached.
set -euo pipefail

# Ensure standard user and Homebrew binary paths are in PATH
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$PATH"

# Parse optional --account / -a / --url / -u flags from arguments
NEW_ARGS=()
URL_EXPLICIT=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --account|-a)
      DOT_ACCOUNT="$2"
      shift 2
      ;;
    --account=*)
      DOT_ACCOUNT="${1#*=}"
      shift 1
      ;;
    --url|-u)
      DOT_URL="$2"
      URL_EXPLICIT=1
      shift 2
      ;;
    --url=*)
      DOT_URL="${1#*=}"
      URL_EXPLICIT=1
      shift 1
      ;;
    *)
      NEW_ARGS+=("$1")
      shift 1
      ;;
  esac
done
set -- ${NEW_ARGS[@]+"${NEW_ARGS[@]}"}

# Existing-profile-only launch is local by contract and never falls back to another host.
if [[ "${1:-}" == "existing-profile-only" || "${1:-}" == "probe" ||
      "${DOT_PREPARED:-0}" == "1" || "${1:-}" == "send-prepared" ]]; then
  DOT_NO_REMOTE=1
  export DOT_NO_REMOTE
fi
PROFILE_RESOLVER_MODE="resolve-profile"
if [[ "${1:-}" == "probe" ]]; then
  PROFILE_RESOLVER_MODE="resolve-profile-existing"
fi

# Resolve Node runtime before any inline node invocations
if [[ -n "${DOT_NODE:-}" ]]; then
  NODE="$DOT_NODE"
elif [[ -x "$HOME/.nvm/versions/node/v22.22.0/bin/node" ]]; then
  NODE="$HOME/.nvm/versions/node/v22.22.0/bin/node"
elif command -v node >/dev/null 2>&1; then
  NODE="$(command -v node)"
elif [[ -d "$HOME/.nvm/versions/node" ]]; then
  NODE="$(ls -1d "$HOME/.nvm/versions/node"/v* 2>/dev/null | tail -1)/bin/node"
else
  NODE="/usr/local/bin/node"
fi
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CONFIG_FILE="${DOT_CONFIG_FILE:-$HOME/.config/dot/config.json}"
ACCOUNT="${DOT_ACCOUNT:-}"

if [[ -z "$ACCOUNT" && -f "$CONFIG_FILE" ]]; then
  ACCOUNT=$("$NODE" -e '
    try {
      const fs = require("fs");
      const cfg = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
      process.stdout.write(cfg.default_account || "");
    } catch {}
  ' "$CONFIG_FILE" 2>/dev/null || true)
fi
ACCOUNT="${ACCOUNT:-default}"

# Unify profile directory and URL resolution via dot_chrome.mjs resolve-profile
PROFILE_DIR=""
PROFILE_DIRECTORY=""
RESOLVED_URL=""
if [[ -x "$NODE" && -f "$HERE/dot_chrome.mjs" ]]; then
  if ! PROFILE_INFO=$(DOT_ACCOUNT="$ACCOUNT" DOT_CONFIG_FILE="$CONFIG_FILE" DOT_URL="${DOT_URL:-}" DOT_CHROME_USER_DATA="${DOT_CHROME_USER_DATA:-}" "$NODE" "$HERE/dot_chrome.mjs" "$PROFILE_RESOLVER_MODE" 2>&1); then
    echo "$PROFILE_INFO" >&2
    exit 2
  fi
  if [[ -n "$PROFILE_INFO" ]]; then
    PROFILE_DIR=$("$NODE" -e 'try { process.stdout.write(JSON.parse(process.argv[1]).profileDir || ""); } catch {}' "$PROFILE_INFO" 2>/dev/null || true)
    PROFILE_DIRECTORY=$("$NODE" -e 'try { process.stdout.write(JSON.parse(process.argv[1]).profileDirectory || ""); } catch {}' "$PROFILE_INFO" 2>/dev/null || true)
    RESOLVED_URL=$("$NODE" -e 'try { process.stdout.write(JSON.parse(process.argv[1]).url || ""); } catch {}' "$PROFILE_INFO" 2>/dev/null || true)
  fi
fi

if [[ -n "$PROFILE_DIR" ]]; then
  DOT_CHROME_USER_DATA="$PROFILE_DIR"
fi
if [[ -n "$RESOLVED_URL" && -z "${DOT_URL:-}" ]]; then
  DOT_URL="$RESOLVED_URL"
fi
DOT_URL="${DOT_URL:-https://chatgpt.com/}"

if [[ -z "${DOT_BACKEND:-}" || "${DOT_BACKEND:-}" == "auto" ]]; then
  BACKEND="chrome"
else
  BACKEND="$DOT_BACKEND"
fi

case "$BACKEND" in
  auto|chrome)
    BACKEND="chrome"
    ;;
  *)
    echo "dot.sh: DOT_BACKEND must be chrome or auto" >&2
    exit 2
    ;;
esac

# Print diagnostic invocation banner
URL_HOST=$("$NODE" -e '
  try {
    const u = new URL(process.argv[1]);
    process.stdout.write(u.host || "");
  } catch {
    process.stdout.write(process.argv[1] || "");
  }
' "$DOT_URL" 2>/dev/null || echo "$DOT_URL")
if [[ "${1:-}" != "existing-profile-only" && "${DOT_PREPARED:-0}" != "1" && "${1:-}" != "send-prepared" ]]; then
  PROFILE_DIR_DISPLAY="${DOT_CHROME_USER_DATA:-~/.config/dot-headless-chrome-${ACCOUNT}}"
  echo "dot.sh: account=$ACCOUNT backend=$BACKEND url=$URL_HOST dir=$PROFILE_DIR_DISPLAY" >&2
fi

# Headless Chrome backend. Sets CHROME_OUT; returns 0 if it produced a result, 10 if unavailable
# (nothing was sent), otherwise the script's own exit code.
run_chrome() {
  CHROME_OUT=""
  if [[ ! -x "$NODE" || ! -f "$HERE/dot_chrome.mjs" ]]; then CHROME_OUT="DOT_CHROME_UNAVAILABLE: node or dot_chrome.mjs missing"; return 10; fi
  # Foreign-binary enforcement is OPT-IN: DOT_CHROME_BIN is a supported override
  # (tests, alternate Chrome channels), so hardening it by default would break
  # documented callers. DOT_ENFORCE_SYSTEM_CHROME=1 refuses a non-system binary
  # unless DOT_ALLOW_FOREIGN_BINARY=1 explicitly accepts that risk.
  if [[ "${DOT_ENFORCE_SYSTEM_CHROME:-0}" == "1" ]] && \
     ! is_system_chrome "${DOT_CHROME_BIN:-}" && [[ "${DOT_ALLOW_FOREIGN_BINARY:-0}" != "1" ]]; then
    CHROME_OUT="DOT_CHROME_UNAVAILABLE: refusing non-system Chrome binary '${DOT_CHROME_BIN:-}' (foreign binaries evict Keychain-encrypted session cookies; set DOT_ALLOW_FOREIGN_BINARY=1 only to override deliberately)"
    return 10
  fi
  if ! acquire_profile_lock "${DOT_CHROME_USER_DATA:-}" "${DOT_LOCK_WAIT_SECS:-90}"; then
    CHROME_OUT="DOT_CHROME_UNAVAILABLE: DOT_PROFILE_LOCKED (another dot.sh instance or an open login window owns this profile)"
    return 10
  fi
  if ! profile_disk_ok "${DOT_CHROME_USER_DATA:-}"; then
    release_profile_lock
    CHROME_OUT="DOT_CHROME_UNAVAILABLE: low disk"
    return 10
  fi
  local rc=0
  local extra_node_path
  if [[ -d "$HOME/.npm-global/lib/node_modules" ]]; then
    extra_node_path="$HOME/.npm-global/lib/node_modules:${NODE_PATH:-}"
  elif [[ -d "$(dirname "$NODE")/../lib/node_modules" ]]; then
    extra_node_path="$(dirname "$NODE")/../lib/node_modules:${NODE_PATH:-}"
  else
    extra_node_path="${NODE_PATH:-}"
  fi
  local runner=()
  if [[ "$(uname -s)" == "Linux" ]]; then
    export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$(id -u)/bus}"
    export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
    if command -v xvfb-run >/dev/null 2>&1; then
      runner=(xvfb-run -a)
    fi
  fi
  local budget="${DOT_CHROME_TIMEOUT_SECS:-130}"
  local grace="${DOT_CHROME_KILL_GRACE_SECS:-10}"
  local out_file timed_out_file
  out_file="$(mktemp "${TMPDIR:-/tmp}/dot-chrome-out.XXXXXX")"
  timed_out_file="$(mktemp "${TMPDIR:-/tmp}/dot-chrome-timedout.XXXXXX")"
  rm -f "$timed_out_file"
  # Own process group (set -m) so the timeout kill reaches browser descendants.
  # Killing only the direct child (plain `timeout`) orphans headless Chrome
  # against its live profile and destroys the session cookie store.
  set -m
  DOT_ACCOUNT="$ACCOUNT" DOT_URL="$DOT_URL" DOT_CHROME_USER_DATA="${DOT_CHROME_USER_DATA:-}" \
    DOT_CLEAR_DRAFT="${DOT_CLEAR_DRAFT:-}" NODE_PATH="$extra_node_path" \
    ${runner[@]+"${runner[@]}"} "$NODE" "$HERE/dot_chrome.mjs" "$@" >"$out_file" 2>/dev/null &
  local pid=$!
  (
    sleep "$budget" 2>/dev/null
    touch "$timed_out_file" 2>/dev/null
    kill -TERM -- -"$pid" 2>/dev/null || true
    sleep "$grace" 2>/dev/null
    kill -KILL -- -"$pid" 2>/dev/null || true
  ) &
  local watchdog=$!
  wait "$pid" || rc=$?
  # The wrapper exited, but a browser descendant may still hold the live
  # profile (orphaned Chrome corrupts the cookie store on its next write).
  # Tear down any surviving group member before returning.
  if kill -TERM -- -"$pid" 2>/dev/null; then
    # A descendant surviving a NORMAL wrapper exit is an orphan: tear it down
    # promptly (the long grace applies only to the timeout path, where Chrome
    # may still be flushing its cookie store).
    sleep "${DOT_CHROME_TEARDOWN_GRACE_SECS:-1}" 2>/dev/null
    kill -KILL -- -"$pid" 2>/dev/null || true
  fi
  set +m
  kill -TERM -- -"$watchdog" 2>/dev/null || true
  wait "$watchdog" 2>/dev/null || true
  CHROME_OUT="$(cat "$out_file")"
  local timed_out=0
  if [[ -e "$timed_out_file" ]]; then timed_out=1; fi
  rm -f "$out_file" "$timed_out_file"
  release_profile_lock
  if [[ "$timed_out" -eq 1 ]]; then
    return 124
  fi
  return "$rc"
}

get_next_account() {
  local current="$1"
  if [[ ! -f "$CONFIG_FILE" ]]; then
    return 1
  fi
  "$NODE" -e '
    try {
      const fs = require("fs");
      const cfg = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
      const rot = cfg.rotation || Object.keys(cfg.accounts || {});
      const cur = process.argv[2].toLowerCase();
      const curKey = (cfg.aliases && cfg.aliases[cur]) || cur;
      let idx = rot.findIndex(a => a.toLowerCase() === curKey);
      if (idx === -1) {
        idx = rot.findIndex(a => cur.includes(a.toLowerCase()) || a.toLowerCase().includes(cur));
      }
      if (rot.length > 1) {
        const nextIdx = (idx === -1) ? 0 : (idx + 1) % rot.length;
        process.stdout.write(rot[nextIdx]);
      }
    } catch {}
  ' "$CONFIG_FILE" "$current" 2>/dev/null
}

rotate_account_if_needed() {
  local output="$1"
  local action="$2"
  shift 2
  # Never rotate on successful send
  if [[ "$output" == *"DOT_SENT_VERIFIED"* ]]; then
    return 0
  fi
  # Rotate strictly when dot_chrome.mjs detects genuine usage limit banners
  if [[ "${DOT_ROTATE_ON_LIMIT:-1}" == "1" && "$output" == *"DOT_USAGE_LIMIT_REACHED"* ]]; then
    local next_acc
    next_acc="$(get_next_account "$ACCOUNT")"
    local rotated="${DOT_ROTATED_ACCOUNTS:-}"
    if [[ -n "$next_acc" && "$next_acc" != "$ACCOUNT" ]] && ! echo ",$rotated," | grep -q ",$next_acc,"; then
      echo "dot.sh: account '$ACCOUNT' hit usage limit; rotating to '$next_acc'..." >&2
      # Clear all per-account overrides before resolving the rotated account.
      release_profile_lock
      exec env -u DOT_CHROME_USER_DATA -u DOT_URL -u DOT_PROFILE_DIRECTORY DOT_ROTATED_ACCOUNTS="${rotated:+$rotated,}$ACCOUNT" DOT_ACCOUNT="$next_acc" "$BASH" "${BASH_SOURCE[0]}" "$action" "$@"
    fi
  fi
}

# --- Session-hardening helpers (2026-10-11 review batch) -------------------
# Machine checks so the prose policy in SKILL.md cannot be silently violated:
# per-profile exclusive locks, disk floor, foreign-binary guard, cookie-store
# rebuild classification, per-profile snapshots, and login STOP management.

DOT_LOCK_DIR=""
DOT_STOP_CREATED=0
DOT_STOP_MARKER_PATH="${DOT_STOP_MARKER_PATH:-$HOME/.local/state/ai.gemini.agy-dot-coordinator/STOP}"

profile_lock_path() {
  # Stable per-profile lock path outside the profile directory (host-local).
  local dir="$1"
  local digest
  digest="$(printf '%s' "$dir" | shasum -a 256 2>/dev/null | cut -c1-16)"
  [[ -n "$digest" ]] || digest="$(printf '%s' "$dir" | cksum 2>/dev/null | tr -d ' ' | cut -c1-16)"
  echo "${DOT_LOCK_BASE:-${TMPDIR:-/tmp}}/dot-profile-locks/${digest:-profile}.lock"
}

release_profile_lock() {
  if [[ -n "${DOT_LOCK_HOLDER_PID:-}" ]]; then
    local pid="${DOT_LOCK_HOLDER_PID}"
    DOT_LOCK_HOLDER_PID=""
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
    rm -f "${DOT_LOCK_READY:-}" 2>/dev/null || true
    DOT_LOCK_READY=""
  fi
  return 0
}

login_stop_cleanup() {
  if [[ "${DOT_STOP_CREATED:-0}" == "1" && -f "${DOT_STOP_MARKER_PATH:-}" ]]; then
    rm -f "${DOT_STOP_MARKER_PATH}" 2>/dev/null || true
  fi
  DOT_STOP_CREATED=0
}

# Serialize every dot.sh Chrome launch on the same profile directory using the
# kernel's own lock primitive (fcntl.flock), held by a small holder process
# that dies with its parent dot.sh: the kernel releases the lock on ANY
# process exit (including kill -9), so there is no stale-lock logic, no
# pid-recycle ambiguity, and no check-then-act reclaim race. Concurrent
# launches race SQLite cookie-store writes (2026-10-11 incidents).
acquire_profile_lock() {
  local dir="$1"
  local wait_secs="${2:-${DOT_LOCK_WAIT_SECS:-90}}"
  [[ -z "$dir" ]] && return 0
  # Never operate unlocked because the profile dir could not be created.
  if ! mkdir -p "$dir" 2>/dev/null && [[ ! -d "$dir" ]]; then
    echo "DOT_PROFILE_LOCKED: cannot access or create $dir" >&2
    return 1
  fi
  # The lock lives OUTSIDE the profile directory: (a) a probe contract asserts
  # the profile dir is untouched by launches, and (b) a lock path inside the
  # profile makes process scans that substring-match the profile dir believe the
  # profile is in use.
  local lockfile
  lockfile="$(profile_lock_path "$dir")"
  mkdir -p "$(dirname "$lockfile")" 2>/dev/null || true
  # Unique per-caller ready file: bash shares $$ across sibling subshells, so
  # $$-named files let one holder's ready signal satisfy every sibling caller
  # (seven false claims in an 8-way repro). mktemp guarantees uniqueness.
  local ready
  ready="$(mktemp "${lockfile}.ready.XXXXXX" 2>/dev/null)" || {
    # No colliding fallback: a $$.$RANDOM name is shared by sibling subshells.
    echo "DOT_PROFILE_LOCKED: cannot create a unique lock handshake for $dir" >&2
    return 1
  }
  rm -f "$ready" 2>/dev/null || true
  python3 - "$lockfile" "$ready" <<'PYHOLDER' &
import fcntl, os, sys, time
lock_path, ready_path = sys.argv[1], sys.argv[2]
ppid = os.getppid()  # capture BEFORE locking: reparenting to init means dead parent
if ppid == 1 or os.getppid() != ppid:
    sys.exit(0)  # caller already dead (orphaned to init pre-start); never lock
fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
fcntl.flock(fd, fcntl.LOCK_EX)  # kernel-arbitrated; no stale logic needed
if os.getppid() != ppid:
    sys.exit(0)  # caller died while we were queued; release immediately
with open(ready_path, "w") as f:
    f.write(str(os.getpid()))
while os.getppid() == ppid:
    time.sleep(1)
PYHOLDER
  local holder=$!
  local deadline=$((SECONDS + wait_secs))
  while (( SECONDS < deadline )); do
    if [[ -f "$ready" ]]; then
      DOT_LOCK_HOLDER_PID="$holder"
      DOT_LOCK_READY="$ready"
      return 0
    fi
    kill -0 "$holder" 2>/dev/null || break
    sleep 0.25
  done
  kill "$holder" 2>/dev/null || true
  wait "$holder" 2>/dev/null
  rm -f "$ready" 2>/dev/null || true
  echo "DOT_PROFILE_LOCKED: another dot.sh instance holds the profile lock for $dir" >&2
  return 1
}

# A full disk corrupts the SQLite cookie store (2026-10-11 incident: Chrome
# could not even create temp files). Refuse to launch below the floor.
profile_disk_ok() {
  local dir="${1:-${DOT_CHROME_USER_DATA:-}}"
  local min_mb="${DOT_MIN_FREE_MB:-512}"
  [[ -z "$dir" ]] && return 0
  local free_kb
  free_kb="$(df -k "$dir" 2>/dev/null | awk 'NR==2 {print $4}')"
  [[ -z "$free_kb" || ! "$free_kb" =~ ^[0-9]+$ ]] && return 0
  if (( free_kb < min_mb * 1024 )); then
    echo "dot.sh: refusing to launch Chrome: only ${free_kb}KB free under $dir (floor ${min_mb}MB). A full disk corrupts the cookie store." >&2
    return 1
  fi
  return 0
}

# Read-only classification of a profile's cookie store. Live DBs must be
# read with mode=ro only (immutable=1 ignores WAL and can mislead on a
# database Chrome is actively writing).
profile_cookies_db() {
  echo "${DOT_CHROME_USER_DATA:-}/${PROFILE_DIRECTORY:-Default}/Cookies"
}

classify_cookie_store() {
  local db="$1"
  if [[ -z "$db" || ! -f "$db" ]]; then echo "absent"; return 0; fi
  command -v sqlite3 >/dev/null 2>&1 || { echo "unknown"; return 0; }
  local tokens chatgpt
  tokens="$(sqlite3 "file:$db?mode=ro" 'SELECT count(*) FROM cookies WHERE name LIKE "%session-token%";' 2>/dev/null)"
  chatgpt="$(sqlite3 "file:$db?mode=ro" 'SELECT count(*) FROM cookies WHERE host_key LIKE "%chatgpt.com";' 2>/dev/null)"
  if [[ -z "$tokens" || -z "$chatgpt" ]]; then echo "unreadable"; return 0; fi
  if (( tokens > 0 )); then
    echo "authenticated"
  elif (( chatgpt > 0 )); then
    echo "rebuild"
  else
    echo "absent"
  fi
  return 0
}

# Keep a last-known-good snapshot of this profile's OWN cookie store (SQLite
# online backup API; no cross-profile coupling). Restore is opportunistic:
# server-side token rotation may make a snapshot stale, in which case the
# probe reports logged_out and the canonical `login` path still applies.
snapshot_cookie_store() {
  local db="$1"
  [[ "${DOT_SNAPSHOT:-1}" != "1" ]] && return 0
  [[ -z "$db" || ! -f "$db" ]] && return 0
  command -v sqlite3 >/dev/null 2>&1 || return 0
  local tokens
  tokens="$(sqlite3 "file:$db?mode=ro" 'SELECT count(*) FROM cookies WHERE name LIKE "%session-token%";' 2>/dev/null)"
  [[ "$tokens" =~ ^[0-9]+$ ]] || return 0
  (( tokens > 0 )) || return 0
  sqlite3 "$db" ".backup '$db.snapshot'" >/dev/null 2>&1 || true
}

# Foreign-binary guard: only the system Google Chrome may touch a live
# profile. Playwright/bundled Chromium evicts Keychain-encrypted session
# cookies (2026-10-11 two-profile wipe).
is_system_chrome() {
  local bin="$1"
  [[ -z "$bin" ]] && return 0
  if [[ "$(uname -s)" == "Darwin" ]]; then
    [[ "$bin" == "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]]
  else
    local sys
    sys="$(command -v google-chrome || command -v chromium-browser || command -v chromium || true)"
    [[ -n "$sys" && "$bin" == "$sys" ]]
  fi
}

emit_store_forensics() {
  # Called when a read/send reports not-signed-in: distinguish a rebuilt
  # (evicted) store from other failures so operators stop misreading
  # client-side evictions as account logouts.
  local sig
  sig="$(classify_cookie_store "$(profile_cookies_db)" 2>/dev/null)"
  if [[ "$sig" == "rebuild" ]]; then
    echo "DOT_STORE_REBUILD: the profile's cookie store was rebuilt (client-side eviction — fresh anonymous cookies, zero session tokens). The account itself is likely still signed in server-side. Canonical recovery: dot.sh --account $ACCOUNT login (fresh independent sign-in). Never resync cookies from another browser profile (rotation race)." >&2
  fi
}

cmd_read() {
  local n="${1:-5000}"
  [[ "$n" =~ ^[0-9]+$ ]] || { echo "chars must be an integer" >&2; exit 2; }
  local out=""
  local rc=0
  run_chrome read "$n" || rc=$?
  if [[ $rc -eq 0 ]]; then
    out="$CHROME_OUT"
    snapshot_cookie_store "$(profile_cookies_db)"
  else
    [[ $rc -eq 124 ]] && { CHROME_OUT="DOT_CHROME_UNAVAILABLE: timeout"; rc=10; }
    if [[ $rc -ne 10 ]]; then echo "$CHROME_OUT"; exit "$rc"; fi
    echo "$CHROME_OUT" >&2
    emit_store_forensics
    exit 2
  fi
  echo "$out"
}

cmd_send_once() {
  local file="${1:-}"
  [[ -f "$file" && -s "$file" ]] || { echo "usage: dot.sh send <non-empty message-file>" >&2; exit 2; }
  if [[ "${DOT_PREPARED:-0}" == "1" ]]; then
    if [[ "${DOT_ENFORCE_SYSTEM_CHROME:-0}" == "1" ]] && \
       ! is_system_chrome "${DOT_CHROME_BIN:-}" && [[ "${DOT_ALLOW_FOREIGN_BINARY:-0}" != "1" ]]; then
      echo "DOT_CHROME_UNAVAILABLE: refusing non-system Chrome binary '${DOT_CHROME_BIN:-}' (foreign binaries evict Keychain-encrypted session cookies; set DOT_ALLOW_FOREIGN_BINARY=1 only to override deliberately)" >&2
      exit 10
    fi
    if ! acquire_profile_lock "${DOT_CHROME_USER_DATA:-}" "${DOT_LOCK_WAIT_SECS:-90}"; then
      echo "DOT_CHROME_UNAVAILABLE: DOT_PROFILE_LOCKED (another dot.sh instance owns this profile)" >&2
      exit 2
    fi
    if ! profile_disk_ok "${DOT_CHROME_USER_DATA:-}"; then
      exit 2
    fi
    local extra_node_path
    if [[ -d "$HOME/.npm-global/lib/node_modules" ]]; then
      extra_node_path="$HOME/.npm-global/lib/node_modules:${NODE_PATH:-}"
    elif [[ -d "$(dirname "$NODE")/../lib/node_modules" ]]; then
      extra_node_path="$(dirname "$NODE")/../lib/node_modules:${NODE_PATH:-}"
    else
      extra_node_path="${NODE_PATH:-}"
    fi
    DOT_ACCOUNT="$ACCOUNT" DOT_URL="$DOT_URL" DOT_CHROME_USER_DATA="${DOT_CHROME_USER_DATA:-}" DOT_CLEAR_DRAFT="${DOT_CLEAR_DRAFT:-}" DOT_PREPARED="1" DOT_NO_REMOTE="1" NODE_PATH="$extra_node_path" \
      "$NODE" "$HERE/dot_chrome.mjs" send-prepared "$file"
    exit $?
  fi
  local out="" rc=0
  run_chrome send "$file" || rc=$?
  [[ $rc -eq 124 ]] && { CHROME_OUT="DOT_CHROME_UNAVAILABLE: timeout"; rc=10; }
  [[ $rc -ne 0 && $rc -ne 10 ]] && CHROME_OUT="DOT_SEND_UNVERIFIED chrome_rc=$rc"
  if [[ $rc -ne 10 ]]; then
    out="$CHROME_OUT"
    [[ "$out" == *DOT_SENT_VERIFIED* ]] && snapshot_cookie_store "$(profile_cookies_db)"
  else
    echo "$CHROME_OUT" >&2
    emit_store_forensics
    exit 2
  fi
  rotate_account_if_needed "$out" "${DOT_ACTION:-send-once}" "$file"
  echo "$out"
  case "$out" in
    *DOT_COMPOSER_MISMATCH*) echo "Composer text did not match the message after typing; nothing sent. Check with 'dot.sh read'." >&2; exit 4 ;;
    *DOT_DRAFT_PRESENT*) echo "Refusing to send: the dot composer holds an unsent draft (a peer session?). Not cleared. Retry later." >&2; exit 3 ;;
    *DOT_USAGE_LIMIT_REACHED*) echo "ChatGPT usage limit reached: $out" >&2; exit 5 ;;
    *DOT_SENT_VERIFIED*|*DOT_DRYRUN_OK*) ;;
    *) echo "Send not verified in page text; run 'dot.sh read' to check." >&2; exit 4 ;;
  esac
}

cmd_send() {
  export DOT_ACTION="send"
  local deadline=$((SECONDS + ${DOT_WAIT_SECS:-1800})) rc=0
  while :; do
    (cmd_send_once "$@") && return 0 || rc=$?
    [[ $rc -eq 3 && $SECONDS -lt $deadline ]] || return "$rc"
    echo "dot.sh: composer busy; retrying in ${DOT_RETRY_SECS:-60}s" >&2
    sleep "${DOT_RETRY_SECS:-60}"
  done
}

validate_login_profile() {
  local expected_dir="$1"
  local expected_profile_directory="$2"
  local profile_info profile_dir profile_directory
  if ! profile_info=$(DOT_ACCOUNT="$ACCOUNT" DOT_CONFIG_FILE="$CONFIG_FILE" \
      DOT_URL="${DOT_URL:-}" DOT_CHROME_USER_DATA="$expected_dir" \
      "$NODE" "$HERE/dot_chrome.mjs" resolve-profile 2>&1); then
    echo "$profile_info" >&2
    return 1
  fi
  profile_dir=$("$NODE" -e 'try { process.stdout.write(JSON.parse(process.argv[1]).profileDir || ""); } catch {}' \
    "$profile_info" 2>/dev/null || true)
  profile_directory=$("$NODE" -e 'try { process.stdout.write(JSON.parse(process.argv[1]).profileDirectory || ""); } catch {}' \
    "$profile_info" 2>/dev/null || true)
  if [[ "$profile_dir" != "$expected_dir" ||
        "$profile_directory" != "$expected_profile_directory" ]]; then
    echo "dot.sh: refusing login because the configured profile changed before launch" >&2
    return 1
  fi
}

cmd_login() {
  local dir="${DOT_CHROME_USER_DATA:-}"
  if [[ -z "$dir" ]]; then
    echo "dot.sh: refusing login because the dedicated account profile could not be resolved" >&2
    exit 2
  fi
  if ! validate_login_profile "$dir" "$PROFILE_DIRECTORY"; then
    exit 2
  fi
  mkdir -p "$dir"
  local target_url="${DOT_URL:-https://chatgpt.com}"
  echo "dot.sh: launching visible Google Chrome for account '$ACCOUNT'" >&2
  echo "  Profile directory: $dir" >&2
  echo "  URL: $target_url" >&2
  echo "Sign in to ChatGPT in the Chrome window. When finished and the chat page loads, close Chrome." >&2

  local chrome_bin="${DOT_CHROME_BIN:-}"
  if [[ -z "$chrome_bin" ]]; then
    if [[ "$(uname -s)" == "Darwin" ]]; then
      chrome_bin="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    else
      chrome_bin="$(command -v google-chrome || command -v chromium-browser || command -v chromium || true)"
    fi
  fi
  if [[ ! -x "$chrome_bin" ]]; then
    echo "dot.sh: Google Chrome binary not found: $chrome_bin" >&2
    exit 2
  fi
  # Foreign-binary guard: anything but the system Google Chrome requires an
  # explicit opt-in (is_system_chrome tightens Linux to the resolved path).
  if [[ "${DOT_ENFORCE_SYSTEM_CHROME:-0}" == "1" ]] && \
     ! is_system_chrome "$chrome_bin" && [[ "${DOT_ALLOW_FOREIGN_BINARY:-0}" != "1" ]]; then
    echo "dot.sh: refusing login: '$chrome_bin' is not the system Google Chrome. Foreign binaries evict Keychain-encrypted session cookies. Set DOT_ALLOW_FOREIGN_BINARY=1 only if you deliberately accept that risk." >&2
    exit 2
  fi
  if ! profile_disk_ok "$dir"; then
    exit 2
  fi
  if ! acquire_profile_lock "$dir" "${DOT_LOGIN_LOCK_WAIT_SECS:-15}"; then
    echo "dot.sh: another dot.sh instance or login window holds this profile; close it and retry" >&2
    exit 2
  fi
  # Hold the coordinator STOP marker for the whole login window so ticks do
  # not collide with the visible Chrome (removed only if we created it).
  if [[ -d "$(dirname "${DOT_STOP_MARKER_PATH:-}")" && ! -f "${DOT_STOP_MARKER_PATH:-}" ]]; then
    touch "${DOT_STOP_MARKER_PATH:-}" 2>/dev/null && DOT_STOP_CREATED=1
  fi
  if ! validate_login_profile "$dir" "$PROFILE_DIRECTORY"; then
    login_stop_cleanup
    release_profile_lock
    exit 2
  fi
  local profile_args=()
  if [[ -n "$PROFILE_DIRECTORY" ]]; then
    profile_args+=("--profile-directory=$PROFILE_DIRECTORY")
  fi
  # Launch with the SAME password-store semantics as the headless path so a
  # manually signed-in session is stored decryptable by every later launch.
  local store_args=()
  if [[ "$(uname -s)" == "Darwin" ]]; then
    store_args=("--password-store=keychain")
  else
    store_args=("--password-store=gnome-libsecret")
  fi
  local chrome_rc=0
  "$chrome_bin" --user-data-dir="$dir" --no-first-run \
    "${profile_args[@]}" \
    "${store_args[@]}" \
    --no-default-browser-check "$target_url" || chrome_rc=$?
  login_stop_cleanup
  release_profile_lock
  exit "$chrome_rc"
}

cmd_existing_profile_only() {
  local rc=0
  run_chrome existing-profile-only || rc=$?
  if [[ $rc -ne 0 && $rc -ne 10 ]]; then
    echo "DOT_PROFILE_LAUNCH_RESULT {\"schema_version\":1,\"launch_state\":\"unavailable\",\"diagnostic\":\"transport_error\"}"
    exit "$rc"
  fi
  printf '%s\n' "$CHROME_OUT"
  exit "$rc"
}

cmd_probe() {
  local expected_digest="${1:-}"
  [[ "$expected_digest" =~ ^[a-f0-9]{64}$ ]] || {
    echo "usage: dot.sh [--account <name>] probe <expected-email-sha256>" >&2
    exit 2
  }
  local rc=0
  run_chrome probe "$expected_digest" || rc=$?
  if [[ $rc -ne 0 || "$CHROME_OUT" != DOT_SESSION_PROBE\ * ]]; then
    echo "dot.sh: session probe transport unavailable" >&2
    emit_store_forensics
    exit 2
  fi
  if [[ "$CHROME_OUT" == *'"status":"authenticated"'* ]]; then
    snapshot_cookie_store "$(profile_cookies_db)"
  fi
  printf '%s\n' "$CHROME_OUT"
}

cmd_restore_session() {
  local dir="${DOT_CHROME_USER_DATA:-}"
  [[ -z "$dir" ]] && { echo "dot.sh: profile directory not resolved" >&2; exit 2; }
  local prof="${PROFILE_DIRECTORY:-Default}"
  local db="$dir/$prof/Cookies" snap="$dir/$prof/Cookies.snapshot"
  if ! [[ -f "$snap" ]]; then
    echo "dot.sh: no session snapshot for this profile. Canonical recovery: dot.sh --account $ACCOUNT login" >&2
    exit 2
  fi
  if pgrep -f "user-data-dir=$dir" >/dev/null 2>&1; then
    echo "dot.sh: a Chrome process is using this profile; close it before restoring" >&2
    exit 2
  fi
  if ! acquire_profile_lock "$dir" "${DOT_LOCK_WAIT_SECS:-90}"; then
    echo "dot.sh: another dot.sh instance holds this profile; close it and retry" >&2
    exit 2
  fi
  if [[ -f "$db" ]]; then
    cp "$db" "$db.pre-restore" || { release_profile_lock; echo "dot.sh: could not keep a pre-restore copy; aborting" >&2; exit 2; }
  fi
  if cp "$snap" "$db"; then
    rm -f "$db-journal" "$db-wal" "$db-shm"
    chmod 600 "$db"
  else
    release_profile_lock
    echo "dot.sh: restore copy failed" >&2
    exit 2
  fi
  echo "dot.sh: session snapshot restored (pre-restore copy kept at $db.pre-restore)." >&2
  echo "dot.sh: verify with 'dot.sh --account $ACCOUNT read'; if it reports not signed in, the token rotated server-side — recover with 'dot.sh --account $ACCOUNT login' (never resync from another profile)." >&2
  release_profile_lock
}

if [[ "${DOT_SKIP_DISPATCH:-0}" != "1" ]]; then
  trap 'release_profile_lock; login_stop_cleanup' EXIT
  case "${1:-}" in
    read) shift; cmd_read "$@" ;;
    probe) shift; cmd_probe "$@" ;;
    send) shift; cmd_send "$@" ;;
    send-once) shift; cmd_send_once "$@" ;;
    send-prepared) shift; export DOT_PREPARED=1; cmd_send_once "$@" ;;
    existing-profile-only) shift; cmd_existing_profile_only "$@" ;;
    restore-session) shift; cmd_restore_session "$@" ;;
    login|auth) shift; cmd_login "$@" ;;
    *) echo "usage: dot.sh [--account <name>] [--url <url>] read [chars] | probe <expected-email-sha256> | send|send-once|send-prepared <message-file> | existing-profile-only | restore-session | login" >&2; exit 2 ;;
  esac
fi
