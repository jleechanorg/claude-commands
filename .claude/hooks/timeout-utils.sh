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

    # Helper to perform the actual read with timeout-protected cat
    safe_read_stdin__read_with_cat() {
        local data=""
        if data=$(portable_timeout "$timeout_duration" cat 2>/dev/null); then
            printf '%s' "$data"
            return 0
        fi

        local status=$?
        if [ -n "$data" ]; then
            # Even on timeout, return any buffered data that was read
            printf '%s' "$data"
        elif [ "$status" -eq 124 ]; then
            # Timed out without receiving input
            printf ''
        else
            # Unknown failure - degrade gracefully
            printf ''
        fi
    }

    # Check if stdin is a terminal (interactive mode)
    if [ -t 0 ]; then
        # Attempt to non-blockingly read any available data from the TTY
        if command -v python3 >/dev/null 2>&1; then
            local python_output
            python_output=$(python3 - "$timeout_duration" <<'PY'
import os
import select
import sys
import time

timeout = float(sys.argv[1])
fd = sys.stdin.buffer.fileno()
end_time = time.time() + timeout
chunks = []

while True:
    remaining = end_time - time.time()
    if remaining <= 0:
        break

    ready, _, _ = select.select([fd], [], [], remaining)
    if not ready:
        break

    try:
        data = os.read(fd, 4096)
    except BlockingIOError:
        continue

    if not data:
        break

    chunks.append(data)

    if len(data) < 4096:
        ready_again, _, _ = select.select([fd], [], [], 0)
        if not ready_again:
            break

sys.stdout.buffer.write(b"".join(chunks))
PY
)
            local python_status=$?
            if [ $python_status -eq 0 ] && [ -n "$python_output" ]; then
                printf '%s' "$python_output"
                return 0
            elif [ $python_status -eq 0 ]; then
                # No data was available within the timeout
                printf ''
                return 0
            fi
            # Fall back to cat-based reader if Python fails
        fi

        safe_read_stdin__read_with_cat
        return 0
    fi

    safe_read_stdin__read_with_cat
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
