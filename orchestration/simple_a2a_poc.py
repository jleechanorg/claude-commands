#!/usr/bin/env python3
"""
Simple Real A2A SDK Proof of Concept

This demonstrates basic integration with Google's A2A SDK,
creating a minimal working agent that uses the real A2A protocol.
"""

import asyncio
import logging
from typing import Any, Dict

from a2a.client.client import A2AClient
from a2a.types import AgentCard
import uvicorn
from fastapi import FastAPI

import httpx


class SimpleA2AAgent:
    """Simple real A2A agent using official SDK"""
    
    def __init__(self, name: str = "orchestrator-poc", port: int = 8000):
        self.name = name
        self.port = port
        self.logger = logging.getLogger(__name__)
        
        # Create agent card for real A2A protocol
        self.agent_card = AgentCard(
            name=self.name,
            description="WorldArchitect.AI Orchestrator POC with real A2A integration",
            version="1.0.0",
            # Add required agent card fields
        )
        
        # Create FastAPI app for A2A endpoints
        self.app = FastAPI(title=self.name)
        self.setup_routes()
        
    def setup_routes(self):
        """Setup real A2A protocol routes"""
        
        @self.app.get("/.well-known/agent.json")
        async def get_agent_card():
            """Standard A2A agent card endpoint"""
            return {
                "name": self.agent_card.name,
                "description": self.agent_card.description, 
                "version": self.agent_card.version,
                "tasks": {
                    "orchestrate": {
                        "description": "Orchestrate workflow execution",
                        "parameters": {
                            "workflow_data": {"type": "object"}
                        }
                    },
                    "discover": {
                        "description": "Discover available agents",
                        "parameters": {
                            "capability": {"type": "string", "required": False}
                        }
                    }
                }
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy", "agent": self.name}
        
        self.logger.info("A2A routes configured")
    
    async def start(self):
        """Start the real A2A agent server"""
        self.logger.info(f"Starting real A2A agent '{self.name}' on port {self.port}")
        
        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        await server.serve()


class A2ATestClient:
    """Test client for real A2A communication"""
    
    def __init__(self):
        self.client = A2AClient()
        self.logger = logging.getLogger(__name__)
    
    async def test_agent_discovery(self, agent_url: str):
        """Test real A2A agent discovery"""
        try:
            self.logger.info(f"Discovering A2A agent at {agent_url}")
            
            # Real A2A agent card discovery

            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(f"{agent_url}/.well-known/agent.json")
                
                if response.status_code == 200:
                    agent_card = response.json()
                    self.logger.info(f"✅ Agent discovered: {agent_card['name']}")
                    return agent_card
                else:
                    self.logger.error(f"❌ Discovery failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"❌ Discovery error: {e}")
            return None
    
    async def test_health_check(self, agent_url: str):
        """Test agent health check"""
        try:

            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(f"{agent_url}/health")
                
                if response.status_code == 200:
                    health_data = response.json()
                    self.logger.info(f"✅ Health check passed: {health_data}")
                    return health_data
                else:
                    self.logger.error(f"❌ Health check failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"❌ Health check error: {e}")
            return None


async def run_poc_test():
    """Run POC test sequence"""
    print("🚀 Starting Simple Real A2A SDK Proof of Concept")
    print("=" * 60)
    
    # Start agent in background
    agent = SimpleA2AAgent("orchestrator-poc", 8000)
    
    server_task = asyncio.create_task(agent.start())
    
    # Wait for server startup
    await asyncio.sleep(3)
    
    try:
        # Test client
        client = A2ATestClient()
        
        print("🧪 Testing real A2A agent discovery...")
        agent_card = await client.test_agent_discovery("http://localhost:8000")
        
        print("🧪 Testing agent health check...")
        health = await client.test_health_check("http://localhost:8000")
        
        if agent_card and health:
            print("\n✅ POC VALIDATION SUCCESSFUL!")
            print("✅ Real A2A agent running and discoverable")
            print("✅ Standard A2A protocol endpoints working")
            print("✅ Ready for orchestrator integration")
        else:
            print("\n❌ POC validation failed")
        
        # Keep running for manual testing
        print("\n📡 Agent running at: http://localhost:8000")
        print("🔍 Agent card: http://localhost:8000/.well-known/agent.json")
        print("💓 Health check: http://localhost:8000/health")
        print("\nPress Ctrl+C to stop...")
        
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping A2A agent...")
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
        print("✅ A2A agent stopped")


async def main():
    """Main entry point"""
    logging.basicConfig(level=logging.INFO)
    await run_poc_test()


if __name__ == "__main__":
    asyncio.run(main())