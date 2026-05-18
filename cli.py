#!/usr/bin/env python3
"""
CLI Interface for SkunkAgent
"""

import sys
import argparse
import cmd
from typing import Dict, List, Optional, Any

from state import SimpleSessionDB
import agent


class SimpleCLI(cmd.Cmd):
    """CLI with session management"""
    
    prompt = "myapp> "
    intro = "Welcome! Type /help for commands or start chatting."
    
    def __init__(self, session_db: SimpleSessionDB = None, auto_session: bool = True):
        super().__init__()
        self.session_db = session_db
        self.current_session_id: Optional[str] = None
        self.agent_history: List[Dict[str, Any]] = []
        self.auto_session = auto_session
    
    def onecmd(self, line: str):
        """Override to handle / prefix for commands"""
        if line.startswith('/'):
            line = line[1:]
        return super().onecmd(line)
    
    def do_new(self, args: str):
        """Start a new session: /new [title]"""
        if self.current_session_id:
            self.session_db.end_session(self.current_session_id)
        
        title = args.strip() if args.strip() else None
        session_id = self.session_db.create_session(title)
        self.current_session_id = session_id
        self.agent_history = []
        
        print(f"New session started: {session_id}")
        if title:
            print(f"Title: {title}")
    
    def do_sessions(self, args: str):
        """List active sessions: /sessions"""
        sessions = self.session_db.list_sessions(limit=10)
        if not sessions:
            print("No active sessions found.")
            return
        
        print("\nActive sessions:")
        print("-" * 50)
        for session in sessions:
            title = session.get("title") or "(no title)"
            display_id = session.get("display_id", session["id"])
            print(f"  {display_id} {title}")
        print()
    
    def do_resume(self, args: str):
        """Resume a session: /resume <session_id>"""
        if not args.strip():
            print("Usage: /resume <session_id>")
            return
        
        search_id = args.strip()
        session = self.session_db.get_session(search_id)
        
        if not session:
            sessions = self.session_db.list_sessions()
            for s in sessions:
                if s.get("display_id") == search_id:
                    session = s
                    break
        
        if not session:
            print(f"Session not found: {search_id}")
            return
        
        self.session_db.reopen_session(session["id"])
        self.current_session_id = session["id"]
        self.agent_history = self.session_db.get_messages(session["id"])
        
        title = session.get("title") or "(no title)"
        display_id = session.get("display_id", session["id"])
        print(f"Resumed session: {display_id}")
        print(f"Title: {title}")
    
    def do_help(self, args: str):
        """Show help: /help"""
        print("\nAvailable commands:")
        print("-" * 50)
        print("  /new [title]       Start a new chat session")
        print("  /sessions          List active sessions")
        print("  /resume <id>       Resume a previous session")
        print("  /help              Show this help")
        print("  /quit              Exit the application")
        print()
        print("Type your message to chat with the agent.")
    
    def do_quit(self, args: str):
        """Exit: /quit"""
        print("Goodbye!")
        if self.current_session_id:
            self.session_db.end_session(self.current_session_id)
        return True
    
    def default(self, line: str):
        """Handle chat messages"""
        if not line.strip():
            return
        
        if self.current_session_id is None:
            if self.auto_session:
                print("No active session. Creating new session...")
                title = None
                session_id = self.session_db.create_session(title)
                self.current_session_id = session_id
                self.agent_history = []
                print(f"New session started: {session_id}")
            else:
                print("No active session. Use /new to start one.")
                return
        
        user_msg = line.strip()
        self.agent_history.append({"role": "user", "content": user_msg})
        self.session_db.append_message(self.current_session_id, "user", user_msg)
        
        agent.CHAT_HISTORY = self.agent_history
        response = agent.run(user_msg)
        
        self.agent_history.append({"role": "assistant", "content": response})
        self.session_db.append_message(self.current_session_id, "assistant", response)
        
        print(response)
    
    def do_EOF(self, args: str):
        """Handle EOF (Ctrl+D)"""
        return True


def run_single_query(query: str, session_db: SimpleSessionDB) -> str:
    """Run a single query and return response"""
    title = None
    session_id = session_db.create_session(title)
    
    agent_history = []
    agent_history.append({"role": "user", "content": query})
    session_db.append_message(session_id, "user", query)
    
    agent.CHAT_HISTORY = agent_history
    response = agent.run(query)
    
    agent_history.append({"role": "assistant", "content": response})
    session_db.append_message(session_id, "assistant", response)
    
    session_db.end_session(session_id)
    
    return response


def main():
    parser = argparse.ArgumentParser(description="SkunkAgent CLI")
    parser.add_argument("-q", "--query", type=str, help="Single query mode")
    parser.add_argument("--resume", type=str, help="Resume specific session")
    args = parser.parse_args()
    
    session_db = SimpleSessionDB()
    
    if args.query:
        response = run_single_query(args.query, session_db)
        print(response)
        session_db.close()
        sys.exit(0)
    
    if args.resume:
        session = session_db.get_session(args.resume)
        if not session:
            print(f"Session not found: {args.resume}")
            session_db.close()
            sys.exit(1)
        
        session_db.reopen_session(args.resume)
        current_session_id = args.resume
        agent_history = session_db.get_messages(args.resume)
        
        title = session.get("title") or "(no title)"
        display_id = session.get("display_id", session["id"])
        print(f"Resumed session: {display_id}")
        print(f"Title: {title}")
        
        cli = SimpleCLI(session_db, auto_session=False)
        cli.current_session_id = current_session_id
        cli.agent_history = agent_history
        
        print()
        print("Starting chat...")
        try:
            cli.cmdloop()
        except KeyboardInterrupt:
            print("\nGoodbye!")
            session_db.close()
            sys.exit(0)
    
    cli = SimpleCLI(session_db, auto_session=True)
    
    print("Starting SkunkAgent CLI...")
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
