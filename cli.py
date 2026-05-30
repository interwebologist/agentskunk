#!/usr/bin/env python3
"""
CLI Interface for SkunkAgent - Simple stdin-based
"""

import sys
import argparse
import logging
import os

from state import SimpleSessionDB
from agent import run as agent_run
from compression.context_compressor import ContextCompressor

logging.basicConfig(
    level=logging.DEBUG
    if os.getenv("DEBUG", "false").lower() == "true"
    else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def get_multiline_input():
    """Read multi-line input from stdin until EOF (Ctrl+D on Mac/Linux)."""
    print("Multi-Line Mode, Ctrl-D to Enter")
    return sys.stdin.read()


def cmd_new(
    args: str, session_db: SimpleSessionDB, current_session_id: str | None
) -> str:
    """Start a new session: /new [title]"""
    if current_session_id:
        session_db.end_session(current_session_id)

    title = args.strip() if args.strip() else None
    session_id = session_db.create_session(title)
    current_session_id = session_id

    print(f"New session started: {session_id}")
    if title:
        print(f"Title: {title}")

    return current_session_id


def cmd_sessions(args: str, session_db: SimpleSessionDB) -> None:
    """List active sessions: /sessions"""
    sessions = session_db.list_sessions()
    if not sessions:
        print("No sessions found.")
        return

    print("Active sessions:")
    print("-" * 50)
    for session in sessions:
        display_id = session.get("display_id", session["id"])
        title = session.get("title") or "(no title)"
        print(f"  {display_id}: {title}")


def cmd_resume(args: str, session_db: SimpleSessionDB) -> tuple[str | None, list[dict]]:
    """Resume a session: /resume <id>"""
    if not args.strip():
        print("Usage: /resume <session_id>")
        return None, []

    session = session_db.get_session(args.strip())
    if not session:
        print(f"Session not found: {args.strip()}")
        return None, []

    session_db.reopen_session(session["id"])
    session_id = session["id"]
    agent_history = session_db.get_messages(session_id)

    title = session.get("title") or "(no title)"
    display_id = session.get("display_id", session["id"])
    print(f"Resumed session: {display_id}")
    print(f"Title: {title}")

    return session_id, agent_history


def cmd_help(args: str) -> None:
    """Show help: /help"""
    print("\nAvailable commands:")
    print("-" * 50)
    print("  /new [title]       Start a new chat session")
    print("  /sessions          List active sessions")
    print("  /resume <id>       Resume a previous session")
    print("  /help              Show this help")
    print("  /quit              Exit the application")
    print("  /paste             Enter multi-line mode for pasting text")
    print()
    print("Type your message to chat with the agent.")


def cmd_quit(
    args: str, session_db: SimpleSessionDB, current_session_id: str | None
) -> bool:
    """Exit: /quit"""
    print("Goodbye!")
    if current_session_id:
        session_db.end_session(current_session_id)
    return True


def handle_slash_command(
    line: str,
    session_db: SimpleSessionDB,
    current_session_id: str | None,
    agent_history: list[dict],
) -> tuple[str | None, list[dict]]:
    """Handle slash commands. Returns updated (session_id, agent_history)."""
    parts = line.split(maxsplit=1)
    cmd = parts[0]
    args = parts[1] if len(parts) > 1 else ""

    if cmd == "/new":
        current_session_id = cmd_new(args, session_db, current_session_id)
        agent_history = []
    elif cmd == "/sessions":
        cmd_sessions(args, session_db)
    elif cmd == "/resume":
        new_id, new_history = cmd_resume(args, session_db)
        if new_id:
            current_session_id = new_id
            agent_history = new_history
    elif cmd == "/help":
        cmd_help(args)
    elif cmd == "/quit":
        if cmd_quit(args, session_db, current_session_id):
            sys.exit(0)
    elif cmd == "/paste":
        logger.debug("Entering paste mode...")
        multiline_text = get_multiline_input()
        logger.debug(f"Captured {len(multiline_text)} characters")
        if multiline_text.strip():
            current_session_id, agent_history = process_chat_message(
                multiline_text, session_db, current_session_id, agent_history
            )
    else:
        print(f"Unknown command: {cmd}")

    return current_session_id, agent_history


def process_chat_message(
    message: str,
    session_db: SimpleSessionDB,
    current_session_id: str | None,
    agent_history: list[dict],
) -> tuple[str | None, list[dict]]:
    """Process a chat message. Returns updated (session_id, agent_history)."""
    if not message.strip():
        return current_session_id, agent_history

    if current_session_id is None:
        print("No active session. Use /new to start one.")
        return current_session_id, agent_history

    agent_history.append({"role": "user", "content": message})
    session_db.append_message(current_session_id, "user", message)
    logger.debug(f"User message stored: {message[:100]}...")

    from agent import CHAT_HISTORY

    CHAT_HISTORY[:] = agent_history
    logger.debug("Calling agent_run...")
    response = agent_run(message)
    logger.debug(f"Agent response received: {response[:100]}...")

    agent_history.append({"role": "assistant", "content": response})
    session_db.append_message(current_session_id, "assistant", response)
    logger.debug("Assistant response stored")

    print(f"\n{response}\n")

    if os.getenv("ENABLE_COMPRESSION") == "true":
        from compression.model_metadata import estimate_messages_tokens_rough

        estimate = estimate_messages_tokens_rough(agent_history)
        if estimate > 100000:
            print(f"Warning: Context size ({estimate} tokens) is getting large")
            compressor = ContextCompressor()
            compressor.compress(agent_history)

    return current_session_id, agent_history


def main():
    parser = argparse.ArgumentParser(description="NerdFace CLI")
    parser.add_argument(
        "--no-auto-session", action="store_true", help="Don't auto-create sessions"
    )
    parser.add_argument("--session-id", help="Resume a specific session")
    parser.add_argument("--title", help="Title for new session")
    args = parser.parse_args()

    session_db = SimpleSessionDB()

    current_session_id: str | None = None
    agent_history: list[dict] = []

    if args.session_id:
        session = session_db.get_session(args.session_id)
        if not session:
            print(f"Session not found: {args.session_id}")
            sys.exit(1)

        session_db.reopen_session(session["id"])
        current_session_id = session["id"]
        agent_history = session_db.get_messages(args.session_id)
        title = session.get("title") or "(no title)"
        display_id = session.get("display_id", session["id"])
        print(f"Resumed session: {display_id}")
        print(f"Title: {title}")
        if args.title:
            session_db.update_session_title(args.session_id, args.title)
    elif not args.no_auto_session:
        title = None
        current_session_id = session_db.create_session(title)
        print(f"New session started: {current_session_id}")

    print("Starting NerdFace Agent CLI...")
    print(f"Session database: {session_db.db_path}")
    print("Type /help for commands. Type /paste for multi-line mode.")
    print()

    try:
        while True:
            try:
                line = input("NerdFace> ")
            except EOFError:
                print("\nGoodbye!")
                break

            if not line.strip():
                continue

            if line.startswith("/"):
                current_session_id, agent_history = handle_slash_command(
                    line, session_db, current_session_id, agent_history
                )
            else:
                current_session_id, agent_history = process_chat_message(
                    line, session_db, current_session_id, agent_history
                )

    except KeyboardInterrupt:
        print("\nGoodbye!")
    finally:
        if current_session_id:
            session_db.end_session(current_session_id)
        session_db.close()


if __name__ == "__main__":
    main()
