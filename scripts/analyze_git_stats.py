#!/usr/bin/env python3
"""
Analyze git statistics excluding vendor/generated files.
Provides real development metrics by filtering out noise.
"""

import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta

# Patterns to exclude from statistics
EXCLUDE_PATTERNS = [
    r"venv/",
    r"node_modules/",
    r"discovery_cache/",
    r"_snapshot\.txt$",
    r"5e_SRD_All\.md$",
    r"_Campaign.*\.txt$",
    r"temp/",
    r"\.min\.js$",
    r"\.min\.css$",
    r"package-lock\.json$",
    r"yarn\.lock$",
    r"\.pyc$",
    r"__pycache__/",
    r"coverage/",
    r"htmlcov/",
    r"\.pytest_cache/",
]


def run_git_command(cmd):
    """Run a git command and return output."""
    try:
        result = subprocess.run(
            cmd, check=False, shell=True, capture_output=True, text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {cmd}")
        print(f"Error: {e}")
        return ""
    except Exception as e:
        print(f"Unexpected error running command: {cmd}")
        print(f"Error type: {type(e).__name__}, Error: {e}")
        return ""


def should_exclude_file(filepath):
    """Check if file should be excluded from stats."""
    return any(re.search(pattern, filepath) for pattern in EXCLUDE_PATTERNS)


def analyze_commits(since_date):
    """Analyze commits since given date."""
    # Get all commits
    cmd = f'git log --since="{since_date}" --pretty=format:"%H|%ad|%s" --date=short'
    commits = run_git_command(cmd).split("\n")

    total_commits = len([c for c in commits if c])

    # Group by date
    commits_by_date = defaultdict(int)
    fix_commits = 0
    feature_commits = 0

    for commit in commits:
        if not commit:
            continue
        parts = commit.split("|", 2)
        if len(parts) >= 2:
            date = parts[1]
            commits_by_date[date] += 1

            if len(parts) >= 3:
                message = parts[2].lower()
                if "fix:" in message or "fix(" in message or "bugfix" in message:
                    fix_commits += 1
                elif "feat:" in message or "feature" in message or "add" in message:
                    feature_commits += 1

    return {
        "total": total_commits,
        "by_date": dict(commits_by_date),
        "fix_commits": fix_commits,
        "feature_commits": feature_commits,
        "other_commits": total_commits - fix_commits - feature_commits,
    }


def analyze_prs(since_date):
    """Analyze PRs since given date."""
    cmd = (
        "gh pr list --state merged --limit 1000 --json number,title,createdAt,mergedAt"
    )
    output = run_git_command(cmd)

    if not output:
        return {"total": 0, "by_type": {}}

    try:
        prs = json.loads(output)
    except:
        return {"total": 0, "by_type": {}}

    # Filter by date
    since_dt = datetime.fromisoformat(since_date.replace(" ", "T"))
    filtered_prs = []

    for pr in prs:
        if pr.get("createdAt"):
            # Remove timezone info for comparison
            created_str = (
                pr["createdAt"].replace("Z", "").replace("T", " ").split(".")[0]
            )
            try:
                created = datetime.fromisoformat(created_str)
                if created >= since_dt:
                    filtered_prs.append(pr)
            except (ValueError, AttributeError) as e:
                print(f"Failed to parse PR date: {e}")
                continue

    # Categorize PRs
    pr_types = defaultdict(int)
    for pr in filtered_prs:
        title = pr.get("title", "").lower()
        if "fix" in title:
            pr_types["fixes"] += 1
        elif "feat" in title or "add" in title:
            pr_types["features"] += 1
        elif "refactor" in title:
            pr_types["refactoring"] += 1
        elif "test" in title:
            pr_types["tests"] += 1
        elif "doc" in title:
            pr_types["documentation"] += 1
        else:
            pr_types["other"] += 1

    return {"total": len(filtered_prs), "by_type": dict(pr_types)}


def analyze_changes(since_date):
    """Analyze line changes since given date."""
    cmd = f'git log --since="{since_date}" --numstat --pretty=format:""'
    output = run_git_command(cmd)

    added = 0
    deleted = 0
    files_changed = 0
    excluded_added = 0
    excluded_deleted = 0
    excluded_files = 0

    for line in output.split("\n"):
        if not line or line.isspace():
            continue

        parts = line.split("\t")
        if len(parts) != 3:
            continue

        try:
            adds = int(parts[0]) if parts[0] != "-" else 0
            dels = int(parts[1]) if parts[1] != "-" else 0
            filepath = parts[2]

            if should_exclude_file(filepath):
                excluded_added += adds
                excluded_deleted += dels
                excluded_files += 1
            else:
                added += adds
                deleted += dels
                files_changed += 1
        except (ValueError, IndexError):
            # Skip lines that can't be parsed (e.g., binary files)
            continue

    return {
        "added": added,
        "deleted": deleted,
        "total": added + deleted,
        "files": files_changed,
        "excluded": {
            "added": excluded_added,
            "deleted": excluded_deleted,
            "total": excluded_added + excluded_deleted,
            "files": excluded_files,
        },
    }


def get_codebase_size():
    """Get current codebase size."""
    # Count lines in actual code files
    cmd = 'find . -type f \\( -name "*.py" -o -name "*.js" -o -name "*.html" -o -name "*.css" \\) -not -path "*/venv/*" -not -path "*/node_modules/*" -not -path "*/__pycache__/*" | xargs wc -l | tail -1'
    output = run_git_command(cmd)

    try:
        return int(output.split()[0])
    except (IndexError, ValueError):
        return 0


def main():
    if len(sys.argv) > 1:
        since_date = sys.argv[1]
    else:
        # Default to 30 days ago
        since_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    print(f"Analyzing git statistics since {since_date}...")
    print("=" * 60)

    # Get current branch
    branch = run_git_command("git branch --show-current")
    print(f"Current branch: {branch}")
    print()

    # Analyze commits
    commits = analyze_commits(since_date)
    days = len(commits["by_date"])

    print("## Commit Statistics")
    print(f"Total commits: {commits['total']}")
    print(f"Days with commits: {days}")
    print(f"Average commits/day: {commits['total'] / days:.1f}" if days > 0 else "N/A")
    print("\nCommit types:")
    print(
        f"  - Fix commits: {commits['fix_commits']} ({commits['fix_commits'] / commits['total'] * 100:.1f}%)"
    )
    print(
        f"  - Feature commits: {commits['feature_commits']} ({commits['feature_commits'] / commits['total'] * 100:.1f}%)"
    )
    print(
        f"  - Other commits: {commits['other_commits']} ({commits['other_commits'] / commits['total'] * 100:.1f}%)"
    )
    print()

    # Analyze PRs
    prs = analyze_prs(since_date)
    print("## Pull Request Statistics")
    print(f"Total merged PRs: {prs['total']}")
    print(f"Average PRs/day: {prs['total'] / days:.1f}" if days > 0 else "N/A")
    print("\nPR types:")
    for pr_type, count in prs["by_type"].items():
        percentage = (count / prs["total"] * 100) if prs["total"] > 0 else 0
        print(f"  - {pr_type.capitalize()}: {count} ({percentage:.1f}%)")
    print()

    # Analyze changes
    changes = analyze_changes(since_date)
    print("## Code Change Statistics (Excluding Vendor/Generated Files)")
    print(f"Lines added: {changes['added']:,}")
    print(f"Lines deleted: {changes['deleted']:,}")
    print(f"Total changes: {changes['total']:,}")
    print(f"Files changed: {changes['files']:,}")
    print(f"Average changes/day: {changes['total'] / days:,.0f}" if days > 0 else "N/A")
    print()

    # Get codebase size and calculate ratios
    codebase_size = get_codebase_size()
    if codebase_size > 0:
        print("## Change Ratios")
        print(f"Current codebase size: {codebase_size:,} lines")
        print(f"Change ratio: {changes['total'] / codebase_size:.2f}:1")
        print(f"(Changed {changes['total'] / codebase_size:.1%} of the codebase)")
    print()

    # Show excluded stats
    print("## Excluded from Statistics")
    print(f"Vendor/generated lines added: {changes['excluded']['added']:,}")
    print(f"Vendor/generated lines deleted: {changes['excluded']['deleted']:,}")
    print(f"Total excluded changes: {changes['excluded']['total']:,}")
    print(f"Files excluded: {changes['excluded']['files']:,}")

    # Calculate noise ratio
    total_all = changes["total"] + changes["excluded"]["total"]
    if total_all > 0:
        noise_ratio = changes["excluded"]["total"] / total_all * 100
        print(
            f"\nNoise ratio: {noise_ratio:.1f}% of changes were vendor/generated files"
        )

    print("\n" + "=" * 60)
    print("Note: Fix commits are identified by 'fix:', 'fix(', or 'bugfix' in message")
    print("Feature commits are identified by 'feat:', 'feature', or 'add' in message")


if __name__ == "__main__":
    main()
