#!/usr/bin/env python3
"""Unit tests for check_browser_policy.py — the headed-browser detection gate."""
from __future__ import annotations

import importlib.util
import pathlib
import subprocess
import sys
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "check_browser_policy.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_browser_policy", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class FindForbiddenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = _load_module()

    def test_clean_text_is_clean(self):
        self.assertEqual(self.mod.find_forbidden(""), [])
        self.assertEqual(self.mod.find_forbidden("Please navigate to the docs page"), [])
        self.assertEqual(self.mod.find_forbidden("Use hide_browser before any click"), [])

    def test_show_browser_forbidden(self):
        self.assertIn("show_browser", self.mod.find_forbidden("call show_browser now"))

    def test_headless_false_forbidden(self):
        self.assertIn(
            "hide_browser_false",
            self.mod.find_forbidden("launch with headless: false"),
        )

    def test_headed_flag_forbidden(self):
        self.assertIn("headed_flag", self.mod.find_forbidden("chrome --headed --no-sandbox"))

    def test_headed_mode_forbidden(self):
        self.assertIn("headed_mode", self.mod.find_forbidden("Switch to headed mode"))

    def test_visible_browser_forbidden(self):
        self.assertIn("visible_browser", self.mod.find_forbidden("Open the visible browser please"))

    def test_claude_in_chrome_localhost_forbidden(self):
        body = "mcp__claude-in-chrome__navigate http://localhost:3000"
        self.assertIn("claude_in_chrome_localhost", self.mod.find_forbidden(body))

    def test_claude_in_chrome_non_localhost_allowed(self):
        body = "mcp__claude-in-chrome__navigate https://example.com"
        self.assertEqual(self.mod.find_forbidden(body), [])


class UserOptedIntoHeadedTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = _load_module()

    def test_explicit_opt_in_phrases(self):
        for phrase in [
            "show browser",
            "headed mode",
            "visible browser",
            "I want to see the window",
        ]:
            self.assertTrue(self.mod.user_opted_into_headed(phrase), phrase)

    def test_default_no_opt_in(self):
        self.assertFalse(self.mod.user_opted_into_headed("please run a check"))
        self.assertFalse(self.mod.user_opted_into_headed(""))


class CliIntegrationTests(unittest.TestCase):
    """Drive the script via CLI the way SOUL's pre-flight check does."""

    def _run(self, text: str) -> subprocess.CompletedProcess:
        return subprocess.run(  # noqa: S603
            [sys.executable, str(SCRIPT), "-"],
            input=text,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_clean_plan_passes(self):
        result = self._run("1. Open playwright-mcp headless\n2. Take screenshot\n")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("OK", result.stdout)

    def test_show_browser_plan_fails(self):
        result = self._run("Step 1: call show_browser\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("FORBIDDEN", result.stdout)

    def test_headed_mode_plan_fails(self):
        result = self._run("Switch browser to headed mode\n")
        self.assertEqual(result.returncode, 1)

    def test_claude_in_chrome_localhost_plan_fails(self):
        result = self._run("Use mcp__claude-in-chrome to test http://127.0.0.1:5000\n")
        self.assertEqual(result.returncode, 1)

    def test_opt_in_phrase_not_flagged_by_cli(self):
        # The script only checks FORBIDDEN patterns; opt-in is consumed upstream by the
        # calling agent (see SKILL.md "Explicit opt-in phrases"). "show browser" (with a
        # space) is the opt-in phrase, NOT the forbidden "show_browser" (underscored)
        # tool parameter. The CLI script must let opt-in phrases pass through.
        result = self._run("Please show browser so I can see the result\n")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_forbidden_underscored_show_browser_is_caught(self):
        # The tool call form "show_browser" (single token) IS forbidden regardless of
        # whether the user also said "show browser" — the tool parameter wins.
        result = self._run("show browser please, but call show_browser=true\n")
        self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
