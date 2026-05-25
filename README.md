<p align="center">
  <img src="images/nerdface.png" alt="Nerdface Logo" width="600"/>
</p>

# Nerdface 

A hackable, lightweight local agent hardened for production

## Project Focus for MVP (Work In Progress)

#### Security

<<<<<<< HEAD
- [X] **Guardrails** - Input scanning to prevent prompt injection using llm-guard NLP models
- **Policy** - Human-in-the-loop approvals (out of band or Auth'd IDV. Would like out of band links and biometric scans ) for destructive actions, all policy outside the prompt.
=======
- [X] **Guardrails** - Input/output scanning to prevent prompt injection, data exfiltration, and malicious behavior using llm-guard NLP models
- [X] **Human-in-the-loop** approvals (out of band or Auth'd IDV. Would like out of band links and biometric scans ) for destructive actions, all policy outside the prompt.
>>>>>>> 0d3fa78a0649d38cf6ef5547fcfbd0a5033684a1
- **logging** - immutable logs for auditing user+agent+tool action. connections for loki /tempo
- [X] **Sandbox** - microVM (Shuru) or strong container isolation
- [X] **Secrets Vault** - Shuru MicroVM has secret proxy
- [ ] **Secured Messaging** - API , IDV Messaging service
- [ ] **Biometic logins** 


#### Agent AI Stuff

- [ ] **Memory** - Local , possible FTS5. Holographic? May do RRF. Research needed here.
- [ ] **Sub-agents** - We want endless types of 'workflows' for orchestration 
- [X] **Web Search:** (SerpBase) that allows deep search engine Dorking and pay as you go, keep forever searches
- [X] **Tools**
- [X] **CLI**
- [X] **API**
- [ ] **Voice STT**
- [ ] **Archtechual Patterns for Small languge models**
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
| **Runaway Loops** | Max iterations limit in ReAct loop | Stops agent after limits exceeded |

### How Guardrails Work

```
User Query → Guardrails (Local NLP) → Agent → Guardrails → User
              ↓ Local Inference ↓              ↓ Local Inference ↓
         (Models on agent machine)       (Models on agent machine)
```

- **Models run locally** on the agent machine (NOT on the LLM server)
- **No network dependency** to LLM server for security scanning
- **Low latency** - models load once, inference takes milliseconds

### NLP Models Used

| Model | Size | Purpose | Hugging Face Path |
|-------|------|---------|-------------------|
| PromptInjection | 714MB | Detects prompt injection attempts | `protectai/deberta-v3-base-prompt-injection-v2` |
| **Total** | **~714MB** | | |

### How Models Run

1. **Download**: First time you run guardrails, models download to `~/.cache/huggingface/hub/`
2. **Load**: Models load into memory using PyTorch + Transformers (happens once on agent startup)
3. **Inference**: Each scanner runs locally on the agent machine
4. **No LLM dependency**: Models don't need access to your LLM server

### Setup

The models are automatically downloaded on first use. To pre-download them:

```bash
cd /Users/ryan/AI/nerdface
uv run python -c "from guardrails import Guardrails; g = Guardrails()"
```

Models will be cached in `~/.cache/huggingface/hub/` for future runs.

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
