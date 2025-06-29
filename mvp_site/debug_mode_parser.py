"""
Debug mode command parser for WorldArchitect.AI.
Handles parsing and validation of debug mode commands from user input.
"""
import re
from typing import Tuple, Optional


class DebugModeParser:
    """Parser for debug mode commands in god mode."""
    
    # Comprehensive patterns for enabling debug mode
    ENABLE_PATTERNS = [
        # Direct commands
        r'^enable\s+debug\s+mode$',
        r'^debug\s+mode\s+on$',
        r'^debug\s+on$',
        r'^turn\s+on\s+debug\s+mode$',
        r'^turn\s+debug\s+mode\s+on$',
        r'^activate\s+debug\s+mode$',
        r'^debug\s+mode\s+enable$',
        r'^set\s+debug\s+mode\s+on$',
        r'^start\s+debug\s+mode$',
        
        # With punctuation
        r'^enable\s+debug\s+mode[.!]?$',
        r'^debug\s+mode:\s*on$',
        r'^debug:\s*enable$',
        
        # Common variations
        r'^debugmode\s+on$',
        r'^debug-mode\s+on$',
        r'^enable\s+debugging$',
        r'^enable\s+debug$',  # Allow "enable debug" without "mode"
        r'^debugging\s+on$',
        
        # Conversational
        r'^i\s+want\s+to\s+enable\s+debug\s+mode$',
        r'^please\s+enable\s+debug\s+mode$',
        r'^can\s+you\s+enable\s+debug\s+mode[?]?$',
        r'^let\'?s\s+turn\s+on\s+debug\s+mode$',
        r'^show\s+me\s+debug\s+mode$',
        r'^show\s+debug\s+info$',
        
        # Flexible variations
        r'^enable\s+debug\s+mode\s+please$',  # Allow "please" at end
    ]
    
    # Comprehensive patterns for disabling debug mode
    DISABLE_PATTERNS = [
        # Direct commands
        r'^disable\s+debug\s+mode$',
        r'^debug\s+mode\s+off$',
        r'^debug\s+off$',
        r'^turn\s+off\s+debug\s+mode$',
        r'^turn\s+debug\s+mode\s+off$',
        r'^deactivate\s+debug\s+mode$',
        r'^debug\s+mode\s+disable$',
        r'^set\s+debug\s+mode\s+off$',
        r'^stop\s+debug\s+mode$',
        r'^exit\s+debug\s+mode$',
        r'^quit\s+debug\s+mode$',
        
        # With punctuation
        r'^disable\s+debug\s+mode[.!]?$',
        r'^debug\s+mode:\s*off$',
        r'^debug:\s*disable$',
        
        # Common variations
        r'^debugmode\s+off$',
        r'^debug-mode\s+off$',
        r'^disable\s+debugging$',
        r'^disable\s+debug$',
        r'^debugging\s+off$',
        
        # Conversational
        r'^i\s+want\s+to\s+disable\s+debug\s+mode$',
        r'^please\s+disable\s+debug\s+mode$',
        r'^can\s+you\s+disable\s+debug\s+mode[?]?$',
        r'^let\'?s\s+turn\s+off\s+debug\s+mode$',
        r'^hide\s+debug\s+mode$',
        r'^hide\s+debug\s+info$',
        r'^no\s+more\s+debug\s+mode$',
    ]
    
    # Patterns that might be confused but should NOT trigger debug mode
    NEGATIVE_PATTERNS = [
        r'debug\s+the\s+',  # "debug the issue"
        r'debugging\s+my\s+',  # "debugging my code"
        r'in\s+debug\s+mode',  # "while in debug mode"
        r'debug\s+information',  # "show debug information about X"
        r'debug\s+.*\s+problem',  # "debug this problem"
        r'debug\s+.*\s+error',  # "debug the error"
    ]
    
    @classmethod
    def parse_debug_command(cls, user_input: str, current_mode: str) -> Tuple[Optional[str], bool]:
        """
        Parse user input for debug mode commands.
        
        Args:
            user_input: Raw user input string
            current_mode: Current interaction mode ('god' or 'character')
            
        Returns:
            Tuple of (command_type, should_update_state)
            - command_type: 'enable', 'disable', or None
            - should_update_state: True if state should be updated before LLM call
        """
        # Only process in god mode
        if current_mode != 'god':
            return None, False
            
        # Normalize input
        normalized = user_input.strip().lower()
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        # Check negative patterns first
        for pattern in cls.NEGATIVE_PATTERNS:
            if re.search(pattern, normalized):
                return None, False
        
        # Check enable patterns
        for pattern in cls.ENABLE_PATTERNS:
            if re.match(pattern, normalized):
                return 'enable', True
                
        # Check disable patterns
        for pattern in cls.DISABLE_PATTERNS:
            if re.match(pattern, normalized):
                return 'disable', True
                
        return None, False
    
    @classmethod
    def is_debug_toggle_command(cls, user_input: str, current_mode: str) -> bool:
        """
        Quick check if input is likely a debug toggle command.
        
        Args:
            user_input: Raw user input string
            current_mode: Current interaction mode
            
        Returns:
            True if this appears to be a debug toggle command
        """
        command_type, _ = cls.parse_debug_command(user_input, current_mode)
        return command_type is not None
    
    @classmethod
    def get_state_update_message(cls, command_type: str, new_state: bool) -> str:
        """
        Get appropriate system message for debug mode state change.
        
        Args:
            command_type: 'enable' or 'disable'
            new_state: New debug mode state
            
        Returns:
            System message to display to user
        """
        if command_type == 'enable' and new_state:
            return "[System Message: Debug mode enabled. You will now see DM commentary and game state changes.]"
        elif command_type == 'disable' and not new_state:
            return "[System Message: Debug mode disabled. DM commentary and state changes are now hidden.]"
        elif command_type == 'enable' and not new_state:
            return "[System Message: Debug mode is already enabled.]"
        elif command_type == 'disable' and new_state:
            return "[System Message: Debug mode is already disabled.]"
        else:
            return "[System Message: Debug mode command processed.]"