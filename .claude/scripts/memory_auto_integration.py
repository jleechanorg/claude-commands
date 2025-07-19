#!/usr/bin/env python3
"""
Memory MCP Auto-Integration Pipeline
Automatically stores detected corrections in Memory MCP with fallback to local storage
"""

import json
from datetime import datetime
from pathlib import Path

# Note: In a real Claude conversation, these would be available via MCP functions
# For testing purposes, we'll simulate the Memory MCP interface


class MemoryMCPIntegration:
    """Handles automatic storage of corrections in Memory MCP"""

    def __init__(self):
        self.local_fallback_file = (
            Path.home() / ".cache" / "claude-learning" / "memory_mcp_fallback.json"
        )
        self.local_fallback_file.parent.mkdir(parents=True, exist_ok=True)
        self.memory_mcp_available = True  # Will be set based on actual MCP availability

    def store_correction_in_memory_mcp(
        self, correction: dict, conversation_context: dict | None = None
    ) -> bool:
        """Store a correction in Memory MCP with proper entity structure"""
        try:
            if self.memory_mcp_available:
                return self._store_in_memory_mcp(correction, conversation_context)
            return self._store_in_local_fallback(correction, conversation_context)
        except Exception as e:
            print(f"Memory MCP storage failed: {e}")
            # Fallback to local storage
            return self._store_in_local_fallback(correction, conversation_context)

    def _store_in_memory_mcp(
        self, correction: dict, conversation_context: dict | None = None
    ) -> bool:
        """Store correction using actual Memory MCP functions"""

        # Generate unique entity name
        entity_name = f"correction_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{correction['type']}"

        # Prepare observations
        observations = [
            f"Correction type: {correction['type']}",
            f"Original text: {correction['original_text']}",
            f"Pattern: {' → '.join(correction['pattern']) if isinstance(correction['pattern'], tuple) else correction['pattern']}",
            f"Context: {', '.join(correction['context'])}",
            f"Confidence: {correction['confidence']:.2f}",
            f"Detected at: {correction['timestamp']}",
        ]

        if conversation_context:
            observations.append(
                f"Conversation context: {json.dumps(conversation_context)}"
            )

        # In a real implementation, this would use:
        # mcp__memory-server__create_entities([{
        #     "name": entity_name,
        #     "entityType": "user_correction",
        #     "observations": observations
        # }])

        # For now, simulate successful storage
        print(f"📝 [Simulated] Stored in Memory MCP: {entity_name}")

        # Create relations to user
        # mcp__memory-server__create_relations([{
        #     "from": "jleechan2015",
        #     "to": entity_name,
        #     "relationType": "provided_correction"
        # }])

        return True

    def _store_in_local_fallback(
        self, correction: dict, conversation_context: dict | None = None
    ) -> bool:
        """Store correction in local fallback storage"""
        try:
            # Load existing data
            if self.local_fallback_file.exists():
                with open(self.local_fallback_file) as f:
                    data = json.load(f)
            else:
                data = {
                    "entities": {},
                    "relations": [],
                    "metadata": {"created": datetime.now().isoformat()},
                }

            # Create entity
            entity_name = f"correction_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{correction['type']}"

            entity = {
                "name": entity_name,
                "entityType": "user_correction",
                "correction_type": correction["type"],
                "pattern": correction["pattern"],
                "original_text": correction["original_text"],
                "context": correction["context"],
                "confidence": correction["confidence"],
                "timestamp": correction["timestamp"],
                "conversation_context": conversation_context or {},
                "stored_in_fallback": True,
                "created": datetime.now().isoformat(),
            }

            data["entities"][entity_name] = entity

            # Create relation to user
            relation = {
                "from": "jleechan2015",
                "to": entity_name,
                "relationType": "provided_correction",
                "created": datetime.now().isoformat(),
            }
            data["relations"].append(relation)

            # Save data
            with open(self.local_fallback_file, "w") as f:
                json.dump(data, f, indent=2)

            print(f"💾 Stored in local fallback: {entity_name}")
            return True

        except Exception as e:
            print(f"Local fallback storage failed: {e}")
            return False

    def sync_to_memory_mcp(self) -> dict:
        """Sync local fallback data to Memory MCP when available"""
        if not self.local_fallback_file.exists():
            return {"synced": 0, "errors": 0}

        try:
            with open(self.local_fallback_file) as f:
                data = json.load(f)

            synced = 0
            errors = 0

            for entity_name, entity in data.get("entities", {}).items():
                if entity.get("stored_in_fallback") and not entity.get("synced_to_mcp"):
                    success = self._sync_entity_to_mcp(entity)
                    if success:
                        entity["synced_to_mcp"] = True
                        entity["synced_at"] = datetime.now().isoformat()
                        synced += 1
                    else:
                        errors += 1

            # Save updated data
            with open(self.local_fallback_file, "w") as f:
                json.dump(data, f, indent=2)

            return {"synced": synced, "errors": errors}

        except Exception as e:
            print(f"Sync to Memory MCP failed: {e}")
            return {"synced": 0, "errors": 1}

    def _sync_entity_to_mcp(self, entity: dict) -> bool:
        """Sync a single entity to Memory MCP"""
        # In real implementation, would use actual MCP functions
        print(f"🔄 [Simulated] Syncing to Memory MCP: {entity['name']}")
        return True

    def get_stored_corrections(self, include_fallback: bool = True) -> list[dict]:
        """Get all stored corrections from Memory MCP and/or fallback"""
        corrections = []

        # In real implementation, would query Memory MCP:
        # results = mcp__memory-server__search_nodes("user_correction")

        # Get from local fallback
        if include_fallback and self.local_fallback_file.exists():
            try:
                with open(self.local_fallback_file) as f:
                    data = json.load(f)

                for entity in data.get("entities", {}).values():
                    if entity.get("entityType") == "user_correction":
                        corrections.append(entity)
            except:
                pass

        return corrections


class AutoCorrectionProcessor:
    """Processes corrections automatically from detection to storage"""

    def __init__(self):
        from auto_correction_detector import AutoCorrectionPipeline

        self.detector_pipeline = AutoCorrectionPipeline()
        self.memory_integration = MemoryMCPIntegration()

    def process_message_for_learning(
        self, message: str, conversation_context: dict | None = None
    ) -> dict:
        """Complete pipeline: detect corrections and store in memory automatically"""

        # Step 1: Detect corrections
        detection_result = self.detector_pipeline.process_user_message(
            message, conversation_context
        )

        # Step 2: Store in Memory MCP
        storage_results = []
        for correction in detection_result["corrections_detected"]:
            success = self.memory_integration.store_correction_in_memory_mcp(
                correction, conversation_context
            )
            storage_results.append(success)

        # Step 3: Generate complete result
        result = {
            "message": message,
            "corrections_detected": len(detection_result["corrections_detected"]),
            "corrections_stored": sum(storage_results),
            "storage_success": all(storage_results) if storage_results else True,
            "summary": detection_result["summary"],
            "user_confirmation_needed": detection_result["user_confirmation_needed"],
            "corrections": detection_result["corrections_detected"],
        }

        return result

    def sync_pending_to_memory_mcp(self) -> dict:
        """Sync any pending corrections to Memory MCP"""
        return self.memory_integration.sync_to_memory_mcp()

    def get_learning_statistics(self) -> dict:
        """Get statistics about learned corrections"""
        corrections = self.memory_integration.get_stored_corrections()

        if not corrections:
            return {"total": 0}

        # Analyze correction types
        types = {}
        contexts = {}
        avg_confidence = 0

        for correction in corrections:
            correction_type = correction.get("correction_type", "unknown")
            types[correction_type] = types.get(correction_type, 0) + 1

            for context in correction.get("context", []):
                contexts[context] = contexts.get(context, 0) + 1

            avg_confidence += correction.get("confidence", 0)

        avg_confidence = avg_confidence / len(corrections) if corrections else 0

        return {
            "total": len(corrections),
            "by_type": types,
            "by_context": contexts,
            "avg_confidence": round(avg_confidence, 3),
            "recent": len(
                [
                    c
                    for c in corrections
                    if "created" in c
                    and (datetime.now() - datetime.fromisoformat(c["created"])).days < 7
                ]
            ),
        }


def test_memory_integration():
    """Test the complete memory integration pipeline"""
    processor = AutoCorrectionProcessor()

    test_messages = [
        "Don't use inline imports, use module-level imports instead.",
        "I prefer using Memory MCP for persistent storage.",
        "When testing, always use the --puppeteer flag for browser tests.",
    ]

    print("🧪 Testing Memory Integration Pipeline")
    print("=" * 50)

    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. Processing: '{message}'")
        result = processor.process_message_for_learning(message, {"test_run": True})

        print(f"   Corrections detected: {result['corrections_detected']}")
        print(f"   Corrections stored: {result['corrections_stored']}")
        print(f"   Storage success: {result['storage_success']}")

        if result["summary"]:
            print(f"   Summary: {result['summary']}")

    # Show statistics
    stats = processor.get_learning_statistics()
    print("\n📊 Learning Statistics:")
    print(f"   Total corrections: {stats['total']}")
    print(f"   By type: {stats.get('by_type', {})}")
    print(f"   Average confidence: {stats.get('avg_confidence', 0)}")


if __name__ == "__main__":
    test_memory_integration()
