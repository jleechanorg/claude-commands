#!/usr/bin/env python3
"""
copilot_comment_fetch.py - Standalone GitHub PR Comment Fetcher

Extracts and sorts GitHub PR comments with robust pagination handling.
Replaces complex shell script logic with clean Python implementation.

Features:
- Fetches all comment types (inline, reviews, general)
- Implements 3-page pagination strategy for completeness
- Sorts by most recent first (chronological descending)
- Bot and user comment filtering
- JSON output compatible with shell workflow
- Standalone testing capability
"""

import json
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class Comment:
    """Represents a GitHub comment with standardized fields."""
    id: str
    body: str
    user: str
    comment_type: str
    created_at: str
    file: Optional[str] = None
    line: Optional[int] = None
    position: Optional[int] = None
    state: Optional[str] = None


class CommentFetcher:
    """GitHub PR comment fetcher with advanced pagination and sorting."""
    
    def __init__(self, pr_number: str, repo: str = None):
        """Initialize comment fetcher.
        
        Args:
            pr_number: GitHub PR number
            repo: Repository in format "owner/name" (auto-detected if None)
        """
        self.pr_number = pr_number
        self.repo = repo or self._get_current_repo()
        self.total_comments = 0
        self.fetch_duration = 0
        
    def _get_current_repo(self) -> str:
        """Auto-detect current repository from GitHub CLI."""
        try:
            result = subprocess.run(
                ["gh", "repo", "view", "--json", "owner,name"],
                capture_output=True, text=True, check=True
            )
            repo_info = json.loads(result.stdout)
            return f"{repo_info['owner']['login']}/{repo_info['name']}"
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            raise ValueError("Could not auto-detect repository. Please specify repo parameter.")
    
    def _run_gh_command(self, command: List[str]) -> List[Dict[str, Any]]:
        """Run GitHub CLI command and return parsed JSON."""
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            if not result.stdout.strip():
                return []
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"GitHub CLI error: {e.stderr}", file=sys.stderr)
            return []
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}", file=sys.stderr)
            return []
    
    def _get_rest_api_pagination_info(self) -> int:
        """Get total number of pages for REST API inline comments using per_page=1 to find total."""
        try:
            result = subprocess.run([
                "gh", "api", f"repos/{self.repo}/pulls/{self.pr_number}/comments?per_page=1",
                "--include"
            ], capture_output=True, text=True, check=True)
            
            # Parse Link header for pagination
            for line in result.stderr.split('\n'):
                if line.lower().startswith('link:'):
                    if 'rel="last"' in line:
                        # Extract page number from Link header
                        import re
                        match = re.search(r'page=(\d+)>; rel="last"', line)
                        if match:
                            return int(match.group(1))
            return 1
        except (subprocess.CalledProcessError, ValueError):
            return 1
    
    def fetch_inline_comments_rest_api(self) -> List[Comment]:
        """Fetch ALL inline review comments using REST API with safe pagination (max 1000 pages)."""
        print("  📝 Fetching inline review comments via REST API...", file=sys.stderr)
        
        # Fetch ALL comments with safe pagination
        all_comments = []
        page = 1
        per_page = 100  # Max per page
        max_pages = 1000  # Safety limit
        
        while page <= max_pages:
            page_comments = self._run_gh_command([
                "gh", "api", f"repos/{self.repo}/pulls/{self.pr_number}/comments?page={page}&per_page={per_page}"
            ])
            
            if not page_comments:
                break
                
            all_comments.extend(page_comments)
            
            # If we got less than per_page, we're done
            if len(page_comments) < per_page:
                break
                
            page += 1
            
        if page > max_pages:
            print(f"    ⚠️ Hit pagination limit of {max_pages} pages", file=sys.stderr)
        
        # Sort by creation date descending (newest first)
        all_comments.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        merged_comments = all_comments
        
        # Convert to Comment objects, filtering for bots and specific users
        comments = []
        for comment in merged_comments:
            user = comment.get('user', {})
            user_login = user.get('login', '')
            user_type = user.get('type', '')
            
            # Filter: bots, specific users, or accounts with bot-like names
            if (user_type == "Bot" or 
                any(bot_name in user_login.lower() for bot_name in ['bot', 'copilot', 'coderabbit', 'ai', 'reviewer']) or
                user_login == "jleechan2015"):
                
                comments.append(Comment(
                    id=str(comment.get('id', '')),
                    body=comment.get('body', ''),
                    user=user_login,
                    comment_type='inline',
                    created_at=comment.get('created_at', ''),
                    file=comment.get('path'),
                    line=comment.get('line'),
                    position=comment.get('position')
                ))
        
        print(f"    ✅ Found {len(comments)} inline comments", file=sys.stderr)
        return comments
    
    def fetch_review_comments_graphql(self) -> List[Comment]:
        """Fetch PR review comments using GraphQL-style gh pr view command."""
        print("  📋 Fetching PR reviews via GraphQL...", file=sys.stderr)
        
        result = self._run_gh_command([
            "gh", "pr", "view", self.pr_number, "--json", "reviews"
        ])
        
        comments = []
        reviews = result.get('reviews', []) if isinstance(result, dict) else []
        
        for review in reviews:
            author = review.get('author', {})
            author_login = author.get('login', '')
            
            # Filter for bots and specific users
            if (any(bot_name in author_login.lower() for bot_name in ['bot', 'copilot', 'github-actions', 'coderabbit', 'ai', 'reviewer']) or
                author_login == "jleechan2015"):
                
                comments.append(Comment(
                    id=str(review.get('id', '')),
                    body=review.get('body', ''),
                    user=author_login,
                    comment_type='review',
                    created_at=review.get('createdAt', ''),
                    state=review.get('state')
                ))
        
        print(f"    ✅ Found {len(comments)} review comments", file=sys.stderr)
        return comments
    
    def fetch_general_comments_graphql(self) -> List[Comment]:
        """Fetch general PR comments using GraphQL-style gh pr view command."""
        print("  💬 Fetching general PR comments via GraphQL...", file=sys.stderr)
        
        result = self._run_gh_command([
            "gh", "pr", "view", self.pr_number, "--json", "comments"
        ])
        
        comments = []
        comment_list = result.get('comments', []) if isinstance(result, dict) else []
        
        for comment in comment_list:
            author = comment.get('author', {})
            author_login = author.get('login', '')
            
            # Filter for bots and specific users
            if (any(bot_name in author_login.lower() for bot_name in ['bot', 'copilot', 'github-actions', 'coderabbit', 'ai', 'reviewer']) or
                author_login == "jleechan2015"):
                
                comments.append(Comment(
                    id=str(comment.get('id', '')),
                    body=comment.get('body', ''),
                    user=author_login,
                    comment_type='general',
                    created_at=comment.get('createdAt', '')
                ))
        
        print(f"    ✅ Found {len(comments)} general comments", file=sys.stderr)
        return comments
    
    def fetch_all_comments(self) -> List[Comment]:
        """Fetch all comments with parallel processing and optimal sorting."""
        start_time = time.time()
        print(f"🔍 Fetching all GitHub comments for PR #{self.pr_number}...", file=sys.stderr)
        
        # Fetch all comment types in parallel using both REST API and GraphQL
        with ThreadPoolExecutor(max_workers=3) as executor:
            inline_future = executor.submit(self.fetch_inline_comments_rest_api)
            review_future = executor.submit(self.fetch_review_comments_graphql)
            general_future = executor.submit(self.fetch_general_comments_graphql)
            
            # Collect results
            all_comments = []
            all_comments.extend(inline_future.result())
            all_comments.extend(review_future.result())
            all_comments.extend(general_future.result())
        
        # Sort by creation date descending (most recent first)
        all_comments.sort(key=lambda x: x.created_at, reverse=True)
        
        # Remove duplicates by ID while preserving order
        seen_ids = set()
        unique_comments = []
        for comment in all_comments:
            if comment.id not in seen_ids:
                seen_ids.add(comment.id)
                unique_comments.append(comment)
        
        self.total_comments = len(unique_comments)
        self.fetch_duration = time.time() - start_time
        
        print(f"📊 Total comments found: {self.total_comments}", file=sys.stderr)
        print(f"⏱️  Fetch completed in {self.fetch_duration:.2f}s", file=sys.stderr)
        
        return unique_comments
    
    
    def to_json(self, comments: List[Comment]) -> str:
        """Convert comments to JSON format compatible with shell workflow."""
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
                comment_dict['line'] = comment.line
            if comment.position:
                comment_dict['position'] = comment.position
            if comment.state:
                comment_dict['state'] = comment.state
            
            comment_dicts.append(comment_dict)
        
        return json.dumps(comment_dicts, indent=2)


def main():
    """Standalone testing and demonstration."""
    if len(sys.argv) < 2:
        print("Usage: python3 copilot_comment_fetch.py <PR_NUMBER> [REPO] [--json]", file=sys.stderr)
        print("Example: python3 copilot_comment_fetch.py 722", file=sys.stderr)
        print("Example: python3 copilot_comment_fetch.py 722 jleechanorg/worldarchitect.ai", file=sys.stderr)
        print("Example: python3 copilot_comment_fetch.py 722 --json", file=sys.stderr)
        sys.exit(1)
    
    # Parse arguments
    args = sys.argv[1:]
    json_only = "--json" in args
    if json_only:
        args.remove("--json")
    
    pr_number = args[0]
    repo = args[1] if len(args) > 1 else None
    
    try:
        fetcher = CommentFetcher(pr_number, repo)
        all_comments = fetcher.fetch_all_comments()
        
        if json_only:
            # JSON-only output for shell script integration
            print(fetcher.to_json(all_comments))
        else:
            # Verbose output for human consumption
            top_comments = all_comments[:20]  # Show top 20 for display
            
            print("\n" + "="*60)
            print(f"🔍 TOP 20 COMMENTS FROM PR #{pr_number}")
            print("="*60)
            
            for i, comment in enumerate(top_comments, 1):
                print(f"\n📝 Comment #{i}")
                print(f"ID: {comment.id}")
                print(f"Author: {comment.user}")
                print(f"Type: {comment.comment_type}")
                print(f"Created: {comment.created_at}")
                
                # Truncate long content for display
                body = comment.body
                if len(body) > 200:
                    body = body[:200] + "..."
                print(f"Content: {body}")
                
                if comment.file:
                    print(f"File: {comment.file}:{comment.line}")
                
                print("-" * 50)
            
            print(f"\n✅ Successfully fetched and displayed top 20 comments")
            print(f"📊 Total processing time: {fetcher.fetch_duration:.2f}s")
            
            # Output JSON for shell script compatibility
            json_output = fetcher.to_json(all_comments)
            print(f"\n🔧 JSON Output for Shell Integration:")
            print(json_output)
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()