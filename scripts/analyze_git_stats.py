#!/usr/bin/env python3
"""
Analyze git statistics excluding vendor/generated files.
Provides real development metrics by filtering out noise.
"""

import json
import re
import subprocess
import sys
import statistics
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

    # Create commit objects for weekly analysis
    commit_objects = []
    for commit in commits:
        if not commit:
            continue
        parts = commit.split("|", 2)
        if len(parts) >= 2:
            commit_objects.append({
                "hash": parts[0],
                "date": parts[1],
                "message": parts[2] if len(parts) >= 3 else ""
            })

    return {
        "total": total_commits,
        "by_date": dict(commits_by_date),
        "fix_commits": fix_commits,
        "feature_commits": feature_commits,
        "other_commits": total_commits - fix_commits - feature_commits,
        "commits": commit_objects  # Add commit data for weekly analysis
    }


def analyze_prs(since_date):
    """Analyze PRs since given date."""
    cmd = (
        "gh pr list --state merged --limit 1000 --json number,title,createdAt,mergedAt,closedAt,additions,deletions"
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

    return {
        "total": len(filtered_prs),
        "by_type": dict(pr_types),
        "prs": filtered_prs  # Return the actual PR data for further analysis
    }


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


def parse_github_datetime(datetime_str):
    """Parse GitHub datetime string to datetime object."""
    if not datetime_str:
        return None
    # Remove timezone info for comparison
    clean_str = datetime_str.replace("Z", "").replace("T", " ").split(".")[0]
    try:
        return datetime.fromisoformat(clean_str)
    except (ValueError, AttributeError):
        return None


def calculate_pr_timing_metrics(prs):
    """Calculate PR timing metrics (open to merge/close time)."""
    timing_data = []

    for pr in prs:
        created_at = parse_github_datetime(pr.get("createdAt"))
        merged_at = parse_github_datetime(pr.get("mergedAt"))

        if created_at and merged_at:
            # Calculate time difference in hours
            time_diff = (merged_at - created_at).total_seconds() / 3600
            timing_data.append({
                "pr_number": pr.get("number"),
                "title": pr.get("title", ""),
                "hours": time_diff,
                "days": time_diff / 24
            })

    if not timing_data:
        return {"count": 0, "hours": [], "days": []}

    hours = [item["hours"] for item in timing_data]
    days = [item["days"] for item in timing_data]

    return {
        "count": len(timing_data),
        "hours": hours,
        "days": days,
        "avg_hours": statistics.mean(hours),
        "avg_days": statistics.mean(days),
        "median_hours": statistics.median(hours),
        "median_days": statistics.median(days),
        "p95_hours": statistics.quantiles(hours, n=100)[94] if len(hours) > 5 else max(hours),
        "p95_days": statistics.quantiles(days, n=100)[94] if len(days) > 5 else max(days),
        "min_hours": min(hours),
        "max_hours": max(hours),
        "detailed": timing_data
    }


def categorize_prs_by_size(prs):
    """Categorize PRs by line change buckets."""
    buckets = {
        "0-50": [],
        "50-100": [],
        "100-1000": [],
        "1000-10000": [],
        "10000+": []
    }

    for pr in prs:
        additions = pr.get("additions", 0) or 0
        deletions = pr.get("deletions", 0) or 0
        total_lines = additions + deletions

        # Add total_lines to PR data for later use
        pr["total_lines"] = total_lines

        if total_lines <= 50:
            buckets["0-50"].append(pr)
        elif total_lines <= 100:
            buckets["50-100"].append(pr)
        elif total_lines <= 1000:
            buckets["100-1000"].append(pr)
        elif total_lines <= 10000:
            buckets["1000-10000"].append(pr)
        else:
            buckets["10000+"].append(pr)

    return buckets


def calculate_dora_metrics_by_size(prs, since_date):
    """Calculate DORA metrics split by PR size buckets (excluding change failure rate)."""
    buckets = categorize_prs_by_size(prs)
    results = {}

    for bucket_name, bucket_prs in buckets.items():
        if bucket_prs:
            # Calculate timing metrics only (no change failure rate per bucket)
            timing_metrics = calculate_pr_timing_metrics(bucket_prs)

            since_dt = datetime.fromisoformat(since_date.replace(" ", "T"))
            days_in_period = (datetime.now() - since_dt).days
            deployment_frequency = len(bucket_prs) / max(days_in_period, 1)

            results[bucket_name] = {
                "deployment_frequency": deployment_frequency,
                "deployment_frequency_per_day": deployment_frequency,
                "lead_time_hours": timing_metrics.get("median_hours", 0),
                "lead_time_days": timing_metrics.get("median_hours", 0) / 24,
                "pr_count": len(bucket_prs),
                "avg_lines": statistics.mean([pr.get("total_lines", 0) for pr in bucket_prs]) if bucket_prs else 0
            }
        else:
            results[bucket_name] = {
                "deployment_frequency": 0,
                "lead_time_hours": 0,
                "pr_count": 0,
                "avg_lines": 0
            }

    return results


def calculate_dora_metrics(prs, since_date):
    """Calculate DORA metrics from PR data."""
    if not prs:
        return {
            "deployment_frequency": 0,
            "lead_time_hours": 0,
            "mttr_hours": 0,
            "change_failure_rate": 0
        }

    # 1. Deployment Frequency - using merged PRs as deployment proxy
    try:
        since_dt = datetime.fromisoformat(since_date.replace(" ", "T"))
    except (ValueError, TypeError):
        print(f"Error: since_date '{since_date}' is not in a valid ISO format.", file=sys.stderr)
        return {
            "deployment_frequency": 0,
            "lead_time_hours": 0,
            "mttr_hours": 0,
            "change_failure_rate": 0
        }
    days_in_period = (datetime.now() - since_dt).days
    deployment_frequency = len(prs) / max(days_in_period, 1)

    # 2. Lead Time for Changes - PR creation to merge time
    timing_metrics = calculate_pr_timing_metrics(prs)
    lead_time_hours = timing_metrics.get("median_hours", 0)

    # 3. Change Failure Rate - approximate by looking at fix PRs following feature PRs
    # NOTE: This heuristic matches PRs with 'fix' in title - may include false positives
    # For more accuracy, consider GitHub labels (bug, fix, hotfix) if available
    fix_prs = [pr for pr in prs if "fix" in pr.get("title", "").lower()]
    feature_prs = [pr for pr in prs if any(word in pr.get("title", "").lower()
                                          for word in ["feat", "feature"]) or
                   pr.get("title", "").lower().startswith("add")]
    change_failure_rate = len(fix_prs) / max(len(feature_prs), 1) * 100

    # 4. MTTR - approximate by time between failure (fix PR creation) and resolution (fix PR merge)
    fix_timing = calculate_pr_timing_metrics(fix_prs)
    mttr_hours = fix_timing.get("median_hours", 0)

    return {
        "deployment_frequency": deployment_frequency,
        "deployment_frequency_per_day": deployment_frequency,
        "lead_time_hours": lead_time_hours,
        "lead_time_days": lead_time_hours / 24,
        "mttr_hours": mttr_hours,
        "mttr_days": mttr_hours / 24,
        "change_failure_rate": change_failure_rate,
        "total_prs": len(prs),
        "fix_prs": len(fix_prs),
        "feature_prs": len(feature_prs)
    }


def group_data_by_week(data_list, date_field, since_date):
    """Group data by week number and return weekly breakdowns."""
    since_dt = datetime.fromisoformat(since_date.replace(" ", "T"))
    weekly_data = defaultdict(list)

    for item in data_list:
        item_date = parse_github_datetime(item.get(date_field))
        if item_date and item_date >= since_dt:
            # Calculate week number from start date
            days_diff = (item_date - since_dt).days
            week_num = days_diff // 7 + 1
            weekly_data[week_num].append(item)

    return dict(weekly_data)


def calculate_weekly_metrics(prs, commits, since_date):
    """Calculate weekly DORA and PR metrics."""
    # Group data by weeks
    prs_by_week = group_data_by_week(prs, "mergedAt", since_date)
    commits_by_week = group_data_by_week(commits, "date", since_date) if commits else {}

    weekly_results = {}

    for week_num in range(1, max(list(prs_by_week.keys()) + [1]) + 1):
        week_prs = prs_by_week.get(week_num, [])
        week_commits = commits_by_week.get(week_num, [])

        if week_prs:
            # Calculate DORA metrics for this week
            timing = calculate_pr_timing_metrics(week_prs)

            # Calculate change failure rate for this week
            fix_prs = [pr for pr in week_prs if "fix" in pr.get("title", "").lower()]
            feature_prs = [pr for pr in week_prs if any(word in pr.get("title", "").lower()
                                                      for word in ["feat", "feature"]) or
                           pr.get("title", "").lower().startswith("add")]
            change_failure_rate = len(fix_prs) / max(len(feature_prs), 1) * 100 if feature_prs else 0

            weekly_results[week_num] = {
                "prs_count": len(week_prs),
                "commits_count": len(week_commits),
                "deployment_frequency": len(week_prs) / 7,  # per day
                "lead_time_hours": timing.get("median_hours", 0),
                "lead_time_days": timing.get("median_hours", 0) / 24,
                "avg_pr_size": statistics.mean([pr.get("total_lines", 0) for pr in week_prs]) if week_prs else 0,
                "change_failure_rate": change_failure_rate,
                "fix_prs": len(fix_prs),
                "feature_prs": len(feature_prs)
            }
        else:
            weekly_results[week_num] = {
                "prs_count": 0,
                "commits_count": len(week_commits),
                "deployment_frequency": 0,
                "lead_time_hours": 0,
                "lead_time_days": 0,
                "avg_pr_size": 0,
                "change_failure_rate": 0,
                "fix_prs": 0,
                "feature_prs": 0
            }

    return weekly_results


def analyze_weekly_trends(weekly_metrics):
    """Analyze trends in weekly metrics to show improvement/decline."""
    if len(weekly_metrics) < 2:
        return {"trend_analysis": "Insufficient data for trend analysis"}

    weeks = sorted(weekly_metrics.keys())
    trends = {}

    # Calculate trends for key metrics
    metrics_to_track = ["deployment_frequency", "lead_time_hours", "change_failure_rate", "avg_pr_size"]

    for metric in metrics_to_track:
        values = [weekly_metrics[week][metric] for week in weeks if weekly_metrics[week]["prs_count"] > 0]

        if len(values) >= 2:
            # Simple trend: compare first half vs second half
            mid_point = len(values) // 2
            first_half_avg = statistics.mean(values[:mid_point]) if values[:mid_point] else 0
            second_half_avg = statistics.mean(values[mid_point:]) if values[mid_point:] else 0

            if first_half_avg == 0:
                trend = "insufficient_data"
                change_pct = 0
            else:
                change_pct = ((second_half_avg - first_half_avg) / first_half_avg) * 100
                if change_pct > 5:
                    trend = "improving" if metric in ["deployment_frequency"] else "declining"
                elif change_pct < -5:
                    trend = "declining" if metric in ["deployment_frequency"] else "improving"
                else:
                    trend = "stable"

            trends[metric] = {
                "trend": trend,
                "change_percent": change_pct,
                "first_half_avg": first_half_avg,
                "second_half_avg": second_half_avg
            }

    return trends


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

    # PR Timing Analysis
    if prs["total"] > 0:
        timing = calculate_pr_timing_metrics(prs["prs"])
        print("## PR Timing Metrics (Open to Merge)")
        print(f"PRs with timing data: {timing['count']}")
        if timing['count'] > 0:
            print(f"Average time to merge: {timing['avg_hours']:.1f} hours ({timing['avg_days']:.1f} days)")
            print(f"Median time to merge: {timing['median_hours']:.1f} hours ({timing['median_days']:.1f} days)")
            print(f"95th percentile: {timing['p95_hours']:.1f} hours ({timing['p95_days']:.1f} days)")
            print(f"Fastest merge: {timing['min_hours']:.1f} hours")
            print(f"Slowest merge: {timing['max_hours']:.1f} hours ({timing['max_hours']/24:.1f} days)")
        print()

        # DORA Metrics
        dora = calculate_dora_metrics(prs["prs"], since_date)
        print("## DORA Metrics")
        print(f"Deployment Frequency: {dora['deployment_frequency_per_day']:.1f} deployments/day")
        print(f"Lead Time for Changes: {dora['lead_time_hours']:.1f} hours ({dora['lead_time_days']:.1f} days)")
        print(f"Mean Time to Recovery: {dora['mttr_hours']:.1f} hours ({dora['mttr_days']:.1f} days)")
        print(f"Change Failure Rate: {dora['change_failure_rate']:.1f}%")
        print(f"  (Based on {dora['fix_prs']} fix PRs vs {dora['feature_prs']} feature PRs)")
        print()

        # DORA Metrics by PR Size
        dora_by_size = calculate_dora_metrics_by_size(prs["prs"], since_date)
        print("## DORA Metrics by PR Size")
        for bucket, metrics in dora_by_size.items():
            print(f"\n### {bucket} lines ({metrics['pr_count']} PRs, avg: {metrics['avg_lines']:.0f} lines)")
            if metrics['pr_count'] > 0:
                print(f"  Deployment Frequency: {metrics['deployment_frequency_per_day']:.1f}/day")
                print(f"  Lead Time: {metrics['lead_time_hours']:.1f}h ({metrics['lead_time_days']:.1f}d)")
            else:
                print("  No PRs in this size bucket")
        print()

        # Weekly Metrics Analysis
        weekly_metrics = calculate_weekly_metrics(prs["prs"], commits.get("commits", []), since_date)
        if len(weekly_metrics) > 1:
            print("## Weekly Metrics Analysis")

            # Show weekly breakdown
            for week_num in sorted(weekly_metrics.keys()):
                week = weekly_metrics[week_num]
                print(f"\n### Week {week_num}")
                print(f"  PRs: {week['prs_count']}, Commits: {week['commits_count']}")
                if week['prs_count'] > 0:
                    print(f"  Deployment Frequency: {week['deployment_frequency']:.1f}/day")
                    print(f"  Lead Time: {week['lead_time_hours']:.1f}h")
                    print(f"  Avg PR Size: {week['avg_pr_size']:.0f} lines")
                    print(f"  Change Failure Rate: {week['change_failure_rate']:.1f}%")
                else:
                    print("  No PRs this week")

            # Show trends
            trends = analyze_weekly_trends(weekly_metrics)
            print("\n### Trend Analysis (First Half vs Second Half)")

            trend_labels = {
                "deployment_frequency": "Deployment Frequency",
                "lead_time_hours": "Lead Time",
                "change_failure_rate": "Change Failure Rate",
                "avg_pr_size": "Average PR Size"
            }

            for metric, trend_data in trends.items():
                if metric in trend_labels:
                    label = trend_labels[metric]
                    trend = trend_data["trend"]
                    change = trend_data["change_percent"]

                    trend_emoji = "📈" if trend == "improving" else "📉" if trend == "declining" else "➡️"
                    print(f"  {trend_emoji} {label}: {trend} ({change:+.1f}%)")

            print()
        else:
            print("## Weekly Metrics Analysis")
            print("Insufficient data for weekly analysis (need multiple weeks)")
            print()
    else:
        print("## PR Timing Metrics")
        print("No PR data available for timing analysis")
        print()
        print("## DORA Metrics")
        print("No PR data available for DORA metrics")
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
