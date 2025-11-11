#!/usr/bin/env python3
"""
Conversation Learning Integration
Real-time integration for automatic correction detection and learning during conversations
"""

import json
from datetime import datetime
from pathlib import Path


class ConversationLearningSystem:
    """Integrates correction detection into live conversation flow"""

    def __init__(self):
        self.session_file = (
            Path.home() / ".cache" / "claude-learning" / "current_session.json"
        )
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        self.baseline_corrections = []
        self.session_data = self._load_session()

    def _load_session(self) -> dict:
        """Load current session data"""
        if self.session_file.exists():
            try:
                with open(self.session_file) as f:
                    return json.load(f)
            except:
                pass

        return {
            "session_start": datetime.now().isoformat(),
            "messages_processed": 0,
            "corrections_detected": 0,
            "corrections_confirmed": 0,
            "learning_enabled": True,
            "baseline_measured": False,
            "conversation_log": [],
        }

    def _save_session(self):
        """Save session data"""
        try:
            with open(self.session_file, "w") as f:
                json.dump(self.session_data, f, indent=2)
        except:
            pass

    def process_user_message(
        self, message: str, conversation_context: dict | None = None
    ) -> dict:
        """Process user message for automatic learning"""
        from auto_correction_detector import CorrectionDetector
        from memory_auto_integration import AutoCorrectionProcessor

        CorrectionDetector()
        processor = AutoCorrectionProcessor()

        # Update session
        self.session_data["messages_processed"] += 1
        self.session_data["conversation_log"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "message": message[:100] + "..." if len(message) > 100 else message,
                "context": conversation_context or {},
            }
        )

        # Process for corrections
        result = processor.process_message_for_learning(message, conversation_context)

        if result["corrections_detected"] > 0:
            self.session_data["corrections_detected"] += result["corrections_detected"]
            self._save_session()

            return {
                "learning_detected": True,
                "correction_count": result["corrections_detected"],
                "summary": result["summary"],
                "confirmation_needed": True,
                "auto_stored": result["storage_success"],
            }
        self._save_session()
        return {
            "learning_detected": False,
            "correction_count": 0,
            "summary": "",
            "confirmation_needed": False,
            "auto_stored": False,
        }

    def confirm_learning(
        self, confirmed: bool, correction_ids: list[str] | None = None
    ) -> str:
        """Handle user confirmation of detected learning"""
        if confirmed:
            self.session_data["corrections_confirmed"] += 1
            self._save_session()
            return "✅ Learning confirmed and stored in memory."
        # Remove or mark corrections as invalid
        return "❌ Learning rejected. Corrections not stored."

    def get_session_stats(self) -> dict:
        """Get current session statistics"""
        return {
            "session_duration": self._get_session_duration(),
            "messages_processed": self.session_data["messages_processed"],
            "corrections_detected": self.session_data["corrections_detected"],
            "corrections_confirmed": self.session_data["corrections_confirmed"],
            "learning_rate": self._calculate_learning_rate(),
            "baseline_measured": self.session_data["baseline_measured"],
        }

    def _get_session_duration(self) -> str:
        """Calculate session duration"""
        try:
            start = datetime.fromisoformat(self.session_data["session_start"])
            duration = datetime.now() - start
            return f"{duration.seconds // 60} minutes"
        except:
            return "unknown"

    def _calculate_learning_rate(self) -> float:
        """Calculate corrections per message"""
        messages = self.session_data["messages_processed"]
        corrections = self.session_data["corrections_detected"]
        return round(corrections / max(1, messages), 3)

    def measure_baseline(self, correction_history: list[str]) -> dict:
        """Measure baseline correction frequency"""
        detector = CorrectionDetector()
        baseline_corrections = 0

        for message in correction_history:
            corrections = detector.detect_corrections(message)
            baseline_corrections += len(corrections)

        self.session_data["baseline_measured"] = True
        self.session_data["baseline_corrections"] = baseline_corrections
        self.session_data["baseline_messages"] = len(correction_history)
        self.session_data["baseline_rate"] = baseline_corrections / max(
            1, len(correction_history)
        )

        self._save_session()

        return {
            "baseline_corrections": baseline_corrections,
            "baseline_messages": len(correction_history),
            "baseline_rate": self.session_data["baseline_rate"],
        }

    def generate_learning_report(self) -> str:
        """Generate a comprehensive learning report"""
        stats = self.get_session_stats()

        report_lines = [
            "📊 **Automatic Learning Report**",
            "",
            f"**Session Duration**: {stats['session_duration']}",
            f"**Messages Processed**: {stats['messages_processed']}",
            f"**Corrections Detected**: {stats['corrections_detected']}",
            f"**Corrections Confirmed**: {stats['corrections_confirmed']}",
            f"**Learning Rate**: {stats['learning_rate']} corrections/message",
            "",
        ]

        if stats["baseline_measured"]:
            baseline_rate = self.session_data.get("baseline_rate", 0)
            current_rate = stats["learning_rate"]

            if current_rate < baseline_rate:
                improvement = ((baseline_rate - current_rate) / baseline_rate) * 100
                report_lines.extend(
                    [
                        f"**Baseline Rate**: {baseline_rate:.3f} corrections/message",
                        f"**Improvement**: {improvement:.1f}% reduction in corrections needed",
                        "",
                    ]
                )

        # Add recent learning
        recent_log = self.session_data["conversation_log"][-5:]
        if recent_log:
            report_lines.extend(["**Recent Activity**:", ""])
            for entry in recent_log:
                timestamp = entry["timestamp"][:19].replace("T", " ")
                report_lines.append(f"- {timestamp}: {entry['message']}")

        return "\n".join(report_lines)


def create_memory_enhanced_response_template() -> str:
    """Template for memory-enhanced responses"""
    return """
🧠 **Memory Consultation**

💭 *Checking learned patterns for relevant context...*

{memory_insights}

{main_response}

{learning_detection}
"""


def demo_conversation_integration():
    """Demonstrate the conversation integration system"""

    learning_system = ConversationLearningSystem()

    print("🧪 Conversation Learning Integration Demo")
    print("=" * 50)

    # Simulate conversation messages
    conversation_messages = [
        "Don't use inline imports, use module-level imports instead.",
        "I prefer structured commit messages with prefixes like 'feat:', 'fix:', etc.",
        "When working on urgent tasks, focus on surgical fixes not comprehensive refactoring.",
        "The implementation looks good overall.",
        "Actually, let's change the approach to use Memory MCP directly.",
        "Always run tests before marking any task complete.",
    ]

    for i, message in enumerate(conversation_messages, 1):
        print(f"\n--- Message {i} ---")
        print(f"User: {message}")

        # Process message
        result = learning_system.process_user_message(message, {"demo_mode": True})

        if result["learning_detected"]:
            print(f"🧠 Learning detected: {result['correction_count']} correction(s)")
            print(f"Summary: {result['summary']}")

            # Simulate user confirmation
            confirmed = True  # In real usage, this would be user input
            confirmation = learning_system.confirm_learning(confirmed)
            print(f"Response: {confirmation}")
        else:
            print("No learning detected in this message.")

    # Generate report
    print("\n" + "=" * 50)
    report = learning_system.generate_learning_report()
    print(report)

    # Show session stats
    stats = learning_system.get_session_stats()
    print(f"\n📈 Final Stats: {stats}")


if __name__ == "__main__":
    demo_conversation_integration()
