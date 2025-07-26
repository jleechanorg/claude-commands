#!/usr/bin/env python3
"""
Daily Memory Summary Automation
Reads all memories from Memory MCP and emails a summary to jleechan@gmail.com
"""

import json
import subprocess
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
import sys
from pathlib import Path

def get_memory_data():
    """Fetch all memories using Memory MCP via Claude"""
    # Use Claude in headless mode to get memory data
    cmd = [
        'claude', '-p',
        'Use Memory MCP to read the entire knowledge graph and output it as JSON. Use the mcp__memory-server__read_graph tool and output only the raw JSON result, no other text.',
        '--output-format', 'stream-json',
        '--verbose',
        '--dangerously-skip-permissions'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Extract JSON from output
        for line in result.stdout.split('\n'):
            if line.strip().startswith('{') and 'entities' in line:
                return json.loads(line)
    except Exception as e:
        print(f"Error fetching memory data: {e}")
        return None

def generate_summary(memory_data):
    """Generate a markdown summary of memories"""
    if not memory_data:
        return "No memory data available."

    entities = memory_data.get('entities', [])
    relations = memory_data.get('relations', [])

    summary_lines = [
        f"# Daily Memory Summary - {datetime.now().strftime('%Y-%m-%d')}",
        "",
        f"Total Entities: {len(entities)}",
        f"Total Relations: {len(relations)}",
        "",
        "## Key Learnings by Category",
        ""
    ]

    # Group entities by type
    by_type = {}
    for entity in entities:
        entity_type = entity.get('entityType', 'unknown')
        if entity_type not in by_type:
            by_type[entity_type] = []
        by_type[entity_type].append(entity)

    # Summarize each type
    for entity_type, items in sorted(by_type.items()):
        summary_lines.append(f"### {entity_type.replace('_', ' ').title()} ({len(items)})")
        summary_lines.append("")

        # Show most recent/important items
        for entity in items[:5]:  # Top 5 per category
            name = entity.get('name', 'Unnamed')
            observations = entity.get('observations', [])
            if observations:
                latest = observations[-1] if observations else "No observations"
                summary_lines.append(f"- **{name}**: {latest[:100]}...")

        if len(items) > 5:
            summary_lines.append(f"- ...and {len(items) - 5} more")
        summary_lines.append("")

    # Recent critical patterns
    summary_lines.extend([
        "## Recent Critical Patterns",
        ""
    ])

    critical_entities = [e for e in entities if any('🚨' in str(o) for o in e.get('observations', []))]
    for entity in critical_entities[:10]:
        name = entity.get('name', 'Unnamed')
        critical_obs = [o for o in entity.get('observations', []) if '🚨' in str(o)]
        if critical_obs:
            summary_lines.append(f"- **{name}**: {critical_obs[0][:150]}...")

    summary_lines.append("")

    return '\n'.join(summary_lines)

def save_summary(summary):
    """Save summary to file"""
    summary_path = Path('memory_summary.md')
    summary_path.write_text(summary)
    return summary_path

def send_email(summary, recipient='jleechan@gmail.com'):
    """Send email using local SMTP server"""
    msg = MIMEMultipart()
    msg['From'] = 'claude@localhost'
    msg['To'] = recipient
    msg['Subject'] = f"Daily Memory Summary - {datetime.now().strftime('%Y-%m-%d')}"

    # Attach summary
    msg.attach(MIMEText(summary, 'plain'))

    # Send via local SMTP
    try:
        # Try localhost first
        with smtplib.SMTP('localhost', 25) as server:
            server.send_message(msg)
            print(f"Email sent to {recipient}")
            return True
    except Exception as e:
        print(f"Failed to send via localhost:25 - {e}")

        # Try sendmail command as fallback
        try:
            sendmail_cmd = ['sendmail', recipient]
            sendmail_input = msg.as_string()
            subprocess.run(sendmail_cmd, input=sendmail_input, text=True, check=True)
            print(f"Email sent via sendmail to {recipient}")
            return True
        except Exception as e2:
            print(f"Failed to send via sendmail - {e2}")
            print("Consider setting up postfix or another local mail server")
            return False

def main():
    """Main execution"""
    print("Testing with local memory data...")

    # For testing, use local file directly
    if Path('memory.json').exists():
        with open('memory.json') as f:
            memory_data = json.load(f)
        print(f"Loaded local memory data: {len(memory_data.get('entities', []))} entities")
    else:
        print("Fetching memory data from MCP...")
        memory_data = get_memory_data()

        if not memory_data:
            print("No memory data available from any source")
            memory_data = {"entities": [], "relations": []}

    print("Generating summary...")
    summary = generate_summary(memory_data)

    print("Saving summary...")
    summary_path = save_summary(summary)
    print(f"Summary saved to {summary_path}")

    print("Sending email...")
    if send_email(summary):
        print("Daily memory summary complete!")
    else:
        print("Failed to send email, but summary was saved locally")

if __name__ == "__main__":
    main()
