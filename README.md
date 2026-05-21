<p align="center">
  <img src="images/skunkagent.png" alt="Skunk Agent Logo" width="600"/>
</p>

# Skunk Agent - "Agent with Defenses"

## Project Focus for MVP (Work In Progress)

#### Security

- [X] **Guardrails** - Input/output scanning to prevent prompt injection, data exfiltration, and malicious behavior using llm-guard NLP models
- **Policy** - Human-in-the-loop approvals (out of band or Auth'd IDV. Would like out of band links and biometric scans ) for destructive actions, all policy outside the prompt.
- **logging** - immutable logs for auditing user+agent+tool action. connections for loki /tempo
- [X] **Sandbox** - microVM (Shuru) or strong container isolation
- [X] **Secrets Vault** - Shuru MicroVM has secret proxy
- [ ] **Secured Messaging** - API , IDV Messaging service
- [ ] **Biometic logins** 


#### Agent AI Stuff

- [ ] **Memory** - Local , possible FTS5. Holographic?
- [ ] **Sub-agents**
- [X] **Web Search:** (SerpBase) that allows deep search engine Dorking and pay as you go, keep forever searches
- [X] **Tools**
- [X] **CLI**
- [X] **API**
- [ ] **Voice STT**

## Guardrails Overview

The Skunk Agent uses **llm-guard** to scan all inputs and outputs for security threats before they reach the the agent or before it leaves the agent and they are returned to the user.

### What Guardrails Protect Against

| Threat | Detection Method | Action |
|--------|-----------------|--------|
| **Prompt Injection** | NLP model analyzes text for attempts to override system instructions | Blocks input, triggers kill-switch |
| **Gibberish/LLM Jailbreaks** | Detects nonsensical or encoded payloads | Blocks suspicious inputs |
| **Sandbox Escape Attempts** | Regex patterns for `/etc/passwd`, Docker/K8s commands | Blocks output containing system paths |
| **Proxy Token Leaks** | Regex patterns for API keys, tokens, bearer tokens | Revokes credentials, triggers kill-switch |
| **Malicious URLs** | NLP model classifies URLs as safe/malicious | Blocks output with malicious links |
| **High-Entropy Data** | Shannon entropy calculation for encoded secrets | Detects base64/hex encoded payloads |
| **Runaway Loops** | Step counter, token velocity monitoring | Stops agent after limits exceeded |

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
| Gibberish | 256MB | Detects nonsensical/gibberish text | `madhurjindal/autonlp-Gibberish-Detector-492513457` |
| MaliciousURLs | 954MB | Detects malicious URLs | `DunnBC22/codebert-base-Malicious_URLs` |
| **Total** | **~1.9GB** | | |

### How Models Run

1. **Download**: First time you run guardrails, models download to `~/.cache/huggingface/hub/`
2. **Load**: Models load into memory using PyTorch + Transformers (happens once on agent startup)
3. **Inference**: Each scanner runs locally on the agent machine
4. **No LLM dependency**: Models don't need access to your LLM server

### Setup

The models are automatically downloaded on first use. To pre-download them:

```bash
cd /Users/ryan/AI/skunkagent
uv run python -c "from guardrails import Guardrails; g = Guardrails()"
```

Models will be cached in `~/.cache/huggingface/hub/` for future runs.

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
