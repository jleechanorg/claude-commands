"""
Claude service for handling AI interactions and header compliance tracking.
Manages header validation and compliance monitoring for Claude responses.
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import logging_util
from constants import (
    HEADER_COMPLIANCE_COLLECTION,
    HEADER_PATTERN,
    MIN_COMPLIANCE_RATE,
    PUSH_COMPLIANCE_COLLECTION,
    MIN_PUSH_COMPLIANCE_RATE,
    PUSH_VERIFICATION_COMMANDS
)
from firestore_service import (
    track_header_compliance, 
    get_session_compliance_rate,
    track_push_compliance,
    get_session_push_compliance_rate
)

# Configure logging
logger = logging_util.getLogger(__name__)


def validate_header_compliance(response_text: str) -> bool:
    """
    Validate if Claude response contains mandatory branch header.
    
    Expected format: [Local: <branch> | Remote: <upstream> | PR: <number> <url>]
    
    Args:
        response_text: The Claude response text to validate
        
    Returns:
        bool: True if header is present and valid, False otherwise
    """
    if not response_text or not isinstance(response_text, str):
        return False
    
    # Check if response starts with the expected header pattern
    header_pattern = re.compile(HEADER_PATTERN, re.MULTILINE)
    match = header_pattern.match(response_text.strip())
    
    return match is not None


def parse_header_components(response_text: str) -> Optional[Dict[str, str]]:
    """
    Extract branch, remote, and PR info from header.
    
    Args:
        response_text: The Claude response text containing header
        
    Returns:
        dict: Header components or None if parsing fails
        {
            'local_branch': str,
            'remote_branch': str,
            'pr_info': str
        }
    """
    if not validate_header_compliance(response_text):
        return None
    
    # Enhanced pattern to capture components
    pattern = r'^\[Local: (.+?) \| Remote: (.+?) \| PR: (.+?)\]'
    match = re.match(pattern, response_text.strip())
    
    if match:
        return {
            'local_branch': match.group(1).strip(),
            'remote_branch': match.group(2).strip(),
            'pr_info': match.group(3).strip()
        }
    
    return None


def process_claude_response(session_id: str, response_text: str) -> Dict[str, any]:
    """
    Process Claude response and track header compliance.
    
    Args:
        session_id: Current session identifier
        response_text: The Claude response text
        
    Returns:
        dict: Processing results including compliance status
        {
            'has_header': bool,
            'header_components': dict or None,
            'compliance_rate': float,
            'response_preview': str
        }
    """
    try:
        # Validate header compliance
        has_header = validate_header_compliance(response_text)
        
        # Parse header components if valid
        header_components = None
        if has_header:
            header_components = parse_header_components(response_text)
        
        # Track compliance in Firestore
        track_header_compliance(session_id, response_text, has_header)
        
        # Get updated compliance rate
        compliance_rate = get_session_compliance_rate(session_id)
        
        # Get session statistics for total_responses
        from firestore_service import get_session_compliance_stats
        stats = get_session_compliance_stats(session_id)
        total_responses = stats.get('total_responses', 0)
        
        # Create response preview (first 100 chars)
        response_preview = response_text[:100] if response_text else ""
        
        result = {
            'has_header': has_header,
            'header_components': header_components,
            'compliance_rate': compliance_rate,
            'response_preview': response_preview,
            'total_responses': total_responses
        }
        
        logger.info(f"Processed Claude response for session {session_id}: "
                   f"has_header={has_header}, compliance_rate={compliance_rate:.2f}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing Claude response for session {session_id}: {str(e)}")
        # Return safe defaults on error
        return {
            'has_header': False,
            'header_components': None,
            'compliance_rate': 0.0,
            'response_preview': response_text[:100] if response_text else "",
            'total_responses': 0
        }


def get_compliance_status(session_id: str) -> Dict[str, any]:
    """
    Get current compliance status for a session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        dict: Compliance status information
        {
            'compliance_rate': float,
            'is_compliant': bool,
            'total_responses': int,
            'compliant_responses': int
        }
    """
    try:
        compliance_rate = get_session_compliance_rate(session_id)
        is_compliant = compliance_rate >= MIN_COMPLIANCE_RATE
        
        # Get detailed statistics from Firestore
        from firestore_service import get_session_compliance_stats
        stats = get_session_compliance_stats(session_id)
        
        return {
            'compliance_rate': compliance_rate,
            'is_compliant': is_compliant,
            'total_responses': stats.get('total_responses', 0),
            'compliant_responses': stats.get('compliant_responses', 0)
        }
        
    except Exception as e:
        logger.error(f"Error getting compliance status for session {session_id}: {str(e)}")
        return {
            'compliance_rate': 0.0,
            'is_compliant': False,
            'total_responses': 0,
            'compliant_responses': 0
        }


def generate_compliance_alert(compliance_rate: float) -> Optional[str]:
    """
    Generate user-friendly compliance alert message.
    
    Args:
        compliance_rate: Current compliance rate (0.0 to 1.0)
        
    Returns:
        str: Alert message or None if no alert needed
    """
    if compliance_rate < MIN_COMPLIANCE_RATE:
        percentage = int(compliance_rate * 100)
        return (f"Header compliance is at {percentage}%. "
                f"Minimum required: {int(MIN_COMPLIANCE_RATE * 100)}%")
    
    return None


def validate_multiple_responses(responses: List[str]) -> List[Dict[str, any]]:
    """
    Validate header compliance for multiple responses.
    
    Args:
        responses: List of Claude response texts
        
    Returns:
        list: List of validation results for each response
    """
    results = []
    
    for i, response in enumerate(responses):
        has_header = validate_header_compliance(response)
        header_components = parse_header_components(response) if has_header else None
        
        # Handle non-string responses safely
        if isinstance(response, str):
            response_preview = response[:100]
        else:
            response_preview = str(response)[:100] if response is not None else ""
        
        results.append({
            'index': i,
            'has_header': has_header,
            'header_components': header_components,
            'response_preview': response_preview
        })
    
    return results


# --- PUSH COMPLIANCE TRACKING ---

def detect_push_command(command_text: str) -> Optional[str]:
    """
    Detect if a command text contains a git push command.
    
    Args:
        command_text: The command text to analyze
        
    Returns:
        str: The detected push command or None if not found
    """
    if not command_text or not isinstance(command_text, str):
        return None
    
    # Common git push patterns
    push_patterns = [
        r'git\s+push\s+origin\s+HEAD:\w+',
        r'git\s+push\s+--set-upstream\s+origin\s+\w+',
        r'git\s+push\s+-u\s+origin\s+\w+',
        r'git\s+push\s+origin\s+[\w\-]+',
        r'git\s+push\s+[\w\-]+\s+[\w\-]+',
        r'git\s+push\s+\w+'
    ]
    
    for pattern in push_patterns:
        match = re.search(pattern, command_text, re.IGNORECASE)
        if match:
            return match.group(0)
    
    return None


def extract_verification_command(command_text: str) -> Optional[str]:
    """
    Extract push verification command from command text.
    
    Args:
        command_text: The command text to analyze
        
    Returns:
        str: The verification command or None if not found
    """
    if not command_text or not isinstance(command_text, str):
        return None
    
    # Check for verification commands
    for verification_cmd in PUSH_VERIFICATION_COMMANDS:
        if verification_cmd in command_text.lower():
            return verification_cmd
    
    return None


def analyze_push_verification_output(verification_output: str, push_command: str) -> bool:
    """
    Analyze verification command output to determine if push was successful.
    
    Args:
        verification_output: Output from verification command
        push_command: The original push command
        
    Returns:
        bool: True if push appears to be verified, False otherwise
    """
    if not verification_output or not isinstance(verification_output, str):
        return False
    
    output_lower = verification_output.lower()
    
    # Positive indicators of successful push
    positive_indicators = [
        'ahead',
        'up to date',
        'fast-forward',
        'merged',
        'origin/',
        'remotes/origin/',
        'pull request',
        'pr #'
    ]
    
    # Negative indicators suggesting push failed
    negative_indicators = [
        'error',
        'failed',
        'rejected',
        'not found',
        'no upstream',
        'no remote',
        'fatal'
    ]
    
    # Check for negative indicators first
    for indicator in negative_indicators:
        if indicator in output_lower:
            return False
    
    # Check for positive indicators
    for indicator in positive_indicators:
        if indicator in output_lower:
            return True
    
    return False


def process_push_compliance(session_id: str, command_text: str, verification_output: str = None) -> Dict[str, any]:
    """
    Process command text for push compliance tracking.
    
    Args:
        session_id: Current session identifier
        command_text: The command text to analyze
        verification_output: Optional verification command output
        
    Returns:
        dict: Processing results including push compliance status
        {
            'has_push_command': bool,
            'push_command': str or None,
            'push_attempted': bool,
            'push_verified': bool,
            'verification_command': str or None,
            'push_compliance_rate': float
        }
    """
    try:
        # Detect push command
        push_command = detect_push_command(command_text)
        has_push_command = push_command is not None
        
        # Extract verification command
        verification_command = extract_verification_command(command_text)
        
        # Analyze verification output
        push_verified = False
        if verification_output and has_push_command:
            push_verified = analyze_push_verification_output(verification_output, push_command)
        
        # Track push compliance if push was attempted
        if has_push_command:
            track_push_compliance(
                session_id=session_id,
                push_command=push_command,
                push_attempted=True,
                push_verified=push_verified,
                verification_command=verification_command,
                verification_output=verification_output
            )
        
        # Get updated compliance rate
        push_compliance_rate = get_session_push_compliance_rate(session_id)
        
        result = {
            'has_push_command': has_push_command,
            'push_command': push_command,
            'push_attempted': has_push_command,
            'push_verified': push_verified,
            'verification_command': verification_command,
            'push_compliance_rate': push_compliance_rate
        }
        
        logger.info(f"Processed push compliance for session {session_id}: "
                   f"has_push={has_push_command}, verified={push_verified}, "
                   f"compliance_rate={push_compliance_rate:.2f}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing push compliance for session {session_id}: {str(e)}")
        return {
            'has_push_command': False,
            'push_command': None,
            'push_attempted': False,
            'push_verified': False,
            'verification_command': None,
            'push_compliance_rate': 0.0
        }


def get_push_compliance_status(session_id: str) -> Dict[str, any]:
    """
    Get current push compliance status for a session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        dict: Push compliance status information
        {
            'compliance_rate': float,
            'is_compliant': bool,
            'total_pushes': int,
            'verified_pushes': int
        }
    """
    try:
        compliance_rate = get_session_push_compliance_rate(session_id)
        is_compliant = compliance_rate >= MIN_PUSH_COMPLIANCE_RATE
        
        # Get detailed statistics from Firestore
        from firestore_service import get_session_push_compliance_stats
        stats = get_session_push_compliance_stats(session_id)
        
        return {
            'compliance_rate': compliance_rate,
            'is_compliant': is_compliant,
            'total_pushes': stats.get('total_pushes', 0),
            'verified_pushes': stats.get('verified_pushes', 0)
        }
        
    except Exception as e:
        logger.error(f"Error getting push compliance status for session {session_id}: {str(e)}")
        return {
            'compliance_rate': 0.0,
            'is_compliant': False,
            'total_pushes': 0,
            'verified_pushes': 0
        }


def generate_push_compliance_alert(compliance_rate: float) -> Optional[str]:
    """
    Generate user-friendly push compliance alert message.
    
    Args:
        compliance_rate: Current push compliance rate (0.0 to 1.0)
        
    Returns:
        str: Alert message or None if no alert needed
    """
    if compliance_rate < MIN_PUSH_COMPLIANCE_RATE:
        percentage = int(compliance_rate * 100)
        return (f"Push compliance is at {percentage}%. "
                f"Minimum required: {int(MIN_PUSH_COMPLIANCE_RATE * 100)}%. "
                f"Remember to verify push success with 'gh pr view' or 'git log origin/branch'")
    
    return None


def validate_multiple_push_commands(commands: List[str]) -> List[Dict[str, any]]:
    """
    Validate push compliance for multiple commands.
    
    Args:
        commands: List of command texts
        
    Returns:
        list: List of validation results for each command
    """
    results = []
    
    for i, command in enumerate(commands):
        push_command = detect_push_command(command)
        has_push_command = push_command is not None
        verification_command = extract_verification_command(command)
        
        results.append({
            'index': i,
            'has_push_command': has_push_command,
            'push_command': push_command,
            'verification_command': verification_command,
            'command_preview': command[:100] if isinstance(command, str) else str(command)[:100]
        })
    
    return results