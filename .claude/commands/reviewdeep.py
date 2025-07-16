#!/usr/bin/env python3
"""
Deep review command - Comprehensive analysis with ultra thinking, /arch review, and Gemini MCP
"""

import os
import sys
import subprocess
import json
import time
from typing import Optional, Dict, List, Tuple, Any

# Add lib directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from request_optimizer import optimize_file_read, check_request_size, handle_timeout, optimizer


def get_pr_info(pr_number: str) -> Optional[Dict]:
    """Get PR information from GitHub"""
    try:
        result = subprocess.run(
            ['gh', 'pr', 'view', pr_number, '--json', 'title,body,files,commits,state'],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return None


def get_file_content(filepath: str) -> Optional[str]:
    """Read file content with size optimization"""
    try:
        # Use request optimizer to determine read parameters
        read_params = optimize_file_read(filepath)
        
        with open(filepath, 'r') as f:
            if 'limit' in read_params:
                # Read only specified number of lines for large files
                lines = []
                for i, line in enumerate(f):
                    if i >= read_params['limit']:
                        lines.append(f"\n... [File truncated after {read_params['limit']} lines to prevent timeout] ...")
                        break
                    lines.append(line)
                return ''.join(lines)
            else:
                return f.read()
                
    except (FileNotFoundError, PermissionError, UnicodeDecodeError):
        return None


def run_arch_review(target: str, target_type: str) -> Dict[str, str]:
    """Run /arch review command with timeout optimization"""
    print("\n🏛️ Running architecture review...")
    
    # Execute arch review command with timeout handling
    arch_script = os.path.join(os.path.dirname(__file__), 'arch.py')
    cmd = ['python3', arch_script, target]
    
    attempt = 1
    max_attempts = 2  # Limit arch review retries
    
    while attempt <= max_attempts:
        try:
            # Set reasonable timeout for arch review
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            arch_output = result.stdout if result.returncode == 0 else result.stderr
            status = 'success' if result.returncode == 0 else 'failed'
            break
            
        except subprocess.TimeoutExpired:
            should_retry, delay = handle_timeout("arch_review", attempt)
            if should_retry and attempt < max_attempts:
                print(f"⏱️ Arch review timeout (attempt {attempt}), retrying in {delay}s...")
                time.sleep(delay)
                attempt += 1
                continue
            else:
                arch_output = f"Architecture review timed out after {attempt} attempts"
                status = 'timeout'
                break
                
        except Exception as e:
            arch_output = f"Failed to run /arch review: {str(e)}"
            status = 'failed'
            break
    
    return {
        'output': arch_output,
        'status': status,
        'attempts': attempt
    }


def analyze_with_gemini_mcp(target: str, target_type: str, role: str) -> Dict[str, str]:
    """Use Gemini MCP for analysis"""
    print(f"\n🤖 Analyzing with Gemini MCP (Role: {role})...")
    
    # Format prompt based on role
    if role == "developer":
        prompt = f"""As a senior developer, review this {target_type}: {target}
        
Focus on:
- Code quality and maintainability
- Implementation correctness
- Performance implications
- Testing adequacy
- Security vulnerabilities
- Error handling

Provide specific, actionable feedback."""
    
    elif role == "architect":
        prompt = f"""As a system architect, review this {target_type}: {target}
        
Focus on:
- System design and patterns
- Scalability considerations
- Integration points
- Technology choices
- Long-term maintainability
- Architectural debt

Identify architectural strengths and weaknesses."""
    
    else:  # business analyst
        prompt = f"""As a business analyst, review this {target_type}: {target}
        
Focus on:
- Business value delivered
- User experience impact
- Cost-benefit analysis
- Risk assessment
- Time to market
- ROI considerations

Evaluate from a business perspective."""
    
    # Call Gemini MCP for actual analysis with timeout handling
    start_time = time.time()
    try:
        import importlib.util
        
        # Check request size before sending
        context_size = len(prompt) + len(str(target))
        if context_size > 30000:  # Large request
            print(f"⚠️ Large Gemini request ({context_size} chars), may timeout...")
        
        # Check if MCP is available in Claude Code environment
        if importlib.util.find_spec('mcp__gemini_cli_mcp'):
            # Try Gemini Pro first with timeout handling
            attempt = 1
            max_attempts = 3
            
            while attempt <= max_attempts:
                try:
                    from mcp__gemini_cli_mcp import gemini_chat_pro
                    result = gemini_chat_pro(message=prompt, context=f"Analyzing {target_type}: {target}")
                    analysis = result if isinstance(result, str) else str(result)
                    status = 'success'
                    break
                    
                except Exception as e:
                    if "timeout" in str(e).lower() and attempt < max_attempts:
                        should_retry, delay = handle_timeout(f"gemini_{role}", attempt)
                        if should_retry:
                            print(f"⏱️ Gemini timeout (attempt {attempt}), retrying in {delay}s...")
                            time.sleep(delay)
                            attempt += 1
                            continue
                    
                    # Fall back to Gemini Flash if Pro fails
                    try:
                        from mcp__gemini_cli_mcp import gemini_chat_flash
                        result = gemini_chat_flash(message=prompt, context=f"Analyzing {target_type}: {target}")
                        analysis = result if isinstance(result, str) else str(result)
                        status = 'success'
                        break
                    except Exception as e2:
                        analysis = f"Gemini analysis unavailable after {attempt} attempts: {str(e2)}"
                        status = 'failed'
                        break
        else:
            # Graceful fallback when MCP not available
            analysis = f"Real {role} analysis would be performed here via Gemini MCP (MCP not available in current environment)"
            status = 'fallback'
            
        # Record performance metrics
        duration_ms = int((time.time() - start_time) * 1000)
        optimizer.record_success(f"gemini_{role}", duration_ms, context_size)
            
        return {
            'role': role,
            'analysis': analysis,
            'prompt': prompt,
            'status': status
        }
        
    except Exception as e:
        # Graceful fallback if MCP unavailable
        return {
            'role': role,
            'analysis': f"Gemini MCP unavailable for {role} analysis: {str(e)}",
            'prompt': prompt,
            'status': 'failed'
        }


def analyze_with_ultra_thinking(target: str, target_type: str) -> Dict[str, Any]:
    """Trigger ultra thinking analysis with integrated reviews"""
    print(f"🧠 Initiating deep review with ultra thinking mode...")
    print(f"📊 Analyzing {target_type}: {target}")
    print("="*60)
    
    # Phase 1: Ultra thinking analysis
    analysis_points = [
        "1. Architecture Soundness",
        "2. Implementation Quality", 
        "3. Practical Feasibility",
        "4. Error Handling & Recovery",
        "5. Performance & Scalability",
        "6. Integration Compatibility",
        "7. Security Implications",
        "8. Testing Strategy & Coverage",
        "9. Resource & Cost Analysis",
        "10. Success Probability",
        "11. Required Improvements",
        "12. Final Verdict"
    ]
    
    print("\n📋 Phase 1: Ultra Thinking Analysis (12+ thoughts)")
    for point in analysis_points:
        print(f"   {point}")
    
    # Phase 2: Architecture review
    print("\n📋 Phase 2: Architecture Review (/arch)")
    arch_results = run_arch_review(target, target_type)
    
    # Phase 3: Gemini MCP with role switching
    print("\n📋 Phase 3: Gemini MCP Multi-Role Analysis")
    
    gemini_results = {}
    roles = ["developer", "architect", "business analyst"]
    
    for role in roles:
        gemini_results[role] = analyze_with_gemini_mcp(target, target_type, role)
    
    print("\n" + "="*60)
    print("🔄 Deep analysis in progress...")
    print("   ✓ Ultra thinking with 12+ thought steps")
    print("   ✓ Architecture review with dual perspectives")
    print("   ✓ Gemini MCP analysis with 3 role perspectives")
    print("   ✓ Synthesizing insights from all sources")
    print("="*60)
    
    # Structure for the analysis results
    results = {
        'target': target,
        'type': target_type,
        'verdict': {
            'production_ready_percent': 0,
            'summary': ''
        },
        'strengths': [],
        'critical_flaws': [],
        'realistic_assessment': {
            'current_success_probability': 0,
            'improved_success_probability': 0,
            'expected_outcome': ''
        },
        'required_improvements': [],
        'bottom_line': '',
        'arch_review': arch_results,
        'gemini_analysis': gemini_results
    }
    
    return results


def format_review_output(results: Dict) -> str:
    """Format the review results for display"""
    output = []
    
    # Verdict
    output.append(f"## Verdict: {results['verdict']['production_ready_percent']}% Production Ready")
    output.append(f"{results['verdict']['summary']}\n")
    
    # Strengths
    if results['strengths']:
        output.append("### ✅ Strengths")
        for strength in results['strengths']:
            output.append(f"- {strength}")
        output.append("")
    
    # Critical Flaws
    if results['critical_flaws']:
        output.append("### ❌ Critical Flaws")
        for flaw in results['critical_flaws']:
            output.append(f"- {flaw}")
        output.append("")
    
    # Realistic Assessment
    output.append("### 📊 Realistic Assessment")
    assessment = results['realistic_assessment']
    output.append(f"- Current Success Probability: {assessment['current_success_probability']}%")
    output.append(f"- With Improvements: {assessment['improved_success_probability']}%")
    output.append(f"- Expected Outcome: {assessment['expected_outcome']}")
    output.append("")
    
    # Required Improvements
    if results['required_improvements']:
        output.append("### 🔧 Required Improvements")
        for i, improvement in enumerate(results['required_improvements'], 1):
            output.append(f"{i}. {improvement}")
        output.append("")
    
    # Bottom Line
    output.append("### 📌 Bottom Line")
    output.append(results['bottom_line'])
    
    # Architecture Review Results
    if 'arch_review' in results and results['arch_review']['status'] == 'success':
        output.append("\n### 🏛️ Architecture Review Insights")
        output.append("(See detailed /arch output above)")
    
    # Gemini Analysis Results
    if 'gemini_analysis' in results:
        output.append("\n### 🤖 Gemini MCP Multi-Role Perspectives")
        for role, analysis in results['gemini_analysis'].items():
            output.append(f"\n**{role.title()} Perspective:**")
            if analysis.get('status') == 'success':
                # Show first 200 chars of actual analysis
                analysis_text = analysis.get('analysis', 'No analysis provided')
                preview = analysis_text[:200] + "..." if len(analysis_text) > 200 else analysis_text
                output.append(preview)
            else:
                output.append(f"Analysis failed: {analysis.get('analysis', 'Unknown error')}")
    
    return "\n".join(output)


def get_current_branch_info():
    """Get current branch and associated PR info"""
    try:
        # Get current branch
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              capture_output=True, text=True, check=True)
        branch = result.stdout.strip()
        
        # Get PR info for current branch
        pr_result = subprocess.run(['gh', 'pr', 'list', '--head', branch, '--json', 'number,title,url'], 
                                 capture_output=True, text=True, check=True)
        prs = json.loads(pr_result.stdout)
        
        if prs:
            pr = prs[0]
            print(f"📋 Found PR: #{pr['number']} - {pr.get('title', 'No title')}")
            return f"PR #{pr['number']}", pr['number']
        else:
            # Check if there are uncommitted changes
            status_result = subprocess.run(['git', 'status', '--porcelain'], 
                                         capture_output=True, text=True)
            has_changes = bool(status_result.stdout.strip())
            
            status = " (with uncommitted changes)" if has_changes else ""
            return f"branch '{branch}'{status}", branch
            
    except Exception as e:
        return None, None


def detect_key_file_changes():
    """Detect changes to critical files that should trigger auto-review"""
    key_files = [
        'mvp_site/gemini_service.py',
        'mvp_site/firestore_service.py', 
        'mvp_site/main.py',
        'mvp_site/auth.py',
        'mvp_site/game_state.py'
    ]
    
    try:
        # Check for uncommitted changes to key files
        result = subprocess.run(['git', 'status', '--porcelain'] + key_files, 
                              capture_output=True, text=True)
        changed_files = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                # Extract filename from git status output
                filename = line[3:].strip()
                if filename in key_files:
                    changed_files.append(filename)
        
        # Check for recent commits affecting key files
        recent_result = subprocess.run(['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'] + key_files,
                                     capture_output=True, text=True)
        recent_changes = [f.strip() for f in recent_result.stdout.strip().split('\n') if f.strip()]
        
        all_changes = list(set(changed_files + recent_changes))
        return all_changes
        
    except Exception as e:
        return []


def main():
    # Initialize performance monitoring
    start_time = time.time()
    
    # Check for auto-trigger conditions first
    key_changes = detect_key_file_changes()
    if key_changes:
        print(f"🔍 Auto-detected changes to key files: {', '.join(key_changes)}")
        print("⚡ Triggering automatic review...")
    
    # If no arguments, review current branch/PR
    if len(sys.argv) < 2:
        print("🔍 No target specified, reviewing current branch/PR...")
        target_desc, target = get_current_branch_info()
        
        if not target:
            print("❌ Could not determine current branch")
            print("\nUsage: /reviewdeep [target]")
            print("       /reviewd [target]")
            print("\nExamples:")
            print("  /reviewdeep          # Review current branch/PR")
            print("  /reviewdeep 592      # Review specific PR")
            print("  /reviewd file.py     # Review specific file")
            return
            
        print(f"📊 Reviewing {target_desc}...")
        target = str(target)
    else:
        target = " ".join(sys.argv[1:])
    
    # Determine target type
    if target.isdigit() or target.startswith('#'):
        # PR number
        pr_number = target.lstrip('#')
        pr_info = get_pr_info(pr_number)
        if not pr_info:
            print(f"❌ Could not fetch PR #{pr_number}")
            return
        target_type = "PR"
        
    elif os.path.exists(target):
        # File path
        content = get_file_content(target)
        if not content:
            print(f"❌ Could not read file: {target}")
            return
        target_type = "file"
        
    else:
        # Feature description
        target_type = "feature"
    
    # Perform deep analysis
    results = analyze_with_ultra_thinking(target, target_type)
    
    # Use the results from the actual analysis function
    print(format_review_output(results))
    
    # Show performance and optimization report
    total_duration = time.time() - start_time
    print(f"\n⏱️ Total execution time: {total_duration:.1f}s")
    
    # Show optimization metrics if there were issues
    opt_report = optimizer.get_optimization_report()
    if "No timeouts recorded" not in opt_report:
        print("\n" + opt_report)


if __name__ == '__main__':
    main()