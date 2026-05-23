---
description: "/factory — run the Dark Factory DOT pipeline runner against a goal"
type: quality
execution_mode: immediate
aliases: [df]
---

# /factory — Dark Factory DOT Pipeline Runner

Dispatches to the `dark-factory` skill, which shells out to the Python
Attractor-pattern pipeline runner in `~/projects/dark-factory/`.

Unlike `/h` (which runs the 4-gate harness as in-Claude subagent dispatch),
`/factory` runs the *external* `.dot`-driven pipeline. The pipeline definition
itself is the versionable artifact — the `.dot` file in
`pipelines/factory/` describes the workflow as a directed graph.

**Usage**:

```
/factory <goal description>                       # default: gates.dot, feature=hello
/factory --pipeline gates <goal>                  # explicit pipeline
/factory --pipeline hello --feature hello <goal>  # implement loop + holdout
/factory --backend echo <goal>                    # no LLM, deterministic
```

## Action

Run the `dark-factory` skill with `$ARGUMENTS`.
