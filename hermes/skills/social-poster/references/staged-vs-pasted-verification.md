---
name: staged-vs-pasted-verification
description: How to verify that a social-media draft actually got pasted into the compose form (vs. just loaded an empty form). Required reading before claiming any platform "ready to POST APPROVED".
---

# staged vs. pasted — verification checklist

## The failure mode

`stage_in_aside.py` (and any wrapper that calls `openTab(compose_url)` then screenshots) labels the platform `staged` once the page loads. **It does NOT verify that the draft text actually landed in the title input / body textarea.**

Three reasons the paste silently fails:

1. **React-controlled-field re-render.** Programmatic `el.value = text` + `dispatchEvent('input')` works for vanilla `<textarea>` and `<input>` elements but doesn't sync React's internal `useState` value tracker on platforms like Twitter/X. Twitter's text input box (`[data-testid="tweetTextarea_0"]`) requires a specific 3-step dance: focus → `document.execCommand('insertText', false, text)` → blur. Verified 2026-07-11 — Twitter compose modal opened, paste attempted via React setter, vision-verified the textbox was empty.
2. **contentEditable fields (LinkedIn, Facebook).** `el.innerText = text` doesn't fire the synthetic input event that React/LinkedIn's composer listens for. Must use `el.innerHTML` + dispatch a full `InputEvent` with `data` and `inputType: 'insertText'` properties, then call `el.dispatchEvent(new InputEvent('input', { bubbles: true, data: text }))`. Even then, LinkedIn's composer often rejects programmatic input entirely — manual paste is more reliable.
3. **Compose modal not yet rendered.** For platforms that need a click to open the compose modal (LinkedIn "Start a post", Facebook "What's on your mind?", Threads), the stage script may screenshot the feed page instead of the modal. Verify the compose modal is actually in the DOM before attempting paste.

## Vision-verification checklist (run after every stage)

The default `vision_analyze` prompt ("Is this the X compose form?") will return "yes, this is the compose form" whether the form is empty OR filled — because it answers about page state, not field content. **You must explicitly ask about field contents.**

```python
vision_prompt = (
    "Look ONLY at the *title input box* and the *text (body) textarea*. "
    "What exact text (if any) is currently inside them? "
    "Quote any text character-for-character. "
    "If empty say so explicitly."
)
```

For Reddit-style forms (title + body textareas):
- Empty: vision returns "Both the title input box and the text textarea are empty."
- Pasted: vision returns the actual draft text in the fields.

For Twitter/LinkedIn contentEditable:
- Empty: vision returns "the placeholder text 'What's happening?' is showing"
- Pasted: vision returns the actual draft text rendered inside the compose box

**If vision says "empty" or "placeholder showing" → the stage script's paste did NOT persist. Do NOT claim ready.**

## Reusable paste verification snippet (for stage_in_aside.py)

Add this to the end of each platform's stage function, BEFORE marking "staged":

```python
verify = page.evaluate("""() => {
    const titleEl = document.querySelector(
        'textarea[name="title"], input[name="title"], '
        + 'div[contenteditable="true"][role="textbox"]'
    );
    const bodyEl = document.querySelector(
        'textarea[name="text"], textarea[name="body"], '
        + 'div[contenteditable="true"][data-testid="tweetTextarea_0"]'
    );
    return {
        titleVal: titleEl ? (titleEl.value ?? titleEl.innerText ?? '').slice(0, 200) : null,
        bodyVal: bodyEl ? (bodyEl.value ?? bodyEl.innerText ?? '').slice(0, 200) : null,
        titleLen: titleEl ? (titleEl.value ?? titleEl.innerText ?? '').length : 0,
        bodyLen: bodyEl ? (bodyEl.value ?? bodyEl.innerText ?? '').length : 0,
    };
}""")
if verify["titleLen"] == 0 or verify["bodyLen"] == 0:
    return {"ok": False, "reason": "paste_did_not_persist", "verify": verify}
```

## What to do when paste fails

1. **For Reddit / Mastodon / Dev.to** (plain textareas): the React-setter pattern usually works. Verify `wait_for_selector` fires BEFORE attempting paste — SPA hydration can take 3-5s on old.reddit.
2. **For Twitter**: use the 3-step `execCommand('insertText')` dance in a Playwright `page.locator(...).fill()` call instead of evaluate(). Playwright's `fill()` works around the React-controlled issue for Twitter's tweetTextarea.
3. **For LinkedIn / Facebook / Threads (contentEditable)**: abandon programmatic paste. Manually open the compose modal, then have the user copy-paste from the .md file. The `aside repl` openTab() path can stage the modal open, but the paste step is a user action.
4. **For all platforms**: the fallback is always "open the compose modal via automation, surface the .md draft text in Slack, user pastes manually". This is the only 100%-reliable path for contentEditable + React-controlled fields.

## Anti-pattern (what NOT to do)

❌ "stage_in_aside.py said `staged: True`, so I'll trust it" — without vision-verifying field contents. This was the bug in the 2026-07-11 Fable-2D-game run: 13 platforms marked staged, 0 actually had pasted text. User caught it immediately: "all of those drafts are obviously wrong and just random login screens so youre not even close to working".

## Provenance

- 2026-07-11: Jeffrey Lee-Chan pushback in Slack thread `C09GRLXF9GR/p1783809934.098269`.
- Stage script source: `~/.hermes/skills/social-poster/scripts/stage_in_aside.py`.
- Verification snippet adapted from the `stage_and_paste.py` Playwright script written 2026-07-11 at `/tmp/drafts/fable-2d-game-2026-07-11/stage_and_paste.py`.