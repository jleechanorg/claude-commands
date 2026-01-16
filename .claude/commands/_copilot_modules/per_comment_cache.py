#!/usr/bin/env python3
"""
per_comment_cache.py - Per-comment cache structure for efficient incremental updates

Structure:
/tmp/{repo}/{branch}/
├── comments_index.json          # Index with metadata and list of comment IDs
├── comments/
│   ├── {comment_id}.json       # Individual comment files
│   └── ...
└── cache_metadata.json          # Existing cache metadata
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class PerCommentCache:
    """Cache manager for per-comment file structure.
    
    Benefits:
    - Incremental updates: Only write changed comments (~2KB vs 399KB)
    - Parallel access: Multiple processes can update different comments
    - Easy tracking: File timestamps show which comments are new/updated
    - Selective loading: Load only needed comments
    """
    
    def __init__(self, cache_dir: Path):
        """Initialize cache manager.
        
        Args:
            cache_dir: Base cache directory (e.g., /tmp/{repo}/{branch})
        """
        self.cache_dir = Path(cache_dir)
        self.comments_dir = self.cache_dir / "comments"
        self.index_file = self.cache_dir / "comments_index.json"
        self.comments_dir.mkdir(parents=True, exist_ok=True)
    
    def save_comment(self, comment: Dict[str, Any]) -> None:
        """Save or update a single comment.
        
        Args:
            comment: Comment dictionary with 'id' field
        """
        comment_id = str(comment.get("id"))
        if not comment_id:
            raise ValueError("Comment must have an 'id' field")
        
        comment_file = self.comments_dir / f"{comment_id}.json"
        with open(comment_file, 'w') as f:
            json.dump(comment, f, indent=2)
    
    def save_comments(self, comments: List[Dict[str, Any]], 
                     pr_number: str, fetched_at: str, ci_status: Dict[str, Any]) -> None:
        """Save all comments and update index.
        
        Args:
            comments: List of comment dictionaries
            pr_number: PR number
            fetched_at: ISO timestamp when comments were fetched
            ci_status: CI status dictionary
        """
        # Save individual comment files
        comment_ids = []
        for comment in comments:
            self.save_comment(comment)
            comment_id = str(comment.get("id"))
            if comment_id:
                comment_ids.append(comment_id)
        
        # Update index
        index = {
            "pr": pr_number,
            "fetched_at": fetched_at,
            "comment_ids": comment_ids,
            "total": len(comments),
            "ci_status": ci_status,
            "by_type": {}
        }
        
        # Count by type
        for comment in comments:
            ctype = comment.get("type", "unknown")
            index["by_type"][ctype] = index["by_type"].get(ctype, 0) + 1
        
        with open(self.index_file, 'w') as f:
            json.dump(index, f, indent=2)
    
    def load_comment(self, comment_id: str) -> Optional[Dict[str, Any]]:
        """Load a single comment by ID.
        
        Args:
            comment_id: Comment ID as string
            
        Returns:
            Comment dictionary or None if not found
        """
        comment_file = self.comments_dir / f"{comment_id}.json"
        if not comment_file.exists():
            return None
        
        try:
            with open(comment_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def load_all_comments(self) -> List[Dict[str, Any]]:
        """Load all comments from cache.
        
        Returns:
            List of comment dictionaries
        """
        if not self.index_file.exists():
            return []
        
        try:
            with open(self.index_file, 'r') as f:
                index = json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
        
        comments = []
        for comment_id in index.get("comment_ids", []):
            comment = self.load_comment(str(comment_id))
            if comment:
                comments.append(comment)
        
        return comments
    
    def load_index(self) -> Optional[Dict[str, Any]]:
        """Load the index file.
        
        Returns:
            Index dictionary or None if not found
        """
        if not self.index_file.exists():
            return None
        
        try:
            with open(self.index_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def add_or_update_comment(self, comment: Dict[str, Any]) -> None:
        """Add a new comment or update existing one.
        
        Args:
            comment: Comment dictionary with 'id' field
        """
        comment_id = str(comment.get("id"))
        if not comment_id:
            raise ValueError("Comment must have an 'id' field")
        
        # Save the comment file
        self.save_comment(comment)
        
        # Update index if it exists
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    index = json.load(f)
            except (json.JSONDecodeError, IOError):
                # If index is corrupted, create new one
                index = {
                    "pr": comment.get("pr", "unknown"),
                    "fetched_at": comment.get("created_at", ""),
                    "comment_ids": [],
                    "total": 0,
                    "by_type": {}
                }
            
            comment_ids = index.get("comment_ids", [])
            if comment_id not in comment_ids:
                comment_ids.append(comment_id)
                index["comment_ids"] = comment_ids
                index["total"] = len(comment_ids)
            
            # Update type counts
            ctype = comment.get("type", "unknown")
            index["by_type"][ctype] = index["by_type"].get(ctype, 0) + 1
            
            with open(self.index_file, 'w') as f:
                json.dump(index, f, indent=2)
    
    def get_comment_count(self) -> int:
        """Get total number of cached comments.
        
        Returns:
            Number of comments in cache
        """
        index = self.load_index()
        if index:
            return index.get("total", 0)
        return 0
    
    def has_comments(self) -> bool:
        """Check if cache has any comments.
        
        Returns:
            True if cache has comments, False otherwise
        """
        return self.get_comment_count() > 0
