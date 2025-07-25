#!/usr/bin/env python3
"""Monitor Redis activity in real-time"""

import redis
import time
import json
import datetime

def monitor_redis():
    """Monitor Redis for real-time activity"""
    r = redis.Redis(decode_responses=True)

    print("=== Redis Live Monitor ===")
    print("Monitoring for messages...\n")

    # Track what we've seen
    seen_messages = set()

    while True:
        try:
            # Check all queues
            for key in r.scan_iter("queue:*"):
                messages = r.lrange(key, 0, -1)
                for msg in messages:
                    msg_hash = hash(msg)
                    if msg_hash not in seen_messages:
                        seen_messages.add(msg_hash)
                        try:
                            data = json.loads(msg)
                            print(f"\n[{time.strftime('%H:%M:%S')}] New message in {key}:")
                            print(f"  Type: {data.get('type')}")
                            print(f"  From: {data.get('from_agent')} -> To: {data.get('to_agent')}")
                            print(f"  ID: {data.get('id')}")
                            if 'task_id' in data.get('payload', {}):
                                print(f"  Task ID: {data['payload']['task_id']}")
                        except json.JSONDecodeError:
                            print(f"  Raw: {msg[:100]}...")

            # Also check for agent heartbeats
            for key in r.scan_iter("agent:*"):
                agent_info = r.hgetall(key)
                if agent_info.get('last_heartbeat'):
                    # Only show if updated in last 2 seconds
                    hb_time = datetime.datetime.fromisoformat(agent_info['last_heartbeat'])
                    if (datetime.datetime.now() - hb_time).seconds < 2:
                        print(f"[{time.strftime('%H:%M:%S')}] Heartbeat from {key}")

            time.sleep(0.5)

        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    monitor_redis()
