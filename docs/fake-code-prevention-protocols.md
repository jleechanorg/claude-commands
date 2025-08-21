# Fake Code Prevention Protocols

**Purpose**: Systematic prevention of fake/placeholder code through behavioral, automated, and process controls

## 🛡️ Multi-Layer Prevention System

### **Layer 1: Behavioral Prevention (Highest Impact)**

**🧠 Mental Model Change**:
- **Old Pattern**: "I'll create a placeholder and implement later"
- **New Pattern**: "Can't implement fully? Use orchestration instead"

**🚪 Decision Gate Protocol**:
1. **Before ANY function creation**, ask: "Can I implement this fully right now?"
2. **If NO**: Don't create function - use orchestration/composition
3. **If YES**: Implement with working code, no placeholders

### **Layer 2: Automated Detection**

**🔍 Existing Infrastructure**:
- **Hook**: `.claude/hooks/detect_speculation_and_fake_code.sh`
- **Patterns**: 20+ fake code patterns detected
- **Action**: Blocks commits with exit 2 when fake code found
- **Warning**: Creates `docs/CRITICAL_FAKE_CODE_WARNING.md`

**🚨 Automatic Triggers**:
- Pre-commit hooks scan all code changes
- CI pipeline rejects PRs with fake code
- Real-time detection during development

### **Layer 3: Process Integration**

**📋 Standard Development Workflow**:
```bash
# MANDATORY before any commit
/fake3                    # Check for fake patterns
# Fix any issues, then proceed
git add .
git commit -m "message"
```

**🔄 PR Review Standards**:
- All PRs automatically scanned for fake code
- Reviewers trained to recognize fake patterns
- Zero tolerance for placeholder implementations

### **Layer 4: Architecture Prevention**

**🏗️ Orchestration-First Design**:
- **Default**: Use existing commands rather than reimplementing
- **Pattern**: Composition > Implementation > Placeholder
- **Example**: Use `/commentfetch` instead of creating `call_github_mcp()`

## 🚨 Fake Code Patterns to Prevent

### **High-Risk Patterns**

```python
# ❌ NEVER CREATE THESE PATTERNS

# 1. Placeholder Returns
def function():
    return None  # Fallback to X

# 2. TODO Implementations  
def function():
    # TODO: Implement actual logic
    pass

# 3. Commented Fake Logic
def function():
    # This would call actual API
    # For now, return fake data
    return fake_data

# 4. Simulation Code
def call_api():
    # Simulates API call
    return {"status": "success"}
```

### **Prevention Replacements**

```python
# ✅ INSTEAD, USE THESE PATTERNS

# 1. Orchestration (via .md files)
# Call existing /commentfetch command instead of implementing GitHub API

# 2. Incremental Implementation
def validate_input(data):
    return isinstance(data, dict)  # Actually works

def process_data(data):
    if validate_input(data):
        return data.get('field')
    return None

# 3. Utility Reuse
from existing_module import api_call
result = api_call(params)  # Use existing working code
```

## 📊 Prevention Metrics

**Success Indicators**:
- ✅ Zero fake code in new commits
- ✅ Higher orchestration ratio (reusing existing commands)
- ✅ Faster development cycles (no cleanup needed)
- ✅ Better architecture (composition over duplication)

**Warning Signs**:
- ❌ TODO comments in function bodies
- ❌ "Implement later" patterns
- ❌ Hardcoded None returns
- ❌ Comments saying "for now" or "temporary"

## 🔧 Tools and Commands

### **Detection Tools**
- **`/fake3`**: Iterative fake code detection and fixing
- **Hook**: Automatic detection on every response
- **CI**: Pipeline rejection of fake code PRs

### **Prevention Tools**
- **Decision Framework**: `docs/implementation-decision-framework.md`
- **CLAUDE.md Rules**: Pre-implementation decision gate
- **Workflow Integration**: Mandatory `/fake3` before commits

### **Fix Tools**
- **`/fake`**: Automatic fake code fixing command
- **Manual**: Replace with orchestration or working code
- **Architecture**: Refactor to composition patterns

## 🎯 Team Adoption Guidelines

### **For Developers**
1. **Internalize decision gate**: Ask "Can I implement fully?" before coding
2. **Default to orchestration**: Look for existing commands first
3. **Run `/fake3`** before every commit (mandatory)
4. **Report patterns**: Submit new fake code patterns to hook

### **For Reviewers**  
1. **Zero tolerance**: Reject any PR with fake/placeholder code
2. **Architecture focus**: Encourage orchestration over reimplementation
3. **Pattern recognition**: Learn to spot subtle fake code patterns
4. **Education**: Explain better alternatives when rejecting fake code

### **For Team Leads**
1. **Process enforcement**: Make `/fake3` mandatory in workflow
2. **Training**: Educate team on orchestration-first thinking
3. **Metrics tracking**: Monitor fake code incidents and prevention success
4. **Continuous improvement**: Update patterns and tools based on findings

## 🚀 Implementation Timeline

**Phase 1: Immediate (Deployed)**
- ✅ Enhanced CLAUDE.md rules with decision framework
- ✅ Decision tree documentation created
- ✅ Workflow integration documented

**Phase 2: Adoption (This Week)**
- Train team on new decision framework
- Enforce `/fake3` in all development workflows
- Update PR templates with fake code checking

**Phase 3: Culture (Ongoing)**
- Monitor prevention metrics
- Continuously update fake code patterns
- Celebrate orchestration-first architecture wins

## 📚 References

- **CLAUDE.md**: Primary rules and decision framework
- **Implementation Decision Framework**: `docs/implementation-decision-framework.md`
- **Detection Hook**: `.claude/hooks/detect_speculation_and_fake_code.sh`
- **Fix Command**: `/fake3` for iterative detection and fixing

---

**Generated**: 2025-08-21 via /execute fake code prevention implementation
**Status**: Active prevention system deployed