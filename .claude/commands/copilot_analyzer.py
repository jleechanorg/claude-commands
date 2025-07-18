#!/usr/bin/env python3
"""
Copilot Analyzer Module - Comment parsing and categorization for GitHub PRs

This module extracts and categorizes GitHub PR comments to determine what can be
automatically implemented vs what needs manual attention.
"""

import re
import json
import subprocess
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommentType(Enum):
    """Types of comments we can encounter"""
    INLINE = "inline"
    REVIEW = "review"
    GENERAL = "general"
    CI_FAILURE = "ci_failure"

class Priority(Enum):
    """Priority levels for suggestions"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Implementability(Enum):
    """How implementable a suggestion is"""
    AUTO_FIXABLE = "auto_fixable"  # Can be automatically implemented
    MANUAL = "manual"              # Requires manual implementation
    NOT_APPLICABLE = "not_applicable"  # Not applicable/subjective

@dataclass
class Comment:
    """Represents a GitHub PR comment"""
    id: str
    body: str
    user: str
    comment_type: CommentType
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    priority: Priority = Priority.MEDIUM
    implementability: Implementability = Implementability.MANUAL
    suggested_actions: List[str] = None
    
    def __post_init__(self):
        if self.suggested_actions is None:
            self.suggested_actions = []

@dataclass
class AnalysisResult:
    """Results of comment analysis"""
    comments: List[Comment]
    auto_fixable_count: int
    manual_count: int
    not_applicable_count: int
    total_count: int
    ci_failures: List[Dict[str, Any]]

class CopilotAnalyzer:
    """Main analyzer class for GitHub PR comments"""
    
    # Patterns for auto-fixable issues
    AUTO_FIXABLE_PATTERNS = {
        'unused_imports': [
            r'unused import',
            r'imported but unused',
            r'remove unused import',
            r'import.*not used',
        ],
        'magic_numbers': [
            r'magic number',
            r'hardcoded.*number',
            r'extract.*constant',
            r'define.*constant',
        ],
        'formatting': [
            r'formatting',
            r'indentation',
            r'whitespace',
            r'line length',
            r'code style',
        ],
        'simple_refactoring': [
            r'extract.*method',
            r'rename.*variable',
            r'duplicate.*code',
            r'simplify.*expression',
        ]
    }
    
    # Patterns for manual review needed
    MANUAL_PATTERNS = [
        r'logic.*error',
        r'business.*logic',
        r'algorithm.*improvement',
        r'architectural.*change',
        r'design.*pattern',
        r'security.*concern',
        r'performance.*bottleneck',
    ]
    
    # Patterns for not applicable
    NOT_APPLICABLE_PATTERNS = [
        r'personal.*preference',
        r'style.*choice',
        r'opinion',
        r'subjective',
        r'consider.*using',
        r'might.*want',
        r'could.*be',
    ]
    
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
    
    def _detect_pr_number(self) -> Optional[str]:
        """Detect PR number for current branch"""
        try:
            # Get current branch
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True,
                text=True,
                check=True
            )
            current_branch = result.stdout.strip()
            
            # Get PR info for current branch
            result = subprocess.run(
                ['gh', 'pr', 'list', '--head', current_branch, '--json', 'number', '--limit', '1'],
                capture_output=True,
                text=True,
                check=True
            )
            
            data = json.loads(result.stdout)
            if data and len(data) > 0:
                return str(data[0]['number'])
            return None
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to detect PR number: {e}")
            return None
    
    def extract_pr_comments(self, pr_number: str) -> List[Comment]:
        """Extract all comments from a PR"""
        comments = []
        
        # Extract inline review comments
        comments.extend(self._extract_inline_comments(pr_number))
        
        # Extract general PR comments
        comments.extend(self._extract_general_comments(pr_number))
        
        # Extract review comments
        comments.extend(self._extract_review_comments(pr_number))
        
        logger.info(f"Extracted {len(comments)} comments from PR #{pr_number}")
        return comments
    
    def _extract_inline_comments(self, pr_number: str) -> List[Comment]:
        """Extract inline review comments"""
        try:
            result = subprocess.run(
                ['gh', 'api', f'repos/{self.repo_info}/pulls/{pr_number}/comments'],
                capture_output=True,
                text=True,
                check=True
            )
            
            data = json.loads(result.stdout)
            comments = []
            
            for comment_data in data:
                # Filter for bot comments and user feedback
                user = comment_data.get('user', {}).get('login', '')
                user_type = comment_data.get('user', {}).get('type', '')
                
                if (user_type == 'Bot' or 
                    any(bot_name in user.lower() for bot_name in ['bot', 'copilot', 'coderabbit']) or
                    user == 'jleechan2015'):  # Include user feedback
                    
                    comment = Comment(
                        id=str(comment_data['id']),
                        body=comment_data['body'],
                        user=user,
                        comment_type=CommentType.INLINE,
                        file_path=comment_data.get('path'),
                        line_number=comment_data.get('line')
                    )
                    comments.append(comment)
            
            return comments
            
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error(f"Failed to extract inline comments: {e}")
            return []
    
    def _extract_general_comments(self, pr_number: str) -> List[Comment]:
        """Extract general PR comments"""
        try:
            result = subprocess.run(
                ['gh', 'pr', 'view', pr_number, '--json', 'comments'],
                capture_output=True,
                text=True,
                check=True
            )
            
            data = json.loads(result.stdout)
            comments = []
            
            for comment_data in data.get('comments', []):
                # Filter for bot comments and user feedback
                user = comment_data.get('author', {}).get('login', '')
                
                if (any(bot_name in user.lower() for bot_name in ['bot', 'copilot', 'github-actions', 'coderabbit']) or
                    user == 'jleechan2015'):  # Include user feedback
                    
                    comment = Comment(
                        id=str(comment_data['id']),
                        body=comment_data['body'],
                        user=user,
                        comment_type=CommentType.GENERAL
                    )
                    comments.append(comment)
            
            return comments
            
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error(f"Failed to extract general comments: {e}")
            return []
    
    def _extract_review_comments(self, pr_number: str) -> List[Comment]:
        """Extract PR review comments"""
        try:
            result = subprocess.run(
                ['gh', 'pr', 'view', pr_number, '--json', 'reviews'],
                capture_output=True,
                text=True,
                check=True
            )
            
            data = json.loads(result.stdout)
            comments = []
            
            for review_data in data.get('reviews', []):
                # Filter for bot reviews and user feedback
                author = review_data.get('author', {})
                if not author:
                    continue
                    
                user = author.get('login', '')
                
                if (any(bot_name in user.lower() for bot_name in ['bot', 'copilot', 'github-actions', 'coderabbit']) or
                    user == 'jleechan2015'):  # Include user feedback
                    
                    comment = Comment(
                        id=str(review_data['id']),
                        body=review_data.get('body', ''),
                        user=user,
                        comment_type=CommentType.REVIEW
                    )
                    comments.append(comment)
            
            return comments
            
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error(f"Failed to extract review comments: {e}")
            return []
    
    def extract_ci_failures(self, pr_number: str) -> List[Dict[str, Any]]:
        """Extract CI failure information"""
        try:
            result = subprocess.run(
                ['gh', 'pr', 'view', pr_number, '--json', 'statusCheckRollup'],
                capture_output=True,
                text=True,
                check=True
            )
            
            data = json.loads(result.stdout)
            failures = []
            
            for check in data.get('statusCheckRollup', []):
                if check.get('conclusion') in ['FAILURE', 'CANCELLED']:
                    failures.append({
                        'name': check.get('name', check.get('checkName', 'Unknown')),
                        'conclusion': check.get('conclusion'),
                        'details_url': check.get('detailsUrl'),
                        'context': check.get('context')
                    })
            
            logger.info(f"Found {len(failures)} CI failures")
            return failures
            
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error(f"Failed to extract CI failures: {e}")
            return []
    
    def categorize_comment(self, comment: Comment) -> Comment:
        """Categorize a comment by implementability and priority"""
        body_lower = comment.body.lower()
        
        # Check for auto-fixable patterns
        for category, patterns in self.AUTO_FIXABLE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, body_lower):
                    comment.implementability = Implementability.AUTO_FIXABLE
                    comment.priority = Priority.HIGH
                    comment.suggested_actions.append(f"auto_fix_{category}")
                    return comment
        
        # Check for manual patterns
        for pattern in self.MANUAL_PATTERNS:
            if re.search(pattern, body_lower):
                comment.implementability = Implementability.MANUAL
                comment.priority = Priority.HIGH
                return comment
        
        # Check for not applicable patterns
        for pattern in self.NOT_APPLICABLE_PATTERNS:
            if re.search(pattern, body_lower):
                comment.implementability = Implementability.NOT_APPLICABLE
                comment.priority = Priority.LOW
                return comment
        
        # Default to manual if no pattern matches
        comment.implementability = Implementability.MANUAL
        comment.priority = Priority.MEDIUM
        return comment
    
    def analyze_pr(self, pr_number: Optional[str] = None) -> AnalysisResult:
        """Analyze a PR and return categorized results"""
        if pr_number is None:
            pr_number = self._detect_pr_number()
            if pr_number is None:
                raise ValueError("No PR number provided and could not detect from current branch")
        
        logger.info(f"Analyzing PR #{pr_number}")
        
        # Extract comments
        comments = self.extract_pr_comments(pr_number)
        
        # Categorize each comment
        categorized_comments = []
        for comment in comments:
            categorized_comment = self.categorize_comment(comment)
            categorized_comments.append(categorized_comment)
        
        # Extract CI failures
        ci_failures = self.extract_ci_failures(pr_number)
        
        # Count categories
        auto_fixable_count = sum(1 for c in categorized_comments if c.implementability == Implementability.AUTO_FIXABLE)
        manual_count = sum(1 for c in categorized_comments if c.implementability == Implementability.MANUAL)
        not_applicable_count = sum(1 for c in categorized_comments if c.implementability == Implementability.NOT_APPLICABLE)
        
        result = AnalysisResult(
            comments=categorized_comments,
            auto_fixable_count=auto_fixable_count,
            manual_count=manual_count,
            not_applicable_count=not_applicable_count,
            total_count=len(categorized_comments),
            ci_failures=ci_failures
        )
        
        logger.info(f"Analysis complete: {auto_fixable_count} auto-fixable, {manual_count} manual, {not_applicable_count} not applicable")
        return result

def main():
    """Main function for standalone testing"""
    import sys
    
    analyzer = CopilotAnalyzer()
    
    pr_number = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        result = analyzer.analyze_pr(pr_number)
        
        print(f"PR Analysis Results:")
        print(f"  Total comments: {result.total_count}")
        print(f"  Auto-fixable: {result.auto_fixable_count}")
        print(f"  Manual: {result.manual_count}")
        print(f"  Not applicable: {result.not_applicable_count}")
        print(f"  CI failures: {len(result.ci_failures)}")
        
        print("\nAuto-fixable comments:")
        for comment in result.comments:
            if comment.implementability == Implementability.AUTO_FIXABLE:
                print(f"  - {comment.body[:100]}... (Actions: {comment.suggested_actions})")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()