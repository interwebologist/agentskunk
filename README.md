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

### Build Docker Image
```bash
docker build -t skunkagent .
```

### Run Agent in Sandbox with GitHub Token
```bash
docker run -it -e GITHUB_TOKEN=${GITHUB_AGENT1_TOKEN} skunkagent
```

The container will:
1. Start and provide a shell prompt
2. Have opencode CLI available (run `opencode --version` to verify)
3. Have git installed and configured to use the GITHUB_TOKEN for authentication
4. Have vim and tmux installed for editing and terminal multiplexing
5. Automatically set up git credentials when GITHUB_TOKEN is provided

*Note: The Dockerfile includes git, vim, tmux installation and automatic GitHub token configuration for HTTP endpoints. The agent will automatically use the GITHUB_TOKEN environment variable for git operations requiring authentication.*
