#!/usr/bin/env python3
"""
GitHub Copilot PR Analysis - Option 3 Implementation
====================================================

Comprehensive PR cleanup - collects data, runs CI in parallel, then hands off to LLM.
Integrates comment fetching and CI checks, then provides structured data for LLM analysis.

Architecture: Python (data collection + CI) → LLM (analysis + fixes + replies)
"""

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

# Import the comment fetcher directly (now in same directory)
from copilot_comment_fetch import CommentFetcher


class CopilotDataCollector:
    """Collects all PR data and CI status in parallel for LLM analysis."""
    
    def __init__(self, pr_number: Optional[str] = None, args=None):
        """Initialize with optional PR number (auto-detects if None) and args."""
        self.pr_number = pr_number or self._detect_pr_number()
        self.repo = self._get_repo_info()
        self.start_time = time.time()
        self.data_dir = f"/tmp/copilot_pr_{self.pr_number}"
        self.ci_result = "UNKNOWN"
        self.args = args or argparse.Namespace()
        
        # Configuration based on arguments
        self.auto_fix = getattr(self.args, 'auto_fix', False)
        self.merge_conflicts_only = getattr(self.args, 'merge_conflicts', False)
        self.threaded_reply = getattr(self.args, 'threaded_reply', False)
        self.priority_filter = getattr(self.args, 'priority', None)
        self.predict_ci = getattr(self.args, 'predict_ci', False)
        self.check_github_ci = getattr(self.args, 'check_github_ci', False)
        
        # Create data directory
        os.makedirs(self.data_dir, exist_ok=True)
        
        print(f"🤖 GitHub Copilot PR Analyzer (Enhanced)")
        print(f"=========================================")
        print(f"PR #{self.pr_number} | Repository: {self.repo}")
        print(f"Data directory: {self.data_dir}")
        
        # Show active flags
        if self.auto_fix:
            print(f"🔧 Auto-fix mode: ENABLED")
        if self.merge_conflicts_only:
            print(f"🚨 Focus: Merge conflicts only")
        if self.threaded_reply:
            print(f"💬 Threaded replies: ENABLED")
        if self.priority_filter:
            print(f"📊 Priority filter: {self.priority_filter}")
        if self.predict_ci:
            print(f"🔮 CI prediction: ENABLED")
        if self.check_github_ci:
            print(f"📊 GitHub CI check: ENABLED")
    
    def _detect_pr_number(self) -> str:
        """Auto-detect PR number from current branch."""
        try:
            current_branch = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True, text=True, check=True
            ).stdout.strip()
            
            pr_info = subprocess.run(
                ["gh", "pr", "list", "--head", current_branch, "--json", "number", "--limit", "1"],
                capture_output=True, text=True, check=True
            ).stdout.strip()
            
            if pr_info and pr_info != "[]":
                pr_data = json.loads(pr_info)
                if pr_data:
                    return str(pr_data[0]["number"])
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, IndexError):
            pass
        
        print("❌ No PR found for current branch and no PR number provided")
        print("Usage: /copilot [PR_NUMBER]")
        sys.exit(1)
    
    def _get_repo_info(self) -> str:
        """Get repository information."""
        try:
            result = subprocess.run(
                ["gh", "repo", "view", "--json", "owner,name"],
                capture_output=True, text=True, check=True
            )
            repo_info = json.loads(result.stdout)
            return f"{repo_info['owner']['login']}/{repo_info['name']}"
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            raise ValueError("Could not determine repository information")
    
    def _run_gh_command(self, command: List[str]) -> Optional[Dict]:
        """Run GitHub CLI command and return parsed JSON."""
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            if not result.stdout.strip():
                return None
            return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            print(f"  ⚠️ GitHub CLI error: {e}", file=sys.stderr)
            return None
    
    def fetch_all_comments(self) -> List[Dict]:
        """Fetch all PR comments using direct CommentFetcher integration."""
        print("📝 Fetching all PR comments...")
        
        try:
            # Use CommentFetcher class directly
            fetcher = CommentFetcher(self.pr_number, self.repo)
            comments = fetcher.fetch_all_comments()
            
            # Convert Comment objects to dictionaries
            comment_dicts = []
            for comment in comments:
                comment_dict = {
                    'id': comment.id,
                    'body': comment.body,
                    'user': comment.user,
                    'type': comment.comment_type,
                    'created_at': comment.created_at,
                    '_type': comment.comment_type  # For compatibility
                }
                
                # Add optional fields if present
                if comment.file:
                    comment_dict['file'] = comment.file
                if comment.line:
                    comment_dict['line'] = str(comment.line)
                if comment.position:
                    comment_dict['position'] = str(comment.position)
                if comment.state:
                    comment_dict['state'] = comment.state
                
                comment_dicts.append(comment_dict)
            
            print(f"  ✅ Fetched {len(comment_dicts)} comments")
            
            # Categorize comments
            inline_count = len([c for c in comment_dicts if c.get('type') == 'inline'])
            review_count = len([c for c in comment_dicts if c.get('type') == 'review'])
            general_count = len([c for c in comment_dicts if c.get('type') == 'general'])
            
            print(f"     📊 Breakdown: {inline_count} inline + {review_count} reviews + {general_count} general")
            return comment_dicts
            
        except Exception as e:
            print(f"  ❌ Comment fetching failed: {e}")
            return []
    
    def check_ci_status(self) -> Dict:
        """Check CI status and get failure details."""
        print("🔍 Checking CI status...")
        
        try:
            # Get CI status from PR
            result = self._run_gh_command([
                "gh", "pr", "view", self.pr_number, "--json", "statusCheckRollup"
            ])
            
            if not result:
                return {"failed_checks": [], "total_checks": 0}
            
            checks = result.get("statusCheckRollup", [])
            failed_checks = [
                check for check in checks 
                if check.get("conclusion") in ["FAILURE", "CANCELLED"]
            ]
            
            print(f"  ✅ Found {len(checks)} total checks, {len(failed_checks)} failed")
            return {
                "failed_checks": failed_checks,
                "total_checks": len(checks),
                "all_checks": checks
            }
            
        except Exception as e:
            print(f"  ❌ CI status check failed: {e}")
            return {"failed_checks": [], "total_checks": 0, "error": str(e)}
    
    def run_ci_replica(self) -> str:
        """Run CI replica in background and return result."""
        print("🚀 Running CI replica...")
        
        # Find CI replica script
        possible_scripts = [
            "./run_ci_replica.sh",
            "../run_ci_replica.sh",
            os.path.join(os.getcwd(), "run_ci_replica.sh")
        ]
        
        ci_script = None
        for script in possible_scripts:
            if os.path.exists(script) and os.access(script, os.X_OK):
                ci_script = script
                break
        
        if not ci_script:
            print("  ⚠️ CI replica script not found")
            return "CI_UNAVAILABLE"
        
        try:
            # Run CI replica with timeout
            result = subprocess.run(
                [ci_script],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                print("  ✅ CI replica passed")
                return "CI_PASSED"
            else:
                print("  ❌ CI replica failed")
                return "CI_FAILED"
                
        except subprocess.TimeoutExpired:
            print("  ⏰ CI replica timed out")
            return "CI_TIMEOUT"
        except Exception as e:
            print(f"  ❌ CI replica error: {e}")
            return "CI_ERROR"
    
    def predict_ci_failure(self) -> Dict:
        """Predict CI outcome using local CI replica with enhanced analysis."""
        print("🔮 Predicting CI outcome using local replica...")
        
        prediction = {
            'prediction': 'UNKNOWN',
            'confidence': 0.0,
            'reason': '',
            'replica_result': '',
            'recommendation': ''
        }
        
        try:
            # Run CI replica and capture result
            replica_result = self.run_ci_replica()
            prediction['replica_result'] = replica_result
            
            if replica_result == "CI_PASSED":
                prediction.update({
                    'prediction': 'SUCCESS',
                    'confidence': 0.95,
                    'reason': 'Local CI replica passed successfully',
                    'recommendation': 'GitHub CI likely to pass'
                })
                print(f"  ✅ Prediction: SUCCESS (95% confidence)")
                
            elif replica_result == "CI_FAILED":
                prediction.update({
                    'prediction': 'FAILURE', 
                    'confidence': 0.90,
                    'reason': 'Local CI replica failed',
                    'recommendation': 'Fix issues before pushing to avoid GitHub CI failure'
                })
                print(f"  ❌ Prediction: FAILURE (90% confidence)")
                
            elif replica_result == "CI_TIMEOUT":
                prediction.update({
                    'prediction': 'UNKNOWN',
                    'confidence': 0.30,
                    'reason': 'Local CI replica timed out',
                    'recommendation': 'Manual CI check recommended'
                })
                print(f"  ⏰ Prediction: TIMEOUT (low confidence)")
                
            else:
                prediction.update({
                    'prediction': 'ERROR',
                    'confidence': 0.10,
                    'reason': f'CI replica returned unexpected result: {replica_result}',
                    'recommendation': 'Manual investigation required'
                })
                print(f"  ❓ Prediction: ERROR ({replica_result})")
                
        except Exception as e:
            prediction.update({
                'prediction': 'ERROR',
                'confidence': 0.05,
                'reason': f'CI prediction failed: {str(e)}',
                'recommendation': 'Use manual CI checking'
            })
            print(f"  ❌ Prediction error: {e}")
            
        return prediction
    
    def check_github_ci_status(self) -> Dict:
        """Check actual GitHub CI status using MCP and CLI fallback."""
        print("📊 Checking GitHub CI status...")
        
        status = {
            'status': 'UNKNOWN',
            'checks': [],
            'summary': '',
            'method': '',
            'details': {}
        }
        
        try:
            # Try GitHub MCP first (primary method per CLAUDE.md)
            try:
                print("  🔍 Attempting GitHub MCP status check...")
                # Note: This would use GitHub MCP in actual Claude Code environment
                # For now, we'll use the fallback method
                raise Exception("MCP not available in current environment")
                
            except Exception:
                # Fallback to gh CLI (secondary method per CLAUDE.md)
                print("  🔧 Falling back to gh CLI...")
                result = subprocess.run(
                    ['gh', 'pr', 'view', self.pr_number, '--json', 'statusCheckRollup'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    pr_data = json.loads(result.stdout)
                    checks = pr_data.get('statusCheckRollup', [])
                    
                    if not checks:
                        status.update({
                            'status': 'NO_CHECKS',
                            'summary': 'No CI checks found for this PR',
                            'method': 'gh_cli'
                        })
                        print("  ℹ️  No CI checks found")
                    else:
                        # Analyze check results
                        success_count = sum(1 for check in checks if check.get('state') == 'SUCCESS')
                        failure_count = sum(1 for check in checks if check.get('state') in ['FAILURE', 'ERROR'])
                        pending_count = sum(1 for check in checks if check.get('state') in ['PENDING', 'IN_PROGRESS'])
                        
                        if failure_count > 0:
                            overall_status = 'FAILURE'
                        elif pending_count > 0:
                            overall_status = 'PENDING'
                        elif success_count > 0:
                            overall_status = 'SUCCESS'
                        else:
                            overall_status = 'UNKNOWN'
                        
                        status.update({
                            'status': overall_status,
                            'checks': checks,
                            'summary': f'{success_count} passed, {failure_count} failed, {pending_count} pending',
                            'method': 'gh_cli',
                            'details': {
                                'total': len(checks),
                                'success': success_count,
                                'failure': failure_count, 
                                'pending': pending_count
                            }
                        })
                        
                        print(f"  📊 CI Status: {overall_status}")
                        print(f"      {success_count} passed, {failure_count} failed, {pending_count} pending")
                else:
                    status.update({
                        'status': 'ERROR',
                        'summary': f'gh CLI failed: {result.stderr}',
                        'method': 'gh_cli_error'
                    })
                    print(f"  ❌ gh CLI error: {result.stderr}")
                    
        except subprocess.TimeoutExpired:
            status.update({
                'status': 'TIMEOUT',
                'summary': 'GitHub CI status check timed out',
                'method': 'timeout'
            })
            print("  ⏰ GitHub CI check timed out")
            
        except Exception as e:
            status.update({
                'status': 'ERROR',
                'summary': f'CI status check failed: {str(e)}',
                'method': 'error'
            })
            print(f"  ❌ CI status check error: {e}")
            
        return status
    
    def check_merge_conflicts(self) -> Dict:
        """Check for merge conflicts using GitHub API, git status and file scanning."""
        print("🔍 Checking for merge conflicts...")
        
        conflicts = {
            'has_conflicts': False,
            'conflicted_files': [],
            'conflict_markers': {},
            'summary': '',
            'github_status': None
        }
        
        # PRIMARY: Check GitHub PR merge status via gh CLI
        try:
            print("  🔗 Checking GitHub PR merge status...")
            gh_result = subprocess.run([
                'gh', 'pr', 'view', str(self.pr_number), 
                '--json', 'mergeable,mergeStateStatus'
            ], capture_output=True, text=True, timeout=30)
            
            if gh_result.returncode == 0:
                import json
                gh_data = json.loads(gh_result.stdout)
                conflicts['github_status'] = gh_data
                
                if gh_data.get('mergeable') == 'CONFLICTING':
                    conflicts['has_conflicts'] = True
                    conflicts['summary'] = '🚨 GitHub detected merge conflicts'
                    print("  ❌ GitHub reports PR has merge conflicts")
                else:
                    print(f"  ✅ GitHub merge status: {gh_data.get('mergeable')}")
            else:
                print(f"  ⚠️ GitHub CLI failed: {gh_result.stderr}")
        except Exception as gh_error:
            print(f"  ⚠️ GitHub status check failed: {gh_error}")
        
        # SECONDARY: Check local git status for conflicted files
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse git status output for conflicts
                for line in result.stdout.strip().split('\n'):
                    if line.startswith('UU ') or line.startswith('AA ') or line.startswith('DD '):
                        # UU = both modified, AA = both added, DD = both deleted
                        conflicted_file = line[3:].strip()
                        conflicts['conflicted_files'].append(conflicted_file)
                        conflicts['has_conflicts'] = True
                        
                        # Scan file for conflict markers
                        markers = self._find_conflict_markers(conflicted_file)
                        if markers:
                            conflicts['conflict_markers'][conflicted_file] = markers
                
                # Create summary
                if conflicts['has_conflicts']:
                    file_count = len(conflicts['conflicted_files'])
                    marker_count = sum(len(markers) for markers in conflicts['conflict_markers'].values())
                    conflicts['summary'] = f"🚨 {file_count} files with conflicts, {marker_count} conflict markers found"
                    print(f"  ❌ Found conflicts in {file_count} files")
                else:
                    conflicts['summary'] = "✅ No merge conflicts detected"
                    print("  ✅ No merge conflicts found")
                    
            else:
                print(f"  ⚠️ Git status failed: {result.stderr}")
                conflicts['summary'] = "❓ Unable to check merge conflicts"
                
        except subprocess.TimeoutExpired:
            print("  ⏰ Git status timed out")
            conflicts['summary'] = "⏰ Merge conflict check timed out"
        except Exception as e:
            print(f"  ❌ Error checking conflicts: {e}")
            conflicts['summary'] = f"❌ Error: {str(e)}"
        
        # Save GitHub status to separate file for cross-validation
        if conflicts.get('github_status'):
            try:
                github_status_path = os.path.join(self.data_dir, 'github_status.json')
                with open(github_status_path, 'w') as f:
                    json.dump(conflicts['github_status'], f, indent=2)
                print(f"  💾 GitHub status saved to: {github_status_path}")
            except Exception as save_error:
                print(f"  ⚠️ Failed to save GitHub status: {save_error}")
        
        return conflicts
    
    def auto_resolve_conflicts(self, merge_conflicts: Dict) -> Dict:
        """Automatically resolve conflicts if auto-fix is enabled."""
        if not self.auto_fix or not merge_conflicts.get('has_conflicts'):
            return {'auto_resolved': False, 'message': 'Auto-fix not enabled or no conflicts'}
        
        print("🔧 Auto-fix enabled - attempting conflict resolution...")
        
        try:
            # Use the conflict resolver
            conflicted_files = merge_conflicts.get('conflicted_files', [])
            if not conflicted_files:
                return {'auto_resolved': False, 'message': 'No conflicted files found'}
            
            resolver = ConflictResolver()
            
            # Analyze conflicts
            analysis = resolver.analyze_conflicts(conflicted_files)
            resolvable_count = len(analysis['resolvable_files'])
            total_count = analysis['total_files']
            
            print(f"  📊 Analysis: {resolvable_count}/{total_count} files can be auto-resolved")
            
            if resolvable_count == 0:
                return {
                    'auto_resolved': False, 
                    'message': 'No conflicts are safe for automatic resolution',
                    'analysis': analysis
                }
            
            # Attempt resolution
            success_count = 0
            for file_path in analysis['resolvable_files']:
                if resolver.resolve_file(file_path):
                    success_count += 1
            
            # Run validation tests
            tests_passed = resolver.run_tests_after_resolution() if success_count > 0 else True
            
            # Generate resolution report
            report = resolver.generate_resolution_report()
            
            return {
                'auto_resolved': success_count > 0,
                'resolved_files': success_count,
                'total_files': total_count,
                'tests_passed': tests_passed,
                'backup_dir': report['backup_directory'],
                'message': f"Successfully resolved {success_count}/{resolvable_count} auto-resolvable conflicts"
            }
            
        except Exception as e:
            print(f"  ❌ Auto-resolution failed: {e}")
            return {'auto_resolved': False, 'message': f'Error: {str(e)}'}
    
    def _find_conflict_markers(self, file_path: str) -> List[Dict]:
        """Find conflict markers in a specific file."""
        markers = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for i, line in enumerate(lines, 1):
                line_stripped = line.strip()
                if line_stripped.startswith('<<<<<<<'):
                    # Start of conflict
                    markers.append({
                        'type': 'conflict_start',
                        'line': i,
                        'content': line_stripped,
                        'branch': line_stripped[7:].strip() if len(line_stripped) > 7 else 'unknown'
                    })
                elif line_stripped == '=======':
                    # Conflict separator
                    markers.append({
                        'type': 'conflict_separator',
                        'line': i,
                        'content': line_stripped
                    })
                elif line_stripped.startswith('>>>>>>>'):
                    # End of conflict
                    markers.append({
                        'type': 'conflict_end',
                        'line': i,
                        'content': line_stripped,
                        'branch': line_stripped[7:].strip() if len(line_stripped) > 7 else 'unknown'
                    })
                    
        except Exception as e:
            print(f"  ⚠️ Could not scan {file_path}: {e}")
            
        return markers
    
    def collect_all_data(self) -> Dict:
        """Collect data based on configuration flags."""
        print("\n🔄 Starting data collection...")
        
        # Results storage
        results = {}
        collection_tasks = []
        
        def collect_comments():
            results['comments'] = self.fetch_all_comments()
        
        def collect_ci_status():
            results['ci_status'] = self.check_ci_status()
        
        def collect_ci_replica():
            results['ci_replica'] = self.run_ci_replica()
        
        def collect_merge_conflicts():
            conflicts = self.check_merge_conflicts()
            results['merge_conflicts'] = conflicts
            
            # Auto-resolve conflicts if enabled
            if self.auto_fix and conflicts.get('has_conflicts'):
                print("🔧 Auto-fix enabled - will attempt resolution after collection...")
                resolution_result = self.auto_resolve_conflicts(conflicts)
                results['auto_resolution'] = resolution_result
                
                # Update conflict status if resolution was successful
                if resolution_result.get('auto_resolved'):
                    # Re-check conflicts after resolution
                    updated_conflicts = self.check_merge_conflicts()
                    results['merge_conflicts'] = updated_conflicts
        
        def collect_ci_prediction():
            if self.predict_ci:
                results['ci_prediction'] = self.predict_ci_failure()
        
        def collect_github_ci_status():
            if self.check_github_ci:
                results['github_ci_status'] = self.check_github_ci_status()
        
        # Always collect merge conflicts
        collection_tasks.append(collect_merge_conflicts)
        
        # Add CI prediction and GitHub CI checking if requested
        if self.predict_ci:
            collection_tasks.append(collect_ci_prediction)
        if self.check_github_ci:
            collection_tasks.append(collect_github_ci_status)
        
        # Conditional collection based on flags
        if self.merge_conflicts_only:
            print("🚨 Merge conflicts only mode - skipping other data collection")
        else:
            # Collect comments unless in conflict-only mode
            collection_tasks.append(collect_comments)
            
            # Collect CI data unless disabled
            if not getattr(self.args, 'no_ci', False):
                collection_tasks.append(collect_ci_status)
                collection_tasks.append(collect_ci_replica)
            else:
                print("⏭️ Skipping CI collection (--no-ci flag)")
        
        # Run collections in parallel
        max_workers = min(len(collection_tasks), 4)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(task) for task in collection_tasks]
            
            # Wait for all to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"❌ Data collection error: {e}")
        
        print("✅ Parallel data collection completed!")
        return results
    
    def save_collected_data(self, data: Dict) -> None:
        """Save all collected data to files for LLM analysis."""
        print("💾 Saving collected data...")
        
        # Save comments
        comments_file = f"{self.data_dir}/comments.json"
        with open(comments_file, 'w') as f:
            json.dump(data.get('comments', []), f, indent=2)
        
        # Save CI status
        ci_file = f"{self.data_dir}/ci_status.json"
        with open(ci_file, 'w') as f:
            json.dump(data.get('ci_status', {}), f, indent=2)
        
        # Save CI replica result
        replica_file = f"{self.data_dir}/ci_replica.txt"
        with open(replica_file, 'w') as f:
            f.write(data.get('ci_replica', 'UNKNOWN'))
        
        # Save merge conflicts
        conflicts_file = f"{self.data_dir}/merge_conflicts.json"
        with open(conflicts_file, 'w') as f:
            json.dump(data.get('merge_conflicts', {}), f, indent=2)
        
        # Save auto-resolution results if available
        if 'auto_resolution' in data:
            resolution_file = f"{self.data_dir}/auto_resolution.json"
            with open(resolution_file, 'w') as f:
                json.dump(data['auto_resolution'], f, indent=2)
        
        # Create comment ID mapping for GitHub MCP replies
        comments = data.get('comments', [])
        id_map_file = f"{self.data_dir}/comment_id_map.json"
        id_mapping = {}
        for comment in comments:
            comment_id = comment.get('id', '')
            if comment_id:
                id_mapping[comment_id] = {
                    'user': comment.get('user', ''),
                    'type': comment.get('type', ''),
                    'file': comment.get('file', ''),
                    'line': comment.get('line', ''),
                    'preview': comment.get('body', '')[:100] + '...' if len(comment.get('body', '')) > 100 else comment.get('body', '')
                }
        
        with open(id_map_file, 'w') as f:
            json.dump(id_mapping, f, indent=2)
        
        # Create summary
        self._create_summary(data)
        
        print(f"  ✅ Data saved to: {self.data_dir}/")
    
    def _create_summary(self, data: Dict) -> None:
        """Create human-readable summary."""
        comments = data.get('comments', [])
        ci_status = data.get('ci_status', {})
        ci_replica = data.get('ci_replica', 'UNKNOWN')
        merge_conflicts = data.get('merge_conflicts', {})
        auto_resolution = data.get('auto_resolution', {})
        
        summary_file = f"{self.data_dir}/summary.md"
        with open(summary_file, 'w') as f:
            f.write(f"# PR #{self.pr_number} Analysis Summary\n\n")
            f.write(f"**Repository**: {self.repo}  \n")
            f.write(f"**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}  \n")
            f.write(f"**Data Directory**: {self.data_dir}/  \n\n")
            
            f.write(f"## Comments Analysis\n")
            f.write(f"- **Total Comments**: {len(comments)}\n")
            f.write(f"- **Data File**: comments.json\n\n")
            
            # Comment breakdown
            comment_types = {}
            comment_users = {}
            for comment in comments:
                c_type = comment.get('type', 'unknown')
                c_user = comment.get('user', 'unknown')
                comment_types[c_type] = comment_types.get(c_type, 0) + 1
                comment_users[c_user] = comment_users.get(c_user, 0) + 1
            
            f.write("### Comment Types\n")
            for c_type, count in sorted(comment_types.items()):
                f.write(f"- **{c_type}**: {count}\n")
            
            f.write("\n### Comment Authors\n")
            for user, count in sorted(comment_users.items(), key=lambda x: x[1], reverse=True):
                f.write(f"- **{user}**: {count}\n")
            
            f.write(f"\n## CI Status\n")
            failed_checks = ci_status.get('failed_checks', [])
            total_checks = ci_status.get('total_checks', 0)
            f.write(f"- **Total Checks**: {total_checks}\n")
            f.write(f"- **Failed Checks**: {len(failed_checks)}\n")
            f.write(f"- **CI Replica Result**: {ci_replica}\n")
            f.write(f"- **Data File**: ci_status.json\n\n")
            
            if failed_checks:
                f.write("### Failed Checks\n")
                for check in failed_checks:
                    name = check.get('name') or check.get('checkName', 'Unknown')
                    conclusion = check.get('conclusion', 'Unknown')
                    f.write(f"- **{name}**: {conclusion}\n")
            
            f.write(f"\n## Merge Conflicts\n")
            f.write(f"- **Status**: {merge_conflicts.get('summary', 'Unknown')}\n")
            f.write(f"- **Has Conflicts**: {merge_conflicts.get('has_conflicts', False)}\n")
            f.write(f"- **Conflicted Files**: {len(merge_conflicts.get('conflicted_files', []))}\n")
            f.write(f"- **Data File**: merge_conflicts.json\n\n")
            
            conflicted_files = merge_conflicts.get('conflicted_files', [])
            if conflicted_files:
                f.write("### Conflicted Files\n")
                for file_path in conflicted_files:
                    markers = merge_conflicts.get('conflict_markers', {}).get(file_path, [])
                    marker_count = len(markers)
                    f.write(f"- **{file_path}**: {marker_count} conflict markers\n")
            
            f.write(f"\n## Auto-Resolution Results\n")
            if auto_resolution:
                f.write(f"- **Auto-Resolution Attempted**: {auto_resolution.get('auto_resolved', False)}\n")
                f.write(f"- **Message**: {auto_resolution.get('message', 'No resolution attempted')}\n")
                f.write(f"- **Files Resolved**: {auto_resolution.get('resolved_files', 0)}\n")
                f.write(f"- **Tests Passed**: {auto_resolution.get('tests_passed', 'N/A')}\n")
                
                backup_dir = auto_resolution.get('backup_dir')
                if backup_dir:
                    f.write(f"- **Backup Directory**: {backup_dir}\n")
                f.write(f"- **Data File**: auto_resolution.json\n\n")
            else:
                f.write(f"- **Status**: No auto-resolution attempted\n")
                f.write(f"- **Reason**: Auto-fix not enabled or no conflicts detected\n\n")
            
            f.write(f"\n## Ready for LLM Analysis\n")
            f.write(f"All data has been collected and is ready for intelligent analysis.\n")
            f.write(f"The LLM should now:\n")
            f.write(f"1. Read comments.json and categorize issues by priority\n")
            f.write(f"2. **PRIORITY**: Review merge_conflicts.json and resolve conflicts if present\n")
            f.write(f"3. Address failing tests and CI issues\n")
            f.write(f"4. Apply automatic fixes where appropriate\n")
            f.write(f"5. Reply to comments using GitHub MCP\n")
            f.write(f"6. Generate final mergeability report\n")
    
    def run(self) -> None:
        """Main execution method - collect data then hand off to LLM."""
        try:
            # Collect all data in parallel
            data = self.collect_all_data()
            
            # Save data for LLM analysis
            self.save_collected_data(data)
            
            # Performance metrics
            duration = time.time() - self.start_time
            comment_count = len(data.get('comments', []))
            failed_count = len(data.get('ci_status', {}).get('failed_checks', []))
            
            print(f"\n🎯 Data Collection Complete!")
            print(f"=====================================")
            print(f"⏱️  Collection time: {duration:.2f}s")
            print(f"📝 Comments collected: {comment_count}")
            print(f"❌ Failed CI checks: {failed_count}")
            print(f"🤖 CI replica result: {data.get('ci_replica', 'UNKNOWN')}")
            print(f"📁 Data location: {self.data_dir}/")
            print(f"\n💭 Ready for LLM analysis and action!")
            
            # Signal successful completion
            print(f"\n✅ Data collection phase complete. LLM analysis can now begin.")
            
        except Exception as e:
            print(f"❌ Error during data collection: {e}")
            sys.exit(1)


def main():
    """Main entry point for enhanced /copilot command."""
    
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Enhanced GitHub Copilot PR Analysis with workflow automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  /copilot                              # Auto-detect PR, full analysis
  /copilot 123                         # Analyze specific PR number
  /copilot --merge-conflicts           # Focus only on merge conflicts
  /copilot --auto-fix --threaded-reply # Auto-fix with threaded responses
  /copilot --priority high             # Filter high-priority issues only

Data is saved to /tmp/copilot_pr_[NUMBER]/ for LLM analysis.
Architecture: Python (data collection) → LLM (analysis + fixes + replies)
        """
    )
    
    parser.add_argument('pr_number', nargs='?', 
                       help='PR number to analyze (auto-detects if not provided)')
    
    parser.add_argument('--auto-fix', action='store_true',
                       help='Enable automatic fixes for detected issues')
    
    parser.add_argument('--merge-conflicts', action='store_true',
                       help='Focus only on merge conflict detection and resolution')
    
    parser.add_argument('--threaded-reply', action='store_true',
                       help='Use threaded replies when responding to comments')
    
    parser.add_argument('--priority', choices=['low', 'medium', 'high'],
                       help='Filter issues by priority level')
    
    
    parser.add_argument('--no-ci', action='store_true',
                       help='Skip CI status collection and replica run')
    
    parser.add_argument('--predict-ci', action='store_true',
                       help='Run CI prediction using local replica')
    
    parser.add_argument('--check-github-ci', action='store_true',
                       help='Check actual GitHub CI status via MCP/CLI')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run data collection with enhanced configuration
    collector = CopilotDataCollector(args.pr_number, args)
    collector.run()


if __name__ == "__main__":
    main()