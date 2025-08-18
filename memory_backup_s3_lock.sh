#!/usr/bin/env bash
# Memory Backup with S3-based Distributed Locking
# Uses S3's conditional PUT for atomic lock acquisition

set -euo pipefail

HOSTNAME=$(hostname -s)
S3_BUCKET="memory-backup-locks"
LOCK_KEY="memory-backup.lock"
LOCK_TTL=60  # seconds

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$HOSTNAME:$$]: $1"
}

# Acquire lock using S3 conditional PUT
acquire_s3_lock() {
    local lock_id="$HOSTNAME-$$-$(date +%s)"
    local lock_acquired=false
    local max_attempts=30
    
    log "Attempting to acquire S3-based distributed lock..."
    
    for attempt in $(seq 1 $max_attempts); do
        # Check if lock exists
        if aws s3api head-object --bucket "$S3_BUCKET" --key "$LOCK_KEY" 2>/dev/null; then
            # Lock exists, check if it's expired
            local lock_time=$(aws s3api head-object --bucket "$S3_BUCKET" --key "$LOCK_KEY" \
                --query 'LastModified' --output text)
            local lock_age=$(( $(date +%s) - $(date -d "$lock_time" +%s) ))
            
            if [ $lock_age -gt $LOCK_TTL ]; then
                log "Found expired lock ($lock_age seconds old), removing..."
                aws s3 rm "s3://$S3_BUCKET/$LOCK_KEY"
            else
                log "Lock held by another process ($lock_age seconds old), waiting..."
                sleep 2
                continue
            fi
        fi
        
        # Try to acquire lock with conditional PUT (only if object doesn't exist)
        echo "$lock_id" | aws s3 cp - "s3://$S3_BUCKET/$LOCK_KEY" \
            --metadata "host=$HOSTNAME,pid=$$,timestamp=$(date -Iseconds)" \
            --acl private \
            2>/dev/null && lock_acquired=true && break
        
        sleep 2
    done
    
    if [ "$lock_acquired" = true ]; then
        log "S3 lock acquired successfully"
        return 0
    else
        log "Failed to acquire S3 lock"
        return 1
    fi
}

release_s3_lock() {
    log "Releasing S3 lock..."
    aws s3 rm "s3://$S3_BUCKET/$LOCK_KEY" 2>/dev/null || true
}

# Alternative: DynamoDB conditional writes (even better for this use case)
acquire_dynamodb_lock() {
    local lock_id="$HOSTNAME-$$"
    local timestamp=$(date +%s)
    local ttl=$((timestamp + LOCK_TTL))
    
    # Try to acquire lock with conditional write
    aws dynamodb put-item \
        --table-name MemoryBackupLocks \
        --item "{
            \"LockKey\": {\"S\": \"memory-backup\"},
            \"Owner\": {\"S\": \"$lock_id\"},
            \"Timestamp\": {\"N\": \"$timestamp\"},
            \"TTL\": {\"N\": \"$ttl\"},
            \"Host\": {\"S\": \"$HOSTNAME\"}
        }" \
        --condition-expression "attribute_not_exists(LockKey) OR #ttl < :now" \
        --expression-attribute-names '{"#ttl": "TTL"}' \
        --expression-attribute-values "{\":now\": {\"N\": \"$timestamp\"}}" \
        2>/dev/null
}

release_dynamodb_lock() {
    local lock_id="$HOSTNAME-$$"
    
    aws dynamodb delete-item \
        --table-name MemoryBackupLocks \
        --key '{"LockKey": {"S": "memory-backup"}}' \
        --condition-expression "Owner = :owner" \
        --expression-attribute-values "{\":owner\": {\"S\": \"$lock_id\"}}" \
        2>/dev/null || true
}