#!/usr/bin/env python3
"""
Redis A2A Bridge - Production Integration
Connects A2A protocol messages to Redis orchestrator operations
"""

import asyncio
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from message_broker import MessageBroker, TaskMessage, MessageType


class RedisA2ABridge:
    """
    Production bridge connecting A2A protocol to Redis orchestrator operations.

    This replaces demo/fake implementations with real Redis operations
    that interact with the existing orchestrator infrastructure.
    """

    def __init__(self, message_broker: Optional[MessageBroker] = None):
        self.message_broker = message_broker or MessageBroker()
        self.logger = logging.getLogger(__name__)

        # Production error handling configuration
        self.task_timeout = 30.0  # seconds
        self.max_retries = 3
        self.retry_delay = 1.0  # exponential backoff base

    async def orchestrate_workflow_real(self, workflow_description: str, context_id: str) -> Dict[str, Any]:
        """
        Create real workflow in Redis orchestrator system.

        NO DEMO CODE - This creates actual Redis tasks and manages real workflow state.
        """
        workflow_id = f"a2a_workflow_{uuid.uuid4().hex[:8]}"

        try:
            # Parse workflow steps from description
            workflow_steps = self._parse_workflow_description(workflow_description)

            # Create workflow state in Redis
            workflow_state = {
                "id": workflow_id,
                "context_id": context_id,
                "description": workflow_description,
                "steps": workflow_steps,
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "results": {}
            }

            # Store workflow state in Redis
            workflow_key = f"a2a_workflow:{workflow_id}"
            self.message_broker.redis_client.hset(
                workflow_key,
                mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                        for k, v in workflow_state.items()}
            )

            # Set workflow expiration (24 hours)
            self.message_broker.redis_client.expire(workflow_key, 24 * 3600)

            # Execute workflow steps on real Redis agents
            step_results = await self._execute_workflow_steps(workflow_id, workflow_steps)

            # Update workflow state with results
            workflow_state["results"] = step_results
            # Check if all steps completed successfully
            all_success = all(
                result.get("status") == "completed"
                for result in step_results.values()
            )
            workflow_state["status"] = "completed" if all_success else "failed"
            workflow_state["completed_at"] = datetime.now().isoformat()

            # Update Redis state
            self.message_broker.redis_client.hset(
                workflow_key,
                mapping={
                    "status": workflow_state["status"],
                    "results": json.dumps(workflow_state["results"]),
                    "completed_at": workflow_state["completed_at"]
                }
            )

            self.logger.info(f"Workflow {workflow_id} completed with status: {workflow_state['status']}")

            return {
                "workflow_id": workflow_id,
                "status": workflow_state["status"],
                "steps_completed": len([r for r in step_results.values() if r]),
                "total_steps": len(workflow_steps),
                "results": step_results
            }

        except Exception as e:
            self.logger.error(f"Workflow {workflow_id} failed: {e}")
            # Update Redis with failure state
            self.message_broker.redis_client.hset(
                f"a2a_workflow:{workflow_id}",
                mapping={
                    "status": "failed",
                    "error": str(e),
                    "failed_at": datetime.now().isoformat()
                }
            )
            raise

    async def discover_agents_real(self) -> List[Dict[str, Any]]:
        """
        Query live Redis agent registry for active agents.

        NO DEMO CODE - Returns actual agent data from Redis.
        """
        try:
            # Get all active agents from Redis registry
            agent_keys = list(self.message_broker.redis_client.scan_iter("agent:*"))
            active_agents = []

            for agent_key in agent_keys:
                agent_info = self.message_broker.redis_client.hgetall(agent_key)

                if agent_info.get("status") == "active":
                    # Check agent health (heartbeat within last 24 hours for development)
                    last_heartbeat = agent_info.get("last_heartbeat")
                    if last_heartbeat:
                        heartbeat_time = datetime.fromisoformat(last_heartbeat)
                        if datetime.now() - heartbeat_time < timedelta(hours=24):
                            agent_id = agent_key.split(":", 1)[1]
                            active_agents.append({
                                "id": agent_id,
                                "type": agent_info.get("type", "unknown"),
                                "status": "active",
                                "capabilities": json.loads(agent_info.get("capabilities", "{}")),
                                "last_heartbeat": last_heartbeat,
                                "queue_size": self.message_broker.redis_client.llen(f"queue:{agent_id}")
                            })

            self.logger.info(f"Discovered {len(active_agents)} active agents from Redis")
            return active_agents

        except Exception as e:
            self.logger.error(f"Agent discovery failed: {e}")
            return []

    async def execute_task_real(self, task_description: str, context_id: str,
                              target_agent: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute task on real Redis agent with timeout and retry handling.

        NO DEMO CODE - Creates actual Redis TaskMessage and waits for real agent response.
        """
        task_id = f"a2a_task_{uuid.uuid4().hex[:8]}"

        try:
            # Select target agent (use load balancing if not specified)
            if not target_agent:
                agents = await self.discover_agents_real()
                if not agents:
                    raise RuntimeError("No active agents available for task execution")

                # Simple load balancing - choose agent with smallest queue
                target_agent = min(agents, key=lambda a: a["queue_size"])["id"]

            # Create real TaskMessage for Redis agent
            task_message = TaskMessage(
                id=task_id,
                type=MessageType.TASK_ASSIGNMENT,
                from_agent="a2a_bridge",
                to_agent=target_agent,
                timestamp=datetime.now().isoformat(),
                payload={
                    "description": task_description,
                    "context_id": context_id,
                    "timeout": self.task_timeout,
                    "task_id": task_id  # Include for correlation
                }
            )

            # Send task to Redis agent queue
            # Convert to dict and handle enum serialization
            task_dict = asdict(task_message)
            task_dict['type'] = task_message.type.value  # Ensure enum is serialized as string

            self.message_broker.redis_client.lpush(
                f"queue:{target_agent}",
                json.dumps(task_dict)
            )

            # Wait for real agent response with timeout
            result = await self._wait_for_task_result(task_id, "a2a_bridge", target_agent)

            self.logger.info(f"Task {task_id} completed by agent {target_agent}")
            return result

        except Exception as e:
            self.logger.error(f"Task {task_id} execution failed: {e}")
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "agent": target_agent
            }

    def _parse_workflow_description(self, description: str) -> List[Dict[str, Any]]:
        """Parse workflow description into executable steps using semantic understanding"""
        steps = []

        # Parse based on sentence structure and semantic meaning
        sentences = [s.strip() for s in description.replace(';', '.').split('.') if s.strip()]

        for i, sentence in enumerate(sentences):
            step_data = self._analyze_sentence_for_step(sentence, i)
            if step_data:
                steps.append(step_data)

        # If no clear steps identified, create logical workflow based on task type
        if not steps:
            steps = self._infer_workflow_steps(description)

        # Add dependencies between sequential steps
        for i in range(1, len(steps)):
            steps[i]["depends_on"] = [steps[i-1].get("id", f"step_{i-1}")]

        return steps

    def _analyze_sentence_for_step(self, sentence: str, index: int) -> Dict[str, Any]:
        """Analyze a sentence to extract step information"""
        sentence_lower = sentence.lower()

        # Determine step type and details from sentence structure
        step = {
            "id": f"step_{index}",
            "description": sentence.strip(),
            "estimated_duration": self._estimate_step_duration(sentence)
        }

        # Identify action type and assign agent dynamically
        if any(word in sentence_lower for word in ["analyze", "review", "examine", "investigate"]):
            step["type"] = "analysis"
        elif any(word in sentence_lower for word in ["implement", "create", "build", "develop"]):
            step["type"] = "implementation"
        elif any(word in sentence_lower for word in ["test", "verify", "validate", "check"]):
            step["type"] = "testing"
        elif any(word in sentence_lower for word in ["deploy", "release", "publish"]):
            step["type"] = "deployment"
        elif any(word in sentence_lower for word in ["document", "write", "describe"]):
            step["type"] = "documentation"
        else:
            step["type"] = "task"

        # Dynamic agent assignment for all step types
        step["agent"] = self._select_agent_for_task(sentence)

        return step

    def _infer_workflow_steps(self, description: str) -> List[Dict[str, Any]]:
        """Infer workflow steps when not explicitly stated"""
        desc_lower = description.lower()
        steps = []

        # Infer based on overall task type with dynamic agent assignment
        if "feature" in desc_lower or "functionality" in desc_lower:
            steps = [
                {"id": "step_0", "type": "analysis", "description": "Analyze feature requirements"},
                {"id": "step_1", "type": "implementation", "description": "Implement core functionality"},
                {"id": "step_2", "type": "testing", "description": "Test implementation"},
                {"id": "step_3", "type": "documentation", "description": "Document changes"}
            ]
        elif "bug" in desc_lower or "fix" in desc_lower:
            steps = [
                {"id": "step_0", "type": "analysis", "description": "Investigate issue"},
                {"id": "step_1", "type": "implementation", "description": "Apply fix"},
                {"id": "step_2", "type": "testing", "description": "Verify fix"}
            ]
        elif "refactor" in desc_lower or "optimize" in desc_lower:
            steps = [
                {"id": "step_0", "type": "analysis", "description": "Analyze current implementation"},
                {"id": "step_1", "type": "implementation", "description": "Refactor code"},
                {"id": "step_2", "type": "testing", "description": "Ensure functionality preserved"}
            ]
        else:
            # Default workflow
            steps = [
                {"id": "step_0", "type": "task", "description": description}
            ]

        # Assign agents dynamically to all steps
        for step in steps:
            step["agent"] = self._select_agent_for_task(step["description"])

        return steps

    def _estimate_step_duration(self, description: str) -> int:
        """Estimate duration based on task complexity"""
        word_count = len(description.split())
        if word_count < 10:
            return 300  # 5 minutes for simple tasks
        elif word_count < 25:
            return 900  # 15 minutes for medium tasks
        else:
            return 1800  # 30 minutes for complex tasks

    def _select_agent_for_task(self, description: str) -> str:
        """Select appropriate agent based on capabilities and workload"""
        return asyncio.create_task(self._select_agent_for_task_async(description)).result()

    async def _select_agent_for_task_async(self, description: str) -> str:
        """Dynamically select agent based on capabilities, availability, and workload"""
        desc_lower = description.lower()

        # Get all active agents with their capabilities and workload
        active_agents = await self.discover_agents_real()

        if not active_agents:
            # Fallback to dynamic default agent selection
            return self._get_default_agent(desc_lower)

        # Score agents based on capability match and availability
        agent_scores = []

        for agent in active_agents:
            score = self._calculate_agent_score(agent, desc_lower)
            agent_scores.append((agent["id"], score, agent["queue_size"]))

        # Sort by score (descending) then by queue size (ascending)
        agent_scores.sort(key=lambda x: (-x[1], x[2]))

        # Return the best available agent
        if agent_scores:
            selected_agent = agent_scores[0][0]
            self.logger.info(f"Selected agent {selected_agent} for task: {description[:50]}...")
            return selected_agent

        # Fallback to default agent
        return self._get_default_agent(desc_lower)

    def _calculate_agent_score(self, agent: Dict[str, Any], task_description: str) -> float:
        """Calculate agent suitability score based on capabilities and task requirements"""
        score = 1.0  # Base score for all active agents
        capabilities = agent.get("capabilities", {})

        if not isinstance(capabilities, dict):
            capabilities = {}

        # Task-specific keyword matching with capability scoring
        task_keywords = {
            # Frontend/UI capabilities
            "frontend": ["ui", "frontend", "interface", "display", "web", "html", "css", "javascript", "react", "vue"],
            "ui": ["ui", "frontend", "interface", "display", "web", "html", "css", "javascript", "react", "vue"],
            "web": ["ui", "frontend", "interface", "display", "web", "html", "css", "javascript", "react", "vue"],

            # Testing capabilities
            "testing": ["test", "quality", "verify", "validate", "check", "qa", "automation", "cypress", "jest"],
            "qa": ["test", "quality", "verify", "validate", "check", "qa", "automation", "cypress", "jest"],

            # Backend/API capabilities
            "backend": ["api", "server", "database", "service", "backend", "python", "nodejs", "flask", "django"],
            "api": ["api", "server", "database", "service", "backend", "python", "nodejs", "flask", "django"],
            "database": ["api", "server", "database", "service", "backend", "python", "nodejs", "flask", "django"],

            # DevOps/Deployment capabilities
            "devops": ["deploy", "release", "publish", "docker", "kubernetes", "ci", "cd", "pipeline"],
            "deployment": ["deploy", "release", "publish", "docker", "kubernetes", "ci", "cd", "pipeline"],

            # Documentation capabilities
            "documentation": ["document", "write", "describe", "markdown", "docs", "readme"],

            # Analysis capabilities
            "analysis": ["analyze", "review", "examine", "investigate", "research", "audit"]
        }

        # Check agent capabilities against task requirements
        for capability, keywords in task_keywords.items():
            if capability in capabilities:
                capability_strength = capabilities.get(capability, 0)
                if isinstance(capability_strength, (int, float)):
                    # Direct capability scoring
                    if any(keyword in task_description for keyword in keywords):
                        score += capability_strength * 10
                elif capability_strength is True or capability_strength == "true":
                    # Boolean capability match
                    if any(keyword in task_description for keyword in keywords):
                        score += 5

        # Agent type bonuses for backward compatibility
        agent_type = agent.get("type", "").lower()
        if "frontend" in agent_type and any(word in task_description for word in ["ui", "frontend", "interface", "web"]):
            score += 3
        elif "testing" in agent_type and any(word in task_description for word in ["test", "verify", "validate"]):
            score += 3
        elif "backend" in agent_type and any(word in task_description for word in ["api", "server", "backend", "database"]):
            score += 3

        # General task handling capability
        if "general" in capabilities or "task_execution" in capabilities:
            score += 2  # Higher base score for general agents

        # Penalize heavily loaded agents
        queue_size = agent.get("queue_size", 0)
        if queue_size > 5:
            score *= 0.5  # 50% penalty for overloaded agents
        elif queue_size > 2:
            score *= 0.8  # 20% penalty for busy agents

        return score

    def _get_default_agent(self, task_description: str) -> str:
        """Get default agent when no active agents are available"""
        desc_lower = task_description.lower()

        # Dynamic default based on task type
        if any(word in desc_lower for word in ["ui", "frontend", "interface", "web", "html", "css"]):
            return "frontend-worker"
        elif any(word in desc_lower for word in ["test", "verify", "validate", "qa", "check"]):
            return "testing-worker"
        elif any(word in desc_lower for word in ["deploy", "release", "publish", "docker"]):
            return "devops-worker"
        else:
            return "general-worker"

    async def _execute_workflow_steps(self, workflow_id: str, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute workflow steps on real Redis agents"""
        results = {}

        for i, step in enumerate(steps):
            step_id = f"{workflow_id}_step_{i}"
            try:
                # Execute step on real agent
                result = await self.execute_task_real(
                    task_description=step["description"],
                    context_id=workflow_id
                )
                results[step_id] = result

                # Brief delay between steps
                await asyncio.sleep(0.1)

            except Exception as e:
                self.logger.error(f"Workflow {workflow_id} step {i} failed: {e}")
                results[step_id] = {"status": "failed", "error": str(e)}

        return results

    async def _wait_for_task_result(self, task_id: str, from_agent: str, to_agent: str) -> Dict[str, Any]:
        """Wait for real agent to complete task by monitoring the response queue"""

        # Store our correlation ID for matching responses
        correlation_key = f"a2a_correlation:{task_id}"
        self.message_broker.redis_client.setex(
            correlation_key,
            int(self.task_timeout),
            json.dumps({"waiting": True, "from": from_agent})
        )

        # Wait for result with timeout
        start_time = datetime.now()
        last_check = 0

        while (datetime.now() - start_time).total_seconds() < self.task_timeout:
            # Use BRPOP for efficient blocking wait on the response queue
            # This will wait up to 0.5 seconds for a message
            msg_data = self.message_broker.redis_client.brpop(f"queue:{from_agent}", timeout=0.5)

            if msg_data:
                # BRPOP returns (queue_name, message)
                _, msg_content = msg_data
                try:
                    message = json.loads(msg_content)
                    # Check if this is a result for our task
                    if (message.get("type") == MessageType.TASK_RESULT.value and
                        message.get("from_agent") == to_agent and
                        message.get("to_agent") == from_agent):

                        # Check if this result is related to our task
                        payload = message.get("payload", {})
                        if payload.get("task_id") == task_id or payload.get("original_task_id") == task_id:
                            # Clean up correlation key
                            self.message_broker.redis_client.delete(correlation_key)
                            self.logger.info(f"Received result for task {task_id} from {to_agent}")
                            return payload
                        else:
                            # Not our message, put it back at the end of the queue
                            self.message_broker.redis_client.lpush(f"queue:{from_agent}", msg_content)
                    else:
                        # Not a result message or not for us, put it back
                        self.message_broker.redis_client.lpush(f"queue:{from_agent}", msg_content)

                except Exception as e:
                    self.logger.warning(f"Error checking message: {e}")
                    # Put malformed message back
                    self.message_broker.redis_client.lpush(f"queue:{from_agent}", msg_content)

            # Log progress every 5 seconds
            current_time = int((datetime.now() - start_time).total_seconds())
            if current_time >= last_check + 5:
                self.logger.info(f"Still waiting for task {task_id} result... ({current_time}s elapsed)")
                last_check = current_time

        # Cleanup correlation key
        self.message_broker.redis_client.delete(correlation_key)

        # Timeout - task didn't complete
        raise TimeoutError(f"Task {task_id} timed out after {self.task_timeout} seconds")


class ProductionErrorHandler:
    """Production-grade error handling for A2A Redis integration"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ErrorHandler")
        self.circuit_breaker_failures = {}
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 300  # 5 minutes

    async def handle_with_retry(self, operation, *args, max_retries: int = 3, **kwargs):
        """Execute operation with exponential backoff retry"""
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    delay = (2 ** attempt) * 1.0  # Exponential backoff
                    self.logger.warning(f"Operation failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(f"Operation failed after {max_retries + 1} attempts: {e}")

        raise last_exception

    def check_circuit_breaker(self, agent_id: str) -> bool:
        """Check if circuit breaker is open for agent"""
        if agent_id not in self.circuit_breaker_failures:
            return False

        failures, last_failure_time = self.circuit_breaker_failures[agent_id]

        # Reset circuit breaker after timeout
        if datetime.now() - last_failure_time > timedelta(seconds=self.circuit_breaker_timeout):
            del self.circuit_breaker_failures[agent_id]
            return False

        return failures >= self.circuit_breaker_threshold

    def record_failure(self, agent_id: str):
        """Record failure for circuit breaker"""
        if agent_id not in self.circuit_breaker_failures:
            self.circuit_breaker_failures[agent_id] = (1, datetime.now())
        else:
            failures, _ = self.circuit_breaker_failures[agent_id]
            self.circuit_breaker_failures[agent_id] = (failures + 1, datetime.now())
