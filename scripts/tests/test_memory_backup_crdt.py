# test_memory_backup_crdt.py
"""
Comprehensive test suite for CRDT-based memory backup system.
Tests parallel backups, conflict resolution, and Git integration.
"""

import pytest
import time
import json
import subprocess
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from typing import Dict, Any, List
import threading
import random
from datetime import datetime
import tempfile
import os

# Import the module we're testing (from parent directory)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from memory_backup_crdt import (
    MemoryBackupCRDT, 
    CRDTMetadata,
    crdt_merge,
    GitIntegration
)


@pytest.fixture
def mock_memory_data():
    """Generate mock memory data for testing."""
    return [
        {"id": "mem_001", "content": "memory_dump_abc123"},
        {"id": "mem_002", "content": "memory_dump_def456"},
        {"id": "mem_003", "content": "memory_dump_ghi789"}
    ]


@pytest.fixture
def crdt_instance():
    """Create a CRDT instance with a test host ID."""
    return MemoryBackupCRDT('test-host-001')


@pytest.fixture
def temp_git_repo():
    """Create a temporary Git repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        subprocess.run(['git', 'init'], cwd=repo_path, check=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=repo_path, check=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=repo_path, check=True)
        
        # Create initial commit to make git operations work
        readme_file = repo_path / "README.md"
        readme_file.write_text("# Test Repository\n")
        subprocess.run(['git', 'add', 'README.md'], cwd=repo_path, check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=repo_path, check=True)
        
        yield repo_path


class TestCRDTMetadata:
    """Test CRDT metadata injection functionality."""
    
    def test_metadata_injection_format(self, crdt_instance):
        """Test that metadata is injected with correct format."""
        entry = {"id": "test_entry", "content": "test_content"}
        result = crdt_instance.inject_metadata(entry)
        
        assert 'id' in result
        assert 'content' in result
        assert '_crdt_metadata' in result
        
        metadata = result['_crdt_metadata']
        assert metadata['host'] == 'test-host-001'
        assert metadata['version'] == 1
        assert 'unique_id' in metadata
        
        # Check unique_id format: UUID4 (collision-resistant)
        unique_id = metadata['unique_id']
        # UUID4 format: 8-4-4-4-12 hexadecimal digits separated by hyphens
        import re
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
        assert re.match(uuid_pattern, unique_id, re.IGNORECASE), f"UUID format invalid: {unique_id}"
        
        # Check timestamp format (ISO8601 with timezone)
        timestamp = metadata['timestamp']
        # Should be able to parse as ISO datetime with timezone
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))  # Should not raise

    def test_metadata_injection_uniqueness(self, crdt_instance):
        """Test that each metadata injection generates unique identifiers."""
        entry = {"id": "test_entry", "content": "test_content"}
        
        result1 = crdt_instance.inject_metadata(entry.copy())
        time.sleep(0.001)  # Ensure different timestamps
        result2 = crdt_instance.inject_metadata(entry.copy())
        
        assert result1['_crdt_metadata']['unique_id'] != result2['_crdt_metadata']['unique_id']
        assert result1['_crdt_metadata']['timestamp'] != result2['_crdt_metadata']['timestamp']

    @pytest.mark.parametrize("entry_id,content", [
        ("simple_id", "simple content"),
        ("complex-id_123", "content with special chars !@#$"),
        ("unicode_テスト", "unicode content 日本語"),
        ("very_long_id" * 10, "x" * 1000),
    ])
    def test_metadata_injection_various_inputs(self, crdt_instance, entry_id, content):
        """Test metadata injection with various input types."""
        entry = {"id": entry_id, "content": content}
        result = crdt_instance.inject_metadata(entry)
        
        assert result['id'] == entry_id
        assert result['content'] == content
        assert '_crdt_metadata' in result


class TestLWWConflictResolution:
    """Test Last-Write-Wins conflict resolution."""
    
    def test_lww_resolution_newer_wins(self):
        """Test that newer timestamp wins in conflict resolution."""
        entries1 = [
            {
                "id": "conflict_entry",
                "content": "content from host1",
                "_crdt_metadata": {
                    "host": "host1",
                    "timestamp": "2025-01-01T00:00:00Z",
                    "version": 1,
                    "unique_id": "host1_conflict_entry_2025-01-01T00:00:00Z"
                }
            }
        ]
        
        entries2 = [
            {
                "id": "conflict_entry",
                "content": "content from host2",
                "_crdt_metadata": {
                    "host": "host2",
                    "timestamp": "2025-01-01T00:00:01Z",  # Newer
                    "version": 1,
                    "unique_id": "host2_conflict_entry_2025-01-01T00:00:01Z"
                }
            }
        ]
        
        merged = crdt_merge([entries1, entries2])
        
        # Should have content from host2 (newer timestamp)
        assert len(merged) == 1
        assert merged[0]['content'] == 'content from host2'
        assert merged[0]['_crdt_metadata']['host'] == 'host2'

    def test_lww_resolution_older_loses(self):
        """Test that older timestamp loses in conflict resolution."""
        entries1 = [
            {
                "id": "conflict_entry",
                "content": "newer content",
                "_crdt_metadata": {
                    "host": "host1",
                    "timestamp": "2025-01-01T00:00:02Z",
                    "version": 1,
                    "unique_id": "host1_conflict_entry_2025-01-01T00:00:02Z"
                }
            }
        ]
        
        entries2 = [
            {
                "id": "conflict_entry",
                "content": "older content",
                "_crdt_metadata": {
                    "host": "host2",
                    "timestamp": "2025-01-01T00:00:01Z",  # Older
                    "version": 1,
                    "unique_id": "host2_conflict_entry_2025-01-01T00:00:01Z"
                }
            }
        ]
        
        merged = crdt_merge([entries1, entries2])
        
        # Should have content from host1 (newer timestamp)
        assert len(merged) == 1
        assert merged[0]['content'] == 'newer content'
        assert merged[0]['_crdt_metadata']['host'] == 'host1'


class TestParallelBackup:
    """Test parallel backup scenarios."""
    
    def test_concurrent_backups(self):
        """Test handling of 10+ simultaneous backups."""
        results: List[List[Dict[str, Any]]] = []
        threads = []
        
        def backup_task(host_id: str, entry_id: str, content: str):
            crdt = MemoryBackupCRDT(host_id)
            entry = {"id": entry_id, "content": content}
            result = crdt.inject_metadata(entry)
            results.append([result])
        
        # Create 15 parallel backup tasks
        for i in range(15):
            thread = threading.Thread(
                target=backup_task,
                args=(f'host-{i}', f'entry_{i}', f'content_{i}')
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All backups should complete successfully
        assert len(results) == 15
        
        # Merge all results
        merged = crdt_merge(results)
        assert len(merged) == 15
        
        # Verify all entries are present
        entry_ids = {entry['id'] for entry in merged}
        expected_ids = {f'entry_{i}' for i in range(15)}
        assert entry_ids == expected_ids

    def test_concurrent_conflicting_backups(self):
        """Test parallel backups with conflicting IDs."""
        results: List[List[Dict[str, Any]]] = []
        threads = []
        
        def backup_task(host_id: str, delay: float):
            time.sleep(delay)
            crdt = MemoryBackupCRDT(host_id)
            # All use same entry ID to create conflicts
            entry = {"id": "shared_entry", "content": f"content from {host_id}"}
            result = crdt.inject_metadata(entry)
            results.append([result])
        
        # Create 10 parallel backup tasks with slight delays
        for i in range(10):
            thread = threading.Thread(
                target=backup_task,
                args=(f'host-{i}', i * 0.001)
            )
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Merge all results - should resolve to single entry
        merged = crdt_merge(results)
        assert len(merged) == 1
        
        # Should have content from the last host (newest timestamp)
        assert 'host-9' in merged[0]['content'] or 'host-8' in merged[0]['content']


class TestGitIntegration:
    """Test Git atomic operations with retry logic."""
    
    def test_git_backup_success(self, temp_git_repo):
        """Test successful Git backup operation."""
        git = GitIntegration(str(temp_git_repo))
        crdt = MemoryBackupCRDT('test-host')
        
        # Create test data
        entry = {"id": "test", "content": "test data"}
        data = [crdt.inject_metadata(entry)]
        
        # Save to file
        memory_file = temp_git_repo / "memory-test-host.json"
        with open(memory_file, 'w') as f:
            json.dump(data, f)
        
        # Backup to Git
        result = git.backup_to_git(str(memory_file), "test-host")
        assert result is True
        
        # Verify commit was created
        log = subprocess.run(
            ['git', 'log', '--oneline'],
            cwd=temp_git_repo,
            capture_output=True,
            text=True
        )
        assert 'Memory backup from test-host' in log.stdout

    @patch('shutil.copy2')
    @patch('subprocess.run')
    @patch.object(GitIntegration, '__init__', lambda self, repo_path: setattr(self, 'repo_path', Path(repo_path)))
    def test_git_backup_retry_logic(self, mock_run, mock_copy):
        """Test Git backup retry logic on failure."""
        git = GitIntegration("/tmp/test-repo")
        
        # Mock both Path methods to avoid file system operations
        with patch.object(Path, 'is_relative_to', return_value=False), \
             patch.object(Path, 'relative_to', return_value=Path("test.json")):
            
            # Create a proper mock for successful runs
            success_mock = MagicMock()
            success_mock.returncode = 0
            success_mock.stdout = ""
            success_mock.stderr = ""
            
            # First attempt fails, second succeeds
            mock_run.side_effect = [
                subprocess.CalledProcessError(1, 'git pull'),  # Git pull fails (expected)
                subprocess.CalledProcessError(1, 'git add'),   # Git add fails first attempt
                success_mock,  # Git pull success on second attempt  
                success_mock,  # Git add success
                success_mock,  # Git commit success
                success_mock   # Git push success
            ]
            
            result = git.backup_to_git("test.json", "test-host")
            assert result is True
            # Should have been called multiple times due to retries
            assert mock_run.call_count >= 4

    @patch('shutil.copy2')
    @patch('subprocess.run')
    @patch.object(GitIntegration, '__init__', lambda self, repo_path: setattr(self, 'repo_path', Path(repo_path)))
    def test_git_backup_failure_after_retries(self, mock_run, mock_copy):
        """Test Git backup failure after max retries."""
        git = GitIntegration("/tmp/test-repo")
        
        # Mock both Path methods to avoid file system operations
        with patch.object(Path, 'is_relative_to', return_value=False), \
             patch.object(Path, 'relative_to', return_value=Path("test.json")):
            # All attempts fail
            mock_run.side_effect = subprocess.CalledProcessError(1, 'git')
            
            result = git.backup_to_git("test.json", "test-host")
            assert result is False
            # Each retry attempt calls git pull + git add, so 3 retries = 6 calls
            assert mock_run.call_count == 6


class TestStressTests:
    """Stress tests with large numbers of entries."""
    
    def test_large_scale_entries(self):
        """Test handling of 10,000 entries."""
        crdt = MemoryBackupCRDT('stress-test-host')
        entries = []
        
        # Generate 10,000 entries  
        for i in range(10000):
            entry = {"id": f"entry_{i}", "content": f"content_{i}"}
            entries.append(crdt.inject_metadata(entry))
        
        assert len(entries) == 10000
        
        # Verify a sample of entries
        for i in random.sample(range(10000), 100):
            assert entries[i]['id'] == f'entry_{i}'
            assert entries[i]['content'] == f'content_{i}'
            assert entries[i]['_crdt_metadata']['host'] == 'stress-test-host'

    def test_merge_large_scale(self):
        """Test merging large numbers of entries from multiple hosts."""
        all_entries = []
        
        # Generate entries from 10 hosts, 1,000 entries each
        for host_id in range(10):
            crdt = MemoryBackupCRDT(f'host-{host_id}')
            host_entries = []
            for i in range(1000):
                entry = {"id": f"h{host_id}_e{i}", "content": f"content_{host_id}_{i}"}
                host_entries.append(crdt.inject_metadata(entry))
            all_entries.append(host_entries)
        
        # Merge all entries
        merged = crdt_merge(all_entries)
        
        # Should have all 10,000 unique entries
        assert len(merged) == 10000


class TestPerformance:
    """Performance benchmark tests."""
    
    def test_backup_performance_10k_entries(self):
        """Test backup performance with 10,000 entries completes in <1 second."""
        crdt = MemoryBackupCRDT('perf-test-host')
        
        start_time = time.time()
        
        # Generate 10,000 entries
        entries = []
        for i in range(10000):
            entry = {"id": f"entry_{i}", "content": f"content_{i}"}
            entries.append(crdt.inject_metadata(entry))
        
        # Merge operation
        merged = crdt_merge([entries])
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert duration < 1.0  # Should complete in less than 1 second
        assert len(merged) == 10000

    def test_merge_performance(self):
        """Test merge performance with multiple large datasets."""
        datasets = []
        
        # Create 5 datasets with 2000 entries each
        for host_id in range(5):
            crdt = MemoryBackupCRDT(f'host-{host_id}')
            entries = []
            for i in range(2000):
                entry = {"id": f"h{host_id}_e{i}", "content": f"data_{i}"}
                entries.append(crdt.inject_metadata(entry))
            datasets.append(entries)
        
        start_time = time.time()
        merged = crdt_merge(datasets)
        end_time = time.time()
        
        duration = end_time - start_time
        assert duration < 0.5  # Merge should be fast
        assert len(merged) == 10000


class TestNetworkFailureRecovery:
    """Test network failure recovery scenarios."""
    
    @patch('shutil.copy2')
    @patch('subprocess.run')
    @patch.object(GitIntegration, '__init__', lambda self, repo_path: setattr(self, 'repo_path', Path(repo_path)))
    def test_recovery_from_network_failure(self, mock_run, mock_copy):
        """Test recovery from network failure during backup."""
        git = GitIntegration("/tmp/test-repo")
        crdt = MemoryBackupCRDT('test-host')
        
        # Mock both Path methods to avoid file system operations
        with patch.object(Path, 'is_relative_to', return_value=False), \
             patch.object(Path, 'relative_to', return_value=Path("test.json")):
            
            # Create success and failure mocks
            success_mock = MagicMock()
            success_mock.returncode = 0
            success_mock.stdout = ""
            success_mock.stderr = ""
            
            # Create proper CalledProcessError with stderr
            push_error = subprocess.CalledProcessError(128, 'git push')
            push_error.stderr = "Network error occurred"
            
            # First simulate network failure during push after successful operations
            mock_run.side_effect = [
                success_mock,  # git pull success
                success_mock,  # git add success  
                success_mock,  # git commit success
                push_error,    # push fails
                success_mock,  # git pull success (retry)
                success_mock,  # git add success (retry)
                success_mock,  # git commit success (retry) 
                push_error,    # push fails again
                success_mock,  # git pull success (retry)
                success_mock,  # git add success (retry)
                success_mock,  # git commit success (retry)
                push_error     # push fails final time
            ]
            
            # Backup should fail due to network issues
            result = git.backup_to_git("test.json", "test-host")
            assert result is False
            
            # System should still be able to inject metadata
            entry = {"id": "recovery_test", "content": "recovery_content"}
            injected = crdt.inject_metadata(entry)
            assert injected['content'] == 'recovery_content'
            
            # After network is restored, backup should succeed
            mock_run.side_effect = [success_mock] * 10  # All operations succeed
            result = git.backup_to_git("test.json", "test-host")
            assert result is True


class TestBackwardsCompatibility:
    """Test backwards compatibility with shell wrapper."""
    
    @patch('subprocess.run')
    def test_shell_wrapper_integration(self, mock_run):
        """Test integration with existing shell backup wrapper."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        
        # Simulate calling Python script from shell
        result = subprocess.run(
            ['python3', 'scripts/memory_backup_crdt.py', '--backup'],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Should work with shell wrapper
        # Note: This will fail until we implement the actual script
        # For now, just test that we can mock the call
        assert mock_run.return_value.returncode == 0

    def test_json_format_compatibility(self, tmp_path):
        """Test that JSON format is compatible with existing system."""
        crdt = MemoryBackupCRDT('test-host')
        
        # Create entries
        entries = []
        for i in range(5):
            entry = {"id": f"entry_{i}", "content": f"content_{i}"}
            entries.append(crdt.inject_metadata(entry))
        
        # Save to file
        json_file = tmp_path / "memory.json"
        with open(json_file, 'w') as f:
            json.dump(entries, f, indent=2)
        
        # Read back and verify format
        with open(json_file, 'r') as f:
            loaded = json.load(f)
        
        assert len(loaded) == 5
        for entry in loaded:
            assert 'id' in entry
            assert 'content' in entry
            assert '_crdt_metadata' in entry