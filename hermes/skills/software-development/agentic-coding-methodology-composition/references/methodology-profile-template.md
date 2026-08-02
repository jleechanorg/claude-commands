# Methodology Profile Template

Copy this template when adding a new methodology to `references/<name>.md`.

---

# <Methodology Name>

- **Author(s):** <name(s)>
- **Canonical source:** <GitHub URL or npm package or official docs URL>
- **License:** <MIT / Apache-2.0 / etc>
- **First commit / latest release:** <date(s) if known>
- **Star count:** <if known; reject as "evidence of correctness" — useful only as adoption signal>
- **Local install status:** <installed at <path> v<version> / NOT installed>

## One-line positioning

<What it is in 10 words.>

## Core question it asks

<The framing question the methodology is built around. e.g., Superpowers: "how do we ship from idea to mergeable branch with discipline?" / grill-me: "have you actually thought this through?">

## Pipeline / loop / workflow

<The named phases or skills, in order.>

```
<phase1> → <phase2> → <phase3> → …
```

## Distinctive features (what it does that others don't)

- <Feature 1>
- <Feature 2>
- <Feature 3>

## Invocation model

- **Auto-fire** (agent triggers on session start, hard-gates implementation): e.g., Superpowers.
- **Opt-in** (user must explicitly invoke): e.g., grill-me (`disable-model-invocation: true`).
- **Mixed** (some auto-fire, some opt-in): e.g., GSD Core (`/gsd-*` namespace).

## Artifact tree (where state lives)

<Where the methodology persists state. e.g., GSD → `.planning/`. Superpowers → `docs/superpowers/{specs,plans}/`. grill-me → nothing.>

## Multi-harness support

<Which CLIs / editors it works on. e.g., Superpowers: Claude Code, Codex, Cursor, OpenCode, Pi, Copilot CLI, Antigravity, Kimi CLI.>

## Installation paths

<Exact install commands per harness.>

## Known anti-patterns

- <Anti-pattern 1>
- <Anti-pattern 2>

## Sources

- <URL 1>
- <URL 2>