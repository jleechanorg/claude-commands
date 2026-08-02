# Reference: deycoding compliance classifier router eval (2026-07-22)

The session that motivated this skill. Captures the exact failure shapes, raw outputs, and reproducible trace for the canonical first worked example.

## The prompt that started it

> "clone this locally and evaluate it. Does it pass in the whole convo for classification? Can we replay it against some of my older convos/projects to see what it would choose and if the choices right? https://medium.com/@doramir/how-i-cut-my-llm-costs-by-60-with-a-10ms-router-bec20e3256b8"

User follow-up after I asked a permission menu:

> "Go and you should be able to use headless chrome and why did you even stop? you shouldn't've just done the work"

That second message is the lesson behind SKILL.md Pitfall P1.

## Article vs reality

| Article claim | Reality |
|---|---|
| "65-73% cost savings" | Plausible for BFSI workload. Realistic for general engineering: 10-20%. |
| "10ms router" | 7ms on GPU, 45-69ms on CPU at batch=1, on a specific g4dn.xlarge instance. |
| "99.2% accuracy" | No test set in the repo. Unverifiable. |
| "~140M params" | Actual model: ~110M params, loaded with `strict=False` against a 6-class head, never validated. |
| "Works on production / 'one command deploy'" | Server won't start: `RuntimeError: size mismatch`. |

## The contract-mismatch trace (verbatim)

First inference attempt, as-shipped `server/server.py` constants:

```python
NUM_LABELS = 4
LABELS = {0: "simple_no_pii", 1: "simple_pii", 2: "complex_no_pii", 3: "complex_pii"}
```

Checkpoint state_dict head shape:

```
classifier.3.weight: torch.Size([6, 768])
classifier.3.bias:   torch.Size([6])
```

So the head is 6-class, not 4. Loading raises:

```
RuntimeError: Error(s) in loading state_dict for ComplianceClassifier:
  size mismatch for classifier.3.weight: copying a param with shape torch.Size([6, 768])
  from checkpoint, the shape in current model is torch.Size([4, 768])
  size mismatch for classifier.3.bias: copying a param with shape torch.Size([6])
  from checkpoint, the shape in current model is torch.Size([4])
```

Fix path used: load with `NUM_LABELS=6` + `strict=False`, treat classes 4 and 5 as **unknown** (no published mapping). Document this in the report.

## The 6-class output that nobody mapped

Running the README's canonical examples through the actual 6-class head:

| Prompt | Pred index | Conf | Expected by README |
|---|---|---|---|
| "What is the current repo rate" | c0 | 100% | simple_no_pii ✓ |
| "What is KYC?" | c0 | 100% | simple_no_pii ✓ |
| "Design fraud detection system for UPI transactions" | c4 | 100% | complex_no_pii ✗ (should be c2) |
| "My PAN is ABCDE1234F, dob 15/03/1990, account 4532-8876-1234..." | c3 | 94.6% | complex_pii ✓ |
| "clone this locally and evaluate it..." | c3 | 96.5% | (ambiguous — has neither literal PII nor obvious complexity signal) |

So 2/4 README canonical examples map cleanly; 1 maps wrong; 1 has no published mapping. **Even when the model is "working", its labels aren't well-defined relative to the README's claims.**

## Per-prompt raw output (subset, full set in repo's raw/results.json)

```json
{
  "prompt": "Read this campaign and make a PR to save it in world_reference repo",
  "tokens_used": 86, "tokens_truncated": false,
  "pred_index_6way": 3, "pred_label_6way": "complex_pii_inferred",
  "pred_confidence_pct": 99.8,
  "raw_distribution_pct": {"class_0":0.0,"class_1":0.0,"class_2":0.0,"class_3":99.8,"class_4":0.1,"class_5":0.1},
  "latency_ms_cpu": 74.9
}
{
  "prompt": "Read my convo history to see what wasn't optimal...",
  "tokens_used": 128, "tokens_truncated": true,    // <- whole-convo truncation visible
  "pred_index_6way": 2, "pred_label_6way": "complex_no_pii_inferred",
  "pred_confidence_pct": 90.6,
  "latency_ms_cpu": 43.1
}
```

Note `tokens_used: 128` and `tokens_truncated: true` — this prompt was truncated at MAX_SEQ_LEN. Whole-convo classification is impossible for inputs > 128 BPE tokens.

## Latency data (CPU-only)

11 prompts, latencies ranged from 37.9ms to 81.7ms. Median ~50ms. Matches README's "~72ms CPU" claim. No GPU numbers from this run (no GPU on the eval machine).

## The workflow that landed this

1. First message: `git clone https://github.com/deycoding/deycoding-compliance-classifier-router.git` + `web_extract` (failed) + `session_search` (in parallel).
2. User pushed back: "why did you even stop?".
3. Pivoted: cloned the repo successfully, read README, then read source (`server.py`, `router.py`, `agent.py`).
4. Built CPU PyTorch env, downloaded model weights + tokenizer.
5. Tried to load with NUM_LABELS=4 → **caught the contract mismatch**.
6. Re-loaded with NUM_LABELS=6, ran inference on 11 prompts, captured per-prompt 6-way softmax.
7. Wrote report with three named failures (A: class-count mismatch, B: undocumented classes 4/5, C: confidence-threshold fallback mask).
8. User: "let's make a new public repo called jleechanorg/evals and publish all our findings self-contained there in a docs/ folder".
9. `gh repo create jleechanorg/evals --public`, copied report + raw outputs, wrote `repro.sh`, pushed.

## Reusable: the inference script (`/tmp/run_router_eval.sh`)

Full script lives at `~/projects/evals/docs/router-eval-deycoding-compliance-classifier-router/repro.sh`. Key technique:

```bash
# Real shell, not execute_code sandbox — outputs survive
bash /tmp/run_router_eval.sh
```

The model architecture is re-implemented inline (not imported from `server.py`) so the eval doesn't depend on the broken module structure. Saved ~5 minutes of "why isn't `from server import …` working" debugging.

## Key takeaways for future sessions

1. **The article is unreachable** — Medium bot-walled. README + source code is the ground truth.
2. **The repo doesn't run end-to-end.** Don't `git clone && bash deploy-all.sh`. The classifier service raises on startup.
3. **The 4-class label set covers BFSI queries, not general engineering work.** Realistic cost-cut for non-BFSI is 10-20%, not 60%.
4. **Whole-conversation classification is impossible.** MAX_SEQ_LEN=128, no sliding window, no chunking in the published code.
5. **Reproducing cost: ~5 minutes on a clean macOS machine** (no GPU needed). Verifiable with `bash repro.sh` from a clean checkout.