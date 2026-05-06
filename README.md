# Skunk Agent - Agent with Defenses

# Project Focus 

These may or may not end up being features in the end product, at this point these are just ideas. I will build a around security products that are better or not needed and add only what is needed be added to the agent though I want this to deploy "secure"

#### Normal Agent Stuff
- add all agent stuff here. memory, web search
- Tuned for Local use and self hosting to keep company secrets safe. of course big models can play tool
- Would like smaller fine-tuned mode LLM for routing and basic tasks, Larger for deep reasoning. configurable. Would like ppl to run it in their house and securely as a C-Suite team daily driver

#### Isolation & Sandboxing
- **Shadow Git Checkpointing**: Read/Write for a shadow Git folder; all other OS access is Read-Only. not sure if I want to do this shadow gitfolder, microvm , etc
- **Hardware-Isolated MicroVMs / Token proxies**: Uses a MicroVM for hardware-enforced blocking of the OS. it does not share kernels like container
- **Unikernel Image**: Utilizes a Unikernel for a minimal attack surface. No hacker tools (e.g., `curl`, `vim`) exist within the image, preventing host takeover... unless you want your agent to have this. Could be good configurable option. 
- **Network Sandboxing with Egress Proxy and HITP**: HITP/configurable sandboxing to prevent unauthorized network access, blocking tool usage and lateral movement

#### Content & Execution Guardrails
- **Input Guardrails**:
    - "Police" LLM evaluates input for malicious intent.
    - Canary trap words integrated to detect prompt injection.
    - Ingress Guardrails check incoming data for social engineering; instantly rejects and blocks IPs attempting exploitation.
- **Output Guardrails**:
    - "Police" LLM reviews output for leaked secrets, sensitive data, or security threats.
    - Egress Proxy reads all outflowing data; instantly kills connection upon detecting strings matching API keys, passwords, or PII. Enforces HTTP allow/deny URLs for network sandboxing.
- **Agent Lifecycle & Resource Control**:
    - Loop Detection: Implements cyclic graph checks or dumb checks like `message[-1]==message[-2]`. Can inject "dont do that again ! try something new" commands or break loops.
    - Limits: Max iterations cap and a Time-To-Live (TTL) on every task (e.g., 60 seconds) with forced termination.
    - Resource Quotas: CPU and RAM consumption limited to small, defined slices.

#### Authentication & Authorization
- **Ephemeral Secrets, indentity **: Employs short-lived tokens (e.g., AWS IAM Roles, HashiCorp Vault,github, okta, etc).Not Telegram... owned by the Russians or whoever has it now.

## Quick Start for Autonomous Coding

1. Set your GitHub token: `export GITHUB_AGENT1_TOKEN='your_token_here'`
2. Source your shell: `source ~/.zshrc`
3. Start agent: `./run-agent.sh feature-branch 1`
4. Workspace ready at `../feature-branch` with Opencode running headless
5. Use `shuru` directly in workspace for subsequent sessions
6. Connect to Opencode: `curl -X POST localhost:8000/apply -H "Content-Type: application/json" -d '{"text":"your command"}'`

## Practicing What I Preach: The Fully Augmented Engineer 

- Agent runs in a Ralph Loop as I engineer and plan/work the tasks for the next feature as architect , team lead , and project manager.
- This is a test of the what I believe is the final form of the "fully augmented" engineer except I believe it can all be done today while most the hype is still on "out of reach" models
- finally I would like to be able to launch many features at once and have agent know expected input/output and weave it all together (we will get there)

### What is it
- skunk agent is being built with a microVM'd (sandboxed) Ralph loop agent using either Pi/Opencode and local models running on the Strix Halo 128GB AI APU locally. 
- Agent cuts a PR to a "main" branch protected repo for "Human in the loop" (HITL) review. Agents uses linting, ruff and other feedback verification scripts along the way. 
- CI via github actions builds gates into the agent PR for further guardrails. 
