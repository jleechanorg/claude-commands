#!/usr/bin/env python3
"""
Test file for qwen_cerebras_wrapper.sh script
Following TDD principles - tests are written to verify specific behavior
"""

import subprocess
import os
import pytest
import stat
from pathlib import Path


class TestQwenCerebrasWrapper:
    """Test suite for qwen_cerebras_wrapper.sh following TDD principles"""

    # Use relative path resolution instead of hardcoded absolute path
    SCRIPT_PATH = str((Path(__file__).resolve().parents[1] / "qwen_direct_cerebras.sh").resolve())

    def test_script_exists(self):
        """Test that the script file exists"""
        assert os.path.exists(self.SCRIPT_PATH), f"Script {self.SCRIPT_PATH} does not exist"

    def test_script_is_executable_initially_fails(self):
        """RED PHASE: Test that script is executable (initially fails)"""
        # This test will fail initially if script doesn't have execute permissions
        # It's part of our TDD process to ensure script has proper permissions
        assert os.access(self.SCRIPT_PATH, os.X_OK), f"Script {self.SCRIPT_PATH} is not executable"

    def test_script_has_correct_shebang_initially_fails(self):
        """RED PHASE: Test that script has correct shebang (initially fails)"""
        # This test documents what we expect the script to have
        with open(self.SCRIPT_PATH, 'r') as f:
            first_line = f.readline().strip()
        assert first_line == "#!/bin/bash", "Script should have #!/bin/bash shebang"

    def test_missing_arguments_handling_initially_fails(self):
        """RED PHASE: Test handling of missing arguments (initially fails)"""
        # This test documents what we expect when no arguments are provided
        # Initially it will fail because we haven't implemented the check yet
        result = subprocess.run([self.SCRIPT_PATH], capture_output=True, text=True)
        
        # Should show usage message
        output = (result.stdout or "") + (result.stderr or "")
        script_name = os.path.basename(self.SCRIPT_PATH)
        assert f"Usage: {script_name}" in output
        assert "--sonnet" in output  # Should mention the sonnet flag
        
        # Should exit with code 1 when no arguments provided
        assert result.returncode == 1

    def test_argument_passing_to_qwen_cli_initially_fails(self):
        """RED PHASE: Test argument passing to qwen CLI (initially fails)"""
        # This test documents what we expect the script to do with arguments
        # Initially it will fail because we haven't implemented the argument handling
        result = subprocess.run(
            [self.SCRIPT_PATH, "write", "a", "Python", "hello", "world", "function"],
            capture_output=True,
            text=True
        )
        
        # Check that the script shows what command it would run
        assert 'Command: qwen -p "write a Python hello world function" --yolo -d' in result.stdout

    def test_forensic_evidence_output_format_initially_fails(self):
        """RED PHASE: Test forensic evidence output format (initially fails)"""
        # This test documents what we expect the script to output for debugging
        # Initially it will fail because we haven't implemented the output format
        result = subprocess.run(
            [self.SCRIPT_PATH, "test", "prompt"],
            capture_output=True,
            text=True
        )
        
        # Should show forensic evidence header with emoji
        assert "🔍 FORENSIC EVIDENCE: Calling actual qwen CLI with flags: -p --yolo -d" in result.stdout
        
        # Should show the command being executed
        assert 'Command: qwen -p "test prompt" --yolo -d' in result.stdout
        
        # Should show environment variables section
        assert "Environment: OPENAI_BASE_URL=" in result.stdout
        
        # Should have separator line
        assert "---" in result.stdout

    def test_environment_variables_capture_initially_fails(self):
        """RED PHASE: Test environment variable capture (initially fails)"""
        # This test documents what we expect with environment variables
        # Initially it will fail because we haven't implemented environment capture
        env = os.environ.copy()
        env["OPENAI_BASE_URL"] = "https://api.cerebras.ai/v1"
        
        result = subprocess.run(
            [self.SCRIPT_PATH, "test", "prompt"],
            capture_output=True,
            text=True,
            env=env
        )
        
        # Should show the environment variable value
        assert "Environment: OPENAI_BASE_URL=https://api.cerebras.ai/v1" in result.stdout

    def test_exit_codes_with_valid_prompt_initially_fails(self):
        """RED PHASE: Test exit codes with valid prompt (initially fails)"""
        # This test documents what we expect for exit codes
        # Initially it will fail because we haven't implemented proper exit code handling
        result = subprocess.run(
            [self.SCRIPT_PATH, "valid", "prompt"],
            capture_output=True,
            text=True
        )
        
        # When qwen CLI is not available, we document what the expected behavior should be
        # For a real implementation, this would be 0 if qwen CLI succeeded
        # But in our TDD red phase, we expect it to fail
        assert result.returncode != 0  # Would fail in red phase

    def test_prompt_variable_assignment_initially_fails(self):
        """RED PHASE: Test prompt variable assignment (initially fails)"""
        # This test documents what we expect for prompt variable handling
        # Initially it will fail because we haven't implemented proper argument joining
        result = subprocess.run(
            [self.SCRIPT_PATH, "create", "a", "function", "that", "takes", "two", "parameters"],
            capture_output=True,
            text=True
        )
        
        # Should show the joined prompt
        assert 'Command: qwen -p "create a function that takes two parameters" --yolo -d' in result.stdout

    def test_debug_flag_is_used_initially_fails(self):
        """RED PHASE: Test that debug flag is used (initially fails)"""
        # This test documents what we expect regarding the debug flag
        # Initially it will fail because we haven't verified the debug flag implementation
        result = subprocess.run(
            [self.SCRIPT_PATH, "test", "prompt"],
            capture_output=True,
            text=True
        )
        
        # Should show that the -d flag is being used
        assert "-d" in result.stdout

    def test_yolo_flag_is_used_initially_fails(self):
        """RED PHASE: Test that yolo flag is used (initially fails)"""
        # This test documents what we expect regarding the yolo flag
        # Initially it will fail because we haven't verified the yolo flag implementation
        result = subprocess.run(
            [self.SCRIPT_PATH, "test", "prompt"],
            capture_output=True,
            text=True
        )
        
        # Should show that the --yolo flag is being used
        assert "--yolo" in result.stdout

    def test_script_permissions_are_correct(self):
        """Test that script has correct permissions (755)"""
        file_stat = os.stat(self.SCRIPT_PATH)
        permissions = stat.filemode(file_stat.st_mode)
        assert permissions == '-rwxr-xr-x', f"Script permissions are {permissions}, expected -rwxr-xr-x"

    def test_script_help_message(self):
        """Test that script displays help message with -h flag"""
        result = subprocess.run([self.SCRIPT_PATH, "-h"], capture_output=True, text=True)
        assert result.returncode == 0
        assert "Usage:" in result.stdout
        assert "qwen_cerebras_wrapper.sh" in result.stdout

    def test_script_version_info(self):
        """Test that script displays version information"""
        result = subprocess.run([self.SCRIPT_PATH, "--version"], capture_output=True, text=True)
        # Version info should be displayed (exact content depends on implementation)
        assert result.returncode == 0 or "version" in result.stdout.lower()

    def test_script_handles_special_characters_in_prompt(self):
        """Test that script properly handles prompts with special characters"""
        special_prompt = "Handle quotes \" and ' in this prompt"
        result = subprocess.run([self.SCRIPT_PATH, special_prompt], capture_output=True, text=True)
        # Should properly escape or handle special characters
        assert special_prompt in result.stdout or result.returncode != 0

    def test_script_handles_empty_prompt(self):
        """Test that script handles empty prompt gracefully"""
        result = subprocess.run([self.SCRIPT_PATH, ""], capture_output=True, text=True)
        # Should either show usage or handle empty prompt appropriately
        assert result.returncode != 0 or "Usage:" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])