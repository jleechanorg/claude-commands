# Combinations Command

**Usage**: `/combinations` or `/combos`

**Description**: Lists all available slash command combinations and their effects.

## Available Command Combinations

### True Universal Command Composition

**BREAKTHROUGH**: The system now leverages Claude's natural language processing for **genuine universality**!

### How It Works

Instead of complex hardcoded mappings, the system creates simple meta-prompts that Claude interprets naturally:

**Input**: `/think /debug /weird analyze performance`
**Meta-prompt**: `Use these approaches in combination: /think /debug /weird. Apply this to: analyze performance`
**Claude's Natural Understanding**: Combines deep thinking, systematic debugging, and unconventional approaches

### Revolutionary Simplicity

- **ANY commands work** - even completely made-up ones
- **No predefined lists** - Claude understands context and meaning
- **Consistent quality** - no degradation for "unknown" commands
- **Self-improving** - gets better as Claude's understanding evolves

### Examples of True Universality

**Real Commands**:
- `/think /plan /arch` → Strategic architectural planning with deep thinking
- `/debug /optimize /test` → Systematic debugging with optimization and testing

**Creative Commands**:
- `/mythical /dragon /optimize` → Creative powerful optimization approaches
- `/stealth /ninja /implement` → Subtle, efficient implementation strategies

**Completely Made-Up Commands**:
- `/quantum /cosmic /analyze` → Claude interprets creatively for analysis
- `/fluffy /rainbow /debug` → Claude finds meaningful interpretation

**Technical Commands**:
- `/security /scale /deploy` → Security-focused scalable deployment
- `/performance /monitor /validate` → Performance monitoring with validation

## How It Works

The **Universal Command Composition** system:
1. **Parses ANY commands** from your input (known or unknown)
2. **Builds natural language instructions** dynamically
3. **Combines behaviors intelligently** without predefined rules
4. **Handles unknown commands gracefully** with "approach" patterns

## Dynamic Examples

**Input**: `/think /debug /brief /test analyze memory leaks`
**Output**: `/execute Use sequential thinking for systematic debugging with testing methodology: analyze memory leaks [Respond concisely]`

**Input**: `/arch /optimize /secure build API gateway`  
**Output**: `/arch for architectural design to optimize and improve with security considerations: build API gateway`

**Input**: `/custom /weird /nonexistent create something`
**Output**: `/execute with custom approach with weird approach with nonexistent approach: create something`

**Input**: `/research /validate /monitor /verbose setup CI/CD`
**Output**: `/execute with research methodology to validate and verify to monitor and track: setup CI/CD [Provide detailed explanations]`

## Configuration

The system requires no configuration! Claude's natural language processing handles all command interpretation. The hook script at `.claude/hooks/compose-commands.sh` is simple and needs no customization.

## Usage Notes

- Order doesn't matter: `/think /plan` = `/plan /think`
- Single commands work unchanged: `/think` remains `/think`
- Unknown combinations pass through unchanged
- Conflicting combinations (like `/brief /verbose`) are handled gracefully