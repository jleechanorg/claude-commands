# Branch Guidelines - copilotsuperfix

## 🎯 Branch-Specific Principles

### Security Boundary Management
- **User Autonomy**: Respect explicit user decisions on security boundaries
- **Documentation First**: Security decisions should be clearly documented with rationale
- **Context Preservation**: Maintain decision context to prevent future confusion

## 🚫 Branch-Specific Anti-Patterns

### ❌ **Repeated Security Flag Complaints**
**Issue**: AI repeatedly flagging `--dangerously-skip-permissions` after user explicitly approved it
**Example**: 
```
# Previous AI behavior
Critical security vulnerability: --dangerously-skip-permissions detected
```

### ✅ **Respectful Security Assessment**
**Solution**: Acknowledge user decision while providing balanced security perspective
**Example**:
```
# Correct approach
User has explicitly approved --dangerously-skip-permissions flag usage.
Providing security context without overriding user judgment.
```

### ❌ **Ignoring User Security Feedback**
**Issue**: Continuing to treat user-approved flags as critical vulnerabilities
**Context**: User corrected AI assessment multiple times

### ✅ **Adaptive Security Analysis**
**Solution**: Incorporate user feedback into security assessment approach
**Learning**: User's security boundaries may differ from default AI assumptions

## 📋 Implementation Patterns for This Branch

### Documentation Enhancement Patterns
- **Explicit Policy Documentation**: Clear ❌/✅ patterns for behavioral guidance
- **Context Inclusion**: Provide reasoning behind security policy decisions
- **Mandatory Indicators**: Use ⚠️ MANDATORY for enforcement clarity

### Security Review Patterns
- **Balanced Assessment**: Present security considerations without overriding user judgment
- **Context-Aware Analysis**: Consider user's explicit decisions in security evaluation
- **Educational Approach**: Explain security implications while respecting boundaries

## 🔧 Specific Implementation Guidelines

### When Reviewing Security-Related Changes
1. **Check for user context** - Has user previously made explicit security decisions?
2. **Acknowledge decisions** - Respect documented user security boundaries
3. **Provide education** - Explain security implications without being prescriptive
4. **Suggest alternatives** - Offer safer approaches where applicable without demanding changes

### Documentation Standards
- Use clear ❌/✅ patterns for behavioral guidance
- Include context and rationale for policy decisions
- Structure with proper emoji indicators for scanning efficiency
- Maintain consistency with existing CLAUDE.md patterns

## 🛡️ Security Context

### DANGEROUSLY-SKIP-PERMISSIONS Flag Policy
**User Decision**: Explicitly approved usage with documented rationale
**Context**: User corrected AI assessment after repeated security complaints
**Approach**: Provide balanced security perspective without overriding judgment
**Learning**: Adapt security analysis to respect informed user decisions

## 📊 Quality Metrics

- **User Frustration Reduction**: Eliminate repeated complaints about approved decisions
- **Documentation Clarity**: Clear behavioral guidance for AI assistants
- **Security Balance**: Maintain security awareness without overreach
- **Workflow Efficiency**: Reduce noise in security reviews

## 🔄 Review Process

This branch demonstrates the importance of:
1. **Listening to user feedback** on security assessments
2. **Adapting AI behavior** based on user corrections
3. **Documenting decisions** to prevent repeated issues
4. **Balancing security** with user autonomy

## 📈 Success Indicators

- ✅ Reduced AI complaints about user-approved security decisions
- ✅ Maintained security awareness without overriding user judgment
- ✅ Clear documentation of security policy rationale
- ✅ Improved AI-user collaboration on security boundaries