#!/usr/bin/env python3
"""
Copilot Reporter Module - Evidence-based reply generation

This module generates truthful, evidence-based replies to GitHub PR comments
with actual proof of what was implemented vs what was acknowledged.
"""

import json
import subprocess
import logging
from dataclasses import dataclass
import os
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

# Import our modules - will be imported at runtime to avoid circular dependencies

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResponseType(Enum):
    """Types of responses we can generate"""
    IMPLEMENTED = "implemented"
    ACKNOWLEDGED = "acknowledged"
    DECLINED = "declined"

@dataclass
class ResponseEvidence:
    """Evidence for a response"""
    commit_hash: Optional[str] = None
    files_changed: List[str] = None
    test_results: Optional[str] = None
    diff_summary: Optional[str] = None
    
    def __post_init__(self):
        if self.files_changed is None:
            self.files_changed = []

@dataclass
class CommentResponse:
    """Response to a GitHub comment"""
    comment_id: str
    original_comment: str
    response_type: ResponseType
    response_text: str
    evidence: ResponseEvidence
    timestamp: str

class CopilotReporter:
    """Main reporter class for generating evidence-based replies"""
    
    def __init__(self):
        self.repo_info = self._get_repo_info()
    
    def _get_repo_info(self) -> str:
        """Get repository information"""
        try:
            result = subprocess.run(
                ['gh', 'repo', 'view', '--json', 'owner,name'],
                capture_output=True,
                text=True,
                check=True
            )
            data = json.loads(result.stdout)
            return f"{data['owner']['login']}/{data['name']}"
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to get repo info: {e}")
            return "unknown/unknown"
    
    def get_commit_diff(self, commit_hash: str) -> Optional[str]:
        """Get diff summary for a commit"""
        try:
            result = subprocess.run(
                ['git', 'show', '--stat', commit_hash],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get diff for {commit_hash}: {e}")
            return None
    
    def run_tests(self) -> Optional[str]:
        """Run tests and return results"""
        try:
            # Check if run_tests.sh exists
            if os.path.exists('./run_tests.sh'):
                result = subprocess.run(
                    ['./run_tests.sh'],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode == 0:
                    return "✅ All tests passed"
                else:
                    # Extract failure summary
                    lines = result.stdout.split('\n')
                    failure_lines = [line for line in lines if 'FAILED' in line or 'ERROR' in line]
                    if failure_lines:
                        return f"❌ {len(failure_lines)} test failures"
                    else:
                        return "❌ Tests failed (see logs for details)"
            else:
                return "⚠️ No test runner found"
                
        except subprocess.TimeoutExpired:
            return "⚠️ Tests timed out"
        except Exception as e:
            logger.error(f"Error running tests: {e}")
            return f"❌ Test execution failed: {e}"
    
    def generate_implemented_response(self, comment: "Comment", implementation_results: List["ImplementationResult"]) -> "CommentResponse":
        """Generate response for successfully implemented suggestions"""
        # Filter successful results
        successful_results = [r for r in implementation_results if r.success and r.changes_made]
        
        if not successful_results:
            # No actual implementation - fall back to acknowledged
            return self.generate_acknowledged_response(comment, "Could not implement automatically")
        
        # Build evidence
        evidence = ResponseEvidence()
        
        # Get commit hash from results
        commit_hashes = [r.commit_hash for r in successful_results if r.commit_hash]
        if commit_hashes:
            evidence.commit_hash = commit_hashes[0]  # Use first commit
            evidence.diff_summary = self.get_commit_diff(evidence.commit_hash)
        
        # Get affected files
        evidence.files_changed = list(set(r.file_path for r in successful_results))
        
        # Run tests to verify changes don't break functionality
        evidence.test_results = self.run_tests()
        
        # Build response text
        response_lines = [
            f"✅ **IMPLEMENTED**: {comment.body[:100]}{'...' if len(comment.body) > 100 else ''}"
        ]
        
        # Add implementation details
        response_lines.append("\n**Changes made:**")
        for result in successful_results:
            response_lines.append(f"- {result.description}")
            for change in result.changes_made:
                response_lines.append(f"  - {change}")
        
        # Add evidence
        if evidence.commit_hash:
            response_lines.append(f"\n**Evidence:**")
            response_lines.append(f"- Commit: {evidence.commit_hash}")
            
            if evidence.files_changed:
                response_lines.append(f"- Files modified: {', '.join(evidence.files_changed)}")
            
            if evidence.test_results:
                response_lines.append(f"- Tests: {evidence.test_results}")
        
        response_text = "\n".join(response_lines)
        
        return CommentResponse(
            comment_id=comment.id,
            original_comment=comment.body,
            response_type=ResponseType.IMPLEMENTED,
            response_text=response_text,
            evidence=evidence,
            timestamp=datetime.now().isoformat()
        )
    
    def generate_acknowledged_response(self, comment: "Comment", reason: str = "") -> "CommentResponse":
        """Generate response for acknowledged but not implemented suggestions"""
        
        response_lines = [
            f"🔄 **ACKNOWLEDGED**: {comment.body[:100]}{'...' if len(comment.body) > 100 else ''}"
        ]
        
        if reason:
            response_lines.append(f"\n**Reason**: {reason}")
        
        response_lines.append("\n**Status**: Will address in follow-up commit")
        
        response_text = "\n".join(response_lines)
        
        return CommentResponse(
            comment_id=comment.id,
            original_comment=comment.body,
            response_type=ResponseType.ACKNOWLEDGED,
            response_text=response_text,
            evidence=ResponseEvidence(),
            timestamp=datetime.now().isoformat()
        )
    
    def generate_declined_response(self, comment: "Comment", reason: str) -> "CommentResponse":
        """Generate response for declined suggestions"""
        
        response_lines = [
            f"❌ **DECLINED**: {comment.body[:100]}{'...' if len(comment.body) > 100 else ''}"
        ]
        
        response_lines.append(f"\n**Reason**: {reason}")
        
        response_text = "\n".join(response_lines)
        
        return CommentResponse(
            comment_id=comment.id,
            original_comment=comment.body,
            response_type=ResponseType.DECLINED,
            response_text=response_text,
            evidence=ResponseEvidence(),
            timestamp=datetime.now().isoformat()
        )
    
    def post_comment_response(self, pr_number: str, response: CommentResponse) -> bool:
        """Post a response to a GitHub PR comment"""
        try:
            # For inline comments, we need to use the API differently
            # For now, we'll post as a general PR comment
            
            # Create comment body
            comment_body = f"**Reply to comment {response.comment_id}:**\n\n{response.response_text}"
            
            # Post comment
            result = subprocess.run(
                ['gh', 'pr', 'comment', pr_number, '--body', comment_body],
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"Posted response to comment {response.comment_id}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to post response to comment {response.comment_id}: {e}")
            return False
    
    def generate_summary_report(self, responses: List[CommentResponse]) -> str:
        """Generate a comprehensive summary report"""
        implemented_count = sum(1 for r in responses if r.response_type == ResponseType.IMPLEMENTED)
        acknowledged_count = sum(1 for r in responses if r.response_type == ResponseType.ACKNOWLEDGED)
        declined_count = sum(1 for r in responses if r.response_type == ResponseType.DECLINED)
        
        report_lines = [
            "# 🤖 Copilot Auto-Implementation Report",
            "",
            f"**Total suggestions processed:** {len(responses)}",
            f"- ✅ Implemented: {implemented_count}",
            f"- 🔄 Acknowledged: {acknowledged_count}",
            f"- ❌ Declined: {declined_count}",
            "",
            "## Implementation Details",
            ""
        ]
        
        # Add details for implemented suggestions
        if implemented_count > 0:
            report_lines.append("### ✅ Successfully Implemented")
            for response in responses:
                if response.response_type == ResponseType.IMPLEMENTED:
                    report_lines.append(f"- {response.original_comment[:100]}{'...' if len(response.original_comment) > 100 else ''}")
                    if response.evidence.commit_hash:
                        report_lines.append(f"  - Commit: {response.evidence.commit_hash}")
                    if response.evidence.files_changed:
                        report_lines.append(f"  - Files: {', '.join(response.evidence.files_changed)}")
            report_lines.append("")
        
        # Add details for acknowledged suggestions
        if acknowledged_count > 0:
            report_lines.append("### 🔄 Acknowledged for Follow-up")
            for response in responses:
                if response.response_type == ResponseType.ACKNOWLEDGED:
                    report_lines.append(f"- {response.original_comment[:100]}{'...' if len(response.original_comment) > 100 else ''}")
            report_lines.append("")
        
        # Add details for declined suggestions
        if declined_count > 0:
            report_lines.append("### ❌ Declined")
            for response in responses:
                if response.response_type == ResponseType.DECLINED:
                    report_lines.append(f"- {response.original_comment[:100]}{'...' if len(response.original_comment) > 100 else ''}")
            report_lines.append("")
        
        # Add overall status
        report_lines.extend([
            "## Overall Status",
            ""
        ])
        
        if implemented_count > 0:
            report_lines.append("🎯 **This PR has been automatically improved with working implementations.**")
        elif acknowledged_count > 0:
            report_lines.append("📋 **Suggestions have been acknowledged and will be addressed in follow-up commits.**")
        else:
            report_lines.append("ℹ️ **No actionable suggestions found for automatic implementation.**")
        
        return "\n".join(report_lines)
    
    def save_report(self, responses: List[CommentResponse], report_content: str) -> str:
        """Save the report to a file"""
        try:
            # Create tmp directory if it doesn't exist
            os.makedirs('tmp', exist_ok=True)
            
            # Save report
            report_file = f'tmp/copilot_implementation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            # Save detailed JSON data
            json_file = f'tmp/copilot_responses_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump([{
                    'comment_id': r.comment_id,
                    'original_comment': r.original_comment,
                    'response_type': r.response_type.value,
                    'response_text': r.response_text,
                    'evidence': {
                        'commit_hash': r.evidence.commit_hash,
                        'files_changed': r.evidence.files_changed,
                        'test_results': r.evidence.test_results,
                        'diff_summary': r.evidence.diff_summary
                    },
                    'timestamp': r.timestamp
                } for r in responses], f, indent=2)
            
            logger.info(f"Report saved to {report_file}")
            logger.info(f"JSON data saved to {json_file}")
            
            return report_file
            
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            return ""

def main():
    """Main function for standalone testing"""
    
    # This would typically be called from the main copilot orchestrator
    # For testing, we can generate sample responses
    
    reporter = CopilotReporter()
    
    # Sample data for testing
    sample_responses = [
        CommentResponse(
            comment_id="123",
            original_comment="Remove unused imports from main.py",
            response_type=ResponseType.IMPLEMENTED,
            response_text="✅ IMPLEMENTED: Removed 3 unused imports",
            evidence=ResponseEvidence(
                commit_hash="abc123",
                files_changed=["main.py"],
                test_results="✅ All tests passed"
            ),
            timestamp=datetime.now().isoformat()
        ),
        CommentResponse(
            comment_id="456",
            original_comment="Consider using a more efficient algorithm",
            response_type=ResponseType.ACKNOWLEDGED,
            response_text="🔄 ACKNOWLEDGED: Will address in follow-up",
            evidence=ResponseEvidence(),
            timestamp=datetime.now().isoformat()
        )
    ]
    
    # Generate and save report
    report_content = reporter.generate_summary_report(sample_responses)
    print("Generated report:")
    print(report_content)
    
    report_file = reporter.save_report(sample_responses, report_content)
    print(f"\nReport saved to: {report_file}")

if __name__ == "__main__":
    main()