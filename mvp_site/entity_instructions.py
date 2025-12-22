"""
Enhanced Explicit Entity Instructions (Option 5 Enhanced)
Generates specific AI instructions requiring entity mentions and presence.
"""

import re
from dataclasses import dataclass
from typing import Any

from mvp_site import logging_util
from mvp_site.entity_tracking import SceneManifest, create_from_game_state


@dataclass
class EntityInstruction:
    """Represents an instruction for handling a specific entity"""

    entity_name: str
    instruction_type: str  # 'mandatory', 'conditional', 'background'
    specific_instruction: str
    priority: int  # 1 = highest, 3 = lowest


class EntityInstructionGenerator:
    """
    Generates explicit instructions for AI to ensure entity presence.
    Creates targeted instructions based on entity types and context.
    """

    def __init__(self):
        self.instruction_templates = self._build_instruction_templates()
        self.entity_priorities = self._build_entity_priorities()

    def _build_instruction_templates(self) -> dict[str, dict[str, str]]:
        """Build instruction templates for different entity types and situations"""
        return {
            "player_character": {
                "mandatory": "The player character {entity} MUST be present and actively involved in this scene. Include their actions, thoughts, or dialogue.",
                "dialogue": "Show {entity}'s response or reaction to the current situation through dialogue or internal monologue.",
                "action": "Describe {entity}'s physical actions and emotional state in response to the scene.",
            },
            "npc_referenced": {
                "mandatory": "{entity} has been directly referenced by the player and MUST appear or respond in this scene. Do not ignore this reference.",
                "dialogue": "Include {entity}'s direct response to being mentioned or addressed.",
                "presence": "Even if {entity} was not previously in the scene, they should appear or their voice should be heard in response to being referenced.",
            },
            "location_npc": {
                "mandatory": "{entity} is associated with this location and should be present unless explicitly stated otherwise.",
                "contextual": "As someone who belongs in {location}, {entity} should naturally be part of the scene.",
                "authority": "{entity} has authority or expertise relevant to this location and should contribute accordingly.",
            },
            "story_critical": {
                "mandatory": "{entity} is critical to the current story development and MUST be included with meaningful contribution.",
                "development": "Advance the story through {entity}'s unique perspective or knowledge.",
                "relationship": "Show the relationship dynamics between {entity} and other present characters.",
            },
            "background": {
                "presence": "{entity} should be acknowledged as present, even if not actively participating.",
                "atmosphere": "Include {entity} to maintain scene atmosphere and character continuity.",
                "reactive": "{entity} may react to events but doesn't need to drive the action.",
            },
        }

    def _build_entity_priorities(self) -> dict[str, int]:
        """Define priority levels for different entity types"""
        return {
            "player_character": 1,
            "npc_referenced": 1,
            "location_owner": 1,
            "story_critical": 2,
            "location_associated": 2,
            "background": 3,
        }

    def generate_entity_instructions(
        self,
        entities: list[str],
        player_references: list[str],
        location: str | None = None,
        story_context: str | None = None,
    ) -> str:
        """
        Generate comprehensive entity instructions for AI prompts.

        Args:
            entities: List of all entities that should be present
            player_references: Entities specifically referenced by player input
            location: Current scene location
            story_context: Additional story context
        """
        if not entities:
            return ""

        instructions = []
        entity_instructions = []

        # Process each entity
        for entity in entities:
            entity_instruction = self._create_entity_instruction(
                entity, player_references, location, story_context
            )
            entity_instructions.append(entity_instruction)

        # Sort by priority
        entity_instructions.sort(key=lambda x: x.priority)

        # Build instruction sections
        instructions.append("=== MANDATORY ENTITY REQUIREMENTS ===")

        mandatory_instructions = [
            ei for ei in entity_instructions if ei.instruction_type == "mandatory"
        ]
        if mandatory_instructions:
            instructions.append(
                "The following entities are REQUIRED and MUST appear in your response:"
            )
            for ei in mandatory_instructions:
                instructions.append(f"• {ei.entity_name}: {ei.specific_instruction}")

        conditional_instructions = [
            ei for ei in entity_instructions if ei.instruction_type == "conditional"
        ]
        if conditional_instructions:
            instructions.append("\nCONDITIONAL REQUIREMENTS:")
            for ei in conditional_instructions:
                instructions.append(f"• {ei.entity_name}: {ei.specific_instruction}")

        background_instructions = [
            ei for ei in entity_instructions if ei.instruction_type == "background"
        ]
        if background_instructions:
            instructions.append("\nBACKGROUND PRESENCE:")
            for ei in background_instructions:
                instructions.append(f"• {ei.entity_name}: {ei.specific_instruction}")

        # Add enforcement clause
        instructions.append("\n=== ENFORCEMENT ===")
        instructions.append(
            f"DO NOT complete your response without including ALL {len(mandatory_instructions)} mandatory entities listed above."
        )
        instructions.append(
            "Each mandatory entity must have at least one line of dialogue, action, or clear presence indication."
        )

        if player_references:
            instructions.append(
                f"\nSPECIAL ATTENTION: The player specifically mentioned {', '.join(player_references)}. "
                f"These entities MUST respond or appear, as ignoring player references breaks immersion."
            )

        instructions.append("=== END ENTITY REQUIREMENTS ===\n")

        return "\n".join(instructions)

    def _create_entity_instruction(
        self,
        entity: str,
        player_references: list[str],
        location: str | None,
        story_context: str | None,
    ) -> EntityInstruction:
        """Create specific instruction for an individual entity"""
        entity.lower()

        # Determine entity category and priority
        if entity in player_references:
            category = "npc_referenced"
            instruction_type = "mandatory"
            priority = 1
            template_key = "mandatory"
        elif self._is_player_character(entity):
            category = "player_character"
            instruction_type = "mandatory"
            priority = 1
            template_key = "mandatory"
        elif self._is_location_owner(entity, location):
            category = "location_npc"
            instruction_type = "mandatory"
            priority = 1
            template_key = "mandatory"
        elif self._is_story_critical(entity, story_context):
            category = "story_critical"
            instruction_type = "conditional"
            priority = 2
            template_key = "development"
        else:
            category = "background"
            instruction_type = "background"
            priority = 3
            template_key = "presence"

        # Get template and create instruction
        templates = self.instruction_templates.get(
            category, self.instruction_templates["background"]
        )
        if template_key in templates:
            template = templates[template_key]
        else:
            # Fallback to first available template in category
            template = list(templates.values())[0]

        specific_instruction = template.format(
            entity=entity, location=location or "this location"
        )

        # Add context-specific enhancements
        if entity in player_references:
            specific_instruction += " The player directly referenced this character, so ignoring them would break narrative continuity."

        # Note: Emotional context detection is now handled by enhanced system instructions
        # that naturally understand emotional appeals and guide appropriate character responses

        return EntityInstruction(
            entity_name=entity,
            instruction_type=instruction_type,
            specific_instruction=specific_instruction,
            priority=priority,
        )

    def _is_player_character(self, entity: str) -> bool:
        """Determine if entity is a player character based on game state"""
        try:
            # Check if entity matches player character data patterns
            if not entity:
                return False

            entity_lower = entity.lower()

            # Common player character indicators (exact matches or specific patterns)
            player_indicators = [
                "player",
                "pc",
                "hero",
                "protagonist",
                "you",
            ]

            # Specific phrase patterns
            player_phrases = [
                "your character",
                "main character",
                "the player",
                "player character",
            ]

            # Check if entity name exactly matches or contains specific phrases
            for indicator in player_indicators:
                if entity_lower in {indicator, f"the {indicator}"}:
                    return True

            return any(phrase in entity_lower for phrase in player_phrases)

            # Integrate with actual game state to check player_character_data
            # Using heuristic approach until full game state integration
        except Exception:
            return False

    def _is_location_owner(self, entity: str, location: str | None) -> bool:  # noqa: ARG002
        """Determine if entity owns/belongs to the current location

        Currently disabled to avoid hardcoded location ownership patterns.
        All entities are treated as background/story_critical based on other factors.
        """
        # Always return False to disable location ownership detection
        # This ensures all entities are categorized based on story_critical or background logic
        return False

    def _is_story_critical(self, entity: str, story_context: str | None) -> bool:
        """Determine if entity is critical to current story development"""
        if not story_context:
            return False

        # Simple keyword matching - could be enhanced
        story_lower = story_context.lower()
        entity.lower()

        critical_indicators = ["important", "key", "crucial", "main"]
        return any(indicator in story_lower for indicator in critical_indicators)

    # NOTE: create_entity_specific_instruction method removed
    # Entity-specific instructions are now handled by enhanced system instructions
    # (Part 8.B: Emotional Context and Character Response) which provide semantic
    # understanding of entity references without hardcoded string matching.

    def create_location_specific_instructions(
        self,
        location: str,
        expected_entities: list[str],  # noqa: ARG002
    ) -> str:
        """Create location-specific entity instructions"""
        # Generic location-based instructions
        location_types = {
            "throne": "Court setting requires appropriate nobles, guards, or advisors to be present for authenticity.",
            "study": "Scholarly atmosphere with appropriate inhabitants and materials.",
            "chamber": "Private setting with appropriate personal touches and inhabitants.",
            "archive": "Scholarly environment with researchers and knowledge seekers.",
            "temple": "Religious setting with appropriate clergy and worshippers.",
            "market": "Bustling commercial area with merchants and customers.",
            "tavern": "Social gathering place with patrons and staff.",
        }

        location_lower = location.lower()
        for loc_type, instruction in location_types.items():
            if loc_type in location_lower:
                return f"LOCATION REQUIREMENT for {location}: {instruction}"

        return f"LOCATION: {location} - Ensure entities appropriate to this setting are present."


class EntityEnforcementChecker:
    """
    Validates that entity instructions are being followed in AI responses.
    """

    def __init__(self):
        self.instruction_compliance_patterns = self._build_compliance_patterns()

    def _build_compliance_patterns(self) -> dict[str, list[str]]:
        """Build patterns to check instruction compliance"""
        return {
            "presence_indicators": [
                r"\b{entity}\b",
                r"\b{entity}(?:\'s|\s+says|\s+does)",
                r"(?:says|speaks|responds).*{entity}",
            ],
            "action_indicators": [
                r"{entity}.*(?:moves|walks|turns|looks|nods|speaks)",
                r"(?:moves|walks|turns|looks|nods|speaks).*{entity}",
            ],
            "dialogue_indicators": [
                r'{entity}.*["\']',
                r'["\'].*{entity}',
                r"{entity}.*(?:says|speaks|responds)",
            ],
        }

    def check_instruction_compliance(
        self, narrative: str, mandatory_entities: list[str]
    ) -> dict[str, Any]:
        """Check if narrative complies with entity instructions"""
        compliance_report: dict[str, Any] = {
            "overall_compliance": True,
            "compliant_entities": [],
            "non_compliant_entities": [],
            "compliance_details": {},
        }

        narrative_lower = narrative.lower()

        for entity in mandatory_entities:
            entity_compliance = self._check_entity_compliance(narrative_lower, entity)
            compliance_report["compliance_details"][entity] = entity_compliance

            if entity_compliance["present"]:
                compliance_report["compliant_entities"].append(entity)
            else:
                compliance_report["non_compliant_entities"].append(entity)
                compliance_report["overall_compliance"] = False

        return compliance_report

    def _check_entity_compliance(
        self, narrative_lower: str, entity: str
    ) -> dict[str, Any]:
        """Check compliance for a specific entity"""
        entity_lower = entity.lower()

        compliance = {
            "present": False,
            "has_dialogue": False,
            "has_action": False,
            "mention_count": 0,
        }

        # Check basic presence
        if entity_lower in narrative_lower:
            compliance["present"] = True
            compliance["mention_count"] = narrative_lower.count(entity_lower)

        # Check for dialogue
        dialogue_patterns = [
            f"{entity_lower}.*[\"']",
            f"[\"'].*{entity_lower}",
            f"{entity_lower}.*(?:says|speaks|responds)",
        ]

        for pattern in dialogue_patterns:
            if re.search(pattern, narrative_lower):
                compliance["has_dialogue"] = True
                break

        # Check for action
        action_patterns = [
            f"{entity_lower}.*(?:moves|walks|turns|looks|nods|speaks)",
            f"(?:moves|walks|turns|looks|nods|speaks).*{entity_lower}",
        ]

        for pattern in action_patterns:
            if re.search(pattern, narrative_lower):
                compliance["has_action"] = True
                break

        return compliance


# =============================================================================
# Entity Preloader Classes (consolidated from entity_preloader.py)
# =============================================================================


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
            logging_util.info(
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
            if (
                hasattr(npc, "location")
                and npc.location
                and (
                    location.lower() in npc.location.lower()
                    or npc.location.lower() in location.lower()
                )
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
        logging_util.info("Entity preloader cache cleared")


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


# =============================================================================
# Global Instances
# =============================================================================

entity_instruction_generator = EntityInstructionGenerator()
entity_enforcement_checker = EntityEnforcementChecker()
entity_preloader = EntityPreloader()
location_enforcer = LocationEntityEnforcer()
