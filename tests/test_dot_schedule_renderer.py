import importlib.util
import json
import os
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / ".claude/skills/agy-dot-coordinator/scripts/render_native_schedule.py"
spec = importlib.util.spec_from_file_location("schedule_renderer", SCRIPT)
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


class ScheduleRendererTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir="/tmp")
        self.root = Path(self.temp.name)
        self.dot = self.root / "dot.json"
        self.dot.write_text(json.dumps({"accounts": {f"account-{x}": {"user_data_dir": "/tmp/profile"} for x in "abc"}}))
        self.dot.chmod(0o600)
        self.pi = self.root / "pi"
        self.pi.write_text("#!/bin/sh\nexit 0\n")
        self.pi.chmod(0o700)
        self.package_root = self.root / "node_modules/chrome-devtools-mcp"
        entry = self.package_root / "build/src/bin/chrome-devtools-mcp.js"
        entry.parent.mkdir(parents=True)
        entry.write_text("// test\n")
        (self.package_root / "package.json").write_text('{"version":"1.6.0"}')
        self.mcp = entry
        self.config = self.root / "schedule.json"
        self.write_config("macos")

    def tearDown(self):
        self.temp.cleanup()

    def write_config(self, host, minutes=None):
        minutes = minutes or (renderer.MAC_MINUTES if host == "macos" else renderer.LINUX_MINUTES)
        self.config.write_text(json.dumps({
            "version": 1, "host_role": host, "dot_config_file": str(self.dot),
            "pi_bin": str(self.pi), "chrome_devtools_mcp_js": str(self.mcp),
            "accounts": [{"key": f"account-{x}", "minute": minutes[i], "identity_sha256": f"{i:064x}", "task": "Read-only check"} for i, x in enumerate("abc")],
        }))
        self.config.chmod(0o600)

    def test_macos_renders_three_inactive_private_plists_with_ordered_minutes(self):
        out = renderer.render(self.config, self.root / "mac-stage", "macos")
        self.assertEqual(len(list(out.glob("*.plist"))), 3)
        self.assertEqual(stat.S_IMODE(out.stat().st_mode), 0o700)
        plists = [renderer.plistlib.loads(p.read_bytes()) for p in sorted(out.glob("*.plist"))]
        self.assertEqual([p["StartCalendarInterval"]["Minute"] for p in plists], [0, 20, 40])
        self.assertTrue(all(p["ProgramArguments"][-2:] == ["--account", p["ProgramArguments"][-1]] for p in plists))
        self.assertTrue(all(stat.S_IMODE(p.stat().st_mode) == 0o600 for p in out.iterdir()))

    def test_linux_renders_ordered_timer_service_and_private_env(self):
        self.write_config("linux")
        session = {"DISPLAY": ":1", "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/user/1000/bus", "XDG_RUNTIME_DIR": "/run/user/1000"}
        with patch.dict(os.environ, session):
            out = renderer.render(self.config, self.root / "linux-stage", "linux")
        timers = sorted(out.glob("*.timer"))
        self.assertEqual({"10", "30", "50"}, {p.stem.rsplit("-", 1)[1] for p in timers})
        self.assertTrue(all(f"OnCalendar=*-*-* *:{p.stem.rsplit('-', 1)[1]}:00" in p.read_text() for p in timers))
        self.assertIn("--account account-a", (out / "ai.gemini.agy-dot-coordinator-30.service").read_text())
        service = (out / "ai.gemini.agy-dot-coordinator-30.service").read_text()
        self.assertIn("TimeoutStartSec=800", service)
        self.assertIn("WorkingDirectory=%h", service)
        self.assertIn("DOT_EXPECTED_IDENTITY_SHA256=\"", (out / "ai.gemini.agy-dot-coordinator-30.env").read_text())
        self.assertIn('DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/1000/bus"', (out / "ai.gemini.agy-dot-coordinator-30.env").read_text())
        self.assertIn('XDG_RUNTIME_DIR="/run/user/1000"', (out / "ai.gemini.agy-dot-coordinator-30.env").read_text())

    def test_rejects_wrong_cadence_or_host_before_output(self):
        self.write_config("macos", (10, 20, 40))
        output = self.root / "bad-stage"
        with self.assertRaisesRegex(ValueError, "ordered host cadence"):
            renderer.render(self.config, output, "macos")
        self.assertFalse(output.exists())

    def test_rejects_missing_dot_account_and_unpinned_mcp(self):
        config = json.loads(self.config.read_text())
        config["accounts"][0]["key"] = "not-configured"
        self.config.write_text(json.dumps(config))
        with self.assertRaisesRegex(ValueError, "missing from Dot configuration"):
            renderer.render(self.config, self.root / "missing-stage", "macos")
        config["accounts"][0]["key"] = "account-a"
        self.config.write_text(json.dumps(config))
        self.config.chmod(0o600)
        self.package_root.joinpath("package.json").write_text('{"version":"1.5.0"}')
        with self.assertRaisesRegex(ValueError, "version 1.6.0"):
            renderer.render(self.config, self.root / "version-stage", "macos")

    def test_refuses_existing_destination_and_insecure_config(self):
        output = self.root / "existing"
        output.mkdir()
        with self.assertRaisesRegex(ValueError, "already exists"):
            renderer.render(self.config, output, "macos")
        self.config.chmod(0o644)
        with self.assertRaisesRegex(ValueError, "mode 0600"):
            renderer.render(self.config, self.root / "insecure-stage", "macos")

    def test_staging_output_must_be_under_tmp(self):
        with self.assertRaisesRegex(ValueError, "under /tmp"):
            renderer.render(self.config, Path.home() / "not-a-stage", "macos")

    def test_systemd_environment_escapes_shell_metacharacters(self):
        encoded = renderer.systemd_value('a"b$PATH`x\\y')
        self.assertEqual(encoded, '"a\\"b\\$PATH\\`x\\\\y"')

    def test_legacy_installer_entrypoints_refuse_activation_without_render_flag(self):
        scripts = SCRIPT.parent
        for name in ("install-service.sh", "install-launchagent.sh", "install-systemd.sh"):
            result = subprocess.run(["/bin/bash", str(scripts / name)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("Activation is not performed", result.stderr)


if __name__ == "__main__":
    unittest.main()
