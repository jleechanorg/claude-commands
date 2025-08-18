#!/usr/bin/env bash
# Memory Backup with Redis Distributed Locking (Redlock algorithm)
# Most robust solution for production use

set -euo pipefail

HOSTNAME=$(hostname -s)
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
LOCK_KEY="memory:backup:lock"
LOCK_TTL=60  # seconds
LOCK_VALUE="$HOSTNAME-$$-$(date +%s)"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$HOSTNAME:$$]: $1"
}

# Acquire Redis lock with Redlock algorithm
acquire_redis_lock() {
    local max_attempts=30
    
    log "Attempting to acquire Redis distributed lock..."
    
    for attempt in $(seq 1 $max_attempts); do
        # Try to set lock with NX (only if not exists) and EX (expiry)
        if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" \
            SET "$LOCK_KEY" "$LOCK_VALUE" NX EX "$LOCK_TTL" | grep -q "OK"; then
            log "Redis lock acquired successfully"
            return 0
        fi
        
        # Check who has the lock and how old it is
        local current_lock=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" GET "$LOCK_KEY")
        local ttl=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" TTL "$LOCK_KEY")
        
        if [ "$ttl" = "-1" ] || [ "$ttl" = "-2" ]; then
            # No TTL or key doesn't exist, try to clean up
            log "Found lock without TTL, attempting cleanup..."
            redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" DEL "$LOCK_KEY" >/dev/null
        else
            log "Lock held by: $current_lock (TTL: ${ttl}s), waiting..."
        fi
        
        sleep 2
    done
    
    log "Failed to acquire Redis lock after $max_attempts attempts"
    return 1
}

# Release Redis lock (only if we own it)
release_redis_lock() {
    log "Releasing Redis lock..."
    
    # Lua script for atomic check-and-delete
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" EVAL "
        if redis.call('GET', KEYS[1]) == ARGV[1] then
            return redis.call('DEL', KEYS[1])
        else
            return 0
        end
    " 1 "$LOCK_KEY" "$LOCK_VALUE" >/dev/null
}

# Extend lock if operation takes longer
extend_redis_lock() {
    # Lua script for atomic check-and-extend
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" EVAL "
        if redis.call('GET', KEYS[1]) == ARGV[1] then
            return redis.call('EXPIRE', KEYS[1], ARGV[2])
        else
            return 0
        end
    " 1 "$LOCK_KEY" "$LOCK_VALUE" "$LOCK_TTL" >/dev/null
}

# Alternative: Using etcd for distributed locking
acquire_etcd_lock() {
    local lease_id=$(etcdctl lease grant "$LOCK_TTL" | grep "lease" | cut -d' ' -f2)
    
    if etcdctl put "$LOCK_KEY" "$LOCK_VALUE" --lease="$lease_id" 2>/dev/null; then
        log "Etcd lock acquired with lease $lease_id"
        echo "$lease_id" > /tmp/etcd_lease_id
        return 0
    fi
    
    return 1
}

release_etcd_lock() {
    if [ -f /tmp/etcd_lease_id ]; then
        local lease_id=$(cat /tmp/etcd_lease_id)
        etcdctl lease revoke "$lease_id" 2>/dev/null || true
        rm -f /tmp/etcd_lease_id
    fi
}