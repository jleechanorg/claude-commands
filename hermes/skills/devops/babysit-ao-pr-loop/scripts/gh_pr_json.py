"""GitHub REST JSON parser tolerant of literal control chars inside strings.

Why this exists: GitHub's REST API does not pre-escape the ``body`` field on
``/repos/{owner}/{repo}/pulls/{N}`` responses. When the PR body contains
hard line breaks (very common for multi-paragraph Markdown), the response
JSON contains literal LF/CR bytes inside what looks like a string value, and
Python's stdlib ``json.loads`` rejects them per RFC 7159 strict mode with::

    json.decoder.JSONDecodeError: Invalid control character at: line N column M (char K)

Babysit cron prompts that fall back to REST after a GraphQL rate-limit
``gh pr view`` failure (see references/graphql-rate-limit-rest-fallback.md)
hit this every time the PR description is non-trivial. This helper escapes
control chars on the fly and parses the result transparently.

Usage::

    from gh_pr_json import gh_safe_json_loads
    data = gh_safe_json_loads(open("/tmp/pr779.json").read())
    print(data["state"])

Or run as a CLI for one-off status checks::

    python3 gh_pr_json.py "$(gh auth token)" jleechanorg/jleechanclaw 779
    # -> PR #779 [jleechanorg/jleechanclaw] state=open mergeable=True ...

CLI flags::

    --state-only    print only the "state" field, suitable for shell capture
    --summary       print one-line summary table (default)
    --json          print the full parsed JSON object (pretty-printed)

Pitfalls (read before modifying):

- This module uses ``re.sub`` to escape control chars before ``json.loads``.
  It does NOT validate the JSON structure first, and it does NOT strip
  BOMs. If the GitHub response ever starts including the BOM character,
  add ``\\ufeff`` to the regex.
- Keeping DEL (``\\x7f``) in the escape set is the safer default; narrow
  the pattern with ``r'[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f]'`` only if you have
  a regression test that demonstrates DEL is fine to leave raw.
- Do NOT use ``json.loads(raw, strict=False)`` — Python's ``strict=False``
  still rejects U+0000-U+001F per the spec, and the ``strict=False`` flag
  exists for a different (legacy) reason.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request

# Match every byte in 0x00-0x08, 0x0b, 0x0c, 0x0e-0x1f, 0x7f. We exclude 0x09 (TAB),
# 0x0a (LF), and 0x0d (CR) because those are valid inside JSON strings per RFC 7159.
# But GitHub's response *does* include literal LF/CR inside the body field —
# those are also caught by this pattern. If a regression test shows we are
# double-escaping LFs that GitHub has already escaped, narrow the set.
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _to_escape(byte: str) -> str:
    """Escape a single control character. Tab (\\x09) becomes ``\\t``; everything
    else in the catch range becomes a ``\\u00XX`` hex escape.
    """
    if byte == "\t":
        return "\\t"
    return f"\\u00{ord(byte):02x}"


def _escape_control_chars(raw: str) -> str:
    return _CONTROL_CHARS_RE.sub(lambda m: _to_escape(m.group()), raw)


def gh_safe_json_loads(raw):
    """Parse a GitHub REST JSON response that may contain raw LF/CR inside
    string values. Returns the decoded dict.
    """
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    return json.loads(_escape_control_chars(raw))


def fetch_pr_via_rest(token: str, owner: str, repo: str, pr_number: int) -> dict:
    """Fetch a PR's REST payload and return the parsed dict. Uses
    ``urllib.request`` to avoid a hard dep on the ``requests`` library
    (cron environments rarely have it preinstalled).
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "babysit-pr-json-helper",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return {
            "error": f"http {exc.code}",
            "detail": exc.read().decode("utf-8", errors="replace"),
        }
    return gh_safe_json_loads(body)


def _format_summary(data: dict, owner: str, repo: str, pr: int) -> str:
    return (
        f"PR #{pr} [{owner}/{repo}] "
        f"state={data.get('state')} "
        f"mergeable={data.get('mergeable')} "
        f"additions={data.get('additions')} "
        f"deletions={data.get('deletions')} "
        f"files={data.get('changed_files')} "
        f"merged={data.get('merged')}"
    )


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    flags = {a for a in argv if a.startswith("--")}

    usage = (
        "usage: gh_pr_json.py <token> <owner/repo> <pr> "
        "[--state-only | --summary | --json]"
    )
    if len(args) != 3:
        print(usage, file=sys.stderr)
        return 2

    token, owner_repo, pr_arg = args[0], args[1], args[2]
    if "/" not in owner_repo:
        print(usage, file=sys.stderr)
        print(
            "error: <owner/repo> must contain a slash, e.g. jleechanorg/jleechanclaw",
            file=sys.stderr,
        )
        return 2
    owner, repo = owner_repo.split("/", 1)
    try:
        pr = int(pr_arg)
    except ValueError:
        print(
            f"error: PR number must be an integer, got {pr_arg!r}",
            file=sys.stderr,
        )
        return 2

    data = fetch_pr_via_rest(token, owner, repo, pr)
    if isinstance(data, dict) and "error" in data:
        print(data["error"], file=sys.stderr)
        return 1

    if "--state-only" in flags:
        print(data.get("state"))
    elif "--json" in flags:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(_format_summary(data, owner, repo, pr))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
