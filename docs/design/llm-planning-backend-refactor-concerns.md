# LLM Planning Backend Refactor: Valid Concerns & Action Items

**Document**: Follow-up concerns for PR #3537  
**Date**: 2026-01-15  
**Status**: Action Items for Implementation  
**Related**: [`llm-planning-backend-refactor.md`](./llm-planning-backend-refactor.md)

---

## Overview

This document captures valid technical concerns and missing implementation details that should be addressed before or during implementation of the LLM Planning Backend Refactor. These are **not blockers** but rather **gaps that need specification** to ensure successful implementation.

**Note**: Timeline concerns are excluded per design review feedback. Focus is on technical feasibility and integration details.

---

## 1. Security: Formula Dice & Expression Evaluation

### Concern

The design uses `simpleeval` for formula dice evaluation but doesn't specify security hardening. Expression evaluation with user-controlled or LLM-generated content requires careful sandboxing.

### Risks

1. **Context Injection**: Untrusted data in evaluation context could enable code execution
2. **Known simpleeval Bypasses**: Historical CVEs exist for expression evaluators
3. **Denial of Service**: Complex expressions causing infinite loops or resource exhaustion
4. **Integer Overflow**: No bounds checking on formula results

### Required Specification

#### 1.1 Whitelist Approach

```python
# Allowed functions (whitelist only)
ALLOWED_FUNCTIONS = {
    "min", "max", "abs", "floor", "int", "round", 
    "ceil", "sqrt"  # Add only safe math functions
}

# Allowed operators
ALLOWED_OPERATORS = {
    "+", "-", "*", "//", "%",  # Math operators
    "==", ">=", "<=", ">", "<", "!=",  # Comparison
    "and", "or", "not"  # Boolean logic
}

# Forbidden patterns
FORBIDDEN_PATTERNS = [
    r"__.*__",  # Magic methods
    r"eval\s*\(", r"exec\s*\(", r"compile\s*\(",  # Code execution
    r"import\s+", r"from\s+.*\s+import",  # Imports
    r"open\s*\(", r"file\s*\(",  # File access
    r"input\s*\(", r"raw_input\s*\("  # User input
]
```

#### 1.2 Context Sanitization

```python
def sanitize_context(context: dict) -> dict:
    """Remove dangerous keys, validate values."""
    sanitized = {}
    for key, value in context.items():
        # Reject dangerous keys
        if key.startswith("__") or key in ["eval", "exec", "import", "open", "file"]:
            continue
        
        # Only allow safe types
        if isinstance(value, (int, float, str, bool)):
            sanitized[key] = value
        elif isinstance(value, dict):
            # Recursively sanitize nested dicts
            sanitized[key] = sanitize_context(value)
        # Reject all other types (lists, objects, etc.)
    
    return sanitized
```

#### 1.3 Bounds Checking

```python
# Maximum formula result (prevent huge dice pools)
MAX_FORMULA_RESULT = 1000  # Configurable per operation type

# Maximum execution time
MAX_EXECUTION_TIME = 0.05  # 50ms timeout

# Maximum expression depth
MAX_EXPRESSION_DEPTH = 10

def resolve_formula_dice(formula: str, context: dict) -> DiceResult:
    """Evaluate expressions with security bounds."""
    # 1. Sanitize context
    safe_context = sanitize_context(context)
    
    # 2. Validate formula pattern (no forbidden patterns)
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, formula):
            raise ValueError(f"Forbidden pattern in formula: {pattern}")
    
    # 3. Evaluate with timeout
    evaluator = SimpleEval(
        functions=ALLOWED_FUNCTIONS,
        operators=ALLOWED_OPERATORS,
        names=safe_context
    )
    
    try:
        with timeout(MAX_EXECUTION_TIME):
            result = evaluator.eval(formula)
    except TimeoutError:
        raise ValueError("Formula evaluation timeout")
    
    # 4. Validate bounds
    if isinstance(result, (int, float)):
        if abs(result) > MAX_FORMULA_RESULT:
            raise ValueError(f"Formula result {result} exceeds maximum {MAX_FORMULA_RESULT}")
    
    # 5. Convert to dice notation and roll
    notation = re.sub(r'\{([^}]+)\}', lambda m: str(int(evaluator.eval(m.group(1)))), formula)
    return roll_dice(notation)
```

### Action Items

- [ ] **Specify security whitelist** - Document exact allowed functions/operators
- [ ] **Implement context sanitization** - Add sanitize_context() function
- [ ] **Add bounds checking** - MAX_FORMULA_RESULT, MAX_EXECUTION_TIME constants
- [ ] **Security review** - External security audit of expression evaluator
- [ ] **Add security tests** - Test forbidden patterns, injection attempts, DoS vectors

---

## 2. Edge Cases: Circular Triggers & Resource Conflicts

### Concern 2.1: Circular Trigger Evaluation

**Problem**: Triggers can cause other triggers to fire, potentially creating infinite loops.

**Example**:
```json
{
  "resource_id": "rage",
  "triggers": [
    {
      "condition": "rage < 100",
      "effect": "add",
      "amount": "10"
    }
  ]
}
```

If `rage` starts at 0, this trigger fires → adds 10 → condition still true → fires again → infinite loop.

**Current Design**: Mentions `MAX_TRIGGER_DEPTH = 5` but doesn't specify evaluation order.

### Required Specification

```python
MAX_TRIGGER_DEPTH = 5
MAX_TRIGGER_ITERATIONS = 100  # Total trigger evaluations per event

def evaluate_triggers(
    resource: ResourceDefinition, 
    event: dict, 
    depth: int = 0,
    iteration_count: int = 0
) -> list[TriggerResult]:
    """Evaluate triggers with recursion protection."""
    
    # Stop if depth exceeded
    if depth > MAX_TRIGGER_DEPTH:
        logging.warning(f"Trigger depth exceeded for {resource.resource_id}, stopping")
        return []
    
    # Stop if total iterations exceeded
    if iteration_count >= MAX_TRIGGER_ITERATIONS:
        logging.warning(f"Trigger iteration limit reached, stopping")
        return []
    
    results = []
    
    # Evaluate triggers in order
    for trigger in resource.triggers:
        # Check condition
        if not evaluate_condition(trigger.condition, event):
            continue
        
        # Apply effect
        result = apply_trigger_effect(trigger, resource)
        results.append(result)
        
        # Update event context for next trigger evaluation
        updated_event = {**event, **result.as_event()}
        
        # Recursively evaluate if this trigger caused state changes
        if result.modified_resource:
            nested_results = evaluate_triggers(
                resource, 
                updated_event, 
                depth + 1,
                iteration_count + 1
            )
            results.extend(nested_results)
    
    return results
```

**Evaluation Order Rules**:
1. Triggers evaluate **sequentially** (not in parallel)
2. Each trigger sees the **cumulative state** from prior triggers
3. Recursive triggers evaluate **depth-first** with depth limit
4. Total iteration count prevents infinite loops even with multiple resources

### Action Items

- [ ] **Specify trigger evaluation order** - Sequential vs parallel, state visibility
- [ ] **Document recursion limits** - MAX_TRIGGER_DEPTH, MAX_TRIGGER_ITERATIONS
- [ ] **Add trigger cycle detection** - Detect circular dependencies at registration time
- [ ] **Add trigger tests** - Test circular triggers, deep recursion, iteration limits

---

### Concern 2.2: Resource Definition Conflicts

**Problem**: LLM may attempt to re-register existing resources with different values.

**Example**:
- Backend has `spell_slot_3` with `max_value=2`
- LLM tries to register `spell_slot_3` with `max_value=3`

**Current Design**: Says "backend wins" but doesn't specify merge strategy or conflict resolution.

### Required Specification

```python
def register_homebrew_resource(
    definition: ResourceDefinition, 
    game_state: GameState,
    allow_override: bool = False
) -> OperationResult:
    """Register resource with conflict resolution."""
    
    existing = game_state.resources.get(definition.resource_id)
    
    if existing:
        # Check if definitions match exactly
        if definitions_match(existing, definition):
            return OperationResult(
                success=True, 
                message="Resource already registered with same schema"
            )
        
        # Definitions differ - conflict resolution
        if allow_override:
            # DM authorization check
            if not is_dm_authorized(game_state.campaign_id):
                return OperationResult(
                    success=False,
                    error="DM authorization required to override existing resource"
                )
            
            # Override with warning
            game_state.resources[definition.resource_id] = definition
            return OperationResult(
                success=True,
                warning=f"⚠️ Resource '{definition.display_name}' overridden. "
                       f"Previous: max={existing.max_value}, New: max={definition.max_value}"
            )
        else:
            # Reject with error
            return OperationResult(
                success=False,
                error=f"Resource '{definition.resource_id}' already exists with different schema. "
                      f"Existing: max={existing.max_value}, Attempted: max={definition.max_value}. "
                      f"Use 'modify_resource' operation to change values."
            )
    
    # New resource - register it
    game_state.resources[definition.resource_id] = definition
    return OperationResult(success=True, resource_id=definition.resource_id)

def definitions_match(existing: ResourceDefinition, new: ResourceDefinition) -> bool:
    """Check if resource definitions are equivalent."""
    return (
        existing.max_value == new.max_value and
        existing.recharge_trigger == new.recharge_trigger and
        existing.computed_bonuses == new.computed_bonuses and
        existing.triggers == new.triggers
    )
```

**Conflict Resolution Rules**:
1. **Exact match**: Silent success (idempotent)
2. **Different schema + allow_override=False**: Reject with error message
3. **Different schema + allow_override=True**: Require DM authorization, override with warning
4. **Current value differences**: Always allowed (use `modify_resource` operation)

### Action Items

- [ ] **Specify conflict resolution strategy** - Exact match, override rules, DM authorization
- [ ] **Document definition matching logic** - What fields must match for "same schema"
- [ ] **Add conflict tests** - Test exact match, schema differences, override authorization

---

### Concern 2.3: Mass Combat Mode Transitions

**Problem**: When does system switch from turn-by-turn to mass combat? What if reinforcements arrive mid-fight?

**Example**:
- Player fights 5 goblins → turn-by-turn mode
- Round 3: 15 more goblins arrive → now 20 total
- Should system switch to mass combat mid-fight?

**Current Design**: Doesn't specify transition rules or mid-combat mode switching.

### Required Specification

```python
MASS_COMBAT_THRESHOLD = 6  # Switch to mass combat at 6+ enemies

def should_use_mass_combat(game_state: GameState) -> bool:
    """Determine if mass combat resolution should be used."""
    
    enemy_count = count_enemies(game_state)
    
    # Always use mass combat if threshold exceeded
    if enemy_count >= MASS_COMBAT_THRESHOLD:
        return True
    
    # Check if already in mass combat mode (don't switch back)
    if game_state.combat_mode == "mass":
        return True
    
    # Check if player explicitly requested mass combat
    if game_state.player_preference == "mass_combat":
        return True
    
    return False

def handle_mid_combat_reinforcements(
    game_state: GameState,
    new_enemies: list[dict]
) -> CombatTransition:
    """Handle reinforcements that push combat over threshold."""
    
    current_mode = game_state.combat_mode
    total_enemies = count_enemies(game_state) + len(new_enemies)
    
    if current_mode == "turn_by_turn" and total_enemies >= MASS_COMBAT_THRESHOLD:
        # Transition to mass combat
        return CombatTransition(
            from_mode="turn_by_turn",
            to_mode="mass",
            reason="Reinforcements exceeded threshold",
            preserve_state=True  # Keep current HP/damage
        )
    
    return CombatTransition(no_change=True)
```

**Transition Rules**:
1. **Threshold-based**: Auto-switch at 6+ enemies
2. **Mode lock**: Once in mass combat, stay in mass combat (even if enemies die)
3. **Mid-combat transition**: Preserve current state (HP, damage, conditions)
4. **Player override**: Allow explicit mode selection via planning block choice

### Action Items

- [ ] **Specify mode transition rules** - Threshold, mode lock, mid-combat switching
- [ ] **Document state preservation** - How to preserve HP/damage during transition
- [ ] **Add transition tests** - Test threshold crossing, reinforcements, mode lock

---

## 3. Integration Details: UI, Error Handling, Prompts

### Concern 3.1: UI Display of Operation Results

**Problem**: Design doesn't specify where/how `operation_results` display in the UI.

**Current State**: Players see narrative + `state_updates`. New design adds `operation_results` but doesn't specify UI integration.

### Required Specification

#### UI Component Design

```typescript
// Frontend component for operation results display
interface OperationResultDisplay {
  // Display location: Below narrative, above planning block
  position: "after_narrative" | "before_planning" | "sidebar" | "expandable";
  
  // Display format
  format: "compact" | "detailed" | "minimal";
  
  // Grouping
  groupBy: "operation_type" | "chronological" | "importance";
}

// Example: Fireball operation results
{
  "operation_results": [
    {
      "operation": "consume_resource",
      "display": {
        "icon": "⚡",
        "message": "Spell Slot (3rd Level): Consumed (2 → 1 remaining)",
        "compact": "⚡ -1 Spell Slot (3rd)"
      }
    },
    {
      "operation": "roll_dice",
      "display": {
        "icon": "🎲",
        "message": "Fireball Damage: 8d6 = [4,6,2,5,3,6,1,4] = 31 fire damage",
        "compact": "🎲 31 fire damage"
      }
    },
    {
      "operation": "roll_saving_throw_batch",
      "display": {
        "icon": "🛡️",
        "message": "DEX Saves vs DC 15: 4 passed, 16 failed",
        "compact": "🛡️ 4/20 saved"
      }
    }
  ]
}
```

**UI Requirements**:
1. **Visibility**: Operation results must be visible without scrolling
2. **Grouping**: Group related operations (e.g., all fireball operations together)
3. **Expandability**: Allow expanding to see full dice rolls
4. **Accessibility**: Screen reader support for operation results
5. **Mobile**: Responsive layout for mobile devices

### Action Items

- [ ] **Create UI mockups** - Show operation results display in context
- [ ] **Specify display format** - Compact vs detailed, grouping rules
- [ ] **Add UI component specs** - TypeScript interfaces, React components
- [ ] **Accessibility audit** - Screen reader support, keyboard navigation

---

### Concern 3.2: Error Handling & Degradation

**Problem**: Design doesn't specify what happens when operations fail or LLM generates invalid operations.

**Scenarios**:
1. LLM generates invalid `pending_operations` (missing required fields)
2. Operation execution fails (resource doesn't exist, insufficient balance)
3. Backend service unavailable (Firestore timeout, dice service down)

### Required Specification

#### Error Handling Flow

```python
class OperationError(Exception):
    """Base exception for operation errors."""
    pass

class ValidationError(OperationError):
    """Operation validation failed."""
    pass

class ExecutionError(OperationError):
    """Operation execution failed."""
    pass

def execute_operations_with_fallback(
    operations: list[dict],
    game_state: GameState
) -> OperationResults:
    """Execute operations with error handling and fallback."""
    
    results = []
    errors = []
    
    for op in operations:
        try:
            # Validate operation
            validate_operation(op, game_state)
            
            # Execute operation
            result = execute_operation(op, game_state)
            results.append(result)
            
        except ValidationError as e:
            # Validation failed - log and continue
            errors.append({
                "operation": op,
                "error": str(e),
                "type": "validation"
            })
            results.append(OperationResult(
                success=False,
                error=str(e),
                operation=op["operation"]
            ))
            
        except ExecutionError as e:
            # Execution failed - check if required
            if op.get("required", False) and op.get("on_failure") == "abort":
                # Abort entire batch
                return OperationResults(
                    success=False,
                    aborted_at=op,
                    results=results,
                    errors=errors + [{"operation": op, "error": str(e), "type": "execution"}]
                )
            else:
                # Continue with other operations
                errors.append({
                    "operation": op,
                    "error": str(e),
                    "type": "execution"
                })
                results.append(OperationResult(
                    success=False,
                    error=str(e),
                    operation=op["operation"]
                ))
    
    return OperationResults(
        success=len(errors) == 0,
        results=results,
        errors=errors
    )
```

#### Degradation Strategy

```python
def process_action_with_fallback(
    user_input: str,
    game_state: GameState,
    execution_mode: str
) -> dict:
    """Process action with fallback to classic mode on failure."""
    
    if execution_mode == "planning":
        try:
            # Try planning mode
            response = process_planning_mode(user_input, game_state)
            
            # Validate response has required fields
            if "pending_operations" not in response:
                raise ValidationError("LLM omitted pending_operations")
            
            # Execute operations
            operation_results = execute_operations(
                response["pending_operations"],
                game_state
            )
            
            # Check if operations succeeded
            if not operation_results.success:
                # Operations failed - fallback to classic mode
                logging.warning("Planning mode operations failed, falling back to classic")
                return process_classic_mode(user_input, game_state)
            
            return {
                **response,
                "operation_results": operation_results
            }
            
        except Exception as e:
            # Any error - fallback to classic mode
            logging.error(f"Planning mode error: {e}, falling back to classic")
            return process_classic_mode(user_input, game_state)
    
    # Classic mode (no fallback needed)
    return process_classic_mode(user_input, game_state)
```

**Error Handling Rules**:
1. **Validation errors**: Log and continue (don't abort unless `required: true`)
2. **Execution errors**: Check `required` and `on_failure` flags
3. **System errors**: Fallback to classic mode automatically
4. **LLM errors**: Reprompt once, then fallback to classic mode

### Action Items

- [ ] **Specify error handling flow** - Validation vs execution errors, abort rules
- [ ] **Document degradation strategy** - Fallback to classic mode, retry logic
- [ ] **Add error handling tests** - Test validation failures, execution failures, system errors
- [ ] **Create error message templates** - User-friendly error messages

---

### Concern 3.3: LLM Prompt Engineering

**Problem**: Design doesn't specify how to ensure LLM generates valid `pending_operations` or how to provide feedback on validation errors.

**Questions**:
1. How to structure prompt to encourage valid operations?
2. What happens when LLM generates invalid operations?
3. How to provide validation error feedback to LLM?

### Required Specification

#### Prompt Structure

```markdown
## Pending Operations Format

You MUST generate a `pending_operations` array with valid operation schemas.

### Operation Types

1. **consume_resource**
   - Required: `resource_id`, `amount`
   - Optional: `purpose`
   - Example: `{"operation": "consume_resource", "args": {"resource_id": "spell_slot_3", "amount": 1}}`

2. **roll_dice**
   - Required: `notation` (e.g., "8d6", "{level}d6")
   - Optional: `purpose`, `result_key`
   - Example: `{"operation": "roll_dice", "args": {"notation": "8d6", "purpose": "Fireball damage"}, "result_key": "fireball_damage"}`

[... more operation types ...]

### Validation Rules

- All `resource_id` values must exist in current game state
- All `result_key` values must be unique within the operation batch
- References (`*_ref`) must reference prior operations with `result_key`
- Formula dice (`{expression}`) must use valid context variables

### Error Handling

If validation fails, you will receive an error message. Fix the operation and retry.
```

#### Validation Error Feedback

```python
def provide_validation_feedback(
    llm_response: dict,
    validation_errors: list[dict]
) -> str:
    """Generate feedback message for LLM to fix operations."""
    
    feedback = "VALIDATION ERRORS:\n\n"
    
    for error in validation_errors:
        feedback += f"Operation: {error['operation']}\n"
        feedback += f"Error: {error['message']}\n"
        feedback += f"Location: {error.get('field', 'unknown')}\n\n"
    
    feedback += "Please fix these errors and regenerate pending_operations.\n"
    feedback += "Available resources: " + ", ".join(get_available_resources())
    
    return feedback

def reprompt_with_validation(
    user_input: str,
    game_state: GameState,
    validation_errors: list[dict],
    max_retries: int = 1
) -> dict:
    """Reprompt LLM with validation error feedback."""
    
    feedback = provide_validation_feedback({}, validation_errors)
    
    enhanced_prompt = f"""
{user_input}

{feedback}
"""
    
    return generate_llm_response(enhanced_prompt, game_state)
```

**Prompt Engineering Rules**:
1. **Explicit schemas**: Provide JSON schemas for each operation type
2. **Examples**: Include multiple examples of valid operations
3. **Validation feedback**: Return specific error messages with field locations
4. **Retry limit**: Allow 1 retry with validation feedback, then fallback
5. **Context awareness**: Include available resources/entities in prompt

### Action Items

- [ ] **Create prompt templates** - Operation schemas, examples, validation rules
- [ ] **Specify validation feedback format** - Error messages, field locations
- [ ] **Document retry logic** - How many retries, when to fallback
- [ ] **Add prompt tests** - Test LLM generates valid operations, handles errors

---

### Concern 3.4: Computed Bonuses Visibility

**Problem**: Design adds computed bonuses but doesn't specify where/how they appear in LLM prompts or UI.

**Example**: Divine rank 3 = +3 to AC, attacks, saves, spell DCs. How does LLM know these exist?

### Required Specification

#### Prompt Integration

```markdown
## Character Resources & Bonuses

### Resources
- Spell Slots: 1st (4/4), 2nd (3/3), 3rd (2/2)
- HP: 32/32
- Divine Rank: 3 (Minor God)

### Computed Bonuses (Auto-Applied)
These bonuses are automatically added to rolls - you don't need to add them manually:

- **AC Bonus**: +3 (from Divine Rank)
- **Attack Bonus**: +3 (from Divine Rank)
- **Save Bonus**: +3 (from Divine Rank)
- **Spell DC Bonus**: +3 (from Divine Rank)

When calculating DCs or attack modifiers, these bonuses are already included in the base values shown above.
```

#### UI Display

```typescript
interface ComputedBonusDisplay {
  source: string;  // "Divine Rank", "Magic Item", etc.
  bonuses: {
    ac?: number;
    attack?: number;
    saves?: number;
    spell_dc?: number;
  };
}

// Display in character sheet
<div className="computed-bonuses">
  <h3>Auto-Applied Bonuses</h3>
  <div>Divine Rank (+3): AC, Attack, Saves, Spell DC</div>
</div>
```

**Visibility Rules**:
1. **Prompt**: Include computed bonuses in session header with clear labeling
2. **UI**: Display in character sheet with source attribution
3. **Transparency**: Show bonuses in operation results (e.g., "Attack: 1d20+7 (+3 from Divine Rank)")
4. **LLM Guidance**: Explicitly state bonuses are auto-applied, don't double-count

### Action Items

- [ ] **Specify prompt format** - Where computed bonuses appear in session header
- [ ] **Create UI mockups** - Character sheet display of computed bonuses
- [ ] **Document transparency rules** - How to show bonuses in operation results
- [ ] **Add visibility tests** - Test LLM sees bonuses, doesn't double-count

---

## 4. Performance & Scalability

### Concern 4.1: Firestore Write Throughput

**Problem**: Audit trail writes to Firestore for every operation. High-frequency operations (mass combat, living world) could cause write throttling.

**Current Design**: Doesn't specify batching, rate limiting, or write optimization.

### Required Specification

```python
# Batch audit events for efficient Firestore writes
AUDIT_BATCH_SIZE = 50
AUDIT_BATCH_TIMEOUT = 1.0  # seconds

class AuditEventBatcher:
    """Batch audit events for efficient Firestore writes."""
    
    def __init__(self):
        self.batch = []
        self.last_write = time.time()
    
    def add_event(self, event: AuditEvent):
        """Add event to batch."""
        self.batch.append(event)
        
        # Flush if batch full or timeout exceeded
        if len(self.batch) >= AUDIT_BATCH_SIZE:
            self.flush()
        elif time.time() - self.last_write > AUDIT_BATCH_TIMEOUT:
            self.flush()
    
    def flush(self):
        """Write batch to Firestore."""
        if not self.batch:
            return
        
        # Batch write
        db.batch().set_multiple(self.batch).commit()
        self.batch = []
        self.last_write = time.time()
```

**Performance Rules**:
1. **Batching**: Batch audit events (50 per write)
2. **Rate limiting**: Max 10 writes/second per campaign
3. **Async writes**: Non-blocking audit writes (don't delay operation results)
4. **Compression**: Compress audit events for storage efficiency

### Action Items

- [ ] **Specify batching strategy** - Batch size, timeout, flush triggers
- [ ] **Document rate limiting** - Max writes per second, throttling behavior
- [ ] **Add performance tests** - Test high-frequency operations, write throughput
- [ ] **Optimize storage** - Compression, indexing strategy

---

## Summary: Action Items by Priority

### High Priority (Blocking Implementation)

1. **Security hardening** - simpleeval sandboxing, context sanitization
2. **Error handling specification** - Validation errors, execution errors, fallback
3. **UI integration** - Operation results display, computed bonuses visibility

### Medium Priority (Should Address Before Launch)

4. **Edge case handling** - Circular triggers, resource conflicts, mode transitions
5. **Prompt engineering** - Operation schemas, validation feedback, retry logic
6. **Performance optimization** - Firestore batching, rate limiting

### Low Priority (Can Address Post-Launch)

7. **Advanced error recovery** - Sophisticated retry strategies
8. **Analytics integration** - Operation success rates, error tracking

---

## Next Steps

1. **Review this document** with design team
2. **Prioritize action items** based on implementation phase
3. **Create implementation tickets** for each action item
4. **Update design document** with specifications as they're finalized
5. **Track progress** in implementation PRs

---

**End of Document**
