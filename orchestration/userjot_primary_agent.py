#!/usr/bin/env python3
"""
UserJot Primary Agent Implementation
Primary Agent coordinator following UserJot two-tier architecture patterns
"""

import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


@dataclass
class SubagentRequest:
    """Structured request format for subagents"""
    objective: str
    context: Dict[str, Any]
    constraints: Dict[str, Any]
    success_criteria: str
    timeout: int = 30


@dataclass
class SubagentResponse:
    """Structured response format from subagents"""
    result: Any
    success: bool
    confidence: float
    metrics: Dict[str, Any]
    notes: str = ""
    error: Optional[str] = None


@dataclass
class TaskContext:
    """Context package prepared by Primary Agent for subagents"""
    task_id: str
    user_objective: str
    relevant_code: Optional[str] = None
    requirements: List[str] = None
    constraints: List[str] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.requirements is None:
            self.requirements = []
        if self.constraints is None:
            self.constraints = []


class UserJotPrimaryAgent:
    """
    Primary Agent following UserJot architecture patterns
    
    Responsibilities:
    - Maintain conversation context
    - Analyze tasks and select subagents
    - Prepare minimal context packages for stateless subagents
    - Coordinate parallel subagent execution
    - Integrate responses and track performance
    """
    
    def __init__(self):
        self.conversation_context = {}
        self.task_history = []
        self.subagent_registry = {}
        self.performance_metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "average_response_time": 0,
            "subagent_success_rates": {}
        }
        
        # Register available subagents
        self._register_subagents()
    
    def _register_subagents(self):
        """Register available stateless subagents"""
        self.subagent_registry = {
            "code_reviewer": {
                "module": "userjot_subagents.code_reviewer",
                "function": "review_code",
                "description": "Security and quality analysis of code",
                "required_context": ["code", "requirements"],
                "optional_context": ["security_level", "standards"]
            },
            "test_generator": {
                "module": "userjot_subagents.test_generator", 
                "function": "generate_tests",
                "description": "Generate comprehensive test cases",
                "required_context": ["code", "test_type"],
                "optional_context": ["coverage_target", "framework"]
            },
            "documentation": {
                "module": "userjot_subagents.documentation",
                "function": "generate_docs",
                "description": "Generate technical documentation", 
                "required_context": ["code", "doc_type"],
                "optional_context": ["audience", "format"]
            },
            "security_analyzer": {
                "module": "userjot_subagents.security_analyzer",
                "function": "analyze_security",
                "description": "Identify security vulnerabilities",
                "required_context": ["code", "security_checklist"],
                "optional_context": ["threat_model", "compliance"]
            },
            "qwen_coder": {
                "module": "userjot_subagents.qwen_coder",
                "function": "generate_code",
                "description": "Generate large blocks of code using Qwen model",
                "required_context": ["requirements", "language"],
                "optional_context": ["framework", "existing_code", "style_guide"],
                "specialization": "large_code_generation",
                "estimated_lines_threshold": 50
            }
        }
    
    def update_conversation_context(self, user_input: str, assistant_response: str = None):
        """Update conversation context maintained by Primary Agent"""
        timestamp = time.time()
        
        if "messages" not in self.conversation_context:
            self.conversation_context["messages"] = []
        
        self.conversation_context["messages"].append({
            "role": "user",
            "content": user_input,
            "timestamp": timestamp
        })
        
        if assistant_response:
            self.conversation_context["messages"].append({
                "role": "assistant", 
                "content": assistant_response,
                "timestamp": timestamp
            })
        
        # Keep conversation context manageable
        if len(self.conversation_context["messages"]) > 20:
            self.conversation_context["messages"] = self.conversation_context["messages"][-20:]
    
    def analyze_task(self, user_request: str) -> Dict[str, Any]:
        """
        Analyze user request to determine required subagents and context
        Returns task analysis with subagent selection
        """
        task_analysis = {
            "task_id": f"task_{int(time.time())}",
            "original_request": user_request,
            "required_subagents": [],
            "parallel_execution": True,
            "estimated_complexity": "medium"
        }
        
        # Simple keyword-based analysis (could be enhanced with LLM)
        request_lower = user_request.lower()
        
        if any(word in request_lower for word in ["review", "security", "vulnerable", "safe"]):
            task_analysis["required_subagents"].append("code_reviewer")
            
        if any(word in request_lower for word in ["test", "testing", "coverage", "unittest"]):
            task_analysis["required_subagents"].append("test_generator")
            
        if any(word in request_lower for word in ["document", "docs", "documentation", "readme"]):
            task_analysis["required_subagents"].append("documentation")
            
        if any(word in request_lower for word in ["security", "exploit", "vulnerability", "attack"]):
            task_analysis["required_subagents"].append("security_analyzer")
        
        # Intelligent Qwen selection for large code generation
        if self._should_use_qwen_coder(request_lower):
            task_analysis["required_subagents"].append("qwen_coder")
            task_analysis["estimated_complexity"] = "high"
        
        # Default to code review if no specific subagent identified
        if not task_analysis["required_subagents"]:
            task_analysis["required_subagents"].append("code_reviewer")
        
        return task_analysis
    
    def _should_use_qwen_coder(self, request_lower: str) -> bool:
        """
        Intelligent decision logic for when to use Qwen coder subagent
        Based on indicators of large/complex code generation needs
        """
        # Large code generation indicators
        large_code_patterns = [
            "create class", "implement class", "build application", "develop system",
            "generate module", "create framework", "build library", "implement api",
            "full implementation", "complete code", "entire system", "whole application"
        ]
        
        # Multi-file generation indicators  
        multi_file_patterns = [
            "multiple files", "several files", "project structure", "directory structure",
            "scaffold", "boilerplate", "template", "starter", "framework setup"
        ]
        
        # Complex algorithm indicators
        complex_patterns = [
            "algorithm", "data structure", "complex logic", "state machine",
            "parser", "compiler", "interpreter", "optimization", "machine learning"
        ]
        
        # Size indicators
        size_patterns = [
            "large", "big", "extensive", "comprehensive", "detailed", "complete",
            "full", "entire", "whole", "complex", "advanced", "sophisticated"
        ]
        
        # Language-specific complex patterns
        language_complex_patterns = [
            "react component", "vue component", "angular component", 
            "express server", "flask app", "django model", "fastapi",
            "neural network", "pytorch", "tensorflow", "pandas analysis"
        ]
        
        # Check for any indicators
        if any(pattern in request_lower for pattern in large_code_patterns):
            return True
        if any(pattern in request_lower for pattern in multi_file_patterns):
            return True
        if any(pattern in request_lower for pattern in complex_patterns):
            return True
        if any(pattern in request_lower for pattern in language_complex_patterns):
            return True
        
        # Size + generation combination
        has_size_indicator = any(pattern in request_lower for pattern in size_patterns)
        has_generation_indicator = any(word in request_lower for word in ["create", "generate", "build", "implement", "develop", "write"])
        
        if has_size_indicator and has_generation_indicator:
            return True
        
        return False
    
    def prepare_subagent_context(self, task_analysis: Dict[str, Any], full_context: Dict[str, Any]) -> TaskContext:
        """
        Prepare minimal context package for stateless subagents
        Following UserJot principle of minimal required context only
        """
        return TaskContext(
            task_id=task_analysis["task_id"],
            user_objective=task_analysis["original_request"],
            relevant_code=full_context.get("code", ""),
            requirements=full_context.get("requirements", []),
            constraints=full_context.get("constraints", [])
        )
    
    def execute_subagent(self, subagent_name: str, request: SubagentRequest) -> SubagentResponse:
        """
        Execute a single stateless subagent
        Each subagent is called as a pure function with no shared state
        """
        start_time = time.time()
        
        try:
            subagent_info = self.subagent_registry.get(subagent_name)
            if not subagent_info:
                return SubagentResponse(
                    result=None,
                    success=False,
                    confidence=0.0,
                    metrics={"error": "Subagent not found"},
                    error=f"Subagent {subagent_name} not registered"
                )
            
            # For now, simulate subagent execution
            # In real implementation, would dynamically import and call subagent
            result = self._simulate_subagent_execution(subagent_name, request)
            
            execution_time = time.time() - start_time
            
            return SubagentResponse(
                result=result,
                success=True,
                confidence=0.85,
                metrics={
                    "execution_time": execution_time,
                    "context_size": len(str(request.context)),
                    "subagent": subagent_name
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Subagent {subagent_name} execution failed: {e}")
            
            return SubagentResponse(
                result=None,
                success=False,
                confidence=0.0,
                metrics={"execution_time": execution_time, "subagent": subagent_name},
                error=str(e)
            )
    
    def _simulate_subagent_execution(self, subagent_name: str, request: SubagentRequest) -> str:
        """Simulate subagent execution for demo purposes"""
        simulations = {
            "code_reviewer": f"Code review completed for: {request.objective[:50]}...\n✅ Security: Pass\n✅ Quality: Good\n⚠️ Recommendation: Add input validation",
            "test_generator": f"Generated test cases for: {request.objective[:50]}...\n✅ Unit tests: 5 cases\n✅ Integration tests: 2 cases\n✅ Coverage: 85%",
            "documentation": f"Documentation generated for: {request.objective[:50]}...\n✅ API documentation\n✅ Usage examples\n✅ Installation guide",
            "security_analyzer": f"Security analysis completed for: {request.objective[:50]}...\n✅ No critical vulnerabilities\n⚠️ 2 minor issues found\n✅ Compliance: OWASP verified"
        }
        
        return simulations.get(subagent_name, f"Executed {subagent_name} for {request.objective}")
    
    def execute_parallel_subagents(self, task_analysis: Dict[str, Any], context: TaskContext) -> List[SubagentResponse]:
        """
        Execute multiple stateless subagents in parallel
        Key UserJot benefit: Stateless design enables safe concurrent execution
        """
        subagent_requests = []
        
        for subagent_name in task_analysis["required_subagents"]:
            subagent_info = self.subagent_registry[subagent_name]
            
            # Prepare minimal context for this subagent
            minimal_context = {
                "objective": context.user_objective,
                "code": context.relevant_code,
                "requirements": context.requirements
            }
            
            request = SubagentRequest(
                objective=f"{subagent_info['description']}: {context.user_objective}",
                context=minimal_context,
                constraints={"timeout": 30},
                success_criteria="Complete analysis with actionable recommendations"
            )
            
            subagent_requests.append((subagent_name, request))
        
        # Execute subagents in parallel
        responses = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_subagent = {
                executor.submit(self.execute_subagent, name, req): name 
                for name, req in subagent_requests
            }
            
            for future in as_completed(future_to_subagent):
                subagent_name = future_to_subagent[future]
                try:
                    response = future.result()
                    response.metrics.setdefault("subagent", subagent_name)
                    responses.append(response)
                    logger.info(f"Subagent {subagent_name} completed: success={response.success}")
                except Exception as e:
                    logger.error(f"Subagent {subagent_name} failed: {e}")
                    responses.append(SubagentResponse(
                        result=None,
                        success=False,
                        confidence=0.0,
                        metrics={"error": str(e), "subagent": subagent_name},
                        error=str(e)
                    ))
        
        return responses
    
    def integrate_responses(self, responses: List[SubagentResponse], task_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Integrate subagent responses into coherent result
        Primary Agent responsibility: Synthesize stateless subagent outputs
        """
        successful_responses = [r for r in responses if r.success]
        failed_responses = [r for r in responses if not r.success]
        required_subagents = task_analysis.get("required_subagents", [])
        response_index_map = {id(resp): index for index, resp in enumerate(responses)}
        
        integrated_result = {
            "task_id": task_analysis["task_id"],
            "original_request": task_analysis["original_request"],
            "overall_success": len(successful_responses) > 0,
            "subagent_results": {},
            "failed_subagents": [],
            "summary": "",
            "recommendations": [],
            "metrics": {
                "total_subagents": len(responses),
                "successful_subagents": len(successful_responses),
                "failed_subagents": len(failed_responses),
                "success_rate": len(successful_responses) / len(responses) if responses else 0,
                "average_confidence": sum(r.confidence for r in successful_responses) / len(successful_responses) if successful_responses else 0
            }
        }
        
        # Aggregate successful results
        for response in successful_responses:
            subagent_name = response.metrics.get("subagent")
            if not subagent_name:
                original_index = response_index_map.get(id(response))
                if original_index is not None and original_index < len(required_subagents):
                    subagent_name = required_subagents[original_index]
                else:
                    subagent_name = "subagent_unknown"
            integrated_result["subagent_results"][subagent_name] = {
                "result": response.result,
                "confidence": response.confidence,
                "metrics": response.metrics,
                "notes": response.notes
            }

        for response in failed_responses:
            subagent_name = response.metrics.get("subagent")
            if not subagent_name:
                original_index = response_index_map.get(id(response))
                if original_index is not None and original_index < len(required_subagents):
                    subagent_name = required_subagents[original_index]
                else:
                    subagent_name = "subagent_unknown"
            integrated_result["failed_subagents"].append(
                {
                    "subagent": subagent_name,
                    "error": response.error or response.metrics.get("error"),
                    "metrics": response.metrics,
                }
            )
        
        # Generate summary
        if successful_responses:
            integrated_result["summary"] = f"Task completed successfully using {len(successful_responses)} subagents. "
            integrated_result["summary"] += f"Overall confidence: {integrated_result['metrics']['average_confidence']:.2f}"
        else:
            integrated_result["summary"] = "Task failed - no subagents completed successfully"
        
        # Extract recommendations
        for response in successful_responses:
            if response.result and "recommendation" in str(response.result).lower():
                integrated_result["recommendations"].append(response.result)
        
        return integrated_result
    
    def update_performance_metrics(self, task_result: Dict[str, Any]):
        """Update Primary Agent performance tracking"""
        self.performance_metrics["total_tasks"] += 1
        
        if task_result["overall_success"]:
            self.performance_metrics["successful_tasks"] += 1
        
        # Update success rate
        success_rate = self.performance_metrics["successful_tasks"] / self.performance_metrics["total_tasks"]
        self.performance_metrics["overall_success_rate"] = success_rate
        
        # Update subagent success rates
        for subagent_name, result in task_result["subagent_results"].items():
            if subagent_name not in self.performance_metrics["subagent_success_rates"]:
                self.performance_metrics["subagent_success_rates"][subagent_name] = {"attempts": 0, "successes": 0}
            
            self.performance_metrics["subagent_success_rates"][subagent_name]["attempts"] += 1
            if result.get("confidence", 0) > 0.5:
                self.performance_metrics["subagent_success_rates"][subagent_name]["successes"] += 1
    
    def process_user_request(self, user_request: str, additional_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main entry point: Process user request using UserJot two-tier architecture
        
        Flow:
        1. Primary Agent analyzes task
        2. Prepares minimal context for stateless subagents
        3. Executes subagents in parallel
        4. Integrates responses
        5. Updates performance metrics
        """
        start_time = time.time()
        
        try:
            # Update conversation context
            self.update_conversation_context(user_request)
            
            # Analyze task and select subagents
            task_analysis = self.analyze_task(user_request)
            logger.info(f"Task analysis: {task_analysis['required_subagents']}")
            
            # Prepare context package for subagents
            context = self.prepare_subagent_context(
                task_analysis, 
                additional_context or {}
            )
            
            # Execute stateless subagents in parallel
            subagent_responses = self.execute_parallel_subagents(task_analysis, context)
            
            # Integrate responses
            integrated_result = self.integrate_responses(subagent_responses, task_analysis)
            
            # Update performance metrics
            self.update_performance_metrics(integrated_result)
            
            # Add execution metrics
            integrated_result["execution_time"] = time.time() - start_time
            
            return integrated_result
            
        except Exception as e:
            logger.error(f"Primary Agent processing failed: {e}")
            return {
                "task_id": f"failed_{int(time.time())}",
                "overall_success": False,
                "error": str(e),
                "execution_time": time.time() - start_time
            }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get Primary Agent performance summary"""
        return {
            "agent_type": "UserJot Primary Agent",
            "architecture": "Two-tier with Stateless Subagents",
            "metrics": self.performance_metrics.copy(),
            "active_subagents": list(self.subagent_registry.keys()),
            "conversation_messages": len(self.conversation_context.get("messages", [])),
            "task_history_size": len(self.task_history)
        }


def demo_userjot_architecture():
    """Demonstrate UserJot Primary Agent architecture"""
    print("🧠 UserJot Primary Agent Architecture Demo")
    print("=" * 50)
    
    # Initialize Primary Agent
    primary_agent = UserJotPrimaryAgent()
    
    # Demo scenarios
    test_scenarios = [
        {
            "request": "Review this authentication code for security vulnerabilities",
            "context": {
                "code": "def login(username, password):\n    if username == 'admin' and password == 'password':\n        return True\n    return False",
                "requirements": ["secure authentication", "input validation"]
            }
        },
        {
            "request": "Generate tests and documentation for the user registration module",
            "context": {
                "code": "def register_user(email, password):\n    # Registration logic\n    return user_id",
                "requirements": ["comprehensive testing", "API documentation"]
            }
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📋 Scenario {i}: {scenario['request']}")
        print("-" * 40)
        
        # Process request through Primary Agent
        result = primary_agent.process_user_request(
            scenario["request"], 
            scenario["context"]
        )
        
        print(f"✅ Task Success: {result['overall_success']}")
        print(f"🎯 Success Rate: {result['metrics']['success_rate']:.2%}")
        print(f"⏱️ Execution Time: {result['execution_time']:.2f}s")
        print(f"🤖 Subagents Used: {len(result['subagent_results'])}")
        
        # Show subagent results
        for subagent_name, subagent_result in result["subagent_results"].items():
            print(f"\n   {subagent_name}:")
            print(f"   └─ {subagent_result['result'][:100]}...")
            print(f"   └─ Confidence: {subagent_result['confidence']:.2f}")
    
    # Show performance summary
    print(f"\n📊 Primary Agent Performance Summary:")
    summary = primary_agent.get_performance_summary()
    print(f"   Architecture: {summary['architecture']}")
    print(f"   Total Tasks: {summary['metrics']['total_tasks']}")
    print(f"   Success Rate: {summary['metrics'].get('overall_success_rate', 0):.2%}")
    print(f"   Available Subagents: {len(summary['active_subagents'])}")


if __name__ == "__main__":
    demo_userjot_architecture()
