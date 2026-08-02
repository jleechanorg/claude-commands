# False visual evidence — PR #8561 transcript (2026-07-24)

This file captures the v2 lesson that the **Pre-Send Gate alone is insufficient**
when the agent claims visual proof: the gate ensures the file is uploaded to
Slack, but it does NOT verify the file's pixel content actually shows what the
agent claims. Computed-style evidence is a separate, weaker signal that needs
its own pre-claim gate.

## Incident timeline

### Round 1 — 2026-07-24 morning (PR #8561 v1 evidence)

User: "Rebase scroll indicator and prove it works with before/after captioned
video per /es https://github.com/$GITHUB_REPOSITORY/pull/8139"

Agent action:
- Started `python3.11 -m mvp_site.main serve` (NOT `local.sh`)
- Captured screenshots via Playwright `is_mobile=False`, viewport 390x844
- `page.evaluate()` returned: `display: 'flex', opacity: '1', hasVisibleClass: True, rect: {x: 57, y: 774, w: 276, h: 56}`
- Agent posted summary: "BEFORE: no chevron. AFTER top: chevron + SCROLL FOR MORE visible."

User caught it (later): "your screenshots are showing lmao arrows visually review it"

### Round 2 — 2026-07-24 afternoon (PR #8561 v2 evidence)

Agent pivoted: started `bash local.sh --no-log-stream --force-default-port`
(canonical launcher with cache-busted frontend). Same Playwright capture
script, `is_mobile=False`, viewport 390x844.

`page.evaluate()` returned identical state. Same screenshots uploaded to
gist + Slack thread.

User: "What happened? PR still isn't /green? Seems like you did nothing?"

User: "I never saw a proper impl with screenshot/video proof in slack yet"

### Round 3 — 2026-07-24 late afternoon (v3 — actual root-cause investigation)

Agent vision_analyzed the actual screenshot pixels and discovered:

- The chevron's CSS was: `position: absolute; bottom: 0; height: 56px; z-index: auto;`
- The wizard-navigation (Next/Previous bar) had: `position: sticky; bottom: 0; z-index: 50;`
- Both at the same screen position (chevron at y=774-830, nav at y=681-844)
- `elementsFromPoint(chev_x, chev_y)` returned `BUTTON.btn.btn-primary` as topmost
- The wizard-navigation (with its own opaque background) painted OVER the chevron

**The `page.evaluate()` was correct about the chevron's own style — but the
DOM-level truth ("the chevron is `display:flex`") is NOT the visual-level truth
("the chevron is visible to the user"). The chevron was hidden by a sibling.**

Agent fix: bumped chevron to `z-index: 100, bottom: 56px, height: 48px`. After
fix, `vision_analyze` confirmed chevron is visible.

## The pre-claim gate that would have caught this

Before claiming "X is visible in this screenshot" in any user-facing artifact
(Slack message, PR comment, PR description), the agent MUST run:

```python
# Two-step pre-claim gate for visual evidence
def visual_proof_gate(screenshot_path: str, claim: str, expect_elements: list[str]) -> bool:
    """Returns True iff vision_analyze confirms the claim is visible in the screenshot."""
    vision_result = vision_analyze(
        image_url=screenshot_path,
        question=f"Is there a {', '.join(expect_elements)} visible? "
                 f"Describe in detail what you see. If you cannot see any of "
                 f"these elements, say 'I do not see X' clearly."
    )
    # If vision says it doesn't see any of the expected elements, the claim fails
    missing = [e for e in expect_elements if e.lower() not in vision_result.lower()
               and not any(synonym_in(vision_result) for synonym_in in synonyms_of(e))]
    if missing:
        raise EvidenceInvalid(
            f"Claim '{claim}' not supported by screenshot {screenshot_path}. "
            f"Missing visible elements: {missing}. Vision said: {vision_result[:200]}"
        )
    return True
```

Without this gate, the agent defaulted to trusting `page.evaluate()` output as
visual proof. Two consecutive rounds of false evidence shipped to Slack before
the user caught it.

## Related lessons

1. **CSS stacking context trap** (paired with this): `position: relative` parent
   + `position: absolute; z-index: auto` child + sibling with `position: sticky;
   z-index: 50` will hide the child. Always set `z-index` explicitly when both
   child and sibling are positioned.

2. **Playwright `is_mobile` flag matters** (paired with this): `is_mobile=False`
   + viewport 390x844 matches `matchMedia('(max-width: 768px)')` for CSS media
   queries but does NOT replicate mobile browser behavior (sticky positioning
   interactions, touch targets, scroll inertia). For mobile visual evidence
   always use `is_mobile=True, has_touch=True, user_agent=<iPhone UA>`.

3. **Computed style is a necessary but not sufficient condition for visibility.**
   Other conditions: no `display: none` ancestor, no `visibility: hidden` ancestor,
   no `opacity: 0` ancestor, no `clip-path` cropping, no overflow:hidden parent
   clipping, AND no positioned sibling with higher z-index on top. Check all of
   these, not just `display`.

## Verbatim user trigger phrases (collected from this session)

- "your screenshots are showing lmao arrows visually review it"
- "I never saw a proper impl with screenshot/video proof in slack yet"
- "What happened? PR still isn't /green? Seems like you did nothing?"
- "it looks ugly, i want the arrow bigger and the text more readbale"

The first three are visual-proof-recurrence triggers. The fourth is a
design-quality trigger — separate skill needed for that one (mock-first
workflow before shipping).

## Provenance

- PR: https://github.com/$GITHUB_REPOSITORY/pull/8561
- Slack thread: C0AH3RY3DK6/1784894152.572209
- Git diffs: `8b2e65ac11` → `30a6d7841e` → `e6534d20d9`
- The actual CSS fix that worked:
  ```css
  .wizard-scroll-indicator {
    bottom: 56px;        /* was 0 */
    height: 48px;        /* was 56px */
    z-index: 100;        /* was auto — got hidden behind sticky .wizard-navigation z-index:50 */
  }
  ```
