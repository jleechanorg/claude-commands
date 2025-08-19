# AI Development Guidelines

**MOVED TO CLAUDE.MD**

This document has been consolidated into the main operating protocol for better maintenance and single source of truth.

## 📍 Primary Reference

**All AI development guidelines are now located in:**
→ **[CLAUDE.md](../../CLAUDE.md)**

## 🔧 What's Included in CLAUDE.md

- **Terminal Session Safety** - Scripts must preserve user terminal control
- **Subprocess Security** - Mandatory `shell=False, timeout=30` patterns  
- **Import Standards** - Module-level only, no inline/try-catch imports
- **Tool Selection Hierarchy** - Serena MCP → Read tool → Bash commands
- **Universal Composition Patterns** - Distinguish composition vs embedded implementation
- **Evidence-Based Development** - Always use Read tool vs assuming file contents
- **Mistake Prevention Protocols** - All critical anti-patterns and safety guidelines

## ⚠️ Important Notes

- **Single Source of Truth**: CLAUDE.md contains the complete and current guidelines
- **No Duplication**: This prevents documentation drift and maintenance overhead  
- **Enhanced Coverage**: Additional protocols integrated for comprehensive guidance
- **Active Maintenance**: CLAUDE.md is actively maintained and referenced in daily operations

## 🚀 Quick Start

1. **Read CLAUDE.md** - Complete operating protocol with all guidelines
2. **Follow Tool Hierarchy** - Serena MCP first, then Read tool, then Bash
3. **Apply Safety Patterns** - Terminal preservation, subprocess security
4. **Use Evidence-Based Development** - Verify before assuming

---

**For all AI development guidance, consult [CLAUDE.md](../../CLAUDE.md)**