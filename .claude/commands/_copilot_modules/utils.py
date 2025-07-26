#!/usr/bin/env python3
"""
utils.py - Shared utilities for modular copilot commands

Provides common functionality for:
- GitHub API operations
- Git command wrappers
- JSON schema validation
- Common error messages
"""

import json
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple


class GitHubAPI:
    """Wrapper for common GitHub API operations with caching."""

    # Simple in-memory cache with 5-minute TTL
    _cache = {}
    _cache_ttl = 300  # 5 minutes

    @classmethod
    def _get_cache_key(cls, method: str, *args) -> str:
        """Generate cache key from method and arguments."""
        return f"{method}:{':'.join(str(arg) for arg in args)}"

    @classmethod
    def _get_cached(cls, key: str) -> Optional[Dict[str, Any]]:
        """Get cached result if not expired."""
        if key in cls._cache:
            cached_time, data = cls._cache[key]
            if time.time() - cached_time < cls._cache_ttl:
                return data
        return None

    @classmethod
    def _set_cache(cls, key: str, data: Dict[str, Any]):
        """Cache result with timestamp."""
        cls._cache[key] = (time.time(), data)

    @classmethod
    def get_pr_status(cls, repo: str, pr_number: str) -> Dict[str, Any]:
        """Get PR status including CI checks with caching.

        Args:
            repo: Repository in format owner/name
            pr_number: PR number

        Returns:
            Dict with PR status information
        """
        # Check cache first
        cache_key = cls._get_cache_key('get_pr_status', repo, pr_number)
        cached = cls._get_cached(cache_key)
        if cached is not None:
            return cached

        try:
            cmd = [
                "gh", "pr", "view", pr_number,
                "--repo", repo,
                "--json", "state,mergeable,statusCheckRollup,number,title"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            cls._set_cache(cache_key, data)
            return data
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            return {'error': str(e)}

    @staticmethod
    def get_ci_checks(repo: str, pr_number: str) -> List[Dict[str, Any]]:
        """Get detailed CI check results.

        Args:
            repo: Repository in format owner/name
            pr_number: PR number

        Returns:
            List of CI check results
        """
        try:
            # First try MCP if available
            cmd = [
                "gh", "pr", "checks", pr_number,
                "--repo", repo,
                "--json", "name,status,conclusion,startedAt,completedAt,detailsUrl"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0 and result.stdout:
                return json.loads(result.stdout)

            # Fallback to status from PR view
            pr_data = GitHubAPI.get_pr_status(repo, pr_number)
            checks = pr_data.get('statusCheckRollup', [])
            return checks if isinstance(checks, list) else []

        except Exception:
            return []

    @staticmethod
    def run_graphql_query(query: str) -> Dict[str, Any]:
        """Run a GraphQL query against GitHub API.

        Args:
            query: GraphQL query string

        Returns:
            Query result dict
        """
        try:
            cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            return {'error': str(e)}


class GitCommands:
    """Wrapper for common Git operations."""

    @staticmethod
    def get_current_branch() -> str:
        """Get current branch name."""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "unknown"

    @staticmethod
    def get_merge_conflicts() -> List[str]:
        """Get list of files with merge conflicts."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=U"],
                capture_output=True, text=True, check=True
            )
            return [f.strip() for f in result.stdout.splitlines() if f.strip()]
        except subprocess.CalledProcessError:
            return []

    @staticmethod
    def check_merge_tree(pr_number: str) -> Tuple[bool, str]:
        """Check if PR would merge cleanly using git merge-tree.

        Args:
            pr_number: PR number to check

        Returns:
            Tuple of (has_conflicts, merge_tree_output)
        """
        try:
            # Get default branch
            cmd = ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            default_branch = result.stdout.strip().split('/')[-1] if result.returncode == 0 else "main"

            # Run merge-tree
            cmd = [
                "git", "merge-tree",
                f"$(git merge-base {default_branch} HEAD)",
                default_branch,
                "HEAD"
            ]
            result = subprocess.run(
                ' '.join(cmd),
                shell=True,
                capture_output=True,
                text=True
            )

            # Check for conflict markers
            has_conflicts = "<<<<<<< " in result.stdout
            return has_conflicts, result.stdout

        except Exception as e:
            return False, str(e)

    @staticmethod
    def find_conflict_markers(file_path: str) -> List[Dict[str, Any]]:
        """Find conflict markers in a file.

        Args:
            file_path: Path to file to check

        Returns:
            List of conflict marker locations
        """
        markers = []
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()

            in_conflict = False
            conflict_start = 0

            for i, line in enumerate(lines, 1):
                if line.startswith("<<<<<<<"):
                    in_conflict = True
                    conflict_start = i
                elif line.startswith(">>>>>>>") and in_conflict:
                    markers.append({
                        'file': file_path,
                        'start_line': conflict_start,
                        'end_line': i,
                        'lines': i - conflict_start + 1
                    })
                    in_conflict = False
        except Exception:
            pass

        return markers


class JSONSchemas:
    """JSON schema definitions for I/O contracts."""

    COMMENTS_SCHEMA = {
        "type": "object",
        "required": ["pr", "fetched_at", "comments", "metadata"],
        "properties": {
            "pr": {"type": "string"},
            "fetched_at": {"type": "string", "format": "date-time"},
            "comments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "type", "body", "author"],
                    "properties": {
                        "id": {"type": ["string", "number"]},
                        "type": {"enum": ["inline", "general", "review", "copilot"]},
                        "body": {"type": "string"},
                        "author": {"type": "string"},
                        "created_at": {"type": "string"},
                        "requires_response": {"type": "boolean"}
                    }
                }
            },
            "metadata": {"type": "object"}
        }
    }

    FIXES_SCHEMA = {
        "type": "object",
        "required": ["pr", "analyzed_at", "ci_status", "conflicts"],
        "properties": {
            "pr": {"type": "string"},
            "analyzed_at": {"type": "string", "format": "date-time"},
            "ci_status": {"type": "object"},
            "conflicts": {"type": "object"},
            "fixes_applied": {"type": "array"},
            "metadata": {"type": "object"}
        }
    }

    @staticmethod
    def validate(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Basic JSON schema validation.

        Args:
            data: Data to validate
            schema: Schema to validate against

        Returns:
            Tuple of (is_valid, error_message)
        """
        # This is a simplified validator - in production use jsonschema library
        try:
            required = schema.get('required', [])
            for field in required:
                if field not in data:
                    return False, f"Missing required field: {field}"
            return True, None
        except Exception as e:
            return False, str(e)


class ErrorMessages:
    """Standard error messages for consistent UX."""

    PR_NOT_FOUND = "❌ PR #{pr} not found or inaccessible"
    CI_TIMEOUT = "⏱️ CI check timed out after {seconds} seconds"
    NO_CONFLICTS = "✅ No merge conflicts detected"
    API_ERROR = "🚫 GitHub API error: {error}"
    FILE_NOT_FOUND = "📄 File not found: {file}"
    JSON_INVALID = "🔧 Invalid JSON in {file}: {error}"

    @classmethod
    def format(cls, template: str, **kwargs) -> str:
        """Format error message with parameters."""
        return template.format(**kwargs)
