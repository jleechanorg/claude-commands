"""
Shared integration test library for Firebase and Gemini API setup.
Provides common utilities for integration tests that need to interact with external services.
"""
import os
import sys
import tempfile
import shutil
import signal
import platform
from typing import Optional, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging_util

# Configure logging
logging_util.basicConfig(level=logging_util.WARNING)
logger = logging_util.getLogger(__name__)


class TimeoutError(Exception):
    """Custom timeout exception for test timeouts"""
    pass


def timeout_handler(signum, frame):
    """Signal handler for test timeouts"""
    raise TimeoutError("Test timed out")


class IntegrationTestSetup:
    """Shared setup utilities for integration tests"""
    
    # Test configuration
    TEST_MODEL_OVERRIDE = 'gemini-1.5-flash'  # Faster model for tests
    TEST_SELECTED_PROMPTS = ['narrative']  # Minimal prompts for speed
    USE_TIMEOUT = platform.system() != 'Windows'  # Unix-only timeouts
    
    def __init__(self):
        self.original_cwd = os.getcwd()
        self.temp_prompts_dir = None
        self._setup_test_environment()
        
    def _setup_test_environment(self):
        """Set up the test environment with required configurations"""
        # Enable testing mode
        os.environ["TESTING"] = "true"
        
        # Set up signal handler for timeouts (Unix only)
        if self.USE_TIMEOUT:
            signal.signal(signal.SIGALRM, timeout_handler)
            
    def setup_api_keys(self, project_root: Optional[str] = None):
        """
        Set up Gemini API key from various possible locations.
        
        Args:
            project_root: Optional project root directory to check for keys
            
        Returns:
            bool: True if API key was found and set, False otherwise
        """
        if os.environ.get("GEMINI_API_KEY"):
            return True
            
        # Check multiple locations for API key
        key_locations = [
            os.path.expanduser("~/.gemini_api_key.txt"),
            os.path.expanduser("~/gemini_api_key.txt"),
        ]
        
        if project_root:
            key_locations.extend([
                os.path.join(project_root, "gemini_api_key.txt"),
                os.path.join(project_root, ".gemini_api_key.txt"),
                os.path.join(project_root, "mvp_site", "gemini_api_key.txt"),
            ])
        else:
            # Try current directory and parent
            key_locations.extend([
                "gemini_api_key.txt",
                ".gemini_api_key.txt",
                "../gemini_api_key.txt",
                "../.gemini_api_key.txt",
            ])
            
        for key_path in key_locations:
            if os.path.exists(key_path):
                try:
                    with open(key_path, "r") as key_file:
                        api_key = key_file.read().strip()
                        if api_key:
                            os.environ["GEMINI_API_KEY"] = api_key
                            logger.info(f"Loaded API key from: {key_path}")
                            return True
                except Exception as e:
                    logger.warning(f"Failed to read key from {key_path}: {e}")
                    
        logger.warning("No Gemini API key found in any expected location")
        return False
        
    def create_test_prompts_directory(self) -> str:
        """
        Create a temporary directory with minimal test prompt files.
        
        Returns:
            str: Path to the temporary prompts directory
        """
        self.temp_prompts_dir = tempfile.mkdtemp(prefix='test_prompts_')
        prompts_dir = os.path.join(self.temp_prompts_dir, 'prompts')
        os.makedirs(prompts_dir, exist_ok=True)
        
        # Create minimal test prompt files
        test_prompt_files = {
            'narrative_system_instruction.md': "Test narrative instruction.",
            'mechanics_system_instruction.md': "Test mechanics instruction.", 
            'calibration_instruction.md': "Test calibration instruction.",
            'destiny_ruleset.md': "Test destiny rules.",
            'game_state_instruction.md': "Test game state instruction.",
            'character_template.md': "Test character template.",
            'character_sheet_template.md': "Test character sheet.",
        }
        
        for filename, content in test_prompt_files.items():
            with open(os.path.join(prompts_dir, filename), 'w') as f:
                f.write(content)
                
        return self.temp_prompts_dir
        
    def cleanup(self):
        """Clean up temporary directories and restore original state"""
        if self.temp_prompts_dir and os.path.exists(self.temp_prompts_dir):
            shutil.rmtree(self.temp_prompts_dir, ignore_errors=True)
        os.chdir(self.original_cwd)
        
    def set_timeout(self, seconds: int):
        """
        Set a timeout for test execution (Unix only).
        
        Args:
            seconds: Timeout duration in seconds
        """
        if self.USE_TIMEOUT:
            signal.alarm(seconds)
            
    def cancel_timeout(self):
        """Cancel any active timeout"""
        if self.USE_TIMEOUT:
            signal.alarm(0)
            
    @staticmethod
    def create_test_headers(user_id: str) -> Dict[str, str]:
        """
        Create standard test headers for API requests.
        
        Args:
            user_id: Test user ID
            
        Returns:
            Dict of headers for test requests
        """
        return {
            'Content-Type': 'application/json',
            'X-Test-Bypass-Auth': 'true',
            'X-Test-User-ID': user_id
        }
        
    @staticmethod
    def mock_system_instructions() -> Dict[str, str]:
        """
        Get mock system instructions for testing.
        
        Returns:
            Dict of instruction type to content
        """
        return {
            'narrative': "Integration test narrative instruction.",
            'mechanics': "Integration test mechanics instruction.",
            'calibration': "Integration test calibration instruction."
        }


# Convenience functions for backward compatibility
def setup_integration_test_environment(project_root: Optional[str] = None) -> IntegrationTestSetup:
    """
    Set up a complete integration test environment.
    
    Args:
        project_root: Optional project root directory
        
    Returns:
        IntegrationTestSetup instance
    """
    setup = IntegrationTestSetup()
    setup.setup_api_keys(project_root)
    return setup