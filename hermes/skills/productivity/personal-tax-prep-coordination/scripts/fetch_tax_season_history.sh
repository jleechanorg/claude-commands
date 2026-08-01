#!/bin/bash
# fetch_tax_season_history.sh — Phase 1 + 2 of personal-tax-prep-coordination
#
# Pulls the most recent Preparer threads, vendor 1099 availability
# emails, the prior-year 1040 from Drive, and outstanding TaxDome
# invoices. Outputs both JSON (for tooling) and human-readable MD
# (for review).
#
# Usage: scripts/fetch_tax_season_history.sh [year] [preparer_domain]
#
# Defaults:
#   year = current year - 1 (the tax year that just ended)
#   preparer_domain = orenhenea.com
#
# Output:
#   /tmp/<year>-tax-history.json
#   /tmp/<year>-tax-history.md
#
# Verified 2026-07-18 against gog v?.?.? (Google Workspace CLI).

set -euo pipefail

YEAR="${1:-$(date -v-1y +%Y)}"
PREPARER_DOMAIN="${2:-orenhenea.com}"

GOG="gog -a $USER@gmail.com"
JSON_OUT="/tmp/${YEAR}-tax-history.json"
MD_OUT="/tmp/${YEAR}-tax-history.md"

if [ ! -x "$(command -v gog)" ]; then
  echo "FATAL: 'gog' not on PATH. Install gws + run gws auth login first." >&2
  exit 1
fi

if ! $GOG auth status >/dev/null 2>&1; then
  echo "FATAL: gog not authenticated for $USER@gmail.com." >&2
  exit 1
fi

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

echo "[fetch_tax_season_history] year=${YEAR} preparer=${PREPARER_DOMAIN}" >&2

# 1. Preparer personal emails
$GOG gmail search "from:${PREPARER_DOMAIN} newer_than:18m" --max 50 \
  --json > "$tmp/preparer_emails.json" 2>&1 || true

# 2. Vendor 1099 availability emails (past 18 months)
for pattern in "IMPORTANT TAX RETURN DOCUMENT AVAILABLE" \
               "Important Tax Return Document Available" \
               "Tax Document" "Form 1099" "Your Consolidated Form 1099" \
               "1095" "1099-R" "Wage and Tax"; do
  $GOG gmail search "$pattern" --max 20 --json > "$tmp/vendor_${pattern// /_}.json" 2>&1 || true
done

# 3. Payment confirmations
$GOG gmail search '"Confirmation of invoice"' --max 30 --json > "$tmp/payments.json" 2>&1 || true
$GOG gmail search 'from:paypal.com' --max 30 --json > "$tmp/paypal.json" 2>&1 || true
$GOG gmail search 'from:venmo.com' --max 30 --json > "$tmp/venmo.json" 2>&1 || true

# 4. Drive — prior-year 1040 + tax document folder
$GOG drive search "${YEAR} 1040" "1040 ${YEAR}" "tax return ${YEAR}" \
                  "tax_${YEAR}" "tax/${YEAR}" "${YEAR} tax" \
                  --max 20 --plain > "$tmp/drive_tax.txt" 2>&1 || true

# 5. Tax-season calendar events
$GOG calendar list --from "$(date -v-1y +%Y-%m-%dT%H:%M:%SZ)" \
                   --to "$(date +%Y-%m-%dT%H:%M:%SZ)" \
                   --json --max 200 > "$tmp/calendar.json" 2>&1 || true

# 6. Build JSON summary
python3 - "$tmp" "$YEAR" "$PREPARER_DOMAIN" > "$JSON_OUT" <<'PY'
import sys, json, os, glob
tmp, year, domain = sys.argv[1], sys.argv[2], sys.argv[3]

def slurp(p):
    try:
        with open(p, 'r') as f:
            t = f.read().strip()
        return json.loads(t)
    except Exception:
        return []

result = {
    "year": int(year),
    "preparer_domain": domain,
    "preparer_emails": slurp(f"{tmp}/preparer_emails.json"),
    "vendor_emails": slurp(f"{tmp}/vendor_IMPORTANT_TAX_RETURN_DOCUMENT_AVAILABLE.json"),
    "payment_confirmations": slurp(f"{tmp}/payments.json"),
    "drive_tax_files": [],
    "calendar_events": [],
}

# Drive search returns plain text (CSV-ish), keep first 50 lines
dt = os.path.join(tmp, "drive_tax.txt")
if os.path.exists(dt):
    with open(dt) as f:
        result["drive_tax_files"] = [line.strip() for line in f if line.strip()][:50]

cal = slurp(os.path.join(tmp, "calendar.json"))
if isinstance(cal, dict) and "events" in cal:
    events = cal["events"]
elif isinstance(cal, list):
    events = cal
else:
    events = []
result["calendar_events"] = [
    {"summary": e.get("summary"), "start": e.get("start", {}).get("dateTime") or e.get("start", {}).get("date")}
    for e in events
    if any(k.lower() in (e.get("summary") or "").lower()
           for k in ["tax", "taxdome", "1099", "extension", "filing", "filing deadline"])
]

print(json.dumps(result, indent=2, default=str))
PY

# 7. Build human-readable MD
python3 - "$JSON_OUT" > "$MD_OUT" <<'PY'
import sys, json
p = sys.argv[1]
with open(p) as f:
    r = json.load(f)

lines = [f"# {r['year']} tax season — history", ""]

lines.append("## Preparer emails ({} total)".format(len(r["preparer_emails"])))
for e in r["preparer_emails"][:30]:
    lines.append(f"- `{e.get('id', '?')}` ({e.get('date', '?')}) — {e.get('subject', '?')}")

lines.append("")
lines.append("## Vendor tax-document emails ({} total)".format(len(r["vendor_emails"])))
for e in r["vendor_emails"][:30]:
    lines.append(f"- `{e.get('id', '?')}` ({e.get('date', '?')}) — {e.get('subject', '?')}")

lines.append("")
lines.append("## Payment confirmations ({} total)".format(len(r["payment_confirmations"])))
for e in r["payment_confirmations"][:30]:
    lines.append(f"- `{e.get('id', '?')}` ({e.get('date', '?')}) — {e.get('subject', '?')}")

lines.append("")
lines.append("## Drive tax files")
for f in r["drive_tax_files"][:30]:
    lines.append(f"- {f}")

lines.append("")
lines.append("## Calendar tax events ({} total)".format(len(r["calendar_events"])))
for e in r["calendar_events"][:30]:
    lines.append(f"- {e['start']} — {e['summary']}")

print("\n".join(lines))
PY

echo "[fetch_tax_season_history] wrote ${JSON_OUT}" >&2
echo "[fetch_tax_season_history] wrote ${MD_OUT}" >&2
