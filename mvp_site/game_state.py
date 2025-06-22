"""
Defines the GameState class, which represents the complete state of a campaign.
"""
import datetime
from enum import Enum
from typing import Optional

class MigrationStatus(Enum):
    NOT_CHECKED = "NOT_CHECKED"
    MIGRATED = "MIGRATED"
    NO_LEGACY_DATA = "NO_LEGACY_DATA"

class GameState:
    """
    A class to hold and manage game state data, behaving like a flexible dictionary.
    """
    def __init__(self, **kwargs):
        """Initializes the GameState object with arbitrary data."""
        # Set default values for core attributes if they are not provided
        self.game_state_version = kwargs.get("game_state_version", 1)
        self.player_character_data = kwargs.get("player_character_data", {})
        self.world_data = kwargs.get("world_data", {})
        self.npc_data = kwargs.get("npc_data", {})
        self.custom_campaign_state = kwargs.get("custom_campaign_state", {})
        self.world_time = kwargs.get("world_time", {"year": 2024, "month": "January", "day": 1, "hour": 9, "minute": 0, "second": 0})
        self.last_state_update_timestamp = kwargs.get("last_state_update_timestamp", datetime.datetime.now(datetime.timezone.utc))
        
        migration_status_value = kwargs.get("migration_status", MigrationStatus.NOT_CHECKED.value)
        try:
            self.migration_status = MigrationStatus(migration_status_value)
        except ValueError:
            self.migration_status = MigrationStatus.NOT_CHECKED

        # Dynamically set any other attributes from kwargs
        for key, value in kwargs.items():
            if not hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> dict:
        """Serializes the GameState object to a dictionary for Firestore."""
        # Copy all attributes from the instance's __dict__
        data = self.__dict__.copy()
        
        # Convert Enum members to their string values for serialization
        if 'migration_status' in data and isinstance(data['migration_status'], MigrationStatus):
            data['migration_status'] = data['migration_status'].value
            
        return data

    @classmethod
    def from_dict(cls, source: dict):
        """Creates a GameState object from a dictionary (e.g., from Firestore)."""
        if not source:
            return None
        
        # The constructor now directly accepts the dictionary.
        return cls(**source) 

def get_initial_game_state(premise, migration_status="FRESH_INSTALL"):
    """
    Returns the initial game state dictionary.
    """
    player_character_data = {
        "name": "Sir Gareth Valerius",
        "archetype": "The Idealistic Knight, Reluctant Redeemer of a Fallen Legacy",
        "occupation": "Knight Errant",
        "social_standing": "Scion of a once-respected but now disgraced minor noble house",
        "alignment": "Lawful Good",
        "mbti": "INFJ",
        "age": 24,
        "level": 5,
        "xp_current": 5700,
        "ep_current": 32,
        "stats": {
            "physique": {"score": 16, "modifier": 3, "potential": 4, "yearly_growth_rate": "+0.4/year"},
            "coordination": {"score": 10, "modifier": 0, "potential": 2, "yearly_growth_rate": "+0.2/year"},
            "health": {"score": 14, "modifier": 2, "potential": 3, "yearly_growth_rate": "+0.3/year"},
            "intelligence": {"score": 12, "modifier": 1, "potential": 3, "yearly_growth_rate": "+0.3/year"},
            "wisdom": {"score": 16, "modifier": 3, "potential": 4, "yearly_growth_rate": "+0.4/year"}
        },
        "personality_traits": {
            "openness": {"rating": 3, "modifier": 0},
            "conscientiousness": {"rating": 5, "modifier": 2},
            "extraversion": {"rating": 2, "modifier": -1},
            "agreeableness": {"rating": 4, "modifier": 1},
            "neuroticism": {"rating": 3, "behavioral_influence": " prone to self-doubt and internal conflict over moral compromises"}
        },
        "combat_stats": {
            "defense": 18
        }
    }

    npc_data = {
        "pyrexxus_the_shadowflame_wyrm": {
            "name": "Pyrexxus, The Shadowflame Wyrm",
            "archetype": "Ancient Corrupter, Tempting Tyrant",
            "occupation": "Ancient Red Dragon",
            "social_standing": "Self-proclaimed lord of the Dragon's Tooth mountains",
            "alignment": "Lawful Evil",
            "mbti": "ENTJ",
            "core_motivation": "To assert dominion over mortals by corrupting their ideals and proving futility of virtue.",
            "greatest_fear": "Being forgotten, mocked, or outsmarted.",
            "key_personality_traits": ["Arrogant", "Manipulative", "Cunning", "Patient", "Vain", "Cruel"],
            "backstory": {
                "defining_moment": "Orchestrated the fall of a mighty elven kingdom by sowing discord and temptation.",
                "relevant_history": "One of the oldest and most cunning dragons in Eldoria. Observed countless mortal empires rise and fall.",
                "secrets": [
                    "Slowly succumbing to a debilitating magical disease, a curse from an ancient elven sorceress.",
                    "Discovered 'Heart of the Mountain' artifact, needs mortal agent to retrieve it to cure affliction and enhance power."
                ]
            },
            "personality_traits": {
                "openness": {"rating": 4, "modifier": 1},
                "conscientiousness": {"rating": 5, "modifier": 2},
                "extraversion": {"rating": 5, "modifier": 2},
                "agreeableness": {"rating": 1, "modifier": -2},
                "neuroticism": {"rating": 2, "behavioral_influence": "arrogant and supremely confident, until his fear of being forgotten is triggered"}
            },
            "game_mechanics_summary": {
                "feats": ["Legendary Resistance (3/Day)", "Lair Actions", "Frightful Presence"],
                "special_abilities": ["Corrupting Aura", "Shadowflame Breath"]
            }
        },
        "lord_alaric_valerius": {
            "name": "Lord Alaric Valerius",
            "archetype": "The Broken Idealist, Pragmatic Survivor",
            "occupation": "Lord of Disgraced House Valerius",
            "alignment": "Lawful Neutral",
            "mbti": "ISTJ",
            "core_motivation": "To ensure the survival of House Valerius at any cost, even if it means compromising honor and ideals.",
            "greatest_fear": "The complete extinction of his lineage and total erasure of his family's name.",
            "key_personality_traits": ["Weary", "Resigned", "Pragmatic", "Guilt-ridden (hidden)", "Defensive"],
            "backstory": {
                "defining_moment": "Sacrificed a loyal retainer for momentary political gain that proved hollow.",
                "relevant_history": "Unable to adapt to shifting political landscape, made desperate and morally questionable decisions.",
                "secrets": [
                    "Knows more about Gareth's mother's death, possibly complicit or covered it up.",
                    "Secretly hopes Gareth will succeed in restoring family honor, even as he chides his idealism."
                ]
            },
            "personality_traits": {
                "openness": {"rating": 1, "modifier": -2},
                "conscientiousness": {"rating": 3, "modifier": 0},
                "extraversion": {"rating": 2, "modifier": -1},
                "agreeableness": {"rating": 2, "modifier": -1},
                "neuroticism": {"rating": 5, "behavioral_influence": "guilt-ridden, weary, stressed, fatalistic"}
            },
            "game_mechanics_summary": {
                "feats": ["Defensive Duelist", "Inspiring Leader"],
                "special_abilities": ["Local Authority"]
            }
        },
        "high_priestess_lyra_brightsong": {
            "name": "High Priestess Lyra Brightsong",
            "archetype": "The Zealous Crusader, Unwavering Beacon of Faith",
            "occupation": "Leader of the Children of the Sun",
            "alignment": "Lawful Good",
            "mbti": "ENFJ",
            "core_motivation": "To spread the light of Solarius and purge all darkness and corruption from the land.",
            "greatest_fear": "Apostasy and the triumph of heresy or shadow over divine light.",
            "key_personality_traits": ["Zealous", "Inspirational", "Charismatic", "Unyielding", "Dogmatic"],
            "backstory": {
                "defining_moment": "Survived a demonic incursion that destroyed her home village, interpreting it as a divine mandate.",
                "relevant_history": "Rose quickly through the ranks due to unwavering faith and powerful healing abilities.",
                "secrets": [
                    "Believes the King is too weak and secretly seeks a 'more righteous' ruler.",
                    "Possesses a fragmented prophecy of a 'Chosen Blade of Light' and suspects Gareth is this figure."
                ]
            },
            "personality_traits": {
                "openness": {"rating": 2, "modifier": -1},
                "conscientiousness": {"rating": 5, "modifier": 2},
                "extraversion": {"rating": 5, "modifier": 2},
                "agreeableness": {"rating": 3, "modifier": 0},
                "neuroticism": {"rating": 2, "behavioral_influence": "her faith gives her immense confidence and stability"}
            },
            "game_mechanics_summary": {
                "feats": ["War Caster", "Sentinel"],
                "special_abilities": ["Potent Spellcasting", "Healing Light"]
            }
        }
    }

    world_data = {
        "noble_houses": {
        }
    }
