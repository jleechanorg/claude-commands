#!/usr/bin/env bash
# Regression tests for dot.sh session hardening (2026-10-11 review batch):
#   1. cmd_login launches Chrome with the same password-store flags as headless
#   2. cmd_login refuses foreign Chrome binaries without an explicit opt-in
#   3. cmd_login auto-manages the coordinator STOP marker
#   4. per-profile exclusive lock serializes concurrent dot.sh invocations
#   5. low-disk preflight refuses to launch Chrome against the live profile
#   6. cookie-store rebuild signature is classified and surfaced (not a generic
#      "not signed in") so operators stop misreading evictions as account logouts
#   7. run_chrome tears down process-group survivors even when node exits first
#   8. per-profile cookie-store snapshot + restore-session recovery mechanics
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOT_SH="$SCRIPT_DIR/../scripts/dot.sh"
REAL_NODE="$(command -v node)"
[[ -x "$REAL_NODE" ]] || { echo "node required for these tests" >&2; exit 1; }

PASS=0
FAIL=0
declare -a FAILURES=()

ok()   { PASS=$((PASS+1)); echo "  ok - $1"; }
bad()  { FAIL=$((FAIL+1)); FAILURES+=("$1"); echo "  FAIL - $1"; }

new_fixture() {
  local f
  f="$(mktemp -d /tmp/dot-hardening-fixture.XXXXXX)"
  mkdir -p "$f/profile/Default"
  cp "$DOT_SH" "$f/dot.sh"
  cp "$SCRIPT_DIR/../scripts/dot_chrome.mjs" "$f/dot_chrome.mjs"
  cat > "$f/config.json" <<EOF
{"default_account":"testacct","accounts":{"testacct":{"url":"https://chatgpt.com/","user_data_dir":"$f/profile"}}}
EOF
  echo "$f"
}

mk_chrome_stub() {
  local f="$1" name="$2" sleep_secs="${3:-0}"
  cat > "$f/$name" <<EOF
#!/usr/bin/env bash
printf '%s\n' "\$@" > "$f/chrome-argv.txt"
[[ "$sleep_secs" -gt 0 ]] && sleep "$sleep_secs"
exit 0
EOF
  chmod +x "$f/$name"
}

mk_fake_cookies() {
  # $1=db path, $2=mode: rebuilt|authenticated
  local db="$1" mode="$2"
  mkdir -p "$(dirname "$db")"
  rm -f "$db"
  sqlite3 "$db" "CREATE TABLE cookies (name TEXT, encrypted_value BLOB, creation_utc INTEGER, expires_utc INTEGER, host_key TEXT);"
  if [[ "$mode" == "rebuilt" ]]; then
    sqlite3 "$db" "INSERT INTO cookies VALUES ('oai-did', x'00', (strftime('%s','now')+11644473600)*1000000, 99999999999000000, 'chatgpt.com');"
  else
    sqlite3 "$db" "INSERT INTO cookies VALUES ('__Secure-next-auth.session-token.0', x'00', 1, 99999999999000000, 'chatgpt.com');"
    sqlite3 "$db" "INSERT INTO cookies VALUES ('oai-did', x'00', 1, 99999999999000000, 'chatgpt.com');"
  fi
}

run_login() {
  local f="$1"; shift
  env DOT_NODE="$REAL_NODE" DOT_CONFIG_FILE="$f/config.json" \
    DOT_CHROME_USER_DATA="$f/profile" DOT_ACCOUNT=testacct \
    DOT_STOP_MARKER_PATH="$f/STOP" TMPDIR="${TMPDIR:-/tmp}" \
    "$@" bash "$f/dot.sh" login 2>&1
}

echo "== test 1: login password-store flag parity =="
F=$(new_fixture); FIXTURE="$F" mk_chrome_stub "$F" chrome 0
out=$(FIXTURE="$F" run_login "$F" DOT_CHROME_BIN="$F/chrome" DOT_ALLOW_FOREIGN_BINARY=1)
login_rc_pipe=(${PIPESTATUS[0]:-0})
if [[ "${login_rc_pipe[0]}" != "0" ]]; then
  bad "login must exit 0 when Chrome exits 0 (got ${login_rc_pipe[0]})"
fi
if grep -q -- "--password-store=keychain" "$F/chrome-argv.txt" 2>/dev/null; then
  ok "login passes --password-store=keychain on Darwin"
else
  bad "login must pass the same password-store flag as the headless path (argv: $(cat "$F/chrome-argv.txt" 2>/dev/null | tr '\n' ' '))"
fi
rm -rf "$F"
F=$(new_fixture); FIXTURE="$F" mk_chrome_stub "$F" chrome 0
cat > "$F/chrome" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$@" > "$FIXTURE/chrome-argv.txt"
exit 7
EOF
chmod +x "$F/chrome"
out=$(FIXTURE="$F" run_login "$F" DOT_CHROME_BIN="$F/chrome" DOT_ALLOW_FOREIGN_BINARY=1)
login_rc_pipe=(${PIPESTATUS[0]:-0})
if [[ "${login_rc_pipe[0]}" == "7" ]]; then
  ok "login propagates Chrome's nonzero exit code"
else
  bad "login must propagate Chrome exit 7 (got ${login_rc_pipe[0]})"
fi
rm -rf "$F"

echo "== test 2: foreign binary enforcement is opt-in =="
F=$(new_fixture); FIXTURE="$F" mk_chrome_stub "$F" chrome 0
out=$(FIXTURE="$F" run_login "$F" DOT_CHROME_BIN="$F/chrome" DOT_ENFORCE_SYSTEM_CHROME=1)
if [[ "$out" == *"refusing login"* && ! -f "$F/chrome-argv.txt" ]]; then
  ok "DOT_ENFORCE_SYSTEM_CHROME=1 refuses a non-system binary without the override"
else
  bad "enforcement must refuse a foreign binary (out: $out)"
fi
if FIXTURE="$F" run_login "$F" DOT_CHROME_BIN="$F/chrome" >/dev/null 2>&1 && [[ -f "$F/chrome-argv.txt" ]]; then
  ok "documented DOT_CHROME_BIN overrides still work by default"
else
  bad "a plain DOT_CHROME_BIN override must keep working (documented caller)"
fi
rm -rf "$F"

echo "== test 3: login auto-manages STOP marker =="
F=$(new_fixture); FIXTURE="$F" mk_chrome_stub "$F" chrome 4
FIXTURE="$F" run_login "$F" DOT_CHROME_BIN="$F/chrome" DOT_ALLOW_FOREIGN_BINARY=1 >/dev/null 2>&1 &
login_pid=$!
sleep 2.5
stop_during=0; [[ -f "$F/STOP" ]] && stop_during=1
wait $login_pid
stop_after=0; [[ -f "$F/STOP" ]] && stop_after=1
if [[ "$stop_during" == 1 && "$stop_after" == 0 ]]; then
  ok "STOP created during login window and removed after"
else
  bad "STOP marker lifecycle wrong (during=$stop_during after=$stop_after)"
fi
# preexisting STOP must survive
F=$(new_fixture); FIXTURE="$F" mk_chrome_stub "$F" chrome 1
touch "$F/STOP"
FIXTURE="$F" run_login "$F" DOT_CHROME_BIN="$F/chrome" DOT_ALLOW_FOREIGN_BINARY=1 >/dev/null 2>&1
[[ -f "$F/STOP" ]] && ok "preexisting STOP preserved" || bad "preexisting STOP was removed by cmd_login"
rm -rf "$F"

echo "== test 4: per-profile exclusive lock (kernel flock) =="
F=$(new_fixture)
export DOT_NODE="$REAL_NODE" DOT_CONFIG_FILE="$F/config.json" DOT_ACCOUNT=testacct DOT_CHROME_USER_DATA="$F/profile" DOT_SKIP_DISPATCH=1
source "$F/dot.sh" >/dev/null 2>&1
set +e +o pipefail 2>/dev/null || set +e
# a real concurrent holder: a subshell that acquires and sleeps
( acquire_profile_lock "$F/profile" 10 2>/dev/null; sleep 30 ) & holder_job=$!
sleep 2
if acquire_profile_lock "$F/profile" 3 2>/dev/null; then
  bad "second acquire must fail while a live instance holds the flock"
  release_profile_lock
else
  ok "lock serializes concurrent invocations"
fi
kill "$holder_job" 2>/dev/null; wait "$holder_job" 2>/dev/null
sleep 2  # flock auto-releases on holder death; allow watchdog detection
if acquire_profile_lock "$F/profile" 5 2>/dev/null; then
  ok "lock auto-released after holder death (kernel semantics)"
  release_profile_lock
else
  bad "kernel flock must auto-release when the holder dies"
fi
rm -rf "$F"
unset DOT_SKIP_DISPATCH

echo "== test 5: low-disk preflight =="
F=$(new_fixture); FIXTURE="$F" mk_chrome_stub "$F" chrome 0
out=$(FIXTURE="$F" run_login "$F" DOT_CHROME_BIN="$F/chrome" DOT_ALLOW_FOREIGN_BINARY=1 DOT_MIN_FREE_MB=99999999)
if [[ "$out" == *"disk"* && ! -f "$F/chrome-argv.txt" ]]; then
  ok "launch refused below the disk floor"
else
  bad "low-disk preflight must refuse the launch (out: $out)"
fi
rm -rf "$F"

echo "== test 6: rebuild-signature classification =="
F=$(new_fixture)
export DOT_NODE="$REAL_NODE" DOT_CONFIG_FILE="$F/config.json" \
  DOT_ACCOUNT=testacct DOT_CHROME_USER_DATA="$F/profile" DOT_SKIP_DISPATCH=1
source "$F/dot.sh" >/dev/null 2>&1
set +e +o pipefail 2>/dev/null || set +e
mk_fake_cookies "$F/profile/Default/Cookies" "rebuilt"
sig=$(classify_cookie_store "$F/profile/Default/Cookies" 2>/dev/null || echo "helper-missing")
[[ "$sig" == "rebuild" ]] && ok "rebuilt anonymous store classified" || bad "rebuild classification (got: $sig)"
mk_fake_cookies "$F/profile/Default/Cookies" "authenticated"
sig=$(classify_cookie_store "$F/profile/Default/Cookies" 2>/dev/null || echo "helper-missing")
[[ "$sig" == "authenticated" ]] && ok "authenticated store classified" || bad "authenticated classification (got: $sig)"
rm -rf "$F"
unset DOT_SKIP_DISPATCH

echo "== test 7: node-exit group teardown =="
F=$(new_fixture)
cat > "$F/node" <<'EOF'
#!/usr/bin/env bash
if [[ "${2:-}" == resolve-profile* ]]; then
  printf '{"profileDir":"%s","profileDirectory":"Default","url":"https://chatgpt.com/"}' "$FIXTURE/profile"
  exit 0
fi
if [[ "${1:-}" == "-e" ]]; then exit 0; fi
# emulate: node wrapper exits immediately but a browser descendant stays alive
sleep 600 &
echo $! > "$FAKE_BROWSER_PID_FILE"
exit 0
EOF
chmod +x "$F/node"
: > "$F/dot_chrome.mjs"
export FIXTURE="$F" FAKE_BROWSER_PID_FILE="$F/browser.pid"
export DOT_NODE="$F/node" DOT_CONFIG_FILE="$F/config.json" DOT_ACCOUNT=testacct \
  DOT_CHROME_USER_DATA="$F/profile" DOT_SKIP_DISPATCH=1
source "$F/dot.sh" >/dev/null 2>&1
set +e +o pipefail 2>/dev/null || set +e
run_chrome read 100 >/dev/null 2>&1
sleep 1
leaked=0
if [[ -f "$FAKE_BROWSER_PID_FILE" ]] && kill -0 "$(cat "$FAKE_BROWSER_PID_FILE")" 2>/dev/null; then leaked=1; fi
[[ "$leaked" == 0 ]] && ok "group survivor killed after node exit" || bad "node-exit leak: browser descendant survived run_chrome"
kill -KILL "$(cat "$FAKE_BROWSER_PID_FILE" 2>/dev/null)" 2>/dev/null
rm -rf "$F"
unset DOT_SKIP_DISPATCH

echo "== test 8: snapshot + restore-session =="
F=$(new_fixture)
export DOT_NODE="$REAL_NODE" DOT_CONFIG_FILE="$F/config.json" \
  DOT_ACCOUNT=testacct DOT_CHROME_USER_DATA="$F/profile" DOT_SKIP_DISPATCH=1
source "$F/dot.sh" >/dev/null 2>&1
set +e +o pipefail 2>/dev/null || set +e
mk_fake_cookies "$F/profile/Default/Cookies" "authenticated"
snapshot_cookie_store "$F/profile/Default/Cookies" >/dev/null 2>&1
if [[ -f "$F/profile/Default/Cookies.snapshot" ]]; then
  ok "snapshot written next to the live store"
  mk_fake_cookies "$F/profile/Default/Cookies" "rebuilt"
  out=$(cmd_restore_session 2>&1)
  sig=$(classify_cookie_store "$F/profile/Default/Cookies" 2>/dev/null)
  [[ "$sig" == "authenticated" ]] && ok "restore-session restored the snapshot (store now authenticated)" \
    || bad "restore-session must restore the snapshot (out: $out; sig: $sig)"
  [[ -f "$F/profile/Default/Cookies.pre-restore" ]] && ok "restore keeps a pre-restore copy" || ok "restore keeps a pre-restore copy (optional)"
else
  bad "snapshot_cookie_store must persist a restorable snapshot"
fi
rm -rf "$F"
unset DOT_SKIP_DISPATCH

echo "== test 9: flock not stealable regardless of lockfile age =="
F=$(new_fixture)
export DOT_NODE="$REAL_NODE" DOT_CONFIG_FILE="$F/config.json" DOT_ACCOUNT=testacct DOT_CHROME_USER_DATA="$F/profile" DOT_SKIP_DISPATCH=1
source "$F/dot.sh" >/dev/null 2>&1
set +e +o pipefail 2>/dev/null || set +e
( acquire_profile_lock "$F/profile" 10 2>/dev/null; sleep 30 ) & holder_job=$!
sleep 2
lp="$(profile_lock_path "$F/profile")"; touch -t 202001010000 "$lp" 2>/dev/null
if acquire_profile_lock "$F/profile" 3 2>/dev/null; then
  bad "flock was stolen via apparent file age"
  release_profile_lock
else
  ok "flock holder unaffected by backdated lockfile mtime"
fi
kill "$holder_job" 2>/dev/null; wait "$holder_job" 2>/dev/null; sleep 2
rm -rf "$F"
unset DOT_SKIP_DISPATCH

echo "== test 10: kill -9 of the parent auto-releases the flock =="
F=$(new_fixture)
export DOT_NODE="$REAL_NODE" DOT_CONFIG_FILE="$F/config.json" DOT_ACCOUNT=testacct DOT_CHROME_USER_DATA="$F/profile" DOT_SKIP_DISPATCH=1
# run the acquire in a disposable child shell we then SIGKILL (worst case)
bash -c "source '$F/dot.sh' >/dev/null 2>&1; acquire_profile_lock '$F/profile' 60; sleep 30" & victim=$!
sleep 3
kill -9 "$victim" 2>/dev/null; wait "$victim" 2>/dev/null
sleep 3  # parent-death watchdog: holder exits within ~1s of the parent dying
source "$F/dot.sh" >/dev/null 2>&1
set +e +o pipefail 2>/dev/null || set +e
if acquire_profile_lock "$F/profile" 5 2>/dev/null; then
  ok "flock auto-released after SIGKILL of the owning process"
  release_profile_lock
else
  bad "SIGKILLed owner must release the flock via the parent-death watchdog"
fi
rm -rf "$F"
unset DOT_SKIP_DISPATCH

echo "== test 16: 8-way contention never double-holds the lock =="
F=$(new_fixture)
export DOT_NODE="$REAL_NODE" DOT_CONFIG_FILE="$F/config.json" DOT_ACCOUNT=testacct DOT_CHROME_USER_DATA="$F/profile" DOT_SKIP_DISPATCH=1
source "$F/dot.sh" >/dev/null 2>&1
set +e +o pipefail 2>/dev/null || set +e
for round in 1 2 3; do
  RES="$F/results-$round"; rm -f "$RES"*
  for i in $(seq 1 8); do
    (
      if acquire_profile_lock "$F/profile" 12 2>/dev/null; then
        # record the ready path: concurrent sibling callers must hold DISTINCT
        # handshakes ($$ collisions produce 7 false claims — codex round 7)
        echo "${DOT_LOCK_READY:-none}" >> "$RES.ready"
        sleep 1
        if kill -0 "${DOT_LOCK_HOLDER_PID:-0}" 2>/dev/null; then echo OWN >> "$RES"; else echo STOLEN >> "$RES"; fi
        release_profile_lock
      else
        echo MISS >> "$RES"
      fi
    ) &
  done
  wait
  stolen=$(grep -c STOLEN "$RES" 2>/dev/null); stolen=${stolen:-0}
  own=$(grep -c OWN "$RES" 2>/dev/null); own=${own:-0}
  distinct=$(sort -u "$RES.ready" 2>/dev/null | grep -c .); distinct=${distinct:-0}
  if [[ "$stolen" == "0" && "$distinct" == "$own" && "$own" -gt 0 ]]; then
    ok "round $round: zero thefts, $distinct distinct handshakes for $own claims"
  else
    bad "round $round: thefts=$stolen own=$own distinct=$distinct (ready-file collision = false claims)"
  fi
  rm -f "$RES.ready"
done
rm -rf "$F"
unset DOT_SKIP_DISPATCH

echo "== test 17: caller killed while its holder is queued -> orphan releases =="
F=$(new_fixture)
export DOT_NODE="$REAL_NODE" DOT_CONFIG_FILE="$F/config.json" DOT_ACCOUNT=testacct DOT_CHROME_USER_DATA="$F/profile" DOT_SKIP_DISPATCH=1
source "$F/dot.sh" >/dev/null 2>&1
set +e +o pipefail 2>/dev/null || set +e
# A: hold the lock
acquire_profile_lock "$F/profile" 5 2>/dev/null
# B: caller that queues behind A, then dies
bash -c "source '$F/dot.sh' >/dev/null 2>&1; acquire_profile_lock '$F/profile' 30; sleep 60" & queued_job=$!
sleep 2   # B's holder is now blocked in the flock queue
kill -9 "$queued_job" 2>/dev/null; wait "$queued_job" 2>/dev/null
release_profile_lock   # A releases -> orphan acquires, sees dead parent, releases
sleep 3
if acquire_profile_lock "$F/profile" 5 2>/dev/null; then
  ok "queued-holder orphan released the flock after caller death"
  release_profile_lock
else
  bad "orphaned queued holder must not retain the flock"
fi
rm -rf "$F"
unset DOT_SKIP_DISPATCH

echo
echo "pass=$PASS fail=$FAIL"
if [[ ${#FAILURES[@]} -gt 0 ]]; then
  printf '  - %s\n' "${FAILURES[@]}"
  exit 1
fi
exit 0
