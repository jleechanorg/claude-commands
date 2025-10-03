#!/usr/bin/env python3
"""
/newbranch or /nb - Create a new branch from a fresh origin/main snapshot

By default this command carries forward any uncommitted work while building the
new branch directly from the latest `origin/main`. If the natural language input
indicates that specific committed changes should be brought along (for example,
"bring in changes 123abc"), the script will cherry-pick those commits after the
branch is created.
"""

import subprocess
import sys
import time
import re


def run_command(cmd, check=True):
    """Run a command and return the result"""
    try:
        # Use shell=False for security - cmd should be a list
        if isinstance(cmd, str):
            cmd = cmd.split()
        result = subprocess.run(
            cmd, shell=False, capture_output=True, text=True, check=check
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout.strip(), e.stderr.strip(), e.returncode


def check_uncommitted_changes():
    """Return True if there are uncommitted changes"""
    stdout, _, _ = run_command(["git", "status", "--porcelain"], check=False)
    return len(stdout.strip()) > 0


def stash_changes():
    """Stash uncommitted changes (including untracked files)."""
    print("📝 Stashing uncommitted changes (including untracked files)...")
    stdout, stderr, returncode = run_command(
        ["git", "stash", "push", "--include-untracked", "-m", "auto-stash-before-newbranch"],
        check=False,
    )

    combined_output = (stdout + "\n" + stderr).strip()

    if returncode != 0:
        print("❌ ERROR: Failed to stash changes")
        if combined_output:
            print(combined_output)
        return False, False

    if "No local changes to save" in combined_output:
        print("ℹ️  No changes were stashed (working tree already clean).")
        return True, False

    print("✅ Changes stashed temporarily")
    return True, True


def pop_stash():
    """Restore previously stashed changes."""
    print("📦 Restoring stashed changes...")
    stdout, stderr, returncode = run_command(["git", "stash", "pop"], check=False)
    combined_output = (stdout + "\n" + stderr).strip()

    if returncode != 0:
        print("⚠️  Warning: Failed to automatically restore stashed changes.")
        if combined_output:
            print(combined_output)
        print(
            "👉 Please restore them manually with `git stash pop` or resolve any merge conflicts."
        )
        return False

    if combined_output:
        print(combined_output)
    print("✅ Stashed changes restored")
    return True


def get_current_branch():
    stdout, stderr, returncode = run_command(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], check=False
    )
    if returncode != 0:
        raise RuntimeError(f"Failed to determine current branch: {stderr or stdout}")
    return stdout.strip()


def fetch_origin_main():
    print("🔄 Fetching latest main from origin...")
    stdout, stderr, returncode = run_command(["git", "fetch", "origin", "main"], check=False)
    if returncode != 0:
        print("❌ ERROR: Failed to fetch origin/main")
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)
        return False
    return True


def checkout_main():
    print("🏠 Checking out local main branch...")
    stdout, stderr, returncode = run_command(["git", "checkout", "main"], check=False)
    if returncode != 0:
        print("❌ ERROR: Could not switch to main branch.")
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)
        return False
    return True


def pull_origin_main():
    print("⬇️  Pulling latest changes into main...")
    stdout, stderr, returncode = run_command(["git", "pull", "origin", "main"], check=False)
    if returncode != 0:
        print("❌ ERROR: Failed to pull latest main.")
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)
        return False
    return True


def sanitize_branch_name(name: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z._-]+", "-", name.strip())
    cleaned = cleaned.strip("-._")
    if not cleaned:
        cleaned = f"dev{int(time.time())}"
    return cleaned.lower()


def parse_branch_request(argv):
    if not argv:
        return None, [], False

    argv_joined = " ".join(argv).strip()
    if not argv_joined:
        return None, [], False

    lowered = argv_joined.lower()

    triggers = [
        "bring in changes",
        "bring in change",
        "include changes",
        "include change",
        "with commits",
        "with change",
        "with changes",
    ]

    commit_tokens = []
    include_commits = False
    branch_source = argv_joined

    for trigger in triggers:
        idx = lowered.find(trigger)
        if idx != -1:
            include_commits = True
            before = argv_joined[:idx].strip()
            after = argv_joined[idx + len(trigger) :].strip()
            branch_source = before if before else trigger
            if after:
                cleaned_after = after.replace(" and ", " ")
                commit_tokens = [
                    token.strip(" ,.")
                    for token in re.split(r"[\s,]+", cleaned_after)
                    if token.strip(" ,.")
                ]
            break

    return branch_source if branch_source else None, commit_tokens, include_commits


def get_local_commits(relative_to="origin/main"):
    stdout, _, returncode = run_command(
        [
            "git",
            "log",
            f"{relative_to}..HEAD",
            "--pretty=%H%x01%s",
        ],
        check=False,
    )
    if returncode != 0:
        return []

    commits = []
    for line in stdout.splitlines():
        if "\x01" not in line:
            continue
        commit_hash, subject = line.split("\x01", 1)
        commits.append((commit_hash.strip(), subject.strip()))
    return commits


def resolve_requested_commits(commit_tokens, local_commits):
    if not local_commits:
        print("ℹ️  No local commits detected to bring forward.")
        return []

    if not commit_tokens:
        print("🧩 Including all local commits from the previous branch.")
        return [commit for commit, _ in reversed(local_commits)]

    resolved = []
    lowered_subject_map = {
        commit_hash: subject.lower() for commit_hash, subject in local_commits
    }
    commit_ids_lower = [
        (commit_hash, commit_hash.lower()) for commit_hash, _ in local_commits
    ]
    rev_parse_cache = {}

    for token in commit_tokens:
        cleaned = token.strip()
        lowered_token = cleaned.lower()
        if lowered_token in {"and", ""}:
            continue

        # First try to match against local commits without invoking git.
        hex_like = bool(re.fullmatch(r"[0-9a-fA-F]{6,40}", cleaned))
        prefix_matches = []
        if hex_like:
            lowered_prefix = lowered_token
            prefix_matches = [
                commit_hash
                for commit_hash, lowered_commit in commit_ids_lower
                if lowered_commit.startswith(lowered_prefix)
            ]

        subject_matches = [
            commit_hash
            for commit_hash, lowered_subject in lowered_subject_map.items()
            if lowered_token in lowered_subject
        ]

        candidate = None
        ambiguous = False

        if prefix_matches:
            if len(prefix_matches) == 1:
                candidate = prefix_matches[0]
            else:
                ambiguous = True
                print(
                    f"⚠️  Ambiguous reference '{token}' matched multiple commits. Skipping."
                )
        elif subject_matches:
            unique_subject_matches = []
            for commit_hash in subject_matches:
                if commit_hash not in unique_subject_matches:
                    unique_subject_matches.append(commit_hash)
            if len(unique_subject_matches) == 1:
                candidate = unique_subject_matches[0]
            else:
                ambiguous = True
                print(
                    f"⚠️  Ambiguous reference '{token}' matched multiple commits. Skipping."
                )

        if ambiguous:
            continue

        if candidate:
            resolved.append(candidate)
            continue

        if lowered_token in rev_parse_cache:
            commit_hash = rev_parse_cache[lowered_token]
        else:
            stdout, _, returncode = run_command(
                ["git", "rev-parse", cleaned],
                check=False,
            )
            if returncode != 0:
                rev_parse_cache[lowered_token] = None
                commit_hash = None
            else:
                commit_hash = stdout.strip()
                rev_parse_cache[lowered_token] = commit_hash

        if not commit_hash:
            print(f"⚠️  Could not resolve commit reference '{token}'. Skipping.")
            continue

        if commit_hash not in lowered_subject_map:
            print(
                f"⚠️  Commit {token} is not among the local commits compared to origin/main; skipping."
            )
            continue

        resolved.append(commit_hash)

    if not resolved:
        print("ℹ️  No committed changes selected to carry forward.")
    else:
        unique = []
        for commit in resolved:
            if commit not in unique:
                unique.append(commit)

        chronological = list(reversed([c for c, _ in local_commits]))
        commit_order = {commit: idx for idx, commit in enumerate(chronological)}
        unique.sort(key=lambda c: commit_order.get(c, float("inf")))
        return unique
    return []

def cherry_pick_commits(commits):
    if not commits:
        return True

    print("🍒 Cherry-picking requested commits onto the new branch...")
    for commit in commits:
        stdout, stderr, returncode = run_command(["git", "cherry-pick", commit], check=False)
        if returncode != 0:
            print(f"❌ ERROR: Cherry-pick failed for commit {commit}.")
            if stdout:
                print(stdout)
            if stderr:
                print(stderr)
            print("👉 Resolve the cherry-pick conflict, then run `git cherry-pick --continue`.")
            return False
    print("✅ Requested commits cherry-picked successfully.")
    return True


def main():
    branch_source, commit_tokens, include_commits = parse_branch_request(sys.argv[1:])

    if branch_source:
        branch_name = sanitize_branch_name(branch_source)
    else:
        timestamp = str(int(time.time()))
        branch_name = f"dev{timestamp}"
        print("⚠️  Using timestamp-based branch name. Consider specifying a descriptive name.")

    print(f"Creating new branch: {branch_name}")

    try:
        current_branch = get_current_branch()
    except RuntimeError as exc:
        print(f"❌ ERROR: {exc}")
        return 1

    print(f"📍 Starting from branch: {current_branch}")

    local_commits = []
    if include_commits:
        local_commits = get_local_commits()
        if not local_commits:
            print("ℹ️  No local commits found relative to origin/main.")

    stashed = False
    if check_uncommitted_changes():
        success, stashed = stash_changes()
        if not success:
            print("❌ ERROR: Failed to stash changes")
            return 1

    if not fetch_origin_main():
        if stashed:
            print("🔁 Restoring stashed changes after fetch failure...")
            pop_stash()
        return 1

    if not checkout_main():
        if stashed:
            print("🔁 Restoring stashed changes after checkout failure...")
            pop_stash()
        return 1

    if not pull_origin_main():
        if stashed:
            print("🔁 Restoring stashed changes after pull failure...")
            pop_stash()
        return 1

    print(f"🌿 Creating and switching to new branch from origin/main: {branch_name}")
    stdout, stderr, returncode = run_command(
        ["git", "checkout", "-b", branch_name, "origin/main"],
        check=False,
    )
    if returncode != 0:
        print(f"❌ ERROR: Failed to create branch {branch_name}")
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)
        if stashed:
            print("🔁 Restoring stashed changes since branch creation failed...")
            pop_stash()
        return 1

    commits_to_apply = []
    if include_commits:
        commits_to_apply = resolve_requested_commits(commit_tokens, local_commits)
        if commits_to_apply:
            if not cherry_pick_commits(commits_to_apply):
                if stashed:
                    print("🔁 Restoring stashed changes after cherry-pick failure...")
                    pop_stash()
                return 1

    if stashed:
        pop_stash()

    print(f"🔗 Pushing and setting upstream tracking to origin/{branch_name}...")
    stdout, stderr, returncode = run_command(
        ["git", "push", "-u", "origin", branch_name],
        check=False,
    )
    if returncode != 0:
        print("⚠️  Warning: Failed to set upstream tracking (this is usually okay)")
        if stderr:
            print(stderr)

    print(f"✅ Successfully created and switched to branch: {branch_name}")
    if include_commits:
        if commits_to_apply:
            print("📋 Branch is based on latest main and includes requested commits plus uncommitted work.")
        else:
            print("📋 Branch is based on latest main; no committed changes were added.")
    else:
        print("📋 Branch is based on latest main and includes your uncommitted work (if any).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
