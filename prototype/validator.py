"""
Base validator class and interface for narrative validation.
All validator implementations should inherit from this base class.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationResult:
    """Standardized validation result format."""
    
    def __init__(self):
        self.all_entities_present = False
        self.entities_found = []
        self.entities_missing = []
        self.confidence = 0.0
        self.errors = []
        self.warnings = []
        self.metadata = {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "all_entities_present": self.all_entities_present,
            "entities_found": self.entities_found,
            "entities_missing": self.entities_missing,
            "confidence": self.confidence,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationResult':
        """Create ValidationResult from dictionary."""
        result = cls()
        result.all_entities_present = data.get("all_entities_present", False)
        result.entities_found = data.get("entities_found", [])
        result.entities_missing = data.get("entities_missing", [])
        result.confidence = data.get("confidence", 0.0)
        result.errors = data.get("errors", [])
        result.warnings = data.get("warnings", [])
        result.metadata = data.get("metadata", {})
        return result


class BaseValidator(ABC):
    """Abstract base class for all validators."""
    
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(self.name)
        self._metrics = {
            "validations_performed": 0,
            "total_time": 0.0,
            "errors_encountered": 0
        }
        
    @abstractmethod
    def validate(self, 
                 narrative_text: str, 
                 expected_entities: List[str],
                 location: str = None,
                 **kwargs) -> ValidationResult:
        """
        Validate narrative text for entity presence.
        
        Args:
            narrative_text: The narrative to validate
            expected_entities: List of entity names that should be present
            location: Optional location context
            **kwargs: Additional validator-specific parameters
            
        Returns:
            ValidationResult object with validation findings
        """
        pass
    
    def __call__(self, 
                 narrative_text: str, 
                 expected_entities: List[str],
                 location: str = None,
                 **kwargs) -> Dict[str, Any]:
        """
        Make validator callable for test harness compatibility.
        Returns dictionary format expected by test harness.
        """
        try:
            # Increment metrics
            self._metrics["validations_performed"] += 1
            
            # Perform validation
            result = self.validate(narrative_text, expected_entities, location, **kwargs)
            
            # Log validation
            self.logger.debug(
                f"Validated narrative: found {len(result.entities_found)}/{len(expected_entities)} entities"
            )
            
            # Return dictionary format
            return result.to_dict()
            
        except Exception as e:
            self._metrics["errors_encountered"] += 1
            self.logger.error(f"Validation error: {str(e)}")
            
            # Return error result
            error_result = ValidationResult()
            error_result.entities_missing = expected_entities
            error_result.errors.append(str(e))
            return error_result.to_dict()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get validator performance metrics."""
        return {
            "validator_name": self.name,
            "metrics": self._metrics.copy()
        }
    
    def reset_metrics(self):
        """Reset performance metrics."""
        self._metrics = {
            "validations_performed": 0,
            "total_time": 0.0,
            "errors_encountered": 0
        }


class EntityManifest:
    """
    Helper class for managing entity information during validation.
    Mirrors the game state entity manifest structure.
    """
    
    def __init__(self, entities: List[str], location: str = None):
        self.location = location
        self.entities = []
        self.timestamp = datetime.now().isoformat()
        
        # Build entity records
        for entity_name in entities:
            self.entities.append({
                "id": f"{entity_name.lower()}_001",
                "name": entity_name,
                "type": "player_character",
                "status": ["conscious"],
                "descriptors": self._generate_descriptors(entity_name)
            })
        
        self.entity_count = len(self.entities)
    
    def _generate_descriptors(self, entity_name: str) -> List[str]:
        """Generate descriptors for an entity based on known patterns."""
        descriptors = [entity_name.lower()]
        
        # Add known aliases
        if entity_name.lower() == "gideon":
            descriptors.extend(["ser vance", "knight", "warrior", "the knight"])
        elif entity_name.lower() == "rowan":
            descriptors.extend(["healer", "cleric", "the healer", "the cleric"])
            
        return descriptors
    
    def get_all_descriptors(self) -> Dict[str, str]:
        """Get mapping of all descriptors to entity names."""
        descriptor_map = {}
        for entity in self.entities:
            for descriptor in entity["descriptors"]:
                descriptor_map[descriptor] = entity["name"]
        return descriptor_map
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format matching game state structure."""
        return {
            "location": self.location,
            "entities": self.entities,
            "timestamp": self.timestamp,
            "entity_count": self.entity_count
        }