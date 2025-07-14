#!/usr/bin/env python3
"""
Analyze git statistics to calculate real development metrics.
Filters out vendor files, generated content, and large data files.
"""

import subprocess
import re
from collections import defaultdict
from datetime import datetime, timezone
import sys

# Patterns to exclude from statistics
EXCLUDE_PATTERNS = [
    r'venv/',
    r'node_modules/',
    r'discovery_cache/',
    r'_snapshot\.txt',
    r'5e_SRD_All\.md',
    r'_Campaign.*\.txt',
    r'temp/',
    r'tmp/',
    r'\.pyc$',
    r'__pycache__/',
    r'\.git/',
    r'test_venv/',
    r'coverage_html',
    r'htmlcov/',
    r'\.coverage',
]

def should_exclude(filepath):
    """Check if a file should be excluded from statistics."""
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, filepath):
            return True
    return False

def run_git_command(cmd):
    """Run a git command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{cmd}': {e.stderr}")
        sys.exit(1)

def analyze_commits():
    """Analyze commit patterns."""
    # Get all commits in date range
    commits = run_git_command(
        "git log --since='2025-06-15' --until='2025-07-14' --format='%H|%ai|%s'"
    ).split('\n')
    
    commit_types = defaultdict(int)
    commits_by_day = defaultdict(int)
    
    for commit in commits:
        if not commit:
            continue
        
        hash_val, date_str, message = commit.split('|', 2)
        date = datetime.fromisoformat(date_str.replace(' ', 'T'))
        
        # Remove timezone info for comparison
        date = date.replace(tzinfo=None)
        
        # Categorize commit
        if message.lower().startswith('fix:') or message.lower().startswith('fix '):
            commit_types['fixes'] += 1
        elif message.lower().startswith('feat:') or message.lower().startswith('feature:'):
            commit_types['features'] += 1
        elif message.lower().startswith('refactor:'):
            commit_types['refactors'] += 1
        elif message.lower().startswith('docs:'):
            commit_types['docs'] += 1
        elif message.lower().startswith('test:'):
            commit_types['tests'] += 1
        else:
            commit_types['other'] += 1
        
        # Count by day
        day_key = date.strftime('%Y-%m-%d')
        commits_by_day[day_key] += 1
    
    return len(commits), commit_types, commits_by_day

def analyze_file_changes():
    """Analyze file changes excluding vendor files."""
    # Get all file changes
    changes = run_git_command(
        "git log --since='2025-06-15' --until='2025-07-14' --numstat --format=''"
    ).strip().split('\n')
    
    total_added = 0
    total_deleted = 0
    files_changed = set()
    excluded_lines = 0
    
    for line in changes:
        if not line or line.startswith('-'):
            continue
        
        parts = line.split('\t')
        if len(parts) != 3:
            continue
        
        added, deleted, filepath = parts
        
        # Skip binary files
        if added == '-' or deleted == '-':
            continue
        
        # Check if file should be excluded
        if should_exclude(filepath):
            excluded_lines += int(added) + int(deleted)
            continue
        
        total_added += int(added)
        total_deleted += int(deleted)
        files_changed.add(filepath)
    
    return total_added, total_deleted, len(files_changed), excluded_lines

def main():
    """Main analysis function."""
    print("Analyzing git statistics (excluding vendor/generated files)...")
    print("=" * 60)
    
    # Analyze commits
    total_commits, commit_types, commits_by_day = analyze_commits()
    
    # Analyze file changes
    added, deleted, file_count, excluded = analyze_file_changes()
    
    # Calculate statistics
    total_lines = added + deleted
    days = 29  # June 15 - July 14
    
    print(f"\nCommit Analysis:")
    print(f"  Total commits: {total_commits}")
    print(f"  Average per day: {total_commits / days:.1f}")
    print(f"\nCommit Types:")
    for ctype, count in sorted(commit_types.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_commits) * 100
        print(f"  {ctype.capitalize()}: {count} ({percentage:.1f}%)")
    
    print(f"\nCode Changes (Real Code Only):")
    print(f"  Lines added: {added:,}")
    print(f"  Lines deleted: {deleted:,}")
    print(f"  Total lines changed: {total_lines:,}")
    print(f"  Files modified: {file_count:,}")
    print(f"  Lines excluded (vendor/generated): {excluded:,}")
    
    print(f"\nDaily Averages:")
    print(f"  Lines changed per day: {total_lines / days:,.0f}")
    print(f"  Files changed per day: {file_count / days:.0f}")
    
    # Calculate noise ratio
    total_with_vendor = total_lines + excluded
    noise_ratio = (excluded / total_with_vendor) * 100 if total_with_vendor > 0 else 0
    print(f"\nNoise Ratio:")
    print(f"  Vendor/generated files: {noise_ratio:.1f}% of all changes")
    
    # Find most productive days
    print(f"\nTop 5 Most Productive Days:")
    for day, count in sorted(commits_by_day.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {day}: {count} commits")

if __name__ == "__main__":
    main()