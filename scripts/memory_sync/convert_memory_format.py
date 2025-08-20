#!/usr/bin/env python3
"""
Secure memory format conversion utility
Converts JSONL format (backup repo) to JSON array format (MCP cache)
"""
import json
import os
import sys
import tempfile
from pathlib import Path

def validate_file_path(file_path: str) -> Path:
    """Validate file path for security"""
    path = Path(file_path).expanduser().resolve()
    
    # Ensure path is within allowed directories  
    allowed_dirs = [
        Path.home() / ".cache" / "mcp-memory",
        Path.home() / "projects" / "worldarchitect-memory-backups"
    ]
    
    # Resolve all allowed directories to prevent symlink bypass
    resolved_allowed_dirs = [allowed_dir.resolve() for allowed_dir in allowed_dirs]
    
    # Use robust path containment check
    def _is_relative_to(path, parent):
        """Compatibility function for path.is_relative_to (Python 3.9+)"""
        try:
            path.relative_to(parent)
            return True
        except ValueError:
            return False
    
    if not any(
        # Python 3.9+: path.is_relative_to(allowed_dir)
        # For compatibility, use try/except
        (
            (hasattr(path, "is_relative_to") and path.is_relative_to(allowed_dir))
            or
            (not hasattr(path, "is_relative_to") and _is_relative_to(path, allowed_dir))
        )
        for allowed_dir in resolved_allowed_dirs
    ):
        raise ValueError(f"File path not in allowed directories: {path}")
    
    return path

def convert_jsonl_to_array(source_file: str, target_file: str) -> None:
    """Securely convert JSONL to JSON array format"""
    source_path = validate_file_path(source_file)
    target_path = validate_file_path(target_file)
    
    memories = []
    
    # Read JSONL format from source
    if source_path.exists():
        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        try:
                            memories.append(json.loads(line))
                        except json.JSONDecodeError as e:
                            print(f"Warning: Skipping invalid JSON on line {line_num}: {e}", file=sys.stderr)
                            continue
        except (IOError, OSError) as e:
            print(f"Error reading source file {source_path}: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Atomic write to target using temporary file
    target_dir = target_path.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=target_dir, delete=False, encoding='utf-8') as temp_f:
            temp_path = Path(temp_f.name)
            json.dump(memories, temp_f, indent=2)
            temp_f.flush()
            os.fsync(temp_f.fileno())
        
        # Atomic move
        temp_path.replace(target_path)
        print(f"Synced {len(memories)} memories to cache")
        
    except IOError as e:
        # Cleanup on failure
        if 'temp_path' in locals() and temp_path.exists():
            temp_path.unlink()
        print(f"IOError writing target file {target_path}: {e}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        # Cleanup on failure
        if 'temp_path' in locals() and temp_path.exists():
            temp_path.unlink()
        print(f"OSError writing target file {target_path}: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: convert_memory_format.py <source_jsonl> <target_json>", file=sys.stderr)
        sys.exit(1)
    
    convert_jsonl_to_array(sys.argv[1], sys.argv[2])