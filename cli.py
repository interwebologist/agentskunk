#!/usr/bin/env python3
"""
Simple CLI Framework - Standalone Example
For use in your own projects (skunkagent)

This is a stripped-down version of the Hermes CLI that captures the core pattern:
1. Command registry for slash commands
2. Dynamic method creation for auto-dispatch
3. Session management with SQLite backend
4. Simple agent integration

Copy this to your project and customize!
"""

import sys
import cmd
import sqlite3
import uuid
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any


# ============================================================================
# Session Database (simplified hermes_state.py)
# ============================================================================

read state.py to figure out how to interface with the code here. this is just a roughe idea. 
get the idea working

# ============================================================================
# Command Registry
# ============================================================================

class Command:
    """A single CLI command"""
    def __init__(self, name: str, description: str, func: Callable,
                 aliases: List[str] = None, args_hint: str = ""):
        self.name = name
        self.description = description
        self.func = func
        self.aliases = aliases or []
        self.args_hint = args_hint


class CommandRegistry:
    """Central registry for all commands"""
    
    def __init__(self):
        self.commands: Dict[str, Command] = {}
        self._lookup: Dict[str, Command] = {}
    
    def register(self, command: Command):
        """Register a command"""
        self.commands[command.name] = command
        self._lookup[command.name.lower()] = command
        for alias in command.aliases:
            self._lookup[alias.lower()] = command
    
    def resolve(self, name: str) -> Optional[Command]:
        """Resolve command name or alias"""
        return self._lookup.get(name.lower().lstrip("/"))
    
    def get_all(self) -> List[Command]:
        """Get all registered commands"""
        return list(self.commands.values())


# Global registry
registry = CommandRegistry()


# ============================================================================
# Simple CLI
# ============================================================================

class SimpleCLI(cmd.Cmd):
    """Simple CLI with command registry"""
    
    prompt = "myapp> "
    intro = "Welcome! Type /help for available commands."
    
    def __init__(self, session_db: SimpleSessionDB = None):
        super().__init__()
        self.session_db = session_db
        self.current_session_id: Optional[str] = None
        self.session_history: List[Dict[str, Any]] = []
        
        # Register built-in commands
        self._register_builtin_commands()
        # Register commands from registry
        self._load_commands_from_registry()
    
    def _register_builtin_commands(self):
        """Register built-in commands"""
        registry.register(Command(
            name="help", description="Show available commands",
            func=self._cmd_help, aliases=["?", "h"]
        ))
        registry.register(Command(
            name="quit", description="Exit the application",
            func=self._cmd_quit, aliases=["exit", "q"]
        ))
        registry.register(Command(
            name="new", description="Start a new chat session",
            func=self._cmd_new, args_hint="[title]"
        ))
        registry.register(Command(
            name="sessions", description="List past sessions",
            func=self._cmd_sessions
        ))
        registry.register(Command(
            name="resume", description="Resume a previous session",
            func=self._cmd_resume, args_hint="<session_id>"
        ))
    
    def _load_commands_from_registry(self):
        """Load commands from registry into CLI methods"""
        for command in registry.get_all():
            if command.name in ["help", "quit", "new", "sessions", "resume"]:
                continue  # Skip built-ins, already registered
            
            # Create method: do_greet
            method_name = f"do_{command.name}"
            setattr(self, method_name, 
                    lambda args, cmd=command: self._execute_command(cmd, args))
            
            # Register aliases
            for alias in command.aliases:
                alias_method = f"do_{alias}"
                if not hasattr(self, alias_method):
                    setattr(self, alias_method, getattr(self, method_name))
    
    def _execute_command(self, command: Command, args: str):
        """Execute a command"""
        try:
            if command.args_hint:
                result = command.func(args)
            else:
                result = command.func()
            if result is not None:
                print(result)
        except Exception as e:
            print(f"Error: {e}")
    
    def _cmd_help(self, args: str = ""):
        """Show help"""
        print("\nAvailable commands:")
        print("-" * 50)
        for cmd in registry.get_all():
            if cmd.name not in ["help", "quit"]:
                usage = f"/{cmd.name} {cmd.args_hint}".strip()
                print(f"  {usage:<25} {cmd.description}")
        print()
    
    def _cmd_quit(self):
        """Quit"""
        print("Goodbye!")
        if self.current_session_id:
            self.session_db.end_session(self.current_session_id)
        self.session_db.close()
        return True
    
    def _cmd_new(self, args: str = ""):
        """Start a new session"""
        title = args.strip() if args.strip() else None
        session_id = self.session_db.create_session(title)
        self.current_session_id = session_id
        self.session_history = []
        print(f"New session started: {session_id}")
        if title:
            print(f"Title: {title}")
    
    def _cmd_sessions(self, args: str = ""):
        """List past sessions"""
        sessions = self.session_db.list_sessions(limit=10)
        if not sessions:
            print("No active sessions found.")
            return
        
        print("\nActive sessions:")
        print("-" * 50)
        for session in sessions:
            title = session.get("title") or "(no title)"
            print(f"  {session['id']:<8} {title}")
        print()

    
    def _cmd_resume(self, args: str):
        """Resume a previous session"""
        if not args.strip():
            print("Usage: /resume <session_id>")
            return
        
        session_id = args.strip()
        session = self.session_db.get_session(session_id)
        
        if not session:
            print(f"Session not found: {session_id}")
            return
        
        self.session_db.reopen_session(session_id)
        self.current_session_id = session_id
        self.session_history = []
        
        title = session.get("title") or "(no title)"
        print(f"Resumed session: {session_id}")
        print(f"Title: {title}")
    
    def default(self, line: str):
        """Handle unknown commands"""
        if line.startswith('/'):
            print(f"Unknown command: {line}")
        else:
            print(f"Unknown command: {line}")
    
    def precmd(self, line: str):
        """Pre-process input - auto-add slash"""
        if line and not line.startswith('/'):
            return '/' + line
        return line


# ============================================================================
# Example Agent Integration
# ============================================================================

class SimpleAgent:
    """Minimal agent for demonstration"""
    
    def __init__(self, model: str = "gpt-4"):
        self.model = model
        self.conversation_history: List[Dict[str, str]] = []
    
    def chat(self, message: str) -> str:
        """Simple chat response (placeholder)"""
        # In real usage, this would call your AI API
        self.conversation_history.append({"role": "user", "content": message})
        
        # Simulated response
        response = f"Echo: {message}"
        
        self.conversation_history.append({"role": "assistant", "content": response})
        return response


# ============================================================================
# Example Commands (Add these to your CLI)
# ============================================================================

def example_chat_command(args: str) -> str:
    """Example chat command - replace with real AI integration"""
    if not args.strip():
        return "Usage: /chat <message>"
    
    # Create agent if not exists
    if not hasattr(example_chat_command, 'agent'):
        example_chat_command.agent = SimpleAgent()
    
    response = example_chat_command.agent.chat(args)
    return response


# Register your custom commands here
registry.register(Command(
    name="chat", description="Chat with the AI",
    func=example_chat_command, args_hint="<message>"
))


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run the CLI"""
    # Initialize session database
    sessions_dir = Path.home() / ".myapp"
    session_db = SimpleSessionDB(sessions_dir / "sessions.db")
    
    # Create and run CLI
    cli = SimpleCLI(session_db)
    
    print("Starting Simple CLI...")
    print(f"Session database: {session_db.db_path}")
    print()
    
    try:
        cli.cmdloop()
    except KeyboardInterrupt:
        print("\nGoodbye!")
        session_db.close()
        sys.exit(0)


if __name__ == "__main__":
    main()
