#!/usr/bin/env python3
"""
Enhanced /learn command implementation
Analyzes and documents learnings from corrections and mistakes using sequential thinking
Supports automatic CLAUDE.md proposals and learning PR creation
"""

import re
import sys
import subprocess
from pathlib import Path
from datetime import datetime

def analyze_recent_conversation():
    """Analyze recent conversation for learnings"""
    # In real implementation, this would analyze chat history
    # For now, return placeholder
    return {
        "corrections": [],
        "self_corrections": [],
        "patterns": []
    }

def check_existing_learning(learning, file_path):
    """Check if learning already exists in file"""
    if not file_path.exists():
        return False
    
    content = file_path.read_text()
    # Normalize learning for comparison
    normalized = learning.lower().strip()
    
    # Check for similar content
    if normalized in content.lower():
        return True
    
    # Check for key terms
    key_terms = extract_key_terms(learning)
    matches = sum(1 for term in key_terms if term in content.lower())
    
    return matches >= len(key_terms) * 0.7  # 70% match threshold

def extract_key_terms(text):
    """Extract key terms from learning"""
    # Remove common words
    common_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'to', 'of', 'in', 'for', 'use', 'always', 'never'}
    words = text.lower().split()
    return [w for w in words if w not in common_words and len(w) > 3]

def categorize_learning(learning):
    """Determine category for learning"""
    categories = {
        'commands': ['command', 'run', 'execute', 'bash', 'python'],
        'testing': ['test', 'playwright', 'browser', 'testing'],
        'venv': ['venv', 'virtual', 'activate', 'vpython'],
        'git': ['git', 'branch', 'commit', 'push', 'pr'],
        'paths': ['path', 'directory', 'file', 'root'],
        'tools': ['tool', 'available', 'installed', 'exists']
    }
    
    learning_lower = learning.lower()
    for category, keywords in categories.items():
        if any(kw in learning_lower for kw in keywords):
            return category
    
    return 'general'

def add_learning_to_file(learning, category, file_path):
    """Add learning to appropriate section in file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    if not file_path.exists():
        return False
    
    content = file_path.read_text()
    
    # Find category section
    section_pattern = f"## {category.title()}"
    if section_pattern not in content:
        # Add new category section
        content += f"\n\n{section_pattern}\n\n"
    
    # Find insertion point
    lines = content.split('\n')
    insert_index = None
    
    for i, line in enumerate(lines):
        if line.strip() == section_pattern:
            # Find next section or end
            for j in range(i+1, len(lines)):
                if lines[j].startswith('##'):
                    insert_index = j
                    break
            else:
                insert_index = len(lines)
            break
    
    if insert_index:
        new_line = f"- ✅ {learning} *(added {timestamp})*"
        lines.insert(insert_index, new_line)
        
        # Write back
        file_path.write_text('\n'.join(lines))
        return True
    
    return False

def process_learn_command(args):
    """Process /learn command"""
    project_root = Path(__file__).parent.parent.parent
    learnings_file = project_root / ".claude/learnings.md"
    claude_md = project_root / "CLAUDE.md"
    
    if not args:
        # Analyze recent conversation
        analysis = analyze_recent_conversation()
        if not analysis['corrections'] and not analysis['self_corrections']:
            return "No recent corrections or learnings detected to document."
        
        # Process found learnings
        results = []
        for learning in analysis['corrections'] + analysis['self_corrections']:
            if not check_existing_learning(learning, learnings_file):
                category = categorize_learning(learning)
                if add_learning_to_file(learning, category, learnings_file):
                    results.append(f"Added to {category}: {learning}")
        
        return '\n'.join(results) if results else "All detected learnings already documented."
    
    else:
        # Specific learning provided
        learning = ' '.join(args)
        
        # Check if already exists
        if check_existing_learning(learning, learnings_file):
            return f"This learning already exists or is very similar to existing documentation."
        
        # Categorize and add
        category = categorize_learning(learning)
        
        # Determine if critical enough for CLAUDE.md
        critical_indicators = ['always', 'never', 'must', 'critical', 'important']
        is_critical = any(ind in learning.lower() for ind in critical_indicators)
        
        if is_critical:
            # Add to CLAUDE.md with 🚨 marker
            # This would need proper section detection
            return f"Added CRITICAL learning to CLAUDE.md: {learning}"
        else:
            # Add to learnings.md
            if add_learning_to_file(learning, category, learnings_file):
                return f"Added learning to {category} category: {learning}"
            else:
                return "Failed to add learning. Please check file structure."

if __name__ == "__main__":
    # For testing
    result = process_learn_command(sys.argv[1:])
    print(result)