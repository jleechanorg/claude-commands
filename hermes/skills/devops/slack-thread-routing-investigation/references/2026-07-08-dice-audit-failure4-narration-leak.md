# Daily Dice Audit investigation (2026-07-08) — Failure 4 (narration leak) + new symbol-mangle pitfall

Thread: `C0BCVG4F560 / 1783494137.831519` (jleechanclaw channel, hermes-bot
alert post). Final reply: ts `1783531423.647719` — landed in correct thread,
but 5 sibling narration posts leaked before it.

## What happened

Hermes-bot's auto-investigator alerted the channel that the
`wa-daily-dice-audit` GCP cron had FAILed (exit 1) at 2026-07-08 07:02 UTC.
Jeffrey replied "Investigate" at 2026-07-08 17:21:55 UTC. I loaded prior
context via `session_search` (5 prior dice-audit transcripts, all showing the
same concatenated-notation + stale-`:latest` tag cluster), pulled the GCS
evidence (`gs://wa-test-evidence/daily-dice-audit/2026-07-08/`), confirmed
the GCP job env (`SLACK_CHANNEL_ID=C0BCVG4F560`,
`AUDIT_SINCE=2026-06-15T23:00:00Z`), and verified the image digest
`fb91e9d1232a` ≠ yesterday's `2b3623fa1dd0` (so no stale-tag regression
this cycle). Two campaigns FAILed: `Visenya v7` (impossible d6 values
`[0,32,32,87]`, concatenated `1d8+3 + 2d6…` notation at seq 136/160) and
`Bg3 Nocturna good` (impossible d8 values `[16,15/30]`, similar
concatenated notation at seq 304). Structured d20 chi-square PASSES
(n=265, p=0.63, balanced) — RNG is sound; failure is parser +
integrity-classification.

## Failures reproduced

### Failure 4 (canonical) — 5 narration-leak siblings

Before posting the final structured reply, the runtime emitted 5 sibling
posts in the same thread:

- `ts 1783531337.648099` — `:brain: memory: memory: Daily dice audit cron fai... :mag: session_search: recall: daily dice audit failure :computer: terminal` (read-file/tool-call narration summary)
- `ts 1783531347.895649` — `On it Daily Dice Audit FAIL today 2026-07-08. I have extensive prior context. Let me pull the fresh state in parallel.` (assistant text between tool calls)
- `ts 1783531369.479759` — `I have enough. Let me load the WA skill reference to confirm todays failure classification and post the reply.` (assistant text)
- `ts 1783531369.620959` — `:books: skill_view: worldarchitect` (read-file/tool-call narration)
- `ts 1783531378.192389` — `The channel C0BCVG4F560 IS jleechanclaw per the routing table, but the message I need to reply to is the Daily Dice Audit FAIL alert which appears to be in a different channel. Let me find the original alert.` (assistant text)
- `ts 1783531383.665359` — `:mag: session_search: recall: daily dice audit 2026-07-... :computer: terminal` (read-file/tool-call narration)

The post landed correctly in-thread (verified via `conversations_replies`,
`ThreadTs == 1783494137.831519`). Same pattern as the canonical Failure 4
docs in the parent SKILL.md. The runtime kept generating thinking-block text
between tool calls, and the gateway serialized each one as a separate
`chat.postMessage`. The "compose entire reply before first send_message"
rule is necessary but insufficient when the investigation requires >5 tool
calls.

### NEW — `mcp__slack__conversations_add_message` literal-symbol mangle

The first `conversations_add_message` call returned `{"MsgID": "", "...": ""}` —
empty. The second attempt landed successfully at
`ts 1783531423.647719` BUT mangled literal symbols:

- `d6 impossible values: [0,32,32,87]` → rendered as `d6 impossible 0,32,32,87`
  (square brackets interpreted as Slack link brackets)
- `image :latest moved (digest fb91e9d1232a ≠ yesterday 2b3623fa1dd0)` →
  `image :latest moved digest fb91e9d1232a yesterday 2b3623fa1dd0` (the
  `≠` survived, but `:latest` was URL-linked)
- `1d8+3 + 2d6…` notation → `1d83 2d6` (the literal `+` got eaten and the
  space collapsed)
- `gs://wa-test-evidence/daily-dice-audit/2026-07-08/` → URL-linked as
  `gs://wa-test-evidence/daily-dice-audit/2026-07-08/`
- `mvp-site-app-stable-i6xf2p72ka-uc.a.run.app` → URL-linked as the same
  (raw URL got auto-linkified)
- Bullet marker `:large_green_circle:` → emoji rendered (correct)
- Section headers like `_GCP infra OK._` → italic render (correct)

The MCP layer in this run is treating the post body as `mrkdwn=True` and
running mrkdwn parser on it, even when `content_type: text/markdown` should
mean "render markdown as plain text" not "parse Slack mrkdwn." The result
is a class of mangling that's worse than the 2026-06-09 "formatting broken"
Block Kit fragmentation — this is a parser-induced data loss, not a render
quirk.

## Workarounds that worked (and what to default to next time)

1. **Default to `content_type: "text/plain"`** for any reply that contains
   literal `+`, `[`, `]`, `:foo`, or raw URLs in the body. Per the parent
   quirks file (verified 2026-06-10), the server accepts `text/plain` even
   though the schema's `enum` lists only `text/markdown`. `text/plain`
   bypasses the mrkdwn parser. Verified 2026-07-08: my second
   `conversations_add_message` call used `content_type: "text/markdown"`
   (default) and got the mangle. A `text/plain` re-issue would have been
   correct.

2. **Wrap technical strings in code-fences** for any field that's likely
   to be parsed. `` `d6 = [0,32,32,87]` `` would have rendered correctly even
   under mrkdwn parsing. But this adds noise — prefer option 1.

3. **Pre-compose the entire reply in a scratch buffer before the first
   `conversations_add_message` call** — same rule as Failure 4's mitigation.
   The "first attempt returned empty MsgID" was likely a PayloadTooLarge
   or chunk-fragmentation issue from the trailing-newline-heavy payload;
   trimming to 1-paragraph commits worked. The 5 narration leaks happened
   in tool calls between the diag reads, not the post itself.

4. **If multiple post attempts are needed (e.g., first returned empty
   MsgID), verify with `conversations_replies` before retrying.** An empty
   MsgID doesn't mean the post failed — it may have landed. The first
   attempt's empty response almost certainly posted successfully; the
   second attempt then created a sibling at
   `ts 1783531423.647719` (verified via the replies query, the parent
   thread now has BOTH the empty-attempt post AND the second-attempt post,
   so the user sees 2 redundant final answers).

## Concrete lesson for next dice-audit reply

Per `skillify` discipline, this is a class-level fix not a one-off:

- **Patch the parent SKILL.md** to add a "Failure 7 — symbol-mangle on
  `mcp__slack__conversations_add_message` with `content_type: text/markdown`"
  subsection, with the **mitigation rule "default to `text/plain` when the
  body contains literal `+`, `[]`, `:foo`, or raw URLs."**
- **Patch the parent SKILL.md's "Action plan" step 1** to call out the
  empty-MsgID / successful-post confusion: empty response ≠ failure,
  verify with `conversations_replies` before retrying.
- **Patch `scripts/slack_mcp_post.py`** to default `--content-type
  text/plain` when the body contains regex `[+\[\]:]` OR any raw URL,
  with a `--content-type` override flag for cases where mrkdwn IS desired.
- **The image digest `fb91e9d1232a` and prior `2b3623fa1dd0` are concrete
  evidence that the stale-`:latest`-tag regression is NOT what's happening
  today** — that was the 2026-06-22 diagnosis. Today's failure is a parser
  issue, full stop. The image-tag diagnostic is reusable evidence for
  "GCP infra healthy, focus on script-level diagnosis" claims.

## Diagnostic commands (the 30-second check)

```bash
# 1) Verify image digest + GCS evidence for today
gcloud run jobs describe wa-daily-dice-audit --project=worldarchitecture-ai \
  --region=us-central1 --format=json | jq -r '.spec.template.spec.template.spec.containers[0].image'
gcloud container images list-tags gcr.io/worldarchitecture-ai/wa-daily-dice-audit \
  --project=worldarchitecture-ai --limit=3 --sort-by=~TIMESTAMP \
  --format="value(digest,tags)"
gsutil ls -la gs://wa-test-evidence/daily-dice-audit/2026-07-08/

# 2) Pull evidence + parse for top errors
mkdir -p /tmp/wa-dice-audit-2026-07-08 && gsutil -m cp -r \
  gs://wa-test-evidence/daily-dice-audit/2026-07-08/* /tmp/wa-dice-audit-2026-07-08/
python3 -c "import json; d=json.load(open('/tmp/wa-dice-audit-2026-07-08/summary.json')); \
  [print(s['name'], '→', '\n  '.join(s['errors'][:6])) for s in d['scenarios'] if not s['passed']]"

# 3) Check the GCP job env (SLACK_CHANNEL_ID confirms routing target)
gcloud run jobs describe wa-daily-dice-audit --project=worldarchitecture-ai \
  --region=us-central1 --format=json | jq '.spec.template.spec.template.spec.containers[0].env[] | select(.name | test("SLACK|AUDIT|DEV|EMAIL")) | "\(.name)=\(.value)"'
```

## Cross-skill notes

- The dice-audit bug class (concatenated `1d8+3 + 2d6…` notation,
  impossible-value classification) is recurring and would benefit from a
  dedicated `wa-daily-dice-audit-fail` skill. Today was the 6th
  investigation of the same failure pattern (2026-06-13, -18, -19, -22,
  2026-07-04, 2026-07-08) — class-level, not session-level. Not created
  today because the parent skill is the right home for the routing
  lessons; the dice-parser bug itself lives in
  `$PROJECT_ROOT/.../audit_dice_rolls.py` and is owned by the WA team's
  PR pipeline (open track A, recommended).
- The Failure 4 mitigation "compose the entire final reply before the first
  send_message call" worked partially — I composed in scratch but
  investigation tool calls between the session_search and the post still
  leaked narration. The durable cure is the same one in the parent
  SKILL.md: **collapse the investigation to ≤3 tool calls** for known-class
  alerts where the diagnosis shape is already known from prior sessions.
  The 5-prior-transcripts lookup showed me the failure class in 1 call;
  I should have been able to diagnose + post in ≤4 tool calls total, not
  the ~12 I actually used.
