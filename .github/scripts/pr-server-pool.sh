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

  # First, get list of existing services in one batch (much faster)
  local existing_services=$(gcloud run services list \
    --project="$GCP_PROJECT" \
    --region="$GCP_REGION" \
    --filter="metadata.name:${SERVICE_PREFIX}-s" \
    --format="json" 2>/dev/null || echo "[]")

  # Create associative array of existing services for fast lookup
  declare -A service_metadata
  while IFS= read -r line; do
    if [[ -n "$line" && "$line" != "[]" ]]; then
      local name=$(echo "$line" | jq -r '.metadata.name')
      local pr=$(echo "$line" | jq -r '.metadata.labels["pr-number"] // "null"')
      local last_update=$(echo "$line" | jq -r '(
        .status.conditions[]? | select(.type == "Ready") | .lastTransitionTime
      ) // .metadata.creationTimestamp // "null"')
      service_metadata["$name"]="$pr|$last_update"
    fi
  done < <(echo "$existing_services" | jq -c '.[]' 2>/dev/null)

  # Now iterate through pool and use cached data
  for i in $(seq 1 $POOL_SIZE); do
    local server="s${i}"
    local service_name="${SERVICE_PREFIX}-${server}"

    if [[ -n "${service_metadata[$service_name]:-}" ]]; then
      # Service exists - use cached metadata
      local pr_number=$(echo "${service_metadata[$service_name]}" | cut -d'|' -f1)
      local last_update=$(echo "${service_metadata[$service_name]}" | cut -d'|' -f2)
      services+=("$server|$service_name|$pr_number|$last_update")
    else
      # Service doesn't exist yet - available
      services+=("$server|$service_name|null|null")
    fi
  done

  printf '%s\n' "${services[@]}"
}

# Reserve server by setting label immediately (prevents race conditions)
# NOTE: This requires services to be pre-created. Run this once:
#   for i in {1..10}; do
#     gcloud run deploy "mvp-site-app-s${i}" \
#       --image=gcr.io/cloudrun/hello \
#       --region=us-central1 \
#       --allow-unauthenticated \
#       --quiet
#   done
reserve_server() {
  local service_name="$1"
  local pr_number="$2"

  # Check if service exists first
  local service_exists=$(gcloud run services describe "$service_name" \
    --project="$GCP_PROJECT" \
    --region="$GCP_REGION" \
    --format="value(metadata.name)" 2>/dev/null || echo "")

  if [[ -z "$service_exists" ]]; then
    # Service doesn't exist - create placeholder to enable label-based locking
    echo "⚠️  Service $service_name doesn't exist, creating placeholder..." >&2
    if ! gcloud run deploy "$service_name" \
      --image=gcr.io/cloudrun/hello \
      --project="$GCP_PROJECT" \
      --region="$GCP_REGION" \
      --platform=managed \
      --allow-unauthenticated \
      --memory=256Mi \
      --cpu=1 \
      --max-instances=1 \
      --min-instances=0 \
      --timeout=60 \
      --quiet 2>/dev/null; then
      echo "❌ Failed to create placeholder service $service_name" >&2
      return 1
    fi
    echo "✅ Created placeholder service $service_name" >&2
  fi

  # Try to update label and verify it stuck (prevents concurrent assignment)
  local max_retries=3
  local retry=0

  while [ $retry -lt $max_retries ]; do
    # Attempt to set the label (with timeout)
    if timeout 30 gcloud run services update "$service_name" \
      --project="$GCP_PROJECT" \
      --region="$GCP_REGION" \
      --update-labels="pr-number=$pr_number" \
      --quiet 2>/dev/null; then

      # Wait briefly for label update to propagate
      sleep 1

      # Verify the label wasn't overwritten by a concurrent workflow (with timeout)
      local current_pr=$(timeout 15 gcloud run services describe "$service_name" \
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

  # Find first available server (null PR)
  while IFS='|' read -r server service_name pr last_update; do
    if [[ "$pr" == "null" ]]; then
      # Found available server - reserve immediately to prevent race conditions
      if reserve_server "$service_name" "$pr_number"; then
        echo "{\"server\":\"$server\",\"serviceName\":\"$service_name\",\"evicted\":null}"
        return 0
      fi
    fi
  done <<< "$services"

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
