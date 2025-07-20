#!/usr/bin/env python3
"""
Copilot Automated Conflict Resolution
====================================

Smart merge logic for automated conflict resolution with safety mechanisms:
- Auto-resolve simple formatting conflicts
- Preserve functionality while integrating features
- Handle non-overlapping changes automatically
- Backup and rollback capabilities
"""

import os
import sys
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class ConflictResolver:
    """Automated conflict resolution with safety mechanisms."""
    
    COMMON_WORDS = {'def', 'class', 'return', 'if', 'else', 'for', 'while', 'try', 'except', 'import', 'from'}
    
    def __init__(self, backup_dir: Optional[str] = None):
        self.backup_dir = backup_dir or f"/tmp/copilot_backups/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.resolved_files = []
        self.backup_map = {}
        
    def analyze_conflicts(self, conflicted_files: List[str]) -> Dict:
        """Analyze conflicts to determine resolution strategy."""
        analysis = {
            'total_files': len(conflicted_files),
            'resolvable_files': [],
            'complex_files': [],
            'analysis_per_file': {}
        }
        
        for file_path in conflicted_files:
            file_analysis = self._analyze_file_conflicts(file_path)
            analysis['analysis_per_file'][file_path] = file_analysis
            
            if file_analysis['auto_resolvable']:
                analysis['resolvable_files'].append(file_path)
            else:
                analysis['complex_files'].append(file_path)
                
        return analysis
    
    def _analyze_file_conflicts(self, file_path: str) -> Dict:
        """Analyze conflicts in a specific file."""
        analysis = {
            'auto_resolvable': False,
            'conflict_count': 0,
            'conflict_types': [],
            'complexity_score': 0,
            'safe_to_auto_resolve': False
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Find conflict markers
            conflicts = self._extract_conflicts(content)
            analysis['conflict_count'] = len(conflicts)
            
            for conflict in conflicts:
                conflict_type = self._classify_conflict(conflict)
                analysis['conflict_types'].append(conflict_type)
                
                # Calculate complexity
                if conflict_type in ['whitespace', 'formatting', 'import_order']:
                    analysis['complexity_score'] += 1  # Low complexity
                elif conflict_type in ['simple_addition', 'non_overlapping']:
                    analysis['complexity_score'] += 3  # Medium complexity
                else:
                    analysis['complexity_score'] += 10  # High complexity
            
            # Determine if auto-resolvable
            analysis['auto_resolvable'] = (
                analysis['complexity_score'] <= 5 and
                all(ct in ['whitespace', 'formatting', 'import_order', 'simple_addition'] 
                   for ct in analysis['conflict_types'])
            )
            
            analysis['safe_to_auto_resolve'] = analysis['auto_resolvable']
            
        except Exception as e:
            print(f"⚠️ Error analyzing {file_path}: {e}")
            
        return analysis
    
    def _extract_conflicts(self, content: str) -> List[Dict]:
        """Extract conflict blocks from file content."""
        conflicts = []
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('<<<<<<<'):
                # Found start of conflict
                conflict = {
                    'start_line': i,
                    'start_marker': line,
                    'ours': [],
                    'theirs': [],
                    'end_line': None
                }
                
                i += 1
                # Collect "ours" section
                while i < len(lines) and not lines[i].strip() == '=======':
                    conflict['ours'].append(lines[i])
                    i += 1
                
                if i < len(lines):
                    i += 1  # Skip separator
                    
                # Collect "theirs" section
                while i < len(lines) and not lines[i].strip().startswith('>>>>>>>'):
                    conflict['theirs'].append(lines[i])
                    i += 1
                
                if i < len(lines):
                    conflict['end_line'] = i
                    conflict['end_marker'] = lines[i].strip()
                    conflicts.append(conflict)
                
            i += 1
            
        return conflicts
    
    def _classify_conflict(self, conflict: Dict) -> str:
        """Classify the type of conflict for resolution strategy."""
        ours = '\n'.join(conflict['ours'])
        theirs = '\n'.join(conflict['theirs'])
        
        # Whitespace/formatting conflicts
        if ours.strip() == theirs.strip():
            return 'whitespace'
        
        # Import order conflicts
        if self._is_import_section(ours) and self._is_import_section(theirs):
            return 'import_order'
        
        # Simple additions (one side empty)
        if not ours.strip() and theirs.strip():
            return 'simple_addition'
        if not theirs.strip() and ours.strip():
            return 'simple_addition'
        
        # Non-overlapping changes (different parts of code)
        if self._are_non_overlapping(ours, theirs):
            return 'non_overlapping'
        
        # Default to complex
        return 'complex'
    
    def _is_import_section(self, content: str) -> bool:
        """Check if content is primarily import statements."""
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        import_lines = [line for line in lines if line.startswith(('import ', 'from '))]
        return len(import_lines) > len(lines) * 0.7  # 70% import statements
    
    def _are_non_overlapping(self, ours: str, theirs: str) -> bool:
        """Check if changes are in different parts of the code."""
        # Simple heuristic: if they don't share common keywords/identifiers
        ours_words = set(ours.split())
        theirs_words = set(theirs.split())
        common_words = ours_words & theirs_words
        
        # Exclude common words defined in the class constant
        significant_common = common_words - self.COMMON_WORDS
        
        return len(significant_common) < 3  # Less than 3 significant common words
    
    def create_backup(self, file_path: str) -> str:
        """Create backup of file before resolution."""
        try:
            Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
            backup_name = file_path.replace('/', '_')
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            shutil.copy2(file_path, backup_path)
            self.backup_map[file_path] = backup_path
            
            print(f"✅ Backup created: {file_path} → {backup_path}")
            return backup_path
        except Exception as e:
            print(f"❌ Backup failed for {file_path}: {e}")
            return ""
    
    def resolve_file(self, file_path: str) -> bool:
        """Attempt to resolve conflicts in a specific file."""
        print(f"🔧 Resolving conflicts in: {file_path}")
        
        # Create backup first
        backup_path = self.create_backup(file_path)
        if not backup_path:
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            conflicts = self._extract_conflicts(content)
            if not conflicts:
                print(f"  ℹ️ No conflicts found in {file_path}")
                return True
            
            resolved_content = self._resolve_conflicts(content, conflicts)
            
            if resolved_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(resolved_content)
                
                # Validate the resolution
                if self._validate_resolution(file_path):
                    print(f"  ✅ Successfully resolved {len(conflicts)} conflicts")
                    self.resolved_files.append(file_path)
                    return True
                else:
                    print(f"  ❌ Resolution validation failed")
                    self._rollback_file(file_path)
                    return False
            else:
                print(f"  ⚠️ Could not auto-resolve conflicts")
                return False
                
        except Exception as e:
            print(f"  ❌ Error resolving {file_path}: {e}")
            self._rollback_file(file_path)
            return False
    
    def _resolve_conflicts(self, content: str, conflicts: List[Dict]) -> Optional[str]:
        """Apply resolution strategy to conflicts."""
        lines = content.split('\n')
        resolved_lines = []
        
        current_line = 0
        
        for conflict in conflicts:
            # Add lines before conflict
            resolved_lines.extend(lines[current_line:conflict['start_line']])
            
            # Resolve the specific conflict
            resolution = self._resolve_single_conflict(conflict)
            if resolution is None:
                return None  # Cannot auto-resolve
            
            resolved_lines.extend(resolution)
            current_line = conflict['end_line'] + 1
        
        # Add remaining lines
        resolved_lines.extend(lines[current_line:])
        
        return '\n'.join(resolved_lines)
    
    def _resolve_single_conflict(self, conflict: Dict) -> Optional[List[str]]:
        """Resolve a single conflict based on its type."""
        conflict_type = self._classify_conflict(conflict)
        
        if conflict_type == 'whitespace':
            # Choose the version with better formatting
            ours = '\n'.join(conflict['ours'])
            theirs = '\n'.join(conflict['theirs'])
            return conflict['ours'] if len(ours.strip()) >= len(theirs.strip()) else conflict['theirs']
        
        elif conflict_type == 'import_order':
            # Merge and sort imports
            all_imports = conflict['ours'] + conflict['theirs']
            unique_imports = list(dict.fromkeys(all_imports))  # Remove duplicates, preserve order
            return sorted([imp for imp in unique_imports if imp.strip()])
        
        elif conflict_type == 'simple_addition':
            # Take the non-empty side
            if not '\n'.join(conflict['ours']).strip():
                return conflict['theirs']
            else:
                return conflict['ours']
        
        elif conflict_type == 'non_overlapping':
            # Merge both sides
            return conflict['ours'] + [''] + conflict['theirs']
        
        else:
            # Complex conflict - cannot auto-resolve
            return None
    
    def _validate_resolution(self, file_path: str) -> bool:
        """Validate that the resolved file is syntactically correct."""
        try:
            if file_path.endswith('.py'):
                # Python syntax check
                result = subprocess.run([sys.executable, '-m', 'py_compile', file_path],
                                      capture_output=True, text=True, timeout=30)
                return result.returncode == 0
            
            # For other files, just check that conflict markers are gone
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            has_markers = any(marker in content for marker in ['<<<<<<<', '>>>>>>>', '======='])
            return not has_markers
            
        except Exception as e:
            print(f"  ⚠️ Validation error: {e}")
            return False
    
    def _rollback_file(self, file_path: str) -> bool:
        """Rollback file to backup version."""
        backup_path = self.backup_map.get(file_path)
        if backup_path and os.path.exists(backup_path):
            try:
                shutil.copy2(backup_path, file_path)
                print(f"  🔄 Rolled back: {file_path}")
                return True
            except Exception as e:
                print(f"  ❌ Rollback failed: {e}")
        return False
    
    def run_tests_after_resolution(self) -> bool:
        """Run quick tests to validate overall system after resolution."""
        test_commands = [
            (['git', 'status', '--porcelain'], "Git status check"),
            ([sys.executable, '-m', 'py_compile'] + [f for f in self.resolved_files if f.endswith('.py')], "Python syntax check")
        ]
        
        for command, description in test_commands:
            if len(command) > 2:  # Only run if there are files to check
                try:
                    print(f"🧪 Running: {description}")
                    result = subprocess.run(command, capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0:
                        print(f"  ✅ {description} passed")
                    else:
                        print(f"  ❌ {description} failed")
                        return False
                except Exception as e:
                    print(f"  ⚠️ {description} error: {e}")
                    return False
        
        return True
    
    def generate_resolution_report(self) -> Dict:
        """Generate report of resolution actions."""
        return {
            'resolved_files': self.resolved_files,
            'backup_directory': self.backup_dir,
            'backup_map': self.backup_map,
            'total_resolved': len(self.resolved_files),
            'backup_available': len(self.backup_map) > 0
        }

def main():
    """CLI entry point for conflict resolver."""
    if len(sys.argv) < 2:
        print("Usage: python3 copilot_resolver.py <conflicted_file1> [conflicted_file2] ...")
        sys.exit(1)
    
    files = sys.argv[1:]
    resolver = ConflictResolver()
    
    print("🔧 Copilot Automated Conflict Resolution")
    print("=" * 45)
    
    # Analyze conflicts
    analysis = resolver.analyze_conflicts(files)
    print(f"📊 Analysis: {analysis['total_files']} files, {len(analysis['resolvable_files'])} auto-resolvable")
    
    # Resolve resolvable files
    success_count = 0
    for file_path in analysis['resolvable_files']:
        if resolver.resolve_file(file_path):
            success_count += 1
    
    # Run validation tests
    if success_count > 0:
        print(f"\n🧪 Running post-resolution validation...")
        if resolver.run_tests_after_resolution():
            print(f"✅ All tests passed")
        else:
            print(f"❌ Some tests failed")
    
    # Generate report
    report = resolver.generate_resolution_report()
    print(f"\n📋 Resolution Report:")
    print(f"  ✅ Resolved: {report['total_resolved']} files")
    print(f"  🔄 Backups: {report['backup_directory']}")
    
    return 0 if success_count == len(analysis['resolvable_files']) else 1

if __name__ == "__main__":
    sys.exit(main())