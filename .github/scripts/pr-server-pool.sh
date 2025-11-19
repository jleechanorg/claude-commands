#!/bin/bash
# GCP Preview Server Pool Management Script
# Manages PR-to-server assignments using Cloud Run labels as state
set -euo pipefail

POOL_SIZE=10
SERVICE_PREFIX="mvp-site-app"
GCP_PROJECT="${GCP_PROJECT:-worldarchitecture-ai}"
GCP_REGION="${GCP_REGION:-us-central1}"

# Get all pool services with their metadata
get_pool_services() {
  local services=()

  for i in $(seq 1 $POOL_SIZE); do
    local server="s${i}"
    local service_name="${SERVICE_PREFIX}-${server}"

    # Query service metadata from Cloud Run
    local service_data=$(gcloud run services describe "$service_name" \
      --project="$GCP_PROJECT" \
      --region="$GCP_REGION" \
      --format="json" 2>/dev/null || echo "{}")

    if [[ "$service_data" != "{}" ]]; then
      # Service exists - extract metadata
      local pr_number=$(echo "$service_data" | jq -r '.metadata.labels["pr-number"] // "null"')
      local last_update=$(echo "$service_data" | jq -r '(
        .status.conditions[]? | select(.type == "Ready") | .lastTransitionTime
      ) // .metadata.creationTimestamp // "null"')

      services+=("$server|$service_name|$pr_number|$last_update")
    else
      # Service doesn't exist yet - available
      services+=("$server|$service_name|null|null")
    fi
  done

  printf '%s\n' "${services[@]}"
}

# Reserve server by setting label immediately (prevents race conditions)
reserve_server() {
  local service_name="$1"
  local pr_number="$2"

  # Try to update label and verify it stuck (prevents concurrent assignment)
  local max_retries=3
  local retry=0

  while [ $retry -lt $max_retries ]; do
    # Attempt to set the label
    if gcloud run services update "$service_name" \
      --project="$GCP_PROJECT" \
      --region="$GCP_REGION" \
      --update-labels="pr-number=$pr_number" \
      --quiet 2>/dev/null; then

      # Wait briefly for label update to propagate
      sleep 1

      # Verify the label wasn't overwritten by a concurrent workflow
      local current_pr=$(gcloud run services describe "$service_name" \
        --project="$GCP_PROJECT" \
        --region="$GCP_REGION" \
        --format="value(metadata.labels.pr-number)" 2>/dev/null || echo "")

      if [[ "$current_pr" == "$pr_number" ]]; then
        # Success: our label is still there
        return 0
      else
        # Race condition: another workflow overwrote our label
        # Return failure so caller tries next available server
        return 1
      fi
    fi

    retry=$((retry + 1))
    if [ $retry -lt $max_retries ]; then
      sleep 1
    fi
  done

  return 1
}

# Assign server to PR
assign_server() {
  local pr_number="$1"

  # Validate PR number parameter
  [[ -z "$pr_number" ]] && {
    echo '{"error":"PR number required"}' >&2
    exit 1
  }

  local services=$(get_pool_services)

  # Check if PR already has assignment
  while IFS='|' read -r server service_name pr last_update; do
    if [[ "$pr" == "$pr_number" ]]; then
      echo "{\"server\":\"$server\",\"serviceName\":\"$service_name\",\"evicted\":null}"
      return 0
    fi
  done <<< "$services"

  # Round-robin assignment: Find next available server in sequence (s1→s2→...→s10→s1)
  # Find the most recently assigned server (newest timestamp) to determine where to continue
  local last_assigned_num=0
  local newest_time=""

  while IFS='|' read -r server service_name pr last_update; do
    if [[ "$pr" != "null" && "$last_update" != "null" ]]; then
      # Extract server number (s1 → 1, s2 → 2, etc.)
      local server_num="${server#s}"

      if [[ -z "$newest_time" ]] || [[ "$last_update" > "$newest_time" ]]; then
        newest_time="$last_update"
        last_assigned_num="$server_num"
      fi
    fi
  done <<< "$services"

  # Try to assign starting from next server in sequence
  for offset in $(seq 1 $POOL_SIZE); do
    local next_num=$(( (last_assigned_num + offset - 1) % POOL_SIZE + 1 ))
    local next_server="s${next_num}"
    local next_service="${SERVICE_PREFIX}-${next_server}"

    # Check if this server is available
    while IFS='|' read -r server service_name pr last_update; do
      if [[ "$server" == "$next_server" && "$pr" == "null" ]]; then
        # Found available server in round-robin sequence - reserve immediately
        if reserve_server "$service_name" "$pr_number"; then
          echo "{\"server\":\"$server\",\"serviceName\":\"$service_name\",\"evicted\":null}"
          return 0
        fi
        break
      fi
    done <<< "$services"
  done

  # Pool is full - evict server with oldest timestamp
  local oldest_server=""
  local oldest_service=""
  local oldest_pr=""
  local oldest_time="9999-99-99T99:99:99Z"
  local found_null_timestamp=false

  while IFS='|' read -r server service_name pr last_update; do
    # Handle both null and valid timestamps - prefer null timestamps for eviction
    if [[ "$pr" != "null" ]]; then
      if [[ "$last_update" == "null" ]]; then
        # Null timestamp means never deployed - highest priority for eviction
        # Once we find a null timestamp server, we stick with it (don't replace with valid timestamps)
        if [[ "$found_null_timestamp" == "false" ]]; then
          oldest_server="$server"
          oldest_service="$service_name"
          oldest_pr="$pr"
          found_null_timestamp=true
        fi
      elif [[ "$found_null_timestamp" == "false" ]] && [[ "$last_update" < "$oldest_time" ]]; then
        # Valid timestamp - only consider if we haven't found a null timestamp server yet
        # NOTE: String comparison assumes ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
        # This works for lexicographic comparison but would break with timezone variations
        oldest_time="$last_update"
        oldest_server="$server"
        oldest_service="$service_name"
        oldest_pr="$pr"
      fi
    fi
  done <<< "$services"

  # Ensure we found something to evict
  if [[ -z "$oldest_server" ]]; then
    # Output to stdout for consistent JSON parsing
    echo "{\"server\":null,\"serviceName\":null,\"evicted\":null}"
    exit 1
  fi

  # Reserve the evicted server for the new PR
  if reserve_server "$oldest_service" "$pr_number"; then
    echo "{\"server\":\"$oldest_server\",\"serviceName\":\"$oldest_service\",\"evicted\":$oldest_pr}"
  else
    echo "{\"server\":null,\"serviceName\":null,\"evicted\":null}"
    exit 1
  fi
}

# Release server from PR
release_server() {
  local pr_number="$1"

  # Validate PR number parameter
  [[ -z "$pr_number" ]] && {
    echo '{"error":"PR number required"}' >&2
    exit 1
  }

  local services=$(get_pool_services)

  while IFS='|' read -r server service_name pr last_update; do
    if [[ "$pr" == "$pr_number" ]]; then
      echo "{\"server\":\"$server\",\"serviceName\":\"$service_name\"}"
      return 0
    fi
  done <<< "$services"

  echo "{\"server\":null,\"serviceName\":null}"
}

# Show pool status
show_status() {
  echo ""
  echo "📊 PR Server Pool Status"
  echo ""
  printf "%-8s | %-30s | %-6s | %s\n" "Server" "Service Name" "PR" "Last Update"
  echo "---------|--------------------------------|--------|-------------------------"

  local services=$(get_pool_services)
  local total=0
  local used=0

  while IFS='|' read -r server service_name pr last_update; do
    total=$((total + 1))

    if [[ "$pr" != "null" ]]; then
      used=$((used + 1))
      # Format timestamp to relative time
      # NOTE: The following uses GNU date (-d), which is only available on Linux.
      # On macOS/BSD, this will fail. This script is intended for Ubuntu (GitHub Actions).
      local time_str
      if [[ "$last_update" != "null" ]]; then
        time_str=$(date -d "$last_update" "+%Y-%m-%d %H:%M" 2>/dev/null || echo "$last_update")
      else
        time_str="unknown"
      fi
      printf "%-8s | %-30s | #%-4s | %s\n" "$server" "$service_name" "$pr" "$time_str"
    else
      printf "%-8s | %-30s | %-6s | %s\n" "$server" "$service_name" "-" "(available)"
    fi
  done <<< "$services"

  local available=$((total - used))
  echo ""
  echo "========================================================================="
  echo "Total: $total | Used: $used | Available: $available"
  echo ""
}

# Main CLI
case "${1:-}" in
  assign) assign_server "$2" ;;
  release) release_server "$2" ;;
  status) show_status ;;
  *) echo "Usage: $0 {assign|release|status} [PR_NUMBER]" >&2; exit 1 ;;
esac
