#!/bin/bash
# Cross-platform timeout utilities for Claude Code hooks and commands
# Ensures compatibility between macOS (development) and Ubuntu (CI/production)

# File Justification Protocol:
# GOAL: Provide portable timeout function that works across macOS and Linux systems
# MODIFICATION: Implement OS detection and use appropriate timeout mechanisms
# NECESSITY: Essential for script reliability across development (macOS) and production (Linux) environments
# INTEGRATION PROOF: This is a utility function that can be sourced by existing shell scripts

# Portable timeout function
# Usage: portable_timeout <seconds> <command> [args...]
portable_timeout() {
    local timeout_duration="$1"
    shift

    # Validate timeout duration
    if ! [[ "$timeout_duration" =~ ^[0-9]+$ ]] || [[ "$timeout_duration" -lt 1 ]] || [[ "$timeout_duration" -gt 3600 ]]; then
        echo "Error: Invalid timeout duration: $timeout_duration (must be 1-3600 seconds)" >&2
        return 1
    fi

    # Detect operating system and use appropriate timeout mechanism
    case "$(uname -s)" in
        Darwin*)
            # macOS - check for available timeout implementations
            if command -v gtimeout >/dev/null 2>&1; then
                # GNU coreutils timeout (preferred - from brew install coreutils)
                gtimeout "$timeout_duration" "$@"
            elif command -v timeout >/dev/null 2>&1; then
                # BSD timeout (if available)
                timeout "$timeout_duration" "$@"
            else
                # Fallback using Perl (always available on macOS)
                /usr/bin/perl -e "
                    use POSIX ':sys_wait_h';
                    my \$timeout = $timeout_duration;
                    my \$pid = fork();
                    if (\$pid == 0) {
                        exec(@ARGV) or die \"exec failed: \$!\";
                    } elsif (\$pid > 0) {
                        my \$start = time();
                        while (time() - \$start < \$timeout) {
                            my \$result = waitpid(\$pid, WNOHANG);
                            if (\$result == \$pid) {
                                exit(\$? >> 8);
                            }
                            sleep(1);
                        }
                        kill('TERM', \$pid);
                        my \$terminated = waitpid(\$pid, 0);
                        if (\$terminated != \$pid) {
                            kill('KILL', \$pid);
                            waitpid(\$pid, 0);
                        }
                        exit(124);  # Standard timeout exit code
                    } else {
                        die \"fork failed: \$!\";
                    }
                " -- "$@"
            fi
            ;;
        Linux*)
            # Linux - use standard GNU timeout command
            if command -v timeout >/dev/null 2>&1; then
                timeout "$timeout_duration" "$@"
            else
                echo "Error: timeout command not available on Linux system" >&2
                return 1
            fi
            ;;
        *)
            # Unknown OS - try standard timeout, fallback to direct execution with warning
            if command -v timeout >/dev/null 2>&1; then
                timeout "$timeout_duration" "$@"
            else
                echo "Warning: timeout not available on $(uname -s), executing without timeout" >&2
                "$@"
            fi
            ;;
    esac
}

# Safe read with timeout for stdin operations
# Usage: safe_read_stdin <timeout_seconds>
safe_read_stdin() {
    local timeout_duration="${1:-5}"

    # Check if stdin is a terminal (interactive mode)
    if [ -t 0 ]; then
        # stdin is a terminal, no input expected
        echo ""
        return 0
    fi

    # Read stdin content within the timeout using portable_timeout and cat
    local input_data=""
    if input_data=$(portable_timeout "$timeout_duration" cat 2>/dev/null); then
        printf '%s' "$input_data"
    else
        local status=$?
        if [ -n "$input_data" ]; then
            # Even on timeout, return any buffered data that was read
            printf '%s' "$input_data"
        elif [ "$status" -eq 124 ]; then
            # Timed out without receiving input
            printf ''
        else
            # Unknown failure - degrade gracefully
            printf ''
        fi
    fi
}

# GitHub CLI operations with portable timeout
# Usage: gh_with_timeout <timeout_seconds> <gh_command> [args...]
gh_with_timeout() {
    local timeout_duration="$1"
    shift

    # Validate that gh command is available
    if ! command -v gh >/dev/null 2>&1; then
        echo "Error: GitHub CLI (gh) not available" >&2
        return 1
    fi

    # Use portable timeout for gh operations
    portable_timeout "$timeout_duration" gh "$@"
}

# Check if timeout is available and suggest installation if not
check_timeout_availability() {
    case "$(uname -s)" in
        Darwin*)
            if ! command -v timeout >/dev/null 2>&1 && ! command -v gtimeout >/dev/null 2>&1; then
                echo "INFO: For best compatibility, consider installing GNU coreutils:" >&2
                echo "  brew install coreutils" >&2
                echo "INFO: Falling back to Perl-based timeout implementation" >&2
            fi
            ;;
        Linux*)
            if ! command -v timeout >/dev/null 2>&1; then
                echo "WARNING: timeout command not available on Linux system" >&2
                echo "Consider installing: sudo apt-get install coreutils" >&2
                return 1
            fi
            ;;
    esac
    return 0
}

# Export functions for use in other scripts
export -f portable_timeout
export -f safe_read_stdin
export -f gh_with_timeout
export -f check_timeout_availability

# Auto-check timeout availability when script is sourced
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    # Script is being sourced, check timeout availability
    check_timeout_availability >/dev/null 2>&1
fi
