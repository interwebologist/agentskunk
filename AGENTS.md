# AGENTS.md: Autonomous Execution Protocol

## 5. Constraints
- **No Hallucinations**: Do not build from memory. Search the offical docs online with Webfetch tool and implement based off real up to date web data
- **Exit Condition**: If `scripts/verify.py` fails 5 times on the same error you must search the error using Webfetch or riase a "BLOCKED" message 
- **Stay Focused:** Only touch files needed for the current prompt.
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
