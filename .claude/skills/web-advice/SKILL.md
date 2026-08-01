---
name: web-advice
description: Multi-model Web LLM Chat (ChatGPT, Grok, Gemini Web) review workflow for PRs, evidence bundles, and video proof via browser / aside-mcp
---

# Web Advice Skill (`web-advice`)

Automates multi-model adversarial review of pull requests, evidence bundles, and video proof across Web LLM Chat interfaces (ChatGPT, Grok, Gemini Web) using `aside-mcp` and browser automation.

---

## Overview

When reviewing PRs, evidence standards, or visual video proof, this skill provides a structured workflow to query external Web Chat models (Google Gemini Web, ChatGPT, xAI Grok) via `aside-mcp` browser automation and synthesize their feedback.

---

## Workflow Phases

### Phase 1: Context Aggregation
1. Gather PR context:
   - PR Number, Branch Name, HEAD commit SHA (`gh pr view <number> --json title,body,commits,headRefName,url`).
   - Short diff summary (`git diff --stat`).
   - Key invariants & architectural claims.
2. Locate Evidence Bundle & Video Proof:
   - `metadata.json`, `results.json`, `SHA256SUMS.txt`.
   - Captioned video (`.mp4`) and animation (`.gif`) paths.
   - Frame timeline and WebVTT caption mapping.

### Phase 2: Browser Session Connection
Connect to active Web Chat tabs via `aside-mcp` (`repl` tool) or open new tabs:
- **Google Gemini Web**: `https://gemini.google.com/app`
- **ChatGPT**: `https://chatgpt.com/`
- **xAI Grok**: `https://grok.com/`

### Phase 3: Structured Prompt Submission
Send the standardized review prompt to each Web Chat tab:
```markdown
Please act as a Senior Staff Principal AI Systems Architect and review Pull Request #<number>:

**PR Title**: <title>
**PR Branch**: <branch> (HEAD commit: <sha>)
**Architecture Invariants**:
1. [Invariant 1]
2. [Invariant 2]
3. [Invariant 3]
...

**Verified Video & Evidence Artifacts**:
- Captioned MP4: <mp4_path>
- Captioned GIF: <gif_path>
- Frame Timeline: <timeline_summary>

Evaluate:
1. Architectural soundness & state-machine compliance.
2. Edge case safety & risk analysis.
3. Evidence bundle integrity (relative paths in SHA256SUMS.txt, checksum correctness).

Provide:
1. VERDICT: [APPROVE / REJECT / CHANGES REQUESTED]
2. ARCHITECTURAL ANALYSIS
3. VERIFICATION & EVIDENCE ASSESSMENT
```

### Phase 4: Response Capture & Synthesis
- Snapshot the responses from all Web Chat tabs using Playwright/snapshot tools.
- Compile a multi-model synthesis table containing:
  - Model Name & Web URL
  - Verdict (`APPROVE` / `REJECT` / `CHANGES REQUESTED`)
  - Key Findings & Recommendations

### Phase 5: Remediation & Convergence
- For any valid, actionable finding:
  1. Fix the underlying code, prompt, or test.
  2. Re-verify locally and update the evidence bundle.
  3. Re-run `/web-advice` until all models return `APPROVE`.
