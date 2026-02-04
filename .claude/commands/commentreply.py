#!/usr/bin/env python3
"""
/commentreply Command Implementation

Systematically processes ALL PR comments with proper GitHub API threading.
Prevents the bug pattern where individual comments are missed while claiming 100% coverage.

This is the ACTUAL IMPLEMENTATION that was missing - the .md file had extensive
documentation but no working code to execute the systematic processing.
"""

import json
import subprocess
import sys
import os
import tempfile
import html
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple




def run_command(
    cmd: List[str],
    description: str = "",
    timeout: int = 60,
    input_text: Optional[str] = None,
) -> Tuple[bool, str, str]:
    """Execute shell command safely with error handling"""
    try:
        result = subprocess.run(
            cmd,
            input=input_text,
            capture_output=True,
            text=True,
            check=False,  # Don't raise on non-zero exit
            timeout=timeout,
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"[timeout] {description or 'cmd'}: {' '.join(cmd)}"
    except Exception as e:
        return False, "", f"[failure] {description or 'cmd'}: {e}"


def parse_arguments() -> Tuple[str, str, str]:
    """Parse command line arguments for owner, repo, and PR number"""
    if len(sys.argv) != 4:
        print("❌ ERROR: Missing required arguments")
        print("Usage: python3 commentreply.py <owner> <repo> <pr_number>")
        print("Example: python3 commentreply.py jleechanorg your-project.com 1510")
        sys.exit(1)

    return sys.argv[1], sys.argv[2], sys.argv[3]


def sanitize_branch_name(branch: str) -> str:
    """Sanitize branch name to match shell's tr -cd '[:alnum:]._-'.

    Removes any character that is NOT alphanumeric, dot, underscore, or dash.
    """
    return re.sub(r"[^a-zA-Z0-9._-]", "", branch or "")


def sanitize_repo_name(repo_name: str) -> str:
    """Sanitize repo name for filesystem safety.

    Uses the same allowlist as branch sanitization so cache paths cannot be
    influenced by path separators or traversal sequences.
    """
    return re.sub(r"[^a-zA-Z0-9._-]", "", repo_name or "")


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def get_current_branch() -> str:
    """Get current git branch name for temp file path"""
    success, branch, _ = run_command(["git", "branch", "--show-current"])
    if success and branch.strip():
        return sanitize_branch_name(branch.strip()) or "unknown-branch"
    return "unknown-branch"


def get_repo_name(fallback_repo: str) -> str:
    """Get repo name from git root to match shell scripts, with fallback."""
    success, git_root, _ = run_command(["git", "rev-parse", "--show-toplevel"])
    if success and git_root.strip():
        candidate = os.path.basename(git_root.strip())
    else:
        candidate = fallback_repo

    sanitized = sanitize_repo_name(candidate)
    return sanitized or "unknown-repo"


def load_claude_responses(branch_name: str, repo_name: str) -> Dict:
    """
    Load Claude-generated responses from JSON file.
    In the modern workflow, Claude analyzes comments, implements fixes,
    generates responses, and saves them to responses.json for Python to post.

    Args:
        branch_name: Current git branch name (sanitized)
        repo_name: Repository name (sanitized)

    Returns:
        Dictionary containing responses data, empty dict if file not found
    """
    safe_repo = sanitize_repo_name(repo_name) or "unknown-repo"
    safe_branch = sanitize_branch_name(branch_name) or "unknown-branch"

    base_dir = Path("/tmp").resolve()
    responses_path = (base_dir / safe_repo / safe_branch / "responses.json").resolve()
    expected_dir = (base_dir / safe_repo / safe_branch).resolve()

    # Verify the resolved path stays within /tmp (symlink-safe) and matches expected dir
    if (
        not _is_relative_to(responses_path, base_dir)
        or not _is_relative_to(expected_dir, base_dir)
        or responses_path.parent != expected_dir
    ):
        print(f"⚠️ SECURITY: Path traversal/symlink escape blocked: {responses_path}")
        return {}

    if not responses_path.exists():
        print(f"⚠️  RESPONSES FILE NOT FOUND: {responses_path}")
        print("⚠️  Claude should have generated responses.json after analyzing comments")
        return {}

    try:
        # Additional security: check file size before reading
        if responses_path.exists():
            file_size = responses_path.stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                print(
                    f"⚠️ SECURITY: File too large: {responses_path} ({file_size} bytes)"
                )
                return {}

        with responses_path.open("r") as f:
            responses_data = json.load(f)
        print(
            f"📁 LOADED: {len(responses_data.get('responses', []))} responses from {responses_path}"
        )
        return responses_data
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Failed to parse responses JSON: {e}")
        return {}
    except Exception as e:
        print(f"❌ ERROR: Failed to load responses file: {e}")
        return {}


def load_comments_with_staleness_check(
    branch_name: str, owner: str, repo: str, pr_number: str, repo_name: str
) -> List[Dict]:
    """
    Load comment data with staleness detection and real-time fallback.
        repo: Repository name
        pr_number: PR number
        repo_name: Repository name (sanitized)

    Returns:
        List of comment dictionaries (fresh or cached)
    """
    safe_repo = sanitize_repo_name(repo_name) or "unknown-repo"
    safe_branch = sanitize_branch_name(branch_name) or "unknown-branch"

    base_dir = Path("/tmp").resolve()
    cache_dir = (base_dir / safe_repo / safe_branch).resolve()
    comments_path = (cache_dir / "comments.json").resolve()

    # Security check
    if not _is_relative_to(cache_dir, base_dir) or not _is_relative_to(
        comments_path, base_dir
    ):
        print(f"⚠️ SECURITY: Path traversal/symlink escape blocked: {cache_dir}")
        sys.exit(1)

    # Fallback to legacy single-file format
    comments_file = str(comments_path)

    # COPILOT: Always fetch fresh data - no cache for PR processing
    if comments_path.exists():
        cache_age_minutes = (time.time() - os.path.getmtime(comments_file)) / 60
        print(
            f"🔄 COPILOT MODE: Ignoring {cache_age_minutes:.1f}min cache - fetching fresh comments"
        )
        fetch_fresh_comments(owner, repo, pr_number, comments_file)
    else:
        print(f"📥 NO CACHE: Fetching fresh comments for {owner}/{repo}#{pr_number}")
        fetch_fresh_comments(owner, repo, pr_number, comments_file)

    try:
        with comments_path.open("r") as f:
            comment_data = json.load(f)
        return comment_data.get("comments", [])
    except Exception as e:
        print(f"❌ ERROR: Failed to load comments: {e}")
        sys.exit(1)


def fetch_fresh_comments(owner: str, repo: str, pr_number: str, output_file: str):
    """Fetch fresh comments using GitHub API and save to cache file"""

    # Fetch both review comments and issue comments
    inline_cmd = [
        "gh",
        "api",
        f"repos/{owner}/{repo}/pulls/{pr_number}/comments",
        "--paginate",
        "-q",
        ".[]",
    ]
    issue_cmd = [
        "gh",
        "api",
        f"repos/{owner}/{repo}/issues/{pr_number}/comments",
        "--paginate",
        "-q",
        ".[]",
    ]
    review_body_cmd = [
        "gh",
        "api",
        f"repos/{owner}/{repo}/pulls/{pr_number}/reviews",
        "--paginate",
        "-q",
        ".[]",
    ]

    print("📡 FETCHING: Fresh comment data from GitHub API...")

    success_inline, inline_data, _ = run_command(
        inline_cmd, "fetch inline review comments", timeout=120
    )
    success_issue, issue_data, _ = run_command(
        issue_cmd, "fetch issue comments", timeout=120
    )
    success_review_bodies, review_body_data, _ = run_command(
        review_body_cmd, "fetch review bodies", timeout=120
    )

    # Require inline and issue comments (core functionality)
    # Review bodies are optional - gracefully degrade if endpoint fails
    if not (success_inline and success_issue):
        print("❌ ERROR: Failed to fetch core comments (inline/issue) from GitHub API")
        if not os.path.exists(output_file):
            sys.exit(1)
        print("⚠️  Falling back to stale cache...")
        return

    if not success_review_bodies:
        print(
            "⚠️  WARNING: Review bodies fetch failed (permissions/rate-limit?) - continuing without review bodies"
        )
        review_body_data = ""  # Empty, will result in empty list

    # Parse and combine comments
    try:
        inline_comments = [
            json.loads(line)
            for line in (inline_data or "").splitlines()
            if line.strip()
        ]
        issue_comments = [
            json.loads(line) for line in (issue_data or "").splitlines() if line.strip()
        ]
        # Filter out reviews with empty bodies (e.g., approval reviews without comments)
        raw_reviews = [
            json.loads(line)
            for line in (review_body_data or "").splitlines()
            if line.strip()
        ]
        review_body_comments = [r for r in raw_reviews if r.get("body", "").strip()]

        # Add type information and combine
        for comment in inline_comments:
            comment["type"] = "inline"
        for comment in issue_comments:
            comment["type"] = "issue"
        for review in review_body_comments:
            review["type"] = "review"

        all_comments = inline_comments + issue_comments + review_body_comments

        # Save to cache file
        cache_data = {
            "pr": pr_number,
            "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "comments": all_comments,
        }

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(cache_data, f, indent=2)

        print(f"✅ CACHED: {len(all_comments)} comments saved to {output_file}")

    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Failed to parse fresh comment data: {e}")
        sys.exit(1)


def validate_comment_data(comment: Dict) -> bool:
    """Validate comment data structure and content for security.

    Args:
        comment: Comment data dictionary

    Returns:
        True if comment data is valid and safe
    """
    if not isinstance(comment, dict):
        return False

    # Required fields (user field no longer required due to author field support)
    required_fields = ["id", "body"]
    for field in required_fields:
        if field not in comment:
            return False

    # Validate comment ID (must be numeric)
    comment_id = comment.get("id")
    if not isinstance(comment_id, (int, str)) or not str(comment_id).isdigit():
        return False

    # Validate user structure (support both user.login and author formats)
    user = comment.get("user")
    author = comment.get("author")

    # Accept either user.login structure or direct author field
    has_valid_user = isinstance(user, dict) and "login" in user
    has_valid_author = isinstance(author, str) and author.strip()

    if not (has_valid_user or has_valid_author):
        # Normalize missing author metadata to "unknown" for backward compatibility.
        comment["author"] = "unknown"

    # Validate body content
    body = comment.get("body")
    if not isinstance(body, str):
        return False

    # Check for potentially dangerous content patterns
    dangerous_patterns = [
        r"<script[^>]*>.*?</script>",  # Script tags
        r"javascript:",  # JavaScript URLs
        r"data:text/html",  # Data URLs
        r"vbscript:",  # VBScript
        r"<[^>]+\son\w+\s*=",  # Inline event handlers in HTML tags
    ]

    # Allow known bot content that includes HTML/event-handler examples.
    author_login = ""
    user_type = ""
    if isinstance(user, dict):
        if user.get("login"):
            author_login = str(user.get("login"))
        if user.get("type"):
            user_type = str(user.get("type"))
    elif isinstance(author, str):
        author_login = author

    is_bot_author = False
    if user_type.lower() == "bot":
        is_bot_author = True
    elif author_login.lower().endswith("[bot]"):
        is_bot_author = True

    def strip_code_blocks(text: str) -> str:
        # Remove fenced code blocks and inline code to avoid false positives on examples.
        without_fences = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        return re.sub(r"`[^`]*`", "", without_fences, flags=re.DOTALL)

    for pattern in dangerous_patterns:
        if re.search(pattern, body, re.IGNORECASE | re.DOTALL):
            print(
                f"⚠️ SECURITY: Potentially dangerous content detected in comment #{comment_id}"
            )
            if is_bot_author:
                scrubbed_body = strip_code_blocks(body)
                if not re.search(pattern, scrubbed_body, re.IGNORECASE | re.DOTALL):
                    print(
                        "⚠️ SECURITY: Allowing bot-authored code example content for response processing"
                    )
                    return True
            return False

    return True


def sanitize_comment_content(content: str) -> str:
    """Sanitize comment content for safe processing.

    Args:
        content: Raw comment content

    Returns:
        Sanitized content safe for processing
    """
    if not isinstance(content, str):
        return str(content)

    # HTML escape potentially dangerous characters
    sanitized = html.escape(content)

    # Limit length to prevent DoS
    if len(sanitized) > 10000:  # 10KB limit
        sanitized = sanitized[:10000] + "... [truncated]"

    return sanitized


def get_response_for_comment(
    comment: Dict,
    responses_data: Dict,
    commit_hash: str,
    parent_comment: Optional[Dict] = None,
) -> str:
    """
    Get Claude-generated response for a specific comment.

    Args:
        comment: Comment data from GitHub API
        responses_data: Loaded responses from Claude
        commit_hash: Current commit hash as fallback
        parent_comment: Optional parent comment data for context (when processing replies)
    Returns:
        Claude-generated response text or placeholder if not found
    """
    # SECURITY: Validate comment data first
    if not validate_comment_data(comment):
        print("⚠️ SECURITY: Invalid comment data structure, skipping")
        return ""

    comment_id = str(comment.get("id"))

    # Look for Claude-generated response
    responses = responses_data.get("responses", [])
    for response_item in responses:
        if str(response_item.get("comment_id")) == comment_id:
            # Backward compatibility: support both 'reply_text' and legacy 'response' keys
            return response_item.get("reply_text") or response_item.get("response", "")

    # CRITICAL FIX: Never post placeholder comments - return empty string to skip posting
    print(
        f"⚠️ SKIP: No Claude response found for comment #{comment_id} - will not post placeholder"
    )
    return ""


def get_git_commit_hash() -> str:
    """Get current git commit hash"""
    success, commit_hash, _ = run_command(["git", "rev-parse", "--short", "HEAD"])
    return commit_hash.strip() if success else "unknown"





def detect_comment_type(comment: Dict) -> str:
    """Detect comment kind: inline (code), review (review body), or issue"""
    html_url = comment.get("html_url") or ""
    if (
        "#discussion_r" in html_url
        or comment.get("path")
        or comment.get("position")
        or comment.get("diff_hunk")
    ):
        return "inline"
    if "#pullrequestreview-" in html_url or comment.get("pull_request_review_id"):
        return "review"
    if "#issuecomment-" in html_url:
        return "issue"
    return "inline"


def post_consolidated_summary(
    owner: str,
    repo: str,
    pr_number: str,
    collected_replies: List[Dict],
    responses_data: Dict,
    commit_hash: str,
    total_targets: int,
    already_replied_count: int,
) -> bool:
    """Post ONE consolidated summary comment with all replies embedded.

    Instead of posting individual threaded replies, this posts a single comment
    containing all responses organized by comment, making it easier to review
    and reducing notification spam.

    Args:
        owner: Repository owner
        repo: Repository name
        pr_number: PR number
        collected_replies: List of dicts with comment_id, author, body_snippet, response_text
        responses_data: Loaded responses.json data with ACTION_ACCOUNTABILITY format
        commit_hash: Current commit hash
        total_targets: Total number of target comments
        already_replied_count: Number of comments already replied to

    Returns:
        True if summary was posted successfully
    """
    print(f"📝 POSTING: Consolidated summary comment to PR #{pr_number}")

    responses = responses_data.get("responses", [])

    # Helper function to get all issues from a response (handles both single and multi-issue formats)
    def get_all_issues(response):
        """Extract all issues from response, handling both single-issue and multi-issue formats."""
        if "issues" in response and "analysis" in response:
            # Multi-issue format: return list of issues
            return response.get("issues", [])
        else:
            # Single-issue format: treat entire response as one issue
            return [response]

    # Count by category (aggregate across all issues in all responses)
    critical_count = sum(
        1
        for r in responses
        for issue in get_all_issues(r)
        if issue.get("category") == "CRITICAL"
    )
    blocking_count = sum(
        1
        for r in responses
        for issue in get_all_issues(r)
        if issue.get("category") == "BLOCKING"
    )
    important_count = sum(
        1
        for r in responses
        for issue in get_all_issues(r)
        if issue.get("category") == "IMPORTANT"
    )
    routine_count = sum(
        1
        for r in responses
        for issue in get_all_issues(r)
        if issue.get("category") == "ROUTINE"
    )

    # Count by response type (aggregate across all issues in all responses)
    fixed_count = sum(
        1
        for r in responses
        for issue in get_all_issues(r)
        if issue.get("response") == "FIXED"
    )
    deferred_count = sum(
        1
        for r in responses
        for issue in get_all_issues(r)
        if issue.get("response") == "DEFERRED"
    )
    acknowledged_count = sum(
        1
        for r in responses
        for issue in get_all_issues(r)
        if issue.get("response") == "ACKNOWLEDGED"
    )
    not_done_count = sum(
        1
        for r in responses
        for issue in get_all_issues(r)
        if issue.get("response") == "NOT_DONE"
    )

    # Count multi-issue responses and total issues
    multi_issue_count = sum(1 for r in responses if "issues" in r and "analysis" in r)
    total_issues = sum(len(get_all_issues(r)) for r in responses)

    # Build category breakdown
    category_breakdown = []
    if critical_count > 0:
        category_breakdown.append(f"  - 🚨 **Critical**: {critical_count} issue(s)")
    if blocking_count > 0:
        category_breakdown.append(f"  - ⛔ **Blocking**: {blocking_count} issue(s)")
    if important_count > 0:
        category_breakdown.append(f"  - ⚠️  **Important**: {important_count} issue(s)")
    if routine_count > 0:
        category_breakdown.append(f"  - 📝 **Routine**: {routine_count} issue(s)")

    # Build response type breakdown
    response_breakdown = []
    if fixed_count > 0:
        response_breakdown.append(
            f"  - ✅ **FIXED**: {fixed_count} issue(s) implemented with working code"
        )
    if deferred_count > 0:
        response_breakdown.append(
            f"  - 🔄 **DEFERRED**: {deferred_count} issue(s) - created issues for future implementation"
        )
    if acknowledged_count > 0:
        response_breakdown.append(
            f"  - 📋 **ACKNOWLEDGED**: {acknowledged_count} issue(s) - noted but not actionable"
        )
    if not_done_count > 0:
        response_breakdown.append(
            f"  - ❌ **NOT DONE**: {not_done_count} issue(s) - cannot implement with specific reason"
        )

    # Build consolidated replies section
    replies_section_parts = []
    for idx, reply_data in enumerate(collected_replies, 1):
        comment_id = reply_data.get("comment_id")
        author = reply_data.get("author", "unknown")
        body_snippet = reply_data.get("body_snippet", "")
        response_text = reply_data.get("response_text", "")
        comment_type = reply_data.get("comment_type", "inline")

        # Determine correct anchor based on comment type
        if comment_type == "review":
            anchor = f"pullrequestreview-{comment_id}"
        elif comment_type in ("inline", "copilot"):
            anchor = f"discussion_r{comment_id}"
        else:
            anchor = f"issuecomment-{comment_id}"

        comment_link = f"https://github.com/{owner}/{repo}/pull/{pr_number}#{anchor}"

        reply_entry = f"""
---

### {idx}. Re: [Comment #{comment_id}]({comment_link}) by @{author}

> {body_snippet}...

{response_text}
"""
        replies_section_parts.append(reply_entry)

    max_comment_size = 65000
    part_placeholder = "\n**Summary Part 1 of 10**"

    def build_summary_body(replies_text: str, part_line: str) -> str:
        replies_section = (
            replies_text
            if replies_text.strip()
            else "\n*No new replies needed - all comments already addressed.*\n"
        )
        return f"""## 🤖 [AI responder] Consolidated Comment Response Summary{part_line}

**Processing Overview**:
- 📊 **Total Comments**: {total_targets} comment(s) analyzed
- ✅ **New Responses**: {len(collected_replies)} response(s) in this summary
- 🔄 **Already Replied**: {already_replied_count} comment(s) previously addressed
- 📈 **Total Issues**: {total_issues} distinct issue(s) identified
- 🔀 **Multi-Issue Comments**: {multi_issue_count} comment(s) contain multiple issues
- 📝 **Commit**: {commit_hash}

**Category Breakdown**:
{chr(10).join(category_breakdown) if category_breakdown else "  - No categorized responses"}

**Response Type Breakdown**:
{chr(10).join(response_breakdown) if response_breakdown else "  - No responses"}

---

**Follow-up Reviews Requested**:
- @coderabbitai
- @copilot
- @cursor
- @chatgpt-codex-connector

Please re-review this PR and confirm whether all prior issues are resolved.

---

## 📋 Individual Responses
{replies_section}

---

**LLM Architecture**: Following CLAUDE.md principles - LLM analyzed FULL comment content, identified ALL distinct issues (even when multiple issues in one comment), and generated comprehensive responses with ACTION_ACCOUNTABILITY format.

**Anti-Spam Design**: Consolidated into single comment to reduce notification noise while maintaining 100% coverage.

*Generated by /commentreply - Systematic comment processing with consolidated response format*"""

    def split_reply_entries(entries: List[str]) -> List[str]:
        chunks: List[List[str]] = []
        current_chunk: List[str] = []
        base_size = len(build_summary_body("", part_placeholder))
        max_replies_size = max_comment_size - base_size - 200
        for entry in entries:
            candidate = current_chunk + [entry]
            candidate_text = "\n".join(candidate)
            if len(build_summary_body(candidate_text, part_placeholder)) <= max_comment_size:
                current_chunk = candidate
                continue
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                candidate = [entry]
            entry_text = candidate[0]
            if len(build_summary_body(entry_text, part_placeholder)) > max_comment_size:
                truncated = entry_text[:max_replies_size].rstrip()
                entry_text = (
                    truncated
                    + "\n\n... [TRUNCATED TO FIT GITHUB COMMENT LIMIT]"
                )
            current_chunk = [entry_text]
        if current_chunk:
            chunks.append(current_chunk)
        return ["\n".join(chunk) for chunk in chunks]

    reply_chunks = split_reply_entries(replies_section_parts)
    total_parts = len(reply_chunks) if reply_chunks else 1
    bodies_to_post = []
    for idx, replies_text in enumerate(reply_chunks or [""], 1):
        part_line = (
            f"\n**Summary Part {idx} of {total_parts}**"
            if total_parts > 1
            else ""
        )
        bodies_to_post.append(build_summary_body(replies_text, part_line))

    for idx, summary_body in enumerate(bodies_to_post, 1):
        if total_parts > 1:
            print(f"🧩 POSTING: Summary part {idx}/{total_parts}")

        summary_data = {"body": summary_body}
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as temp_file:
                json.dump(summary_data, temp_file)
                temp_file_path = temp_file.name

            success, response_json, stderr = run_command(
                [
                    "gh",
                    "api",
                    f"repos/{owner}/{repo}/issues/{pr_number}/comments",
                    "--method",
                    "POST",
                    "--header",
                    "Content-Type: application/json",
                    "--input",
                    temp_file_path,
                ]
            )

        except Exception as e:
            print(f"❌ ERROR: Failed to create secure summary JSON: {e}")
            return False
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

        if success:
            try:
                response_data = json.loads(response_json)
                summary_url = response_data.get("html_url")
                print("✅ SUCCESS: Consolidated summary comment posted")
                print(f"🔗 SUMMARY URL: {summary_url}")
            except json.JSONDecodeError:
                print("⚠️ WARNING: Summary posted but couldn't parse response")
        else:
            print("❌ ERROR: Failed to post consolidated summary comment")
            print(f"   Error: {stderr}")
            return False

    return True


def main():
    """Main execution function"""
    print("🚀 STARTING: /commentreply systematic comment processing")
    print(
        "🎯 PURPOSE: Process ALL PR comments with proper threading to prevent missed comment bugs"
    )

    # Step 1: Parse command line arguments (passed from commentreply.md)
    owner, repo, pr_number = parse_arguments()
    print(f"📋 REPOSITORY: {owner}/{repo}")
    print(f"📋 PR NUMBER: #{pr_number}")

    # Retry control: Track retry attempts to prevent infinite loops
    retry_count = 0
    max_retries = 2

    # Global tracking across retries
    initial_target_ids: set[str] = set()
    successful_reply_ids: set[str] = set()
    already_replied_ids: set[str] = set()
    missing_response_ids: set[str] = set()

    # CONSOLIDATED MODE: Collect all replies for single summary comment
    collected_replies: List[Dict] = []
    responses_data: Dict = {}

    # Step 2: Load comments with staleness detection and real-time fallback
    repo_name = get_repo_name(repo)
    branch_name = get_current_branch()

    # Retry loop: Re-fetch and retry on 422 stale comment errors
    while retry_count <= max_retries:
        if retry_count > 0:
            print(
                f"\n🔄 RETRY ATTEMPT {retry_count}/{max_retries}: Re-fetching comments after 422 failures"
            )

        all_comments = load_comments_with_staleness_check(
            branch_name, owner, repo, pr_number, repo_name
        )
        print(f"📁 LOADED: {len(all_comments)} comments with staleness validation")

        if not all_comments:
            print("⚠️ WARNING: No comments found in fetched data")
            if retry_count > 0 and collected_replies:
                print("   ⚠️ Breaking retry loop to preserve collected replies")
                break
            return

        # Step 3: Process each comment systematically
        print(f"\n🔄 PROCESSING: {len(all_comments)} comments systematically")

        # Determine current actor
        ok_actor, actor_login, _ = run_command(
            ["gh", "api", "user", "-q", ".login"], description="current actor"
        )
        actor_login = (actor_login or "").strip() or os.environ.get("GITHUB_ACTOR", "")
        if not ok_actor and not actor_login:
            print(
                "⚠️ WARNING: Unable to determine actor login; self-comment filtering may be incomplete"
            )

        # CRITICAL FIX: Process ALL comments (including replies) in chronological order
        # Sort all comments by created_at to preserve conversation order
        # This prevents out-of-sequence execution when replies contain corrections
        all_targets = sorted(all_comments, key=lambda c: c.get("created_at", ""))
        total_targets = 0
        missing_responses = 0

        # Get commit hash once to avoid multiple git calls (fixes Copilot efficiency issue)
        commit_hash = get_git_commit_hash()
        print(f"📝 COMMIT: Using commit {commit_hash} for all responses")

        # Step 3: Load Claude-generated responses
        responses_data = load_claude_responses(branch_name, repo_name)



        # CONSOLIDATED REPLY MODE: Collect all replies instead of posting individually
        # This reduces notification spam and provides a cleaner summary
        # Note: collected_replies is initialized outside the retry loop
        print("\n📝 CONSOLIDATED MODE: Collecting replies for single summary comment")

        # CRITICAL FIX: Process all comments in chronological order (including replies)
        # On retry, only process comments that previously failed with 422_not_found
        targets_to_process = all_targets
        if retry_count > 0:
            unresolved_ids = (
                initial_target_ids
                - successful_reply_ids
                - already_replied_ids
                - missing_response_ids
            )
            targets_to_process = [
                c for c in all_targets if str(c.get("id")) in unresolved_ids
            ]
            print(
                f"🔄 RETRY: Processing only {len(targets_to_process)} unresolved comment(s)"
            )
        for i, comment in enumerate(targets_to_process, 1):
            # SECURITY: Validate each comment before processing
            if not validate_comment_data(comment):
                print(
                    f"[{i}/{len(targets_to_process)}] ❌ SECURITY: Skipping invalid comment data"
                )
                continue

            comment_id = comment.get("id")
            comment_id_str = str(comment_id)
            in_reply_to_id = comment.get("in_reply_to_id")

            # Capture parent comment context when processing replies (for logging)
            parent_comment = None
            if in_reply_to_id:
                parent_comment = next(
                    (c for c in all_comments if c.get("id") == in_reply_to_id), None
                )
                if parent_comment:
                    parent_user_dict = parent_comment.get("user")
                    if isinstance(parent_user_dict, dict) and parent_user_dict.get("login"):
                        parent_author = parent_user_dict.get("login")
                    else:
                        parent_author = parent_comment.get("author", "unknown")
                    parent_body_snippet = sanitize_comment_content(
                        parent_comment.get("body", "")
                    )[:50].replace("\n", " ")
                    print(
                        f"   📎 Reply context: Parent comment #{in_reply_to_id} by @{parent_author}"
                    )
                    print(f'   📎 Parent content: "{parent_body_snippet}..."')
                else:
                    print(
                        f"   ⚠️ WARNING: Parent comment #{in_reply_to_id} not found in fetched comments"
                    )

            # Support both user.login and author field formats
            user_dict = comment.get("user")
            if isinstance(user_dict, dict) and user_dict.get("login"):
                author = user_dict.get("login")
            else:
                author = comment.get("author", "unknown")
            body_snippet = sanitize_comment_content(comment.get("body", ""))[
                :50
            ].replace("\n", " ")

            comment_type_label = "reply" if in_reply_to_id else "top-level"
            print(
                f"\n[{i}/{len(targets_to_process)}] Processing {comment_type_label} comment #{comment_id} by @{author}"
            )
            print(f'   Content: "{body_snippet}..."')

            # Skip our own comments
            if author == actor_login:
                print("   ↪️ Skip: comment authored by current actor")
                continue
            total_targets += 1
            if retry_count == 0:
                initial_target_ids.add(comment_id_str)

            # Idempotency: skip if already replied by current actor AND no one replied after us
            # Support both user.login and author field formats
            our_replies = [
                c
                for c in all_comments
                if (c.get("in_reply_to_id") == comment_id)
                and (
                    ((c.get("user") or {}).get("login") == actor_login)
                    if isinstance(c.get("user"), dict)
                    else (c.get("author") == actor_login)
                )
            ]
            if our_replies:
                # Check if anyone replied AFTER our last reply
                our_replies.sort(key=lambda x: x.get("created_at", ""))
                our_last_reply_time = our_replies[-1].get("created_at", "")
                # Find all replies to this comment
                all_replies_to_comment = [
                    c for c in all_comments if c.get("in_reply_to_id") == comment_id
                ]
                # Check if there are any replies after our last reply
                replies_after_ours = [
                    c
                    for c in all_replies_to_comment
                    if c.get("created_at", "") > our_last_reply_time
                    and (
                        ((c.get("user") or {}).get("login") != actor_login)
                        if isinstance(c.get("user"), dict)
                        else (c.get("author") != actor_login)
                    )
                ]
                if not replies_after_ours:
                    print(
                        "   ↪️ Skip: already replied by current actor (no new replies)"
                    )
                    already_replied_ids.add(comment_id_str)
                    missing_response_ids.discard(comment_id_str)
                    continue
                # Someone replied after us - continue processing to respond to their reply
                print(
                    f"   ℹ️  We already replied, but {len(replies_after_ours)} new reply(ies) found - will process"
                )

            # Idempotency for comments replied via issue comments (review bodies and issue comments)
            # with reference pattern since these don't use in_reply_to_id
            review_ref_pattern = f"In response to [comment #{comment_id}]"
            consolidated_ref_pattern = f"Re: [Comment #{comment_id}]"
            already_has_review_reply = any(
                ((c.get("user") or {}).get("login") == actor_login)
                and (
                    review_ref_pattern in (c.get("body") or "")
                    or consolidated_ref_pattern in (c.get("body") or "")
                )
                for c in all_comments
                if c.get("type") in ("issue", None)
            )
            if already_has_review_reply:
                print(
                    "   ↪️ Skip: comment already has issue comment reply from current actor"
                )
                already_replied_ids.add(comment_id_str)
                missing_response_ids.discard(comment_id_str)
                continue

            # Skip if thread ends with OUR [AI responder] comment indicating completion
            # Only skip if WE are the last commenter, not if someone else replied after us
            thread_replies = [
                c for c in all_comments if c.get("in_reply_to_id") == comment_id
            ]
            if thread_replies:
                # Sort by created_at to find the last reply
                thread_replies.sort(key=lambda x: x.get("created_at", ""))
                last_reply = thread_replies[-1]
                last_reply_body = last_reply.get("body", "")
                last_reply_user = last_reply.get("user")
                last_reply_author = (
                    last_reply_user.get("login", "")
                    if isinstance(last_reply_user, dict)
                    else ""
                )
                # Only skip if WE are the last commenter AND our comment has [AI responder]
                if (
                    "[AI responder]" in last_reply_body
                    and last_reply_author == actor_login
                ):
                    print(
                        "   ↪️ Skip: thread already completed with our [AI responder] comment"
                    )
                    already_replied_ids.add(comment_id_str)
                    missing_response_ids.discard(comment_id_str)
                    continue

            # Get Claude-generated response for this comment
            response_text = get_response_for_comment(
                comment, responses_data, commit_hash
            )

            # Skip posting if no response available (empty string = skip)
            if not response_text or not response_text.strip():
                print(f"   ❌ No Claude response available for comment #{comment_id}")
                missing_responses += 1
                missing_response_ids.add(comment_id_str)
                continue

            # SECURITY: Final validation before collecting
            if len(response_text.strip()) > 65000:  # GitHub comment limit
                print(
                    f"   ⚠️ WARNING: Response too long for comment #{comment_id}, truncating"
                )
                response_text = (
                    response_text[:65000]
                    + "\n\n[Response truncated due to length limit]"
                )

            # CONSOLIDATED MODE: Collect reply instead of posting individually
            comment_type = comment.get("type") or detect_comment_type(comment)
            collected_replies.append({
                "comment_id": comment_id,
                "author": author,
                "body_snippet": body_snippet,
                "response_text": response_text,
                "comment_type": comment_type,
            })
            successful_reply_ids.add(comment_id_str)
            missing_response_ids.discard(comment_id_str)
            print(f"   ✅ COLLECTED: Response for comment #{comment_id} added to consolidated summary")

        # Capture total targets from first pass for accurate reporting
        if retry_count == 0:
            print(
                f"📊 STATS: First pass processed {len(initial_target_ids)} valid targets"
            )

        # Step 4: Check if retry is needed for coverage gaps or 422 failures
        total_targets = len(initial_target_ids)
        covered = len(successful_reply_ids) + len(already_replied_ids)
        coverage_valid = (len(missing_response_ids) == 0) and (covered == total_targets)
        if not coverage_valid and retry_count < max_retries:
            print(
                f"\n🔄 RETRY NEEDED: coverage {covered}/{total_targets} (missing={len(missing_response_ids)})"
            )
            unresolved_ids = (
                initial_target_ids
                - successful_reply_ids
                - already_replied_ids
                - missing_response_ids
            )
            print(f"   Unresolved IDs: {sorted(unresolved_ids)}")
            print(
                f"   Will re-fetch comments and retry (attempt {retry_count + 1}/{max_retries})"
            )
            retry_count += 1
            continue  # Continue while loop for retry
        elif not coverage_valid:
            print(
                f"\n⚠️ RETRY EXHAUSTED: coverage {covered}/{total_targets} (missing={len(missing_response_ids)})"
            )
            print("   Some comments could not be processed after retries")
        else:
            print("\n✅ NO RETRIES NEEDED: Coverage is 100%")

        # Exit retry loop - proceed with coverage validation
        break

    # Step 5: Coverage validation over target comments
    total_targets = len(initial_target_ids)
    covered = len(successful_reply_ids) + len(already_replied_ids)
    coverage_valid = (len(missing_response_ids) == 0) and (covered == total_targets)
    print(
        f"\n🔍 VALIDATION: targets={total_targets} covered={covered} "
        f"(already={len(already_replied_ids)}, posted={len(successful_reply_ids)}) "
        f"missing={len(missing_response_ids)}"
    )

    # Fail on insufficient coverage
    if not coverage_valid:
        print("\n❌ CRITICAL: Coverage validation failed")
        sys.exit(1)

    # Step 6: Post consolidated summary with all replies embedded
    print("\n📝 SUMMARY: Posting consolidated summary comment with all replies")
    summary_posted = post_consolidated_summary(
        owner,
        repo,
        pr_number,
        collected_replies,
        responses_data,
        commit_hash,
        total_targets,
        len(already_replied_ids),
    )
    if not summary_posted:
        print("\n❌ CRITICAL: Failed to post consolidated summary comment")
        sys.exit(1)

    # Step 7: Final report
    print("\n✅ COMPLETE: Comment processing finished")
    print(f"   📊 Total comments: {len(all_comments)}")
    print(f"   🎯 Target comments: {total_targets}")
    print(f"   ✅ Successful replies: {len(successful_reply_ids)}")
    print(f"   🔄 Already replied: {len(already_replied_ids)}")
    print(f"   ❌ Missing responses: {len(missing_response_ids)}")
    print(f"   🎯 Coverage valid: {'Yes' if coverage_valid else 'No'}")

    # Note: No additional failure check needed here - coverage_valid check above
    # already exits if coverage is invalid or missing_responses > 0
    print("\n🎉 SUCCESS: All comments processed with verified coverage!")


if __name__ == "__main__":
    main()
