# Harness Guardrails (Added from Bug Analysis)

These guardrails are derived from recent bug classes and regressions in the WorldArchitect engine.

- **Vanilla JS Event Listeners:** Do not use `.bind(this)` inline within `addEventListener` or `removeEventListener`. Always store the bound function reference in the class constructor or initialization block to ensure proper removal and avoid memory leaks or dangling listeners (e.g. `this.boundHandleClick = this.handleClick.bind(this)`).
- **Administrative State Poisoning:** Any administrative override feature (e.g., God Mode, Pre-populated Templates) that bypasses standard LLM state-transition flows MUST explicitly enforce cleanup for orthogonal game states (like `in_combat=False` or `character_creation_in_progress=False`). 
- **DRY Constant Extraction:** When modifying logic that relies on hardcoded lists or tuples (like stripping cooldown fields), you MUST search the repository for duplicates and extract them to a canonical constant to prevent `NameError` hazards during rebases.
