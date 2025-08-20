#!/usr/bin/env python3
"""
Memory MCP CRDT Merge Logic for Multi-Machine Synchronization
Handles both JSONL format (backup repo) and array format (MCP cache)
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, List

def load_memory_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load memory from JSONL file (backup repo format)"""
    memories = []
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        memories.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    return memories

def load_memory_array(file_path: str) -> List[Dict[str, Any]]:
    """Load memory from JSON array file (MCP cache format)"""
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                return []
    except json.JSONDecodeError:
        return []

def save_memory_jsonl(memories: List[Dict[str, Any]], file_path: str) -> None:
    """Save memory to JSONL file (backup repo format)"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        for memory in memories:
            f.write(json.dumps(memory, separators=(',', ':')) + '\n')

def save_memory_array(memories: List[Dict[str, Any]], file_path: str) -> None:
    """Save memory to JSON array file (MCP cache format)"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(memories, f, indent=2)

def get_memory_timestamp(memory: Dict[str, Any]) -> str:
    """Extract timestamp from memory entry for CRDT comparison"""
    # Check various timestamp fields
    for field in ['timestamp', 'last_updated', 'created_at', '_crdt_metadata.timestamp']:
        if '.' in field:
            # Handle nested fields like _crdt_metadata.timestamp
            parts = field.split('.')
            value = memory
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    value = None
                    break
            if value:
                return str(value)
        elif field in memory:
            return str(memory[field])
    
    # Default timestamp if none found
    return "1970-01-01T00:00:00Z"

def merge_memory_entries(local_memories: List[Dict[str, Any]], remote_memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge two memory lists using CRDT Last-Write-Wins strategy"""
    # Create lookup by memory ID/name
    merged = {}
    fallback_counter = 0
    
    # Process local memories first
    for memory in local_memories:
        memory_id = memory.get('id') or memory.get('name')
        if not memory_id:
            memory_id = f"memory_{fallback_counter}"
            fallback_counter += 1
        merged[memory_id] = memory
    
    # Merge remote memories using LWW
    for remote_memory in remote_memories:
        memory_id = remote_memory.get('id') or remote_memory.get('name')
        if not memory_id:
            memory_id = f"memory_{fallback_counter}"
            fallback_counter += 1
        
        if memory_id in merged:
            local_memory = merged[memory_id]
            local_timestamp = get_memory_timestamp(local_memory)
            remote_timestamp = get_memory_timestamp(remote_memory)
            
            # Last-Write-Wins: keep the memory with later timestamp
            if remote_timestamp > local_timestamp:
                merged[memory_id] = remote_memory
                print(f"Updated memory '{memory_id}' (remote newer: {remote_timestamp} > {local_timestamp})")
            else:
                print(f"Kept local memory '{memory_id}' (local newer: {local_timestamp} >= {remote_timestamp})")
        else:
            merged[memory_id] = remote_memory
            print(f"Added new memory '{memory_id}' from remote")
    
    return list(merged.values())

def sync_memory() -> None:
    """Synchronize memory between cache and repo with CRDT merge"""
    cache_path = os.path.expanduser("~/.cache/mcp-memory/memory.json")
    repo_path = os.path.expanduser("~/projects/worldarchitect-memory-backups/memory.json")
    
    print("Starting memory synchronization...")
    
    # Load both memory files in their respective formats
    cache_memories = load_memory_array(cache_path)
    repo_memories = load_memory_jsonl(repo_path)
    
    print(f"Loaded {len(cache_memories)} memories from cache")
    print(f"Loaded {len(repo_memories)} memories from repo")
    
    # Merge memories using CRDT
    merged_memories = merge_memory_entries(cache_memories, repo_memories)
    
    print(f"Merged result: {len(merged_memories)} total memories")
    
    # Save to both locations in their respective formats
    save_memory_array(merged_memories, cache_path)
    save_memory_jsonl(merged_memories, repo_path)
    
    print("Memory synchronization complete")
    print(f"Cache updated: {cache_path}")
    print(f"Repo updated: {repo_path}")

if __name__ == "__main__":
    sync_memory()