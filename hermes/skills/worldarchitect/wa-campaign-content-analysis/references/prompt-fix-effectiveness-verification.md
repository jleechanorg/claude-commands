# Prompt-fix-effectiveness verification — when the LLM still ignores the directive

Session provenance: continuation of `references/pc-silent-prompt-diagnosis.md` thread `C0AH3RY3DK6 / ts 1783986579.477669`.

Jeffrey's verbatim correction: *"Look at my most recent campaign under $USER@gmail.com not sure if dialog working?"* — asked AFTER PR #8382/#8383 (commit `879d4512`, dialog prompt fix) was already on `main` and merged 2026-07-13 22:24 PT.

## What this reference adds on top of the earlier diagnosis

The earlier reference (`pc-silent-prompt-diagnosis.md`) covered the **prompt-bug detection** workflow and assumed "add the right prompt → LLM follows → metric improves." That assumption broke in this session. The new bug class is **prompt-fix-shipped-but-LLM-ignores-it**, and it requires a distinct verification recipe.

## The two-stage bug class

1. **Original (PC-silent)** — diagnosed 2026-07-13. Found 67-75% NPC-monologue dominance in HeavyDialogAgent/DialogAgent across 10 long campaigns. Anti-pattern entries #9-#11 added to `dialog_system_instruction.md`. PR #8382 / #8383 / commit `879d4512` landed on `main`.

2. **Re-diagnosed (NPC-silent, not PC-silent)** — 2026-07-14. The user's actual complaint wasn't that the PC wasn't speaking; it was that **NPCs weren't speaking**. The original diagnosis was an inversion of the user's actual bug. The earlier `%pc_silent=67.8%` numbers were real, but they weren't the user's bug — they were a *symptom* of the same root cause (prompt bias toward NPC internal monologue over spoken dialog).

**Key takeaway**: when a per-agent metric looks anomalous, ask "which axis is the user complaining about" before writing the fix. PC-silent ≠ NPC-silent in the user's eyes even though they're inversely correlated in the data.

## Verification recipe — when the fix has shipped

Trigger: user asks "is the dialog fix working" / "is X actually being applied" / "let me check after deploy" — AFTER a prompt-fix PR has merged. Do NOT assume "PR merged → LLM follows → metric improves."

### Step 1 — Find the merge SHA

```python
import subprocess, re
result = subprocess.run(
    ["git", "-C", "$HOME/your-project.com",
     "log", "--format=%H %ai %s", "-3",
     "--", "$PROJECT_ROOT/prompts/<changed_file>.md"],
    capture_output=True, text=True, timeout=10,
)
print(result.stdout)
```

The user's most-recent campaign will have entries both BEFORE and AFTER this SHA. Find the merge SHA timestamp (commit date in local TZ).

### Step 2 — Locate the user's most-recent campaign

Most-recent ≠ top-level `campaigns` collection (which contains only test fixtures, 0 entries each). The actual user data is in **subcollections**:

```python
db.collection("users").document(uid).collection("campaigns")  # REAL data
# NOT
db.collection("campaigns")  # test fixtures only
```

This is the same trap documented in `wa-prod-data-query` Pitfall #1 — re-verify with `db.collection("campaigns").count().get()` returning 20 or some small number before assuming you've found the right collection.

For "most recent", sort by `last_played` (top-level campaign field), descending. The user's primary campaign is usually the top entry.

### Step 3 — Stream `story` subcollection, split by merge time

```python
import datetime as dt
MERGE_TS = 1784006813  # epoch seconds; or fetch from git log
def norm(v):
    if v is None: return 0
    if isinstance(v, dt.datetime): return v.timestamp()
    if isinstance(v, (int, float)): return float(v)
    if isinstance(v, str):
        try: return dt.datetime.fromisoformat(v.replace("Z","+00:00")).timestamp()
        except: return 0
    return 0

story = db.collection("users").document(uid).collection("campaigns").document(cid).collection("story")
all_docs = list(story.stream())

# Use the mode+agent filter that matches the bug class
# For dialog: actor=gemini AND mode=character (StoryModeAgent narrative, where NPCs should speak)
post = [d for d in all_docs
        if norm((d.to_dict() or {}).get("timestamp")) > MERGE_TS
        and (d.to_dict() or {}).get("actor") == "gemini"
        and (d.to_dict() or {}).get("mode") == "character"]
pre  = [d for d in all_docs
        if norm((d.to_dict() or {}).get("timestamp")) <= MERGE_TS
        and (d.to_dict() or {}).get("actor") == "gemini"
        and (d.to_dict() or {}).get("mode") == "character"]
```

For the same-campaign pre/post comparison, take the **last N of pre** to match the **N of post** (controls for "campaign was warming up" or other time-varying effects).

### Step 4 — Compute the metric that the user's complaint is about

For the dialog bug (NPC-silent), the metric is **NPC-attributed direct quotes per scene**. The classifier from `references/pc-silent-prompt-diagnosis.md` includes `count_dialog()`, but its heuristic (first-person → PC, otherwise → NPC) misclassifies the *italicized action* common in fantasy prose as quoted dialog. Use a tighter regex:

```python
import re

VERB_DIALOG_RE = re.compile(
    r"\b([A-Z][a-zA-Z'\-]+(?:\s+[A-Z][a-zA-Z'\-]+)?)\s+"
    r"(?:said|replied|whispered|bellowed|shouted|asked|muttered|cried|exclaimed|spoke|"
    r"called|answered|gasped|snarled|hissed|warned|declared|insisted|pleaded|sighed|"
    r"laughed|chuckled|noted|interrupted|continued|added|responded|queried|demanded|"
    r"proclaimed|announced|observed|reminded|promised|threatened|confessed|admitted|"
    r"denied|agreed|refused|argued|objected|suggested|proposed|ordered|commanded|"
    r"begged|implored|inquired|wondered|grumbled|complained|roared|yelled|screamed|"
    r"hollered|howled|croaked|drawled|murmured|mumbled|breathed)\b"
    r"[^.!?\n]{0,80}"
    r"\"([^\"]+)\"",  # MUST have a quoted speech following the verb
    flags=re.MULTILINE,
)

def npc_quoted_speech(text, pc_name):
    """Return list of (speaker, quoted_line) tuples attributed to NPCs."""
    out = []
    for m in VERB_DIALOG_RE.finditer(text):
        sn = m.group(1).strip()
        q = m.group(2).strip()
        if not q: continue
        if pc_name and sn.lower() == pc_name.lower():
            continue  # PC
        out.append((sn, q))
    return out

# Compare pre vs post:
#   total npc_attributed_quotes pre vs post
#   avg npc_attributed_quotes per response pre vs post
```

The key tightening: the regex **requires** a `"..."` quoted segment within 80 chars after the speech verb. The earlier `count_dialog()` accepted "Name said that..." (paraphrase), which inflates counts when narration uses speech verbs without actually quoting.

### Step 5 — Read 2-3 sample scenes verbatim to confirm the numbers

The numbers can lie if the classifier misses a pattern. Always dump at least one full pre-merge and one full post-merge scene side-by-side. Look for:
- `*Florent swallows...*` — italicized action disguised as a quote
- `**Name** *thinks: '...'` — think-block masquerading as internal monologue
- `[DIVINE HUD v13.0] ...` — mechanical panels crowding out narrative
- Dialogue buried in HUD blocks: `[SOCIAL SKILL CHALLENGE: ...] Outcome: SURRENDERED`

These are the patterns that produce "lots of quote marks" in the loose classifier but **zero attributed NPC speech** in the tight regex.

### Step 6 — Diagnose why the prompt fix isn't sticking

When pre and post are statistically indistinguishable, the prompt fix landed but the LLM isn't following. Five common causes (ordered by frequency observed in this session):

1. **The fix is in the wrong place** — system instructions get cached and deprioritized across turns. AGENTS.md §"LLM Prompt Caching & Model Deployment Guidelines" mandates dynamic content at prompt TAIL. Anti-pattern entries alone are not enough; the directive must be in a high-salience position (near `Section 7: OUTPUT FORMAT` for example-outputs anchoring).

2. **Structural panels crowd the directive** — `[DIVINE HUD]`, `[SOCIAL SKILL CHALLENGE]`, planning blocks, etc. can dwarf the dialog instruction's effective influence. The LLM follows the structure over the prose.

3. **Model capacity** — Gemini 3 Flash Preview is the small/fast variant. It follows structural patterns better than nuanced negative instructions ("anti-patterns to avoid"). Stronger model or stronger structural framing (dedicated `SECTION 10` with positive example) is needed.

4. **Wrong bug class fixed** — see "The two-stage bug class" above. The fix addressed a different symptom than the user's complaint. Re-run the diagnostic with the correct axis.

5. **Cache miss on prompt update** — Gemini implicit cache uses prefix matching. If the prompt file changed in the *middle* of the prefix instead of the tail, early turns after deploy get full recompute but later turns re-cache the OLD prefix. Force a fresh prefix by adding a `Last Updated: <date>` line near the top.

### Step 7 — Report findings with the pre/post delta

The user's question is "is it working?" Answer with a single number pair:

```
NPC-attributed direct quotes pre-merge:  X
NPC-attributed direct quotes post-merge: Y
```

Followed by the verbatim sample that proves the classifier is right. Then list which of the 5 causes apply to this specific case. Don't speculate about "prompt might not be loaded" — check git, confirm the file on disk matches what's on `main`, and present the cause list as options for the user to choose from.

## Fix recipes (when the cause is confirmed)

### Cause 1 — Wrong place

Move the directive from anti-pattern list to a dedicated high-salience section. Example: promote from item #9 in the `## ANTI-PATTERNS` list to a new `## SECTION 10: NPC SPEECH REQUIREMENTS` placed near `SECTION 7: OUTPUT FORMAT`. The structural-position bump + dedicated heading increases salience more than any wording change.

### Cause 2 — Structural panels crowd

Look for a way to *embed* the directive inside the output template. For WA: the `[SOCIAL SKILL CHALLENGE]` template forces a structured response. Adding a `direct_quotes` field there is a structural reminder that the LLM fills with actual speech.

### Cause 3 — Model capacity

Route dialog-heavy scenes (`mode=character` with NPC count ≥ 2 in the scene header) to a larger model (Gemini 3 Pro). The structural anchor is the routing rule, not the prompt.

### Cause 4 — Wrong bug class

Re-run the diagnostic on the user's actual axis. Don't trust your earlier diagnosis — read the user's words, find the verb, and instrument the metric that maps to it.

### Cause 5 — Cache miss

Append a `Last Updated: <date>` line at the top of the prompt file. Gemini will recompute the cached prefix once per deployment, so the new directive takes effect on the next turn after deploy rather than after the cache TTL expires.

## Anti-patterns in the verification workflow

- ❌ Trusting "PR merged" as proof the fix works. Merged ≠ applied at the model level.
- ❌ Using a loose classifier (`count_dialog()`) that overcounts italicized action as NPC speech. The numbers will look healthy while the bug persists.
- ❌ Sampling one or two post-merge scenes. The directive may fire 10% of the time and miss the other 90%; need ≥30 scenes for a stable rate.
- ❌ Skipping the pre/post comparison. The pre-merge baseline is what tells you whether the change made things better, worse, or unchanged.
- ❌ Speculating about why without naming one of the 5 causes. Each cause has a different fix; guessing wastes a round-trip.

## Artifacts (durable)

- Wiki source page (this round): `~/llm_wiki/wiki/sources/dialog-fix-effectiveness-2026-07-14.md`
- Pre/post comparison script: `scripts/post_merge_dialog_audit.py` (extends `per_scene_dialog_audit.py`)
- Bead for follow-up: `br create "Promote NPC-direct-quote directive to dedicated SECTION 10"` (the recommended Cause 1 fix from this session)