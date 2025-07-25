"""
Entity Pre-Loading System (Option 3)
Includes full entity manifest in every AI prompt to ensure entity presence.
"""

from typing import Any

import logging_util
from entity_tracking import SceneManifest, create_from_game_state

logger = logging_util.getLogger(__name__)


class EntityPreloader:
    """
    Handles entity pre-loading for AI prompts to prevent entity disappearing.
    Implements Option 3: Entity Pre-Loading in Prompts.
    """

    def __init__(self):
        self.manifest_cache = {}

    def generate_entity_manifest(
        self, game_state: dict[str, Any], session_number: int, turn_number: int
    ) -> SceneManifest:
        """Generate or retrieve cached entity manifest"""
        cache_key = f"{session_number}_{turn_number}"

        if cache_key not in self.manifest_cache:
            manifest = create_from_game_state(game_state, session_number, turn_number)
            self.manifest_cache[cache_key] = manifest
            logger.info(
                f"Generated entity manifest for session {session_number}, turn {turn_number}"
            )

        return self.manifest_cache[cache_key]

    def create_entity_preload_text(
        self,
        game_state: dict[str, Any],
        session_number: int,
        turn_number: int,
        location: str | None = None,
    ) -> str:
        """
        Create entity pre-loading text to inject into AI prompts.
        This ensures all active entities are explicitly mentioned before generation.
        """
        manifest = self.generate_entity_manifest(
            game_state, session_number, turn_number
        )

        preload_sections = []

        # Player Characters Section
        if manifest.player_characters:
            pc_list = []
            for pc in manifest.player_characters:
                status_info = []
                if hasattr(pc, "hp_current") and hasattr(pc, "hp_max"):
                    status_info.append(f"HP: {pc.hp_current}/{pc.hp_max}")
                if hasattr(pc, "status") and pc.status != "normal":
                    status_info.append(f"Status: {pc.status}")

                status_text = f" ({', '.join(status_info)})" if status_info else ""
                pc_name = (
                    pc.display_name
                    if hasattr(pc, "display_name")
                    else getattr(pc, "name", "Unknown")
                )
                pc_list.append(f"- {pc_name}{status_text}")

            preload_sections.append("PLAYER CHARACTERS PRESENT:\n" + "\n".join(pc_list))

        # NPCs Section
        if manifest.npcs:
            npc_list = []
            for npc in manifest.npcs:
                status_info = []
                if hasattr(npc, "hp_current") and hasattr(npc, "hp_max"):
                    status_info.append(f"HP: {npc.hp_current}/{npc.hp_max}")
                if hasattr(npc, "status") and npc.status != "normal":
                    status_info.append(f"Status: {npc.status}")
                if hasattr(npc, "location") and npc.location:
                    status_info.append(f"Location: {npc.location}")

                status_text = f" ({', '.join(status_info)})" if status_info else ""
                npc_name = (
                    npc.display_name
                    if hasattr(npc, "display_name")
                    else getattr(npc, "name", "Unknown")
                )
                npc_list.append(f"- {npc_name}{status_text}")

            preload_sections.append("NPCS PRESENT:\n" + "\n".join(npc_list))

        # Location-specific entities
        if location:
            location_entities = self._get_location_entities(manifest, location)
            if location_entities:
                preload_sections.append(
                    f"ENTITIES IN {location.upper()}:\n"
                    + "\n".join([f"- {entity}" for entity in location_entities])
                )

        if not preload_sections:
            return "ENTITIES PRESENT: None specified"

        preload_text = "\n\n".join(preload_sections)

        # Add enforcement instruction
        entity_names = []
        if manifest.player_characters:
            entity_names.extend(
                [
                    pc.display_name
                    if hasattr(pc, "display_name")
                    else getattr(pc, "name", "Unknown")
                    for pc in manifest.player_characters
                ]
            )
        if manifest.npcs:
            entity_names.extend(
                [
                    npc.display_name
                    if hasattr(npc, "display_name")
                    else getattr(npc, "name", "Unknown")
                    for npc in manifest.npcs
                ]
            )

        if entity_names:
            enforcement_text = (
                f"\n\nIMPORTANT: The following entities MUST be acknowledged or mentioned "
                f"in your response as they are present in this scene: {', '.join(entity_names)}. "
                f"Do not let any of these entities disappear from the narrative."
            )
            preload_text += enforcement_text

        return f"=== ENTITY MANIFEST ===\n{preload_text}\n=== END ENTITY MANIFEST ===\n"

    def _get_location_entities(
        self, manifest: SceneManifest, location: str
    ) -> list[str]:
        """Get entities that should be present in a specific location"""
        location_entities = []

        # Check NPCs with location data
        for npc in manifest.npcs:
            if hasattr(npc, "location") and npc.location:
                if (
                    location.lower() in npc.location.lower()
                    or npc.location.lower() in location.lower()
                ):
                    npc_name = (
                        npc.display_name
                        if hasattr(npc, "display_name")
                        else getattr(npc, "name", "Unknown")
                    )
                    location_entities.append(f"{npc_name} (resident)")

        # Generic location-based ambiance (not campaign-specific)
        location_lower = location.lower()
        if any(word in location_lower for word in ["throne", "court", "palace"]):
            location_entities.append("Court guards (background)")
        elif any(word in location_lower for word in ["library", "study", "archive"]):
            location_entities.append("Books and scholarly materials")
        elif any(word in location_lower for word in ["chamber", "bedroom", "quarters"]):
            location_entities.append("Personal furnishings")
        elif any(word in location_lower for word in ["temple", "shrine", "church"]):
            location_entities.append("Religious symbols and atmosphere")

        return location_entities

    def get_entity_count(
        self, game_state: dict[str, Any], session_number: int, turn_number: int
    ) -> dict[str, int]:
        """Get count of entities for logging/validation"""
        manifest = self.generate_entity_manifest(
            game_state, session_number, turn_number
        )

        return {
            "player_characters": len(manifest.player_characters),
            "npcs": len(manifest.npcs),
            "total_entities": len(manifest.player_characters) + len(manifest.npcs),
        }

    def clear_cache(self):
        """Clear the manifest cache (useful for testing)"""
        self.manifest_cache.clear()
        logger.info("Entity preloader cache cleared")


class LocationEntityEnforcer:
    """
    Implements location-based entity enforcement.
    Ensures location-appropriate NPCs are included in scenes.
    """

    def __init__(self):
        # Generic location rules based on location types
        # No campaign-specific hardcoding
        self.location_rules = {}

    def get_required_entities_for_location(self, location: str) -> dict[str, list[str]]:
        """Get entities that should be present in a specific location"""
        location_key = location.lower()

        # Find matching location rule
        for rule_location, rules in self.location_rules.items():
            if rule_location in location_key or any(
                word in location_key for word in rule_location.split()
            ):
                return rules

        return {}

    def validate_location_entities(
        self, location: str, present_entities: list[str]
    ) -> dict[str, Any]:
        """Validate that required entities are present for a location"""
        rules = self.get_required_entities_for_location(location)
        validation_result = {
            "location": location,
            "validation_passed": True,
            "missing_entities": [],
            "warnings": [],
        }

        present_entities_lower = [entity.lower() for entity in present_entities]

        # Check required NPCs
        if "required_npcs" in rules:
            for required_npc in rules["required_npcs"]:
                if not any(
                    required_npc.lower() in entity.lower()
                    for entity in present_entities_lower
                ):
                    validation_result["missing_entities"].append(required_npc)
                    validation_result["validation_passed"] = False

        # Check required roles (more flexible matching)
        if "required_roles" in rules:
            for role in rules["required_roles"]:
                if not any(role in entity.lower() for entity in present_entities_lower):
                    validation_result["warnings"].append(f"No {role} present")

        return validation_result

    def generate_location_enforcement_text(self, location: str) -> str:
        """Generate text to enforce location-appropriate entities"""
        rules = self.get_required_entities_for_location(location)

        if not rules:
            return f"LOCATION: {location} (no specific entity requirements)"

        enforcement_parts = [f"LOCATION: {location}"]

        if "required_npcs" in rules:
            enforcement_parts.append(
                f"REQUIRED NPCS: {', '.join(rules['required_npcs'])}"
            )

        if "suggested_npcs" in rules:
            enforcement_parts.append(
                f"SUGGESTED NPCS: {', '.join(rules['suggested_npcs'])}"
            )

        if "required_roles" in rules:
            enforcement_parts.append(
                f"REQUIRED ROLES: {', '.join(rules['required_roles'])}"
            )

        if "ambiance" in rules:
            enforcement_parts.append(f"AMBIANCE: {', '.join(rules['ambiance'])}")

        return "\n".join(enforcement_parts)


# Global instances for easy import
entity_preloader = EntityPreloader()
location_enforcer = LocationEntityEnforcer()
