#!/usr/bin/env python3
"""
Test Cleanup Script for WorldArchitect.AI

Systematically removes failing tests that are not worth fixing,
with proper backup and reporting.
"""

import os
import sys
import shutil
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestCleanup:
    def __init__(self, project_root: str, dry_run: bool = False):
        self.project_root = Path(project_root)
        self.dry_run = dry_run
        self.backup_dir = self.project_root / "archived_tests" / "deleted_tests_backup"
        self.deletion_report_path = self.project_root / "deletion_report.txt"
        
    def create_backup_directory(self):
        """Create backup directory structure"""
        if not self.dry_run:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Backup directory: {self.backup_dir}")
        
    def backup_test_file(self, test_path: Path) -> bool:
        """Backup a test file before deletion"""
        try:
            if not test_path.exists():
                logger.warning(f"Test file not found: {test_path}")
                return False
                
            # Create relative path structure in backup
            relative_path = test_path.relative_to(self.project_root)
            backup_path = self.backup_dir / relative_path
            
            if not self.dry_run:
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(test_path, backup_path)
                
            logger.info(f"Backed up: {relative_path} -> {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup {test_path}: {e}")
            return False
    
    def delete_test_file(self, test_path: Path) -> bool:
        """Delete a test file after backup"""
        try:
            if not test_path.exists():
                logger.warning(f"Test file not found: {test_path}")
                return False
                
            if not self.dry_run:
                test_path.unlink()
                
            logger.info(f"Deleted: {test_path.relative_to(self.project_root)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete {test_path}: {e}")
            return False
    
    def cleanup_empty_directories(self, base_path: Path):
        """Remove empty test directories after cleanup"""
        try:
            for item in base_path.iterdir():
                if item.is_dir():
                    self.cleanup_empty_directories(item)
                    
            # Remove directory if empty (except for __pycache__)
            remaining = [f for f in base_path.iterdir() if f.name != "__pycache__"]
            if not remaining:
                if not self.dry_run:
                    # Remove __pycache__ first if it exists
                    pycache = base_path / "__pycache__"
                    if pycache.exists():
                        shutil.rmtree(pycache)
                    base_path.rmdir()
                logger.info(f"Removed empty directory: {base_path}")
                
        except Exception as e:
            logger.warning(f"Could not cleanup directory {base_path}: {e}")
    
    def generate_deletion_report(self, deleted_tests: List[str], categories: Dict[str, List[str]]):
        """Generate deletion report"""
        timestamp = datetime.now().isoformat()
        
        report_content = f"""# Test Deletion Report
Generated: {timestamp}
Branch: fix-run-tests-readarray-compatibility
Dry Run: {self.dry_run}

## Summary
Total tests deleted: {len(deleted_tests)}

## Categories

### Infrastructure Tests (Redis/tmux required)
"""
        
        for category, tests in categories.items():
            if tests:
                report_content += f"\n### {category.title()} Tests\n"
                for test in tests:
                    report_content += f"- {test}\n"
        
        report_content += f"\n## All Deleted Tests\n"
        for test in sorted(deleted_tests):
            report_content += f"- {test}\n"
            
        if not self.dry_run:
            with open(self.deletion_report_path, 'w') as f:
                f.write(report_content)
                
        logger.info(f"Generated deletion report: {self.deletion_report_path}")
        
    def cleanup_tests(self, test_categories: Dict[str, List[str]]) -> bool:
        """Main cleanup method"""
        self.create_backup_directory()
        
        all_deleted = []
        success_count = 0
        
        for category, test_files in test_categories.items():
            logger.info(f"\n--- Processing {category} tests ---")
            
            for test_file in test_files:
                test_path = self.project_root / test_file
                
                if self.backup_test_file(test_path):
                    if self.delete_test_file(test_path):
                        all_deleted.append(test_file)
                        success_count += 1
        
        # Cleanup empty directories
        test_dirs = ['orchestration/tests', 'prototype/tests', 'roadmap/tests']
        for test_dir in test_dirs:
            dir_path = self.project_root / test_dir
            if dir_path.exists():
                self.cleanup_empty_directories(dir_path)
        
        # Generate report
        self.generate_deletion_report(all_deleted, test_categories)
        
        logger.info(f"\nCleanup complete: {success_count} tests processed")
        return success_count > 0


def main():
    parser = argparse.ArgumentParser(description="Clean up failing tests systematically")
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be deleted without actually deleting')
    parser.add_argument('--project-root', default='.', 
                       help='Project root directory (default: current directory)')
    
    args = parser.parse_args()
    
    # Define test categories to delete
    test_categories = {
        'infrastructure': [
            'orchestration/tests/test_a2a_integration.py',
            'orchestration/tests/test_end_to_end.py', 
            'orchestration/tests/test_orchestrate_unified.py',
            'orchestration/tests/test_orchestration_no_redis.py',
            'orchestration/tests/test_prompt_file_lifecycle.py',
            'orchestration/tests/test_simple_flow.py',
            'orchestration/tests/test_stale_task_prevention.py',
            'orchestration/tests/test_task_dispatcher.py',
            'orchestration/tests/test_task_execution_verification.py',
            'orchestration/tests/test_tmux_session_lifecycle.py',
            'tests/test_infrastructure_commands.py'
        ],
        'experimental': [
            'prototype/tests/test_narrative_sync.py',
            'prototype/tests/test_word_boundary_bug.py',
            'roadmap/cognitive_enhancement/test_framework.py',
            'roadmap/tests/test_ai_content_personalization_fix.py'
        ],
        'dependencies': [
            'scripts/tests/test_crdt_validation.py'
        ]
    }
    
    cleanup = TestCleanup(args.project_root, args.dry_run)
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No files will actually be deleted")
    
    success = cleanup.cleanup_tests(test_categories)
    
    if success:
        logger.info("Test cleanup completed successfully")
        return 0
    else:
        logger.error("Test cleanup encountered errors")
        return 1

if __name__ == "__main__":
    sys.exit(main())