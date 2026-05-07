# Skunk Agent - Agent with Defenses

## Project Focus 

These may or may not end up being features in the end product, at this point these are just ideas. I will build a around security products that are better or not needed and add only what is needed be added to the agent though I want this to deploy "secure"

#### Normal Agent Stuff
- add all agent stuff here. memory, web search

#### Isolation & Sandboxing
- **Shadow Git Checkpointing**
- **Hardware-Isolated MicroVMs / Token proxies**
- **Unikernel Image**
- **Network Sandboxing with Egress Proxy and HITP**
- **HITP**
- **network / command whitelisting**
#### Content & Execution Guardrails
- **Input Guardrails**:
- **Output Guardrails**:
- **Agent Lifecycle & Resource Control**:

#### Authentication & Authorization
- **Ephemeral Secrets, indentity**

## Development with Agent Sandbox

Set GITHUB_AGENT1_TOKEN

### Setup Agent Worktree
```bash
cd skunkagent
git worktree add -b agent/working ../skunkagent-agent-worktree
```

### Build Docker Image
```bash
docker build -t opencode-sandbox .
```

### Run Agent in Sandbox
```bash
docker run --rm -it -v /Users/ryan/AI/skunkagent-agent-worktree:/app -e GITHUB_AGENT1_TOKEN=${GITHUB_TOKEN} opencode-sandbox /bin/sh
.loop.sh, write .spec.md 1st)
```

```bash
docker exec -it opencode-sandbox /bin/sh
```

*Note: The Dockerfile now includes git installation and automatic GitHub token configuration for HTTP endpoints. The agent will automatically use the GITHUB_TOKEN environment variable for git operations requiring authentication.*

To run the container with your GitHub token:
docker run -it -e GITHUB_TOKEN=your_token_here skunkagent
