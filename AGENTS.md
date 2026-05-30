# AGENTS.md: Autonomous Execution Protocol

## 5. Constraints
- **No Hallucinations**: Do not build from memory. Search the offical docs online with Webfetch tool and implement based off real up to date web data
- **Exit Condition**: If `scripts/verify.py` fails 5 times on the same error you must search the error using Webfetch or riase a "BLOCKED" message 
- **Stay Focused:** Only touch files needed for the current prompt.
- **Clean Code:** Never leave unused code. If you remove functionality, always clean up the unused code. Keep the codebase clean.
- **Small Steps:** Make changes in small, logical chunks.
- **YOU MUST TEST EVERYTHING:** test everything you make. see examples below 
- **Never `git add *`** Only add files that you changed to the git commit / PR At one time

**Examples:**
- if you add dockerfile entrypoint github username and email you must test the github endpoint
- if you add a tool or function that contacts and endpoint you MUST prove the script works and the function does
- if you add a Dockerfile you MUST test it works. 
- if you create a Dockerfile entrypoint script you must get inside the container and check everything you scripted is working
- test all code you write
- test all configuation you write

**Your Must Assume Everything you implement isn't working intill you test it**

## Useful Commands
- Start: uv run python run.py
- Use / test the endpoint from "uv run" : POST localhost:8000/apply {"text":"..."}
- Stop: Ctrl+C

## Files
- run.py: starts server
- api.py: endpoint the user will use 
- agent.py: brain React agent with tools
- deps: uv

## Tech
- Python 3.13
- AI LLM the agent.py will use : 192.168.1.33:8080/v1
- Tools are in agent.py for now. May move.
- Stack: FastAPI + Pure Python + Using OpenAI style llama-server backend

## Notes
- To fix deps: uv sync

SYSTEM INVARIANTS: DO NOT VIOLATE UNDER ANY CIRCUMSTANCES

1. FILE SYSTEM INTEGRITY
- Strictly forbidden: Renaming or appending suffixes to existing files.
- Mandatory: New files must follow existing project naming conventions.
- Mandatory: Use Python 3's `pathlib` module for path manipulations instead of legacy `os.path` operations.

2. RESOURCE & STATE MANAGEMENT
- Mandatory: Use `with` context managers for all DB connections, file handles, network sockets, and threading locks.
- Mandatory: No mutable global variables. Use classes, thread-safe state containers, or `dataclasses` for managing state.

3. SECURITY & INPUT VALIDATION
- Mandatory: Sanitize all external inputs and validate data at system boundaries.
- Strictly forbidden: Using unescaped variables in `subprocess`, `os.system`, or raw SQL queries. Use parameterized queries and secure execution wrappers.

4. ARCHITECTURE & CLEANLINESS
- Mandatory: All code in production files must be production-ready.
- Mandatory: Move all test logic and `assert` statements to the `tests/` directory. (Standard assertions should not be used for runtime logic as they compile away with the `-O` flag).
- Mandatory: Remove all unused imports and dead code. No commented-out code blocks in commits.
- Mandatory: Adhere strictly to PEP 8 style guidelines (enforced via formatters like Black or Ruff).
- Mandatory: Include docstrings (PEP 257) for all public modules, classes, and functions.

5. ERROR HANDLING & LOGGING
- Mandatory: No bare `except:` clauses. Catch specific exception types to avoid silencing `KeyboardInterrupt` or `SystemExit`.
- Mandatory: Use the `logging` module only. No `print()` statements for system output or debugging in production code.
- Mandatory: Use exception chaining (`raise NewException from original_exception`) when re-raising to preserve tracebacks.

6. TYPE SAFETY
- Mandatory: All new functions/methods must include PEP 484 type hints.
- Note: Type hints are standard for Python 3.5+ and essential for IDE support and static analysis tools (e.g., `mypy`).

7. CONFIGURATION & DEPENDENCIES
- Mandatory: Extract all hard-coded URLs, keys, and values to `.env` or config files.
- Mandatory: Explicitly declare all project dependencies and their versions in a `pyproject.toml` or `requirements.txt`.

8. MODERN PYTHON 3 IDIOMS
- Mandatory: Use f-strings (`f"Hello {name}"`) for string interpolation instead of legacy `%` formatting or `.format()`.
- Mandatory: Use `@dataclass` (Python 3.7+) to reduce boilerplate for classes that primarily store state.
- Mandatory: Always use the `is` operator for comparing singletons (e.g., `if x is None:`, `if not flag is True:`).

