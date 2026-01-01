#!/usr/bin/env python3
"""
WorldArchitect.AI Daily Campaign Activity Report

Generates a daily activity report showing:
- Last week stats (DAU, total users, top campaigns)
- Last 4 weeks stats (DAU, WAU, top campaigns)
- Top users by campaign entries

Usage:
    python scripts/daily_campaign_report.py
    python scripts/daily_campaign_report.py --no-daily  # Hide daily breakdown
    python scripts/daily_campaign_report.py --send-email  # Send via Gmail

Prerequisites:
    export WORLDAI_DEV_MODE=true
    export WORLDAI_GOOGLE_APPLICATION_CREDENTIALS=~/serviceAccountKey.json

Email Prerequisites (for --send-email):
    export EMAIL_USER=your-email@gmail.com
    export EMAIL_APP_PASSWORD=your-app-password  # Gmail App Password
"""

import argparse
import os
import smtplib
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Firebase credentials - use env var if set (CI), else local file
if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.expanduser('~/serviceAccountKey.json')
os.environ['WORLDAI_DEV_MODE'] = 'true'

from mvp_site.clock_skew_credentials import apply_clock_skew_patch
apply_clock_skew_patch()

import firebase_admin
from firebase_admin import auth, credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

# Known test user emails to exclude
TEST_USER_PATTERNS = [
    'jleechan@gmail.com',
    'jleechantest@gmail.com',
    'jleechan+*',
]


def init_firebase():
    """Initialize Firebase connection."""
    if not firebase_admin._apps:
        creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if creds_path and os.path.exists(creds_path):
            cred = credentials.Certificate(creds_path)
        else:
            cred = credentials.Certificate(os.path.expanduser('~/serviceAccountKey.json'))
        firebase_admin.initialize_app(cred)
    return firestore.client()


def is_test_user(email: str) -> bool:
    """Check if email belongs to a test user."""
    if not email:
        return True  # No email = anonymous = skip
    email_lower = email.lower()
    for pattern in TEST_USER_PATTERNS:
        if '*' in pattern:
            prefix = pattern.replace('*', '')
            if email_lower.startswith(prefix):
                return True
        elif email_lower == pattern.lower():
            return True
    return False


def get_date_key(dt: datetime) -> str:
    """Get YYYY-MM-DD date key."""
    return dt.strftime('%Y-%m-%d')


def get_week_key(dt: datetime) -> str:
    """Get ISO week key (YYYY-WNN)."""
    return f"{dt.isocalendar()[0]}-W{dt.isocalendar()[1]:02d}"


def calculate_percentile(values: list, percentile: float) -> float:
    """Calculate percentile of a list of values."""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = (percentile / 100) * (len(sorted_values) - 1)
    lower = int(index)
    upper = min(lower + 1, len(sorted_values) - 1)
    if lower == upper:
        return float(sorted_values[lower])
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * (index - lower)


def calculate_avg(values: list) -> float:
    """Calculate average of a list of values."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def query_campaign_activity():
    """Query all campaign activity from Firebase."""
    db = init_firebase()

    now = datetime.now(timezone.utc)
    one_week_ago = now - timedelta(days=7)
    four_weeks_ago = now - timedelta(days=28)

    print("📊 Querying Firebase for campaign activity...\n")

    # Collect all activity data
    user_campaigns = defaultdict(list)  # email -> list of campaign data
    all_activity = []  # list of {email, timestamp, entries}

    total_users = 0
    total_campaigns = 0

    # Iterate through Firebase Auth users (to get all users including those without user docs)
    print("  Scanning Firebase Auth users...")
    for user in auth.list_users().iterate_all():
        total_users += 1
        uid = user.uid
        email = user.email or ''

        # Skip test users
        if is_test_user(email):
            continue

        if total_users % 50 == 0:
            print(f"    Scanned {total_users} users...")

        # Query campaigns for this user
        campaigns_ref = db.collection('users').document(uid).collection('campaigns')
        try:
            # Only get campaigns played in last 4 weeks
            campaigns = campaigns_ref.where(
                filter=FieldFilter('last_played', '>=', four_weeks_ago)
            ).stream()

            for camp in campaigns:
                total_campaigns += 1
                data = camp.to_dict()

                # Count story entries
                entry_count = sum(1 for _ in camp.reference.collection('story').stream())

                last_played = data.get('last_played')
                if last_played:
                    # Convert to datetime if needed
                    if hasattr(last_played, 'timestamp'):
                        last_played = datetime.fromtimestamp(last_played.timestamp(), tz=timezone.utc)

                    campaign_data = {
                        'id': camp.id,
                        'title': data.get('title', 'Untitled'),
                        'entries': entry_count,
                        'last_played': last_played,
                        'email': email,
                    }

                    user_campaigns[email].append(campaign_data)
                    all_activity.append({
                        'email': email,
                        'timestamp': last_played,
                        'entries': entry_count,
                    })
        except Exception:
            pass  # Skip users with no campaigns

    print(f"  Scanned {total_users} users, {total_campaigns} campaigns\n")

    return user_campaigns, all_activity, now, one_week_ago, four_weeks_ago


def analyze_dau_wau(all_activity, one_week_ago, four_weeks_ago, now):
    """Analyze Daily and Weekly Active Users."""
    # Filter to last 4 weeks
    recent_activity = [a for a in all_activity if a['timestamp'] >= four_weeks_ago]
    last_week_activity = [a for a in all_activity if a['timestamp'] >= one_week_ago]

    # Group by day (4 weeks)
    daily_users = defaultdict(set)
    weekly_users = defaultdict(set)
    daily_users_week = defaultdict(set)

    for activity in recent_activity:
        date_key = get_date_key(activity['timestamp'])
        week_key = get_week_key(activity['timestamp'])
        daily_users[date_key].add(activity['email'])
        weekly_users[week_key].add(activity['email'])

    for activity in last_week_activity:
        date_key = get_date_key(activity['timestamp'])
        daily_users_week[date_key].add(activity['email'])

    # Calculate DAU values
    dau_values_4w = [len(users) for users in daily_users.values()]
    dau_values_1w = [len(users) for users in daily_users_week.values()]
    wau_values = [len(users) for users in weekly_users.values()]

    # Get daily/weekly breakdowns
    sorted_dates = sorted(daily_users.keys())[-28:]
    last_28_days = [{'date': d, 'users': len(daily_users[d])} for d in sorted_dates]

    sorted_dates_week = sorted(daily_users_week.keys())[-7:]
    last_7_days = [{'date': d, 'users': len(daily_users_week[d])} for d in sorted_dates_week]

    sorted_weeks = sorted(weekly_users.keys())[-4:]
    last_4_weeks = [{'week': w, 'users': len(weekly_users[w])} for w in sorted_weeks]

    return {
        'one_week': {
            'total_unique_users': len(set(a['email'] for a in last_week_activity)),
            'dau': {
                'avg': calculate_avg(dau_values_1w),
                'p50': calculate_percentile(dau_values_1w, 50),
                'p90': calculate_percentile(dau_values_1w, 90),
                'p99': calculate_percentile(dau_values_1w, 99),
                'daily': last_7_days,
            },
            'period_start': one_week_ago.strftime('%Y-%m-%d'),
            'period_end': now.strftime('%Y-%m-%d'),
        },
        'four_weeks': {
            'total_unique_users': len(set(a['email'] for a in recent_activity)),
            'dau': {
                'avg': calculate_avg(dau_values_4w),
                'p50': calculate_percentile(dau_values_4w, 50),
                'p90': calculate_percentile(dau_values_4w, 90),
                'p99': calculate_percentile(dau_values_4w, 99),
                'daily': last_28_days,
            },
            'wau': {
                'avg': calculate_avg(wau_values),
                'p50': calculate_percentile(wau_values, 50),
                'p90': calculate_percentile(wau_values, 90),
                'p99': calculate_percentile(wau_values, 99),
                'weekly': last_4_weeks,
            },
            'period_start': four_weeks_ago.strftime('%Y-%m-%d'),
            'period_end': now.strftime('%Y-%m-%d'),
        },
    }


def calculate_top_users(user_campaigns, cutoff_date):
    """Calculate top users by total campaign entries."""
    user_stats = []

    for email, campaigns in user_campaigns.items():
        # Filter campaigns by cutoff date
        period_campaigns = [c for c in campaigns if c['last_played'] >= cutoff_date]

        if period_campaigns:
            total_entries = sum(c['entries'] for c in period_campaigns)
            num_campaigns = len(period_campaigns)
            last_activity = max(c['last_played'] for c in period_campaigns)

            user_stats.append({
                'email': email,
                'total_entries': total_entries,
                'campaigns': num_campaigns,
                'last_activity': last_activity,
            })

    # Sort by total entries descending
    user_stats.sort(key=lambda x: x['total_entries'], reverse=True)
    return user_stats[:10]


def format_report(dau_wau_stats, top_users_week, top_users_4weeks, show_daily=True):
    """Format the report output."""
    lines = []

    # Header
    lines.append("WorldArchitect.AI Daily Campaign Activity Report")
    lines.append("=" * 50)
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")

    # Last Week Stats
    lines.append("━" * 50)
    lines.append("📅 LAST WEEK STATS")
    lines.append("━" * 50)
    week_stats = dau_wau_stats['one_week']
    lines.append(f"Total Unique Users: {week_stats['total_unique_users']}")
    lines.append("")
    lines.append("Daily Active Users (DAU):")
    lines.append(f"  Average: {week_stats['dau']['avg']:.2f} users/day")
    lines.append(f"  P50 (Median): {week_stats['dau']['p50']:.2f} users/day")
    lines.append(f"  P90: {week_stats['dau']['p90']:.2f} users/day")
    lines.append(f"  P99: {week_stats['dau']['p99']:.2f} users/day")
    lines.append("")

    # Top Users Last Week
    lines.append("👥 Top 10 Users (Last Week):")
    lines.append("-" * 100)
    for i, user in enumerate(top_users_week, 1):
        lines.append(f"  {i} {user['email']} ({user['total_entries']} entries, {user['campaigns']} campaigns)")
    lines.append("-" * 100)
    lines.append("")

    # Last 4 Weeks Stats
    lines.append("━" * 50)
    lines.append("📅 LAST 4 WEEKS STATS")
    lines.append("━" * 50)
    four_week_stats = dau_wau_stats['four_weeks']
    lines.append(f"Total Unique Users: {four_week_stats['total_unique_users']}")
    lines.append("")
    lines.append("Daily Active Users (DAU):")
    lines.append(f"  Average: {four_week_stats['dau']['avg']:.2f} users/day")
    lines.append(f"  P50 (Median): {four_week_stats['dau']['p50']:.2f} users/day")
    lines.append(f"  P90: {four_week_stats['dau']['p90']:.2f} users/day")
    lines.append(f"  P99: {four_week_stats['dau']['p99']:.2f} users/day")
    lines.append("")
    lines.append("Weekly Active Users (WAU):")
    lines.append(f"  Average: {four_week_stats['wau']['avg']:.2f} users/week")
    lines.append(f"  P50 (Median): {four_week_stats['wau']['p50']:.2f} users/week")
    lines.append(f"  P90: {four_week_stats['wau']['p90']:.2f} users/week")
    lines.append(f"  P99: {four_week_stats['wau']['p99']:.2f} users/week")
    lines.append("")

    # Top Users Last 4 Weeks
    lines.append("👥 Top 10 Users (Last 4 Weeks):")
    lines.append("-" * 100)
    for i, user in enumerate(top_users_4weeks, 1):
        lines.append(f"  {i} {user['email']} ({user['total_entries']} entries, {user['campaigns']} campaigns)")
    lines.append("-" * 100)

    # Daily breakdown if requested
    if show_daily and four_week_stats['dau']['daily']:
        lines.append("")
        lines.append("Daily breakdown (last 28 days):")
        for day in four_week_stats['dau']['daily']:
            bar = "█" * min(day['users'], 50)
            lines.append(f"  {day['date']}: {day['users']:3d} {bar}")

    return "\n".join(lines)


def send_email(report: str, dau_wau_stats: dict, to_email: str = None):
    """Send report via Gmail SMTP."""
    email_user = os.environ.get('EMAIL_USER')
    email_password = os.environ.get('EMAIL_APP_PASSWORD') or os.environ.get('EMAIL_PASS')

    if not email_user or not email_password:
        print("❌ Email credentials not set. Set EMAIL_USER and EMAIL_APP_PASSWORD environment variables.")
        print("   To create an App Password: https://myaccount.google.com/apppasswords")
        return False

    to_email = to_email or email_user

    # Extract stats for subject line
    dau_avg = dau_wau_stats['four_weeks']['dau']['avg']
    wau_avg = dau_wau_stats['four_weeks']['wau']['avg']

    # Create message
    msg = MIMEMultipart()
    msg['From'] = f"WorldArchitect Reports <{email_user}>"
    msg['To'] = to_email
    msg['Subject'] = f"📊 WorldArchitect.AI Daily Report - DAU: {dau_avg:.2f}, WAU: {wau_avg:.2f}"

    # Attach report as body
    msg.attach(MIMEText(report, 'plain'))

    try:
        print(f"📧 Sending email to {to_email}...")
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(email_user, email_password)
            server.send_message(msg)
        print(f"✅ Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Generate daily campaign activity report')
    parser.add_argument('--no-daily', action='store_true', help='Hide daily breakdown')
    parser.add_argument('--output', type=str, default=None, help='Output file path')
    parser.add_argument('--send-email', action='store_true', help='Send report via Gmail')
    parser.add_argument('--to', type=str, default=None, help='Email recipient (defaults to EMAIL_USER)')
    args = parser.parse_args()

    # Query data
    user_campaigns, all_activity, now, one_week_ago, four_weeks_ago = query_campaign_activity()

    # Analyze DAU/WAU
    dau_wau_stats = analyze_dau_wau(all_activity, one_week_ago, four_weeks_ago, now)

    # Calculate top users
    top_users_week = calculate_top_users(user_campaigns, one_week_ago)
    top_users_4weeks = calculate_top_users(user_campaigns, four_weeks_ago)

    # Format and print report
    report = format_report(dau_wau_stats, top_users_week, top_users_4weeks, show_daily=not args.no_daily)
    print(report)

    # Save to file
    output_path = args.output or os.path.expanduser(
        f"~/Downloads/campaign-activity-report-{now.strftime('%Y-%m-%d')}.txt"
    )
    with open(output_path, 'w') as f:
        f.write(report)
    print(f"\n✅ Report saved to: {output_path}")

    # Send email if requested
    if args.send_email:
        send_email(report, dau_wau_stats, args.to)


if __name__ == '__main__':
    main()
