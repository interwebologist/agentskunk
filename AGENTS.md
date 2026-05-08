# AGENTS.md: Autonomous Execution Protocol

## 5. Constraints
- **No Hallucinations**: Do not build from memory. Search the offical docs online with Webfetch tool and implement based off real up to date web data
- **Exit Condition**: If `scripts/verify.py` fails 5 times on the same error you must search the error using Webfetch or riase a "BLOCKED" message 
- **Stay Focused:** Only touch files needed for the current prompt.
- **Small Steps:** Make changes in small, logical chunks.
- **YOU MUST TEST EVERYTHING:** test everything you make and use the verify.py before ever commiting to repos

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
- Stack: FastAPI + LangGraph + Using OpenAI style llama-server backend

## Notes
- To fix deps: uv sync
