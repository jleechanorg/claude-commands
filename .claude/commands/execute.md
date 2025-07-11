# Execute Command - Simplified Protocol

**Purpose**: Execute complex tasks with proper planning and milestone tracking

**Usage**: `/execute` or `/e`

## 🚨 MANDATORY 3-STEP PROTOCOL

### Step 1: TodoWrite Checklist
When you see `/e` or `/execute`, IMMEDIATELY create a todo with:
```
## EXECUTE PROTOCOL CHECKLIST
- [ ] Context check: ___% remaining
- [ ] Complexity assessment: Low/Medium/High  
- [ ] Subagents needed? Yes/No (Why: ___)
- [ ] Execution plan presented to user
- [ ] User approval received: YES/NO
```

### Step 2: Present Plan
Based on checklist analysis:
- **Low complexity + >50% context**: Direct execution
- **Medium/High complexity OR <50% context**: Use subagents
- Show user the plan and WAIT for approval

### Step 3: Execute (ONLY after approval)
- **Direct**: Work with 5-minute milestone updates
- **Subagents**: Create worktrees, assign tasks, coordinate results

## Example Flow
```
User: /e implement JSON backend support