# Root cause: what the swarm review pipeline missed and a fresh Fable /er caught

Date: 2026-07-11. Context: after two adversarial review swarms (~10 lens/persona
agents), an /advice fan-out (3 reviewers), and an independent supervision
teammate all passed the sidekick/swarm evidence work, a **fresh Fable reviewer
running /er against the final claims returned PARTIAL** with four violations
none of the prior layers had flagged:

1. Evidence media hosted on a PRIVATE repo while the report said "all
   published" (anonymous reviewers get 404; the public PR can't render it).
2. Neither PR body linked the release or media index — no path from the PR to
   the mp4s.
3. No checksum manifest — integrity asserted, not verifiable.
4. The "independent supervisor verification" was asserted only inside the
   artifact it verified (circular provenance), with no raw transcript.

All four were remediated same-day (checksums.sha256 + verification transcript
uploaded, PR bodies given `## Evidence` sections, private hosting logged as an
accepted exception). This doc is about WHY the pipeline missed them.

## Root causes

**RC1 — Every reviewer inherited the author's framing (scope contamination).**
Each swarm lens attacked the questions the orchestrator posed: "are these
claims true?", "do the files contradict?", "can a cold reader follow this?".
Nobody was assigned "does the EVIDENCE PACKAGING meet the /es standard?" —
because the orchestrator, having just built the packaging, didn't think of it
as an artifact under review. Adversarial depth is not adversarial breadth: a
swarm is only adversarial within the scope its author chose. The fresh /er
reviewer started from the STANDARD's checklist (public-URL check, checksum
check, PR-body evidence-section check, circular-provenance check), not from
the author's questions — so the whole missed dimension popped out immediately.

**RC2 — Saturated context normalizes known deviations.** The orchestrator KNEW
hosting was private (chose it deliberately, for a good reason — TUI banners
expose the account email/hostname) and knew the supervisor's verification had
happened (watched it live in-conversation). In a saturated context those facts
feel settled, so "all published" and "independently verified" got written
without noticing that neither is checkable by anyone outside the conversation.
A fresh reviewer has ONLY the artifacts; anything not discoverable from them
is, correctly, treated as unproven. This is the difference between "I know it
happened" and "the bundle proves it happened" — the /es standard exists
precisely to force the second.

**RC3 — Same-model, same-session verification layers correlate.** The lenses,
personas, and supervisor were all Sonnet agents spawned from the same
orchestrator with prompts the orchestrator wrote; the /advice pass reviewed
the SKILL CONTENT, not the final evidence publication (which didn't exist yet
at /advice time). Layers that share an author, a model family, and a moment in
time share blind spots — this repo's own swarm skill rule 12 (cross-model cold
review before any merge-readiness claim) encodes exactly this, and the final
publication step skipped it: no fresh-context /er ran between "media uploaded"
and "goal complete" being reported.

**RC4 — Verification was event-scoped, not claim-scoped.** The supervisor
verified the DEMOS (files on disk, completion markers) — and did that well,
even catching its own grep false-positive. But the report's headline claims
("all published", "goal complete") were about the PUBLICATION, an event no
agent was assigned to verify. Claims that nobody owns don't get checked.

## Why a fresh Fable reviewer caught more

Not (primarily) model capability — the catches required no deep reasoning,
just checklist discipline against unfamiliar artifacts. The advantages were:
(a) **zero authorship context** — every claim had to be re-derived from the
bundle, so claim/artifact gaps were visible; (b) **standard-first framing** —
/er walks the /es checklist, immune to the author's scope choices; (c)
**incentive inversion** — its job was to cap the verdict, not to finish the
project. A Fable-class model does help with (a)-(c) synthesis speed and with
noticing pattern-level issues (e.g. recognizing circular provenance as a
class), but a Sonnet /er with the same checklist and zero context would likely
have caught violations 1–3; violation 4 (circular provenance) is where the
stronger reviewer plausibly mattered.

## Durable fixes

1. **Add a packaging lens to every evidence-producing swarm**: one lens whose
   only scope is the /es checklist against the final bundle (public URL,
   checksums, PR-body links, provenance chain, exception log). Encoded in
   `swarm-adversarial-review-howto.md` step 5.
2. **Fresh-context /er gate between "evidence uploaded" and any
   "published/complete" claim** — same rule as swarm rule 12, extended from
   code claims to evidence claims. The reviewer must NOT be the orchestrating
   session.
3. **Claim-ownership check before reporting**: for each sentence in the final
   report, name the artifact that proves it. "All published" fails this test
   instantly against a private release.
4. **Exceptions are logged, never narrated away**: a deliberate deviation
   (private hosting) is written into the bundle as an accepted PARTIAL
   exception at decision time — not discovered by a reviewer later.

## Severity assessment (added 2026-07-11, after bead triage)

Was anything the fresh reviewer found actually SERIOUS? Honest ranking:

- **Serious — one finding.** The private-hosting + "all published" overclaim
  (bead rev-xwc0i, P1). Serious for two reasons: it is a REPEAT of a known
  failure class (PR #6161, 2026-04-11 — the evidence-review skill documents it
  as a historical lesson, and it happened again anyway), and it converts a
  deliberate, defensible engineering decision (keep identity-exposing footage
  private) into a false claim simply by omitting the disclosure. The artifacts
  were fine; the sentence about them wasn't. Status: mitigated (exception
  logged in-bundle, PR bodies disclose "collaborators only"); full fix (redact
  banners → public rehost) tracked in rev-xwc0i.
- **Moderate hygiene — three findings, all fixed same-day.** Missing PR-body
  evidence links (rev-jamxs), missing checksum manifest (rev-wcs6q), and the
  circular "supervisor verified it" provenance (rev-kbmn9). None indicated
  wrong results — the transcript re-run reproduced every PASS — but each made
  a true claim unverifiable, which per /es is the same as unproven.
- **Zero findings against the technical substance.** Team formation, split
  panes, two-way SendMessage, codex spawn_agent lanes, bidi steering, SHA
  provenance — the reviewer rated the core mechanics STRONG and explicitly
  concluded "this isn't fabricated." Nothing in the skill content, the demo
  results, or the recorded behavior was refuted.

Net: the fresh window found no correctness defects, one serious process
defect (a recurring overclaim class), and three verifiability gaps. That
distribution is itself the lesson — after enough same-context review layers,
the remaining defects live in the REPORTING, not the work.
