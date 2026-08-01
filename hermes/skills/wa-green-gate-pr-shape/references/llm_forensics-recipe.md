# BigQuery `llm_forensics` recipe — god-mode directive forensics

Used by your-project.com PR investigations where the reported bug is
"LLM ignored the formula / directive was truncated" and the PR claims to fix
it by capping or restructuring the directives block.

## When to use this

- User says "LLM ignored directive X", "god-mode commands were truncated",
  "stop trimming player commands", or pastes a scene number from a campaign.
- A PR on `$GITHUB_REPOSITORY` proposes a directive count cap,
  truncation toggle, or "newest N" filter.
- You need raw evidence to decide whether the PR's mechanism matches the bug.

## One-shot query

```bash
# 1. Find the relevant campaign id from the scene URL or user message
CAMPAIGN_ID="wc2BBcSgOljiU3vJ160A"   # example; replace per session

# 2. Pull every gemini_provider.stream + GodModeAgent row for this campaign
#    with full request_json so you can search the actual prompt body.
bq query --use_legacy_sql=false --format=csv --max_rows=2000 "
SELECT ingested_at, agent, event_type, model, prompt_tokens,
       LENGTH(request_json) AS request_bytes,
       LENGTH(response_text) AS response_bytes,
       request_json, response_text, user_id, session_id
FROM \`worldarchitecture-ai.llm_forensics.llm_payloads\`
WHERE campaign_id = '${CAMPAIGN_ID}'
  AND agent IN ('gemini_provider.stream','GodModeAgent')
ORDER BY ingested_at DESC
" > /tmp/${CAMPAIGN_ID}.csv
```

If `request_json` column doesn't exist on this dataset, try:
`prompt_json`, `payload_json`, `raw_request`, `messages`, `body`.
Check schema first:
```bash
bq show --format=pretty worldarchitecture-ai:llm_forensics.llm_payloads
```

## Three quick counts that defeat a "count cap will fix it" PR

```python
import csv, sys, re
csv.field_size_limit(sys.maxsize)
rows = list(csv.DictReader(open('/tmp/${CAMPAIGN_ID}.csv', newline='')))
stream = [r for r in rows if r['agent'] == 'gemini_provider.stream']
print('stream rows:', len(stream))
print('prompt_tokens min/median/p90/max:',
      min(int(r['prompt_tokens']) for r in stream),
      sorted(int(r['prompt_tokens']) for r in stream)[len(stream)//2],
      sorted(int(r['prompt_tokens']) for r in stream)[int(len(stream)*.9)],
      max(int(r['prompt_tokens']) for r in stream))
print('over_200k:', sum(int(r['prompt_tokens']) > 200000 for r in stream))
```

Then scan each `request_json` for the directive marker block. The standard
header in your-project.com prompts is:
```
Active God Mode Directives (Newest First)
The following rules were set by the player and MUST be followed.
```

```python
directive_counts = []
for r in stream:
    req = r['request_json']
    p = req.find('Active God Mode Directives')
    if p < 0: continue
    # The block ends at the next ## heading or end-of-prompt.
    end_candidates = [x for x in (req.find('## ', p+10), req.find('### ', p+10)) if x > p]
    end = min(end_candidates) if end_candidates else len(req)
    block = req[p:end]
    n = len(re.findall(r'(?:^|\\n|\n)\s*\d+\.\s+', block))
    directive_counts.append((r['ingested_at'], len(req), n))
print('rows with active directives block:', len(directive_counts))
print('directive counts seen:',
      sorted({x[2] for x in directive_counts}))
```

**The PR-shape smoking gun:** if the renderer is already emitting 250+
directives but the PR proposes a cap of 50, the cap is the wrong mechanism.
The renderer isn't the bottleneck — something else (size? context
window? token-budget slicer?) is.

## Detecting directive-contradiction vs truncation

The bug "LLM ignored the formula" is almost never caused by truncation in
this codebase. It's caused by **15+ duplicated/conflicting rules** stacked
in the active block, with the LLM picking whichever appears latest.

```python
# Count rules touching gear/equipment/level math inside the active block
for r in stream:
    req = r['request_json']
    p = req.find('Active God Mode Directives')
    if p < 0: continue
    end = min([x for x in (req.find('## ', p+10), req.find('### ', p+10)) if x > p] or [len(req)])
    block = req[p:end]
    lines = re.findall(r'(?:^|\\n|\n)\s*(\d+)\.\s+(.*?)(?=(?:\\n|\n)\s*\d+\.\s+|$)',
                       block, re.S)
    gear_rules = [(int(n), t[:200])
                  for n, t in lines
                  if any(k in t.lower() for k in
                         ['gear', 'equipment', 'original divine',
                          'level / 10', 'formula'])]
    if gear_rules:
        print(r['ingested_at'], 'n_rules=', len(lines), 'gear_rules=', len(gear_rules))
        for n, t in gear_rules[:10]:
            print(' ', n, t)
```

If you see ~10+ rules in the active block that all claim to define the
same formula but disagree on the inputs (Original Level vs Current Level,
45 vs 49 vs 89 vs 95 for Bane, etc.), the LLM isn't "ignoring" the rule —
the renderer is shipping conflicting rules. The LLM picks one and that
choice looks like ignoring from the player's perspective.

## Late-evidence check (the "rule was at 97% of prompt" pattern)

When the player reports "the LLM ignored this rule that I just set", the
rule usually *is* present in the prompt — just buried near the end. Check
the *position* of the relevant rule vs the rendered position:

```python
# How far into the prompt does the relevant rule appear?
for needle in ['equipment_bonus', 'Original Divine Level', 'Level / 10']:
    pcts = []
    for r in stream:
        req = r['request_json']
        i = req.lower().find(needle.lower())
        if i >= 0:
            pcts.append(i / len(req) * 100)
    print(needle, 'rows=', len(pcts),
          'min=', min(pcts) if pcts else None,
          'median=', sorted(pcts)[len(pcts)//2] if pcts else None,
          'max=', max(pcts) if pcts else None,
          'late>85%=', sum(p > 85 for p in pcts))
```

A median position under 60% means the rule is mid-prompt and the LLM
should see it. A median over 85% means the rule is being pushed near the
end (often after the conversation history) and competing with attention
budget.

## Verdict template (paste into PR comment / bvr issue)

```
BQ evidence on campaign ${CAMPAIGN_ID} over ${N} streaming calls:
- prompt_tokens min/median/p90/max: <min>/<med>/<p90>/<max>
- rows exceeding 200k tokens: <N> / <total>
- rows with Active God Mode Directives block: <N>
- directive counts actually rendered: <sorted_set>
- rules inside the block that touch <topic>: <N>
- contradictory rule pairs detected: <N>

Conclusion: <mechanism in PR X> does NOT match the actual bug
because <reason rooted in numbers above>.
```

## Common false-positive patterns

- PR proposes "cap to 50 newest" but renderer is already shipping 293+ →
  cap will manufacture the bug, not fix it.
- PR proposes "include full history" but prompt already exceeds 350k bytes
  → Gemini is already truncating upstream of the renderer. Look at
  `gemini_provider.stream` `request_bytes` distribution, not the directive
  count.
- PR proposes "deduplicate directives" but the active block uses
  `directives.drop` / `directives.add` semantics already — count duplicates
  with `re.findall` to confirm there are real duplicates before recommending
  the fix.

## Provenance

This recipe was extracted from the 2026-07-24 PR #8531 ("cap god-mode
directives at 50 newest entries") investigation. PR #8531 turned out to
be the wrong mechanism: the renderer was emitting 293-299 directives, not
50, and the actual bug was 15+ contradictory gear-formula rules stacked
in the active block, not truncation. PR #8532 was a separate PR
hardcoding one campaign's 5-NPC gear list and was correctly rejected as
campaign-specific. See `references/pr-8531-directive-cap-recipe.md` for
the full investigation log.