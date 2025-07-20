"""Memory Enhancement Hook for Claude Commands
Integrates Memory MCP auto-read into slash command processing.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'mvp_site'))

from memory_integration import memory_integration
import logging_util

logger = logging_util.getLogger(__name__)

def enhance_command_with_memory(command_line: str, interpretation_result: dict = None) -> str:
    """
    Enhance command execution with relevant memory context.
    
    Args:
        command_line: Original command input like "/debug /learn git workflow issues"
        interpretation_result: Result from composition hook (optional)
    
    Returns:
        str: Enhanced prompt with memory context injected
    """
    try:
        # Commands that benefit from memory enhancement
        memory_enhanced_commands = {
            '/learn', '/debug', '/think', '/analyze', '/fix', 
            '/troubleshoot', '/investigate', '/research', '/review'
        }
        
        # Extract the main command
        if interpretation_result:
            main_command = interpretation_result.get('protocol_command', '')
            args_text = ' '.join(interpretation_result.get('arguments', []))
            search_context = f"{main_command} {args_text}"
        else:
            # Parse command directly
            tokens = command_line.strip().split()
            main_command = tokens[0] if tokens else ''
            search_context = command_line
        
        # Check if this command should be enhanced
        if not any(cmd in command_line for cmd in memory_enhanced_commands):
            return ""  # No enhancement needed
        
        logger.debug(f"Enhancing command with memory: {main_command}")
        
        # Get relevant memory context
        memory_context = memory_integration.get_enhanced_response_context(search_context)
        
        if memory_context:
            logger.info(f"Injected memory context for command: {main_command}")
            return memory_context
        else:
            logger.debug("No relevant memory context found")
            return ""
            
    except Exception as e:
        logger.error(f"Memory enhancement failed: {e}")
        return ""

def should_enhance_command(command_line: str) -> bool:
    """Check if command should be enhanced with memory"""
    enhance_commands = {
        '/learn', '/debug', '/think', '/analyze', '/fix',
        '/troubleshoot', '/investigate', '/research', '/review',
        '/replicate', '/understand', '/explain'
    }
    
    return any(cmd in command_line for cmd in enhance_commands)

def get_memory_enhanced_prompt(base_prompt: str, command_line: str, interpretation_result: dict = None) -> str:
    """
    Get a memory-enhanced version of the prompt.
    
    Args:
        base_prompt: The original command prompt
        command_line: User's command input  
        interpretation_result: Parsed command structure
    
    Returns:
        str: Enhanced prompt with memory context
    """
    if not should_enhance_command(command_line):
        return base_prompt
    
    memory_context = enhance_command_with_memory(command_line, interpretation_result)
    
    if memory_context:
        # Inject memory context at the beginning
        enhanced_prompt = f"""
{memory_context}

## Original Request
{base_prompt}

**Note**: The above memory context is provided automatically to enhance response accuracy. Use it to inform your response but focus on the user's specific request."""
        return enhanced_prompt
    
    return base_prompt

# Integration functions for the command system
def memory_pre_process_hook(command_line: str) -> dict:
    """
    Pre-processing hook that can be called before command execution.
    
    Returns:
        dict: Memory enhancement metadata
    """
    return {
        'memory_enhanced': should_enhance_command(command_line),
        'memory_context_available': bool(enhance_command_with_memory(command_line))
    }

def memory_post_process_hook(command_line: str, result: str) -> str:
    """
    Post-processing hook that can enhance the result.
    
    Returns:
        str: Enhanced result (currently just passes through)
    """
    # For now, enhancement happens pre-execution
    # Could add memory storage of results here in future
    return result

# Example usage and testing
if __name__ == "__main__":
    test_commands = [
        "/learn git workflow patterns",
        "/debug test failures in PR #123", 
        "/think about architecture improvements",
        "/test src/",  # Should not be enhanced
        "/analyze memory leaks in performance",
        "/fix authentication issues"
    ]
    
    print("=== Memory Enhancement Hook Test ===\n")
    
    for cmd in test_commands:
        print(f"Command: {cmd}")
        should_enhance = should_enhance_command(cmd)
        print(f"Should enhance: {should_enhance}")
        
        if should_enhance:
            enhancement = enhance_command_with_memory(cmd)
            if enhancement:
                print("✅ Memory context available")
                print(f"Context preview: {enhancement[:100]}...")
            else:
                print("❌ No relevant memory context found")
        print()