# ⚠️ REFERENCE ONLY - Requires adaptation for your project setup

# /exportcommands - Export Claude Commands to Reference Repository

**Purpose**: Comprehensive export workflow to https://github.com/jleechanorg/claude-commands for reference and sharing

**Usage**: `/exportcommands` - Executes complete export pipeline with Git operations

## 🚨 EXPORT PROTOCOL

### Phase 1: Preparation & Validation

**Repository Access Verification**:
- Validate GitHub token and permissions for target repository
- Check if target repository exists and is accessible
- Create local staging directory: `/tmp/claude_commands_export_$(date +%s)/`
- Verify Git configuration for commit operations

**Content Filtering Setup**:
- Initialize export filter to exclude mvp_site specific content
- Prepare content transformation rules for generalization
- Set up warning header templates for exported files

### Phase 2: Content Export & Transformation

**CLAUDE.md Export**:
```bash
# Add reference-only warning header
cat > staging/CLAUDE.md << 'EOF'
# ⚠️ REFERENCE ONLY - DO NOT USE DIRECTLY

**WARNING**: This is a reference export from a specific project setup. These configurations:
- May contain project-specific paths and settings
- Have not been tested in isolation
- May require significant adaptation for your environment
- Include setup-specific assumptions and dependencies

Use this as inspiration and reference, not direct implementation.

---

EOF
# Append original CLAUDE.md with project-specific content filtered
```

**Commands Export** (`.claude/commands/` → `commands/`):
- Export all 70+ command definitions with proper categorization
- Transform hardcoded paths to generic placeholders
- Add compatibility warnings for project-specific commands
- Organize by category: cognitive, operational, testing, development, meta

**Scripts Export** (`claude_command_scripts/` → `scripts/`):
- Export script implementations with dependency documentation
- Transform mvp_site paths to generic PROJECT_ROOT placeholders
- Add setup requirements documentation for each script
- Include execution environment requirements

**Orchestration Export** (`orchestration/` → `orchestration/`):
- Export complete agent system with Redis requirements
- Document system architecture and setup requirements
- Include monitoring and recovery procedures
- Add scaling and customization guidance

**Configuration Export**:
- Export relevant config files (filtered for sensitive data)
- Include setup templates and environment examples
- Document MCP server requirements and configuration
- Provide installation verification procedures

### Phase 3: Documentation Generation

**README Generation**:
- Use comprehensive structure from subagent research
- Include prominent warning about reference-only status
- Add detailed installation instructions with prerequisites
- Document command categories and composition principles
- Include troubleshooting and adaptation guidance

**Support Documentation**:
- Generate installation guide with step-by-step procedures
- Create configuration templates for different environments
- Include troubleshooting guide with common issues
- Provide usage examples with progressive complexity

### Phase 4: Git Operations & Publishing

**Repository Management**:
```bash
# Clone or update target repository
gh repo clone jleechanorg/claude-commands /tmp/claude_commands_repo
cd /tmp/claude_commands_repo

# Create export branch
export_branch="export-$(date +%Y%m%d-%H%M%S)"
git checkout -b "$export_branch"

# Copy exported content
cp -r /tmp/claude_commands_export_*/. .

# Commit changes
git add .
git commit -m "Export Claude commands and configurations

- CLAUDE.md with reference warnings
- All command definitions with categorization  
- Scripts with dependency documentation
- Orchestration system with setup guides
- Comprehensive README and documentation

⚠️ Reference export - requires adaptation for other projects"

# Push and create PR
git push -u origin "$export_branch"
gh pr create --title "Claude Commands Export $(date +%Y-%m-%d)" \
  --body "Automated export of Claude command system for reference.

## ⚠️ Reference Only
This export contains project-specific configurations that require adaptation.

## Contents
- Complete command system (70+ commands)
- Orchestration infrastructure 
- Supporting scripts and utilities
- Documentation and setup guides

## Usage
See README.md for installation and adaptation guidance."
```

**Verification**:
- Confirm PR creation and return link
- Validate exported content structure
- Test basic command loading in clean environment
- Document any export-specific issues or requirements

## Content Transformation Rules

**Path Generalization**:
- `$PROJECT_ROOT/` → `$PROJECT_ROOT/`
- `/home/jleechan/projects/worldarchitect.ai/` → `$WORKSPACE_ROOT/`
- Hardcoded file paths → Environment variable placeholders

**Project References**:
- `WorldArchitect.AI` → `Your Project`
- `D&D/RPG` specific → Generic game/app references
- Firebase/Firestore → Generic database references

**Command Adaptations**:
- Testing commands: Add environment setup requirements
- Deployment commands: Generalize for different platforms
- Integration commands: Document external dependencies

## Error Handling

**Repository Access Issues**:
- Validate GitHub token setup
- Check repository permissions
- Provide manual export fallback instructions

**Content Export Failures**:
- Log specific file processing errors
- Continue export with warnings for failed items
- Provide recovery procedures for partial exports

**Git Operation Failures**:
- Handle branch conflicts and naming issues
- Provide manual Git workflow instructions
- Include rollback procedures for failed operations

## Memory Enhancement

This command automatically searches Memory MCP for:
- Previous export experiences and lessons learned
- Command adaptation patterns and successful transformations
- Documentation improvements and user feedback
- Repository maintenance and update procedures

## Success Criteria

**Export Completion Verification**:
- All major content categories exported successfully
- README and documentation generated
- Git operations completed (branch, commit, push, PR)
- PR link returned to user for verification

**Content Quality Validation**:
- Reference warnings prominently displayed
- Project-specific content appropriately generalized
- Installation instructions comprehensive and testable
- Command categories properly organized

**Memory Enhancement**: This command automatically searches memory context using Memory MCP for relevant export experiences, adaptation patterns, and lessons learned from previous command sharing initiatives.