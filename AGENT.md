# AI Agent Directives

## 1. Goal
Execute tasks, verify them, and open a PR when done for approval by an admin. Work autonomously. Do not wait for human input unless stuck.

## 2. Rules of Engagement
* **Read First:** Always read `opencode.json` ignores to avoid scanning junk files.
* **Stay Focused:** Only touch files needed for the current prompt.
* **Small Steps:** Make changes in small, logical chunks.
* **Use less words** work faster by enabling the "caveman full" skill and use less words, or monosyllable words. Speak concisely for faster work.

## 3. Workflow to PR
Follow these exact steps for every task:

1. **Analyze:** Review the prompt and explore relevant code.
2. **Execute:** Write the required code and tests.
3. **Verify:** Run the project's test suite (`pytest`).
4. **Fix:** If tests fail, read the logs, fix the code, and re-run until they pass.
5. **Format & Lint:** Run formatting and linting tools. Fix any errors.
6. **Commit:** Stage changes. Write clear, concise commit messages.  
7. **Push & PR:** Push the branch to the remote repo. Create a Pull Request summarizing the changes and confirming tests pass.
