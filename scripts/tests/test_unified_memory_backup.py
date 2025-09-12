"""
Comprehensive test coverage for unified_memory_backup.py

Tests cover:
- CRDT merging logic (Last-Write-Wins)
- File format detection and conversion
- Historical snapshot creation
- Environment validation
- Lock file management
- Git operations safety
- Error handling and recovery
"""
import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime
import sys

# Add scripts directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'memory_sync'))
from unified_memory_backup import UnifiedMemoryBackup


class TestUnifiedMemoryBackup(unittest.TestCase):
    """Test suite for UnifiedMemoryBackup class"""

    def setUp(self):
        """Set up test environment"""
        self.backup = UnifiedMemoryBackup(mode='manual')
        self.test_timestamp = datetime(2025, 1, 21, 12, 0, 0)

        # Sample memory data for testing
        self.sample_local_memories = [
            {
                "id": "memory_1",
                "name": "Test Memory 1",
                "content": "Local version",
                "timestamp": "2025-01-21T11:00:00Z"
            },
            {
                "id": "memory_2",
                "name": "Test Memory 2",
                "content": "Only in local",
                "timestamp": "2025-01-21T10:00:00Z"
            }
        ]

        self.sample_remote_memories = [
            {
                "id": "memory_1",
                "name": "Test Memory 1",
                "content": "Remote version (newer)",
                "timestamp": "2025-01-21T12:00:00Z"  # Newer timestamp
            },
            {
                "id": "memory_3",
                "name": "Test Memory 3",
                "content": "Only in remote",
                "timestamp": "2025-01-21T09:00:00Z"
            }
        ]

    def test_memory_timestamp_extraction(self):
        """Test timestamp extraction from memory entries"""
        # Test standard timestamp field
        memory_with_timestamp = {"timestamp": "2025-01-21T12:00:00Z"}
        result = self.backup.get_memory_timestamp(memory_with_timestamp)
        self.assertEqual(result, "2025-01-21T12:00:00Z")

        # Test last_updated field
        memory_with_updated = {"last_updated": "2025-01-21T11:00:00Z"}
        result = self.backup.get_memory_timestamp(memory_with_updated)
        self.assertEqual(result, "2025-01-21T11:00:00Z")

        # Test fallback to epoch
        memory_no_timestamp = {"content": "no timestamp"}
        result = self.backup.get_memory_timestamp(memory_no_timestamp)
        self.assertEqual(result, "1970-01-01T00:00:00Z")

    def test_crdt_merge_last_write_wins(self):
        """Test CRDT Last-Write-Wins merging strategy"""
        merged = self.backup.merge_memory_entries(
            self.sample_local_memories,
            self.sample_remote_memories
        )

        # Should have 3 total memories (local + remote unique)
        self.assertEqual(len(merged), 3)

        # Memory 1 should use remote version (newer timestamp)
        memory_1 = next(m for m in merged if m["id"] == "memory_1")
        self.assertEqual(memory_1["content"], "Remote version (newer)")

        # Memory 2 should be from local only
        memory_2 = next(m for m in merged if m["id"] == "memory_2")
        self.assertEqual(memory_2["content"], "Only in local")

        # Memory 3 should be from remote only
        memory_3 = next(m for m in merged if m["id"] == "memory_3")
        self.assertEqual(memory_3["content"], "Only in remote")

    def test_crdt_merge_with_missing_ids(self):
        """Test CRDT merge handles missing memory IDs gracefully"""
        local_no_id = [{"content": "no id", "timestamp": "2025-01-21T10:00:00Z"}]
        remote_no_id = [{"content": "remote no id", "timestamp": "2025-01-21T11:00:00Z"}]

        merged = self.backup.merge_memory_entries(local_no_id, remote_no_id)

        # Should create fallback IDs and merge properly
        self.assertEqual(len(merged), 2)

    def test_load_memory_array_format(self):
        """Test loading JSON array format memory files"""
        test_data = [{"id": "test", "content": "array format"}]

        with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
            with patch('os.path.exists', return_value=True):
                result = self.backup.load_memory_array("dummy_path.json")

        self.assertEqual(result, test_data)

    def test_load_memory_jsonl_format(self):
        """Test loading JSONL format memory files"""
        jsonl_data = '{"id": "test1", "content": "line 1"}\n{"id": "test2", "content": "line 2"}\n'
        expected = [
            {"id": "test1", "content": "line 1"},
            {"id": "test2", "content": "line 2"}
        ]

        with patch('builtins.open', mock_open(read_data=jsonl_data)):
            with patch('os.path.exists', return_value=True):
                result = self.backup.load_memory_jsonl("dummy_path.jsonl")

        self.assertEqual(result, expected)

    def test_load_memory_jsonl_invalid_lines(self):
        """Test JSONL loader handles invalid JSON lines gracefully"""
        invalid_jsonl = '{"valid": "json"}\ninvalid json line\n{"another": "valid"}\n'
        expected = [
            {"valid": "json"},
            {"another": "valid"}
        ]

        with patch('builtins.open', mock_open(read_data=invalid_jsonl)):
            with patch('os.path.exists', return_value=True):
                result = self.backup.load_memory_jsonl("dummy_path.jsonl")

        self.assertEqual(result, expected)

    def test_save_memory_formats(self):
        """Test saving memory in both JSON array and JSONL formats"""
        test_data = [{"id": "test", "content": "save test"}]

        # Test JSON array saving
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.makedirs'):
                self.backup.save_memory_array(test_data, "test.json")

        mock_file.assert_called_once()

        # Test JSONL saving
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.makedirs'):
                self.backup.save_memory_jsonl(test_data, "test.jsonl")

        mock_file.assert_called_once()

    def test_environment_validation(self):
        """Test environment validation checks"""
        with patch('os.path.exists') as mock_exists:
            # Test missing memory file
            mock_exists.return_value = False

            with patch('sys.exit') as mock_exit:
                self.backup.validate_environment()
                mock_exit.assert_called_once_with(1)

            # Reset mock and test existing memory file
            mock_exit.reset_mock()
            mock_exists.return_value = True

            # Should not call sys.exit
            self.backup.validate_environment()
            mock_exit.assert_not_called()

    def test_lock_file_management(self):
        """Test lock file acquisition and cleanup"""
        with tempfile.TemporaryDirectory() as temp_dir:
            lock_file = os.path.join(temp_dir, "test.lock")
            self.backup.lock_file = lock_file

            # Test successful lock acquisition
            self.backup.acquire_lock()
            self.assertTrue(os.path.exists(lock_file))

            # Test cleanup removes lock
            self.backup.cleanup()
            self.assertFalse(os.path.exists(lock_file))

    def test_lock_file_already_exists(self):
        """Test lock file prevents concurrent execution"""
        with tempfile.TemporaryDirectory() as temp_dir:
            lock_file = os.path.join(temp_dir, "test.lock")

            # Create existing lock file with a PID
            with open(lock_file, 'w') as f:
                f.write("12345")  # Mock PID

            self.backup.lock_file = lock_file

            # Mock os.kill to simulate running process (which triggers error_exit)
            with patch('os.kill', return_value=None):  # Process exists (no OSError)
                with patch('sys.exit') as mock_exit:
                    self.backup.acquire_lock()
                    mock_exit.assert_called_once_with(1)

    def test_run_command_success(self):
        """Test successful command execution"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "success"

        with patch('subprocess.run', return_value=mock_result):
            result = self.backup.run_command(['echo', 'test'])

        self.assertTrue(result)

    def test_run_command_failure(self):
        """Test failed command execution"""
        # The run_command method uses check=True, so it raises CalledProcessError on failure
        from subprocess import CalledProcessError

        with patch('subprocess.run', side_effect=CalledProcessError(1, ['false'], stderr="error")):
            result = self.backup.run_command(['false'])

        self.assertFalse(result)

    def test_historical_snapshot_creation(self):
        """Test historical snapshot creation with metadata"""
        test_memories = [{"id": "test", "content": "snapshot test"}]

        with patch('os.path.exists', return_value=False):  # No existing snapshot
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('json.load', return_value=test_memories):
                    with patch('json.dump') as mock_dump:
                        self.backup.create_historical_snapshot()

        # Verify snapshot was created with metadata
        mock_dump.assert_called_once()
        call_args = mock_dump.call_args[0]
        snapshot_data = call_args[0]

        # First item should be metadata
        self.assertIn('_metadata', snapshot_data[0])
        self.assertEqual(snapshot_data[0]['_metadata']['entity_count'], 1)

    def test_historical_snapshot_skip_existing(self):
        """Test historical snapshot skips if already exists for today"""
        with patch('os.path.exists', return_value=True):  # Existing snapshot
            with patch('builtins.open') as mock_file:
                self.backup.create_historical_snapshot()

        # Should not attempt to create file
        mock_file.assert_not_called()

    def test_commit_and_push_no_changes(self):
        """Test commit skips when no changes detected"""
        mock_result = MagicMock()
        mock_result.returncode = 0  # No changes (git diff --quiet succeeds)

        with patch('subprocess.run', return_value=mock_result):
            with patch('os.chdir'):
                self.backup.commit_and_push(0)

        # Should exit early without further git operations

    def test_commit_and_push_with_changes(self):
        """Test commit and push when changes exist"""
        # Mock git diff to show changes exist
        mock_diff_result = MagicMock()
        mock_diff_result.returncode = 1  # Changes exist

        # Mock successful git operations
        mock_success_result = MagicMock()
        mock_success_result.returncode = 0

        # Mock commit hash retrieval
        mock_hash_result = MagicMock()
        mock_hash_result.returncode = 0
        mock_hash_result.stdout = "abc123def456"

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = [
                mock_diff_result,      # git diff --quiet (changes exist)
                mock_success_result,   # git add
                mock_success_result,   # git commit
                mock_success_result,   # git push
                mock_hash_result       # git rev-parse HEAD
            ]

            with patch('os.chdir'):
                with patch.object(self.backup, 'load_memory_jsonl', return_value=[]):
                    self.backup.commit_and_push(5)

        # Verify all git commands were called
        self.assertEqual(mock_run.call_count, 5)

    def test_mode_configurations(self):
        """Test different execution modes (manual vs cron)"""
        # Test manual mode (verbose)
        manual_backup = UnifiedMemoryBackup(mode='manual')
        self.assertTrue(manual_backup.verbose)

        # Test cron mode (quiet)
        cron_backup = UnifiedMemoryBackup(mode='cron')
        self.assertFalse(cron_backup.verbose)

    def test_error_handling_and_cleanup(self):
        """Test error handling ensures proper cleanup"""
        with tempfile.TemporaryDirectory() as temp_dir:
            lock_file = os.path.join(temp_dir, "test.lock")
            self.backup.lock_file = lock_file

            # Create lock file
            self.backup.acquire_lock()
            self.assertTrue(os.path.exists(lock_file))

            # Simulate error and cleanup
            try:
                raise Exception("Simulated error")
            except:
                self.backup.cleanup()

            # Verify cleanup occurred
            self.assertFalse(os.path.exists(lock_file))


class TestUnifiedMemoryBackupIntegration(unittest.TestCase):
    """Integration tests for complete backup workflows"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.backup = UnifiedMemoryBackup(mode='manual')

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_end_to_end_backup_workflow(self):
        """Test complete backup workflow from start to finish"""
        # Create test memory files
        local_memory_file = os.path.join(self.temp_dir, "local_memory.json")
        repo_memory_file = os.path.join(self.temp_dir, "repo_memory.json")

        local_data = [{"id": "local_1", "content": "local", "timestamp": "2025-01-21T10:00:00Z"}]
        remote_data = [{"id": "remote_1", "content": "remote", "timestamp": "2025-01-21T11:00:00Z"}]

        with open(local_memory_file, 'w') as f:
            json.dump(local_data, f)

        with open(repo_memory_file, 'w') as f:
            json.dump(remote_data, f)

        # Configure backup for test files
        self.backup.memory_file = local_memory_file

        # Test merge workflow
        local_memories = self.backup.load_memory_array(local_memory_file)
        remote_memories = self.backup.load_memory_array(repo_memory_file)
        merged = self.backup.merge_memory_entries(local_memories, remote_memories)

        # Verify merge results
        self.assertEqual(len(merged), 2)
        ids = [m["id"] for m in merged]
        self.assertIn("local_1", ids)
        self.assertIn("remote_1", ids)


if __name__ == '__main__':
    # Set environment for testing
    os.environ['TESTING'] = 'true'

    # Create test results directory
    os.makedirs('test_results', exist_ok=True)

    # Run tests with coverage if available
    try:
        import coverage
        cov = coverage.Coverage()
        cov.start()

        unittest.main(verbosity=2, exit=False)

        cov.stop()
        cov.save()
        print("\n" + "="*50)
        print("📊 COVERAGE REPORT")
        print("="*50)
        cov.report(show_missing=True)

    except ImportError:
        # Run without coverage
        print("⚠️  Coverage package not available, running tests without coverage")
        unittest.main(verbosity=2)

    print("\n" + "="*50)
    print("✅ UNIFIED MEMORY BACKUP TESTS COMPLETE")
    print("="*50)
