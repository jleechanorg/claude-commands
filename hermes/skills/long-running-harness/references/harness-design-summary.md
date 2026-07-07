# Harness Design for Long-Running Apps — Key Points

Source: https://www.anthropic.com/engineering/harness-design-long-running-apps (March 24, 2026)
Author: Prithvi Rajasekaran, Anthropic Labs

## Two Core Problems

1. **Subjective quality evaluation** — How do you grade "is this design good?" reliably?
2. **Long-running autonomous coding** — How do you keep an agent coherent over multi-hour sessions?

## Failure Mode 1: Context Anxiety

Models lose coherence as context fills. Some models (especially Sonnet 4.5) exhibit "context anxiety" — wrapping up work prematurely as they approach their context limit.

**Solution: Context Resets**
- Clear the context window entirely
- Start a fresh agent with a structured handoff artifact
- The handoff carries previous agent's state + next steps

**Why not compaction?**
Compaction summarizes in-place. It preserves continuity but doesn't give a clean slate — context anxiety can still persist. A reset provides a clean slate at the cost of requiring the handoff artifact to have enough state.

## Failure Mode 2: Self-Evaluation

Agents grade their own work too generously — even on objective tasks.

**Solution: Separate Generator and Evaluator (GAN-inspired)**
- Generator agent produces the work
- Evaluator agent grades it independently
- The evaluator is tuned for skepticism
- Feedback loop: evaluator critiques → generator iterates → evaluator re-grades

**Key insight:** Tuning a standalone evaluator for skepticism is far more tractable than making a generator self-critical.

## The Three-Agent Architecture

1. **Planner** — Decomposes spec into task list
2. **Generator** — Implements tasks one at a time, hands off artifacts between sessions
3. **Evaluator** — Grades output against explicit criteria

## Frontend Design Lessons

- "Is this design beautiful?" is unanswerable consistently
- "Does this follow our principles for good design?" gives concrete grading criteria
- Develop a rubric that encodes design principles
- Generator + Evaluator feedback loop drives toward stronger outputs

## Long-Running Coding Lessons

1. **Decompose the build into tractable chunks** — one feature at a time
2. **Use structured artifacts to hand off context** — not just chat summaries
3. **Context resets are essential** — compaction alone wasn't sufficient for Sonnet
4. **Separate evaluation from generation** — always
5. **The "Ralph Wiggum" method** (continuous iteration via hooks/scripts) works but has limits

## Implications for Our Harness

1. We MUST do context resets for long tasks (not just compaction)
2. The evaluator must be a separate agent, never the generator grading itself
3. Handoff artifacts need enough state for the next agent to pick up cleanly
4. One feature per session — don't overload a single executor run
