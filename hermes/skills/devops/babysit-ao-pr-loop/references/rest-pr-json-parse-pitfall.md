# REST PR JSON parse pitfall (added v1.6.0, 2026-07-13)

**Symptom:** A Phase 0 / Phase 1 REST fallback (per `references/graphql-rate-limit-rest-fallback.md`) of the form:

```bash
curl -fsS -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/pulls/$PR" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['state'])"
```

crashes with:

```
json.decoder.JSONDecodeError: Invalid control character at: line N column M (char K)
```

**Root cause:** The `/pulls/{N}` REST response includes the `body` field with the full PR description. When that body is multi-paragraph Markdown with hard line breaks (very common — contributors paste prose unchanged), GitHub's response serializer includes the line breaks as **literal `\n` characters inside the JSON string**. Python's `json.loads` rejects raw control chars U+0000–U+001F inside strings (per RFC 7159 strict mode). The document *would* parse if those bytes were `\n`-escaped, but the GitHub serializer does not pre-escape them.

This bites every cron / babysit that does REST fallback instead of `gh pr view`. Confirmed in cron thread `C0BDEAJH8PK/p1783980995.978159` (PR #779 state check, 2026-07-13): the babysit's `python3 -c "json.load(open('/tmp/pr779.json'))"` crashed 3 times in a row; the eventual fix was `re.sub` to escape control chars before parsing.

`jq` (libjq ≥1.6) is tolerant of raw control chars but you cannot rely on it being installed in every cron environment — stick to Python.

## Fix (drop-in helper)

A tolerant parser with the same shape as `json.loads` lives at `scripts/gh_pr_json.py` (created alongside this skill). Use it instead of `json.load` whenever the input is a raw GitHub REST response:

```python
import sys
sys.path.insert(0, os.path.expanduser("~/.hermes/skills/devops/babysit-ao-pr-loop/scripts"))
from gh_pr_json import gh_safe_json_loads
data = gh_safe_json_loads(open("/tmp/pr779.json").read())
print(data["state"])  # 'open'
```

Or inline (no helper) — `python3 -c` form for cron prompts:

```bash
python3 -c "import re,sys,json; \
  raw=sys.stdin.read(); \
  print(json.loads(re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', lambda m: repr(m.group())[1:-1].replace('\"', ''), raw))['state'])"
```

Both pass `state`, `mergeable`, `additions`, `deletions`, `changed_files`, `merged`, `merged_at`, `title`, `head.sha` fields reliably.

## One-liner status helper

`scripts/gh_pr_json.py` ships with a `__main__` block so you can run it as:

```bash
python3 ~/.hermes/skills/devops/babysit-ao-pr-loop/scripts/gh_pr_json.py \
  "$(gh auth token)" jleechanorg/jleechanclaw 779
```

Output:

```
PR #779 [jleechanorg/jleechanclaw] state=open mergeable=True additions=1153 deletions=0 files=5 merged=False
```

Drop this into any cron prompt for a Phase 0 status check that needs to survive both GraphQL rate-limit fallback AND raw-body parse failures.

## Combined rate-limit + parse failure recipe

When BOTH apply (GraphQL rate-limited AND `json.load` rejects body):

```bash
TOKEN=$(gh auth token 2>/dev/null)
curl -fsS -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/pulls/$PR" \
  | python3 ~/.hermes/skills/devops/babysit-ao-pr-loop/scripts/gh_pr_json.py --state-only
```

The script's `--state-only` flag short-circuits to a single `state` field output suitable for a Phase 0 terminal-state check. Use it in the cron prompt template:

```
Phase 0 step 1 (terminal-state probe):
  STATE=$(curl -fsS -H "Authorization: token $(gh auth token)" \
    "https://api.github.com/repos/${OWNER}/${REPO}/pulls/${PR}" \
    | python3 ~/.hermes/skills/devops/babysit-ao-pr-loop/scripts/gh_pr_json.py --state-only)
  if [ "$STATE" = "closed" ]; then ...  # MERGED is detected separately via `merged:true`
```

For full state including merge status, use `--summary` for the one-line tabular output above.

## Companion references

- `references/graphql-rate-limit-rest-fallback.md` — the REST fallback trigger (Phase 0 step 1 pitfall). This reference is its parse-failure companion.
- `finish-the-job` §"Slack reply format" — when posting the post-Phase-0 terminal closeout, keep the proof to ≤3 lines.
