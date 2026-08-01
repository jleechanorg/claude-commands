# Local execute-plan vs Cloud Build — when to use which

**Source:** distilled from user Q&A in Slack thread `C09GRLXF9GR/p1784573431` (2026-07-20). Same `plan.md` flows through both paths; the deltas are in identity, observability, failure recovery, cost, network reach, and enforcement.

## What's the same

- Same `plan.md` input
- Same Superpowers skills (TDD, brainstorming, code review) driving the engine
- Same `git` workflow, same PR-shaped output
- Same hermeticity expectation (tests must pass)

## 6 axes that differ

### 1. Where the LLM runs
| | Local execute-plan | Cloud Build |
|---|---|---|
| Process | Subagent in this Claude/Codex session | Box behind `cloud.superpowers.build:22` |
| Machine | Yours | Prime Radiant's |
| Identity | Your git author | `Cloud Build <supervisor@cloud-build.local>` |
| Model | Whatever your harness uses (you pick) | Whatever the box runs (verified runs used GLM-5.2 on `serf` harness — not your choice) |

### 2. Visibility
| | Local | Cloud Build |
|---|---|---|
| Live transcript | Yes — in your session | No — only `cloud/status` JSON |
| Mid-run intervention | Yes — pause, redirect, inject context | No — except via `needs_input` Q&A (`qid`/`prompt`/`mk_answer`) |
| Failure diagnosis | Direct — read traceback | Wire-only — must `git fetch` the box's branch + parse status JSON |
| Output | Full conversation + diffs | Git commits + status JSON + log file |

### 3. Failure recovery
| | Local | Cloud Build |
|---|---|---|
| Retry on transient failure | Unlimited — you decide | **One** bounded replay, only on the exact standalone marker `cloud-bastion: CLOUD_BUILD_RETRYABLE=provisioning_timed_out`. Every other failure is final. |
| Pause / abort | Free (Ctrl-C, /stop) | `cloud_build_mk_abort` — but box reaper still fires on idle/lifetime cap |
| Cost of failure | Lost minutes | Lost minutes + box provisioning cycle (60-120s) |

### 4. Cost model
| | Local | Cloud Build |
|---|---|---|
| LLM tokens | Your OpenAI/Anthropic/MiniMax budget | Prime Radiant's (invite-only — token-credited or metered) |
| Compute | Your box | Their box |
| Model choice | You pick | They pick (verified: GLM-5.2; no bill visibility, no downgrade) |

### 5. Network reach
| | Local | Cloud Build |
|---|---|---|
| Outbound | Your machine's network (any API you can reach) | Box's network — likely no outbound to your private infra, internal services, or non-allowlisted APIs |
| Git remote access | Your credentials | Box's credentials (the SSH identity you enrolled) |
| Implicit assumption | Can call whatever | **Hermetic** — preflight refuses projects with external secrets or services (`CLOUD_HERMETIC_CONFIRMED=1` is the operator's sign-off) |

### 6. Enforcement
| | Local | Cloud Build |
|---|---|---|
| Branch policy | Whatever you push | Server rejects `feat/*`/`fix/*` — only `refs/heads/private/*` accepted |
| Secret guard | Depends on your pre-push hooks | Server-side git secret guard walks the push range; tracked secrets in history → push blocked (the #1 real-world blocker) |
| Hermeticity | Soft — "tests pass, ship it" | Hard gate — `preflight-local.sh` fails closed without `CLOUD_HERMETIC_CONFIRMED=1` |

## Decision rule

> **Cloud Build is `subagent-driven-development` running on someone else's machine with a different identity, no live observability, one bounded retry, hermetic-only, branch-restricted, and a model you didn't pick.**

## When to use which

| Use local execute-plan when… | Use Cloud Build when… |
|---|---|
| You want to see the trace | You trust the plan and want async handoff |
| The work needs internal services / private APIs | The work is hermetic (lint + tests in the repo, nothing external) |
| You want model choice / model fallback | You don't care which model runs the box |
| Failure debugging will be iterative | The plan is solid enough that one replay is fine |
| Commit identity matters (you want to own the commits) | You WANT the audit trail showing "Cloud Build, not human" (compliance / SOC2 / attribution) |
| You have ≤5min budget for the run | You're OK with 60-300s provisioning on top of execution time |
| Branch is `feat/*` or `fix/*` | You're happy to land on `private/*` first, then port to the real branch |

## Real-world examples (verified on $GITHUB_REPOSITORY)

- **[PR #8476](https://github.com/$GITHUB_REPOSITORY/pull/8476)** (auto-level-up foundation, +1360/-289) — Cloud Build because: plan was solid (3-PR design consult from 2026-06-26, well-scoped), tests are hermetic (`pytest` in `$PROJECT_ROOT/tests/`, no external services), long-running coding session (4 commits, multiple CodeRabbit rounds, all headless), user wanted async + audit-trail attribution.
- **[PR #8466](https://github.com/$GITHUB_REPOSITORY/pull/8466)** (HTTP 500 wire-boundary fix, +318/-0) — Cloud Build because: tight scope (318 lines), hermetic test suite, user wanted the first cloud-build-coded change to be small + obviously correct.
- Typical `/af` 7-green-gate fleet drives — **stay local** because the gate iteration loop needs live observability and adaptive retries that Cloud Build's one-replay budget can't accommodate.

## Common misconception to push back on

If a user says "let's run this plan on the cloud so we don't have to babysit it" — that's usually wrong unless the plan is also hermetic and well-tested. Cloud Build trades observability for async execution; if the work needs mid-run steering, local will be faster end-to-end despite the babysitting.

If a user says "cloud build is just like running locally but remote" — correct them: the model, the retry budget, the network reach, and the branch policy are all different. Cloud Build is a constrained execution environment, not a peer of your local harness.
