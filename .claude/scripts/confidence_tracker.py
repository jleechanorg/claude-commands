#!/usr/bin/env python3
"""
Confidence Tracking System for Learned Patterns
Tracks pattern success/failure and updates confidence scores
"""

import json
import re
from datetime import datetime
from pathlib import Path

MEMORY_FILE = Path.home() / ".cache" / "claude-learning" / "learning_memory.json"


class ConfidenceTracker:
    """Tracks and updates pattern confidence based on user feedback"""

    def __init__(self):
        self.feedback_patterns = {
            "positive": [
                r"good",
                r"great",
                r"perfect",
                r"excellent",
                r"thanks",
                r"correct",
                r"right",
                r"yes",
                r"exactly",
                r"nice",
            ],
            "negative": [
                r"wrong",
                r"incorrect",
                r"no",
                r"actually",
                r"don\'t",
                r"error",
                r"mistake",
                r"fix",
                r"change",
                r"instead",
            ],
            "correction": [
                r"don\'t.*do",
                r"use.*instead",
                r"actually.*should",
                r"prefer.*not",
                r"wrong.*should",
            ],
        }

    def detect_feedback_type(self, user_response):
        """Detect if user response is positive, negative, or correction"""
        response_lower = user_response.lower()

        # Check for corrections first (strongest signal)
        for pattern in self.feedback_patterns["correction"]:
            if re.search(pattern, response_lower):
                return "correction"

        # Count positive and negative indicators
        positive_count = sum(
            1
            for pattern in self.feedback_patterns["positive"]
            if re.search(pattern, response_lower)
        )
        negative_count = sum(
            1
            for pattern in self.feedback_patterns["negative"]
            if re.search(pattern, response_lower)
        )

        if negative_count > positive_count:
            return "negative"
        if positive_count > 0:
            return "positive"
        return "neutral"

    def update_pattern_confidence(self, pattern_ids, user_feedback):
        """Update confidence for applied patterns based on user feedback"""
        if not MEMORY_FILE.exists():
            return "No memory file found"

        try:
            with open(MEMORY_FILE) as f:
                memory = json.load(f)
        except:
            return "Error reading memory file"

        feedback_type = self.detect_feedback_type(user_feedback)

        # Confidence adjustments based on feedback
        adjustments = {
            "positive": +0.1,
            "neutral": 0.0,
            "negative": -0.15,
            "correction": -0.25,
        }

        adjustment = adjustments[feedback_type]
        updated_patterns = []

        for pattern_id in pattern_ids:
            if pattern_id in memory.get("entities", {}):
                pattern = memory["entities"][pattern_id]
                old_confidence = pattern.get("confidence", 0.5)
                new_confidence = max(0.0, min(1.0, old_confidence + adjustment))

                # Update pattern
                pattern["confidence"] = new_confidence
                pattern["last_updated"] = datetime.now().isoformat()
                pattern["applied_count"] = pattern.get("applied_count", 0) + 1

                if feedback_type in ["positive", "neutral"]:
                    pattern["success_count"] = pattern.get("success_count", 0) + 1

                # Add feedback observation
                if "feedback_history" not in pattern:
                    pattern["feedback_history"] = []

                pattern["feedback_history"].append(
                    {
                        "feedback_type": feedback_type,
                        "adjustment": adjustment,
                        "timestamp": datetime.now().isoformat(),
                        "user_text": user_feedback[:100],  # Store snippet
                    }
                )

                updated_patterns.append(
                    {
                        "id": pattern_id,
                        "old_confidence": old_confidence,
                        "new_confidence": new_confidence,
                        "feedback_type": feedback_type,
                    }
                )

        # Save updated memory
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f, indent=2)

        return self._format_confidence_update_report(updated_patterns, feedback_type)

    def _format_confidence_update_report(self, updated_patterns, feedback_type):
        """Format a report of confidence updates"""
        if not updated_patterns:
            return f"No patterns to update for {feedback_type} feedback"

        report = [f"📊 Confidence updated based on {feedback_type} feedback:"]

        for pattern in updated_patterns:
            change = pattern["new_confidence"] - pattern["old_confidence"]
            direction = "↗️" if change > 0 else "↘️" if change < 0 else "→"

            report.append(
                f"  {direction} Pattern {pattern['id']}: "
                f"{pattern['old_confidence']:.2f} → {pattern['new_confidence']:.2f}"
            )

        return "\n".join(report)

    def get_high_confidence_patterns(self, min_confidence=0.8, min_applications=3):
        """Get patterns that are ready for promotion to CLAUDE.md"""
        if not MEMORY_FILE.exists():
            return []

        try:
            with open(MEMORY_FILE) as f:
                memory = json.load(f)
        except:
            return []

        high_confidence = []

        for pattern_id, pattern in memory.get("entities", {}).items():
            if pattern.get("type") == "user_correction":
                confidence = pattern.get("confidence", 0.0)
                applications = pattern.get("applied_count", 0)
                success_rate = pattern.get("success_count", 0) / max(1, applications)

                if (
                    confidence >= min_confidence
                    and applications >= min_applications
                    and success_rate >= 0.7
                ):  # 70% success rate
                    high_confidence.append(
                        {
                            "id": pattern_id,
                            "confidence": confidence,
                            "applications": applications,
                            "success_rate": success_rate,
                            "pattern": pattern,
                        }
                    )

        return sorted(high_confidence, key=lambda x: x["confidence"], reverse=True)

    def get_confidence_stats(self):
        """Get overall confidence statistics"""
        if not MEMORY_FILE.exists():
            return {}

        try:
            with open(MEMORY_FILE) as f:
                memory = json.load(f)
        except:
            return {}

        patterns = [
            p
            for p in memory.get("entities", {}).values()
            if p.get("type") == "user_correction"
        ]

        if not patterns:
            return {"total_patterns": 0}

        confidences = [p.get("confidence", 0.5) for p in patterns]
        applications = [p.get("applied_count", 0) for p in patterns]

        stats = {
            "total_patterns": len(patterns),
            "avg_confidence": sum(confidences) / len(confidences),
            "high_confidence": len([c for c in confidences if c >= 0.8]),
            "medium_confidence": len([c for c in confidences if 0.5 <= c < 0.8]),
            "low_confidence": len([c for c in confidences if c < 0.5]),
            "total_applications": sum(applications),
            "patterns_ready_for_promotion": len(self.get_high_confidence_patterns()),
        }

        return stats


def track_pattern_feedback(pattern_ids, user_feedback):
    """Main function to track pattern feedback"""
    tracker = ConfidenceTracker()
    return tracker.update_pattern_confidence(pattern_ids, user_feedback)


def get_promotable_patterns():
    """Get patterns ready for CLAUDE.md promotion"""
    tracker = ConfidenceTracker()
    return tracker.get_high_confidence_patterns()


if __name__ == "__main__":
    import sys

    tracker = ConfidenceTracker()

    if len(sys.argv) > 1:
        if sys.argv[1] == "stats":
            stats = tracker.get_confidence_stats()
            print("📊 Confidence Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")

        elif sys.argv[1] == "promotable":
            patterns = tracker.get_high_confidence_patterns()
            if patterns:
                print(f"🚀 {len(patterns)} patterns ready for CLAUDE.md promotion:")
                for p in patterns:
                    print(
                        f"  • {p['id']}: {p['confidence']:.2f} confidence, {p['applications']} applications"
                    )
            else:
                print("No patterns ready for promotion yet")

        elif sys.argv[1] == "test":
            # Test feedback detection
            test_responses = [
                "That's perfect, thanks!",
                "Actually, don't use that approach",
                "Good job, works well",
                "Wrong, use X instead of Y",
            ]

            for response in test_responses:
                feedback_type = tracker.detect_feedback_type(response)
                print(f"'{response}' → {feedback_type}")

    else:
        print("Usage:")
        print("  python confidence_tracker.py stats")
        print("  python confidence_tracker.py promotable")
        print("  python confidence_tracker.py test")
