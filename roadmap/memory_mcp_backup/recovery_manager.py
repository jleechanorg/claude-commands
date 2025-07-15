#!/usr/bin/env python3
"""
Recovery manager for Memory MCP backup system.
Handles corruption detection, backup restoration, and data validation.
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List
import time
from atomic_writer import AtomicJSONWriter

class RecoveryManager:
    """Manages recovery operations for Memory MCP data."""
    
    def __init__(self, memory_file: str = "~/.cache/mcp-memory/memory.json"):
        self.memory_file = Path(memory_file).expanduser()
        self.writer = AtomicJSONWriter(str(self.memory_file))
    
    def validate_memory_structure(self, data: Dict[Any, Any]) -> List[str]:
        """
        Validate memory data structure.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required top-level keys
        required_keys = ['entities', 'relations']
        for key in required_keys:
            if key not in data:
                errors.append(f"Missing required key: {key}")
        
        # Validate entities structure
        if 'entities' in data:
            if not isinstance(data['entities'], list):
                errors.append("'entities' must be a list")
            else:
                for i, entity in enumerate(data['entities']):
                    if not isinstance(entity, dict):
                        errors.append(f"Entity {i} must be a dictionary")
                        continue
                    
                    # Check required entity fields
                    required_fields = ['name', 'type', 'observations']
                    for field in required_fields:
                        if field not in entity:
                            errors.append(f"Entity {i} missing required field: {field}")
                    
                    # Validate observations
                    if 'observations' in entity and not isinstance(entity['observations'], list):
                        errors.append(f"Entity {i} observations must be a list")
        
        # Validate relations structure
        if 'relations' in data:
            if not isinstance(data['relations'], list):
                errors.append("'relations' must be a list")
            else:
                for i, relation in enumerate(data['relations']):
                    if not isinstance(relation, dict):
                        errors.append(f"Relation {i} must be a dictionary")
                        continue
                    
                    # Check required relation fields
                    required_fields = ['from', 'to', 'type']
                    for field in required_fields:
                        if field not in relation:
                            errors.append(f"Relation {i} missing required field: {field}")
        
        return errors
    
    def check_file_integrity(self) -> Dict[str, Any]:
        """
        Check integrity of memory file.
        
        Returns:
            Dictionary with integrity status and details
        """
        result = {
            'exists': False,
            'readable': False,
            'valid_json': False,
            'valid_structure': False,
            'checksum_valid': False,
            'errors': [],
            'size': 0
        }
        
        try:
            # Check if file exists
            if not self.memory_file.exists():
                result['errors'].append("Memory file does not exist")
                return result
            
            result['exists'] = True
            result['size'] = self.memory_file.stat().st_size
            
            # Check if file is readable
            try:
                with open(self.memory_file, 'r') as f:
                    content = f.read()
                result['readable'] = True
            except Exception as e:
                result['errors'].append(f"Cannot read file: {e}")
                return result
            
            # Check if valid JSON
            try:
                data = json.loads(content)
                result['valid_json'] = True
            except json.JSONDecodeError as e:
                result['errors'].append(f"Invalid JSON: {e}")
                return result
            
            # Check structure validity
            structure_errors = self.validate_memory_structure(data)
            if not structure_errors:
                result['valid_structure'] = True
            else:
                result['errors'].extend(structure_errors)
            
            # Check checksum
            result['checksum_valid'] = self.writer.verify_integrity()
            if not result['checksum_valid']:
                result['errors'].append("Checksum validation failed")
            
        except Exception as e:
            result['errors'].append(f"Unexpected error: {e}")
        
        return result
    
    def list_recovery_options(self) -> List[Dict[str, Any]]:
        """List available recovery options."""
        options = []
        
        # Check backups
        backups = self.writer.list_backups()
        for backup in backups:
            backup_path = Path(backup['path'])
            integrity = self._check_backup_integrity(backup_path)
            options.append({
                'type': 'backup',
                'path': backup['path'],
                'timestamp': backup['timestamp'],
                'created': backup['created'],
                'size': backup['size'],
                'integrity': integrity
            })
        
        # Check for empty/reset option
        options.append({
            'type': 'reset',
            'description': 'Reset to empty memory structure',
            'integrity': {'valid': True, 'errors': []}
        })
        
        return options
    
    def _check_backup_integrity(self, backup_path: Path) -> Dict[str, Any]:
        """Check integrity of a backup file."""
        try:
            with open(backup_path, 'r') as f:
                content = f.read()
            
            data = json.loads(content)
            errors = self.validate_memory_structure(data)
            
            return {
                'valid': len(errors) == 0,
                'errors': errors
            }
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Cannot validate backup: {e}"]
            }
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """
        Restore memory from backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            bool: True if successful
        """
        try:
            # Validate backup first
            backup_file = Path(backup_path)
            if not backup_file.exists():
                print(f"Backup file not found: {backup_path}")
                return False
            
            with open(backup_file, 'r') as f:
                data = json.load(f)
            
            # Validate structure
            errors = self.validate_memory_structure(data)
            if errors:
                print(f"Backup validation failed: {errors}")
                return False
            
            # Restore using atomic writer
            if self.writer.write(data):
                print(f"Successfully restored from {backup_path}")
                return True
            else:
                print("Failed to write restored data")
                return False
                
        except Exception as e:
            print(f"Error restoring from backup: {e}")
            return False
    
    def reset_memory(self) -> bool:
        """Reset memory to empty structure."""
        empty_memory = {
            'entities': [],
            'relations': [],
            'metadata': {
                'created': time.time(),
                'reset': True
            }
        }
        
        if self.writer.write(empty_memory):
            print("Memory reset to empty structure")
            return True
        else:
            print("Failed to reset memory")
            return False

def main():
    parser = argparse.ArgumentParser(description='Memory MCP Recovery Manager')
    parser.add_argument('--memory-file', default='~/.cache/mcp-memory/memory.json',
                       help='Path to memory file')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check file integrity')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List recovery options')
    
    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore from backup')
    restore_parser.add_argument('backup_path', help='Path to backup file')
    
    # Reset command
    reset_parser = subparsers.add_parser('reset', help='Reset to empty memory')
    reset_parser.add_argument('--confirm', action='store_true', 
                            help='Confirm reset operation')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    recovery = RecoveryManager(args.memory_file)
    
    if args.command == 'check':
        integrity = recovery.check_file_integrity()
        print(f"File exists: {integrity['exists']}")
        print(f"Readable: {integrity['readable']}")
        print(f"Valid JSON: {integrity['valid_json']}")
        print(f"Valid structure: {integrity['valid_structure']}")
        print(f"Checksum valid: {integrity['checksum_valid']}")
        print(f"File size: {integrity['size']} bytes")
        
        if integrity['errors']:
            print("\nErrors:")
            for error in integrity['errors']:
                print(f"  - {error}")
        
        # Overall status
        is_healthy = (integrity['exists'] and integrity['readable'] and 
                     integrity['valid_json'] and integrity['valid_structure'])
        print(f"\nOverall status: {'HEALTHY' if is_healthy else 'CORRUPTED'}")
    
    elif args.command == 'list':
        options = recovery.list_recovery_options()
        print("Available recovery options:")
        
        backups = [opt for opt in options if opt['type'] == 'backup']
        if backups:
            print(f"\nBackups ({len(backups)} available):")
            for i, backup in enumerate(backups, 1):
                status = "VALID" if backup['integrity']['valid'] else "CORRUPTED"
                print(f"  {i}. {backup['created']} - {status}")
                print(f"     Path: {backup['path']}")
                print(f"     Size: {backup['size']} bytes")
                if backup['integrity']['errors']:
                    print(f"     Errors: {backup['integrity']['errors']}")
        else:
            print("\nNo backups available")
        
        print(f"\nOther options:")
        print(f"  - Reset to empty memory structure")
    
    elif args.command == 'restore':
        if recovery.restore_from_backup(args.backup_path):
            print("Restore completed successfully")
        else:
            print("Restore failed")
            sys.exit(1)
    
    elif args.command == 'reset':
        if not args.confirm:
            print("Warning: This will reset all memory data!")
            print("Use --confirm to proceed")
            sys.exit(1)
        
        if recovery.reset_memory():
            print("Reset completed successfully")
        else:
            print("Reset failed")
            sys.exit(1)

if __name__ == "__main__":
    main()