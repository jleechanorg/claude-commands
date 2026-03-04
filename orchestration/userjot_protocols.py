#!/usr/bin/env python3
"""
UserJot Communication Protocols
Structured communication patterns for Primary Agent + Stateless Subagents
"""

import time
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class SubagentStatus(Enum):
    """Standardized subagent execution status"""
    PENDING = "pending"
    RUNNING = "running" 
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class ProtocolRequest:
    """Standardized request format for UserJot subagents"""
    # Required fields
    request_id: str
    subagent_name: str
    objective: str
    context: Dict[str, Any]
    
    # Optional fields with defaults
    constraints: Dict[str, Any] = None
    success_criteria: str = "Task completed successfully"
    timeout_seconds: int = 30
    priority: str = "normal"  # low, normal, high, critical
    
    # Metadata
    timestamp: float = None
    primary_agent_id: str = "default"
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.constraints is None:
            self.constraints = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProtocolRequest':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class ProtocolResponse:
    """Standardized response format from UserJot subagents"""
    # Required fields
    request_id: str
    subagent_name: str
    status: SubagentStatus
    result: Any
    
    # Success metrics
    success: bool
    confidence: float  # 0.0 - 1.0
    
    # Performance metrics
    execution_time: float
    metrics: Dict[str, Any]
    
    # Optional fields
    error_message: Optional[str] = None
    warnings: List[str] = None
    notes: str = ""
    
    # Metadata
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.warnings is None:
            self.warnings = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProtocolResponse':
        """Create from dictionary"""
        # Convert status string back to enum
        if isinstance(data.get('status'), str):
            data['status'] = SubagentStatus(data['status'])
        return cls(**data)


@dataclass
class TaskContext:
    """Context package prepared by Primary Agent for subagents"""
    task_id: str
    user_objective: str
    
    # Code context
    code: Optional[str] = None
    file_path: Optional[str] = None
    
    # Requirements context
    requirements: List[str] = None
    constraints: List[str] = None
    
    # Additional context
    metadata: Dict[str, Any] = None
    
    # Timing
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.requirements is None:
            self.requirements = []
        if self.constraints is None:
            self.constraints = []
        if self.metadata is None:
            self.metadata = {}


class ProtocolValidator:
    """Validates requests and responses follow UserJot protocols"""
    
    @staticmethod
    def validate_request(request: ProtocolRequest) -> List[str]:
        """Validate request format and required fields"""
        errors = []
        
        # Required field validation
        if not request.request_id:
            errors.append("request_id is required")
        
        if not request.subagent_name:
            errors.append("subagent_name is required")
        
        if not request.objective:
            errors.append("objective is required")
        
        if not isinstance(request.context, dict):
            errors.append("context must be a dictionary")
        
        # Type validation
        if not isinstance(request.timeout_seconds, int) or request.timeout_seconds <= 0:
            errors.append("timeout_seconds must be a positive integer")
        
        if request.priority not in ["low", "normal", "high", "critical"]:
            errors.append("priority must be one of: low, normal, high, critical")
        
        return errors
    
    @staticmethod
    def validate_response(response: ProtocolResponse) -> List[str]:
        """Validate response format and required fields"""
        errors = []
        
        # Required field validation
        if not response.request_id:
            errors.append("request_id is required")
        
        if not response.subagent_name:
            errors.append("subagent_name is required")
        
        if not isinstance(response.status, SubagentStatus):
            errors.append("status must be a SubagentStatus enum")
        
        # Success/failure consistency
        if response.status == SubagentStatus.SUCCESS and not response.success:
            errors.append("status=SUCCESS but success=False - inconsistent")
        
        if response.status == SubagentStatus.FAILED and response.success:
            errors.append("status=FAILED but success=True - inconsistent")
        
        # Confidence validation
        if not 0.0 <= response.confidence <= 1.0:
            errors.append("confidence must be between 0.0 and 1.0")
        
        # Error message validation
        if response.status == SubagentStatus.FAILED and not response.error_message:
            errors.append("error_message required when status=FAILED")
        
        return errors


class ProtocolExecutor:
    """Executes subagents using UserJot protocols"""
    
    def __init__(self):
        self.subagent_registry = {}
        self.execution_history = []
        self.performance_metrics = {}
    
    def register_subagent(self, name: str, executor_func: Callable, metadata: Dict[str, Any] = None):
        """Register a stateless subagent function"""
        self.subagent_registry[name] = {
            "executor": executor_func,
            "metadata": metadata or {},
            "registered_at": time.time()
        }
        
        # Initialize performance metrics
        self.performance_metrics[name] = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0,
            "average_confidence": 0.0
        }
        
        logger.info(f"Registered subagent: {name}")
    
    def execute_subagent(self, request: ProtocolRequest) -> ProtocolResponse:
        """Execute a subagent using UserJot protocols"""
        start_time = time.time()
        
        # Validate request
        validation_errors = ProtocolValidator.validate_request(request)
        if validation_errors:
            return self._create_error_response(
                request, 
                f"Request validation failed: {', '.join(validation_errors)}",
                start_time
            )
        
        # Check if subagent is registered
        if request.subagent_name not in self.subagent_registry:
            return self._create_error_response(
                request,
                f"Subagent '{request.subagent_name}' not registered",
                start_time
            )
        
        try:
            # Get subagent executor
            subagent_info = self.subagent_registry[request.subagent_name]
            executor_func = subagent_info["executor"]
            
            # Execute subagent (stateless function call)
            logger.info(f"Executing subagent: {request.subagent_name}")
            
            subagent_result = executor_func(
                objective=request.objective,
                context=request.context,
                constraints=request.constraints,
                success_criteria=request.success_criteria
            )
            
            # Convert subagent result to protocol response
            execution_time = time.time() - start_time
            
            response = ProtocolResponse(
                request_id=request.request_id,
                subagent_name=request.subagent_name,
                status=SubagentStatus.SUCCESS if subagent_result.get("success", False) else SubagentStatus.FAILED,
                result=subagent_result.get("result"),
                success=subagent_result.get("success", False),
                confidence=subagent_result.get("confidence", 0.0),
                execution_time=execution_time,
                metrics=subagent_result.get("metrics", {}),
                error_message=subagent_result.get("error"),
                notes=subagent_result.get("notes", "")
            )
            
            # Update performance metrics
            self._update_performance_metrics(request.subagent_name, response)
            
            # Add to execution history
            self.execution_history.append({
                "request": request,
                "response": response,
                "timestamp": time.time()
            })
            
            logger.info(f"Subagent {request.subagent_name} completed: success={response.success}")
            return response
            
        except Exception as e:
            logger.error(f"Subagent {request.subagent_name} execution failed: {e}")
            return self._create_error_response(request, str(e), start_time)
    
    def execute_parallel_subagents(self, requests: List[ProtocolRequest]) -> List[ProtocolResponse]:
        """Execute multiple subagents in parallel using UserJot protocols"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        responses = []
        
        with ThreadPoolExecutor(max_workers=min(len(requests), 4)) as executor:
            # Submit all requests
            future_to_request = {}
            future_to_start_time = {}
            for req in requests:
                start_time = time.time()
                future = executor.submit(self.execute_subagent, req)
                future_to_request[future] = req
                future_to_start_time[future] = start_time
            
            # Collect responses as they complete
            for future in as_completed(future_to_request):
                request = future_to_request[future]
                try:
                    response = future.result()
                    responses.append(response)
                except Exception as e:
                    # Create error response if future failed
                    error_response = self._create_error_response(
                        request, 
                        f"Parallel execution failed: {str(e)}",
                        future_to_start_time.get(future, time.time())
                    )
                    responses.append(error_response)
        
        return responses
    
    def _create_error_response(self, request: ProtocolRequest, error_message: str, start_time: float) -> ProtocolResponse:
        """Create standardized error response"""
        execution_time = time.time() - start_time
        
        response = ProtocolResponse(
            request_id=request.request_id,
            subagent_name=request.subagent_name,
            status=SubagentStatus.FAILED,
            result=None,
            success=False,
            confidence=0.0,
            execution_time=execution_time,
            metrics={"error": True},
            error_message=error_message
        )
        
        # Update performance metrics for failed execution
        self._update_performance_metrics(request.subagent_name, response)
        
        return response
    
    def _update_performance_metrics(self, subagent_name: str, response: ProtocolResponse):
        """Update performance metrics for subagent"""
        if subagent_name not in self.performance_metrics:
            return
        
        metrics = self.performance_metrics[subagent_name]
        metrics["total_executions"] += 1
        
        if response.success:
            metrics["successful_executions"] += 1
        else:
            metrics["failed_executions"] += 1
        
        # Update running averages
        total_execs = metrics["total_executions"]
        
        # Execution time average
        old_avg_time = metrics["average_execution_time"]
        metrics["average_execution_time"] = (
            (old_avg_time * (total_execs - 1) + response.execution_time) / total_execs
        )
        
        # Confidence average (only for successful executions)
        if response.success:
            successful_execs = metrics["successful_executions"]
            old_avg_confidence = metrics["average_confidence"]
            metrics["average_confidence"] = (
                (old_avg_confidence * (successful_execs - 1) + response.confidence) / successful_execs
            )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for all registered subagents"""
        return {
            "registered_subagents": list(self.subagent_registry.keys()),
            "total_executions": len(self.execution_history),
            "performance_metrics": self.performance_metrics.copy(),
            "protocol_version": "1.0"
        }
    
    def get_subagent_status(self, subagent_name: str) -> Dict[str, Any]:
        """Get detailed status for specific subagent"""
        if subagent_name not in self.subagent_registry:
            return {"error": f"Subagent {subagent_name} not registered"}
        
        metrics = self.performance_metrics.get(subagent_name, {})
        success_rate = 0.0
        
        if metrics.get("total_executions", 0) > 0:
            success_rate = metrics["successful_executions"] / metrics["total_executions"]
        
        return {
            "subagent_name": subagent_name,
            "registration_info": self.subagent_registry[subagent_name]["metadata"],
            "performance_metrics": metrics,
            "success_rate": round(success_rate, 3),
            "status": "active"
        }


class UserJotProtocolManager:
    """High-level manager for UserJot communication protocols"""
    
    def __init__(self):
        self.executor = ProtocolExecutor()
        self.request_counter = 0
    
    def create_request(
        self, 
        subagent_name: str, 
        objective: str, 
        context: Dict[str, Any],
        **kwargs
    ) -> ProtocolRequest:
        """Create a properly formatted protocol request"""
        self.request_counter += 1
        
        return ProtocolRequest(
            request_id=f"req_{int(time.time())}_{self.request_counter}",
            subagent_name=subagent_name,
            objective=objective,
            context=context,
            **kwargs
        )
    
    def register_subagent(self, name: str, executor_func: Callable, metadata: Dict[str, Any] = None):
        """Register a subagent with the protocol manager"""
        self.executor.register_subagent(name, executor_func, metadata)
    
    def execute_single(self, subagent_name: str, objective: str, context: Dict[str, Any], **kwargs) -> ProtocolResponse:
        """Execute a single subagent with protocol handling"""
        request = self.create_request(subagent_name, objective, context, **kwargs)
        return self.executor.execute_subagent(request)
    
    def execute_parallel(self, subagent_requests: List[Dict[str, Any]]) -> List[ProtocolResponse]:
        """Execute multiple subagents in parallel"""
        requests = []
        
        for req_data in subagent_requests:
            request = self.create_request(**req_data)
            requests.append(request)
        
        return self.executor.execute_parallel_subagents(requests)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            "protocol_manager": "UserJot v1.0",
            "active_subagents": len(self.executor.subagent_registry),
            "total_requests_processed": self.request_counter,
            "executor_status": self.executor.get_performance_summary()
        }


def demo_userjot_protocols():
    """Demonstrate UserJot communication protocols"""
    print("📡 UserJot Communication Protocols Demo")
    print("=" * 50)
    
    # Initialize protocol manager
    protocol_manager = UserJotProtocolManager()
    
    # Example: Register mock subagent
    def mock_code_reviewer(objective: str, context: Dict[str, Any], constraints: Dict[str, Any], success_criteria: str):
        return {
            "result": f"Code review completed: {objective[:30]}...",
            "success": True,
            "confidence": 0.85,
            "metrics": {"lines_reviewed": 50, "issues_found": 2},
            "notes": "Review completed successfully"
        }
    
    protocol_manager.register_subagent(
        "code_reviewer", 
        mock_code_reviewer,
        {"description": "Stateless code review subagent", "version": "1.0"}
    )
    
    # Demo: Single subagent execution
    print("\n1. Single Subagent Execution:")
    response = protocol_manager.execute_single(
        subagent_name="code_reviewer",
        objective="Review authentication module for security issues",
        context={"code": "def authenticate(user, password): return True", "requirements": ["security"]},
        priority="high"
    )
    
    print(f"   Request ID: {response.request_id}")
    print(f"   Status: {response.status.value}")
    print(f"   Success: {response.success}")
    print(f"   Confidence: {response.confidence}")
    print(f"   Execution Time: {response.execution_time:.3f}s")
    
    # Demo: Parallel execution
    print("\n2. Parallel Subagent Execution:")
    parallel_requests = [
        {
            "subagent_name": "code_reviewer",
            "objective": "Security review of login function",
            "context": {"code": "def login(): pass"}
        },
        {
            "subagent_name": "code_reviewer", 
            "objective": "Performance review of data processing",
            "context": {"code": "def process_data(): pass"}
        }
    ]
    
    responses = protocol_manager.execute_parallel(parallel_requests)
    for i, response in enumerate(responses, 1):
        print(f"   Response {i}: {response.status.value} (confidence: {response.confidence})")
    
    # Show system status
    print("\n3. System Status:")
    status = protocol_manager.get_system_status()
    print(f"   Active Subagents: {status['active_subagents']}")
    print(f"   Total Requests: {status['total_requests_processed']}")
    print(f"   Protocol Version: UserJot v1.0")


if __name__ == "__main__":
    demo_userjot_protocols()
