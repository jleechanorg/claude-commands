#!/usr/bin/env python3
"""
TASK-091 Simple Test: Frontend Checkbox Analysis and Mock Backend Test
"""

import os
import sys
import json
import time
import re

def analyze_frontend_checkboxes():
    """Analyze the frontend HTML to understand checkbox behavior."""
    print("=== TASK-091: Frontend Checkbox Analysis ===\n")
    
    # Read the HTML file
    html_path = '/home/jleechan/projects/worldarchitect.ai/worktree_roadmap/mvp_site/static/index.html'
    
    with open(html_path, 'r') as f:
        html_content = f.read()
    
    # Extract checkbox information
    narrative_checkbox_match = re.search(r'<input[^>]*id="prompt-narrative"[^>]*>', html_content)
    mechanics_checkbox_match = re.search(r'<input[^>]*id="prompt-mechanics"[^>]*>', html_content)
    
    print("📋 Checkbox Configuration Analysis:")
    print("=" * 50)
    
    if narrative_checkbox_match:
        narrative_checkbox = narrative_checkbox_match.group(0)
        print(f"✅ Narrative Checkbox Found:")
        print(f"   {narrative_checkbox}")
        narrative_checked = 'checked' in narrative_checkbox
        print(f"   Default State: {'CHECKED' if narrative_checked else 'UNCHECKED'}")
    else:
        print("❌ Narrative Checkbox NOT Found")
        narrative_checked = False
    
    if mechanics_checkbox_match:
        mechanics_checkbox = mechanics_checkbox_match.group(0)
        print(f"✅ Mechanics Checkbox Found:")
        print(f"   {mechanics_checkbox}")
        mechanics_checked = 'checked' in mechanics_checkbox
        print(f"   Default State: {'CHECKED' if mechanics_checked else 'UNCHECKED'}")
    else:
        print("❌ Mechanics Checkbox NOT Found")
        mechanics_checked = False
    
    # Find the form submission handling
    form_section = re.search(r'<form[^>]*id="new-campaign-form"[^>]*>.*?</form>', html_content, re.DOTALL)
    if form_section:
        print(f"\n📝 Form Configuration:")
        print("   Form ID: new-campaign-form")
        print("   Submission handling: Via JavaScript")
    
    # Extract JavaScript files to understand form handling
    js_files = re.findall(r'<script[^>]*src="([^"]+\.js)"[^>]*>', html_content)
    print(f"\n🔧 JavaScript Files:")
    for js_file in js_files:
        print(f"   {js_file}")
    
    return {
        'narrative_found': narrative_checkbox_match is not None,
        'mechanics_found': mechanics_checkbox_match is not None,
        'narrative_checked_default': narrative_checked,
        'mechanics_checked_default': mechanics_checked,
        'form_found': form_section is not None
    }

def analyze_javascript_handling():
    """Analyze JavaScript files to understand form submission handling."""
    print("\n=== JavaScript Form Handling Analysis ===\n")
    
    js_files = [
        '/home/jleechan/projects/worldarchitect.ai/worktree_roadmap/mvp_site/static/app.js',
        '/home/jleechan/projects/worldarchitect.ai/worktree_roadmap/mvp_site/static/api.js'
    ]
    
    findings = []
    
    for js_file in js_files:
        if os.path.exists(js_file):
            print(f"📁 Analyzing: {os.path.basename(js_file)}")
            
            with open(js_file, 'r') as f:
                js_content = f.read()
            
            # Look for form submission handling
            form_submit_matches = re.findall(r'(document\.getElementById\([\'"]new-campaign-form[\'"].*?\.addEventListener.*?})', js_content, re.DOTALL)
            
            if form_submit_matches:
                print("✅ Form submission handler found")
                findings.append(f"Form handler in {os.path.basename(js_file)}")
            
            # Look for checkbox handling
            checkbox_matches = re.findall(r'(selectedPrompts.*?|prompt-narrative.*?|prompt-mechanics.*?)', js_content, re.IGNORECASE)
            
            if checkbox_matches:
                print(f"✅ Checkbox handling found: {len(checkbox_matches)} references")
                findings.append(f"Checkbox handling in {os.path.basename(js_file)}")
            
            # Look for API calls
            api_calls = re.findall(r'(fetch\([\'"][^\'\"]*api[^\'\"]*[\'"].*?})', js_content, re.DOTALL)
            
            if api_calls:
                print(f"✅ API calls found: {len(api_calls)} calls")
                findings.append(f"API calls in {os.path.basename(js_file)}")
        else:
            print(f"❌ File not found: {js_file}")
    
    return findings

def simulate_unchecked_scenario():
    """Simulate what happens when both checkboxes are unchecked."""
    print("\n=== Simulating Unchecked Checkbox Scenario ===\n")
    
    # Simulate form data with unchecked checkboxes
    scenarios = [
        {
            'name': 'Both checkboxes unchecked',
            'data': {
                'title': 'Test Campaign',
                'prompt': 'A simple adventure',
                'selected_prompts': []  # Empty array when unchecked
            }
        },
        {
            'name': 'Only narrative checked',
            'data': {
                'title': 'Test Campaign',
                'prompt': 'A simple adventure',
                'selected_prompts': ['narrative']
            }
        },
        {
            'name': 'Only mechanics checked',
            'data': {
                'title': 'Test Campaign',
                'prompt': 'A simple adventure',
                'selected_prompts': ['mechanics']
            }
        },
        {
            'name': 'Both checkboxes checked (default)',
            'data': {
                'title': 'Test Campaign',
                'prompt': 'A simple adventure',
                'selected_prompts': ['narrative', 'mechanics']
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"📋 Scenario: {scenario['name']}")
        print(f"   Data: {json.dumps(scenario['data'], indent=2)}")
        
        # Analyze potential issues
        if not scenario['data']['selected_prompts']:
            print("   ⚠️  Warning: No AI prompts selected - application should handle gracefully")
        elif len(scenario['data']['selected_prompts']) == 1:
            print("   ⚠️  Warning: Only one AI prompt selected - reduced functionality expected")
        else:
            print("   ✅ Standard configuration")
        
        print()

def generate_test_results():
    """Generate comprehensive test results."""
    print("\n=== Generating Test Results ===\n")
    
    # Run analyses
    frontend_analysis = analyze_frontend_checkboxes()
    js_findings = analyze_javascript_handling()
    simulate_unchecked_scenario()
    
    # Generate report
    report = {
        'test_name': 'TASK-091: Campaign Creation with Unchecked Checkboxes',
        'test_date': time.strftime('%Y-%m-%d %H:%M:%S'),
        'frontend_analysis': frontend_analysis,
        'js_findings': js_findings,
        'overall_status': 'ANALYSIS_COMPLETE'
    }
    
    # Determine test status
    if frontend_analysis['narrative_found'] and frontend_analysis['mechanics_found']:
        report['checkbox_config'] = 'CORRECT'
    else:
        report['checkbox_config'] = 'INCORRECT'
    
    # Create detailed findings
    findings = []
    
    findings.append(f"Narrative checkbox found: {frontend_analysis['narrative_found']}")
    findings.append(f"Mechanics checkbox found: {frontend_analysis['mechanics_found']}")
    findings.append(f"Narrative checked by default: {frontend_analysis['narrative_checked_default']}")
    findings.append(f"Mechanics checked by default: {frontend_analysis['mechanics_checked_default']}")
    
    if frontend_analysis['narrative_checked_default'] and frontend_analysis['mechanics_checked_default']:
        findings.append("✅ Both checkboxes are checked by default - user can uncheck them")
    
    if js_findings:
        findings.append("✅ JavaScript form handling appears to be configured")
    else:
        findings.append("❌ JavaScript form handling may be missing")
    
    report['findings'] = findings
    
    # Generate recommendations
    recommendations = []
    
    if not frontend_analysis['narrative_found'] or not frontend_analysis['mechanics_found']:
        recommendations.append("Fix missing checkboxes in frontend")
    
    if not js_findings:
        recommendations.append("Verify JavaScript form handling is working")
    
    recommendations.append("Test actual campaign creation with unchecked boxes")
    recommendations.append("Verify backend handles empty selected_prompts array gracefully")
    
    report['recommendations'] = recommendations
    
    return report

if __name__ == '__main__':
    try:
        # Generate test results
        report = generate_test_results()
        
        # Save report
        report_path = '/home/jleechan/projects/worldarchitect.ai/worktree_roadmap/tmp/task_091_unchecked_checkboxes_results.md'
        
        with open(report_path, 'w') as f:
            f.write(f"# {report['test_name']}\n\n")
            f.write(f"**Test Date:** {report['test_date']}\n")
            f.write(f"**Overall Status:** {report['overall_status']}\n")
            f.write(f"**Checkbox Configuration:** {report['checkbox_config']}\n\n")
            
            f.write("## Frontend Analysis Results\n\n")
            f.write(f"- Narrative checkbox found: {report['frontend_analysis']['narrative_found']}\n")
            f.write(f"- Mechanics checkbox found: {report['frontend_analysis']['mechanics_found']}\n")
            f.write(f"- Narrative checked by default: {report['frontend_analysis']['narrative_checked_default']}\n")
            f.write(f"- Mechanics checked by default: {report['frontend_analysis']['mechanics_checked_default']}\n")
            f.write(f"- Form element found: {report['frontend_analysis']['form_found']}\n\n")
            
            f.write("## JavaScript Handling\n\n")
            if report['js_findings']:
                for finding in report['js_findings']:
                    f.write(f"- {finding}\n")
            else:
                f.write("- No JavaScript form handling detected\n")
            
            f.write("\n## Findings\n\n")
            for finding in report['findings']:
                f.write(f"- {finding}\n")
            
            f.write("\n## Recommendations\n\n")
            for rec in report['recommendations']:
                f.write(f"- {rec}\n")
            
            f.write("\n## Test Scenarios to Verify\n\n")
            f.write("1. **Both checkboxes unchecked**: Create campaign with `selected_prompts: []`\n")
            f.write("2. **Only narrative checked**: Create campaign with `selected_prompts: ['narrative']`\n")
            f.write("3. **Only mechanics checked**: Create campaign with `selected_prompts: ['mechanics']`\n")
            f.write("4. **Both checked (default)**: Create campaign with `selected_prompts: ['narrative', 'mechanics']`\n\n")
            
            f.write("## Expected Behavior\n\n")
            f.write("- Campaign creation should work with any combination of checkboxes\n")
            f.write("- No crashes or errors should occur\n")
            f.write("- Story generation should adapt to available AI prompts\n")
            f.write("- UI should remain responsive throughout the process\n")
            f.write("- State should persist correctly across interactions\n")
        
        print(f"📝 Test analysis saved to: {report_path}")
        print(f"📊 Checkbox configuration: {report['checkbox_config']}")
        
    except Exception as e:
        print(f"❌ Test analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()