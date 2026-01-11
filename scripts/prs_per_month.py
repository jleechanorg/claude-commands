#!/usr/bin/env python3
"""
Analyze PRs and contributions per month across jleechanorg repositories.
Shows monthly trends and contribution patterns.
"""

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta

def run_git_command(cmd):
    """Run a git/gh command and return output."""
    try:
        if isinstance(cmd, str):
            import shlex
            cmd = shlex.split(cmd)
        
        result = subprocess.run(
            cmd, check=False, shell=False, stdout=subprocess.PIPE, 
            text=True, stderr=subprocess.DEVNULL, timeout=60
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"Error running command: {e}", file=sys.stderr)
        return ""

def fetch_repo_prs(repo_full_name, since_date=None):
    """Fetch PRs for a repo."""
    cmd = f"gh pr list --repo {repo_full_name} --state merged --limit 1000 --json number,title,createdAt,mergedAt,additions,deletions,author"
    
    output = run_git_command(cmd)
    if not output:
        return []
    
    try:
        prs = json.loads(output)
    except json.JSONDecodeError:
        return []
    
    # Filter by date if provided
    if since_date:
        since_dt = datetime.fromisoformat(since_date.replace(" ", "T"))
        filtered_prs = []
        for pr in prs:
            if pr.get("createdAt"):
                created_str = pr["createdAt"].replace("Z", "").replace("T", " ").split(".")[0]
                try:
                    created = datetime.fromisoformat(created_str)
                    if created >= since_dt:
                        filtered_prs.append(pr)
                except (ValueError, AttributeError):
                    continue
        return filtered_prs
    
    return prs

def fetch_org_repos(org_name):
    """Fetch all repositories from a GitHub organization."""
    cmd = f"gh repo list {org_name} --limit 1000 --json name,nameWithOwner"
    output = run_git_command(cmd)
    
    if not output:
        return []
    
    try:
        repos = json.loads(output)
        return repos
    except json.JSONDecodeError:
        return []

def group_prs_by_month(prs):
    """Group PRs by month based on mergedAt date."""
    monthly_data = defaultdict(lambda: {
        "prs": [],
        "count": 0,
        "additions": 0,
        "deletions": 0,
        "repos": set(),
        "authors": set()
    })
    
    for pr in prs:
        merged_at = pr.get("mergedAt")
        if not merged_at:
            continue
        
        # Parse date and extract year-month
        try:
            date_str = merged_at.replace("Z", "").replace("T", " ").split(".")[0]
            dt = datetime.fromisoformat(date_str)
            month_key = dt.strftime("%Y-%m")
            month_label = dt.strftime("%B %Y")
        except (ValueError, AttributeError):
            continue
        
        monthly_data[month_key]["prs"].append(pr)
        monthly_data[month_key]["count"] += 1
        monthly_data[month_key]["additions"] += pr.get("additions", 0) or 0
        monthly_data[month_key]["deletions"] += pr.get("deletions", 0) or 0
        
        # Track authors
        author = pr.get("author", {})
        if author and author.get("login"):
            monthly_data[month_key]["authors"].add(author["login"])
    
    # Convert sets to counts
    for month_key in monthly_data:
        monthly_data[month_key]["unique_authors"] = len(monthly_data[month_key]["authors"])
        monthly_data[month_key]["unique_repos"] = len(monthly_data[month_key]["repos"])
        del monthly_data[month_key]["authors"]
        del monthly_data[month_key]["repos"]
    
    return monthly_data

def group_prs_by_week(prs):
    """Group PRs by week based on mergedAt date."""
    weekly_data = defaultdict(lambda: {
        "prs": [],
        "count": 0,
        "additions": 0,
        "deletions": 0,
        "repos": set(),
        "authors": set()
    })
    
    for pr in prs:
        merged_at = pr.get("mergedAt")
        if not merged_at:
            continue
        
        # Parse date and extract year-week
        try:
            date_str = merged_at.replace("Z", "").replace("T", " ").split(".")[0]
            dt = datetime.fromisoformat(date_str)
            # Get ISO week (year, week number)
            year, week_num, weekday = dt.isocalendar()
            week_key = f"{year}-W{week_num:02d}"
            # Week label: start date of week
            days_since_monday = dt.weekday()  # Monday is 0
            week_start = dt - timedelta(days=days_since_monday)
            week_label = week_start.strftime("%b %d, %Y")
        except (ValueError, AttributeError):
            continue
        
        weekly_data[week_key]["prs"].append(pr)
        weekly_data[week_key]["count"] += 1
        weekly_data[week_key]["additions"] += pr.get("additions", 0) or 0
        weekly_data[week_key]["deletions"] += pr.get("deletions", 0) or 0
        
        # Track authors
        author = pr.get("author", {})
        if author and author.get("login"):
            weekly_data[week_key]["authors"].add(author["login"])
        
        # Track repos
        if pr.get("repo"):
            weekly_data[week_key]["repos"].add(pr["repo"])
    
    # Convert sets to counts and add labels
    for week_key in weekly_data:
        data = weekly_data[week_key]
        # Get week start date for label
        year, week_num = map(int, week_key.split("-W"))
        # Find first PR in week to get date
        if data["prs"]:
            first_pr_date = data["prs"][0].get("mergedAt", "")
            if first_pr_date:
                try:
                    date_str = first_pr_date.replace("Z", "").replace("T", " ").split(".")[0]
                    dt = datetime.fromisoformat(date_str)
                    days_since_monday = dt.weekday()
                    week_start = dt - timedelta(days=days_since_monday)
                    data["week_label"] = week_start.strftime("%b %d, %Y")
                except:
                    data["week_label"] = week_key
        else:
            data["week_label"] = week_key
        
        data["unique_authors"] = len(data["authors"])
        data["unique_repos"] = len(data["repos"])
        del data["authors"]
        del data["repos"]
    
    return weekly_data

def analyze_monthly_contributions(org_name, since_date=None, weekly=False):
    """Analyze monthly or weekly PR contributions across an organization."""
    period_type = "weekly" if weekly else "monthly"
    print(f"📊 Analyzing {period_type} PR contributions for {org_name}")
    print("=" * 80)
    
    repos = fetch_org_repos(org_name)
    if not repos:
        print(f"No repositories found for {org_name}")
        return {}
    
    print(f"Found {len(repos)} repositories")
    print("Fetching PRs...")
    
    all_prs = []
    repo_count = 0
    
    for repo in repos:
        repo_full_name = repo["nameWithOwner"]
        repo_count += 1
        if repo_count % 10 == 0:
            print(f"  Processed {repo_count}/{len(repos)} repos...")
        
        prs = fetch_repo_prs(repo_full_name, since_date)
        if prs:
            # Add repo info to each PR
            for pr in prs:
                pr["repo"] = repo["name"]
                pr["repo_full"] = repo_full_name
            all_prs.extend(prs)
    
    print(f"\nTotal PRs found: {len(all_prs)}")
    
    # Group by period
    if weekly:
        period_data = group_prs_by_week(all_prs)
        sorted_periods = sorted(period_data.keys(), key=lambda x: (int(x.split("-W")[0]), int(x.split("-W")[1])))
    else:
        period_data = group_prs_by_month(all_prs)
        sorted_periods = sorted(period_data.keys())
    
    return {
        "period_data": {period: period_data[period] for period in sorted_periods},
        "total_prs": len(all_prs),
        "total_repos": len(repos),
        "period_type": period_type
    }

def print_monthly_report(stats, org_name):
    """Print formatted monthly or weekly report."""
    period_data = stats["period_data"]
    period_type = stats.get("period_type", "monthly")
    is_weekly = period_type == "weekly"
    
    period_label = "WEEKLY" if is_weekly else "MONTHLY"
    print(f"\n{'='*80}")
    print(f"{period_label} PR CONTRIBUTION REPORT - {org_name}")
    print(f"{'='*80}\n")
    
    print(f"Total PRs: {stats['total_prs']:,}")
    print(f"Total Repositories: {stats['total_repos']}")
    periods_label = "Weeks" if is_weekly else "Months"
    print(f"{periods_label} Analyzed: {len(period_data)}\n")
    
    # Table header
    period_col = "Week Starting" if is_weekly else "Month"
    if is_weekly:
        print(f"{period_col:<20} {'PRs':<8} {'Hours':<10} {'PRs/Hr':<10} {'Lines/Hr':<12} {'Net/Hr':<12} {'Repos':<8}")
        print("-" * 100)
    else:
        print(f"{period_col:<20} {'PRs':<8} {'Additions':<12} {'Deletions':<12} {'Net Change':<12} {'Authors':<10} {'Repos':<8}")
        print("-" * 90)
    
    sorted_periods = sorted(period_data.keys())
    if is_weekly:
        sorted_periods = sorted(period_data.keys(), key=lambda x: (int(x.split("-W")[0]), int(x.split("-W")[1])))
    
    # Calculate hours (20-30 range, use 25 as average)
    hours_per_week = 25  # Average of 20-30
    
    for period_key in sorted_periods:
        data = period_data[period_key]
        
        if is_weekly:
            period_label = data.get("week_label", period_key)
        else:
            dt = datetime.strptime(period_key, "%Y-%m")
            period_label = dt.strftime("%B %Y")
        
        net_change = data["additions"] - data["deletions"]
        net_change_str = f"+{net_change:,}" if net_change >= 0 else f"{net_change:,}"
        
        if is_weekly:
            # Calculate hourly metrics
            prs_per_hour = data['count'] / hours_per_week if hours_per_week > 0 else 0
            total_lines = data['additions'] + data['deletions']
            lines_per_hour = total_lines / hours_per_week if hours_per_week > 0 else 0
            net_per_hour = net_change / hours_per_week if hours_per_week > 0 else 0
            net_per_hour_str = f"+{net_per_hour:,.0f}" if net_per_hour >= 0 else f"{net_per_hour:,.0f}"
            
            print(f"{period_label:<20} {data['count']:<8} {hours_per_week:<10} {prs_per_hour:>9.1f} "
                  f"{lines_per_hour:>11,.0f} {net_per_hour_str:>11} {data.get('unique_repos', 0):<8}")
        else:
            print(f"{period_label:<20} {data['count']:<8} {data['additions']:>11,} {data['deletions']:>11,} "
                  f"{net_change_str:>11} {data.get('unique_authors', 0):<10} {data.get('unique_repos', 0):<8}")
    
    # Summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    
    if period_data:
        pr_counts = [data["count"] for data in period_data.values()]
        additions = [data["additions"] for data in period_data.values()]
        deletions = [data["deletions"] for data in period_data.values()]
        
        sorted_period_keys = sorted(period_data.keys())
        if is_weekly:
            sorted_period_keys = sorted(period_data.keys(), key=lambda x: (int(x.split("-W")[0]), int(x.split("-W")[1])))
        
        period_label = "week" if is_weekly else "month"
        print(f"\nAverage PRs per {period_label}: {sum(pr_counts) / len(pr_counts):.1f}")
        max_idx = pr_counts.index(max(pr_counts))
        min_idx = pr_counts.index(min(pr_counts))
        max_period = period_data[sorted_period_keys[max_idx]].get("week_label", sorted_period_keys[max_idx]) if is_weekly else sorted_period_keys[max_idx]
        min_period = period_data[sorted_period_keys[min_idx]].get("week_label", sorted_period_keys[min_idx]) if is_weekly else sorted_period_keys[min_idx]
        print(f"Max PRs in a {period_label}: {max(pr_counts)} ({max_period})")
        print(f"Min PRs in a {period_label}: {min(pr_counts)} ({min_period})")
        print(f"\nAverage additions per {period_label}: {sum(additions) / len(additions):,.0f}")
        print(f"Average deletions per {period_label}: {sum(deletions) / len(deletions):,.0f}")
        
        # Hourly productivity stats for weekly reports
        if is_weekly:
            hours_per_week = 25  # Average of 20-30
            total_prs = sum(pr_counts)
            total_additions = sum(additions)
            total_deletions = sum(deletions)
            total_weeks = len(pr_counts)
            total_hours = hours_per_week * total_weeks
            
            avg_prs_per_hour = total_prs / total_hours if total_hours > 0 else 0
            avg_lines_per_hour = (total_additions + total_deletions) / total_hours if total_hours > 0 else 0
            avg_net_per_hour = (total_additions - total_deletions) / total_hours if total_hours > 0 else 0
            
            print(f"\n{'='*80}")
            print("HOURLY PRODUCTIVITY STATS (assuming 25 hours/week)")
            print(f"{'='*80}")
            print(f"Total hours worked: {total_hours:.0f} hours ({total_weeks} weeks × {hours_per_week} hrs/week)")
            print(f"Average PRs per hour: {avg_prs_per_hour:.2f}")
            print(f"Average lines per hour: {avg_lines_per_hour:,.0f}")
            print(f"Average net lines per hour: {avg_net_per_hour:+,.0f}")
            
            # Show range for 20-30 hours
            print(f"\nProductivity range (20-30 hrs/week):")
            for hrs in [20, 25, 30]:
                prs_per_hr = total_prs / (hrs * total_weeks) if hrs * total_weeks > 0 else 0
                lines_per_hr = (total_additions + total_deletions) / (hrs * total_weeks) if hrs * total_weeks > 0 else 0
                print(f"  {hrs} hrs/week: {prs_per_hr:.2f} PRs/hr, {lines_per_hr:,.0f} lines/hr")
        
        # Recent trend (last 4 periods vs previous 4 periods)
        if len(sorted_period_keys) >= 8:
            recent_periods = sorted_period_keys[-4:]
            previous_periods = sorted_period_keys[-8:-4]
            
            recent_prs = sum(period_data[p]["count"] for p in recent_periods)
            previous_prs = sum(period_data[p]["count"] for p in previous_periods)
            
            if previous_prs > 0:
                trend_pct = ((recent_prs - previous_prs) / previous_prs) * 100
                trend_emoji = "📈" if trend_pct > 0 else "📉" if trend_pct < 0 else "➡️"
                period_label_plural = "weeks" if is_weekly else "months"
                print(f"\n{trend_emoji} Trend (last 4 {period_label_plural} vs previous 4): {trend_pct:+.1f}%")
                print(f"   Last 4 {period_label_plural}: {recent_prs} PRs")
                print(f"   Previous 4 {period_label_plural}: {previous_prs} PRs")

def main():
    parser = argparse.ArgumentParser(
        description="Analyze PRs and contributions per month for GitHub organization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s jleechanorg                    # Analyze all PRs (monthly)
  %(prog)s jleechanorg --since 2025-01-01  # Analyze PRs since date
  %(prog)s jleechanorg --weekly --since 2025-10-01  # Weekly breakdown since Oct
  %(prog)s jleechanorg --json             # Output as JSON
        """
    )
    
    parser.add_argument("org", help="GitHub organization name")
    parser.add_argument("--since", help="Start date for analysis (YYYY-MM-DD)")
    parser.add_argument("--weekly", action="store_true", help="Group by week instead of month")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    
    args = parser.parse_args()
    
    # Analyze
    stats = analyze_monthly_contributions(args.org, args.since, weekly=args.weekly)
    
    if not stats:
        sys.exit(1)
    
    # Output
    if args.json:
        output = json.dumps(stats, indent=2, default=str)
    else:
        # Convert to printable format
        output_lines = []
        print_monthly_report(stats, args.org)
        sys.exit(0)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"✅ Report written to {args.output}")
    else:
        print(output)

if __name__ == "__main__":
    main()
