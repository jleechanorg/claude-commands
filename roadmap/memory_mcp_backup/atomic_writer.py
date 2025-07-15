#!/usr/bin/env python3
"""
Atomic write operations for Memory MCP backup system.
Prevents file corruption during writes by using temporary files and atomic renames.
"""

import json
import os
import tempfile
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import fcntl
import time

class AtomicJSONWriter:
    """Provides atomic write operations for JSON files with backup support."""
    
    def __init__(self, file_path: str, backup_dir: Optional[str] = None, max_backups: int = 10):
        self.file_path = Path(file_path)
        self.backup_dir = Path(backup_dir) if backup_dir else self.file_path.parent / "backups"
        self.max_backups = max_backups
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def _calculate_checksum(self, data: str) -> str:
        """Calculate SHA256 checksum of data."""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _create_backup(self) -> Optional[str]:
        """Create timestamped backup of current file."""
        if not self.file_path.exists():
            return None
            
        timestamp = int(time.time())
        backup_name = f"{self.file_path.stem}_{timestamp}.json"
        backup_path = self.backup_dir / backup_name
        
        try:
            shutil.copy2(self.file_path, backup_path)
            return str(backup_path)
        except Exception as e:
            print(f"Warning: Failed to create backup: {e}")
            return None
    
    def _cleanup_old_backups(self):
        """Remove oldest backups if exceeding max_backups limit."""
        backups = list(self.backup_dir.glob(f"{self.file_path.stem}_*.json"))
        if len(backups) <= self.max_backups:
            return
            
        # Sort by timestamp (embedded in filename)
        backups.sort(key=lambda x: int(x.stem.split('_')[-1]))
        
        # Remove oldest backups
        for backup in backups[:-self.max_backups]:
            try:
                backup.unlink()
            except Exception as e:
                print(f"Warning: Failed to remove old backup {backup}: {e}")
    
    def write(self, data: Dict[Any, Any]) -> bool:
        """
        Atomically write JSON data with backup creation.
        
        Args:
            data: Dictionary to write as JSON
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create backup of existing file
            backup_path = self._create_backup()
            
            # Serialize data
            json_data = json.dumps(data, indent=2, ensure_ascii=False)
            checksum = self._calculate_checksum(json_data)
            
            # Create temporary file in same directory (ensures same filesystem)
            temp_fd, temp_path = tempfile.mkstemp(
                suffix='.tmp',
                prefix=f"{self.file_path.stem}_",
                dir=self.file_path.parent
            )
            
            try:
                with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                    # Lock file to prevent concurrent writes
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    
                    # Write data
                    f.write(json_data)
                    f.flush()
                    os.fsync(f.fileno())  # Force write to disk
                
                # Atomic rename (only works on same filesystem)
                os.rename(temp_path, self.file_path)
                
                # Write checksum file
                checksum_path = self.file_path.with_suffix('.json.checksum')
                with open(checksum_path, 'w') as f:
                    f.write(checksum)
                
                # Cleanup old backups
                self._cleanup_old_backups()
                
                return True
                
            except Exception as e:
                # Clean up temp file on error
                try:
                    os.unlink(temp_path)
                except:
                    pass
                raise e
                
        except Exception as e:
            print(f"Error writing {self.file_path}: {e}")
            return False
    
    def verify_integrity(self) -> bool:
        """Verify file integrity using checksum."""
        try:
            if not self.file_path.exists():
                return False
                
            checksum_path = self.file_path.with_suffix('.json.checksum')
            if not checksum_path.exists():
                return True  # No checksum file, assume valid
                
            # Read stored checksum
            with open(checksum_path, 'r') as f:
                stored_checksum = f.read().strip()
            
            # Calculate current checksum
            with open(self.file_path, 'r') as f:
                current_checksum = self._calculate_checksum(f.read())
            
            return stored_checksum == current_checksum
            
        except Exception:
            return False
    
    def list_backups(self) -> list:
        """List available backups with timestamps."""
        backups = []
        for backup in self.backup_dir.glob(f"{self.file_path.stem}_*.json"):
            try:
                timestamp = int(backup.stem.split('_')[-1])
                backups.append({
                    'path': str(backup),
                    'timestamp': timestamp,
                    'created': time.ctime(timestamp),
                    'size': backup.stat().st_size
                })
            except (ValueError, IndexError):
                continue
        
        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)

# Example usage
if __name__ == "__main__":
    # Test the atomic writer
    writer = AtomicJSONWriter("~/.cache/mcp-memory/memory.json")
    
    test_data = {
        "entities": [
            {"name": "test_entity", "type": "test", "observations": ["test observation"]}
        ],
        "relations": [],
        "metadata": {"created": time.time()}
    }
    
    if writer.write(test_data):
        print("Write successful")
        print(f"Integrity check: {writer.verify_integrity()}")
        print(f"Available backups: {len(writer.list_backups())}")
    else:
        print("Write failed")