#!/usr/bin/env python3
"""
Process queued Memory MCP entities
This script is meant to be called from within Claude to save queued entities
"""

import json
from pathlib import Path

def process_mcp_queue():
    """Process and save queued Memory MCP entities"""
    mcp_queue_file = Path.home() / ".cache" / "claude-learning" / "mcp_queue.json"
    
    if not mcp_queue_file.exists():
        print("No queued entities found.")
        return 0
    
    try:
        with open(mcp_queue_file, 'r') as f:
            queue = json.load(f)
        
        if not queue:
            print("Queue is empty.")
            return 0
            
        print(f"Processing {len(queue)} queued entities...")
        
        # This is where Claude would actually call Memory MCP
        for item in queue:
            print(f"Would save to Memory MCP: {json.dumps(item, indent=2)}")
            # In Claude context:
            # mcp__memory-server__create_entities(item)
        
        # Clear the queue after processing
        with open(mcp_queue_file, 'w') as f:
            json.dump([], f)
            
        print(f"✅ Processed {len(queue)} entities")
        return len(queue)
        
    except Exception as e:
        print(f"Error processing queue: {e}")
        return -1

if __name__ == "__main__":
    process_mcp_queue()