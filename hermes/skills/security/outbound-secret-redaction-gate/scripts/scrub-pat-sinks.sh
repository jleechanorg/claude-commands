#!/usr/bin/env bash
# scrub-pat-sinks.sh - Enumerate and scrub every sink that holds a GitHub PAT
# on this macOS host. Verified 2026-07-17 against $HOME/.
#
# Usage:
#   ./scrub-pat-sinks.sh           # scrub all sinks using current Keychain PAT
#   ./scrub-pat-sinks.sh --audit   # report sinks containing PATs (no edits)
#   ./scrub-pat-sinks.sh --fleet   # also neutralize inline-PAT .git/config URLs
#
# Exit codes:
#   0 - all sinks clean
#   1 - sinks still contain PATs (re-run)
#   2 - Keychain missing the new PAT (run `security add-generic-password` first)
set -euo pipefail

ACCOUNT="${GH_ACCOUNT:-jleechan2015}"
SERVICE="${GH_SERVICE:-github.com}"
PAT_RE='gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}'

AUDIT_ONLY=0
DO_FLEET=0
for a in "$@"; do
  case "$a" in
    --audit) AUDIT_ONLY=1 ;;
    --fleet) DO_FLEET=1 ;;
    --help|-h) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "unknown flag: $a" >&2; exit 2 ;;
  esac
done

if ! NEW_PAT="$(security find-generic-password -s "$SERVICE" -a "$ACCOUNT" -w 2>/dev/null)"; then
  echo "Keychain entry not found for service=$SERVICE account=$ACCOUNT" >&2
  echo "Run: security add-generic-password -U -a $ACCOUNT -s $SERVICE -w \"<NEW_PAT>\"" >&2
  exit 2
fi

# Verify the new PAT works under a clean env
CLEAN_ENV="env -i HOME=$HOME PATH=$HOME/.local/bin:/opt/homebrew/bin:/usr/bin:/bin"
if ! $CLEAN_ENV gh auth status --hostname github.com >/dev/null 2>&1; then
  echo "Keychain PAT does not authenticate via gh - rotate via the GitHub web UI first" >&2
  exit 2
fi

# Sinks that may hold the PAT verbatim
SINKS=(
  "$HOME/.bashrc"
  "$HOME/.config/gh/hosts.yml"
  "$HOME/.config/ezgha/gh_token"
  "$HOME/Library/LaunchAgents/ai.agento.ao-go-daemon.plist"
)

# Add AO runner yamls
AOD="$HOME/.config/ao-runner"
if [[ -d "$AOD" ]]; then
  while IFS= read -r f; do SINKS+=("$f"); done < <(find "$AOD" -maxdepth 1 -type f -name '*.yaml')
fi

# Plaintext backups - delete, never edit
BACKUPS=( "$HOME/.config/gh/hosts.yml.bak" )
while IFS= read -r f; do BACKUPS+=("$f"); done < <(find "$HOME/.config/gh" -maxdepth 1 -type f -name 'hosts.yml.bak*' 2>/dev/null)

# Phase A - audit-only path
scan() {
  local hits=()
  for p in "${SINKS[@]}"; do
    [[ -f "$p" ]] || continue
    local n
    n="$(grep -cE "$PAT_RE" "$p" 2>/dev/null || true)"
    [[ "$n" -gt 0 ]] && hits+=("$p:$n")
  done
  printf 'sink matches:\n'
  for h in "${hits[@]}"; do printf '  %s\n' "$h"; done
  printf 'plaintext backups present:\n'
  for b in "${BACKUPS[@]}"; do
    [[ -f "$b" ]] && printf '  %s\n' "$b"
  done
}

if [[ "$AUDIT_ONLY" -eq 1 ]]; then
  scan
  exit 0
fi

# Phase B - edit sinks in place (PAT replaced with the new keychain value)
for p in "${SINKS[@]}"; do
  [[ -f "$p" ]] || continue
  if grep -qE "$PAT_RE" "$p"; then
    # BSD sed -i '' required on macOS
    sed -i '' -E "s|$PAT_RE|$NEW_PAT|g" "$p"
    [[ "$p" == *.yaml ]] && chmod 600 "$p"
    [[ "$p" == *gh_token ]] && chmod 600 "$p"
    echo "scrubbed: $p"
  fi
done

# Phase C - delete plaintext backups
for b in "${BACKUPS[@]}"; do
  [[ -f "$b" ]] && rm -f "$b" && echo "removed plaintext backup: $b"
done

# Phase D - optional fleet-wide .git/config neutralization
if [[ "$DO_FLEET" -eq 1 ]]; then
  FOUND=$(python3 - <<PY
import os, re
PAT = re.compile(r"$PAT_RE")
hits = []
for base in [os.path.expanduser(b) for b in ["~/projects","~/projects_other","~/projects_reference","~/repos","~/agent-f","~/.worktrees"]]:
  if not os.path.isdir(base): continue
  for dp, dn, fn in os.walk(base):
    if ".git" in dn:
      cfg = os.path.join(dp, ".git", "config")
      try:
        if PAT.search(open(cfg, errors="ignore").read()): hits.append(cfg)
      except: pass
      dn.remove(".git")
for h in hits: print(h)
PY
)
  if [[ -n "$FOUND" ]]; then
    while IFS= read -r cfg; do
      repo="$(dirname "$(dirname "$cfg")")"
      url="$(git -C "$repo" remote get-url origin 2>/dev/null || true)"
      [[ -z "$url" ]] && continue
      neutral="$(printf '%s' "$url" | sed -E 's|^https://[^/@]+(:[^/@]+)?@github\.com/|https://github.com/|')"
      git -C "$repo" remote set-url origin "$neutral" >/dev/null 2>&1 && echo "neutralized: $repo"
    done <<< "$FOUND"
  fi
fi

# Phase E - re-audit to confirm clean state
scan
echo
echo "Verify clean state across all sinks:"
remaining=$(python3 - "$NEW_PAT" <<PY
import os, re, sys, hashlib
PAT = re.compile(r"$PAT_RE")
new_hash = hashlib.sha256(sys.argv[1].encode()).hexdigest()[:12]
count = 0
for p in [
  os.path.expanduser("~/.bashrc"),
  os.path.expanduser("~/.config/gh/hosts.yml"),
  os.path.expanduser("~/.config/ezgha/gh_token"),
  os.path.expanduser("~/Library/LaunchAgents/ai.agento.ao-go-daemon.plist"),
] + [os.path.join(os.path.expanduser("~/.config/ao-runner"), f)
       for f in os.listdir(os.path.expanduser("~/.config/ao-runner")) if f.endswith(".yaml")] if os.path.exists(p):
  text = open(p, errors="ignore").read()
  for m in PAT.findall(text):
    if hashlib.sha256(m.encode()).hexdigest()[:12] != new_hash:
      count += 1
      print(f"  STALE: {p}")
print(count)
PY
)
total=$(echo "$remaining" | tail -1)
if [[ "$total" == "0" ]]; then
  echo "  all sinks contain only the new PAT (fingerprint $(echo "$NEW_PAT" | shasum -a 256 | cut -c1-12))"
  exit 0
else
  echo "  $total sink(s) still hold a different PAT - re-run after more edits" >&2
  exit 1
fi
