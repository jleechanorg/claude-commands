"""
Enhanced Explicit Entity Instructions (Option 5 Enhanced)
Generates specific AI instructions requiring entity mentions and presence.
"""

import re
from dataclasses import dataclass
from typing import Any

import logging_util

logger = logging_util.getLogger(__name__)


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

    def _is_player_character(self, entity: str) -> bool:  # noqa: ARG002
        """Determine if entity is a player character"""
        # This should be determined by game state, not hardcoded
        # For now, return False to avoid false positives
        return False

    def _is_location_owner(self, entity: str, location: str | None) -> bool:
        """Determine if entity owns/belongs to the current location"""
        if not location:
            return False

        location.lower()
        entity.lower()

        # Location mappings should come from game state, not hardcoded
        # For now, return False to avoid false positives
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


# Global instances
entity_instruction_generator = EntityInstructionGenerator()
entity_enforcement_checker = EntityEnforcementChecker()
