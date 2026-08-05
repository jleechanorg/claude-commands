# web-advice Skill Resolver (local)

Local resolver entry for the `web-advice` skill. There is no global
`RESOLVER.md` under `~/.claude-wa/skills/` (the global resolvers live at
`~/.hermes/skills/RESOLVER.md` and `~/.hermes_prod/skills/RESOLVER.md`, which
this skill is not part of) — this file is the skill-local equivalent so
`/skillify` item 6 ("Resolver trigger — entry in the skills resolver with
trigger patterns the user actually types") and item 7 ("Resolver trigger
eval") have something concrete to point at and test.

**Known-bug guidance (skillify SKILL.md, "Known Bugs in skillify Test Suite",
Bug 2):** the standard resolver-trigger regex used by trigger-eval tests is
non-greedy and stops at the first blank line after the heading —
`(name.*?)(?=\n\n|\n##)`. If trigger words live in a `**Triggers:**` sub-line
below a blank line, that regex silently misses them and the trigger eval
false-negatives. The fix: put **ALL** trigger words directly **on the heading
line**, not in a sub-line below it. This file follows that fix.

---

## web-advice — web advice, multi model review, ask chatgpt gemini grok perplexity, external model review, browser review, second opinion from the web

**File:** `~/.claude-wa/skills/web-advice/SKILL.md`
**Command:** `/web-advice`
**Mechanism:** real browser sessions (aside-mcp repl → aside CLI repl →
claude-in-chrome → chrome-headless with browserclaw cookies) driving the
actual ChatGPT/Gemini/Grok/Perplexity websites in the user's authenticated
browser. Provider APIs, CLI models, subagents, and WebSearch/WebFetch
synthesis are BANNED substitutes — see the HARD-FAIL CONTRACT in SKILL.md.
**Distinct from:** `/advice` (in-session subagent + `/secondo` + `/research`
— see `~/.claude/skills/advice/SKILL.md`) and `/er` (evidence-standards
4-gate check — see `~/.claude/skills/evidence-review/SKILL.md`). `/web-advice`
is for an independent multi-model *browser* adversarial pass, not in-session
reasoning and not evidence-bundle integrity checking.
**Evals:** `evals/web_advice_evals.md` (skillify item 5, 4 cases: happy /
2-of-4 honest-accounting edge / API-substitution adversarial / frames-only
methodology-question adversarial).
**Resolver trigger eval:** `evals/test_resolver_trigger.py` (skillify item 7).
**E2E transport smoke:** `scripts/e2e_smoke.sh` (skillify item 9, diagnostic
probe of all 4 transport rungs — never submits a prompt, never opens a tab).
