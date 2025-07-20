#!/usr/bin/env python3
"""
GitHub Copilot PR Analysis - Option 3 Implementation
====================================================

Comprehensive PR cleanup - collects data, runs CI in parallel, then hands off to LLM.
Integrates comment fetching and CI checks, then provides structured data for LLM analysis.

Architecture: Python (data collection + CI) → LLM (analysis + fixes + replies)
"""

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
    
    def __init__(self, pr_number: Optional[str] = None):
        """Initialize with optional PR number (auto-detects if None)."""
        self.pr_number = pr_number or self._detect_pr_number()
        self.repo = self._get_repo_info()
        self.start_time = time.time()
        self.data_dir = f"/tmp/copilot_pr_{self.pr_number}"
        self.ci_result = "UNKNOWN"
        
        # Create data directory
        os.makedirs(self.data_dir, exist_ok=True)
        
        print(f"🤖 GitHub Copilot PR Analyzer (Option 3)")
        print(f"=========================================")
        print(f"PR #{self.pr_number} | Repository: {self.repo}")
        print(f"Data directory: {self.data_dir}")
    
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
    
    def collect_all_data(self) -> Dict:
        """Collect all data in parallel: comments + CI status + CI replica."""
        print("\n🔄 Starting parallel data collection...")
        
        # Results storage
        results = {}
        
        def collect_comments():
            results['comments'] = self.fetch_all_comments()
        
        def collect_ci_status():
            results['ci_status'] = self.check_ci_status()
        
        def collect_ci_replica():
            results['ci_replica'] = self.run_ci_replica()
        
        # Run all collections in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(collect_comments),
                executor.submit(collect_ci_status),
                executor.submit(collect_ci_replica)
            ]
            
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
            
            f.write(f"\n## Ready for LLM Analysis\n")
            f.write(f"All data has been collected and is ready for intelligent analysis.\n")
            f.write(f"The LLM should now:\n")
            f.write(f"1. Read comments.json and categorize issues by priority\n")
            f.write(f"2. Address failing tests and CI issues\n")
            f.write(f"3. Apply automatic fixes where appropriate\n")
            f.write(f"4. Reply to comments using GitHub MCP\n")
            f.write(f"5. Generate final mergeability report\n")
    
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
    """Main entry point for /copilot command."""
    
    # Parse arguments
    pr_number = None
    if len(sys.argv) > 1:
        pr_number = sys.argv[1]
    
    # Show help if requested
    if pr_number in ['-h', '--help']:
        print("GitHub Copilot PR Analysis (Option 3)")
        print("=====================================")
        print()
        print("Usage: /copilot [PR_NUMBER]")
        print()
        print("This command collects PR data (comments, CI status) in parallel,")
        print("then provides structured data for LLM analysis and action.")
        print()
        print("Architecture: Python (data) → LLM (analysis + fixes + replies)")
        print()
        print("Examples:")
        print("  /copilot         # Auto-detect PR from current branch")
        print("  /copilot 123     # Analyze specific PR number")
        print()
        print("Data is saved to /tmp/copilot_pr_[NUMBER]/ for LLM analysis.")
        return
    
    # Run data collection
    collector = CopilotDataCollector(pr_number)
    collector.run()


if __name__ == "__main__":
    main()