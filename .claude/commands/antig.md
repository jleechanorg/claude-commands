---
description: Antigravity computer use via Peekaboo — interact with the Antigravity macOS app. Also used by /eloop to babysit the Antigravity IDE and self-improve this skill.
---

Use the `antigravity-computer-use` skill to complete the following task in Antigravity:

$ARGUMENTS

---

## Self-improvement protocol (for /eloop and monitoring loops)

When you encounter a new failure mode or workaround while using Antigravity:

1. **Document the lesson** as a dated note at the top of the MANDATORY section in the skill:
   ```
   - YYYY-MM-DD: <what failed> → <what works instead>
   ```

2. **Update the skill file** at `$HOME/.claude/skills/antigravity-computer-use/SKILL.md`:
   - Add the new workaround to the relevant section
   - Update the "MANDATORY" section if it's a universal check
   - Keep entries concise and actionable

3. **Report the improvement** in your recap: `skill_updated=true, section=<section name>`

### Known lessons (update as we learn more)

| Date | Failure | Fix added to skill |
|------|---------|-------------------|
| 2026-04-03 | Allow dialog missed after send | MANDATORY section added — PIL blue-button scan after every screenshot |
| 2026-04-03 | Editor FPs: VS Code Python interpreter (726,628), bottom notification (454,715), terminal Relocate (928,595) | Known FP dict added to SKILL.md — add to FP set; real dialogs dismiss on click, FPs do not |
| 2026-04-03 | Manager window closed; old bounds captured wrong window (Claude usage page) | Re-fetch window list each cycle; switch PIL bounds to editor when Manager absent |
| 2026-04-03 | Fullscreen editor window (0,37,1728,1080) triggers FP at (83,623) — VS Code diff gutter indicators | Added '83,623' to FP dict; PIL must divide by 2 for retina (cx//2, cy//2) |
| 2026-04-03 | x<100 coords in fullscreen always gutter FPs — 83,586 and 91,585 also triggered in successive scans | Gutter FP rule added: x<100 in fullscreen = always skip; real Allow dialogs appear at x>300 |
