#!/usr/bin/env python3
"""Test cases for HP unknown value handling in HealthStatus"""

import os
import sys
import unittest

# Add the mvp_site directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from schemas.entities_pydantic import HealthStatus


class TestHPUnknownValues(unittest.TestCase):
    """Test HealthStatus handling of unknown/invalid HP values"""
    
    def test_hp_unknown_string(self):
        """Test HP='unknown' gets converted to 1"""
        health = HealthStatus(hp='unknown', hp_max=10)
        self.assertEqual(health.hp, 1)
        self.assertEqual(health.hp_max, 10)
    
    def test_hp_max_unknown_string(self):
        """Test HP_MAX='unknown' gets converted to 1, hp must be valid"""
        # hp must be <= hp_max after conversion, so use hp=1
        health = HealthStatus(hp=1, hp_max='unknown')
        self.assertEqual(health.hp, 1)
        self.assertEqual(health.hp_max, 1)
    
    def test_both_unknown_strings(self):
        """Test both HP and HP_MAX='unknown'"""
        health = HealthStatus(hp='unknown', hp_max='unknown')
        self.assertEqual(health.hp, 1)
        self.assertEqual(health.hp_max, 1)
    
    def test_hp_none_value(self):
        """Test HP=None gets converted to 1"""
        health = HealthStatus(hp=None, hp_max=10)
        self.assertEqual(health.hp, 1)
        self.assertEqual(health.hp_max, 10)
    
    def test_hp_max_none_value(self):
        """Test HP_MAX=None gets converted to 1, hp must be valid"""
        # hp must be <= hp_max after conversion, so use hp=1
        health = HealthStatus(hp=1, hp_max=None)
        self.assertEqual(health.hp, 1)
        self.assertEqual(health.hp_max, 1)
    
    def test_hp_invalid_string(self):
        """Test HP with invalid string gets converted to 1"""
        health = HealthStatus(hp='not_a_number', hp_max=10)
        self.assertEqual(health.hp, 1)
        self.assertEqual(health.hp_max, 10)
    
    def test_hp_empty_string(self):
        """Test HP with empty string gets converted to 1"""
        health = HealthStatus(hp='', hp_max=10)
        self.assertEqual(health.hp, 1)
        self.assertEqual(health.hp_max, 10)
    
    def test_hp_max_invalid_string(self):
        """Test HP_MAX with invalid string gets converted to 1, hp must be valid"""
        # hp must be <= hp_max after conversion, so use hp=1
        health = HealthStatus(hp=1, hp_max='not_a_number')
        self.assertEqual(health.hp, 1)
        self.assertEqual(health.hp_max, 1)
    
    def test_hp_numeric_string(self):
        """Test HP as numeric string gets converted properly"""
        health = HealthStatus(hp='5', hp_max='10')
        self.assertEqual(health.hp, 5)
        self.assertEqual(health.hp_max, 10)
    
    def test_hp_zero_string(self):
        """Test HP='0' gets converted properly"""
        health = HealthStatus(hp='0', hp_max=10)
        self.assertEqual(health.hp, 1)  # Gets clamped to minimum of 1
        self.assertEqual(health.hp_max, 10)
    
    def test_normal_numeric_values(self):
        """Test normal numeric values still work"""
        health = HealthStatus(hp=5, hp_max=10)
        self.assertEqual(health.hp, 5)
        self.assertEqual(health.hp_max, 10)
    
    def test_hp_exceeds_max_after_conversion(self):
        """Test validation still works after conversion"""
        from pydantic import ValidationError
        
        # HP=5 exceeds converted hp_max=1, should raise ValidationError
        with self.assertRaises(ValidationError) as context:
            HealthStatus(hp=5, hp_max='unknown')
        
        self.assertIn("cannot exceed max HP", str(context.exception))
    
    def test_negative_hp_values(self):
        """Test negative HP and HP_MAX values get converted by DefensiveNumericConverter"""
        # Test negative HP - gets converted to 1 by DefensiveNumericConverter
        health = HealthStatus(hp=-5, hp_max=10)
        self.assertEqual(health.hp, 1)  # Converted to safe default
        self.assertEqual(health.hp_max, 10)
        
        # Test negative HP_MAX - gets converted to 1 by DefensiveNumericConverter
        health = HealthStatus(hp=1, hp_max=-10)
        self.assertEqual(health.hp, 1)
        self.assertEqual(health.hp_max, 1)  # Converted to safe default


if __name__ == '__main__':
    unittest.main()