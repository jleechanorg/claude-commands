# /orchc - Alias for /orchconverge

**Short alias for autonomous convergence with tmux orchestration**

## Usage
All `/orchc` commands are directly equivalent to `/orchconverge`:

```bash
/orchc <goal>                           # Same as: /orchconverge <goal>
/orchc <goal> --max-attempts 15        # Same as: /orchconverge <goal> --max-attempts 15
/orchc <goal> --max-hours 6            # Same as: /orchconverge <goal> --max-hours 6
/orchc <goal> --interval 5             # Same as: /orchconverge <goal> --interval 5
/orchc --status                         # Same as: /orchconverge --status
/orchc --stop                           # Same as: /orchconverge --stop
```

## Command Delegation

**All `/orchc` commands delegate directly to `/orchconverge`**:

```markdown
**Command**: /orchconverge [all arguments passed through]
```

For complete documentation, see: [orchconverge.md](./orchconverge.md)

## Examples

```bash
# Quick autonomous convergence
/orchc "fix all failing tests"

# Custom limits
/orchc "implement auth system" --max-attempts 20 --max-hours 4

# Status check
/orchc --status

# Emergency stop
/orchc --stop
```

---

**This is an alias command. All functionality is provided by `/orchconverge`.**