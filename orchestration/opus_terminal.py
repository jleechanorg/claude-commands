#!/usr/bin/env python3
"""
Opus Terminal - Natural Language Interface
Interactive terminal for Opus agent with natural language commands
"""

import sys
import os
import time
import readline
import atexit
from typing import Dict, List, Optional
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from message_broker import MessageBroker
from agent_system import OpusAgent
from natural_language_parser import NaturalLanguageParser, ParsedCommand, format_response


class OpusTerminal:
    """Interactive terminal for Opus agent with natural language interface."""
    
    def __init__(self):
        self.parser = NaturalLanguageParser()
        self.broker = MessageBroker()
        self.opus_agent = None
        self.history_file = os.path.expanduser('~/.opus_terminal_history')
        self.running = False
        
        # Setup readline for command history
        try:
            readline.read_history_file(self.history_file)
            readline.set_history_length(1000)
            atexit.register(readline.write_history_file, self.history_file)
        except FileNotFoundError:
            pass
        
        # Setup tab completion
        readline.set_completer(self._completer)
        readline.parse_and_bind('tab: complete')
    
    def _completer(self, text: str, state: int) -> Optional[str]:
        """Tab completion for commands."""
        if state == 0:
            self.completion_matches = self.parser.get_suggestions(text)
        
        try:
            return self.completion_matches[state]
        except IndexError:
            return None
    
    def start(self):
        """Start the Opus terminal."""
        self.running = True
        
        try:
            # Initialize message broker
            self.broker.start()
            
            # Create Opus agent
            self.opus_agent = OpusAgent(self.broker)
            self.opus_agent.start()
            
            # Show welcome message
            self._show_welcome()
            
            # Main command loop
            while self.running:
                try:
                    user_input = input("\n🎯 Opus > ").strip()
                    
                    if not user_input:
                        continue
                    
                    if user_input.lower() in ['exit', 'quit', 'bye']:
                        break
                    
                    self._process_command(user_input)
                
                except KeyboardInterrupt:
                    print("\n\n👋 Ctrl+C pressed. Use 'exit' to quit gracefully.")
                    continue
                except EOFError:
                    print("\n\n👋 Goodbye!")
                    break
        
        finally:
            self.stop()
    
    def stop(self):
        """Stop the terminal and cleanup."""
        self.running = False
        
        if self.opus_agent:
            self.opus_agent.stop()
        
        if self.broker:
            self.broker.stop()
        
        print("\n🛑 Opus terminal stopped.")
    
    def _show_welcome(self):
        """Display welcome message."""
        print("\n" + "="*60)
        print("🎯 OPUS TERMINAL - AI Agent Coordinator")
        print("="*60)
        print("🤖 Hello! I'm Opus, your AI agent coordinator.")
        print("💬 Talk to me in natural language - no need for code!")
        print("📝 Examples:")
        print("   • Build a user authentication system")
        print("   • Create a REST API for products")
        print("   • What's the status?")
        print("   • Help me with commands")
        print("\n💡 Type 'help' for more information or 'exit' to quit.")
        print("="*60)
    
    def _process_command(self, user_input: str):
        """Process user command through natural language parser."""
        # Parse the command
        command = self.parser.parse_command(user_input)
        
        # Show parsing confidence if low
        if command.confidence < 0.5:
            print(f"🤔 I'm not entirely sure what you mean (confidence: {command.confidence:.0%})")
            print("💡 I'll try my best to help...")
        
        # Execute the command
        result = self._execute_command(command)
        
        # Format and display response
        response = format_response(command, result)
        print(f"\n{response}")
    
    def _execute_command(self, command: ParsedCommand) -> str:
        """Execute parsed command."""
        if command.action == 'delegate_task':
            return self._handle_task_delegation(command)
        
        elif command.action == 'check_status':
            return self._handle_status_check()
        
        elif command.action == 'show_help':
            return self._handle_help_request(command)
        
        elif command.action == 'spawn_agent':
            return self._handle_spawn_agent()
        
        elif command.action == 'check_progress':
            return self._handle_progress_check()
        
        elif command.action == 'stop_system':
            return self._handle_stop_system()
        
        elif command.action == 'greeting':
            return self._handle_greeting()
        
        elif command.action == 'thanks':
            return self._handle_thanks()
        
        elif command.action == 'unknown':
            return self._handle_unknown_command(command)
        
        else:
            return f"I recognize the command '{command.action}' but don't know how to handle it yet."
    
    def _handle_task_delegation(self, command: ParsedCommand) -> str:
        """Handle task delegation to Sonnet agents."""
        if not command.target:
            return "I need more details about what you want me to build or create."
        
        # Check if we have Sonnet agents available
        active_agents = self.broker.get_active_agents()
        sonnet_agents = [agent for agent in active_agents if agent.startswith("sonnet")]
        
        if not sonnet_agents:
            return ("I don't have any Sonnet agents available right now. "
                   "You might need to start one first with: './start_system.sh start'")
        
        # Delegate the task
        try:
            self.opus_agent.delegate_task(command.target)
            
            priority = command.parameters.get('priority', 'medium')
            deadline = command.parameters.get('deadline', 'not specified')
            
            result = f"✅ Task delegated to {sonnet_agents[0]}\n"
            result += f"📋 Task: {command.target}\n"
            result += f"⚡ Priority: {priority}\n"
            result += f"⏰ Deadline: {deadline}\n"
            result += f"👥 Available agents: {len(sonnet_agents)}"
            
            return result
            
        except Exception as e:
            return f"❌ Error delegating task: {str(e)}"
    
    def _handle_status_check(self) -> str:
        """Handle system status check."""
        try:
            # Check Redis connection
            redis_status = "✅ Connected" if self.broker.redis_client.ping() else "❌ Disconnected"
            
            # Get active agents
            active_agents = self.broker.get_active_agents()
            
            # Count agents by type
            opus_count = len([a for a in active_agents if a.startswith("opus")])
            sonnet_count = len([a for a in active_agents if a.startswith("sonnet")])
            sub_count = len([a for a in active_agents if a.startswith("sub")])
            
            result = f"🔄 Redis: {redis_status}\n"
            result += f"🎯 Opus agents: {opus_count}\n"
            result += f"🤖 Sonnet agents: {sonnet_count}\n"
            result += f"🔧 Sub-agents: {sub_count}\n"
            result += f"📊 Total active agents: {len(active_agents)}"
            
            if active_agents:
                result += f"\n\n👥 Active agents:\n"
                for agent in active_agents[:5]:  # Show first 5
                    result += f"   • {agent}\n"
                if len(active_agents) > 5:
                    result += f"   • ... and {len(active_agents) - 5} more"
            
            return result
            
        except Exception as e:
            return f"❌ Error checking status: {str(e)}"
    
    def _handle_help_request(self, command: ParsedCommand) -> str:
        """Handle help requests."""
        if command.target and 'command' in command.target:
            return self._get_command_help()
        
        help_text = """
🎯 **Task Management:**
   • "Build a user authentication system"
   • "Create a REST API for products"
   • "Implement a database schema"
   • "Develop a web interface"

📊 **System Status:**
   • "What's the status?"
   • "Show me the agents"
   • "How's the progress?"
   • "Check system status"

🤖 **Agent Management:**
   • "Spawn a new agent"
   • "Add more agents"
   • "Need more help"

💬 **Natural Language:**
   • Just talk to me normally!
   • I understand priority: "Build this urgently"
   • I understand deadlines: "Create this by tomorrow"
   • I understand questions: "How do I...?"

🔧 **System Commands:**
   • "help" - Show this help
   • "exit" - Quit the terminal
   • "status" - Check system status
        """
        return help_text
    
    def _get_command_help(self) -> str:
        """Get help about specific commands."""
        return """
🎯 **Available Commands:**

**Task Commands:**
   • build, create, make, develop, implement
   • "Build a [description]"
   • "Create a [description]"
   • "I need you to [description]"

**Status Commands:**
   • status, check, show
   • "What's the status?"
   • "Show system status"
   • "How are things going?"

**Agent Commands:**
   • spawn, start, add
   • "Spawn a new agent"
   • "Add more agents"
   • "Need more help"

**Priority Keywords:**
   • High: urgent, asap, immediately, critical
   • Medium: soon, when possible
   • Low: later, whenever, no rush
        """
    
    def _handle_spawn_agent(self) -> str:
        """Handle spawning new agents."""
        return ("🤖 To spawn new agents, use the system script:\n"
               "   ./start_system.sh spawn sonnet\n\n"
               "💡 This will create a new Sonnet agent in a separate tmux session.")
    
    def _handle_progress_check(self) -> str:
        """Handle progress check requests."""
        # This would check message queues for task progress
        return ("📊 Progress checking is not fully implemented yet.\n"
               "💡 For now, check the individual agent tmux sessions to see their progress.")
    
    def _handle_stop_system(self) -> str:
        """Handle system stop requests."""
        return ("🛑 To stop the system, use:\n"
               "   ./start_system.sh stop\n\n"
               "⚠️  This will stop all agents and clear Redis data.")
    
    def _handle_greeting(self) -> str:
        """Handle greeting messages."""
        return ("Hello! I'm ready to help you coordinate AI agents and manage development tasks. "
               "What would you like me to work on today?")
    
    def _handle_thanks(self) -> str:
        """Handle thank you messages."""
        return ("You're welcome! I'm here whenever you need help with development tasks. "
               "What's the next thing you'd like me to work on?")
    
    def _handle_unknown_command(self, command: ParsedCommand) -> str:
        """Handle unknown commands."""
        suggestions = self.parser.get_suggestions(command.raw_command)
        
        result = "I'm not sure how to handle that command.\n\n"
        
        if suggestions:
            result += "💡 Here are some suggestions:\n"
            for i, suggestion in enumerate(suggestions[:5], 1):
                result += f"   {i}. {suggestion}\n"
        
        result += "\n💬 Try asking me to 'build', 'create', or 'implement' something!"
        return result


def main():
    """Main entry point for Opus terminal."""
    terminal = OpusTerminal()
    
    try:
        terminal.start()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        terminal.stop()


if __name__ == "__main__":
    main()