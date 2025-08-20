#!/usr/bin/env bash
# Focused test to demonstrate the race condition in unified file creation
# This test will prove data loss can occur during parallel execution

set -euo pipefail

# Test setup
TEST_DIR="/tmp/race-condition-test-$$"
ITERATIONS=10
PARALLEL_PROCESSES=4

echo "🔬 Race Condition Demonstration Test"
echo "====================================="
echo "This test will attempt to trigger the race condition in create_unified_memory()"
echo ""

# Create test directory
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Create a mock version of create_unified_memory that simulates the race
cat > race_simulator.sh << 'EOF'
#!/bin/bash
# Simulates the create_unified_memory function with artificial delays

PROCESS_ID=$1
OUTPUT_DIR=$2

# Read phase (simulating reading memory-*.json files)
echo "[$PROCESS_ID] Reading files..." >> "$OUTPUT_DIR/trace.log"
sleep 0.1  # Simulate file reading time

# Get current state
CURRENT_COUNT=$(cat "$OUTPUT_DIR/counter.txt" 2>/dev/null || echo "0")
echo "[$PROCESS_ID] Read count: $CURRENT_COUNT" >> "$OUTPUT_DIR/trace.log"

# Processing phase (simulating jq operations)
echo "[$PROCESS_ID] Processing..." >> "$OUTPUT_DIR/trace.log"
sleep 0.2  # Simulate processing time

# Increment counter (simulating adding new entities)
NEW_COUNT=$((CURRENT_COUNT + 1))

# Write phase (simulating mv "$temp_unified" "memory.json")
echo "[$PROCESS_ID] Writing count: $NEW_COUNT" >> "$OUTPUT_DIR/trace.log"
echo "$NEW_COUNT" > "$OUTPUT_DIR/counter.txt"

# Log completion
echo "[$PROCESS_ID] Complete at $(date +%s.%N)" >> "$OUTPUT_DIR/trace.log"
EOF

chmod +x race_simulator.sh

# Initialize counter
echo "0" > counter.txt
> trace.log

echo "🚀 Starting parallel execution with $PARALLEL_PROCESSES processes..."
echo ""

# Run multiple processes in parallel
for i in $(seq 1 $PARALLEL_PROCESSES); do
    ./race_simulator.sh "P$i" "$TEST_DIR" &
done

# Wait for all to complete
wait

echo "📊 Results:"
echo "---------"
FINAL_COUNT=$(cat counter.txt)
echo "Expected final count: $PARALLEL_PROCESSES"
echo "Actual final count: $FINAL_COUNT"
echo ""

if [ "$FINAL_COUNT" -ne "$PARALLEL_PROCESSES" ]; then
    echo "❌ RACE CONDITION CONFIRMED!"
    echo "   Lost updates: $((PARALLEL_PROCESSES - FINAL_COUNT))"
    echo ""
    echo "📝 Execution trace:"
    cat trace.log | sort
else
    echo "✅ No race condition detected (lucky timing)"
fi

echo ""
echo "🔍 Analysis:"
echo "----------"
echo "The race condition occurs because multiple processes:"
echo "1. Read the same initial state"
echo "2. Process independently"
echo "3. Write their results, overwriting each other"
echo ""
echo "Without proper locking, the last writer wins, losing all other updates."

# Cleanup
cd /
rm -rf "$TEST_DIR"