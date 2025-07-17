#!/usr/bin/env python3
"""
Mock Memory MCP Reader for Testing
Provides the same interface as real Memory MCP functions but reads from local JSON file
"""

import json
import os
from typing import Dict, List, Optional, Any
from collections import defaultdict


class MockMemoryMCPReader:
    """Mock reader that implements Memory MCP interface using local JSON file"""
    
    def __init__(self, memory_file: str = None):
        """Initialize with path to memory.json file"""
        if memory_file is None:
            # Default to memory.json in same directory as this script
            memory_file = os.path.join(os.path.dirname(__file__), 'memory.json')
        
        self.memory_file = memory_file
        self._cache = None
        self._cache_mtime = None
    
    def _load_memory_data(self) -> Dict[str, Any]:
        """Load and parse memory data from JSON file with caching"""
        if not os.path.exists(self.memory_file):
            return {"entities": [], "relations": []}
        
        # Check if cache is still valid
        current_mtime = os.path.getmtime(self.memory_file)
        if self._cache is not None and self._cache_mtime == current_mtime:
            return self._cache
        
        # Parse the JSONL format (one JSON object per line)
        entities = []
        relations = []
        
        with open(self.memory_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    obj = json.loads(line)
                    if obj.get("type") == "entity":
                        entities.append({
                            "name": obj.get("name", ""),
                            "entityType": obj.get("entityType", ""),
                            "observations": obj.get("observations", [])
                        })
                    elif obj.get("type") == "relation":
                        relations.append({
                            "from": obj.get("from", ""),
                            "to": obj.get("to", ""),
                            "relationType": obj.get("relationType", "")
                        })
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse line: {line[:100]}... Error: {e}")
                    continue
        
        # Cache the result
        self._cache = {"entities": entities, "relations": relations}
        self._cache_mtime = current_mtime
        
        return self._cache
    
    def read_graph(self) -> Dict[str, Any]:
        """Get entire knowledge graph - equivalent to mcp__memory-server__read_graph()"""
        return self._load_memory_data()
    
    def search_nodes(self, query: str) -> List[Dict[str, Any]]:
        """Search for nodes by content - equivalent to mcp__memory-server__search_nodes(query)"""
        data = self._load_memory_data()
        results = []
        
        query_lower = query.lower()
        
        for entity in data["entities"]:
            # Search in entity name
            if query_lower in entity["name"].lower():
                results.append(entity)
                continue
            
            # Search in entity type
            if query_lower in entity["entityType"].lower():
                results.append(entity)
                continue
            
            # Search in observations
            for obs in entity["observations"]:
                if query_lower in obs.lower():
                    results.append(entity)
                    break
        
        return results
    
    def open_nodes(self, names: List[str]) -> List[Dict[str, Any]]:
        """Get specific entities by name - equivalent to mcp__memory-server__open_nodes(names)"""
        data = self._load_memory_data()
        results = []
        
        name_set = set(names)
        
        for entity in data["entities"]:
            if entity["name"] in name_set:
                results.append(entity)
        
        return results


class ComplianceMemoryReader:
    """Read past violations from Memory MCP"""
    
    def __init__(self, reader: MockMemoryMCPReader = None):
        self.reader = reader or MockMemoryMCPReader()
    
    def get_violation_history(self, violation_type: str = None) -> List[Dict[str, Any]]:
        """Retrieve past compliance violations"""
        # Search for entities with compliance-related types
        results = self.reader.search_nodes("compliance")
        
        # Filter by specific violation type if provided
        if violation_type:
            filtered = []
            for result in results:
                for obs in result["observations"]:
                    if violation_type.lower() in obs.lower():
                        filtered.append(result)
                        break
            return filtered
        
        return results
    
    def get_violation_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze patterns in violations"""
        # Read full graph
        graph = self.reader.read_graph()
        
        # Extract violation entities
        violations = [e for e in graph["entities"] 
                     if "compliance" in e["entityType"].lower() or 
                        "violation" in e["entityType"].lower()]
        
        # Group by type and frequency
        patterns = defaultdict(list)
        for v in violations:
            # Try to extract violation type from name or observations
            v_type = self._extract_violation_type(v)
            patterns[v_type].append(v)
        
        return dict(patterns)
    
    def _extract_violation_type(self, violation: Dict[str, Any]) -> str:
        """Extract violation type from entity"""
        name = violation["name"].lower()
        
        if "header" in name:
            return "MANDATORY_HEADER"
        elif "import" in name:
            return "NO_INLINE_IMPORTS"
        elif "test" in name:
            return "TEST_EXECUTION"
        elif "push" in name:
            return "PUSH_VERIFICATION"
        else:
            return "OTHER"
    
    def should_remind_about_rule(self, rule_type: str) -> bool:
        """Check if user should be reminded about a rule"""
        recent_violations = self.get_violation_history(rule_type)
        
        # Simple threshold check (in real implementation would consider timestamps)
        threshold = 3
        return len(recent_violations) >= threshold


class LearningMemoryReader:
    """Read learnings from Memory MCP"""
    
    def __init__(self, reader: MockMemoryMCPReader = None):
        self.reader = reader or MockMemoryMCPReader()
    
    def get_learnings_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all learnings in a category"""
        # Search for learning entities
        all_learnings = self.reader.search_nodes("learning")
        
        # Filter by category
        filtered = []
        for learning in all_learnings:
            for obs in learning["observations"]:
                if category.lower() in obs.lower():
                    filtered.append(learning)
                    break
        
        return filtered
    
    def get_related_learnings(self, context: str) -> List[Dict[str, Any]]:
        """Find learnings related to current context"""
        # Search for relevant entities
        results = self.reader.search_nodes(context)
        
        # Filter to learning entities
        learnings = [r for r in results if "learning" in r["entityType"].lower()]
        
        return learnings
    
    def get_learning_graph(self) -> Dict[str, Any]:
        """Get full learning knowledge graph with relations"""
        graph = self.reader.read_graph()
        
        # Extract learning entities and their relations
        learning_entities = [e for e in graph["entities"] 
                           if "learning" in e["entityType"].lower()]
        
        # Find relations involving learning entities
        learning_names = set(e["name"] for e in learning_entities)
        learning_relations = []
        
        for relation in graph["relations"]:
            if (relation["from"] in learning_names or 
                relation["to"] in learning_names):
                learning_relations.append(relation)
        
        return {
            "entities": learning_entities,
            "relations": learning_relations
        }


class PreResponseChecker:
    """Check Memory MCP before responding"""
    
    def __init__(self, reader: MockMemoryMCPReader = None):
        self.reader = reader or MockMemoryMCPReader()
        self.compliance_reader = ComplianceMemoryReader(reader)
        self.learning_reader = LearningMemoryReader(reader)
    
    def check_before_response(self, response_context: Dict[str, Any]) -> List[str]:
        """Run checks before generating response"""
        reminders = []
        
        # Check for repeated violations
        if self.compliance_reader.should_remind_about_rule("MANDATORY_HEADER"):
            reminders.append("⚠️ Remember: Include branch header at end of response")
        
        # Check for relevant learnings
        topic = response_context.get("topic", "")
        if topic:
            learnings = self.learning_reader.get_related_learnings(topic)
            if learnings:
                learning_summary = self._summarize_learnings(learnings)
                reminders.append(f"📚 Related learnings: {learning_summary}")
        
        return reminders
    
    def _summarize_learnings(self, learnings: List[Dict[str, Any]]) -> str:
        """Summarize learnings for reminder"""
        if not learnings:
            return "None"
        
        summaries = []
        for learning in learnings[:3]:  # Limit to top 3
            name = learning["name"]
            if learning["observations"]:
                first_obs = learning["observations"][0][:100]  # First 100 chars
                summaries.append(f"{name}: {first_obs}")
        
        return "; ".join(summaries)


def main():
    """Test the mock reader functionality"""
    print("Testing Mock Memory MCP Reader...")
    
    reader = MockMemoryMCPReader()
    
    # Test read_graph
    print("\n1. Testing read_graph():")
    graph = reader.read_graph()
    print(f"   Found {len(graph['entities'])} entities, {len(graph['relations'])} relations")
    
    # Test search_nodes
    print("\n2. Testing search_nodes('compliance'):")
    results = reader.search_nodes("compliance")
    print(f"   Found {len(results)} compliance-related entities")
    for result in results[:3]:
        print(f"   - {result['name']} ({result['entityType']})")
    
    # Test open_nodes
    print("\n3. Testing open_nodes(['Header Compliance Violation']):")
    results = reader.open_nodes(['Header Compliance Violation'])
    print(f"   Found {len(results)} specific entities")
    for result in results:
        print(f"   - {result['name']}: {len(result['observations'])} observations")
    
    # Test compliance reader
    print("\n4. Testing ComplianceMemoryReader:")
    compliance_reader = ComplianceMemoryReader(reader)
    violations = compliance_reader.get_violation_history("header")
    print(f"   Found {len(violations)} header violations")
    
    patterns = compliance_reader.get_violation_patterns()
    print(f"   Violation patterns: {list(patterns.keys())}")
    
    # Test learning reader
    print("\n5. Testing LearningMemoryReader:")
    learning_reader = LearningMemoryReader(reader)
    learnings = learning_reader.get_related_learnings("branch")
    print(f"   Found {len(learnings)} branch-related learnings")
    
    # Test pre-response checker
    print("\n6. Testing PreResponseChecker:")
    checker = PreResponseChecker(reader)
    reminders = checker.check_before_response({"topic": "header"})
    print(f"   Generated {len(reminders)} reminders:")
    for reminder in reminders:
        print(f"   - {reminder}")
    
    print("\nMock Memory MCP Reader test complete!")


if __name__ == "__main__":
    main()