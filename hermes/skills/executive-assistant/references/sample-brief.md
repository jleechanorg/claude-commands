# Sample Executive Sweep — annotated

This is what a good sweep looks like. The cron delivered one like this on 2026-07-05 at 10:21 PDT (MsgID 1783272065.058539, parent 1783263708.161299).

## What made it work

1. **Threaded to the existing brief, not a new top-level DM.** The earlier brief at 08:00 PDT (MsgID 1783263708.161299) was the parent thread_ts.
2. **Dedupe check passed** — 2h20m gap > the 30 min window.
3. **Status-delta framing** — first line states the time delta and last brief, so Jeffrey can tell at a glance whether anything has changed.
4. **Today / Tomorrow / Email / Slack / Deploys / Tonight** — fixed sections in fixed order. Skipped any section with nothing to report (recruiter pitches crammed into Email carry-over, no Slack carry-on since it's a "delta" brief).
5. **Explicit "Want me to:" close** — every actionable item surfaces as a question.

## Format notes

- Slack renders `*bold*`, `_italic_`, `:emoji:` (colon names, not shortcodes). Use `:spiral_calendar_pad:` `:alarm_clock:` `:e-mail:` `:pushpin:` `:large_green_circle:` `:large_yellow_circle:` `:red_circle:` `:white_circle:` `:dollar:` `:seedling:` `:handshake:` `:rotating_light:` `:warning:` `:mag:`. Avoid emoji Unicode directly — Slack interprets them inconsistently.
- Italicize section headers (`_Now / Today_`), bold the top time-stamp line. The contrast helps Jeffrey scan.
- Time-stamp every brief with explicit PDT (not just UTC). He's in San Francisco; his calendar is in `-07:00`.

## Anti-patterns to avoid

- Don't @-mention Jeffrey (`<@U09GH5BR3QU>`). The mention-gate regression breaks every few weeks.
- Don't quote entire email bodies. One-line summary + age is enough; offer to pull full content in the "Want me to:" close.
- Don't list every Slack message — only items needing his input OR he asked about last time.
- Don't repeat carry-over items in the Slack section if they were already covered under Email; pick one section.
- Don't start with "Here's your brief" or "Good morning". The format is self-evident; the timestamp is the greeting.
