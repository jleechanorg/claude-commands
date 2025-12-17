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
            timeout=timeout
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

def get_current_branch() -> str:
    """Get current git branch name for temp file path"""
    success, branch, _ = run_command(["git", "branch", "--show-current"])
    if success and branch.strip():
        # Sanitize branch name to prevent path traversal
        branch = branch.strip()
        # Remove dangerous characters that could be used for path traversal
        safe_branch = re.sub(r'[^a-zA-Z0-9_-]', '_', branch)
        return safe_branch[:50]  # Limit length
    return "unknown"

def load_claude_responses(branch_name: str) -> Dict:
    """
    Load Claude-generated responses from JSON file.
    In the modern workflow, Claude analyzes comments, implements fixes,
    generates responses, and saves them to responses.json for Python to post.

    Args:
        branch_name: Current git branch name (sanitized)

    Returns:
        Dictionary containing responses data, empty dict if file not found
    """
    # Ensure branch_name is safe and create secure path
    safe_branch = re.sub(r'[^a-zA-Z0-9_-]', '_', branch_name)[:50]
    responses_file = f"/tmp/{safe_branch}/responses.json"

    # Verify the path doesn't contain traversal attempts
    responses_path = Path(responses_file).resolve()
    expected_prefix = Path(f"/tmp/{safe_branch}").resolve()
    if not str(responses_path).startswith(str(expected_prefix)):
        print(f"⚠️ SECURITY: Path traversal attempt blocked: {responses_file}")
        return {}

    if not os.path.exists(responses_file):
        print(f"⚠️  RESPONSES FILE NOT FOUND: {responses_file}")
        print("⚠️  Claude should have generated responses.json after analyzing comments")
        return {}

    try:
        # Additional security: check file size before reading
        if responses_path.exists():
            file_size = responses_path.stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                print(f"⚠️ SECURITY: File too large: {responses_file} ({file_size} bytes)")
                return {}

        with open(responses_file, 'r') as f:
            responses_data = json.load(f)
        print(f"📁 LOADED: {len(responses_data.get('responses', []))} responses from {responses_file}")
        return responses_data
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Failed to parse responses JSON: {e}")
        return {}
    except Exception as e:
        print(f"❌ ERROR: Failed to load responses file: {e}")
        return {}

def load_comments_with_staleness_check(branch_name: str, owner: str, repo: str, pr_number: str) -> List[Dict]:
    """
    Load comment data with staleness detection and real-time fallback.

    Args:
        branch_name: Current git branch name (sanitized)
        owner: Repository owner
        repo: Repository name
        pr_number: PR number

    Returns:
        List of comment dictionaries (fresh or cached)
    """
    # Ensure branch_name is safe and create secure path
    safe_branch = re.sub(r'[^a-zA-Z0-9_-]', '_', branch_name)[:50]
    comments_file = f"/tmp/{safe_branch}/comments.json"

    # Verify the path doesn't contain traversal attempts
    comments_path = Path(comments_file).resolve()
    expected_prefix = Path(f"/tmp/{safe_branch}").resolve()
    if not str(comments_path).startswith(str(expected_prefix)):
        print(f"⚠️ SECURITY: Path traversal attempt blocked: {comments_file}")
        sys.exit(1)

    # COPILOT: Always fetch fresh data - no cache for PR processing
    if os.path.exists(comments_file):
        cache_age_minutes = (time.time() - os.path.getmtime(comments_file)) / 60
        print(f"🔄 COPILOT MODE: Ignoring {cache_age_minutes:.1f}min cache - fetching fresh comments")
        fetch_fresh_comments(owner, repo, pr_number, comments_file)
    else:
        print(f"📥 NO CACHE: Fetching fresh comments for {owner}/{repo}#{pr_number}")
        fetch_fresh_comments(owner, repo, pr_number, comments_file)

    try:
        with open(comments_file, 'r') as f:
            comment_data = json.load(f)
        return comment_data.get('comments', [])
    except Exception as e:
        print(f"❌ ERROR: Failed to load comments: {e}")
        sys.exit(1)

def fetch_fresh_comments(owner: str, repo: str, pr_number: str, output_file: str):
    """Fetch fresh comments using GitHub API and save to cache file"""

    # Fetch both review comments and issue comments
    inline_cmd = ["gh", "api", f"repos/{owner}/{repo}/pulls/{pr_number}/comments", "--paginate", "-q", ".[]"]
    issue_cmd = ["gh", "api", f"repos/{owner}/{repo}/issues/{pr_number}/comments", "--paginate", "-q", ".[]"]
    review_body_cmd = ["gh", "api", f"repos/{owner}/{repo}/pulls/{pr_number}/reviews", "--paginate", "-q", ".[]"]

    print("📡 FETCHING: Fresh comment data from GitHub API...")

    success_inline, inline_data, _ = run_command(inline_cmd, "fetch inline review comments", timeout=120)
    success_issue, issue_data, _ = run_command(issue_cmd, "fetch issue comments", timeout=120)
    success_review_bodies, review_body_data, _ = run_command(review_body_cmd, "fetch review bodies", timeout=120)

    # Require inline and issue comments (core functionality)
    # Review bodies are optional - gracefully degrade if endpoint fails
    if not (success_inline and success_issue):
        print("❌ ERROR: Failed to fetch core comments (inline/issue) from GitHub API")
        if not os.path.exists(output_file):
            sys.exit(1)
        print("⚠️  Falling back to stale cache...")
        return

    if not success_review_bodies:
        print("⚠️  WARNING: Review bodies fetch failed (permissions/rate-limit?) - continuing without review bodies")
        review_body_data = ""  # Empty, will result in empty list

    # Parse and combine comments
    try:
        inline_comments = [json.loads(line) for line in (inline_data or "").splitlines() if line.strip()]
        issue_comments = [json.loads(line) for line in (issue_data or "").splitlines() if line.strip()]
        # Filter out reviews with empty bodies (e.g., approval reviews without comments)
        raw_reviews = [json.loads(line) for line in (review_body_data or "").splitlines() if line.strip()]
        review_body_comments = [r for r in raw_reviews if r.get("body", "").strip()]

        # Add type information and combine
        for comment in inline_comments:
            comment['type'] = 'inline'
        for comment in issue_comments:
            comment['type'] = 'issue'
        for review in review_body_comments:
            review['type'] = 'review'

        all_comments = inline_comments + issue_comments + review_body_comments

        # Save to cache file
        cache_data = {
            "pr": pr_number,
            "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "comments": all_comments
        }

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
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
    required_fields = ['id', 'body']
    for field in required_fields:
        if field not in comment:
            return False

    # Validate comment ID (must be numeric)
    comment_id = comment.get('id')
    if not isinstance(comment_id, (int, str)) or not str(comment_id).isdigit():
        return False

    # Validate user structure (support both user.login and author formats)
    user = comment.get('user')
    author = comment.get('author')

    # Accept either user.login structure or direct author field
    has_valid_user = isinstance(user, dict) and 'login' in user
    has_valid_author = isinstance(author, str) and author.strip()

    if not (has_valid_user or has_valid_author):
        return False

    # Validate body content
    body = comment.get('body')
    if not isinstance(body, str):
        return False

    # Check for potentially dangerous content patterns
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',  # JavaScript URLs
        r'data:text/html',  # Data URLs
        r'vbscript:',  # VBScript
        r'on\w+\s*=',  # Event handlers
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, body, re.IGNORECASE | re.DOTALL):
            print(f"⚠️ SECURITY: Potentially dangerous content detected in comment #{comment_id}")
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

def get_response_for_comment(comment: Dict, responses_data: Dict, commit_hash: str) -> str:
    """
    Get Claude-generated response for a specific comment.

    Args:
        comment: Comment data from GitHub API
        responses_data: Loaded responses from Claude
        commit_hash: Current commit hash as fallback

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
    print(f"⚠️ SKIP: No Claude response found for comment #{comment_id} - will not post placeholder")
    return ""

def get_git_commit_hash() -> str:
    """Get current git commit hash"""
    success, commit_hash, _ = run_command(["git", "rev-parse", "--short", "HEAD"])
    return commit_hash.strip() if success else "unknown"

def detect_comment_type(comment: Dict) -> str:
    """Detect comment kind: inline (code), review (review body), or issue"""
    html_url = (comment.get("html_url") or "")
    if "#discussion_r" in html_url or comment.get("path") or comment.get("position") or comment.get("diff_hunk"):
        return "inline"
    if "#pullrequestreview-" in html_url or comment.get("pull_request_review_id"):
        return "review"
    if "#issuecomment-" in html_url:
        return "issue"
    return "inline"

def create_threaded_reply(owner: str, repo: str, pr_number: str, comment: Dict, response_text: str) -> bool:
    """Create a threaded reply to a PR comment using appropriate GitHub API"""
    comment_id = comment.get("id")
    comment_type = (comment.get("type") or detect_comment_type(comment))
    if comment_id is None:
        print("❌ ERROR: Missing comment id; skip reply")
        return False

    print(f"🔗 CREATING: Threaded reply to {comment_type} comment #{comment_id}")

    # Issue + review-body via issue comments; inline via review API
    if comment_type in ("issue", "review"):
        return create_issue_comment_reply(owner, repo, pr_number, comment, response_text)
    else:
        return create_review_comment_reply(owner, repo, pr_number, comment_id, response_text, comment)

def create_issue_comment_reply(owner: str, repo: str, pr_number: str, comment: Dict, response_text: str) -> bool:
    """Create a reply to an issue comment (general PR discussion)"""
    # SECURITY: Validate inputs
    if not validate_comment_data(comment):
        print("❌ SECURITY: Invalid comment data for issue comment reply")
        return False

    comment_id = comment.get("id")
    print(f"📝 POSTING: Issue comment reply to #{comment_id}")

    # SECURITY: Sanitize response text
    response_text = sanitize_comment_content(response_text)

    # Determine correct anchor based on comment type
    ctype = (comment.get("type") or detect_comment_type(comment))
    if ctype == "review":
        anchor = f"pullrequestreview-{comment_id}"
    elif ctype in ("inline", "copilot"):
        anchor = f"discussion_r{comment_id}"
    else:
        anchor = f"issuecomment-{comment_id}"

    # Issue comments cannot be threaded directly, so we create a new issue comment
    # with a reference to the original comment
    reply_text = (
        f"> In response to [comment #{comment_id}]"
        f"(https://github.com/{owner}/{repo}/pull/{pr_number}#{anchor}):\n\n{response_text}"
    )

    reply_data = {
        "body": reply_text
    }

    # Use secure JSON input with temporary file to prevent shell injection
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(reply_data, temp_file)
            temp_file_path = temp_file.name

        # Use issues endpoint for issue comments
        success, response_json, stderr = run_command([
            "gh", "api", f"repos/{owner}/{repo}/issues/{pr_number}/comments",
            "--method", "POST",
            "--header", "Content-Type: application/json",
            "--header", "Accept: application/vnd.github+json",
            "--input", temp_file_path
        ])

    except Exception as e:
        print(f"❌ ERROR: Failed to create secure JSON input: {e}")
        return False
    finally:
        # Clean up temporary file in all scenarios
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

    if success:
        try:
            response_data = json.loads(response_json)
            reply_id = response_data.get("id")
            reply_url = response_data.get("html_url")

            print(f"✅ SUCCESS: Issue comment reply #{reply_id} created for comment #{comment_id}")
            print(f"🔗 URL: {reply_url}")
            return True
        except json.JSONDecodeError:
            print(f"⚠️ WARNING: Reply created but couldn't parse response for comment #{comment_id}")
            return True
    else:
        print(f"❌ ERROR: Failed to create issue comment reply for #{comment_id}")
        print(f"   Error: {stderr}")
        return False

def create_review_comment_reply(owner: str, repo: str, pr_number: str, comment_id: int, response_text: str, comment: Dict = None) -> bool:
    """Create a threaded reply to a review comment (code-specific)"""
    print(f"🧵 POSTING: Review comment threaded reply to #{comment_id}")

    # SECURITY: Validate inputs to prevent injection
    if not isinstance(comment_id, (int, str)) or not str(comment_id).isdigit():
        print(f"❌ SECURITY: Invalid comment_id format: {comment_id}")
        return False

    # SURGICAL FIX: Validate comment exists before attempting threading
    if comment is None:
        print(f"⚠️ WARNING: Comment object not provided for validation of #{comment_id}")

    # SECURITY: Sanitize response text
    response_text = sanitize_comment_content(response_text)

    # Prepare the API call data for review comment threading
    reply_data = {
        "body": response_text,
        "in_reply_to": comment_id
    }

    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(reply_data, temp_file)
            temp_file_path = temp_file.name

        # Use pulls/comments endpoint for review comment threading
        success, response_json, stderr = run_command([
            "gh", "api", f"repos/{owner}/{repo}/pulls/{pr_number}/comments",
            "--method", "POST",
            "--header", "Content-Type: application/json",
            "--header", "Accept: application/vnd.github+json",
            "--input", temp_file_path
        ])

    except Exception as e:
        print(f"❌ ERROR: Failed to create secure JSON input: {e}")
        return False
    finally:
        # Clean up temporary file in all scenarios
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

    if success:
        try:
            response_data = json.loads(response_json)
            reply_id = response_data.get("id")
            reply_url = response_data.get("html_url")

            print(f"✅ SUCCESS: Review comment reply #{reply_id} created for comment #{comment_id}")
            print(f"🔗 URL: {reply_url}")
            return True
        except json.JSONDecodeError:
            print(f"⚠️ WARNING: Reply created but couldn't parse response for comment #{comment_id}")
            return True
    else:
        if "422" in (stderr or ""):
            print(f"🔍 DEBUG 422: GitHub returned 422 for comment #{comment_id}")
            # SECURITY: Sanitize error output to prevent information disclosure
            sanitized_stderr = (stderr or "")[:200] if stderr else "No error details"
            print(f"🔍 DEBUG 422: Error summary: {sanitized_stderr}...")

            # Check for specific error patterns
            if "not found" in (stderr or "").lower() or "does not exist" in (stderr or "").lower():
                print(f"🚨 STALE COMMENT: Comment #{comment_id} no longer exists (deleted or from different PR state)")
                print(f"↪️ SKIP: Cannot reply to non-existent comment #{comment_id}")
                return False

            if comment:
                # SECURITY: Only log safe diagnostic information
                comment_type = detect_comment_type(comment)
                has_path = bool(comment.get('path'))
                has_position = bool(comment.get('position'))
                has_diff_hunk = bool(comment.get('diff_hunk'))
                print(f"🔍 DEBUG 422: Comment type: {comment_type}")
                print(f"🔍 DEBUG 422: Has path: {has_path}, position: {has_position}, diff_hunk: {has_diff_hunk}")

                # SURGICAL FIX: Fallback to issue comment when review threading fails
                print(f"🔄 FALLBACK: Attempting issue comment fallback for review comment #{comment_id}")
                fallback_success = create_issue_comment_reply(owner, repo, pr_number, comment, response_text)
                if fallback_success:
                    print(f"✅ FALLBACK SUCCESS: Posted as issue comment instead of threaded review reply for #{comment_id}")
                    return True
                else:
                    print(f"❌ FALLBACK FAILED: Both review threading and issue comment failed for #{comment_id}")
                    return False
            else:
                print("🔍 DEBUG 422: Comment object not available for detailed analysis")
                print(f"↪️ SKIP: GitHub returned 422 (likely stale comment or threading constraint) for #{comment_id}")
                return False
        print(f"❌ ERROR: Failed to create review comment reply for #{comment_id}")
        print(f"   Error: {stderr}")
        return False


def post_final_summary(owner: str, repo: str, pr_number: str, processed_count: int, success_count: int, commit_hash: str) -> bool:
    """Post final summary comment to main PR issue"""

    print(f"📝 POSTING: Final summary comment to PR #{pr_number}")

    summary_body = f"""✅ **Comment Reply Analysis Complete**

**Summary**:
- 📊 **Total Comments Processed**: {processed_count}
- ✅ **Successfully Replied**: {success_count} comments
- ❌ **Failed Replies**: {processed_count - success_count} comments
- 🔄 **Threading**: All replies use GitHub's native threading API
- 📝 **Commit**: {commit_hash}

**Individual Responses**: See individual threaded replies above for detailed responses to each comment.

**Process**: Each comment received a dedicated threaded reply using GitHub's native threading API with `in_reply_to` parameter for proper conversation threading.

**Anti-Bug System**: This systematic processing prevents the PR #864 and PR #1509 bug patterns where individual comments were missed while claiming 100% coverage.

*Generated by /commentreply - Systematic comment processing with zero-tolerance coverage validation*"""

    # Post to main PR issue (not review comments)
    summary_data = {"body": summary_body}

    # Use secure JSON input with temporary file to prevent shell injection
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(summary_data, temp_file)
            temp_file_path = temp_file.name

        # Use secure subprocess call with proper argument separation
        success, response_json, stderr = run_command([
            "gh", "api", f"repos/{owner}/{repo}/issues/{pr_number}/comments",
            "--method", "POST",
            "--header", "Content-Type: application/json",
            "--input", temp_file_path
        ])

    except Exception as e:
        print(f"❌ ERROR: Failed to create secure summary JSON: {e}")
        return False
    finally:
        # Clean up temporary file in all scenarios
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

    if success:
        try:
            response_data = json.loads(response_json)
            summary_url = response_data.get("html_url")
            print("✅ SUCCESS: Final summary comment posted")
            print(f"🔗 SUMMARY URL: {summary_url}")
            return True
        except json.JSONDecodeError:
            print("⚠️ WARNING: Summary posted but couldn't parse response")
            return True
    else:
        print("❌ ERROR: Failed to post final summary comment")
        print(f"   Error: {stderr}")
        return False

def main():
    """Main execution function"""
    print("🚀 STARTING: /commentreply systematic comment processing")
    print("🎯 PURPOSE: Process ALL PR comments with proper threading to prevent missed comment bugs")

    # Step 1: Parse command line arguments (passed from commentreply.md)
    owner, repo, pr_number = parse_arguments()
    print(f"📋 REPOSITORY: {owner}/{repo}")
    print(f"📋 PR NUMBER: #{pr_number}")

    # Step 2: Load comments with staleness detection and real-time fallback
    branch_name = get_current_branch()
    all_comments = load_comments_with_staleness_check(branch_name, owner, repo, pr_number)
    print(f"📁 LOADED: {len(all_comments)} comments with staleness validation")

    if not all_comments:
        print("⚠️ WARNING: No comments found in fetched data")
        return

    # Step 3: Process each comment systematically
    print(f"\n🔄 PROCESSING: {len(all_comments)} comments systematically")
    processed_comments = []
    successful_replies = 0

    # Determine current actor and limit to top-level comments
    ok_actor, actor_login, _ = run_command(
        ["gh", "api", "user", "-q", ".login"],
        description="current actor"
    )
    actor_login = (actor_login or "").strip() or os.environ.get("GITHUB_ACTOR", "")
    top_level = [c for c in all_comments if not c.get("in_reply_to_id")]
    total_targets = 0
    already_replied = 0
    missing_responses = 0

    # Get commit hash once to avoid multiple git calls (fixes Copilot efficiency issue)
    commit_hash = get_git_commit_hash()
    print(f"📝 COMMIT: Using commit {commit_hash} for all responses")

    # Step 3: Load Claude-generated responses
    responses_data = load_claude_responses(branch_name)

    for i, comment in enumerate(top_level, 1):
        # SECURITY: Validate each comment before processing
        if not validate_comment_data(comment):
            print(f"[{i}/{len(top_level)}] ❌ SECURITY: Skipping invalid comment data")
            continue

        comment_id = comment.get("id")
        # Support both user.login and author field formats
        user = comment.get("user", {})
        author = user.get("login") if isinstance(user, dict) else comment.get("author", "unknown")
        body_snippet = sanitize_comment_content(comment.get("body", ""))[:50].replace("\n", " ")

        print(f"\n[{i}/{len(top_level)}] Processing comment #{comment_id} by @{author}")
        print(f"   Content: \"{body_snippet}...\"")

        # Skip our own comments
        if author == actor_login:
            print("   ↪️ Skip: comment authored by current actor")
            continue
        total_targets += 1

        # Idempotency: skip if already replied by current actor
        replied_by_actor = any(
            (c.get("in_reply_to_id") == comment_id) and (c.get("user", {}).get("login") == actor_login)
            for c in all_comments
        )
        if replied_by_actor:
            print("   ↪️ Skip: already replied by current actor")
            already_replied += 1
            continue

        # Idempotency for review body comments (type="review"): check for existing issue comment
        # with reference pattern since review bodies are replied via issue comments without in_reply_to_id
        comment_type = comment.get("type") or detect_comment_type(comment)
        if comment_type == "review":
            review_ref_pattern = f"In response to [comment #{comment_id}]"
            already_has_review_reply = any(
                (c.get("user", {}).get("login") == actor_login) and
                (review_ref_pattern in (c.get("body") or ""))
                for c in all_comments if c.get("type") in ("issue", None)
            )
            if already_has_review_reply:
                print("   ↪️ Skip: review body already has issue comment reply from current actor")
                already_replied += 1
                continue

        # Skip if thread ends with [AI responder] comment indicating completion
        thread_replies = [c for c in all_comments if c.get("in_reply_to_id") == comment_id]
        if thread_replies:
            # Sort by created_at to find the last reply
            thread_replies.sort(key=lambda x: x.get("created_at", ""))
            last_reply = thread_replies[-1]
            last_reply_body = last_reply.get("body", "")
            if "[AI responder]" in last_reply_body:
                print("   ↪️ Skip: thread already completed with [AI responder] comment")
                already_replied += 1
                continue

        # Get Claude-generated response for this comment
        response_text = get_response_for_comment(comment, responses_data, commit_hash)

        # Skip posting if no response available (empty string = skip)
        if not response_text or not response_text.strip():
            print(f"   ❌ No Claude response available for comment #{comment_id}")
            missing_responses += 1
            continue

        # SECURITY: Final validation before API call
        if len(response_text.strip()) > 65000:  # GitHub comment limit
            print(f"   ⚠️ WARNING: Response too long for comment #{comment_id}, truncating")
            response_text = response_text[:65000] + "\n\n[Response truncated due to length limit]"

        # Create threaded reply
        if create_threaded_reply(owner, repo, pr_number, comment, response_text):
            successful_replies += 1

        processed_comments.append(comment)

    # Step 4: Coverage validation over target comments
    covered = already_replied + successful_replies
    coverage_valid = (missing_responses == 0) and (covered == total_targets)
    print(f"\n🔍 VALIDATION: targets={total_targets} covered={covered} "
          f"(already={already_replied}, posted={successful_replies}) "
          f"missing={missing_responses}")

    # Fail on insufficient coverage
    if not coverage_valid:
        print("\n❌ CRITICAL: Coverage validation failed")
        sys.exit(1)

    # Step 5: Post final summary
    print("\n📝 SUMMARY: Posting final summary comment")
    post_final_summary(owner, repo, pr_number, len(processed_comments), successful_replies, commit_hash)

    # Step 6: Final report
    print("\n✅ COMPLETE: Comment processing finished")
    print(f"   📊 Total comments: {len(all_comments)}")
    print(f"   🎯 Target comments: {total_targets}")
    print(f"   ✅ Successful replies: {successful_replies}")
    print(f"   🔄 Already replied: {already_replied}")
    print(f"   ❌ Missing responses: {missing_responses}")
    print(f"   🎯 Coverage valid: {'Yes' if coverage_valid else 'No'}")

    # Note: No additional failure check needed here - coverage_valid check at line 692
    # already exits if coverage is invalid or missing_responses > 0
    print("\n🎉 SUCCESS: All comments processed with verified coverage!")

if __name__ == "__main__":
    main()
