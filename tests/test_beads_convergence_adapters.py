"""Focused read-only tests for the br-sqlite-v1 adapter."""

import os
import tempfile
import unittest
from pathlib import Path

from scripts.beads_convergence.adapters import AdapterError, BrSqliteV1Adapter
from scripts.beads_convergence.fsafety import open_trusted_tree


class AdapterTest(unittest.TestCase):
    def _beads(self, root: Path) -> Path:
        beads = root / ".beads"
        beads.mkdir()
        (beads / "beads.db").write_bytes(b"SQLite format 3\x00" + b"\0" * 32)
        (beads / "issues.jsonl").write_bytes(b"{}\n")
        return beads

    def test_sqlite_backend_and_source_fingerprint_are_descriptor_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            beads = self._beads(root)
            with open_trusted_tree(root, beads) as handle:
                adapter = BrSqliteV1Adapter()
                self.assertEqual(adapter.attest_backend(handle).backend, "sqlite")
                snapshot = adapter.fingerprint_sources(handle)
                self.assertEqual(
                    [source.name for source in snapshot.sources],
                    ["beads.db", "issues.jsonl"],
                )

    def test_hot_journal_and_unknown_sidecar_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            beads = self._beads(root)
            (beads / "beads.db-journal").write_bytes(b"hot")
            with open_trusted_tree(root, beads) as handle:
                with self.assertRaisesRegex(AdapterError, "hot beads.db-journal"):
                    BrSqliteV1Adapter().attest_backend(handle)

    def test_hard_linked_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            beads = self._beads(root)
            os.link(beads / "issues.jsonl", beads / "beads.db-wal")
            with open_trusted_tree(root, beads) as handle:
                with self.assertRaisesRegex(AdapterError, "unsafe source"):
                    BrSqliteV1Adapter().fingerprint_sources(handle)

    def test_unproven_writer_lease_is_plan_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            beads = self._beads(root)
            with open_trusted_tree(root, beads) as handle:
                lease = BrSqliteV1Adapter().acquire_writer_exclusion(handle, object())
                self.assertTrue(lease.plan_only)
                self.assertFalse(lease.available)


if __name__ == "__main__":
    unittest.main()
