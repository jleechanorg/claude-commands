# Personal Token Optimization Guide 🎯

*A practical guide for individual developers to reduce Claude API costs while maintaining productivity*

---

## 📊 Where You Stand vs Others

### Typical Personal Usage Patterns
- **Light Users**: $10-30/month (casual coding, occasional questions)
- **Regular Developers**: $50-100/month (daily coding, project work)
- **Power Users**: $150-300/month (heavy development, multiple projects)
- **Your Current Usage**: $___ /month *(check with `/cost` command)*

### Quick Self-Assessment
```
□ I use Claude Code daily for development
□ I often hit context limits in long sessions
□ I frequently ask similar questions across projects
□ I use Claude for both coding and research/planning
□ My monthly bill is higher than I'd like
```

**If you checked 3+ boxes**: This guide will save you significant money

---

## 🚀 Quick Wins (Immediate 30-50% Savings)

### 1. **Smart Session Management**
**Problem**: Long sessions accumulate expensive context
**Solution**: Strategic session resets

```bash
# Before expensive operations, check your usage
/cost

# When context gets heavy (>50K tokens), reset strategically
# Instead of: continuing with bloated context
# Do: "Let's start fresh. Here's what I'm working on: [brief summary]"
```

**Expected Savings**: 20-30%

### 2. **CLAUDE.md Optimization**
**Problem**: Repeating project context every session
**Solution**: Efficient project documentation

```markdown
# Keep your CLAUDE.md under 5K tokens
# Focus on:
- Current task priorities
- Essential code patterns
- Key file locations
- Active bugs/TODOs

# Avoid:
- Full code dumps
- Historical context
- Detailed implementation notes
```

**Expected Savings**: 15-25%

### 3. **Targeted File Reading**
**Problem**: Claude reads entire codebases unnecessarily
**Solution**: Explicit file guidance

```bash
# Instead of: "Look at my code and fix the bug"
# Use: "Read only src/auth.py and look at the login function"

# Use your CLAUDE.md to specify:
- Which directories to focus on
- Which files are most important
- Which files to avoid reading
```

**Expected Savings**: 20-40%

---

## 🎯 Advanced Optimization (50-70% Total Savings)

### 4. **Pattern-Based Prompting**
**Problem**: Starting from scratch each conversation
**Solution**: Reusable prompt templates

Create a `prompts/` folder with reusable templates:

```markdown
# prompts/debug.md
Debug the following issue:
- Current behavior: [describe]
- Expected behavior: [describe]  
- Relevant file: [filename]
- Error message: [if any]

# prompts/review.md
Review this code for:
- Security issues
- Performance problems
- Best practice violations
File: [filename]

# prompts/refactor.md
Refactor the following code to:
- Improve readability
- Reduce complexity
- Follow [specific pattern]
```

**Expected Savings**: 30-40%

### 5. **Task-Specific Conversations**
**Problem**: Mixing different types of work in one session
**Solution**: Separate conversations by task type

```
Session 1: "Bug fixing in user authentication"
Session 2: "Feature development - payment processing" 
Session 3: "Code review and refactoring"
```

**Expected Savings**: 25-35%

### 6. **Smart Context Preservation**
**Problem**: Losing valuable context when resetting
**Solution**: Context summarization strategy

```markdown
# Create session-notes.md
## Current Session Summary
- **Goal**: Implement user authentication
- **Progress**: Login form complete, working on validation
- **Next**: Add password hashing, test error handling
- **Key Decisions**: Using bcrypt, storing tokens in httpOnly cookies

# Reference this in new sessions instead of full context
```

**Expected Savings**: 20-30%

---

## 🔧 Technical Implementation Tips

### Model Selection Strategy
```bash
# For simple tasks (documentation, basic questions):
# Use cheaper models when available or be concise

# For complex reasoning (architecture, debugging):
# Use full context strategically, then summarize results

# For repetitive tasks (code review, formatting):
# Create templates and reuse patterns
```

### Cost Monitoring Workflow
```bash
# Daily habit: Check token usage
/cost

# Weekly review: Analyze patterns
- Which conversations consumed the most tokens?
- What could have been more efficient?
- Which sessions should have been split or reset?

# Monthly optimization: Refine your approach
- Update CLAUDE.md based on current project focus
- Improve prompt templates based on usage patterns
- Identify new opportunities for efficiency
```

### File Organization for Efficiency
```
project/
├── CLAUDE.md              # Project context (keep <5K tokens)
├── docs/
│   ├── api.md             # Reference docs for Claude
│   └── architecture.md    # High-level overview only
├── prompts/               # Reusable prompt templates
│   ├── debug.md
│   ├── review.md
│   └── feature.md
└── session-notes.md       # Running context summary
```

---

## 📈 Measuring Your Success

### Key Metrics to Track
```bash
# Monthly cost tracking
Month 1 (baseline): $____ 
Month 2 (optimized): $____
Savings: ____%

# Session efficiency
Average tokens per session before: ____
Average tokens per session after: ____
Efficiency improvement: ____%

# Productivity check
Development velocity maintained: Yes/No
Code quality maintained: Yes/No
Satisfaction with Claude interactions: Improved/Same/Worse
```

### Red Flags to Avoid
- ❌ Sessions regularly hitting token limits
- ❌ Repeating the same context explanations
- ❌ Having Claude read entire files for small changes
- ❌ Using Claude for tasks that could be automated locally
- ❌ Not leveraging your CLAUDE.md effectively

### Green Flags You're Optimizing Well
- ✅ Conversations stay focused on specific goals
- ✅ You use templates for common tasks
- ✅ Context resets feel strategic, not disruptive
- ✅ Monthly costs are predictable and controlled
- ✅ You spend more time coding, less time explaining context

---

## 🎯 30-Day Implementation Plan

### Week 1: Foundation
- [ ] Audit current usage with `/cost` command
- [ ] Optimize your CLAUDE.md (aim for <5K tokens)
- [ ] Start using targeted file reading instructions

### Week 2: Efficiency Patterns
- [ ] Create prompt templates for common tasks
- [ ] Practice strategic session management
- [ ] Implement session-notes.md for context preservation

### Week 3: Advanced Techniques
- [ ] Separate conversations by task type
- [ ] Refine file organization for Claude efficiency
- [ ] Monitor and measure token usage patterns

### Week 4: Optimization & Refinement
- [ ] Analyze which techniques provided the most savings
- [ ] Fine-tune your approach based on results
- [ ] Plan sustainable habits for ongoing optimization

---

## 💡 Pro Tips from High-Efficiency Users

1. **"I save my most complex questions for the start of fresh sessions"** - Maximizes context for difficult problems

2. **"I use bullets and structured prompts instead of conversational requests"** - More direct = fewer tokens

3. **"I maintain a 'Claude cheat sheet' of my most effective prompts"** - Consistency improves efficiency

4. **"I do quick tasks in separate, focused conversations"** - Prevents context pollution

5. **"I review my `/cost` weekly and adjust habits based on patterns"** - Data-driven optimization

---

## 🚨 Common Mistakes to Avoid

- **Don't**: Start every session by dumping your entire codebase
- **Don't**: Keep sessions running indefinitely without strategic resets
- **Don't**: Use Claude for simple tasks you could Google or automate
- **Don't**: Ignore context accumulation until you hit limits
- **Don't**: Mix unrelated tasks in the same conversation

**Remember**: The goal is smart efficiency, not just cost cutting. These optimizations should make your Claude interactions more focused and productive, not just cheaper.

---

## 🔧 Automation Tools (Copy-Paste Ready)

### Quick Setup Commands
```bash
# Create directory structure
mkdir -p ~/.claude/scripts

# Download and setup all tools in one go
curl -o ~/.claude/scripts/token_monitor.sh "https://gist.githubusercontent.com/your-username/token_monitor/raw"
curl -o ~/.claude/scripts/session_manager.py "https://gist.githubusercontent.com/your-username/session_manager/raw"
curl -o ~/.claude/scripts/cost_tracker.py "https://gist.githubusercontent.com/your-username/cost_tracker/raw"

# Make executable
chmod +x ~/.claude/scripts/*.sh ~/.claude/scripts/*.py

# Add aliases to your shell
echo 'alias claude-cost="~/.claude/scripts/cost_tracker.py visualize"' >> ~/.bashrc
echo 'alias claude-session="~/.claude/scripts/session_manager.py"' >> ~/.bashrc
source ~/.bashrc
```

### 1. Token Usage Monitor
**File**: `~/.claude/scripts/token_monitor.sh`
```bash
#!/bin/bash
# Track your daily token usage patterns
LOG_FILE="$HOME/.claude/token_usage.log"
DAILY_LIMIT=100000  # Adjust based on your plan

log_tokens() {
    local tokens=$1
    local operation=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "$timestamp|$tokens|$operation" >> "$LOG_FILE"
}

show_daily_usage() {
    local today=$(date '+%Y-%m-%d')
    local total=$(grep "^$today" "$LOG_FILE" | cut -d'|' -f2 | paste -sd+ - | bc)
    local remaining=$((DAILY_LIMIT - total))
    
    echo "📊 Daily Token Usage: $total tokens ($remaining remaining)"
    if [ $total -gt $((DAILY_LIMIT * 80 / 100)) ]; then
        echo "⚠️  Warning: Approaching daily limit"
    fi
}

# Usage: ./token_monitor.sh log 15000 "code review"
#        ./token_monitor.sh daily
```

### 2. Smart Session Manager
**File**: `~/.claude/scripts/session_manager.py`
```python
#!/usr/bin/env python3
# Get intelligent session management suggestions
import os
from datetime import datetime

def suggest_action():
    usage_file = os.path.expanduser("~/.claude/token_usage.log")
    if not os.path.exists(usage_file):
        print("🟢 No usage data found - session is clean")
        return
    
    today = datetime.now().strftime('%Y-%m-%d')
    total = 0
    
    with open(usage_file, 'r') as f:
        for line in f:
            if line.startswith(today):
                parts = line.strip().split('|')
                if len(parts) >= 2:
                    total += int(parts[1])
    
    print(f"📊 Today's Usage: {total:,} tokens")
    
    if total > 90000:
        print("🔴 CRITICAL: Reset session now - Run: /clear")
    elif total > 70000:
        print("🟠 WARNING: Consider resetting - Run: /clear")  
    else:
        print("🟢 OK: Session usage normal")

if __name__ == "__main__":
    suggest_action()
```

### 3. CLAUDE.md Generator
**File**: `~/.claude/scripts/claude_md_generator.py`
```python
#!/usr/bin/env python3
# Generate token-efficient CLAUDE.md files
import os
import sys
from pathlib import Path

def generate_claude_md(directory=".", max_files=15):
    essential_patterns = ["*.py", "*.js", "*.ts", "README.md", "package.json"]
    essential_files = []
    
    for pattern in essential_patterns:
        files = list(Path(directory).rglob(pattern))
        essential_files.extend(files)
    
    essential_files = essential_files[:max_files]  # Limit to control tokens
    
    content = f"""# Project Context (Auto-Generated)

## Essential Files ({len(essential_files)} files)
Claude should focus on these files unless explicitly told otherwise:

"""
    for file_path in essential_files:
        relative_path = os.path.relpath(file_path, directory)
        content += f"- `{relative_path}`\n"
    
    content += """
## Token Optimization Rules
1. Read only essential files above
2. Use /compact when context gets heavy  
3. Reset with /clear after major tasks
4. Keep sessions focused on single goals
"""
    
    with open(os.path.join(directory, "CLAUDE.md"), "w") as f:
        f.write(content)
    
    print(f"✅ Generated CLAUDE.md with {len(essential_files)} essential files")

# Usage: python3 claude_md_generator.py /path/to/project
if __name__ == "__main__":
    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    generate_claude_md(directory)
```

### 4. Cost Tracker with Visualization
**File**: `~/.claude/scripts/cost_tracker.py`
```python
#!/usr/bin/env python3
# Track and visualize Claude API costs
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict

def calculate_costs(days=7):
    usage_file = os.path.expanduser("~/.claude/token_usage.log")
    if not os.path.exists(usage_file):
        print("No usage data found")
        return
    
    daily_costs = defaultdict(float)
    pricing = {"input": 0.000003, "output": 0.000015}  # $3/$15 per 1M tokens
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    with open(usage_file, 'r') as f:
        for line in f:
            parts = line.strip().split('|')
            if len(parts) >= 2:
                date_str = parts[0].split()[0]
                date = datetime.strptime(date_str, '%Y-%m-%d')
                
                if date >= cutoff_date:
                    tokens = int(parts[1])
                    # Assume 70% input, 30% output
                    cost = (tokens * 0.7 * pricing["input"]) + (tokens * 0.3 * pricing["output"])
                    daily_costs[date] += cost
    
    total_cost = sum(daily_costs.values())
    avg_cost = total_cost / len(daily_costs) if daily_costs else 0
    
    print(f"💰 Cost Summary ({days} days):")
    print(f"Total: ${total_cost:.2f}")
    print(f"Average: ${avg_cost:.2f}/day")
    print(f"Monthly projection: ${avg_cost * 30:.2f}")
    
    # Show daily breakdown
    for date, cost in sorted(daily_costs.items()):
        print(f"  {date.strftime('%Y-%m-%d')}: ${cost:.2f}")

# Usage: python3 cost_tracker.py [days]
if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    calculate_costs(days)
```

### 5. Efficient Prompt Templates
**Directory**: `~/.claude/prompts/`

**debug.md**:
```markdown
Debug this specific issue:
- Current behavior: [describe]
- Expected behavior: [describe]
- File: [filename] 
- Error: [paste error message]

Keep response focused on actionable fixes only.
```

**review.md**:
```markdown
Review this code for critical issues only:
- Security vulnerabilities
- Performance problems  
- Major bugs

File: [filename]
Code: [paste code here]

Format: Line number + specific issue + fix
```

**refactor.md**:
```markdown
Refactor this code to be:
- More readable
- Better performance
- [specific improvement goal]

Original code: [paste here]
Focus: [specific area to improve]
```

### Daily Usage Workflow
```bash
# Morning: Check yesterday's usage
claude-session

# After coding sessions: Log your usage
~/.claude/scripts/token_monitor.sh log 25000 "feature development"

# Weekly: Review costs and patterns
claude-cost 7

# New project: Generate efficient CLAUDE.md
~/.claude/scripts/claude_md_generator.py ./my-new-project
```

---

*Expected Results: Following this guide with automation tools typically results in 50-70% cost reduction while maintaining or improving development productivity.*