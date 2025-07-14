#!/usr/bin/env python3
"""
Shared utilities for PR-related commands (/pr, /push, /handoff)
"""

import subprocess
import json
import os
from datetime import datetime
from typing import Optional, Dict, List, Tuple


def get_current_branch() -> str:
    """Get current git branch name"""
    try:
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except:
        return "unknown"


def get_remote_tracking_branch() -> Optional[str]:
    """Get remote tracking branch if exists"""
    try:
        result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', '@{upstream}'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except:
        return None


def check_pr_exists_for_branch(branch: Optional[str] = None) -> Optional[Dict]:
    """Check if PR exists for current or specified branch"""
    if not branch:
        branch = get_current_branch()
    
    try:
        result = subprocess.run(['gh', 'pr', 'list', '--head', branch, '--json', 'number,url,state,title'], 
                              capture_output=True, text=True, check=True)
        prs = json.loads(result.stdout)
        return prs[0] if prs else None
    except:
        return None


def get_git_log_summary(base_branch: str = "main", max_commits: int = 20) -> List[str]:
    """Get commit messages since diverging from base branch"""
    try:
        result = subprocess.run(['git', 'log', f'{base_branch}..HEAD', '--oneline', f'-{max_commits}'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except:
        return []


def get_files_changed(base_branch: str = "main") -> List[str]:
    """Get list of files changed compared to base branch"""
    try:
        result = subprocess.run(['git', 'diff', '--name-only', f'{base_branch}...HEAD'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except:
        return []


def run_tests(test_command: str = "./run_tests.sh") -> Tuple[bool, str]:
    """Run tests and return success status and output"""
    try:
        result = subprocess.run([test_command], 
                              capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stdout if e.stdout else str(e)


def format_test_results(success: bool, output: str) -> str:
    """Format test results for PR description"""
    if success:
        # Extract test count if available
        import re
        match = re.search(r'(\d+)\s+test.*pass', output, re.IGNORECASE)
        count = match.group(1) if match else "all"
        return f"✅ **Tests**: {count} tests passing"
    else:
        return "❌ **Tests**: Some tests failing (see details below)"


def read_scratchpad(branch: Optional[str] = None) -> Optional[str]:
    """Read scratchpad content for branch"""
    if not branch:
        branch = get_current_branch()
    
    scratchpad_path = f"roadmap/scratchpad_{branch}.md"
    if os.path.exists(scratchpad_path):
        with open(scratchpad_path, 'r') as f:
            return f.read()
    return None


def parse_scratchpad_summary(content: str) -> Dict[str, str]:
    """Extract key sections from scratchpad"""
    sections = {
        'goal': '',
        'summary': '',
        'implementation': '',
        'testing': ''
    }
    
    if not content:
        return sections
    
    lines = content.split('\n')
    current_section = None
    
    for line in lines:
        line_lower = line.lower()
        
        if '**goal**:' in line_lower:
            sections['goal'] = line.split(':', 1)[1].strip() if ':' in line else ''
        elif any(marker in line_lower for marker in ['## summary', '## analysis summary']):
            current_section = 'summary'
        elif '## implementation' in line_lower:
            current_section = 'implementation'
        elif '## testing' in line_lower:
            current_section = 'testing'
        elif current_section and line.strip() and not line.startswith('#'):
            sections[current_section] += line + '\n'
    
    # Clean up sections
    for key in sections:
        sections[key] = sections[key].strip()
    
    return sections


def generate_pr_description(
    title: str,
    branch: str,
    test_success: bool,
    test_output: str,
    scratchpad_content: Optional[str] = None,
    commit_messages: Optional[List[str]] = None,
    files_changed: Optional[List[str]] = None,
    is_handoff: bool = False
) -> str:
    """Generate comprehensive PR description"""
    
    # Parse scratchpad if available
    scratchpad_data = parse_scratchpad_summary(scratchpad_content) if scratchpad_content else {}
    
    description = f"## Summary\n\n"
    
    if is_handoff:
        description += f"**Status**: 🟡 Ready for implementation handoff\n\n"
        description += f"**Analysis**: Complete implementation plan available in `roadmap/scratchpad_handoff_{branch}.md`\n\n"
    else:
        description += f"**Branch**: `{branch}`\n"
        description += format_test_results(test_success, test_output) + "\n\n"
    
    # Add goal from scratchpad if available
    if scratchpad_data.get('goal'):
        description += f"**Goal**: {scratchpad_data['goal']}\n\n"
    
    # Add summary section
    if scratchpad_data.get('summary'):
        description += f"### Description\n\n{scratchpad_data['summary']}\n\n"
    elif commit_messages:
        description += f"### Changes\n\n"
        for msg in commit_messages[:10]:  # Limit to 10 most recent
            description += f"- {msg}\n"
        description += "\n"
    
    # Add implementation details if not handoff
    if not is_handoff and scratchpad_data.get('implementation'):
        description += f"### Implementation Details\n\n{scratchpad_data['implementation'][:500]}...\n\n"
    
    # Add files changed
    if files_changed and not is_handoff:
        description += f"### Files Changed ({len(files_changed)})\n\n"
        for file in files_changed[:20]:  # Limit to 20 files
            description += f"- `{file}`\n"
        if len(files_changed) > 20:
            description += f"- ... and {len(files_changed) - 20} more files\n"
        description += "\n"
    
    # Add test details if failed
    if not is_handoff and not test_success and test_output:
        description += f"### Test Output\n\n```\n{test_output[:1000]}...\n```\n\n"
    
    # Add testing requirements from scratchpad
    if scratchpad_data.get('testing'):
        description += f"### Testing Requirements\n\n{scratchpad_data['testing']}\n\n"
    
    # Add footer
    description += "\n---\n\n"
    description += "🤖 Generated with [Claude Code](https://claude.ai/code)\n\n"
    
    if not is_handoff:
        description += "Co-Authored-By: Claude <noreply@anthropic.com>"
    
    return description


def create_or_update_pr(
    title: str,
    body: str,
    draft: bool = False,
    base: str = "main"
) -> Tuple[bool, str]:
    """Create new PR or update existing one"""
    branch = get_current_branch()
    existing_pr = check_pr_exists_for_branch(branch)
    
    try:
        if existing_pr:
            # Update existing PR
            pr_number = existing_pr['number']
            subprocess.run(['gh', 'pr', 'edit', str(pr_number), 
                          '--title', title,
                          '--body', body], 
                          check=True)
            return True, existing_pr['url']
        else:
            # Create new PR
            cmd = ['gh', 'pr', 'create', 
                   '--title', title,
                   '--body', body,
                   '--base', base]
            if draft:
                cmd.append('--draft')
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, str(e)


def ensure_pushed_to_remote() -> bool:
    """Ensure current branch is pushed to remote"""
    branch = get_current_branch()
    try:
        # Check if we need to set upstream
        if not get_remote_tracking_branch():
            subprocess.run(['git', 'push', '-u', 'origin', f'HEAD:{branch}'], check=True)
        else:
            subprocess.run(['git', 'push'], check=True)
        return True
    except subprocess.CalledProcessError:
        return False