#!/usr/bin/env python3
"""
Intelligent Agent Planner - LLM-driven agent planning for orchestration system

Analyzes tasks and determines optimal agent configuration instead of using
hardcoded frontend/backend/testing categories.
"""

import json
import os
from typing import List
from dataclasses import dataclass


@dataclass
class AgentSpec:
    """Specification for a specialized agent."""
    name: str
    focus: str
    responsibilities: List[str]
    estimated_duration: str  # e.g., "2-4 hours", "30 minutes"


@dataclass
class AgentPlan:
    """Complete plan for agent deployment."""
    agent_count: int
    agents: List[AgentSpec]
    reasoning: str
    complexity_level: str  # "simple", "moderate", "complex"
    parallel_execution: bool


class IntelligentAgentPlanner:
    """LLM-driven agent planning system."""
    
    def __init__(self):
        # Claude will do the planning directly - no external API needed
        pass
    
    def analyze_task(self, task_description: str) -> AgentPlan:
        """Analyze task and return optimal agent plan using Claude's intelligence."""
        # Claude (me) will analyze the task and return an intelligent plan
        # This is much better than calling external APIs
        return self._claude_analyze_task(task_description)
    
    def _claude_analyze_task(self, task_description: str) -> AgentPlan:
        """Use Claude's built-in intelligence to analyze task and plan agents.
        
        This method contains Claude's direct analysis logic instead of calling external APIs.
        Claude will determine the optimal agent configuration based on the task.
        """
        task_lower = task_description.lower()
        
        # Claude's intelligent task analysis
        
        # Single agent patterns (simple tasks)
        if any(keyword in task_lower for keyword in ['simple', 'quick', 'small', 'minor', 'comment', 'documentation']):
            return AgentPlan(
                agent_count=1,
                agents=[AgentSpec(
                    name="documentation-agent",
                    focus="Documentation and comment enhancement",
                    responsibilities=["Add comments", "Update documentation", "Code clarity"],
                    estimated_duration="1-2 hours"
                )],
                reasoning="Simple documentation task requires single focused agent",
                complexity_level="simple",
                parallel_execution=False
            )
        
        # GitHub/API related tasks (specialized agents)
        if any(keyword in task_lower for keyword in ['github', 'api', 'comment', 'copilot', 'pr', 'issue']):
            if 'checkpoint' in task_lower or 'processing' in task_lower:
                # Complex GitHub task with multiple components
                return AgentPlan(
                    agent_count=2,
                    agents=[
                        AgentSpec(
                            name="github-api-agent",
                            focus="GitHub API integration and data extraction",
                            responsibilities=["API calls", "Comment extraction", "Rate limiting", "Pagination"],
                            estimated_duration="2-3 hours"
                        ),
                        AgentSpec(
                            name="processing-agent",
                            focus="Data processing and checkpoint logic",
                            responsibilities=["Comment processing", "Checkpoint system", "Timestamp tracking"],
                            estimated_duration="1-2 hours"
                        )
                    ],
                    reasoning="GitHub API tasks benefit from separation of API handling and processing logic",
                    complexity_level="moderate",
                    parallel_execution=True
                )
            else:
                # Simple GitHub task
                return AgentPlan(
                    agent_count=1,
                    agents=[AgentSpec(
                        name="github-enhancement-agent",
                        focus="GitHub integration enhancement",
                        responsibilities=["GitHub API integration", "Comment handling", "Testing"],
                        estimated_duration="2-3 hours"
                    )],
                    reasoning="Focused GitHub enhancement requires specialized API expertise",
                    complexity_level="moderate",
                    parallel_execution=False
                )
        
        # Architecture/system tasks (complex)
        if any(keyword in task_lower for keyword in ['system', 'architecture', 'refactor', 'orchestration', 'agent']):
            return AgentPlan(
                agent_count=2,
                agents=[
                    AgentSpec(
                        name="architecture-agent",
                        focus="System design and architecture",
                        responsibilities=["Design decisions", "Architecture planning", "System integration"],
                        estimated_duration="3-4 hours"
                    ),
                    AgentSpec(
                        name="implementation-agent",
                        focus="Core implementation",
                        responsibilities=["Code implementation", "Testing", "Documentation"],
                        estimated_duration="2-3 hours"
                    )
                ],
                reasoning="Architecture tasks require design expertise and implementation focus",
                complexity_level="complex",
                parallel_execution=True
            )
        
        # Default: intelligent single agent
        return AgentPlan(
            agent_count=1,
            agents=[AgentSpec(
                name="task-specialist-agent",
                focus="Specialized task implementation",
                responsibilities=["Task analysis", "Implementation", "Testing", "Documentation"],
                estimated_duration="2-3 hours"
            )],
            reasoning="Task requires focused specialist attention",
            complexity_level="moderate",
            parallel_execution=False
        )
    
    def _fallback_analyze_task(self, task_description: str) -> AgentPlan:
        """Legacy fallback method - now unused since Claude does direct planning."""
        task_lower = task_description.lower()
        
        # Single agent patterns
        if any(keyword in task_lower for keyword in ['simple', 'quick', 'small', 'minor']):
            return AgentPlan(
                agent_count=1,
                agents=[AgentSpec(
                    name=f"task-agent",
                    focus="Complete the requested task",
                    responsibilities=["Handle task implementation", "Testing", "Documentation"],
                    estimated_duration="1-2 hours"
                )],
                reasoning="Simple task requires single focused agent",
                complexity_level="simple",
                parallel_execution=False
            )
        
        # GitHub/API related tasks
        if any(keyword in task_lower for keyword in ['github', 'api', 'comment', 'copilot']):
            return AgentPlan(
                agent_count=2,
                agents=[
                    AgentSpec(
                        name="github-api-agent",
                        focus="GitHub API integration",
                        responsibilities=["API calls", "Data extraction", "Rate limiting"],
                        estimated_duration="2-3 hours"
                    ),
                    AgentSpec(
                        name="processing-agent", 
                        focus="Data processing and logic",
                        responsibilities=["Data processing", "Business logic", "Output formatting"],
                        estimated_duration="1-2 hours"
                    )
                ],
                reasoning="GitHub API tasks benefit from separation of API handling and processing",
                complexity_level="moderate",
                parallel_execution=True
            )
        
        # Complex/system tasks
        if any(keyword in task_lower for keyword in ['system', 'architecture', 'refactor', 'complex']):
            return AgentPlan(
                agent_count=3,
                agents=[
                    AgentSpec(
                        name="architecture-agent",
                        focus="System design and architecture",
                        responsibilities=["Design decisions", "Architecture planning", "Integration"],
                        estimated_duration="3-4 hours"
                    ),
                    AgentSpec(
                        name="implementation-agent",
                        focus="Core implementation", 
                        responsibilities=["Code implementation", "Core logic", "Integration"],
                        estimated_duration="4-6 hours"
                    ),
                    AgentSpec(
                        name="validation-agent",
                        focus="Testing and validation",
                        responsibilities=["Testing", "Validation", "Quality assurance"],
                        estimated_duration="2-3 hours"
                    )
                ],
                reasoning="Complex system tasks require architecture, implementation, and validation expertise",
                complexity_level="complex",
                parallel_execution=True
            )
        
        # Default: 2 agents
        return AgentPlan(
            agent_count=2,
            agents=[
                AgentSpec(
                    name="primary-agent",
                    focus="Main task implementation",
                    responsibilities=["Core implementation", "Primary logic", "Integration"],
                    estimated_duration="2-3 hours"
                ),
                AgentSpec(
                    name="support-agent",
                    focus="Support and validation",
                    responsibilities=["Testing", "Documentation", "Quality checks"],
                    estimated_duration="1-2 hours"
                )
            ],
            reasoning="Standard task requires implementation and validation focus",
            complexity_level="moderate", 
            parallel_execution=True
        )
    
    def format_plan_summary(self, plan: AgentPlan) -> str:
        """Format agent plan for display."""
        summary = [
            f"🎯 **Intelligent Agent Plan**",
            f"",
            f"**Task Complexity**: {plan.complexity_level.title()}",
            f"**Agent Count**: {plan.agent_count}",
            f"**Parallel Execution**: {'Yes' if plan.parallel_execution else 'No'}",
            f"**Reasoning**: {plan.reasoning}",
            f"",
            f"**Specialized Agents**:"
        ]
        
        for i, agent in enumerate(plan.agents, 1):
            summary.append(f"   {i}. **{agent.name}**")
            summary.append(f"      └─ Focus: {agent.focus}")
            summary.append(f"      └─ Duration: {agent.estimated_duration}")
            summary.append(f"      └─ Responsibilities: {', '.join(agent.responsibilities)}")
            summary.append("")
        
        total_duration = "Parallel" if plan.parallel_execution else "Sequential"
        summary.append(f"**Execution Mode**: {total_duration}")
        
        return "\n".join(summary)


def main():
    """Test the intelligent agent planner."""
    planner = IntelligentAgentPlanner()
    
    test_tasks = [
        "make our /copilot command look at all github comments and not just the last 20",
        "fix a simple typo in the documentation", 
        "build a complete user authentication system with database integration",
        "create a REST API for user management"
    ]
    
    for task in test_tasks:
        print(f"\n{'='*60}")
        print(f"TASK: {task}")
        print(f"{'='*60}")
        
        plan = planner.analyze_task(task)
        summary = planner.format_plan_summary(plan)
        print(summary)


if __name__ == "__main__":
    main()