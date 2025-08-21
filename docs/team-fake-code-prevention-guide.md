# Team Guide: Fake Code Prevention

**Target Audience**: Development team, code reviewers, project leads
**Purpose**: Quick adoption guide for enhanced fake code prevention system

## 🚀 Quick Start (5 Minutes)

### **1. Update Your Mental Model**
**Old**: "I'll create a placeholder and implement later"  
**New**: "Can't implement fully? Use orchestration instead"

### **2. Learn the Decision Gate**
Before writing ANY function, ask: **"Can I implement this fully right now?"**
- **YES** → Implement with working code
- **NO** → Use orchestration (call existing commands)

### **3. Update Your Workflow**
```bash
# Add this to your development routine (MANDATORY)
/fake3                    # Check before every commit
git add .
git commit -m "message"
```

## 🧠 Key Mindset Shifts

### **From Implementation to Orchestration**
```python
# ❌ Old Way (Creates fake code risk)
def call_github_api():
    # TODO: Implement GitHub integration
    return None

# ✅ New Way (Orchestration in .md file)
# Use existing /commentfetch command instead
```

### **From Placeholder to Working Code**
```python
# ❌ Old Way
def complex_algorithm():
    # Will implement sophisticated logic later
    pass

# ✅ New Way  
def simple_working_part():
    return validated_result()  # Actually works now

# Complex = orchestration of simple working parts
```

## 📋 Daily Practices

### **Before Writing Code**
1. **Decision Gate**: "Can I implement this fully right now?"
2. **Existing Check**: "Does a command already handle this?"
3. **Breaking Down**: "Can I split this into implementable parts?"

### **Before Committing**
1. **Run `/fake3`** (mandatory - detects fake patterns)
2. **Fix any issues** found by the detection system
3. **Proceed with normal git workflow**

### **During Code Review**
1. **Zero tolerance** for placeholder/fake code
2. **Suggest orchestration** when seeing reimplementation
3. **Look for patterns**: TODO, "implement later", hardcoded None

## 🚨 Red Flags (Stop Immediately)

**In Your Own Code**:
- Writing TODO comments in function bodies
- Using "return None" with "fallback" comments  
- Comments saying "implement later" or "for now"
- Creating simplified versions of existing functionality

**In Code Reviews**:
- Functions that don't actually work
- Placeholder return values
- Duplicated logic from existing commands
- Comments about future implementation

## ✅ Success Patterns

### **Orchestration Examples**
```markdown
# gstatus.md - Good orchestration
/commentfetch                           # Use existing GitHub integration
python3 .claude/commands/gstatus.py    # Handle display/formatting
```

### **Working Implementation Examples**
```python
# All functions actually work when called
def validate_input(data):
    return isinstance(data, dict) and 'field' in data

def process_validated_data(data):
    return data.get('field', 'default_value')

def format_result(processed):
    return f"Result: {processed}"
```

## 🛠️ Tools at Your Disposal

### **Detection Tools**
- **`/fake3`**: Run before commits (finds fake patterns)
- **Hook**: Automatic detection (blocks fake code commits)
- **CI**: Pipeline rejection of PRs with fake code

### **Prevention Resources**
- **Decision Framework**: `docs/implementation-decision-framework.md`
- **CLAUDE.md**: Updated rules with prevention protocols
- **Process Guide**: `docs/fake-code-prevention-protocols.md`

## 🎯 Team Roles

### **Developers**
- ✅ Run `/fake3` before every commit
- ✅ Use decision gate before writing functions
- ✅ Prefer orchestration over reimplementation
- ✅ Report new fake code patterns to team

### **Code Reviewers**
- ✅ Reject PRs with any fake/placeholder code
- ✅ Suggest orchestration alternatives
- ✅ Educate on better patterns
- ✅ Enforce zero tolerance policy

### **Team Leads** 
- ✅ Monitor prevention metrics
- ✅ Ensure workflow compliance
- ✅ Update tools based on team feedback
- ✅ Celebrate orchestration-first wins

## 📊 Success Metrics

**Individual Level**:
- Zero fake code in your commits
- Higher use of existing commands (orchestration)
- Faster development (no cleanup cycles)

**Team Level**:
- Zero fake code incidents per sprint
- Improved architecture (less duplication)
- Faster PR review cycles

## 🚀 Advanced Techniques

### **Breaking Down Complex Tasks**
Instead of creating placeholder for complex function:
1. **Identify smallest working part**
2. **Implement that part fully**
3. **Build complexity through composition**
4. **Use orchestration for integration**

### **Leveraging Existing Commands**
- Study existing `/comment*` commands before building GitHub integration
- Use existing `/push*` commands before building git functionality  
- Check `/test*` commands before building test utilities

### **Composition Patterns**
```bash
# .md orchestration combining multiple tools
/commentfetch              # Get data
python3 process.py         # Transform data  
/pushl                     # Commit results
```

## 🆘 When You Need Help

**If Decision Gate is Unclear**:
- Ask: "What existing command might handle this?"
- Check: Can this be broken into smaller parts?
- Consult: `docs/implementation-decision-framework.md`

**If `/fake3` Detects Issues**:
- Read the detection messages carefully
- Replace placeholders with orchestration
- Ask team for existing command alternatives

**If Architecture Seems Complex**:
- Consider if you're reimplementing existing functionality
- Look for orchestration opportunities
- Discuss composition approaches with team

## 📚 Quick Reference Links

- **Decision Framework**: `docs/implementation-decision-framework.md`
- **Prevention Protocols**: `docs/fake-code-prevention-protocols.md`
- **CLAUDE.md**: Main rules and updated prevention framework
- **Detection Hook**: `.claude/hooks/detect_speculation_and_fake_code.sh`

---

**Next Steps**: 
1. Read this guide (5 minutes)
2. Update your workflow to include `/fake3`
3. Practice the decision gate on your next task
4. Start using orchestration over implementation

**Questions?** Ask the team lead or consult the detailed documentation linked above.

---

**Generated**: 2025-08-21 via /execute fake code prevention system
**Status**: Ready for team adoption