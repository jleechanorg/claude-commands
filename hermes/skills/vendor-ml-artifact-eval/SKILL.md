---
name: vendor-ml-artifact-eval
version: 0.1.0
description: "Pre-adoption evaluation recipe for any third-party ML artifact (router, classifier, embedding model, RAG pipeline). Before recommending adoption — or even running it on real production traffic — load this skill and run the 6-gate checklist: (1) README-vs-claim triangulation, (2) code-level load-path inspection, (3) shipped-checkpoint-vs-claimed-class-count gate (the silent killer — 2026-07-22 incident: NUM_LABELS=4 in code, NUM_LABELS=6 in shipped weights), (4) per-turn architecture boundary check (truncation, fallback policy, confidence threshold), (5) on-distribution label-coverage audit against YOUR real workload, (6) realistic cost-cut estimate for YOUR workload (not the vendor's headline figure)."
tags: ["eval", "vendor", "router", "classifier", "model", "adoption", "pre-adoption", "ml-artifact"]
category: software-development
triggers:
  - evaluate this model
  - evaluate this router
  - evaluate this classifier
  - is this good for our use case
  - should we adopt this
  - replay our convos through this
  - does it pass for classification
  - check if the claims hold
  - vendor model eval
  - third-party router eval
  - run it on my past convos
  - what would it choose on my data
  - are the choices right
  - eval before adoption
  - pre-adoption check
changelog:
  - "0.1.0 (2026-07-22): Initial version. Recipe distilled from `deycoding/deycoding-compliance-classifier-router` evaluation — the first end-to-end run of this checklist. Six gates + the headline finding pattern (NUM_LABELS=4 vs shipped-checkpoint head=6) that the eval surfaced. Companion to `finish-the-job` (the eval-stall anti-pattern was patched there). Verified end-state: 11 prompts run against the actual model, 441MB weights loaded from HuggingFace, eval report at `~/projects/router-eval/EVAL_REPORT.md`."
related_skills:
  - finish-the-job
  - verify-deployed-frontend-fix
  - cli-env-var-verification
  - convergent-bug-triage
  - pr-description-validator-gate6b
  - patch-port-protocol
  - skillify
  - harness-engineering
---

# vendor-ml-artifact-eval

**Pre-adoption evaluation recipe for third-party ML artifacts.** Run this skill when a user asks to evaluate / adopt / replay-against-real-data / check-claims-hold on a third-party model, router, classifier, embedding, or pipeline. The class-of-failure mode this skill catches: **vendor claims that pass the headline test but break under code-level inspection.**

## Why this skill exists

Headline claims ("99.2% accuracy", "65-73% cost savings", "<10ms latency", "supports whole-convo classification") are the **first** layer of evaluation, not the last. The 2026-07-22 incident (this skill's originating event) had every headline claim — and the shipped repo **does not run end-to-end as-documented**. Specifically:

- `server/server.py` sets `NUM_LABELS = 4` and a 4-entry `LABELS` dict (simple_no_pii, simple_pii, complex_no_pii, complex_pii).
- The shipped `state_dict` from HuggingFace has a **6-class** classification head (`classifier.3.weight: torch.Size([6, 768])`).
- The README documents the architecture as `Linear(768-768) - Tanh - Dropout - Linear(768-4)`.
- **Three sources of truth disagree.** The FastAPI server cannot start; `load_state_dict` raises on shape mismatch with the default `strict=True`.

This skill catches that class of failure systematically, **before** recommending adoption. The same checklist catches: short-context truncation that makes "whole-convo" impossible, fallback policies that mask real ambiguity, label sets that don't cover the user's actual distribution, and headline cost-savings numbers that only hold for the vendor's narrow workload.

## When to load

Load this skill when **any** of these signals fire:

| Signal | Example |
|---|---|
| User shares a third-party ML artifact and asks "is this good" | "evaluate this: https://github.com/<vendor>/<router>" |
| User asks to replay their data through a third-party classifier | "can we replay it against some of my older convos" |
| User asks for adoption guidance on a vendor router | "should we adopt this for our cost-cut" |
| User asks to verify vendor claims | "do the claims hold / does it actually do what they say" |
| User shares a Medium / blog post about a vendor's ML pipeline | "look at this article and tell me if it would work for us" |

Do **not** load this skill for: evaluating your own model (use `verify-deployed-frontend-fix` or the harness-engineering skill), CLI tool env var claims (use `cli-env-var-verification`), sibling-bug triage on your own campaign (use `convergent-bug-triage`).

## The 6-gate checklist

Run these in order. **Each gate is independently load-bearing** — a fail at gate N invalidates downstream gate results.

### Gate 1 — README-vs-claim triangulation

**Goal:** Verify the artifact's docs match its claims. Even before reading code, mine the README (or article, or paper) for:

- Architecture numbers (parameters, dimensions, layers, max sequence length, vocabulary size)
- Latency claims (GPU, CPU, throughput)
- Accuracy claims (overall accuracy, per-class precision/recall, PII recall)
- Cost-savings claims (typically stated as a percentage on the vendor's workload)
- Label set / class taxonomy (what the model is supposed to output)
- Deployment story (one command? CloudFormation? Docker? local-only?)

Write these into a 1-row table at the top of the eval report. You'll cross-reference each claim against the code at Gate 3.

**Pitfall:** Medium / blog articles often lose nuance that the README preserves. If the article is bot-walled or paywalled, the **README IS the article** — read it as the canonical source. Do not ask the user to paste the article.

### Gate 2 — Code-level load-path inspection

Read the actual file(s) that load and use the model. For PyTorch: `model = SomeClass(...)` + `model.load_state_dict(torch.load(MODEL_PATH, ...))` + `model.eval()`. For HuggingFace transformers: `AutoModel.from_pretrained(...)` + `AutoTokenizer.from_pretrained(...)`. For ONNX: `ort.InferenceSession(...)`. For TFLite: `tf.lite.Interpreter(...)`.

Extract and tabulate:

| Field | Value | Source |
|---|---|---|
| `NUM_LABELS` / `num_classes` | integer | constants or config |
| `MAX_SEQ_LEN` / `max_position_embeddings` | integer | config dataclass or argparse |
| `LABELS` dict / label mapping | name → index | constants or yaml |
| `MODEL_PATH` env var default | string path | env var block |
| `TOKENIZER_PATH` env var default | string path | env var block |
| `CONFIDENCE_THRESHOLD` default | float | agent config |
| `FALLBACK_LABEL` default | string | agent config |
| `device` resolution | cuda / cpu / mps | runtime check |

### Gate 3 — Shipped-checkpoint-vs-claimed-class-count gate (the silent killer)

**This gate is the load-bearing one.** It catches the `NUM_LABELS=4 in code, NUM_LABELS=6 in weights` class of bug. The recipe:

```python
import torch
sd = torch.load('<model_path>', map_location='cpu', weights_only=False)
# Find the classifier head's weight tensor (last linear layer's W)
# Typical names: 'classifier.3.weight', 'classifier.classifier.weight',
# 'head.weight', 'output.weight', 'pooler.dense.weight'
for k, v in sd.items():
    if 'classifier' in k.lower() or 'head' in k.lower() or 'output' in k.lower():
        if v.ndim == 2:
            print(k, v.shape)  # should be (NUM_CLASSES, HIDDEN_DIM)
            break
```

If the head shape does NOT match the claimed `NUM_LABELS`, **the repo is broken end-to-end**. The FastAPI server will raise on load. **Surface this in the verdict as a 🔴 red finding**, not as a paper-over. Two possible resolutions:

1. **Update `NUM_LABELS` in code** to match the checkpoint. This unblocks inference but breaks the documented label mapping — you don't know what indices 4, 5, etc. mean unless the vendor published a separate label dictionary.
2. **Re-train or re-export** the checkpoint to match the documented label set. This unblocks the documented label mapping but requires the vendor's training code.

Either way, do not adopt the repo as-is. Surface this to the user before any deployment.

### Gate 4 — Per-turn architecture boundary check

Most vendor routers are **per-turn**, not per-conversation. Verify by checking:

- `MAX_SEQ_LEN` / `max_position_embeddings` / `truncation` defaults — if it's small (e.g. 128, 512), the model silently truncates anything longer.
- The API contract (`POST /classify` or `POST /chat` or `POST /route`) — does it accept a single query, a list of queries, or a multi-message conversation?
- The model architecture — bidirectional encoders (BERT, RoBERTa, MiniMax-M3-embed) are per-segment. Causal decoders (GPT, LLaMA) are autoregressive. Long-context variants (Longformer, BigBird, RoPE-extended) are the only ones that can do whole-convo.

If the user asked "does it pass in the whole convo" and the architecture is per-turn, **the answer is no, by design**. That's not a bug; that's the wrong product. Don't recommend a per-turn router for a whole-convo problem; recommend a different product.

### Gate 5 — On-distribution label-coverage audit

The vendor's published label set may not match the user's actual task distribution. Mine the user's past session_search for ~30-100 recent real prompts and bucket them by task type. Compare that distribution against the vendor's class taxonomy.

Example from the 2026-07-22 incident: the vendor's 4-class taxonomy was `{simple_no_pii, simple_pii, complex_no_pii, complex_pii}`. The user's real distribution was roughly `{git/CLI ops, Slack digests, AO orchestration, CSS/UI, PR review, beads, memory/skill management}`. **Zero overlap.** Even if the model classifies perfectly, the routing decisions don't help — a `gh pr view` query routed to "small model" is wrong because the user already prefers the long-context model for that query type.

Recipe:

1. Mine `session_search` for the user's top 5-10 active projects over the last 30 days.
2. Extract the first user prompt from each session.
3. Bucket them by hand-labeled task type (you can use a quick LLM call to label them in batches, or eyeball it for 30-50 prompts).
4. Compare the bucket distribution to the vendor's label taxonomy.
5. Flag as 🟡 if <30% of user tasks have a natural mapping to a vendor class; flag as 🔴 if <10%.

### Gate 6 — Realistic cost-cut estimate for YOUR workload

Vendor headline numbers are measured on **the vendor's workload**, not yours. The 60% cost cut on `deycoding-compliance-classifier-router` is a BFSI banking-chat figure — your dev-ops / Slack-digest / browser-automation distribution won't see the same savings.

Recipe for a realistic estimate:

1. Look at the vendor's cost-cut derivation: it's typically `(small-model-cost * %-small-traffic) + (large-model-cost * %-large-traffic) - routing-overhead`.
2. Estimate your %-small-traffic by applying Gate 5's bucket distribution to the vendor's small/large routing rules.
3. Estimate routing overhead (typically 5-15ms per request).
4. Compare against your **current** cost distribution (large model for everything → 100% large cost).
5. Realistic savings on a non-matching workload: **5-20%**, not the vendor's headline.

Be honest with the user about this. A 60% saving on the vendor's workload is a marketing number; a 10-20% saving on yours is the engineering reality. Do not adopt based on the vendor's figure.

## Verdict shape (mandatory)

Every eval run ends with a verdict in this shape:

```
🔴 / 🟡 / 🟢  verdict on whether to adopt

- Headline finding: <the single most damning or interesting thing the eval turned up>
- Gate-by-gate: 1-6 with pass/fail and one-line evidence
- Realistic cost-cut for your workload: <number>%
- Recommendation: adopt / fork-and-patch / do-not-adopt / build-our-own
- Proof: <path to eval report, raw logits, log dump>
```

If the verdict is "do not adopt" or "fork-and-patch", also include a one-line "what would change my mind" or "what fork-and-patch requires". The user wants to know the minimum delta that would make adoption viable.

## Anti-patterns (do not do)

- ❌ **"Trust the README."** The README is the first source of truth, not the only one. Always triangulate with code + weights + behavior.
- ❌ **"Trust the headline accuracy."** Headline accuracy is measured on the vendor's test set. Your distribution is different. Gate 5 catches this.
- ❌ **"Skip Gate 3 because the README says it works."** Gate 3 is the silent killer. The 2026-07-22 incident proves a vendor can ship a README that documents the wrong number of classes while the shipped weights have the right (different) number.
- ❌ **"Classify the user's data and report accuracy."** Without Gate 5's label-coverage audit, the accuracy number is meaningless — you're measuring how well the model classifies into a taxonomy the user doesn't actually use.
- ❌ **"Recommend adoption if the architecture sounds right."** Architecture rightness ≠ workload rightness. The same router can be production-grade for BFSI and a bad fit for engineering dev work.
- ❌ **"Stall on a pre-execution menu."** When the user says "evaluate this, replay my convos, are the choices right", execute the verbs in sequence. See `finish-the-job` `references/eval-stall-on-preflight-menu-2026-07-22.md`.

## Support files

- `scripts/check_checkpoint_class_count.py` — Gate 3 reproducer. Detects PyTorch / HuggingFace classifier heads, walks the state_dict or config, and reports (or asserts, with `--expected N`) the class count. Catches the 2026-07-22 incident's class of bug in one command: `python3 scripts/check_checkpoint_class_count.py <model_path> --expected 4`. Exit 0 = pass, exit 1 = mismatch.

## Cross-references

- `finish-the-job` — the eval-stall anti-pattern (pre-execution menu) was patched there with a companion reference.
- `verify-deployed-frontend-fix` — three-layer proof pattern (merged code + bundle hash + runtime computed style) is analogous: Gate 1 (README) + Gate 2 (code) + Gate 3 (weights) + Gates 4-5 (runtime behavior + coverage).
- `cli-env-var-verification` — binary-string grep on compiled executable + official vendor docs + live process test + config-file presence. Same triangulation discipline, applied to env vars instead of model artifacts.
- `convergent-bug-triage` — for when the eval surfaces multiple sibling issues (e.g. three separate failures all traceable to the same root cause like the class-count mismatch).
- `pr-description-validator-gate6b` — same gate discipline (read-the-validator-locally, don't trust the headline PASS/FAIL summary), applied to PR description validators instead of model artifacts.

## Worked example — the 2026-07-22 incident

User asked: *"clone this locally and evaluate it. Does it pass in the whole convo for classification? Can we replay it against some of my older convos/projects to see what it would choose and if the choices right?"* with a Medium link.

Phase 0: Classified as vendor-ml-artifact-eval (no existing skill covered this class). Loaded this skill.

Gate 1 (README-vs-claim): Cloned `deycoding/deycoding-compliance-classifier-router`. README documents `NUM_LABELS=4` (simple_no_pii / simple_pii / complex_no_pii / complex_pii), `MAX_SEQ_LEN=128`, ~140M params, ~7ms GPU latency, 99.2% accuracy.

Gate 2 (code-level load path): `server/server.py:18-19` shows `NUM_LABELS = 4; LABELS = {0: "simple_no_pii", 1: "simple_pii", 2: "complex_no_pii", 3: "complex_pii"}`. `MAX_SEQ_LEN = 128` at line 17. `model.load_state_dict(torch.load(MODEL_PATH, ...), weights_only=False)` at line 118 — note `weights_only=False` (security smell, but not the issue here).

Gate 3 (checkpoint-vs-claimed-class-count): Loaded the model weights from HuggingFace. The final classification layer `classifier.3.weight` has shape `torch.Size([6, 768])`. **MISMATCH.** The shipped code wants `NUM_LABELS=4` but the shipped weights have a 6-class head. `load_state_dict` will raise. **🔴 Block.**

Gate 4 (per-turn architecture boundary): `MAX_SEQ_LEN=128` tokens. README example for `Design fraud detection system for UPI transactions` (8 tokens) fits; `Read my convo history to see what wasn't optimal...` (65 tokens) fits but is heavily truncated; a full conversation thread (2000-4000 words) does NOT fit. **The model cannot do whole-convo classification. Different product.**

Gate 5 (on-distribution label coverage): Mined 8 real past Jeffrey prompts via `session_search`. Buckets: `git/CLI ops` (3), `AO orchestration` (2), `Slack digests` (1), `PR work` (1), `other` (1). Vendor's 4-class taxonomy (complexity × PII) has **zero direct overlap** with this distribution. Routing a `git push origin <branch>` to "small model" because it has no PII is wrong.

Gate 6 (realistic cost-cut estimate): Vendor's 60% figure is BFSI-derived. Engineering dev workload (long-context code review, file diff analysis, multi-file refactors) overwhelmingly wants the long-context model — the small-model tier wouldn't even fit most past prompts in its 128-token context window. Realistic estimate for the user's actual distribution: **10-20%**, not 60%.

**Verdict:** 🟡 *workable compliance-routing primitive; **does not, and cannot, do whole-conversation classification** as the user asked; shipped code and shipped weights are out of sync; not ready for drop-in. Recommend fork + re-train on a task-type taxonomy matching the user's session distribution (~2-week AO dispatch).*

**Proof:** Eval report at `~/projects/router-eval/EVAL_REPORT.md` (16 KB). Raw logits at `/tmp/router_eval_results.json`. Model weights + tokenizer at `~/projects/router-eval/deycoding-compliance-classifier-router/server/deycoding.compliance-classifier-in-1-0.{pt,json}`. Reproducer recipe documented in the report.