#!/usr/bin/env python3
"""
Context Health Monitor - SAFE context monitoring without conversation history modification
Provides context usage insights while respecting conversation history protection protocol
🚨 CRITICAL: NEVER modifies ~/.claude/projects/ directory per conversation history protection protocol
"""

import os
import glob
import shutil
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import argparse

class ContextMonitor:
    def __init__(self):
        self.projects_dir = os.path.expanduser('~/.claude/projects/')
        self.archive_base = os.path.expanduser('~/.claude/projects-archive/')
        self.config_file = os.path.expanduser('~/.claude/context_monitor.json')
        self.log_file = os.path.expanduser('~/.claude/context_monitor.log')

        # Default configuration - MONITORING ONLY (NO CLEANUP)
        self.config = {
            'max_total_size_mb': 500,         # 500MB limit (monitoring threshold only)
            'large_file_threshold_mb': 5,     # Files >5MB (reporting only)
            'retention_days': 14,             # Keep 14 days (analysis only)
            'auto_cleanup': False,            # 🚨 DISABLED: Violates conversation history protection
            'archive_compression': False,     # 🚨 DISABLED: No archival allowed
            'monitor_interval_hours': 24,     # Daily monitoring (read-only)
            'alert_threshold_mb': 400         # Alert at 400MB (warning only)
        }

        self.setup_logging()
        self.load_config()

    def setup_logging(self):
        """Configure logging for monitoring actions"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_config(self):
        """Load configuration from file if exists"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    self.config.update(user_config)
                self.logger.info(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                self.logger.warning(f"Failed to load config: {e}")

    def save_config(self):
        """Save current configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info("Configuration saved")
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")

    def get_conversation_stats(self):
        """Get current conversation history statistics"""
        if not os.path.exists(self.projects_dir):
            return {'total_files': 0, 'total_size_mb': 0, 'projects': []}

        jsonl_files = glob.glob(os.path.join(self.projects_dir, '*/*.jsonl'))
        total_size = sum(os.path.getsize(f) for f in jsonl_files)

        # Project breakdown
        project_stats = {}
        for project_dir in os.listdir(self.projects_dir):
            project_path = os.path.join(self.projects_dir, project_dir)
            if os.path.isdir(project_path):
                project_files = [f for f in os.listdir(project_path) if f.endswith('.jsonl')]
                if project_files:
                    project_size = sum(os.path.getsize(os.path.join(project_path, f)) for f in project_files)
                    project_stats[project_dir] = {
                        'files': len(project_files),
                        'size_mb': project_size / 1024 / 1024,
                        'newest': max(os.path.getmtime(os.path.join(project_path, f)) for f in project_files)
                    }

        return {
            'total_files': len(jsonl_files),
            'total_size_mb': total_size / 1024 / 1024,
            'projects': project_stats
        }

    def check_health(self):
        """Check conversation history health status"""
        stats = self.get_conversation_stats()
        total_size_mb = stats['total_size_mb']

        health_status = {
            'status': 'healthy',
            'size_mb': total_size_mb,
            'utilization_percent': (total_size_mb / self.config['max_total_size_mb']) * 100,
            'recommendation': 'No action needed',
            'urgency': 'low'
        }

        if total_size_mb >= self.config['max_total_size_mb']:
            health_status.update({
                'status': 'critical',
                'recommendation': 'Immediate cleanup required',
                'urgency': 'high'
            })
        elif total_size_mb >= self.config['alert_threshold_mb']:
            health_status.update({
                'status': 'warning',
                'recommendation': 'Cleanup recommended',
                'urgency': 'medium'
            })

        return health_status

    def auto_cleanup(self):
        """🚨 DISABLED: Violates conversation history protection protocol"""
        self.logger.warning("🚨 Auto-cleanup PERMANENTLY DISABLED: Violates conversation history protection protocol")
        self.logger.warning("❌ NEVER modify ~/.claude/projects/ directory per CLAUDE.md protection protocol")
        return False

        health = self.check_health()
        if health['status'] == 'healthy':
            self.logger.info("Context health is good, no cleanup needed")
            return False

        self.logger.info(f"Starting auto-cleanup - Status: {health['status']}")

        # Create timestamped archive directory
        archive_timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        archive_dir = os.path.join(self.archive_base, f'auto-{archive_timestamp}')
        os.makedirs(archive_dir, exist_ok=True)

        archived_size = 0
        archived_files = 0

        # Phase 1: Archive large files
        for project_dir in os.listdir(self.projects_dir):
            project_path = os.path.join(self.projects_dir, project_dir)
            if not os.path.isdir(project_path):
                continue

            for file_name in os.listdir(project_path):
                if file_name.endswith('.jsonl'):
                    file_path = os.path.join(project_path, file_name)
                    file_size = os.path.getsize(file_path)

                    if file_size > self.config['large_file_threshold_mb'] * 1024 * 1024:
                        # Move to archive
                        archive_project_dir = os.path.join(archive_dir, project_dir)
                        os.makedirs(archive_project_dir, exist_ok=True)
                        archive_file_path = os.path.join(archive_project_dir, file_name)

                        shutil.move(file_path, archive_file_path)
                        archived_size += file_size
                        archived_files += 1

        # Phase 2: Archive old files if still over limit
        stats = self.get_conversation_stats()
        if stats['total_size_mb'] > self.config['max_total_size_mb']:
            cutoff_date = datetime.now() - timedelta(days=self.config['retention_days'])

            for project_dir in os.listdir(self.projects_dir):
                project_path = os.path.join(self.projects_dir, project_dir)
                if not os.path.isdir(project_path):
                    continue

                for file_name in os.listdir(project_path):
                    if file_name.endswith('.jsonl'):
                        file_path = os.path.join(project_path, file_name)
                        file_date = datetime.fromtimestamp(os.path.getmtime(file_path))

                        if file_date < cutoff_date:
                            file_size = os.path.getsize(file_path)
                            archive_project_dir = os.path.join(archive_dir, project_dir)
                            os.makedirs(archive_project_dir, exist_ok=True)
                            archive_file_path = os.path.join(archive_project_dir, file_name)

                            shutil.move(file_path, archive_file_path)
                            archived_size += file_size
                            archived_files += 1

        self.logger.info(f"Auto-cleanup complete: {archived_files} files ({archived_size/1024/1024:.1f}MB) archived")

        # Log final stats
        final_stats = self.get_conversation_stats()
        self.logger.info(f"Final size: {final_stats['total_size_mb']:.1f}MB ({final_stats['total_files']} files)")

        return True

    def generate_report(self):
        """Generate comprehensive context health report"""
        stats = self.get_conversation_stats()
        health = self.check_health()

        report = {
            'timestamp': datetime.now().isoformat(),
            'health': health,
            'statistics': stats,
            'configuration': self.config,
            'recommendations': []
        }

        # Add recommendations based on health
        if health['status'] == 'critical':
            report['recommendations'].extend([
                'Run immediate cleanup: context_monitor.py --cleanup',
                'Review large files and archive manually',
                'Consider reducing retention period'
            ])
        elif health['status'] == 'warning':
            report['recommendations'].extend([
                'Schedule cleanup soon',
                'Monitor daily for growth patterns',
                'Review project activity'
            ])
        else:
            report['recommendations'].append('Continue monitoring')

        return report

def main():
    """Main CLI interface for context monitor"""

    parser = argparse.ArgumentParser(description='Claude Code Context Monitor')
    parser.add_argument('--check', action='store_true', help='Check context health')
    parser.add_argument('--cleanup', action='store_true', help='Run automatic cleanup')
    parser.add_argument('--report', action='store_true', help='Generate detailed report')
    parser.add_argument('--config', help='Update configuration (JSON)')

    args = parser.parse_args()
    monitor = ContextMonitor()

    if args.config:
        try:
            new_config = json.loads(args.config)
            monitor.config.update(new_config)
            monitor.save_config()
            print("Configuration updated")
        except json.JSONDecodeError:
            print("Error: Invalid JSON in config")
            return 1

    if args.check or not any(vars(args).values()):
        health = monitor.check_health()
        stats = monitor.get_conversation_stats()

        print(f"Context Health: {health['status'].upper()}")
        print(f"Size: {stats['total_size_mb']:.1f}MB / {monitor.config['max_total_size_mb']}MB ({health['utilization_percent']:.1f}%)")
        print(f"Files: {stats['total_files']:,}")
        print(f"Recommendation: {health['recommendation']}")

    if args.cleanup:
        success = monitor.auto_cleanup()
        if success:
            print("Cleanup completed successfully")
        else:
            print("No cleanup was needed")

    if args.report:
        report = monitor.generate_report()
        report_file = f"context_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"Detailed report saved to: {report_file}")

    return 0

if __name__ == '__main__':
    exit(main())
