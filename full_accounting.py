#!/usr/bin/env python3
import subprocess
import re

def parse_line_data():
    """Parse the simple_loc.sh output to extract production code counts"""

    # Run simple_loc.sh and capture output
    result = subprocess.run(['./simple_loc.sh'], capture_output=True, text=True)
    lines = result.stdout.split('\n')

    # Find directory breakdown section
    in_breakdown = False
    directories = []

    for line in lines:
        if "Directory Breakdown:" in line:
            in_breakdown = True
            continue

        if in_breakdown and line.strip() and line.startswith('./'):
            directories.append(line.strip())

    # Parse each directory line
    parsed_dirs = []
    total_py = total_js = total_html = 0

    for line in directories:
        # Format: ./dir : XXXX lines (py:XX/XX js:XX/XX html:XX/XX)
        if ':' not in line:
            continue

        dir_name = line.split(':')[0].strip()

        # Extract production counts (first number in py:X/Y format)
        py_match = re.search(r'py:(\d+)/\d+', line)
        js_match = re.search(r'js:(\d+)/\d+', line)
        html_match = re.search(r'html:(\d+)/\d+', line)

        py_prod = int(py_match.group(1)) if py_match else 0
        js_prod = int(js_match.group(1)) if js_match else 0
        html_prod = int(html_match.group(1)) if html_match else 0

        dir_total = py_prod + js_prod + html_prod

        if dir_total > 0:
            parsed_dirs.append({
                'dir': dir_name,
                'py': py_prod,
                'js': js_prod,
                'html': html_prod,
                'total': dir_total
            })

            total_py += py_prod
            total_js += js_prod
            total_html += html_prod

    return parsed_dirs, total_py, total_js, total_html

def categorize_directory(dir_name):
    """Categorize directories by functionality"""

    if 'mvp_site' in dir_name and 'test' not in dir_name:
        return 'Core Application'
    elif dir_name.startswith('./scripts'):
        return 'Automation Scripts'
    elif '.claude' in dir_name:
        return 'AI Assistant'
    elif 'orchestration' in dir_name and 'test' not in dir_name:
        return 'Task Management'
    elif 'prototype' in dir_name:
        return 'Prototypes'
    elif 'roadmap' in dir_name:
        return 'Planning'
    elif any(x in dir_name for x in ['testing_', 'tests']):
        return 'Testing Infrastructure'
    elif any(x in dir_name for x in ['ajax-chat', 'gemini-demo']):
        return 'Demos'
    elif any(x in dir_name for x in ['claude-bot', 'mcp_servers']):
        return 'AI Assistant'
    elif 'venv' in dir_name:
        return 'Environment'
    else:
        return 'Other'

def main():
    directories, total_py, total_js, total_html = parse_line_data()
    total_all = total_py + total_js + total_html

    print("🔍 COMPLETE PRODUCTION CODE ACCOUNTING")
    print("=" * 45)
    print()

    # Sort by total lines descending
    directories.sort(key=lambda x: x['total'], reverse=True)

    print("📋 ALL DIRECTORIES WITH PRODUCTION CODE:")
    print("-" * 45)

    running_total = 0
    for d in directories:
        print(f"{d['dir']:<40}: {d['total']:>6} (py:{d['py']:>5} js:{d['js']:>4} html:{d['html']:>4})")
        running_total += d['total']

    print()
    print("📊 VERIFICATION:")
    print(f"Directory sum: {running_total:>6} lines")
    print(f"Python total:  {total_py:>6} lines ({total_py/total_all*100:.1f}%)")
    print(f"JS total:      {total_js:>6} lines ({total_js/total_all*100:.1f}%)")
    print(f"HTML total:    {total_html:>6} lines ({total_html/total_all*100:.1f}%)")
    print(f"GRAND TOTAL:   {total_all:>6} lines")

    print()
    print("🎯 BY FUNCTIONALITY:")
    print("-" * 25)

    # Group by category
    categories = {}
    for d in directories:
        cat = categorize_directory(d['dir'])
        if cat not in categories:
            categories[cat] = {'py': 0, 'js': 0, 'html': 0, 'total': 0}

        categories[cat]['py'] += d['py']
        categories[cat]['js'] += d['js']
        categories[cat]['html'] += d['html']
        categories[cat]['total'] += d['total']

    # Sort categories by total
    for cat, data in sorted(categories.items(), key=lambda x: x[1]['total'], reverse=True):
        print(f"{cat:<25}: {data['total']:>6} (py:{data['py']:>5} js:{data['js']:>4} html:{data['html']:>4})")

if __name__ == "__main__":
    main()
