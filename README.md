# Skunk Agent - "Agent with Defenses"

## Project Focus 

- guardrails - input / output guardrails with own LLM. Nemo Guardrails. 
- Policy - Human-in-the-loop approvals (out of band or Auth'd IDV. Would like out of band links and biometric scans ) for destructive actions, all policy outside the prompt.
- logging - immutable logs for auditing user+agent+tool action. connections for loki /tempo
- Sandbox - microVM (Shuru) or strong container isolation
- Secrets Vault - Shuru MicroVM has secret proxy 

#### Normal Agent Stuff
- add all agent stuff here. memory, web search

## Feature Updates

#### State Persistence

The agent saves conversation history to SQLite at `~/.skunk/state.db` using the `user` field from `/v1/chat/completions` as the session ID.

#### Skunk-agent Query

```bash
curl -X POST http://localhost:8000/apply \
     -H "Content-Type: application/json" \
     -d '{"text": "whats the weather in denver today ? "}'
```

*Note: The Dockerfile includes git, vim, tmux installation and automatic GitHub token configuration for HTTP endpoints. The agent will automatically use the GITHUB_TOKEN environment variable for git operations requiring authentication.*
