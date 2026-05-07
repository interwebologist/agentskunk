# AGENTS.md: Autonomous Execution Protocol

## 1. Operating Mission
Your goal is to complete features from start to PR autonomously. You have permission to read the repo, create branches, write code, and execute the verification script. 

## 2. The Hybrid Workflow (Human vs. Agent)
To prevent interference with human developers:
- **Agent Domain**: Your branch is setup for you. do need worry about creating one. 
- **Human Domain**: Never modify `main`, `master`
- **Hand-off**: If you encounter an "Edge Case" (defined as a design choice with >2 viable options or missing API keys), stop and leave a comment in `TASK_STATUS.md`.

## 3. Step-by-Step Execution Path
Follow this linear path for every task:
   - Map the dependencies. Identify which files need modification.
**Always Search Offical Docs**
   - Never write python code without checking the offical online docs using webfetch 
   - its vital you never code from memory as you are wrong and the offline docs are the correct was to write the code 
**Execution Loop**:
   - Write/Modify code.
   - Run verify after completing tasks and fix errors till the verify.py script passes `python scripts/verify.py`.
   - **IF FAIL**: Read error output -> Patch code -> Re-run `scripts/verify.py`.

## 4. PR Content Template

If asked to open PR, the description must follow this structure:
- **Summary**: Brief description of changes.
- **Verification Result**: showed what passed / failed
- **Files Modified**: List of changed files.

## 5. Constraints
- **No Hallucinations**: Do not build from memory. Search the offical docs online with Webfetch tool and implement based off real up to date web data
- **Exit Condition**: If `scripts/verify.py` fails 5 times on the same error you must search the error using Webfetch or riase a "BLOCKED" message 
- **Stay Focused:** Only touch files needed for the current prompt.
- **Small Steps:** Make changes in small, logical chunks.

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
