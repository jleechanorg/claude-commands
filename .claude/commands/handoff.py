#!/usr/bin/env python3
"""
/handoff command implementation
Creates structured handoff with PR, scratchpad, roadmap update, and worker prompt
"""

import os
import sys
import subprocess
import json
from datetime import datetime
import uuid

def get_current_branch():
    """Get current git branch name"""
    try:
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except:
        return "unknown"

def get_git_status():
    """Check if there are uncommitted changes"""
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except:
        return ""

def generate_task_id():
    """Generate unique task ID"""
    return f"TASK-{str(uuid.uuid4())[:8].upper()}"

def create_handoff_branch(task_name):
    """Create handoff branch"""
    branch_name = f"handoff-{task_name}"
    try:
        subprocess.run(['git', 'checkout', '-b', branch_name], check=True)
        return branch_name
    except subprocess.CalledProcessError:
        print(f"❌ Failed to create branch {branch_name}")
        return None

def create_scratchpad(task_name, description, analysis_content=""):
    """Create scratchpad document"""
    current_branch = get_current_branch()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    content = f"""# Scratchpad: {task_name.replace('_', ' ').title()}

**Branch**: {current_branch}  
**Goal**: {description}  
**Status**: Analysis complete, ready for implementation handoff  
**Created**: {timestamp}

## Problem Statement

{description}

## Analysis Summary

{analysis_content if analysis_content else "Add analysis details here..."}

## Implementation Plan

### Step 1: [First Implementation Step]
- [ ] Specific action item
- [ ] Another action item

### Step 2: [Second Implementation Step]  
- [ ] Specific action item
- [ ] Another action item

### Step 3: [Testing & Validation]
- [ ] Unit tests
- [ ] Integration tests  
- [ ] Manual verification

## Files to Modify

- `file1.py`: Description of changes needed
- `file2.py`: Description of changes needed

## Testing Requirements

1. **Unit Tests**: Description of test requirements
2. **Integration Tests**: Description of integration test needs
3. **Manual Verification**: Steps to manually verify solution

## Context for Next Worker

This task is ready for implementation. The analysis phase is complete and the implementation approach is defined.

## Dependencies

- No blocking dependencies
- Related to: [Reference any related tasks/PRs]

## Definition of Done

- [ ] Implementation complete
- [ ] All tests passing
- [ ] Code review complete
- [ ] Documentation updated if needed

## Branch Status

- **Analysis**: ✅ Complete
- **Implementation**: ⏳ Ready for handoff
- **Testing**: ⏳ Pending implementation
"""
    
    filename = f"roadmap/scratchpad_handoff_{task_name}.md"
    with open(filename, 'w') as f:
        f.write(content)
    
    return filename

def update_roadmap(task_name, description):
    """Update roadmap.md with new handoff task"""
    task_id = generate_task_id()
    
    # Read current roadmap
    with open('roadmap/roadmap.md', 'r') as f:
        content = f.read()
    
    # Find the "Next Priority Tasks" section and add new item
    lines = content.split('\n')
    new_lines = []
    added = False
    
    for line in lines:
        new_lines.append(line)
        if not added and line.startswith('### Next Priority Tasks (Ready to Start)'):
            new_lines.append(f"- **{task_id}** 🟡 {description} - HANDOFF READY")
            added = True
    
    # Write back to file
    with open('roadmap/roadmap.md', 'w') as f:
        f.write('\n'.join(new_lines))
    
    return task_id

def create_pr(task_name, description, scratchpad_file):
    """Create GitHub PR"""
    branch_name = get_current_branch()
    
    pr_body = f"""## Handoff Task

**Task**: {description}

**Status**: Ready for implementation handoff

## Analysis

Complete analysis and implementation plan available in `{scratchpad_file}`.

## Implementation Required

See scratchpad for detailed implementation steps, files to modify, and testing requirements.

## Ready for Assignment

This task has been analyzed and is ready for a worker to pick up and implement.

🤖 Generated with [Claude Code](https://claude.ai/code)
"""
    
    try:
        # Commit scratchpad first
        subprocess.run(['git', 'add', scratchpad_file, 'roadmap/roadmap.md'], check=True)
        subprocess.run(['git', 'commit', '-m', f'Add handoff task: {description}\\n\\n🤖 Generated with [Claude Code](https://claude.ai/code)\\n\\nCo-Authored-By: Claude <noreply@anthropic.com>'], check=True)
        
        # Push branch
        subprocess.run(['git', 'push', 'origin', f'HEAD:{branch_name}'], check=True)
        
        # Create PR
        result = subprocess.run(['gh', 'pr', 'create', 
                               '--title', f'Handoff: {description}',
                               '--body', pr_body], 
                              capture_output=True, text=True, check=True)
        
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create PR: {e}")
        return None

def create_new_roadmap_branch():
    """Create new clean branch for continued work"""
    timestamp = int(datetime.now().timestamp())
    branch_name = f"roadmap{timestamp}"
    
    try:
        subprocess.run(['git', 'checkout', 'main'], check=True)
        subprocess.run(['git', 'pull', 'origin', 'main'], check=True)
        subprocess.run(['git', 'checkout', '-b', branch_name], check=True)
        return branch_name
    except subprocess.CalledProcessError:
        print(f"❌ Failed to create new roadmap branch")
        return None

def generate_worker_prompt(task_name, description, pr_url, scratchpad_file):
    """Generate worker prompt"""
    return f"""## Worker Assignment

**Task**: {description}

**Reference**: {pr_url}

**Analysis**: Complete implementation plan available in `{scratchpad_file}`

**Status**: Ready for implementation

### Quick Summary
- Analysis phase complete
- Implementation approach defined  
- Files to modify identified
- Testing strategy documented

### Deliverables
1. Implement solution per scratchpad plan
2. Write/update tests as specified
3. Verify all tests pass
4. Submit for code review

### Getting Started
1. Check out the handoff branch or read the scratchpad for full details
2. Review implementation plan in `{scratchpad_file}`
3. Follow step-by-step implementation guide
4. Run tests to verify solution

The analysis is complete - this is ready for implementation."""

def main():
    if len(sys.argv) < 3:
        print("Usage: /handoff [task_name] [description]")
        print("Example: /handoff logging_fix 'Add file logging configuration to main application'")
        return

    task_name = sys.argv[1]
    description = " ".join(sys.argv[2:])
    
    print(f"🚀 Creating handoff for: {description}")
    
    # Check for uncommitted changes
    if get_git_status():
        print("⚠️  Warning: You have uncommitted changes. Commit them first.")
        return
    
    # Create handoff branch
    print("📝 Creating handoff branch...")
    handoff_branch = create_handoff_branch(task_name)
    if not handoff_branch:
        return
    
    # Create scratchpad
    print("📋 Creating scratchpad...")
    scratchpad_file = create_scratchpad(task_name, description)
    
    # Update roadmap
    print("🗺️  Updating roadmap...")
    task_id = update_roadmap(task_name, description)
    
    # Create PR
    print("🔀 Creating PR...")
    pr_url = create_pr(task_name, description, scratchpad_file)
    if not pr_url:
        return
    
    # Create new roadmap branch
    print("🌿 Creating new roadmap branch...")
    new_branch = create_new_roadmap_branch()
    
    # Generate worker prompt
    print("\\n" + "="*60)
    print("✅ HANDOFF COMPLETE")
    print("="*60)
    print(f"📋 Scratchpad: {scratchpad_file}")
    print(f"🔀 PR: {pr_url}")
    print(f"🆔 Task ID: {task_id}")
    print(f"🌿 New branch: {new_branch}")
    print("\\n" + "="*60)
    print("📤 WORKER PROMPT (Copy & Paste)")
    print("="*60)
    print(generate_worker_prompt(task_name, description, pr_url, scratchpad_file))

if __name__ == "__main__":
    main()