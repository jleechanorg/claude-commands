# Red-state proof as Phase 4 — show the repro, not just the fix

**Verified on 2026-07-13, your-project.com PR [#8381](https://github.com/$GITHUB_REPOSITORY/pull/8381)** (the post-#8380 `PRECOMPUTE_FAILED` fix).

## The user pushback that surfaced this

When I posted a Phase 4 reply with **green-state proof only** (live dev-deploy run [29294984874](https://github.com/$GITHUB_REPOSITORY/actions/runs/29294984874) succeeded, `/health` returns 200, revision serving PR HEAD), the user replied mid-turn:

> **"did we prove the red state and repro locally first?"**

That was the right question at the right time. A green deploy proves "the deploy infra is wired correctly NOW". It does NOT prove "the fix actually fixes the root cause vs coincidentally navigating around it". The Phase 4 reply was incomplete — I had built a local repro for my own reasoning but never surfaced it in the user-facing reply.

## The 4-step recipe (verified end-to-end on PR #8381)

### Step 1 — Reproduce red state in a simulated-toolcache venv

BEFORE writing any fix code, build a venv that matches the toolcache Python's dep set exactly. For the your-project.com precompute path:

```bash
python3 -m venv /tmp/repro_precompute/venv
/tmp/repro_precompute/venv/bin/pip install --no-cache-dir \
    fastembed numpy google-cloud-storage jsonschema pydantic cachetools
# Notice: NO flask. This mirrors what `setup-precompute-deps` installs at the
# time of the v1 PR (#8380) — flask was added in the v2 PR (#8381).
```

Now run the v1 probe against it:

```bash
/tmp/repro_precompute/venv/bin/python -c \
    'import fastembed, numpy, google.cloud.storage; import mvp_site.agent_prompts'
# ModuleNotFoundError: No module named 'flask'
```

**That `ModuleNotFoundError` is your red-state proof.** Save it as a fenced code block for the Phase 4 reply. It tells the user (and future you): "this is exactly what was failing on the self-hosted Mac runner, on a clean venv with only the deps the action installs."

### Step 2 — Verify the fix doesn't just navigate around the bug

After the fix code lands (action `pip install`s flask + probe reduced to 7 deps), re-run the SAME simulated venv with the new transitive dep:

```bash
/tmp/repro_precompute/venv/bin/pip install --no-cache-dir flask
/tmp/repro_precompute/venv/bin/python -c \
    'import fastembed, numpy, google.cloud.storage; import mvp_site.agent_prompts'
# (no error — exits 0)
```

Now also run the v2 probe to confirm scope match:

```bash
/tmp/repro_precompute/venv/bin/python -c \
    'import fastembed, numpy, google.cloud.storage, jsonschema, pydantic, cachetools, flask'
# (exits 0)
```

Both succeed. That's the green-state-of-the-v1-probe AND green-state-of-the-v2-probe. Pair them in the Phase 4 reply.

### Step 3 — Verify the actual workload runs

The probe matching imports doesn't prove the toolcache Python can RUN the actual script. Run it:

```bash
cd <repo-root>
PYTHONPATH=/tmp/repro_precompute/venv/bin python \
    scripts/precompute_prompt_embeddings.py --help
# usage: precompute_prompt_embeddings.py [-h] [--bucket BUCKET] [--project PROJECT] [--force]
```

`--help` exits 0 and prints the CLI usage. That proves the full mvp_site import chain (agent_prompts → dice_strategy → provider_gateway → flask) succeeds against the simulated toolcache. This is what the live deploy is going to do — and it works.

### Step 4 — Live deploy + `/health` 200 (green-state proof)

After the PR is merged, trigger the auto-deploy workflow on the merged branch and verify:

```bash
gh workflow run auto-deploy-dev.yml --repo $GITHUB_REPOSITORY --ref main
# wait for run to complete, then:
URL=$(gcloud run services describe mvp-site-app-dev \
    --region=us-central1 --project=worldarchitecture-ai --format='value(status.url)')
curl -fsS "${URL}/health"
# {"status":"healthy","service":"worldarchitect-ai",...}

# And verify the revision is actually serving the merge commit
gcloud run services describe mvp-site-app-dev \
    --region=us-central1 --project=worldarchitecture-ai \
    --format='value(status.latestReadyRevisionName, metadata.labels.commit-sha-full)'
# mvp-site-app-dev-03847-9tc	21c393042168532b8dd555c38d36f284c24ded46
```

The merge-commit SHA match is the load-bearing bit. If `/health` returns 200 from a DIFFERENT commit than the merge SHA, the deploy was silently stale.

## The Phase 4 reply shape (mandatory, after this learning)

```
✅ Done: <one-line end-state declaration>

**Proof:** <green-state evidence — PR URL + run id + /health response + revision SHA + commit SHA match>

**Red-state repro:** <fenced code block — v1 probe failing on the simulated toolcache venv with the EXACT ModuleNotFoundError that motivated the fix>

**Judgment calls:** <2-3 bullets max — what was decided mid-stream that the user might want to override>

🧠 Memories used: [<source>, ids_or_labels, effect> — one line]
```

The Red-state repro block must come BEFORE the Judgment calls block — it's the proof-of-bug that justifies the fix, not a footnote. A green PR with `green-state proof` only is incomplete; pair them.

## Why "show don't tell" — even when the deploy succeeds

The user was right to push back. Three concrete failure modes if you skip the red-state repro:

1. **False-green coincidence.** The fix navigates around the bug rather than fixing it (e.g. changes the probe scope from `mvp_site.agent_prompts` to a less-strict check) without addressing the transitive dep. The deploy succeeds because the probe no longer fails — but the actual workload (`scripts/precompute_prompt_embeddings.py`) would still `ModuleNotFoundError` at runtime. PR #8380 v1 had this shape.
2. **Wrong root cause.** The fix adds a dep that isn't the actual missing one (e.g. `pip install fpdf2` when the actual missing dep is `flask`). Local repro against the simulated venv with the right dep would have surfaced this BEFORE pushing.
3. **Co-evolution.** The fix changes probe scope AND install list together, but neither matches the actual workload's needs. The deploy succeeds because probe + install agree; the workload still fails. Verified by running the actual `precompute_prompt_embeddings.py --help` against the simulated venv.

## Cross-references

- `~/.hermes/skills/finish-the-job/SKILL.md` — Phase 4 reply shape with the new `Red-state repro:` block.
- `~/.hermes/skills/worldarchitect/wa-cloud-run-deploy-failure-debug/SKILL.md` — Mode 8 (the v2 PR #8381 fix surface); Pitfall #14 (probe scope MUST match install scope).
- `~/.hermes/skills/workflow/drive-pr-to-green/SKILL.md` — Pitfall: Evidence Gate freshness contract (the second-cycle SHA-mismatch failure pattern this session also hit on metadata.json).