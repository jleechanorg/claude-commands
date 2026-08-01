# Campaign document field-naming — verified 2026-07-15

Source: 1,087 campaign documents across `users/{uid}/campaigns` in the `worldarchitecture-ai` Firestore project, $USER's account.

## The trap

The campaign (top-level) document has **two competing name fields**, only one of which is populated for any given campaign:

| Field | Population in scanned corpus | Source |
|---|---|---|
| `title` | populated for ~all real-user campaigns | newer schema; standard creation flow |
| `name` | populated only for ~no real-user campaigns | older / programmatic / test-fixture schema |

Verified numbers from the 2026-07-15 scan:
- Query: `where("title", "==", "Visenya v2").get()` → **1 hit** (the real campaign)
- Query: `where("name", "==", "Visenya v2").get()` → **0 hits** (the schema returns zero results because the field is absent)

This is consistent across both Visenya and other multi-version chains (Aizen v2/v3, Saita v3/v3.1, etc.). Whoever updated the schema moved from `name` to `title` but kept the old field as a vestigial option that no real-user campaign uses.

## The fix (mandatory fallback)

Always read both fields. **Never** trust a literal `.where("name", "==", <x>)` query against the real-user Firestore.

```python
def get_campaign_title(cd: dict) -> str:
    """Robust title extractor — handles both schema versions."""
    return (cd.get("title") or cd.get("name") or "").strip()
```

Apply the same `(cd.get("title") or cd.get("name") or "")` pattern anywhere downstream:

```python
# List view
for c in camps:
    cd = c.to_dict() or {}
    name = cd.get("title") or cd.get("name") or "Untitled"
    print(name, "|", c.id)

# Search filter
for c in camps:
    cd = c.to_dict() or {}
    title_l = (cd.get("title") or cd.get("name") or "").lower()
    if "visenya" in title_l:
        ...
```

## Story-subcollection fields are different

The story-doc schema (sub-collection) uses different field names and is well-documented in `references/story-doc-schema.md`. The trap here is **specifically the campaign-level doc**, not the story entries under it.

| Document | Name field | Notes |
|---|---|---|
| Campaign doc (`users/{uid}/campaigns/{cid}`) | `title` (preferred) or `name` (vestigial) | this file |
| Game state subdoc (`...game_states/current_state`) | no top-level "title"; the PC's name lives at `player_character_data.name` | schema ref |
| Story entry subdoc (`...story/{sid}`) | `text` (scene content), `mode` (user intent), `debug_info.agent_name` (writer agent) | story-doc-schema.md |

## Migration implications (do NOT do this without user approval)

Migrating every campaign doc to standardize on `title` would touch ~1087 docs. Per `your-project.com/AGENTS.md` "File Protocol", a mass-data migration requires:
1. Documented GOAL / MODIFICATION / NECESSITY / INTEGRATION PROOF
2. `/es` evidence with real-server proof
3. PR review with merge approval before apply

If a downstream consumer (an LLM prompt, a UI list, a regression test) is still reading `name`, the safe migration is **dual-write** for one release cycle, not unilateral rename.

The skill's behavior should remain: read both, write to `title`, never assume one without the other.

## How this surfaced

Session 2026-07-15 — user asked "look at the world_reference danerys campaign in meereen". The first scan used the wrong field and returned 0 hits; re-scanning with `title` returned the correct campaign (Visenya v2) immediately. Total wasted tool calls before the fix: ~3 batches.

If you hit a 0-result title scan, your first diagnostic step should be: "am I reading the right field name?"
