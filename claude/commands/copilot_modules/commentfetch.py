#!/usr/bin/env python3
"""
commentfetch.py - Fetch all PR comments from GitHub

Extracts comments from all sources:
- Inline PR comments (code review comments)
- General PR comments (issue comments)
- Review comments
- Copilot suppressed comments

Based on copilot_comment_fetch.py from PR #796 but adapted for modular architecture.
"""

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional, Any

from base import CopilotCommandBase


class CommentFetch(CopilotCommandBase):
    """Fetch all comments from a GitHub PR."""
    
    def __init__(self, pr_number: str, output_file: str = "comments.json"):
        """Initialize comment fetcher.
        
        Args:
            pr_number: GitHub PR number
            output_file: Output filename (default: comments.json)
        """
        super().__init__(pr_number)
        self.output_file = output_file
        self.comments = []
    
    def _get_inline_comments(self) -> List[Dict[str, Any]]:
        """Fetch inline code review comments."""
        self.log("Fetching inline PR comments...")
        
        comments = []
        # Fetch all comments with pagination
        cmd = [
            "gh", "api", 
            f"repos/{self.repo}/pulls/{self.pr_number}/comments",
            "--paginate"
        ]
        
        page_comments = self.run_gh_command(cmd)
        if isinstance(page_comments, list):
            comments.extend(page_comments)
        
        # Standardize format
        standardized = []
        for comment in comments:
            standardized.append({
                'id': comment.get('id'),
                'type': 'inline',
                'body': comment.get('body', ''),
                'author': comment.get('user', {}).get('login', 'unknown'),
                'created_at': comment.get('created_at', ''),
                'file': comment.get('path'),
                'line': comment.get('line') or comment.get('original_line'),
                'position': comment.get('position'),
                'in_reply_to_id': comment.get('in_reply_to_id'),
                'requires_response': self._requires_response(comment)
            })
        
        return standardized
    
    def _get_general_comments(self) -> List[Dict[str, Any]]:
        """Fetch general PR comments (issue comments)."""
        self.log("Fetching general PR comments...")
        
        cmd = [
            "gh", "api",
            f"repos/{self.repo}/issues/{self.pr_number}/comments",
            "--paginate"
        ]
        
        comments = self.run_gh_command(cmd)
        if not isinstance(comments, list):
            return []
        
        # Standardize format
        standardized = []
        for comment in comments:
            standardized.append({
                'id': comment.get('id'),
                'type': 'general',
                'body': comment.get('body', ''),
                'author': comment.get('user', {}).get('login', 'unknown'),
                'created_at': comment.get('created_at', ''),
                'requires_response': self._requires_response(comment)
            })
        
        return standardized
    
    def _get_review_comments(self) -> List[Dict[str, Any]]:
        """Fetch PR review comments."""
        self.log("Fetching PR reviews...")
        
        cmd = [
            "gh", "api",
            f"repos/{self.repo}/pulls/{self.pr_number}/reviews",
            "--paginate"
        ]
        
        reviews = self.run_gh_command(cmd)
        if not isinstance(reviews, list):
            return []
        
        # Extract review body comments
        standardized = []
        for review in reviews:
            if review.get('body'):
                standardized.append({
                    'id': review.get('id'),
                    'type': 'review',
                    'body': review.get('body', ''),
                    'author': review.get('user', {}).get('login', 'unknown'),
                    'created_at': review.get('submitted_at', ''),
                    'state': review.get('state'),
                    'requires_response': self._requires_response(review)
                })
        
        return standardized
    
    def _get_copilot_comments(self) -> List[Dict[str, Any]]:
        """Fetch Copilot suppressed comments if available."""
        self.log("Checking for Copilot comments...")
        
        # Try to get Copilot-specific comments using jq filtering
        cmd = [
            "gh", "api",
            f"repos/{self.repo}/pulls/{self.pr_number}/comments",
            "--jq", '.[] | select(.user.login == "github-advanced-security[bot]" or .user.type == "Bot") | select(.body | contains("copilot"))'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                # Parse JSONL output
                comments = []
                for line in result.stdout.strip().split('\n'):
                    try:
                        comments.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
                
                # Standardize format
                standardized = []
                for comment in comments:
                    standardized.append({
                        'id': comment.get('id'),
                        'type': 'copilot',
                        'body': comment.get('body', ''),
                        'author': 'copilot',
                        'created_at': comment.get('created_at', ''),
                        'file': comment.get('path'),
                        'line': comment.get('line'),
                        'suppressed': True,
                        'requires_response': True  # Copilot comments usually need attention
                    })
                
                return standardized
        except Exception as e:
            self.log(f"Could not fetch Copilot comments: {e}")
        
        return []
    
    def _requires_response(self, comment: Dict[str, Any]) -> bool:
        """Include all comments for Claude to analyze.
        
        Claude will decide what needs responses, not Python pattern matching.
        
        Args:
            comment: Comment data
            
        Returns:
            True (always - let Claude decide)
        """
        # Let Claude decide what needs responses
        # No pattern matching, no keyword detection
        return True
    
    def execute(self) -> Dict[str, Any]:
        """Execute comment fetching from all sources."""
        self.log(f"Fetching all comments for PR #{self.pr_number}")
        
        # Fetch comments in parallel for speed
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self._get_inline_comments): 'inline',
                executor.submit(self._get_general_comments): 'general',
                executor.submit(self._get_review_comments): 'review',
                executor.submit(self._get_copilot_comments): 'copilot'
            }
            
            for future in as_completed(futures):
                comment_type = futures[future]
                try:
                    comments = future.result()
                    self.comments.extend(comments)
                    self.log(f"  Found {len(comments)} {comment_type} comments")
                except Exception as e:
                    self.log_error(f"Failed to fetch {comment_type} comments: {e}")
        
        # Sort by created_at (most recent first)
        self.comments.sort(
            key=lambda c: c.get('created_at', ''), 
            reverse=True
        )
        
        # Count comments needing responses
        needs_response = sum(1 for c in self.comments if c.get('requires_response'))
        
        # Prepare result
        result = {
            'success': True,
            'message': f"Fetched {len(self.comments)} comments ({needs_response} need responses)",
            'data': {
                'pr': self.pr_number,
                'fetched_at': datetime.now().isoformat(),
                'comments': self.comments,
                'metadata': {
                    'total': len(self.comments),
                    'by_type': {
                        'inline': len([c for c in self.comments if c['type'] == 'inline']),
                        'general': len([c for c in self.comments if c['type'] == 'general']),
                        'review': len([c for c in self.comments if c['type'] == 'review']),
                        'copilot': len([c for c in self.comments if c['type'] == 'copilot'])
                    },
                    'needs_response': needs_response,
                    'repo': self.repo
                }
            }
        }
        
        # Save to specified output file
        self.save_json_file(self.output_file, result['data'])
        
        return result


def main():
    """Command line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fetch all comments from a GitHub PR"
    )
    parser.add_argument('pr_number', help='PR number to fetch comments from')
    parser.add_argument(
        '--output', '-o',
        default='comments.json',
        help='Output filename (default: comments.json)'
    )
    
    args = parser.parse_args()
    
    fetcher = CommentFetch(args.pr_number, args.output)
    return fetcher.run()


if __name__ == '__main__':
    sys.exit(main())