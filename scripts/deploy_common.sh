#!/bin/bash
# Shared helper functions for deployment scripts.
set -euo pipefail

deploy_common::get_project_id() {
  gcloud config get-value project
}

deploy_common::submit_build() {
  local context_dir=$1
  local image_tag=$2
  local image_tag_latest=${3:-}  # Optional second tag (e.g., latest)

  # Use --async to avoid "This tool can only stream logs if you are Viewer/Owner" error
  # when service account lacks Viewer/Owner role. We poll for completion instead.
  echo "Starting build asynchronously..."

  # Build with primary tag first
  local build_id
  build_id=$(cd "$context_dir" && gcloud builds submit . --tag "$image_tag" --async --format="value(id)")

  # Get project ID for logs URL
  local project_id
  project_id=$(deploy_common::get_project_id)

  echo "Build ID: $build_id"
  echo "Polling for build completion..."

  # Poll build status every 5 seconds
  local status=""
  while [[ "$status" != "SUCCESS" && "$status" != "FAILURE" && "$status" != "TIMEOUT" && "$status" != "CANCELLED" ]]; do
    sleep 5
    status=$(gcloud builds describe "$build_id" --format="value(status)" 2>/dev/null || echo "PENDING")
    echo "Build status: $status"
  done

  if [[ "$status" != "SUCCESS" ]]; then
    echo "Build failed with status: $status"
    echo "View logs at: https://console.cloud.google.com/cloud-build/builds/$build_id?project=$project_id"
    return 1
  fi

  echo "Build completed successfully!"

  # Add additional tag if provided
  # Note: gcloud builds submit with multiple --tag flags only creates the last tag
  # We must add additional tags AFTER the build completes
  if [[ -n "$image_tag_latest" ]]; then
    echo "Adding additional tag: $image_tag_latest"
    gcloud container images add-tag "$image_tag" "$image_tag_latest" --quiet
    echo "Additional tag added successfully!"
  fi
}

deploy_common::deploy_service() {
  local service_name=$1
  local image_tag=$2
  local secrets=$3
  local memory=$4
  local timeout=$5
  local min_instances=$6
  local max_instances=$7
  local concurrency=$8
  local region=${9:-}
  local port=${10:-}
  local extra_args=()
  if (($# >= 11)); then
    extra_args=("${@:11}")
  fi

  local args=("--image" "$image_tag" "--platform" "managed" "--allow-unauthenticated" \
    "--memory=$memory" "--timeout=$timeout" "--min-instances=$min_instances" \
    "--max-instances=$max_instances" "--concurrency=$concurrency")

  if [[ -n $secrets ]]; then
    args+=("--set-secrets=$secrets")
  fi
  if [[ -n $region ]]; then
    args+=("--region" "$region")
  fi
  if [[ -n $port ]]; then
    args+=("--port=$port")
  fi
  if ((${#extra_args[@]} > 0)); then
    args+=("${extra_args[@]}")
  fi

  gcloud run deploy "$service_name" "${args[@]}"
}

deploy_common::update_service_timeout() {
  local service_name=$1
  local timeout=$2
  local region=${3:-}

  local args=("--platform" "managed" "--timeout=$timeout")
  if [[ -n $region ]]; then
    args+=("--region" "$region")
  fi

  gcloud run services update "$service_name" "${args[@]}"
}

deploy_common::service_url() {
  local service_name=$1
  local region=${2:-}

  local args=("--platform" "managed" "--format" "value(status.url)")
  if [[ -n $region ]]; then
    args+=("--region" "$region")
  fi

  gcloud run services describe "$service_name" "${args[@]}"
}
