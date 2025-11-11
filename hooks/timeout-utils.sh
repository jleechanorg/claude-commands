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

    # Validate timeout (integer within portable timeout range)
    if ! [[ "$timeout_duration" =~ ^[0-9]+$ ]] || [[ "$timeout_duration" -le 0 ]]; then
        echo "safe_read_stdin: invalid timeout '$timeout_duration'; defaulting to 5" >&2
        timeout_duration=5
    elif [[ "$timeout_duration" -gt 3600 ]]; then
        echo "safe_read_stdin: timeout '$timeout_duration' exceeds maximum of 3600; clamping" >&2
        timeout_duration=3600
    fi

    # Helper to perform the actual read with timeout-protected cat
    safe_read_stdin__read_with_cat() {
        local data
        data=$(portable_timeout "$timeout_duration" cat 2>/dev/null)
        local status=$?

        if [ "$status" -eq 0 ]; then
            printf '%s' "$data"
            return 0
        elif [ -n "$data" ]; then
            # Partial data on timeout - indicate truncation
            printf '%s[TIMEOUT_TRUNCATED]' "$data"
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
            local python_script
            local python_output
            local python_status
            local python_returned_data=false
            python_script=$'import os\nimport select\nimport sys\nimport time\n\ntry:\n    timeout = float(sys.argv[1])\nexcept (IndexError, ValueError):\n    timeout = 0.0\n\nif timeout <= 0:\n    sys.exit(0)\n\nfd = sys.stdin.buffer.fileno()\nend_time = time.time() + timeout\nchunks = []\nexit_code = 0\n\ntry:\n    while True:\n        remaining = end_time - time.time()\n        if remaining <= 0:\n            break\n\n        try:\n            ready, _, _ = select.select([fd], [], [], remaining)\n        except (OSError, ValueError):\n            exit_code = 1\n            break\n\n        if not ready:\n            break\n\n        try:\n            data = os.read(fd, 4096)\n        except BlockingIOError:\n            continue\n        except (OSError, ValueError):\n            exit_code = 1\n            break\n\n        if not data:\n            break\n\n        chunks.append(data)\n\n        if len(data) < 4096:\n            try:\n                ready_again, _, _ = select.select([fd], [], [], 0)\n            except (OSError, ValueError):\n                exit_code = 1\n                break\n            if not ready_again:\n                break\nexcept Exception:\n    exit_code = 1\nfinally:\n    try:\n        sys.stdout.buffer.write(b"".join(chunks))\n    except BrokenPipeError:\n        pass\n\nsys.exit(exit_code)'
            python_output=$(python3 -c "$python_script" "$timeout_duration" 2>/dev/null)
            python_status=$?

            if [ -n "$python_output" ]; then
                printf '%s' "$python_output"
                python_returned_data=true
            fi

            if [ "$python_status" -eq 0 ]; then
                # Python helper completed successfully; avoid re-reading the TTY
                printf ''
                return 0
            fi

            # Fall back to cat-based reader if Python exited abnormally
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
