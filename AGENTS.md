# AGENTS.md: Autonomous Execution Protocol

## 1. Operating Mission
Your goal is to complete features from start to PR autonomously. You have permission to read the repo, create branches, write code, and execute the verification script. 

## 2. The Hybrid Workflow (Human vs. Agent)
To prevent interference with human developers:
- **Agent Domain**: You only work on branches prefixed with `agent/` (e.g., `agent/add-login-api`).
- **Human Domain**: Never modify `main`, `master`, or branches without the `agent/` prefix unless explicitly told.
- **Hand-off**: If you encounter an "Edge Case" (defined as a design choice with >2 viable options or missing API keys), stop and leave a comment in `TASK_STATUS.md`.

## 3. Step-by-Step Execution Path
Follow this linear path for every task:

   - Map the dependencies. Identify which files need modification.
3. **Execution Loop**:
   - Write/Modify code.
   - Run verification: `python scripts/verify.py`.
   - **IF FAIL**: Read JSON error output -> Patch code -> Re-run `scripts/verify.py`.
   - **IF PASS**: Proceed to Step 4.
4. **Final Pull Request**:
   - You are authorized to push to origin and create a PR.
   - **Mandatory PR Body**: You must include the exact string: 
     `✅ AUTOMATED VERIFICATION: ALL TESTS AND LINTS PASSED.`

## 4. PR Content Template
When opening a PR, the description must follow this structure:
- **Summary**: Brief description of changes.
- **Verification Result**: (Insert the Mandatory string from Step 3 only if it actually passed).
- **Files Modified**: List of changed files.

## 5. Constraints
- **No Hallucinations**: If a library is being used do not build from memory. Search the offical docs online and implement based off real up to date info 
- **Silent Correction**: Do not ask for permission to fix linting errors; just fix them
- **Exit Condition**: If `scripts/verify.py` fails 6 times on the same error, stop and report a "Blocker" in the PR as a draft.



# OpenCode Agent Directives

## 1. Goal
Execute tasks, verify them, and open a PR. Work autonomously. Do not wait for human input unless stuck.

## 2. Rules of Engagement
* **Read First:** Always read `opencode.json` ignores to avoid scanning junk files.
* **Stay Focused:** Only touch files needed for the current prompt.
* **Small Steps:** Make changes in small, logical chunks.

## 3. Workflow to PR
Follow these exact steps for every task:

1. **Analyze:** Review the prompt and explore relevant code.
2. **Execute:** Write the required code and tests.
3. **Verify:** Run the project's test suite (e.g., `npm test`, `pytest`, `cargo test`).
4. **Fix:** If tests fail, read the logs, fix the code, and re-run until they pass.
5. **Format & Lint:** Run formatting and linting tools. Fix any errors.
6. **Commit:** Stage changes. Write clear, concise commit messages.
7. **Push & PR:** Push the branch to the remote repo. Create a Pull Request summarizing the changes and confirming tests pass.

# SkunkAgent Repo Rules

## Commands
- Start: uv run python run.py
- Use: POST localhost:8000/apply {"text":"..."}
- Stop: Ctrl+C

## Files
- run.py: starts server
- api.py: web stuff
- agent.py: brain
- deps: uv

## Tech
- Python 3.13
- AI: 192.168.1.33:8080/v1
- Tool: get_weather (now with real weather)
- Stack: FastAPI + LangGraph + Using OpenAI style llama-server backend

## Notes
- Fix deps: uv sync
