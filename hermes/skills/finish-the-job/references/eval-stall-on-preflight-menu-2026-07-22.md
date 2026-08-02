# Eval-stall on preflight menu — 2026-07-22

**Skill:** `finish-the-job` (new pitfall appended)
**Verified incident:** 2026-07-22, vendor-router eval (`deycoding/deycoding-compliance-classifier-router`)
**Trigger:** user types a goal with 3+ clear verbs and the agent stalls on a preflight menu before doing the work
**User feedback (verbatim):** "Go and you should be able to use headless chrome and why did you even stop? you shouldnve just done the work"

## What happened

User asked three things in one message:
1. **"clone this locally and evaluate it"** — clone the linked Medium article's repo
2. **"Does it pass in the whole convo for classification?"** — verify the model can do whole-convo classification
3. **"Can we replay it against some of my older convos/projects to see what it would choose and if the choices right?"** — run the model on past conversation prompts and judge whether its routing choices are correct

The agent stalled twice before doing the work:

1. **First stall (Phase 0 menu):** Posted 4 questions before any tool call: "should I clone even though Medium is bot-walled?", "should I try headless chrome?", "which project for the replay?", "per-turn mode or whole-convo mode or both?". The user's answer: *"Go and you should be able to use headless chrome and why did you even stop? you shouldnve just done the work"*.

2. **Second stall (Phase 2 menu):** Even after the user's go-ahead, the agent posted another 2-option menu about which mode to test. The user had already supplied the goal with enough specificity; the agent was asking for permission to interpret it.

## What the agent should have done instead

Three calls into the goal were already mapped out, all of them:

1. `git clone https://github.com/deycoding/deycoding-compliance-classifier-router.git` — find the repo, clone it. The Medium article title is enough to identify the canonical repo (GitHub search confirmed it).
2. `read_file` on the README.md — the README is the article's equivalent content for the model architecture, label set, deployment story, and accuracy claims. **When the article is bot-walled, the README IS the article.** Don't ask the user to paste it.
3. `pip install torch tokenizers huggingface_hub` + `hf_hub_download` to get the model + tokenizer in a venv. Then `m.load_state_dict()` and run.

The "which project for the replay?" question was unnecessary because `session_search` had the answer in one call: the recent sessions in `jleechanclaw`, `your-project.com`, `dark-factory`, and `agent-orchestrator` were all in the Slack-digest topic already loaded in context. The agent had the data; it just hadn't run the search.

The "per-turn vs whole-convo" question was a real fork — but the right move was to **answer it inline** in the report ("the model has MAX_SEQ_LEN=128 tokens, so whole-convo is architecturally impossible; here's what per-turn shows") rather than to ask the user. That's exactly the user's rule from `finish-the-job`: "correct but misinterpret is fine but stopping halfway is not."

## Recipe — when the goal has 3+ verbs and zero data gaps

1. **Read the goal.** Extract every verb. Each verb is one tool call or one tight sequence.
2. **Check the data sources.** For each verb, can it be done with available tools + already-loaded context? If yes, queue it. If no, queue it with a fallback (e.g. Medium bot-walled → README is the article equivalent).
3. **If everything is queued and there's no fork that needs the user**, EXECUTE. Don't post a menu.
4. **If there's a fork that genuinely needs the user** (destructive op, secrets, env-specific config), post **ONE clarifying question**, not a 4-option menu. The user has already paid the up-front Q&A cost by writing the goal — they want execution, not a Phase 0 questionnaire.
5. **Surface judgment calls in the final reply, not in the pre-execution menu.** "I picked X over Y because Z; if you wanted Y, here's the one-line revert" — that's a sentence in the verdict, not a separate message before any work happens.

## What this is NOT

- This is not "always execute without asking." Some goals genuinely need a Phase 0 clarification — when the scope is genuinely ambiguous (3+ reasonable interpretations of the same prompt), when the operation is destructive, when the agent needs secrets only the user has. The Phase 0 question exists for those cases.
- This is not "skip the README." The README is the canonical source of truth when the article is bot-walled. Read it. Mine it for the architecture claims, label set, deployment story, and accuracy claims — those are what an "evaluation" needs.
- This is not "don't post menus at all." When the agent has run the work and hit a fork mid-stream (e.g. `ao spawn` returned `INTERNAL_ERROR`, or the repo has no license file, or the deployment requires AWS credentials the agent doesn't have), the menu is appropriate. The user wants the verdict, not the pre-execution questionnaire.

## How `finish-the-job` already had this rule (and we missed it)

The skill's Phase 0 row says:
> "If the classification is ambiguous after 30 seconds, ASK ONE QUESTION (the only question in this whole pipeline). The user is willing to invest up-front in Q&A specifically to avoid mid-stream steering."

And the existing anti-pattern (verbatim):
> ❌ **"Here's a design with 3 options, which would you like?"** — that's Phase 0 question-count inflation. ONE option (your best judgment) + the path forward. The user's rule: "correct but misinterpret is fine."

The 2026-07-22 incident is the same anti-pattern but at a different stage: instead of posting 3 design options for the user to pick, the agent posted **3 pre-execution questions** before any tool call. Same shape: question-count inflation. Different stage: pre-execution menu vs mid-execution menu.

## Cross-references

- `finish-the-job` Phase 0 row: "If classification is ambiguous after 30 seconds, ASK ONE QUESTION."
- `finish-the-job` anti-pattern: "Here's a design with 3 options, which would you like?"
- `no-confirmation-gate` (SOUL.md): forbids pre-tool-call confirmation gates — applies to `What about this? / Want me to? / Should I?` patterns. The preflight menu violates the same rule.
- New companion skill `vendor-ml-artifact-eval` — the actual evaluation recipe for the class of task this stall was about.

## Verified end-state

After the un-stall, the agent did:

- Cloned to `~/projects/router-eval/deycoding-compliance-classifier-router/` (10 files, ~22 KB of Python + 24 KB README).
- Built a CPU-only PyTorch env in `server/.venv/` (torch 2.13.0, tokenizers 0.23.1).
- Downloaded model weights (441 MB) + BPE tokenizer (2.3 MB) from HuggingFace.
- Ran inference on 11 prompts (6 real past Jeffrey prompts + 4 README-canonical examples + 1 PII test prompt), saved to `/tmp/router_eval_results.json`.
- Discovered the headline finding: **`NUM_LABELS=4` in `server/server.py` vs `NUM_LABELS=6` in the shipped checkpoint** — the repo as-checked-in does not run end-to-end on the shipped weights, and the README's 4-class label mapping does not match the 6 indices in the trained head.
- Wrote `~/projects/router-eval/EVAL_REPORT.md` (16 KB) with per-prompt logit dumps + failure traces + recommended next steps.
- Posted a 4-paragraph Slack verdict with the headline finding, the realistic cost-cut estimate (10-20%, not 60%), and a follow-up offer to spawn an AO worker to build a real router.

The work landed in one session once the stall was broken. The cost was 1 user message + 1 un-stall message + 1 verdict message, ~25 tool calls (well under the 25-call budget concern). No `/finish` required.

## What this means for future sessions

When you read a user goal and find yourself reaching for `clarify` because you have **multiple parallel questions**, ask yourself first:

1. Is each question blocking on data I don't have? If yes → run the tool first to get the data, then maybe ask.
2. Is each question blocking on user preference with no reasonable default? If yes → make the call, surface it in the verdict, post the callout.
3. Is each question blocking on secrets / destructive ops / env config? If yes → that's the **one** legitimate Phase 0 question; post the other questions as part of the verdict if needed.

If only #3 applies, post one question. If 1-2 apply to most of your menu, **don't post the menu — just execute**.