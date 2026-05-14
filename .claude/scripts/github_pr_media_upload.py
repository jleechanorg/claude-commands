#!/usr/bin/env python3
"""Upload PR evidence media to GitHub attachments with no manual browser step.

This uses GitHub's web attachment flow:
1. Get repository id via gh CLI
2. Extract a valid github.com browser cookie from a local browser profile
3. Request an attachment upload policy from github.com
4. Upload the asset to the returned storage URL
5. Finalize the asset on github.com and return the anonymous attachment URL

It can optionally create a ZIP alongside input files, and optionally post the
resulting URLs into a PR comment via `gh pr comment`.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import pathlib
import subprocess
import sys
import tempfile
import zipfile
from typing import Iterable
from urllib.parse import urljoin

import browser_cookie3
import requests


DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

MIME_OVERRIDES = {
    ".gif": "image/gif",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".mov": "video/quicktime",
    ".mp4": "video/mp4",
    ".png": "image/png",
    ".srt": "text/plain",
    ".txt": "text/plain",
    ".webm": "video/webm",
    ".zip": "application/zip",
}


def _run_gh(args: list[str]) -> str:
    env = dict(os.environ)
    env.pop("GITHUB_TOKEN", None)
    env.pop("GH_TOKEN", None)
    result = subprocess.run(
        ["gh", *args],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return result.stdout.strip()


def _gh_repo_id(repo: str) -> str:
    return _run_gh(["api", f"repos/{repo}", "--jq", ".id"])


def _gh_pr_repo(pr: str) -> str:
    return _run_gh(["pr", "view", pr, "--json", "headRepositoryOwner,headRepository", "--jq", ".headRepositoryOwner.login + \"/\" + .headRepository.name"])


def _cookie_string_from_jar(cookiejar) -> str:
    parts = []
    for cookie in cookiejar:
        if cookie.domain.endswith("github.com"):
            parts.append(f"{cookie.name}={cookie.value}")
    return "; ".join(parts)


def _extract_cookie_string(browser: str | None) -> str:
    browser_loaders = []
    if browser == "chrome":
        browser_loaders = [browser_cookie3.chrome]
    elif browser == "edge":
        browser_loaders = [browser_cookie3.edge]
    elif browser == "brave":
        browser_loaders = [browser_cookie3.brave]
    elif browser == "firefox":
        browser_loaders = [browser_cookie3.firefox]
    else:
        browser_loaders = [
            browser_cookie3.chrome,
            browser_cookie3.edge,
            browser_cookie3.brave,
            browser_cookie3.firefox,
        ]

    last_error = None
    for loader in browser_loaders:
        try:
            jar = loader(domain_name="github.com")
            cookie_string = _cookie_string_from_jar(jar)
            if "_gh_sess=" in cookie_string or "user_session=" in cookie_string:
                return cookie_string
        except Exception as exc:  # pragma: no cover - platform/browser-dependent
            last_error = exc

    if os.environ.get("GITHUB_COOKIE"):
        return os.environ["GITHUB_COOKIE"].strip()

    raise RuntimeError(
        "Could not extract a valid github.com browser cookie automatically. "
        "Set GITHUB_COOKIE explicitly or sign in to GitHub in a supported local browser."
    ) from last_error


def _content_type_for(path: pathlib.Path) -> str:
    override = MIME_OVERRIDES.get(path.suffix.lower())
    if override:
        return override
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"


def _default_headers(cookie: str) -> dict[str, str]:
    return {
        "User-Agent": DEFAULT_UA,
        "origin": "https://github.com",
        "referer": "https://github.com/",
        "cookie": cookie,
    }


def _upload_one(path: pathlib.Path, repository_id: str, cookie: str) -> dict[str, str | int]:
    if not path.exists():
        raise FileNotFoundError(path)

    content_type = _content_type_for(path)
    session = requests.Session()

    policies = session.post(
        "https://github.com/upload/policies/assets",
        headers={
            **_default_headers(cookie),
            "GitHub-Verified-Fetch": "true",
            "X-Requested-With": "XMLHttpRequest",
        },
        data={
            "repository_id": repository_id,
            "name": path.name,
            "size": str(path.stat().st_size),
            "content_type": content_type,
        },
        timeout=60,
    )
    policies.raise_for_status()
    policy_json = policies.json()

    with path.open("rb") as infile:
        storage_form = dict(policy_json["form"])
        storage_files = {"file": (path.name, infile, content_type)}
        storage_headers = {
            **_default_headers(cookie),
            **policy_json.get("header", {}),
        }
        if policy_json.get("same_origin"):
            storage_headers["authenticity_token"] = policy_json[
                "upload_authenticity_token"
            ]

        storage_resp = session.post(
            policy_json["upload_url"],
            data=storage_form,
            files=storage_files,
            headers=storage_headers,
            timeout=300,
        )
        storage_resp.raise_for_status()

    finalize_url = urljoin("https://github.com/", policy_json["asset_upload_url"])
    finalize_resp = session.put(
        finalize_url,
        headers={
            **_default_headers(cookie),
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
        },
        data={"authenticity_token": policy_json["asset_upload_authenticity_token"]},
        timeout=60,
    )
    finalize_resp.raise_for_status()
    return policy_json["asset"]


def _zip_path_for(path: pathlib.Path) -> pathlib.Path:
    return path.with_suffix(path.suffix + ".zip")


def _create_zip(path: pathlib.Path) -> pathlib.Path:
    zip_path = _zip_path_for(path)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(path, arcname=path.name)
    return zip_path


def _comment_body(pr: str, uploads: list[dict[str, str | int]]) -> str:
    lines = ["## Evidence Media Uploads", "", f"PR: {pr}", ""]
    for item in uploads:
        lines.append(f"- `{item['original_name']}`: {item['href']}")
    return "\n".join(lines)


def _parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", help="OWNER/REPO")
    parser.add_argument("--pr", help="PR number or full PR URL")
    parser.add_argument("--browser", choices=["chrome", "edge", "brave", "firefox"])
    parser.add_argument(
        "--zip-file",
        action="append",
        default=[],
        help="Create and upload a ZIP next to this file before upload",
    )
    parser.add_argument(
        "--comment",
        action="store_true",
        help="Post a PR comment with the uploaded URLs",
    )
    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Emit JSON instead of plain text",
    )
    parser.add_argument("files", nargs="+")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str]) -> int:
    args = _parse_args(argv)
    repo = args.repo
    if not repo:
        if not args.pr:
            raise SystemExit("Provide either --repo OWNER/REPO or --pr")
        repo = _gh_pr_repo(args.pr)

    repository_id = _gh_repo_id(repo)
    cookie = _extract_cookie_string(args.browser)

    upload_paths: list[pathlib.Path] = [pathlib.Path(item).expanduser().resolve() for item in args.files]
    for zip_item in args.zip_file:
        zip_source = pathlib.Path(zip_item).expanduser().resolve()
        upload_paths.append(_create_zip(zip_source))

    uploads = []
    for path in upload_paths:
        asset = _upload_one(path, repository_id, cookie)
        uploads.append(
            {
                "original_name": path.name,
                "href": asset["href"],
                "id": asset["id"],
                "content_type": asset["content_type"],
                "size": asset["size"],
            }
        )

    if args.comment:
        if not args.pr:
            raise SystemExit("--comment requires --pr")
        with tempfile.NamedTemporaryFile("w", delete=False) as handle:
            handle.write(_comment_body(args.pr, uploads))
            temp_path = handle.name
        try:
            _run_gh(["pr", "comment", args.pr, "--body-file", temp_path])
        finally:
            pathlib.Path(temp_path).unlink(missing_ok=True)

    if args.json_output:
        print(json.dumps({"repo": repo, "repository_id": repository_id, "uploads": uploads}, indent=2))
    else:
        for item in uploads:
            print(f"{item['original_name']}: {item['href']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
