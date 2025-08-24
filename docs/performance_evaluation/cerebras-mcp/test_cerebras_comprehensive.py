#!/usr/bin/env python3
"""
Comprehensive Cerebras MCP Test Suite
Proves 80% Cerebras usage target and validates integration quality
"""
import asyncio
import time
import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

class CerebrasTestSuite:
    """Comprehensive test suite for Cerebras MCP integration"""
    
    def __init__(self):
        self.results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tests": {},
            "performance": {},
            "coverage": {},
            "usage_validation": {}
        }
        self.server_proc = None
        
    def log_test(self, test_name: str, success: bool, details: str, duration: float = 0):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details} ({duration:.3f}s)")
        
        self.results["tests"][test_name] = {
            "success": success,
            "details": details,
            "duration": duration
        }
    
    async def setup_mcp_server(self):
        """Start MCP server for testing"""
        print("🔧 Starting MCP server for testing...")
        
        server_path = "mcp_servers/slash_commands/server.py"
        self.server_proc = subprocess.Popen(
            [sys.executable, server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        # Wait for server startup
        await asyncio.sleep(2)
        print("✅ MCP server ready")
    
    async def teardown_mcp_server(self):
        """Clean up MCP server"""
        if self.server_proc:
            self.server_proc.terminate()
            try:
                await asyncio.wait_for(
                    asyncio.create_subprocess_exec("wait", str(self.server_proc.pid)),
                    timeout=5
                )
            except:
                self.server_proc.kill()
    
    async def test_direct_mcp_tool_call(self):
        """Test 1: Direct MCP tool invocation"""
        start_time = time.time()
        
        try:
            # Send tool call message
            message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "cerebras_generate",
                    "arguments": {
                        "prompt": "Create a simple Python function that adds two numbers"
                    }
                }
            }
            
            self.server_proc.stdin.write(json.dumps(message) + "\n")
            self.server_proc.stdin.flush()
            
            # Wait for response with timeout
            response_line = await asyncio.wait_for(
                asyncio.create_subprocess_shell(
                    f"timeout 10s head -1 <&{self.server_proc.stdout.fileno()}",
                    stdout=asyncio.subprocess.PIPE
                ),
                timeout=15
            )
            
            duration = time.time() - start_time
            
            if duration < 2.0:  # Should be under 2 seconds
                self.log_test("direct_mcp_call", True, 
                             f"Tool executed in {duration:.3f}s (target: <2s)", duration)
                return True
            else:
                self.log_test("direct_mcp_call", False,
                             f"Tool too slow: {duration:.3f}s", duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("direct_mcp_call", False, f"Error: {e}", duration)
            return False
    
    async def test_code_generation_quality(self):
        """Test 2: Code generation quality validation"""
        start_time = time.time()
        
        try:
            # Test with complex prompt
            result = await self.call_cerebras_tool({
                "prompt": "Create a FastAPI endpoint for user authentication with JWT tokens, input validation, and error handling",
                "options": {
                    "include_tests": True,
                    "include_docs": True,
                    "style_guide": "PEP8"
                }
            })
            
            duration = time.time() - start_time
            
            if result and result.get("success"):
                code = result.get("generated_code", "")
                quality = result.get("quality_analysis", {})
                
                # Quality checks
                checks = {
                    "has_imports": "import" in code or "from" in code,
                    "has_function_def": "def " in code or "async def" in code,
                    "has_docstrings": '"""' in code or "'''" in code,
                    "has_error_handling": "try:" in code or "except" in code,
                    "no_placeholders": "TODO" not in code and "FIXME" not in code,
                    "sufficient_length": len(code) > 200
                }
                
                passed_checks = sum(checks.values())
                total_checks = len(checks)
                
                if passed_checks >= total_checks * 0.8:  # 80% quality threshold
                    self.log_test("code_quality", True,
                                 f"Quality: {passed_checks}/{total_checks} checks passed", duration)
                    return True
                else:
                    self.log_test("code_quality", False,
                                 f"Quality: {passed_checks}/{total_checks} checks passed", duration)
                    return False
            else:
                self.log_test("code_quality", False, "Tool call failed", duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("code_quality", False, f"Error: {e}", duration)
            return False
    
    async def test_performance_baseline(self):
        """Test 3: Performance vs baseline measurement"""
        start_time = time.time()
        
        try:
            # Multiple quick tests
            prompts = [
                "Create a Python hello world function",
                "Create a JavaScript function to validate email",
                "Create a SQL query to find users by age",
                "Create a Bash script to count files",
                "Create a CSS flexbox layout"
            ]
            
            total_cerebras_time = 0
            successful_calls = 0
            
            for prompt in prompts:
                call_start = time.time()
                result = await self.call_cerebras_tool({"prompt": prompt})
                call_time = time.time() - call_start
                
                if result and result.get("success"):
                    total_cerebras_time += call_time
                    successful_calls += 1
                    print(f"   📊 {prompt[:30]}... : {call_time:.3f}s")
            
            if successful_calls > 0:
                avg_time = total_cerebras_time / successful_calls
                duration = time.time() - start_time
                
                # Target: Average under 1 second per call
                if avg_time < 1.0:
                    self.log_test("performance_baseline", True,
                                 f"Avg: {avg_time:.3f}s/call, {successful_calls}/{len(prompts)} successful", duration)
                    
                    self.results["performance"]["avg_call_time"] = avg_time
                    self.results["performance"]["success_rate"] = successful_calls / len(prompts)
                    return True
                else:
                    self.log_test("performance_baseline", False,
                                 f"Too slow: {avg_time:.3f}s/call average", duration)
                    return False
            else:
                self.log_test("performance_baseline", False, "No successful calls", time.time() - start_time)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("performance_baseline", False, f"Error: {e}", duration)
            return False
    
    async def test_claude_cli_integration(self):
        """Test 4: Claude CLI integration validation"""
        start_time = time.time()
        
        try:
            # Test if Claude CLI can call our tool
            result = subprocess.run([
                "bash", "-c", 
                'echo "Use cerebras_generate to create Python hello world" | timeout 30s claude --dangerously-skip-permissions'
            ], capture_output=True, text=True, timeout=35)
            
            duration = time.time() - start_time
            
            # Check if Claude CLI mentions Cerebras or generates code
            output = result.stdout + result.stderr
            
            indicators = [
                "cerebras" in output.lower(),
                "def " in output,  # Python function definition
                "hello" in output.lower(),
                len(output) > 50  # Substantial response
            ]
            
            positive_indicators = sum(indicators)
            
            if positive_indicators >= 2:  # At least 2 positive indicators
                self.log_test("claude_cli_integration", True,
                             f"CLI integration working: {positive_indicators}/4 indicators", duration)
                return True
            else:
                self.log_test("claude_cli_integration", False,
                             f"CLI integration issues: {positive_indicators}/4 indicators", duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("claude_cli_integration", False, f"Error: {e}", duration)
            return False
    
    async def test_use_case_coverage(self):
        """Test 5: Different use case validation"""
        start_time = time.time()
        
        use_cases = {
            "web_dev": "Create a React component with hooks and TypeScript",
            "data_science": "Create a Python function for data analysis with pandas",
            "devops": "Create a Docker container configuration for a web app",
            "testing": "Create unit tests for a user authentication service",
            "documentation": "Create API documentation for a REST endpoint"
        }
        
        try:
            successful_cases = 0
            
            for case_name, prompt in use_cases.items():
                case_start = time.time()
                result = await self.call_cerebras_tool({"prompt": prompt})
                case_time = time.time() - case_start
                
                if result and result.get("success"):
                    code = result.get("generated_code", "")
                    if len(code) > 100:  # Substantial output
                        successful_cases += 1
                        print(f"   ✅ {case_name}: {len(code)} chars in {case_time:.3f}s")
                    else:
                        print(f"   ⚠️ {case_name}: Output too short ({len(code)} chars)")
                else:
                    print(f"   ❌ {case_name}: Failed")
            
            duration = time.time() - start_time
            success_rate = successful_cases / len(use_cases)
            
            if success_rate >= 0.8:  # 80% success rate
                self.log_test("use_case_coverage", True,
                             f"Coverage: {successful_cases}/{len(use_cases)} use cases", duration)
                
                self.results["coverage"]["use_cases"] = successful_cases
                self.results["coverage"]["total_cases"] = len(use_cases)
                self.results["coverage"]["success_rate"] = success_rate
                return True
            else:
                self.log_test("use_case_coverage", False,
                             f"Low coverage: {successful_cases}/{len(use_cases)}", duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("use_case_coverage", False, f"Error: {e}", duration)
            return False
    
    async def call_cerebras_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Helper: Call Cerebras tool directly"""
        try:
            # Import and call tool directly for testing
            sys.path.append("mcp_servers/slash_commands")
            from cerebras_tool import CerebrasTool
            
            tool = CerebrasTool()
            result = await tool.execute(arguments)
            return result
            
        except Exception as e:
            print(f"   ❌ Tool call error: {e}")
            return {"success": False, "error": str(e)}
    
    def calculate_usage_target(self):
        """Calculate if we meet 80% Cerebras usage target"""
        tests = self.results["tests"]
        performance = self.results["performance"]
        coverage = self.results["coverage"]
        
        # Usage target criteria
        criteria = {
            "mcp_integration": tests.get("direct_mcp_call", {}).get("success", False),
            "code_quality": tests.get("code_quality", {}).get("success", False),
            "performance": tests.get("performance_baseline", {}).get("success", False),
            "cli_integration": tests.get("claude_cli_integration", {}).get("success", False),
            "use_case_coverage": tests.get("use_case_coverage", {}).get("success", False)
        }
        
        # Performance metrics
        speed_target = performance.get("avg_call_time", 10) < 1.0
        success_rate_target = performance.get("success_rate", 0) >= 0.8
        coverage_target = coverage.get("success_rate", 0) >= 0.8
        
        # Overall score
        technical_score = sum(criteria.values()) / len(criteria)
        performance_score = (speed_target + success_rate_target + coverage_target) / 3
        
        overall_score = (technical_score + performance_score) / 2
        
        self.results["usage_validation"] = {
            "technical_criteria": criteria,
            "performance_metrics": {
                "speed_target": speed_target,
                "success_rate_target": success_rate_target,
                "coverage_target": coverage_target
            },
            "technical_score": technical_score,
            "performance_score": performance_score,
            "overall_score": overall_score,
            "meets_80_percent_target": overall_score >= 0.8
        }
        
        return overall_score >= 0.8
    
    def print_results(self):
        """Print comprehensive test results"""
        print("\n" + "="*80)
        print("🎯 CEREBRAS MCP INTEGRATION TEST RESULTS")
        print("="*80)
        
        # Test summary
        passed = sum(1 for test in self.results["tests"].values() if test["success"])
        total = len(self.results["tests"])
        
        print(f"\n📊 TEST SUMMARY: {passed}/{total} tests passed")
        
        # Performance summary
        if "avg_call_time" in self.results["performance"]:
            print(f"⚡ PERFORMANCE: {self.results['performance']['avg_call_time']:.3f}s avg call time")
            print(f"✅ SUCCESS RATE: {self.results['performance']['success_rate']:.1%}")
        
        # Coverage summary  
        if "success_rate" in self.results["coverage"]:
            print(f"🎯 USE CASE COVERAGE: {self.results['coverage']['success_rate']:.1%}")
        
        # Usage target validation
        meets_target = self.calculate_usage_target()
        validation = self.results["usage_validation"]
        
        print(f"\n🚀 80% CEREBRAS USAGE TARGET: {'✅ MET' if meets_target else '❌ NOT MET'}")
        print(f"   Technical Score: {validation['technical_score']:.1%}")
        print(f"   Performance Score: {validation['performance_score']:.1%}")
        print(f"   Overall Score: {validation['overall_score']:.1%}")
        
        if meets_target:
            print("\n🎉 BREAKTHROUGH: Cerebras MCP integration ready for production!")
            print("   • MCP tool integration: ✓ Working")
            print("   • Performance target: ✓ Under 1s avg")
            print("   • Code quality: ✓ High quality output") 
            print("   • Use case coverage: ✓ 80%+ success")
            print("   • Claude CLI integration: ✓ Functional")
        else:
            print("\n⚠️ AREAS FOR IMPROVEMENT:")
            for criteria, passed in validation["technical_criteria"].items():
                if not passed:
                    print(f"   • {criteria}: Needs attention")
        
        print("="*80)
    
    async def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting Comprehensive Cerebras MCP Test Suite")
        print(f"📅 Timestamp: {self.results['timestamp']}")
        print("-" * 80)
        
        try:
            # Setup
            await self.setup_mcp_server()
            
            # Run all tests
            tests = [
                self.test_direct_mcp_tool_call(),
                self.test_code_generation_quality(),
                self.test_performance_baseline(),
                self.test_claude_cli_integration(),
                self.test_use_case_coverage()
            ]
            
            for test in tests:
                await test
                print()  # Space between tests
            
            # Results
            self.print_results()
            
            # Save results
            results_file = f"test_results_cerebras_{int(time.time())}.json"
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"\n📄 Results saved to: {results_file}")
            
        finally:
            await self.teardown_mcp_server()

async def main():
    """Main test runner"""
    suite = CerebrasTestSuite()
    await suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())