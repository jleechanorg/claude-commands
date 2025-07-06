#!/usr/bin/env python3
"""Test cases for DefensiveNumericConverter"""

import os
import sys
import unittest

# Add the mvp_site directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from schemas.defensive_numeric_converter import DefensiveNumericConverter
from schemas.entities_simple import HealthStatus, Stats, Character, EntityType


class TestDefensiveNumericConverter(unittest.TestCase):
    """Test DefensiveNumericConverter functionality"""
    
    def test_hp_unknown_values(self):
        """Test HP fields with unknown values"""
        # Test HP conversion (case-insensitive)
        self.assertEqual(DefensiveNumericConverter.convert_value('hp', 'unknown'), 1)
        self.assertEqual(DefensiveNumericConverter.convert_value('hp', 'Unknown'), 1)
        self.assertEqual(DefensiveNumericConverter.convert_value('hp', 'UNKNOWN'), 1)
        self.assertEqual(DefensiveNumericConverter.convert_value('hp', None), 1)
        self.assertEqual(DefensiveNumericConverter.convert_value('hp', 'invalid'), 1)
        
        # Test HP_MAX conversion
        self.assertEqual(DefensiveNumericConverter.convert_value('hp_max', 'unknown'), 1)
        self.assertEqual(DefensiveNumericConverter.convert_value('hp_max', None), 1)
        
        # Test temp_hp conversion
        self.assertEqual(DefensiveNumericConverter.convert_value('temp_hp', 'unknown'), 0)
        self.assertEqual(DefensiveNumericConverter.convert_value('temp_hp', None), 0)
    
    def test_stats_unknown_values(self):
        """Test ability score fields with unknown values"""
        for stat in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
            self.assertEqual(DefensiveNumericConverter.convert_value(stat, 'unknown'), 10)
            self.assertEqual(DefensiveNumericConverter.convert_value(stat, None), 10)
            self.assertEqual(DefensiveNumericConverter.convert_value(stat, 'invalid'), 10)
    
    def test_level_unknown_values(self):
        """Test level field with unknown values"""
        self.assertEqual(DefensiveNumericConverter.convert_value('level', 'unknown'), 1)
        self.assertEqual(DefensiveNumericConverter.convert_value('level', None), 1)
        self.assertEqual(DefensiveNumericConverter.convert_value('level', 'invalid'), 1)
    
    def test_non_hp_defaults(self):
        """Test non-HP field defaults (gold, initiative, etc.)"""
        # Test gold (resource field)
        self.assertEqual(DefensiveNumericConverter.convert_value('gold', 'unknown'), 0)
        self.assertEqual(DefensiveNumericConverter.convert_value('gold', None), 0)
        
        # Test initiative (combat field)
        self.assertEqual(DefensiveNumericConverter.convert_value('initiative', 'unknown'), 0)
        self.assertEqual(DefensiveNumericConverter.convert_value('initiative', None), 0)
    
    def test_numeric_string_conversion(self):
        """Test valid numeric strings get converted properly"""
        self.assertEqual(DefensiveNumericConverter.convert_value('hp', '5'), 5)
        self.assertEqual(DefensiveNumericConverter.convert_value('strength', '15'), 15)
        self.assertEqual(DefensiveNumericConverter.convert_value('level', '3'), 3)
    
    def test_range_validation(self):
        """Test range validation for different field types"""
        # HP fields should never be less than 1
        self.assertEqual(DefensiveNumericConverter.convert_value('hp', 0), 1)
        self.assertEqual(DefensiveNumericConverter.convert_value('hp', -5), 1)
        
        # Temp HP should never be negative
        self.assertEqual(DefensiveNumericConverter.convert_value('temp_hp', -5), 0)
        
        # Ability scores should be clamped to 1-30
        self.assertEqual(DefensiveNumericConverter.convert_value('strength', 0), 1)
        self.assertEqual(DefensiveNumericConverter.convert_value('strength', 35), 30)
        self.assertEqual(DefensiveNumericConverter.convert_value('dexterity', -10), 1)
    
    def test_non_numeric_fields_unchanged(self):
        """Test that non-numeric fields are not converted"""
        self.assertEqual(DefensiveNumericConverter.convert_value('name', 'unknown'), 'unknown')
        self.assertEqual(DefensiveNumericConverter.convert_value('description', 'test'), 'test')
    
    def test_dict_conversion(self):
        """Test dictionary conversion functionality"""
        test_dict = {
            'hp': 'unknown',
            'hp_max': None,
            'strength': 'invalid',
            'level': '3',
            'name': 'Test Character',
            'nested': {
                'dexterity': 'unknown',
                'constitution': 25
            }
        }
        
        result = DefensiveNumericConverter.convert_dict(test_dict)
        
        self.assertEqual(result['hp'], 1)
        self.assertEqual(result['hp_max'], 1)
        self.assertEqual(result['strength'], 10)
        self.assertEqual(result['level'], 3)
        self.assertEqual(result['name'], 'Test Character')
        self.assertEqual(result['nested']['dexterity'], 10)
        self.assertEqual(result['nested']['constitution'], 25)


class TestEntitiesWithDefensiveConverter(unittest.TestCase):
    """Test entity classes using DefensiveNumericConverter"""
    
    def test_health_status_with_unknown_values(self):
        """Test HealthStatus with various unknown values"""
        health = HealthStatus(hp='unknown', hp_max=None, temp_hp='invalid')
        self.assertEqual(health.hp, 1)
        self.assertEqual(health.hp_max, 1)
        self.assertEqual(health.temp_hp, 0)
    
    def test_stats_with_unknown_values(self):
        """Test Stats with various unknown values"""
        stats = Stats(
            strength='unknown',
            dexterity=None,
            constitution='invalid',
            intelligence=15,
            wisdom='12',
            charisma=0
        )
        self.assertEqual(stats.strength, 10)
        self.assertEqual(stats.dexterity, 10)
        self.assertEqual(stats.constitution, 10)
        self.assertEqual(stats.intelligence, 15)
        self.assertEqual(stats.wisdom, 12)
        self.assertEqual(stats.charisma, 1)  # Clamped to minimum
    
    def test_character_with_unknown_level(self):
        """Test Character with unknown level"""
        health = HealthStatus(hp=10, hp_max=10)
        
        # This should not raise an exception
        character = Character(
            entity_id='pc_test_001',
            entity_type=EntityType.PLAYER_CHARACTER,
            display_name='Test Character',
            health=health,
            current_location='loc_test_001',
            level='unknown'
        )
        
        self.assertEqual(character.level, 1)
    
    def test_hp_clamping_after_conversion(self):
        """Test that HP is clamped to hp_max after conversion"""
        # HP=10, HP_MAX=unknown (converts to 1) -> HP should be clamped to 1
        health = HealthStatus(hp=10, hp_max='unknown')
        self.assertEqual(health.hp, 1)
        self.assertEqual(health.hp_max, 1)
        
        # HP=unknown (converts to 1), HP_MAX=5 -> HP should be 1
        health = HealthStatus(hp='unknown', hp_max=5)
        self.assertEqual(health.hp, 1)
        self.assertEqual(health.hp_max, 5)


if __name__ == '__main__':
    unittest.main()