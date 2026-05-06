# Skunk Agent - Agent with Defenses

- skunk agent is WIP repo that is being built with a microVM'd (sandboxed) agent using either Pi/Opencode and local models running on the Strix Halo 128GB AI APU locally. 
- Agent cuts a PR to a branch protected repo for "Human in the loop" (HITL) review. Agents uses linting, ruff and other feedback verification scripts along the way. 
- CI via github actions builds gates into the agent PR for further guardrails. This is me practicing what I believe is the future of the agentic dev experience.
- Agent runs in a Ralph Loop as I engineer and plan the tasks for the next feature.
- This is a test of the what I believe is the final form of the "fully augmented" engineer of the future.

# Project Focus 

Deployed Skunk Agent Main Focus:

These may or may not end up being features in the end product, at this point these are just ideas. I will build a around security products that are better or not needed and add only what is needed be added to the agent though I want this to deploy "secure"

#### Normal Agent Stuff
- add all agent stuff here. memory, web search
- Tuned for Local use and self hosting to keep company secrets safe.
- Would like smaller fine-tuned mode LLM for routing and basic tasks, Larger for deep reasoning. configurable

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
    - Loop Detection: Implements cyclic graph checks and `message[-1]==message[-2]` checks. Can inject "STOP" commands or break loops.
    - Limits: Max iterations cap and a Time-To-Live (TTL) on every task (e.g., 60 seconds) with forced termination.
    - Resource Quotas: CPU and RAM consumption limited to small, defined slices.

#### Authentication & Authorization
- **Ephemeral Secrets, indentity **: Employs short-lived tokens (e.g., AWS IAM Roles, HashiCorp Vault,github, okta, etc). 
