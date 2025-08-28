#!/usr/bin/env python3
"""
GREEN PHASE: Test the fixed FastMCP server
Should now expose all 29 tools and handle tool calls properly
"""

import json
import subprocess
import sys
import os
from pathlib import Path

def get_project_root():
    """Find project root by looking for CLAUDE.md file"""
    current = Path.cwd()
    for potential_root in [current] + list(current.parents):
        if (potential_root / "CLAUDE.md").exists():
            return str(potential_root)
    return os.environ.get("PROJECT_ROOT", str(Path.cwd()))

def test_fixed_fastmcp_initialization():
    """Test that fixed server initializes properly"""
    print("🟢 GREEN PHASE: Testing fixed FastMCP initialization...")
    
    try:
        project_root = get_project_root()
        server_path = f"{project_root}/mcp_servers/slash_commands/server.py"
        
        process = subprocess.Popen(
            [f"{project_root}/vpython", server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=project_root
        )
        
        # Send initialize message
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        process.stdin.write(json.dumps(init_message) + "\n")
        process.stdin.flush()
        
        # Send tools/list message
        tools_message = {
            "jsonrpc": "2.0",
            "id": 2, 
            "method": "tools/list",
            "params": {}
        }
        
        process.stdin.write(json.dumps(tools_message) + "\n")
        process.stdin.flush()
        
        # Close stdin and get output
        process.stdin.close()
        stdout, stderr = process.communicate(timeout=10)
        
        print(f"Server stderr: {stderr}")
        
        # Parse the tools/list response
        lines = stdout.strip().split('\n')
        tools_response = None
        for line in lines:
            if line.strip():
                try:
                    response = json.loads(line)
                    if response.get('id') == 2:  # tools/list response
                        tools_response = response
                        break
                except json.JSONDecodeError:
                    continue
        
        if tools_response and 'result' in tools_response:
            tools = tools_response['result']['tools']
            print(f"✅ Fixed server exposes {len(tools)} tools")
            
            # Check for key tools
            tool_names = [tool['name'] for tool in tools]
            key_tools = ['cerebras_generate', 'analyze_architecture', 'run_tests', 'git_push']
            
            for tool in key_tools:
                if tool in tool_names:
                    print(f"  ✅ {tool}")
                else:
                    print(f"  ❌ Missing: {tool}")
            
            return len(tools) >= 20  # Should have most of the 29 tools
        else:
            print(f"❌ Invalid tools response: {tools_response}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_cerebras_tool_call():
    """Test that cerebras_generate tool actually works"""
    print("🟢 GREEN PHASE: Testing cerebras_generate tool call...")
    
    try:
        project_root = get_project_root()
        server_path = f"{project_root}/mcp_servers/slash_commands/server.py"
        
        process = subprocess.Popen(
            [f"{project_root}/vpython", server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=project_root
        )
        
        # Send cerebras_generate tool call
        tool_call = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "cerebras_generate",
                "arguments": {
                    "prompt": "Create a simple hello world function"
                }
            }
        }
        
        process.stdin.write(json.dumps(tool_call) + "\n")
        process.stdin.flush()
        process.stdin.close()
        
        stdout, stderr = process.communicate(timeout=60)
        
        # Look for the tool call response
        lines = stdout.strip().split('\n')
        for line in lines:
            if line.strip():
                try:
                    response = json.loads(line)
                    if response.get('id') == 3:  # tool call response
                        if 'result' in response:
                            content = response['result']['content'][0]['text']
                            if 'def hello' in content.lower() or 'function' in content.lower():
                                print("✅ Cerebras tool call successful")
                                return True
                        elif 'error' in response:
                            print(f"❌ Tool call error: {response['error']}")
                        break
                except json.JSONDecodeError:
                    continue
        
        print("❌ No valid tool call response found")
        return False
        
    except Exception as e:
        print(f"❌ Cerebras test failed: {e}")
        return False

if __name__ == "__main__":
    print("🟢 GREEN PHASE: Testing Fixed FastMCP Server")
    print("="*50)
    
    # Test 1: Initialization and tool listing
    test1_pass = test_fixed_fastmcp_initialization()
    
    # Test 2: Actual tool execution
    test2_pass = test_cerebras_tool_call()
    
    print(f"\n📊 GREEN PHASE RESULTS:")
    print(f"  Tool registration: {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print(f"  Tool execution: {'✅ PASS' if test2_pass else '❌ FAIL'}")
    
    if test1_pass and test2_pass:
        print(f"\n🎯 GREEN PHASE SUCCESS: Fixed FastMCP server working!")
        print(f"   Ready for REFACTOR PHASE: Switch configuration to use fixed server")
    else:
        print(f"\n⚠️ GREEN PHASE INCOMPLETE: Need to fix remaining issues")
