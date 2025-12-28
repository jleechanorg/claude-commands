#!/usr/bin/env python3
"""
A2A Monitor for WorldArchitect.AI Orchestrator

Monitors A2A system health, cleans up stale registrations,
and provides system status reporting.
"""

# Allow direct script execution - add parent directory to sys.path
import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import json
import logging
import threading
import time
from pathlib import Path
from typing import Any

# Use absolute imports with package name for __main__ compatibility
from orchestration.a2a_integration import A2A_BASE_DIR, AgentRegistry, TaskPool

logger = logging.getLogger(__name__)


class A2AMonitor:
    """Monitors A2A system health and maintains system state"""

    def __init__(self, cleanup_interval: int = 300, stale_threshold: int = 120):
        """
        Initialize A2A monitor

        Args:
            cleanup_interval: How often to run cleanup (seconds)
            stale_threshold: When to consider agents stale (seconds)
        """
        self.cleanup_interval = cleanup_interval
        self.stale_threshold = stale_threshold

        self.registry = AgentRegistry()
        self.task_pool = TaskPool()

        # Threading control
        self._running = False
        self._monitor_thread = None

        # Statistics
        self.stats = {
            "start_time": time.time(),
            "cleanup_runs": 0,
            "agents_cleaned": 0,
            "tasks_cleaned": 0,
            "last_cleanup": None,
        }

        logger.info("A2A Monitor initialized")

    def start(self) -> None:
        """Start monitoring in background thread"""
        if self._running:
            return

        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, name="A2A-Monitor", daemon=True)
        self._monitor_thread.start()
        logger.info("A2A Monitor started")

    def stop(self) -> None:
        """Stop monitoring"""
        self._running = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=10)
        logger.info("A2A Monitor stopped")

    def _monitor_loop(self) -> None:
        """Main monitoring loop"""
        while self._running:
            try:
                self._run_cleanup()
                self._update_stats()

                # Sleep until next cleanup
                time.sleep(self.cleanup_interval)

            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(60)  # Back off on error

    def _run_cleanup(self) -> None:
        """Run system cleanup operations"""
        logger.info("Running A2A system cleanup")

        cleanup_start = time.time()
        agents_cleaned = 0
        tasks_cleaned = 0

        try:
            # Clean up stale agents
            agents_cleaned = self._cleanup_stale_agents()

            # Clean up orphaned tasks
            tasks_cleaned = self._cleanup_orphaned_tasks()

            # Clean up old message files
            self._cleanup_old_messages()

            # Update statistics
            self.stats["cleanup_runs"] += 1
            self.stats["agents_cleaned"] += agents_cleaned
            self.stats["tasks_cleaned"] += tasks_cleaned
            self.stats["last_cleanup"] = time.time()

            cleanup_time = time.time() - cleanup_start
            logger.info(
                f"Cleanup completed in {cleanup_time:.2f}s: {agents_cleaned} agents, {tasks_cleaned} tasks cleaned"
            )

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def _cleanup_stale_agents(self) -> int:
        """Remove agents that haven't sent heartbeat recently"""
        current_time = time.time()
        agents_cleaned = 0

        try:
            # Load current registry
            registry_data = self.registry._load_registry()

            stale_agents = []
            for agent_id, agent_data in registry_data.items():
                last_heartbeat = agent_data.get("last_heartbeat", 0)

                if current_time - last_heartbeat > self.stale_threshold:
                    stale_agents.append(agent_id)

            # Remove stale agents
            for agent_id in stale_agents:
                self.registry.unregister_agent(agent_id)
                self._cleanup_agent_directory(agent_id)
                agents_cleaned += 1
                logger.info(f"Cleaned up stale agent: {agent_id}")

        except Exception as e:
            logger.error(f"Error cleaning up stale agents: {e}")

        return agents_cleaned

    def _cleanup_agent_directory(self, agent_id: str) -> None:
        """Clean up agent's directory and files"""
        try:
            agent_dir = Path(A2A_BASE_DIR) / "agents" / agent_id
            if agent_dir.exists():
                # Move to cleanup directory instead of deleting
                cleanup_dir = Path(A2A_BASE_DIR) / "cleanup" / f"agent_{agent_id}_{int(time.time())}"
                cleanup_dir.parent.mkdir(parents=True, exist_ok=True)
                agent_dir.rename(cleanup_dir)
                logger.info(f"Moved stale agent directory to cleanup: {cleanup_dir}")
        except Exception as e:
            logger.error(f"Error cleaning up agent directory {agent_id}: {e}")

    def _cleanup_orphaned_tasks(self) -> int:
        """Remove tasks claimed by agents that no longer exist"""
        tasks_cleaned = 0

        try:
            # Get current active agents
            active_agents = set(self.registry._load_registry().keys())

            # Check claimed tasks
            claimed_dir = Path(A2A_BASE_DIR) / "tasks" / "claimed"
            if claimed_dir.exists():
                for task_file in claimed_dir.glob("*.json"):
                    try:
                        with open(task_file) as f:
                            task_data = json.load(f)

                        claimed_by = task_data.get("claimed_by")
                        if claimed_by and claimed_by not in active_agents:
                            # Move back to available tasks
                            task_id = task_data["task_id"]
                            task_data["status"] = "available"
                            task_data.pop("claimed_by", None)
                            task_data.pop("claimed_at", None)

                            available_file = Path(A2A_BASE_DIR) / "tasks" / "available" / f"{task_id}.json"
                            with open(available_file, "w") as f:
                                json.dump(task_data, f, indent=2)

                            task_file.unlink()
                            tasks_cleaned += 1
                            logger.info(f"Restored orphaned task to available pool: {task_id}")

                    except Exception as e:
                        logger.error(f"Error processing task file {task_file}: {e}")

        except Exception as e:
            logger.error(f"Error cleaning up orphaned tasks: {e}")

        return tasks_cleaned

    def _cleanup_old_messages(self) -> None:
        """Clean up old processed messages"""
        try:
            agents_dir = Path(A2A_BASE_DIR) / "agents"
            if not agents_dir.exists():
                return

            cutoff_time = time.time() - (1 * 3600)  # 1 hour (was 24 hours)

            for agent_dir in agents_dir.iterdir():
                if not agent_dir.is_dir():
                    continue

                processed_dir = agent_dir / "inbox" / "processed"
                if processed_dir.exists():
                    for message_file in processed_dir.glob("*.json"):
                        if message_file.stat().st_mtime < cutoff_time:
                            message_file.unlink()

        except Exception as e:
            logger.error(f"Error cleaning up old messages: {e}")

    def _update_stats(self) -> None:
        """Update monitoring statistics"""
        try:
            # Save stats to file
            stats_file = Path(A2A_BASE_DIR) / "logs" / "monitor_stats.json"
            stats_file.parent.mkdir(parents=True, exist_ok=True)

            with open(stats_file, "w") as f:
                json.dump(self.stats, f, indent=2)

        except Exception as e:
            logger.error(f"Error updating stats: {e}")

    def get_system_health(self) -> dict[str, Any]:
        """Get comprehensive system health report"""
        try:
            # Get agent information
            registry_data = self.registry._load_registry()
            current_time = time.time()

            active_agents = []
            stale_agents = []

            for agent_id, agent_data in registry_data.items():
                last_heartbeat = agent_data.get("last_heartbeat", 0)

                if current_time - last_heartbeat <= self.stale_threshold:
                    active_agents.append(
                        {
                            "agent_id": agent_id,
                            "agent_type": agent_data.get("agent_type"),
                            "status": agent_data.get("status"),
                            "last_heartbeat": last_heartbeat,
                            "heartbeat_age": current_time - last_heartbeat,
                        }
                    )
                else:
                    stale_agents.append(
                        {
                            "agent_id": agent_id,
                            "last_heartbeat": last_heartbeat,
                            "heartbeat_age": current_time - last_heartbeat,
                        }
                    )

            # Get task information
            available_tasks = self.task_pool.get_available_tasks()

            # Count claimed tasks
            claimed_dir = Path(A2A_BASE_DIR) / "tasks" / "claimed"
            claimed_count = len(list(claimed_dir.glob("*.json"))) if claimed_dir.exists() else 0

            # Count completed tasks
            completed_dir = Path(A2A_BASE_DIR) / "tasks" / "completed"
            completed_count = len(list(completed_dir.glob("*.json"))) if completed_dir.exists() else 0

            return {
                "timestamp": current_time,
                "uptime": current_time - self.stats["start_time"],
                "agents": {
                    "active": len(active_agents),
                    "stale": len(stale_agents),
                    "active_list": active_agents,
                    "stale_list": stale_agents,
                },
                "tasks": {
                    "available": len(available_tasks),
                    "claimed": claimed_count,
                    "completed": completed_count,
                    "available_list": available_tasks,
                },
                "monitor_stats": self.stats.copy(),
                "a2a_directory": A2A_BASE_DIR,
                "health_status": "healthy" if len(stale_agents) == 0 else "warning",
            }

        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {"timestamp": time.time(), "error": str(e), "health_status": "error"}

    def get_agent_status(self, agent_id: str) -> dict[str, Any | None]:
        """Get detailed status for specific agent"""
        try:
            registry_data = self.registry._load_registry()
            if agent_id not in registry_data:
                return None

            agent_data = registry_data[agent_id].copy()
            current_time = time.time()
            last_heartbeat = agent_data.get("last_heartbeat", 0)

            agent_data["heartbeat_age"] = current_time - last_heartbeat
            agent_data["is_stale"] = agent_data["heartbeat_age"] > self.stale_threshold

            # Check for agent's tasks
            claimed_dir = Path(A2A_BASE_DIR) / "tasks" / "claimed"
            agent_tasks = []

            if claimed_dir.exists():
                for task_file in claimed_dir.glob(f"*_{agent_id}.json"):
                    try:
                        with open(task_file) as f:
                            task_data = json.load(f)
                            agent_tasks.append(task_data)
                    except Exception as e:
                        logger.error(f"Error reading task file {task_file}: {e}")

            agent_data["current_tasks"] = agent_tasks
            agent_data["task_count"] = len(agent_tasks)

            return agent_data

        except Exception as e:
            logger.error(f"Error getting agent status for {agent_id}: {e}")
            return None

    def force_cleanup(self) -> dict[str, int]:
        """Force immediate cleanup and return results"""
        logger.info("Force cleanup requested")

        agents_cleaned = self._cleanup_stale_agents()
        tasks_cleaned = self._cleanup_orphaned_tasks()
        self._cleanup_old_messages()

        return {
            "agents_cleaned": agents_cleaned,
            "tasks_cleaned": tasks_cleaned,
            "timestamp": time.time(),
        }


# Global monitor instance
_global_monitor = None


def get_monitor() -> A2AMonitor:
    """Get or create global monitor instance"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = A2AMonitor()
        _global_monitor.start()
    return _global_monitor


def get_system_health() -> dict[str, Any]:
    """Get system health from global monitor"""
    return get_monitor().get_system_health()


def get_agent_status(agent_id: str) -> dict[str, Any | None]:
    """Get agent status from global monitor"""
    return get_monitor().get_agent_status(agent_id)


def force_cleanup() -> dict[str, int]:
    """Force cleanup from global monitor"""
    return get_monitor().force_cleanup()


if __name__ == "__main__":
    # Test the monitor
    monitor = A2AMonitor(cleanup_interval=30, stale_threshold=60)

    try:
        monitor.start()

        # Get initial health
        health = monitor.get_system_health()
        print(f"System health: {json.dumps(health, indent=2)}")

        # Run for a bit
        time.sleep(60)

        # Force cleanup
        cleanup_result = monitor.force_cleanup()
        print(f"Cleanup result: {cleanup_result}")

    finally:
        monitor.stop()
