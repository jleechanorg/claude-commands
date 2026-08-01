# 2026-07-20 Sariel compound-notation dice audit FAIL

Bucket: **C (data-class regression)** with a coupled secondary **B3 (audit-script
parser too strict)** — both visible from the same evidence bundle.

## Headline

`Daily Dice Audit FAILED — 2026-07-20 — 0/2 passed`

- `[FAIL] Sariel Valyria (EROaUnSbmDhqBedTbJMg)`
- `[FAIL] Sariel Valyria (forgot control iron bank) (Cg2m2TkGFFez7XBynEah)`

Evidence: `gs://wa-test-evidence/daily-dice-audit/2026-07-20/`
Execution: `wa-daily-dice-audit-bvzll`

The thread that surfaced this (`C0AH3RY3DK6/p1784548844.491489`) was posted by
`mcp_agent_mail` (U0A4G7LDJ4R) at 12:00:45 UTC and sat unanswered for ~9h
because the **auto-reply mechanism that should have caught it is an orphaned
plist template** (see `dropped-messages` → "orphaned plist" section + bead
`rev-fvv22`). That's the harness-fix-side lesson; the audit-side lesson is below.

## Proof — fetch recipe (GCS URL-encoding gotcha, verified 2026-07-20)

`storage.googleapis.com/storage/v1/b/wa-test-evidence/o?prefix=…` does
**anonymous 401** without an authed client. Once authed:

```bash
# Auth source: GOOGLE_APPLICATION_CREDENTIALS=$HOME/serviceAccountKey.json + gcloud auth print-access-token
TOKEN=$(gcloud auth print-access-token)
# THE WORKING ENDPOINT (note: download/storage/v1 + URL-encoded %2F for slashes):
curl -sS -H "Authorization: Bearer $TOKEN" \
  "https://storage.googleapis.com/download/storage/v1/b/wa-test-evidence/o/daily-dice-audit%2F2026-07-20%2Fsummary.json?alt=media"
# Gotcha: raw storage/v1/b/<bucket>/o/<name>?alt=media returns 404 because the
# path-segment "/" between "o/" and the file name is interpreted as a literal
# traversal, not a key separator. Use the URL-encoded form above (NOT -
# which returns 9-byte "Not Found" responses that look like a 401 wrap).
```

Three artifacts in the bundle (verified 2,066 / 2,607 / 18,735 bytes):
`scenario_results_checkpoint.json`, `summary.json`, `test_output.log`.

## Two-defect coupling (the actual finding)

When `summary.json` shows BOTH "unparseable dice notation" AND "d20 impossible
values" in the same campaign, that's one upstream bug with two symptom classes,
not two unrelated regressions. Both Sariel campaigns today demonstrated this.

### Defect D1 — `_is_single_die` rejects compound notation

Location: `scripts/audit_dice_rolls.py:548-551` + `dice_pattern` at `:736-739`.

Regex accepts only single-die notation, optionally with `kh/kl` and `+/-`
modifiers. Today's failing notations all emitted from prod Sariel campaigns:

| seq | Notation (truncated)            | Why the regex drops it                       |
|-----|---------------------------------|----------------------------------------------|
| 96  | `1d6+8+2d6+2d8`                 | Two different die sizes in one expression    |
| 296 | `Contested Insight (Tully 25 vs ...)` | Narrative prose wraps the dice value   |
| 486 | `5x 1d20+8`                     | "5x" multiplier prefix, not in the regex     |
| 488 | `5x 1d20+8`                     | (duplicate emission — identical seq #)       |
| 832 | `54d6+2d8+24`                   | Multi-die compound with three different types |

`scripts/daily_dice_audit.py:289-307` (`audit_single_campaign`) treats these as
**integrity failures** ("real_failures"). Today's `summary.json` shows 5 of
those "unparseable" warnings per campaign.

### Defect D2 — `_bucket_d20_from_structured` uses the modified total as face

Location: `scripts/audit_dice_rolls.py:613-619` (d20 path) and `:1283-1299`
(chi-square path for d4/d6/d8).

Both code paths are written defensively: "prefer `individual_rolls[]` over
`result`". But the FALLBACK when `individual_rolls[]` is missing uses
`result` (the modified total) as the face value. Since Sariel rolls look
like:

```
1d20+34 = 53   (Initiate Final Apotheosis Phase 4)   → "face" 53 → impossible
1d20+12 = 23   (N/A)                                 → "face" 23 → impossible
1d20+9  = 11   (Persuasion Bran)                     → "face" 11 → valid
```

…the d20 impossible-value buckets get filled with values like 25, 27, 37, 44,
51, 53 — all real modifier-totals from `dice_audit_events`.

The d4 impossible=6 + d6 impossible=[9, 13, 216] is the same defect:

- d4=6 impossible (d4 max=4) — a d6/d8 modifier-bearing total in the d4 bucket
- d6=[9, 13] impossible (d6 max=6) — modifier-bearing totals landing in d6
- d6=216 impossible — almost certainly a healing/spell AoE total `(e.g. 6d6+8+2d6+2d8 sum)`

**THE PROOF that D1 and D2 are the same upstream cause**, not two unrelated
defects: **both Sariel campaigns (EROaUnSbmDhqBedTbJMg and
Cg2m2TkGFFez7XBynEah) emit the EXACT SAME SEQUENCE NUMBERS** for the
unparseable rows (96, 296, 486, 488). Different campaign IDs, same
`dice_audit_events` rows → same prompt contract → same LLM output. The fix
should be one PR, not three.

## What a fix PR needs to do

1. **Extend `_is_single_die` + `dice_pattern`** to accept compound notation:
   - `1d6+8+2d6+2d8` → emit per-die buckets `[d6, d6, d6, d8, d8]` face values
     (with the `+8` modifier applied to the single d6 only — preserve
     order-sensitive modifier semantics).
   - `5x 1d20+8` → strip the `5x` prefix (mentions attack count, not dice
     count), parse as `1d20+8` once for the d20 face bucket.
   - `54d6+2d8+24` → emit `[d6]×54 + [d8]×2` face buckets; the trailing
     `+24` is a flat modifier, split evenly across dice OR drop from face
     analysis.
2. **In `_bucket_d20_from_structured`, when `individual_rolls[]` is missing on
   a modifier-bearing d20**, **skip the roll** with a `dropped_modifier_total`
   counter instead of using the modified total as the face value. Same fix
   for the chi-square path at `:1283-1299`.
3. **Demote unparseable-notation to soft warning**, not "Integrity Failure".
   The audit currently flags every compound notation as a blocker, but the
   audit's job is to surface dice-roll INTEGRITY, not to be a parse oracle
   for the LLM's notation choices. Sample-truncate the list (e.g. show first
   5) so a single noisy campaign doesn't bury the daily summary.

## Companion lessons

- **Companion harness fix:** `~/.hermes/launchd/ai.hermes.thread-reply-nudge.plist.template`
  is orphaned — `install-hermes-scheduled-jobs.sh` doesn't enumerate it,
  no `launchctl list` row exists. Patch BOTH the install script AND
  `launchctl load` in the same turn so the plist survives future deploys.
  Bead `rev-fvv22`.
- **Companion GCS-evidence recipe:** use `%2F` URL-encoding for slashes in
  object names; the raw `/o/<name>?alt=media` endpoint returns 9-byte "Not
  Found" responses that look like 401s.
- **No related open PR could be found** — `gh` GraphQL was rate-limited;
  `https://api.github.com/search/issues?q=repo:$GITHUB_REPOSITORY+dice+audit`
  returned 403 + 422 across all phrasings tried. Re-verify before opening a
  new PR.

## Cross-campaign fingerprint check

If a future FAIL shows two campaigns with the **same sequence numbers** in
the unparseable/Integrity-Failure rows, that's the litmus test for "same
upstream cause" — the LLM's dice contract is shared across prompts, so two
campaigns diverge only via state, not via the dice-emission contract. Treat
such co-occurrences as one fix surface even if the integration test only
covers one campaign.

## Source transcripts

- Slack thread: `C0AH3RY3DK6/p1784548844.491489`
- Reddit sibling (cross-check, not the same fix): thread
  `C0AH3RY3DK6/p1784548844.491489`
- MCP Agent Mail alert (bot row): `1784548845.892639`
- Today's thread reply (Hermes, `U0AEZC7RX1Q`): `1784582619.003179`
- Status cron created: `0e601695041e` (one-time, 20m)
- Bead: `rev-fvv22` (orphaned plist)
