# Find the new campaign ID after `copy_campaign.py` — recipe

## Why this exists

`copy_campaign.py` writes the new campaign to Firestore but its stdout output does NOT reliably print the new campaign ID. As of 2026-07-08 the only reliable signal is the `📋 Campaign ID: <id>` footer line — but earlier copies (≤2026-07-04) returned only the `dest_uid` JSON. After a copy, the next step (download_campaign, export, link-building, post-state capture) needs the new campaign ID.

## The 4-step recipe (worked example: #8283, copy returned only `dest_uid`)

```bash
# 1. Run the copy — it returns JSON {dest_uid, dest_email} and the new ID footer
$PY scripts/copy_campaign.py \
  --find-by-id <SOURCE_CAMPAIGN_ID> \
  --dest-email <your-email@gmail.com>

# 2. Use Firestore REST API directly (NOT find-by-title — that searches all 2900+ campaigns and times out)
TOKEN=$(gcloud auth print-access-token)
PROJECT=worldarchitecture-ai        # NOT worldarchitect-ai — confirmed from serviceAccountKey.json
DEST_UID=<dest_uid from step 1>     # resolved by the copy script

# 3. Paginate through dest campaigns and filter by title client-side
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://firestore.googleapis.com/v1/projects/$PROJECT/databases/(default)/documents/users/$DEST_UID/campaigns" \
  | jq -r '.documents[] | select(.fields.title.stringValue | test("Visenya v7 \\(copy\\)")) | {id: (.name | split("/") | .[-1]), title: .fields.title.stringValue, created: .fields.created_at.timestampValue}'
```

For large dest accounts (jleechantest has 2900+ campaigns), iterate all `nextPageToken` pages. The local `(copy)` title suffix is added by default — match exactly `Visenya v7 (copy)` (regex escape the parens).

## The wrong ways (don't do these)

- **`scripts/copy_campaign.py --find-by-title "Visenya v7 (copy)" --source-email <your-email@gmail.com>`** — searches all users, takes 60s+ on large orgs, may exceed the 60s subprocess timeout. Not paginated through the script.
- **`structuredQuery` with `orderBy created_at DESC` against the title filter** — requires a composite index `(title, created_at)` that may not exist (`FAILED_PRECONDITION: The query requires an index`). The error is unhelpful. Don't go down this path.
- **Re-running the copy to "see the ID"** — creates a SECOND copy, polluting the test subject set. Use a `--dry-run` first if you must re-invoke.

## Why `--dest-email` works in 1 step but `--dest-uid` doesn't

`--dest-email <your-email@gmail.com>` triggers an **early-exit email→UID lookup** in `copy_campaign.py` (the script exits with `{dest_uid, dest_email}` JSON BEFORE performing the actual copy). The real copy then runs in a second invocation. The first invocation is your way to get `dest_uid` without doing a copy.

## Why finding the new campaign by ID beats finding by title

When you already have a guess at the new ID (e.g. the script footer printed it), use the direct read:

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://firestore.googleapis.com/v1/projects/$PROJECT/databases/(default)/documents/users/$DEST_UID/campaigns/<GUESSED_ID>" | jq -r '.fields.title.stringValue'
```

This is one HTTP call vs paginating 100-at-a-time through 2900 docs to match a title.

## Verified worked example

- 2026-07-08, issue #8283, copy of `xK3fp5XrV24oarIINTF7` (Visenya v7) → jleechantest
- Footer printed: `🔗 Campaign ID: OMsOa7hkEhWO9GtVmfwM`
- Pre-state pre-state captured 239 KB before any app touch
- See `evidence/pr-8283/pre_state.json` and `VERDICT.md` in PR #8284

## When this doesn't apply

- If `copy_campaign.py` is patched to print the new ID in JSON stdout (proposed but not landed as of 2026-07-08), skip this recipe
- If the dest account has <100 campaigns total, the paginated curl above completes in <1s and is still the safe default
