#!/usr/bin/env bash
# Test script to simulate parallel memory backups from two different environments
# This will help identify race conditions and data loss scenarios

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test configuration
TEST_DIR="/tmp/memory-backup-test-$$"
REPO_DIR="$TEST_DIR/test-repo"
ENV1_DIR="$TEST_DIR/env1"
ENV2_DIR="$TEST_DIR/env2"
TEST_SCRIPT="$TEST_DIR/memory_backup_fixed.sh"

# Logging
log() {
    echo -e "${GREEN}[TEST]${NC} $(date '+%H:%M:%S.%3N'): $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%H:%M:%S.%3N'): $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%H:%M:%S.%3N'): $1"
}

# Cleanup function
cleanup() {
    log "Cleaning up test environment..."
    rm -rf "$TEST_DIR"
}

# Setup test environment
setup_test_env() {
    log "Setting up test environment in $TEST_DIR"

    # Create test directories
    mkdir -p "$ENV1_DIR/.cache/mcp-memory"
    mkdir -p "$ENV2_DIR/.cache/mcp-memory"
    mkdir -p "$REPO_DIR"

    # Initialize git repository
    cd "$REPO_DIR"
    git init
    git config user.email "test@example.com"
    git config user.name "Test User"
    echo "# Test Memory Backup Repo" > README.md
    git add README.md
    git commit -m "Initial commit"
    git branch -M main

    # Copy the backup script
    cp memory_backup_fixed.sh "$TEST_SCRIPT"
    chmod +x "$TEST_SCRIPT"

    # Modify script to use test directories
    sed -i.bak "s|REPO_URL=.*|REPO_URL=\"file://$REPO_DIR\"|" "$TEST_SCRIPT"
    sed -i.bak "s|REPO_DIR=.*|REPO_DIR=\"\$HOME/.cache/memory-backup-repo-test\"|" "$TEST_SCRIPT"

    log "Test environment setup complete"
}

# Create initial memory files for each environment
create_initial_memory() {
    local env_num=$1
    local env_dir=$2
    local entity_count=$3

    log "Creating initial memory for Environment $env_num with $entity_count entities"

    local memory_file="$env_dir/.cache/mcp-memory/memory.json"
    echo "[" > "$memory_file"

    for i in $(seq 1 $entity_count); do
        if [ $i -gt 1 ]; then
            echo "," >> "$memory_file"
        fi
        cat >> "$memory_file" <<EOF
  {
    "id": "env${env_num}_entity_${i}",
    "name": "Entity $i from Environment $env_num",
    "type": "test",
    "timestamp": "$(date -Iseconds)",
    "environment": "env${env_num}"
  }
EOF
    done

    echo "]" >> "$memory_file"

    log "Created $entity_count entities for Environment $env_num"
}

# Add new entities to simulate concurrent updates
add_new_entities() {
    local env_num=$1
    local env_dir=$2
    local new_count=$3
    local start_id=$4

    log "Adding $new_count new entities to Environment $env_num"

    local memory_file="$env_dir/.cache/mcp-memory/memory.json"
    local temp_file=$(mktemp)

    # Read existing entities (remove closing bracket)
    head -n -1 "$memory_file" > "$temp_file"

    # Add comma if there were existing entities
    echo "," >> "$temp_file"

    # Add new entities
    for i in $(seq 1 $new_count); do
        if [ $i -gt 1 ]; then
            echo "," >> "$temp_file"
        fi
        cat >> "$temp_file" <<EOF
  {
    "id": "env${env_num}_entity_$((start_id + i))_parallel",
    "name": "Parallel Entity $i from Environment $env_num",
    "type": "parallel_test",
    "timestamp": "$(date -Iseconds)",
    "environment": "env${env_num}",
    "test_run": "$$"
  }
EOF
    done

    echo "]" >> "$temp_file"

    mv "$temp_file" "$memory_file"

    log "Added $new_count new entities to Environment $env_num"
}

# Run backup script for an environment
run_backup() {
    local env_num=$1
    local env_dir=$2
    local hostname=$3

    log "Running backup for Environment $env_num (hostname: $hostname)"

    # Set environment variables
    export HOME="$env_dir"
    export MEMORY_FILE="$env_dir/.cache/mcp-memory/memory.json"
    export HOSTNAME="$hostname"

    # Run the backup script
    if bash "$TEST_SCRIPT" > "$TEST_DIR/backup_${env_num}.log" 2>&1; then
        log "✅ Backup completed for Environment $env_num"
    else
        error "❌ Backup failed for Environment $env_num"
        cat "$TEST_DIR/backup_${env_num}.log"
        return 1
    fi
}

# Verify results
verify_results() {
    log "Verifying test results..."

    cd "$REPO_DIR"

    # Check for memory files
    local env1_file="memory-test-host-1.json"
    local env2_file="memory-test-host-2.json"
    local unified_file="memory.json"

    # Count entities in each file
    if [ -f "$env1_file" ]; then
        local env1_count=$(jq -s 'length' "$env1_file" 2>/dev/null || echo "0")
        log "Environment 1 file: $env1_count entities"
    else
        error "Environment 1 file missing!"
    fi

    if [ -f "$env2_file" ]; then
        local env2_count=$(jq -s 'length' "$env2_file" 2>/dev/null || echo "0")
        log "Environment 2 file: $env2_count entities"
    else
        error "Environment 2 file missing!"
    fi

    if [ -f "$unified_file" ]; then
        # Count unique entities in unified file
        local unified_count=$(grep -c '"id":' "$unified_file" 2>/dev/null || echo "0")
        log "Unified file: $unified_count total entries"

        # Check for duplicates
        local unique_ids=$(grep -o '"id":[^,}]*' "$unified_file" | sort -u | wc -l)
        local total_ids=$(grep -o '"id":[^,}]*' "$unified_file" | wc -l)

        if [ "$unique_ids" -ne "$total_ids" ]; then
            warn "⚠️  Duplicate entities detected! Unique: $unique_ids, Total: $total_ids"
        else
            log "✅ No duplicate entities found"
        fi

        # Verify all entities from both environments are present
        local env1_parallel=$(grep -c "env1_entity.*parallel" "$unified_file" 2>/dev/null || echo "0")
        local env2_parallel=$(grep -c "env2_entity.*parallel" "$unified_file" 2>/dev/null || echo "0")

        log "Parallel entities from Env1: $env1_parallel"
        log "Parallel entities from Env2: $env2_parallel"

        if [ "$env1_parallel" -eq 0 ] || [ "$env2_parallel" -eq 0 ]; then
            error "❌ DATA LOSS DETECTED! Some parallel entities are missing!"
            return 1
        fi
    else
        error "Unified file missing!"
    fi

    # Check git history
    local commit_count=$(git log --oneline | wc -l)
    log "Total commits: $commit_count"

    # Show commit messages
    log "Commit history:"
    git log --oneline | head -5

    return 0
}

# Main test execution
main() {
    log "Starting parallel memory backup test"

    # Trap for cleanup
    trap cleanup EXIT

    # Setup
    setup_test_env

    # Create initial memory files
    create_initial_memory 1 "$ENV1_DIR" 5
    create_initial_memory 2 "$ENV2_DIR" 5

    # Test 1: Sequential backups (baseline)
    log "=== Test 1: Sequential Backups (Baseline) ==="
    run_backup 1 "$ENV1_DIR" "test-host-1"
    run_backup 2 "$ENV2_DIR" "test-host-2"

    # Add new entities
    add_new_entities 1 "$ENV1_DIR" 3 5
    add_new_entities 2 "$ENV2_DIR" 3 5

    # Test 2: Parallel backups (race condition test)
    log "=== Test 2: Parallel Backups (Race Condition Test) ==="

    # Run backups in parallel using background processes
    run_backup 1 "$ENV1_DIR" "test-host-1" &
    PID1=$!

    run_backup 2 "$ENV2_DIR" "test-host-2" &
    PID2=$!

    # Wait for both to complete
    log "Waiting for parallel backups to complete..."
    wait $PID1
    RESULT1=$?
    wait $PID2
    RESULT2=$?

    if [ $RESULT1 -ne 0 ] || [ $RESULT2 -ne 0 ]; then
        error "One or both parallel backups failed!"
    else
        log "Both parallel backups completed"
    fi

    # Test 3: Rapid successive updates (stress test)
    log "=== Test 3: Rapid Successive Updates (Stress Test) ==="

    for i in {1..5}; do
        log "Rapid update cycle $i"

        # Add entities
        add_new_entities 1 "$ENV1_DIR" 1 $((8 + i))
        add_new_entities 2 "$ENV2_DIR" 1 $((8 + i))

        # Run backups in parallel
        run_backup 1 "$ENV1_DIR" "test-host-1" &
        run_backup 2 "$ENV2_DIR" "test-host-2" &

        # Don't wait - start next cycle immediately
        sleep 0.5
    done

    # Wait for all background jobs
    wait

    # Final verification
    log "=== Final Verification ==="
    if verify_results; then
        log "✅ TEST PASSED: All entities preserved, no data loss detected"
    else
        error "❌ TEST FAILED: Data loss or corruption detected"

        # Show debug information
        log "Showing backup logs:"
        echo "=== Environment 1 Log ==="
        tail -20 "$TEST_DIR/backup_1.log"
        echo "=== Environment 2 Log ==="
        tail -20 "$TEST_DIR/backup_2.log"

        return 1
    fi

    # Performance metrics
    log "=== Performance Metrics ==="
    local total_entities=$(grep -c '"id":' "$REPO_DIR/memory.json" 2>/dev/null || echo "0")
    log "Total entities processed: $total_entities"
    log "Repository size: $(du -sh "$REPO_DIR" | cut -f1)"

    log "Test completed successfully!"
}

# Run the test
main "$@"
