# AGENTS.md: Autonomous Execution Protocol

## 1. Operating Mission
Your goal is to complete features from start to PR autonomously. You have permission to read the repo, create branches, write code, and execute the verification script. 

## 2. The Hybrid Workflow (Human vs. Agent)
To prevent interference with human developers:
- **Agent Domain**: Your branch is setup for you. do need worry about creating one. 
- **Human Domain**: Never modify `main`, `master`, or branches without the `agent/` prefix unless explicitly told.
- **Hand-off**: If you encounter an "Edge Case" (defined as a design choice with >2 viable options or missing API keys), stop and leave a comment in `TASK_STATUS.md`.

## 3. Step-by-Step Execution Path
Follow this linear path for every task:
   - Map the dependencies. Identify which files need modification.
3. **Execution Loop**:
   - Write/Modify code.
   - Run verify after completing tasks and fix errors till the verify.py script passes `python scripts/verify.py`.
   - **IF FAIL**: Read error output -> Patch code -> Re-run `scripts/verify.py`.

## 4. PR Content Template

If asked to open PR, the description must follow this structure:
- **Summary**: Brief description of changes.
- **Verification Result**: (Insert the Mandatory string from Step 3 only if it actually passed).
- **Files Modified**: List of changed files.

## 5. Constraints
- **No Hallucinations**: If a library is being used do not build from memory. Search the offical docs online and implement based off real up to date info if you fail to an
error message to help in in a max of 3 edits to code file
- **Exit Condition**: If `scripts/verify.py` fails 6 times on the same error, stop and search the web for 
for the offical docs for that library then answer. If you fail again stop and report a "blocker" with 
details for your teammate to help get you unstuck.
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
