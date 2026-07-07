# Annotation Cycle Workflow — Key Points

Source: https://boristane.com/blog/how-i-use-claude-code/ (February 10, 2026)
Author: Boris Tane

## Core Principle

**Never let Claude write code until you've reviewed and approved a written plan.**

This separation of planning and execution is the single most important thing. It prevents wasted effort, keeps you in control of architecture decisions, and produces significantly better results with minimal token usage.

## The 6-Phase Workflow

```
Research → Plan → Annotate → Todo List → Implement → Feedback & Iterate
                      ↑_________________________|
                         repeat 1-6x
```

## Phase 1: Research

- Start with a deep-read directive
- **Force depth** — use "deeply", "intricacies", "all specificities", "go through everything" in prompts
- Without these words, Claude will skim — signature-level only
- **Write to a persistent markdown file** (`research.md`), never just chat
- The written artifact is your review surface — verify Claude understood before planning

> "This is the most expensive failure mode with AI-assisted coding: implementations that work in isolation but break the surrounding system."

## Phase 2: Planning

- Ask for a detailed implementation plan in a **separate markdown file** (`plan.md`)
- Plan should include: approach explanation, code snippets, file paths, trade-offs
- **Use your own `.md` plan files, not Claude Code's built-in plan mode** (the built-in mode "sucks")
- **Reference implementation trick**: paste good open-source code and ask Claude to plan how to adopt a similar approach — dramatically better results

## The Annotation Cycle (THE KEY INSIGHT)

After Claude writes the plan:

1. Open `plan.md` in your editor
2. **Add inline notes directly into the document** — correct assumptions, reject approaches, add constraints, provide domain knowledge
3. Send Claude back to the document: "I added notes to plan.md. Read them and update the plan accordingly. Do NOT start coding yet."
4. Repeat until satisfied

**Why this works:**
- The markdown file is a **shared working surface** between you and Claude
- You annotate at your own pace, precisely where something is wrong
- Much better than steering through chat messages (scrolling to reconstruct decisions)
- Three rounds of annotation can transform a generic plan into one that fits perfectly

## Critical Guard

**The explicit "do NOT start coding yet" guard is essential.** Without it, Claude will jump to code the moment it thinks the plan is good enough.

## Phase 4: Todo List

Before implementation, request a granular task breakdown:
- Each item should be small enough to verify independently
- Include file paths and expected changes per item

## Phase 5: Implementation

- Implement one todo at a time
- After each: verify, run tests, check against plan
- If something breaks the system → stop and fix, don't push through

## Phase 6: Feedback & Iterate

- Review the output against the plan
- If quality is poor: specific feedback → re-implement
- If quality is good: ship

## Implications for Our Harness

1. The annotation cycle is the mechanism for human-in-loop quality control
2. Persistent markdown artifacts beat chat messages for steering
3. "Don't code yet" must be enforced by the orchestrator, not just by prompt
4. Reference implementations dramatically improve plan quality
5. Research quality determines everything downstream — invest in depth
