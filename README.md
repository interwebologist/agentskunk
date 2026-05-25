<p align="center">
  <img src="images/nerdface.png" alt="Nerdface Logo" width="600"/>
</p>

# ☝️🤓 NERD FACE 

A hackable, lightweight local agent hardened for production

## Project Focus for MVP (Work In Progress)

#### Security

- [X] **Guardrails** - Input scanning to prevent prompt injection using llm-guard NLP models
- **Policy** - Human-in-the-loop approvals (out of band or Auth'd IDV. Would like out of band links and biometric scans ) for destructive actions, all policy outside the prompt.
- **logging** - immutable logs for auditing user+agent+tool action. connections for loki /tempo
- [X] **Sandbox** - microVM (Shuru) or strong container isolation
- [X] **Secrets Vault** - Shuru MicroVM has secret proxy
- [ ] **Secured Messaging** - API
- [ ] **Biometic, MFA logins** - Identity


#### Agent AI Stuff

- [ ] **Memory** - Local , possible FTS5, HRR Holographic. FTS5 O(log N) with trust score RRF. 
- [ ] **Sub-agents** - We want endless types of 'workflows' for orchestration 
- [X] **Web Search:** (SerpBase) that allows deep search engine Dorking and pay as you go, keep forever searches
- [X] **Tools**
- [X] **CLI**
- [X] **API**

- [ ] **System Design Patterns for Small languge models**
- [ ] **Compression** - head / tail with summerize the middle. tool calls clean up when not needed. 4 part algorithm. patachute for LLM gateway protection as 2nd safety
- [ ] **Reduced Attack Vector** on popular offering
- [ ] **NerdPrompt** - allow to be used with NerdPrompt in terminal

## Guardrails Overview

The Nerdface uses **llm-guard** to scan all inputs for security threats before they reach the agent.

### What Guardrails Protect Against

| Threat | Detection Method | Action |
|--------|-----------------|--------|
| **Prompt Injection** | NLP model analyzes text for attempts to override system instructions | Blocks input, triggers kill-switch |
| **Sandbox Escape Attempts** | Regex patterns for `/etc/passwd`, Docker/K8s commands | Blocks output containing system paths |
| **Runaway Loops** | Max iterations limit 

- **Models run locally** on the agent machine (NOT on the LLM server)
- **Low latency** - models load once, inference takes milliseconds

### NLP Models Used

| Model | Size | Purpose | Hugging Face Path |
|-------|------|---------|-------------------|
| PromptInjection | 714MB | Detects prompt injection attempts | `protectai/deberta-v3-base-prompt-injection-v2` |
| **Total** | **~714MB** | | |

## Feature Updates

#### State Persistence

The agent saves conversation history to SQLite at `~/.nerdface/state.db` using the `user` field from `/v1/chat/completions` as the session ID.

#### Nerdface Query

```bash
curl -X POST http://localhost:8000/apply \
     -H "Content-Type: application/json" \
     -d '{"text": "whats the weather in denver today ? "}'
```

*Note: The Dockerfile includes git, vim, tmux installation and automatic GitHub token configuration for HTTP endpoints. The agent will automatically use the GITHUB_TOKEN environment variable for git operations requiring authentication.*
