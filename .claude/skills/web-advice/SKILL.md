---
name: web-advice
description: Browser-based multi-model review using ChatGPT, Gemini, Grok, and Perplexity Web via aside-mcp. Use when you need an independent multi-model adversarial pass over a PR, evidence bundle, or design doc — not for in-session reviews (use /advice for that).
---

# /web-advice — Multi-Model Browser Review

`/web-advice` queries **4 independent web LLMs** (ChatGPT, Gemini, Grok, Perplexity) through their web UIs in the user's authenticated browser, then synthesizes their verdicts. This is **different from `/advice`** (which is in-session and uses subagents + /secondo + /research).

| Skill | Mechanism | When to use |
|---|---|---|
| `/advice` | In-session: subagent + /secondo + /research | Architectural reasoning, ZFC reviews, code-path analysis |
| `/web-advice` | Browser: ChatGPT + Gemini + Grok + Perplexity Web via `aside-mcp` | Independent multi-model adversarial pass; visual/video evidence; web-search grounding |
| `/er` | In-session: evidence-standards skill | Evidence bundle integrity (4-gate checksum/SHA/real-services) |

Use `/web-advice` when you need at least 2 different model families to converge on a verdict, or when the review must include external web standards (e.g., D&D 5e SRD, Stately XState, industry patterns).

---

## Pre-Flight Checklist (run BEFORE opening any browser)

### Step 0a — Verify the review subject is ready

```bash
# 1. PR + HEAD
gh pr view <N> --json number,title,headRefName,headRefOid,state,url

# 2. Evidence bundle (if reviewing a PR with one)
ls -la docs/pr<N>-evidence/ 2>/dev/null
cat docs/pr<N>-evidence/metadata.json 2>/dev/null | python3 -m json.tool

# 3. /er 4-gate pre-flight (REQUIRED for PRs with evidence bundles)
cd docs/pr<N>-evidence
sha256sum -c SHA256SUMS.txt          # Gate 1: Checksum integrity
test -f verification_report.json    # Gate 2: Verification report (N/A if absent)
cat metadata.json | jq '.git_provenance.git_head' | xargs -I {} \
  bash -c 'test {} = $(gh pr view <N> --json headRefOid -q .headRefOid) && echo Gate 4 PASS || echo Gate 4 FAIL'  # Gate 4: SHA matching
```

**Stop here if any gate FAILs** — regenerate the bundle first; /web-advice is wasted on stale evidence.

### Step 0b — Build the review prompt

A `/web-advice` prompt has 4 mandatory sections. Build it BEFORE opening the browser so you can paste the same prompt to all 3 models in one shot.

```markdown
You are a Senior Staff Principal AI Systems Architect reviewing a [PR | evidence bundle | design doc].

**Subject**:
- Type: [PR | bundle | doc]
- Identifier: [<PR URL> | <bundle path> | <doc path>]
- Branch / Commit: [<branch> @ <sha>]
- Working directory: <absolute path>

**Context** (≤ 200 lines, paste from local files):
- <relevant code, file:line citations>
- <relevant tests, file:line citations>
- <relevant doc snippets>

**Review dimensions** (pick what applies):
1. Architectural soundness (state-machine compliance, ZFC consumer split, layer isolation)
2. Edge case safety (concurrent writes, time freeze, god mode, modal locks)
3. Evidence bundle integrity (checksum validity, SHA alignment, real-service proof)
4. Test coverage (structural vs rendered-text, multi-turn vs single-shot)
5. Web standards alignment (cite external sources)

**Required output format** (verbatim):
VERDICT: APPROVED | APPROVED with notes | CHANGES REQUESTED | REJECTED
REASONING: 3-4 sentences
RISK: main risk, one sentence
CONFIDENCE: high | medium | low
WEB SOURCES: 1-3 URLs with one-line summaries (if you cited any)
```

The prompt is the same for all 3 models. Don't customize per model.

---

## Browser Execution Protocol

### Step 1 — Open 4 tabs

```javascript
// In aside-mcp repl (mcp__aside-mcp__repl tool)
await openTab('https://gemini.google.com/app');
await openTab('https://chatgpt.com/');
await openTab('https://grok.com/');
await openTab('https://www.perplexity.ai/');

const allTabs = await listBrowserTabs();
console.log('opened:', allTabs.length, 'tabs');
for (const t of allTabs) console.log(' -', t.title, '(', t.url, ')');
```

Expected output: 5 tabs (your existing tab + 4 new). Logged-in users will see "Ask Gemini", "ChatGPT", "Grok", "Perplexity" titles.

### Step 2 — Verify auth state (CRITICAL)

```javascript
// Attach to each tab and check login state
const tabs = await listBrowserTabs();
const gemTab = tabs.find(t => t.title === 'Google Gemini');
const gemPage = await attachBrowserTab(gemTab.targetId);
const gemSnap = await snapshot(gemPage);
const geminiLoggedIn = !gemSnap.tree.includes('Sign in') && !gemSnap.tree.includes('Log in');
console.log('gemini logged in:', geminiLoggedIn);
```

**Repeat for ChatGPT, Grok, and Perplexity.** If any model is not logged in, **stop and ask the user to log in** — do NOT try to log in for them (no credentials, no auth cookies, no OAuth flow). Login state per model:

- **Gemini**: Logged in shows "Google Account: <email>" in the sidebar
- **ChatGPT**: Logged in shows "Log in" button HIDDEN; prompt textbox visible. **Heads up:** ChatGPT may show the marketing landing page ("Where should we begin?") with a "Log in" button even when a session cookie exists, depending on cookie state. If the textbox is missing OR the page shows "Sign up for free", the session is genuinely gone — ask the user to log in. Try navigating to `chat.openai.com` as a fallback URL.
- **Grok**: Logged in shows chat history in sidebar; "New Chat" button enabled
- **Perplexity**: Logged in shows username in the top-right corner (e.g., "jleechan77861") AND a "Sessions" sidebar with prior chats

If the user can't log in to one model, run /web-advice with the others (3-of-4 still satisfies the multi-model adversarial requirement) and note the gap in the synthesis.

### Step 3 — Submit prompt to each model (sequentially, not parallel)

Submit one model at a time. Submitting in parallel can hit rate limits or trigger captchas. Wait for each response before submitting the next.

**Pattern (proven to work):**

```javascript
// For Gemini (the locator ref varies — use aria-label selector)
const gemPrompt = `<your 4-section review prompt>`;
const gemTabs2 = await listBrowserTabs();
const gemT = gemTabs2.find(t => t.title === 'Google Gemini');
const gemP = await attachBrowserTab(gemT.targetId);
const textbox = await gemP.locator('div[aria-label="Enter a prompt for Gemini"]');
await textbox.click();
await gemP.keyboard.type(gemPrompt, {delay: 3});  // 3ms per char, real typing
await gemP.keyboard.press('Enter');
console.log('sent to Gemini, waiting...');
// Wait for response — Gemini Pro typically takes 15-45 seconds
await new Promise(r => setTimeout(r, 30000));
const gemResp = await snapshot(gemP);
console.log(gemResp.tree);
```

**Gotcha — duplicated text:** If a prior prompt was inserted via `el.innerText = ...`, the textbox may show duplicated content. Always clear with `Cmd+A` + `Backspace` BEFORE typing the new prompt:

```javascript
await textbox.click();
await gemP.keyboard.press('Meta+A');
await gemP.keyboard.press('Backspace');
await new Promise(r => setTimeout(r, 500));
```

**Gotcha — TrustedHTML errors:** Don't use `el.innerHTML = ...`; Gemini's textbox uses Trusted Types. Use `el.innerText = ...` (which works) OR use `keyboard.type()` (which always works).

**Gotcha — ChatGPT send:** ChatGPT requires clicking the "Send message" button, NOT pressing Enter. After typing, locate and click it.

**Perplexity (proven working pattern):**

```javascript
// Perplexity textbox is a DIV with role="textbox" — NOT a <textarea>
// Selector that works: [role="textbox"]
const perpTabs = await listBrowserTabs();
const perpTab = perpTabs.find(t => t.title === 'Perplexity');
const perpPage = await attachBrowserTab(perpTab.targetId);
const textbox = await perpPage.locator('[role="textbox"]').first();
await textbox.click();
await perpPage.keyboard.type(reviewPrompt, {delay: 3});
await perpPage.keyboard.press('Enter');  // Enter submits; no separate button click
console.log('sent to Perplexity');
```

**Perplexity quirks:**
- Textbox is a `DIV` with `role="textbox"` and no `aria-label` — use the role selector, not the aria-label pattern
- After response, the new textbox ref changes (Perplexity regenerates the textbox element); always re-snapshot to get the fresh ref before the next prompt
- Perplexity answers include a `Sources` accordion (collapsed by default) and a `Pro` badge; responses are typically citation-rich — useful for "cite your web sources" requirements
- Perplexity defaults to "Search" mode (web-grounded); for code-only review, switch to "Reasoning" mode via the model selector button before submitting

### Step 4 — Capture responses

```javascript
// For each model, after the response finishes (look for the "regenerate" / "thumbs up" footer)
const respSnap = await snapshot(modelPage);
const respText = respSnap.tree;
// Parse for VERDICT:, REASONING:, RISK:, CONFIDENCE:
const verdictMatch = respText.match(/VERDICT:\s*([^\n]+)/);
const reasoningMatch = respText.match(/REASONING:\s*([^\n]+(?:\n[^\n]+){0,3})/);
console.log('verdict:', verdictMatch?.[1]);
console.log('reasoning:', reasoningMatch?.[1]);
```

Models don't always format in the exact section headers. If the regex misses, look for the verdict line in the visible response:

- **Gemini Pro**: Structured output, "Copy code" button visible, response in dedicated region
- **Grok**: Conversational, "Like"/"Dislike" footer; verdict may be a single line near the end
- **ChatGPT**: Most conversational, may not return structured output unless explicitly reminded
- **Perplexity**: Citation-rich, "Sources" accordion; "Helpful"/"Not helpful" footer; verdict usually at the end

**Parser fallback** if structured regex fails — re-prompt the model with: *"Reply with ONLY this exact format (no other text): VERDICT: <one line> | REASONING: <one line> | RISK: <one line> | CONFIDENCE: high/med/low"*. This is the most reliable cross-model pattern.

### Step 5 — Synthesize

```markdown
## /web-advice synthesis

| Model | Verdict | Confidence | Key finding |
|---|---|---|---|
| ChatGPT | <verdict> | high/med/low | <one line> |
| Gemini Pro | <verdict> | high/med/low | <one line> |
| Grok | <verdict> | high/med/low | <one line> |
| Perplexity | <verdict> | high/med/low | <one line> (note: web-grounded, citation-rich) |

**Convergence:** <3-of-4 agree / all 4 agree / 2-2 split / other>
**Recommended action:** <APPROVE / approve with conditions / change requests>
**Open web sources cited:** <list URLs from Perplexity + any model that cited external standards>
```

**Decision rule:** 3-of-4 agreement is sufficient (or 2-of-4 if both verdict strongly converge). 2-of-4 is acceptable when the two models are from different model families. If all 4 diverge, surface the disagreement to the user and ask which axis (speed / safety / cost) matters most. Perplexity's web grounding often breaks ties by surfacing external standards (D&D 5e SRD, RFC, etc.) that the other models lack.

---

## Failure Recovery

### Aside daemon disconnects

Symptom: `Task failed: fetch failed: other side closed. Aside daemon is not reachable — make sure Aside Browser is running, then retry.`

Recovery:
1. Check that the Aside Browser app is still running (not crashed)
2. Reopen any lost tabs: `await openTab('https://gemini.google.com/app')` etc.
3. Re-snapshot before each fill (refs are NOT stable across `attachBrowserTab` cycles)
4. If recovery fails 3 times, fall back to a subagent with WebSearch (this is /advice Reviewer A, not /web-advice — but better than nothing)

### Captcha or rate limit

Symptom: a "I'm not a robot" or "You've reached your limit" page.

Recovery:
1. Stop the affected model — don't retry
2. Note the rate-limit in the synthesis
3. Continue with the other 2 models
4. If 2-of-3 already returned, synthesize and stop; if 1-of-3 only, fall back to subagent

### Login required

Symptom: ChatGPT shows "Log in" button; Grok shows "Sign in" page; Gemini shows "Sign in to continue".

Recovery:
1. **Do NOT attempt login** — no credentials, no OAuth flow
2. Stop and ask the user to log in manually
3. Continue with the other models
4. If only 1 model is logged in, that's a single-model review, not multi-model — note this in synthesis

### Stale evidence (Gate 4 FAIL)

Symptom: `metadata.json:git_provenance.git_head` ≠ PR HEAD `headRefOid`.

Recovery:
1. **Stop /web-advice** — the verdict will be against stale evidence
2. Regenerate the evidence bundle against current HEAD
3. Re-run /er 4-gate
4. Re-run /web-advice

---

## When NOT to use /web-advice

- **In-session code review** → use `/advice` (subagent + /secondo + /research)
- **Evidence bundle integrity** → use `/er` (4-gate checksum/SHA/real-services)
- **Triage plan review** → use `/advice` first; escalate to `/web-advice` only if the plan needs external validation
- **Visual/video proof** → `/web-advice` IS the right tool (Gemini can watch video)

---

## Token Budget

| Step | Tokens |
|---|---|
| Pre-flight + prompt build | ~2K |
| Browser session (3 tabs) | ~5K (state management) |
| Per-model response | ~2-3K |
| Synthesis | ~500 |
| **Total** | **~13K** vs ~50-100K for full advisor() |

**~85-90% fewer tokens** than `advisor()` while still getting 3-model adversarial coverage.

---

## Reference

- Provenance: artifact `~/roadmap/2026-08-01-web-advice-and-evidence-review-guide.md` (Antigravity Genesis Coder, 2026-08-01)
- 4-gate pre-flight: `~/.claude/skills/evidence-standards/SKILL.md`
- Browser automation: `aside-mcp` (`mcp__aside-mcp__repl` tool)
- Companion skill: `/advice` (in-session multi-reviewer)
