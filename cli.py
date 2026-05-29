#!/usr/bin/env python3
"""
CLI Interface for SkunkAgent
"""

import argparse
import cmd
import logging
import os
import sys
from typing import Dict, List, Optional, Any

from state import SimpleSessionDB
import agent
from compression.context_compressor import ContextCompressor

logger = logging.getLogger(__name__)


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
        self.compressor: Optional[ContextCompressor] = None
        self._init_compressor()

    def _init_compressor(self):
        """Initialize context compressor if needed."""
        try:
            self.compressor = ContextCompressor(
                model=os.getenv("MODEL_NAME", "test-model"),
                threshold_percent=0.50,
                quiet_mode=False,
                config_context_length=int(os.getenv("MODEL_CONTEXT_LENGTH", "128000")),
            )
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to initialize compressor: {e}")
            self.compressor = None

    def onecmd(self, line: str):
        """Override to handle / prefix for commands"""
        if line.startswith("/"):
            line = line[1:]
        return super().onecmd(line)

    def do_new(self, args: str) -> None:
        """Start a new session: /new [title]"""
        if self.current_session_id:
            self.session_db.end_session(self.current_session_id)

        title = args.strip() if args.strip() else None
        session_id = self.session_db.create_session(title)
        self.current_session_id = session_id
        self.agent_history = []

        logger.info("New session started: %s", session_id)
        if title:
            logger.info("Title: %s", title)

    def do_sessions(self, args: str) -> None:
        """List active sessions: /sessions"""
        sessions = self.session_db.list_sessions(limit=10)
        if not sessions:
            logger.info("No active sessions found.")
            return

        logger.info("Active sessions:")
        logger.info("-" * 50)
        for session in sessions:
            title = session.get("title") or "(no title)"
            display_id = session.get("display_id", session["id"])
            logger.info("  %s %s", display_id, title)
        logger.info("")

    def do_resume(self, args: str) -> None:
        """Resume a session: /resume <session_id>"""
        if not args.strip():
            logger.warning("Usage: /resume <session_id>")
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
            logger.error("Session not found: %s", search_id)
            return

        self.session_db.reopen_session(session["id"])
        self.current_session_id = session["id"]
        self.agent_history = self.session_db.get_messages(session["id"])

        title = session.get("title") or "(no title)"
        display_id = session.get("display_id", session["id"])
        logger.info("Resumed session: %s", display_id)
        logger.info("Title: %s", title)

    def do_help(self, args: str) -> None:
        """Show help: /help"""
        logger.info("Available commands:")
        logger.info("-" * 50)
        logger.info("  /new [title]       Start a new chat session")
        logger.info("  /sessions          List active sessions")
        logger.info("  /resume <id>       Resume a previous session")
        logger.info("  /help              Show this help")
        logger.info("  /quit              Exit the application")
        logger.info("")
        logger.info("Type your message to chat with the agent.")

    def do_quit(self, args: str) -> bool:
        """Exit: /quit"""
        logger.info("Goodbye!")
        if self.current_session_id:
            self.session_db.end_session(self.current_session_id)
        return True

    def default(self, line: str) -> None:
        """Handle chat messages"""
        if not line.strip():
            return

        if self.current_session_id is None:
            if self.auto_session:
                logger.info("No active session. Creating new session...")
                title = None
                session_id = self.session_db.create_session(title)
                self.current_session_id = session_id
                self.agent_history = []
                logger.info("New session started: %s", session_id)
            else:
                logger.warning("No active session. Use /new to start one.")
                return

        user_msg = line.strip()
        self.agent_history.append({"role": "user", "content": user_msg})
        self.session_db.append_message(self.current_session_id, "user", user_msg)

        agent.CHAT_HISTORY = self.agent_history
        response = agent.run(user_msg)

        self.agent_history.append({"role": "assistant", "content": response})
        self.session_db.append_message(self.current_session_id, "assistant", response)

        if self.compressor:
            from compression.model_metadata import estimate_messages_tokens_rough

            tokens = estimate_messages_tokens_rough(self.agent_history)
            if self.compressor.should_compress(tokens):
                compressed = self.compressor.compress(self.agent_history, tokens)
                self.agent_history = compressed

        logger.info("Response: %s", response)

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


def main() -> None:
    parser = argparse.ArgumentParser(description="SkunkAgent CLI")
    parser.add_argument("-q", "--query", type=str, help="Single query mode")
    parser.add_argument("--resume", type=str, help="Resume specific session")
    args = parser.parse_args()

    session_db = SimpleSessionDB()

    if args.query:
        response = run_single_query(args.query, session_db)
        logger.info("Query response: %s", response)
        session_db.close()
        sys.exit(0)

    if args.resume:
        session = session_db.get_session(args.resume)
        if not session:
            logger.error("Session not found: %s", args.resume)
            session_db.close()
            sys.exit(1)

        session_db.reopen_session(args.resume)
        current_session_id = args.resume
        agent_history = session_db.get_messages(args.resume)

        title = session.get("title") or "(no title)"
        display_id = session.get("display_id", session["id"])
        logger.info("Resumed session: %s", display_id)
        logger.info("Title: %s", title)

        cli = SimpleCLI(session_db, auto_session=False)
        cli.current_session_id = current_session_id
        cli.agent_history = agent_history

        logger.info("")
        logger.info("Starting chat...")
        try:
            cli.cmdloop()
        except KeyboardInterrupt:
            logger.info("\nGoodbye!")
            session_db.close()
            sys.exit(0)

    cli = SimpleCLI(session_db, auto_session=True)

    logger.info("Starting SkunkAgent CLI...")
    logger.info("Session database: %s", session_db.db_path)
    logger.info("")

    try:
        cli.cmdloop()
    except KeyboardInterrupt:
        logger.info("\nGoodbye!")
        session_db.close()
        sys.exit(0)


if __name__ == "__main__":
    main()
