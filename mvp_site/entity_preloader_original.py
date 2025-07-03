"""
Entity Pre-Loading System (Option 3)
Includes full entity manifest in every AI prompt to ensure entity presence.
"""

from typing import Dict, List, Any, Optional
from entity_tracking import create_from_game_state, SceneManifest
import logging

logger = logging.getLogger(__name__)


class EntityPreloader:
    """
    Handles entity pre-loading for AI prompts to prevent entity disappearing.
    Implements Option 3: Entity Pre-Loading in Prompts.
    """
    
    def __init__(self):
        self.manifest_cache = {}
    
    def generate_entity_manifest(self, game_state: Dict[str, Any], 
                                session_number: int, turn_number: int) -> SceneManifest:
        """Generate or retrieve cached entity manifest"""
        cache_key = f"{session_number}_{turn_number}"
        
        if cache_key not in self.manifest_cache:
            manifest = create_from_game_state(game_state, session_number, turn_number)
            self.manifest_cache[cache_key] = manifest
            logger.info(f"Generated entity manifest for session {session_number}, turn {turn_number}")
        
        return self.manifest_cache[cache_key]
    
    def create_entity_preload_text(self, game_state: Dict[str, Any], 
                                  session_number: int, turn_number: int,
                                  location: Optional[str] = None) -> str:
        """
        Create entity pre-loading text to inject into AI prompts.
        This ensures all active entities are explicitly mentioned before generation.
        """
        manifest = self.generate_entity_manifest(game_state, session_number, turn_number)
        
        preload_sections = []
        
        # Player Characters Section
        if manifest.player_characters:
            pc_list = []
            for pc in manifest.player_characters:
                status_info = []
                if hasattr(pc, 'hp_current') and hasattr(pc, 'hp_max'):
                    status_info.append(f"HP: {pc.hp_current}/{pc.hp_max}")
                if hasattr(pc, 'status') and pc.status != 'normal':
                    status_info.append(f"Status: {pc.status}")
                
                status_text = f" ({', '.join(status_info)})" if status_info else ""
                pc_list.append(f"- {pc.name}{status_text}")
            
            preload_sections.append(f"PLAYER CHARACTERS PRESENT:\n" + "\n".join(pc_list))
        
        # NPCs Section
        if manifest.npcs:
            npc_list = []
            for npc in manifest.npcs:
                status_info = []
                if hasattr(npc, 'hp_current') and hasattr(npc, 'hp_max'):
                    status_info.append(f"HP: {npc.hp_current}/{npc.hp_max}")
                if hasattr(npc, 'status') and npc.status != 'normal':
                    status_info.append(f"Status: {npc.status}")
                if hasattr(npc, 'location') and npc.location:
                    status_info.append(f"Location: {npc.location}")
                
                status_text = f" ({', '.join(status_info)})" if status_info else ""
                npc_list.append(f"- {npc.name}{status_text}")
            
            preload_sections.append(f"NPCS PRESENT:\n" + "\n".join(npc_list))
        
        # Location-specific entities
        if location:
            location_entities = self._get_location_entities(manifest, location)
            if location_entities:
                preload_sections.append(f"ENTITIES IN {location.upper()}:\n" + 
                                      "\n".join([f"- {entity}" for entity in location_entities]))
        
        if not preload_sections:
            return "ENTITIES PRESENT: None specified"
        
        preload_text = "\n\n".join(preload_sections)
        
        # Add enforcement instruction
        entity_names = []
        if manifest.player_characters:
            entity_names.extend([pc.name for pc in manifest.player_characters])
        if manifest.npcs:
            entity_names.extend([npc.name for npc in manifest.npcs])
        
        if entity_names:
            enforcement_text = (
                f"\n\nIMPORTANT: The following entities MUST be acknowledged or mentioned "
                f"in your response as they are present in this scene: {', '.join(entity_names)}. "
                f"Do not let any of these entities disappear from the narrative."
            )
            preload_text += enforcement_text
        
        return f"=== ENTITY MANIFEST ===\n{preload_text}\n=== END ENTITY MANIFEST ===\n"
    
    def _get_location_entities(self, manifest: SceneManifest, location: str) -> List[str]:
        """Get entities that should be present in a specific location"""
        location_entities = []
        
        # Check NPCs with location data
        for npc in manifest.npcs:
            if hasattr(npc, 'location') and npc.location:
                if location.lower() in npc.location.lower() or npc.location.lower() in location.lower():
                    location_entities.append(f"{npc.name} (resident)")
        
        # Location-specific logic (can be expanded)
        location_lower = location.lower()
        if "throne room" in location_lower:
            location_entities.append("Court guards (background)")
        elif "study" in location_lower:
            location_entities.append("Study materials and books")
        elif "chambers" in location_lower:
            location_entities.append("Personal quarters ambiance")
        elif "archives" in location_lower:
            location_entities.append("Ancient tomes and scrolls")
        
        return location_entities
    
    def get_entity_count(self, game_state: Dict[str, Any], 
                        session_number: int, turn_number: int) -> Dict[str, int]:
        """Get count of entities for logging/validation"""
        manifest = self.generate_entity_manifest(game_state, session_number, turn_number)
        
        return {
            'player_characters': len(manifest.player_characters),
            'npcs': len(manifest.npcs),
            'total_entities': len(manifest.player_characters) + len(manifest.npcs)
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
        self.location_rules = {
            "throne room": {
                "required_roles": ["court_guard", "advisor"],
                "suggested_npcs": ["Court Herald", "Royal Guard Captain"]
            },
            "valerius's study": {
                "required_npcs": ["Valerius"],
                "suggested_items": ["Ancient scrolls", "Mystical artifacts"]
            },
            "lady cressida's chambers": {
                "required_npcs": ["Lady Cressida", "Lady Cressida Valeriana"],
                "suggested_items": ["Elegant furnishings", "Personal effects"]
            },
            "great archives": {
                "required_roles": ["librarian", "archivist"],
                "suggested_npcs": ["Magister Kantos"]
            },
            "chamber of whispers": {
                "required_npcs": ["Magister Kantos"],
                "ambiance": ["Mystical whispers", "Ancient knowledge"]
            }
        }
    
    def get_required_entities_for_location(self, location: str) -> Dict[str, List[str]]:
        """Get entities that should be present in a specific location"""
        location_key = location.lower()
        
        # Find matching location rule
        for rule_location, rules in self.location_rules.items():
            if rule_location in location_key or any(word in location_key for word in rule_location.split()):
                return rules
        
        return {}
    
    def validate_location_entities(self, location: str, present_entities: List[str]) -> Dict[str, Any]:
        """Validate that required entities are present for a location"""
        rules = self.get_required_entities_for_location(location)
        validation_result = {
            "location": location,
            "validation_passed": True,
            "missing_entities": [],
            "warnings": []
        }
        
        present_entities_lower = [entity.lower() for entity in present_entities]
        
        # Check required NPCs
        if "required_npcs" in rules:
            for required_npc in rules["required_npcs"]:
                if not any(required_npc.lower() in entity.lower() for entity in present_entities_lower):
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
            enforcement_parts.append(f"REQUIRED NPCS: {', '.join(rules['required_npcs'])}")
        
        if "suggested_npcs" in rules:
            enforcement_parts.append(f"SUGGESTED NPCS: {', '.join(rules['suggested_npcs'])}")
        
        if "required_roles" in rules:
            enforcement_parts.append(f"REQUIRED ROLES: {', '.join(rules['required_roles'])}")
        
        if "ambiance" in rules:
            enforcement_parts.append(f"AMBIANCE: {', '.join(rules['ambiance'])}")
        
        return "\n".join(enforcement_parts)


# Global instances for easy import
entity_preloader = EntityPreloader()
location_enforcer = LocationEntityEnforcer()