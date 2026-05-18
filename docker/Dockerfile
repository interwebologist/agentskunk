FROM python:3.13-slim
#CODING AGENT CONTAINER ONLY. SHURU IS MICROVM for skunkagent
# meant to be used in skunkagent-worktree worktrees to run yolo coding agents

# Install uv, curl, git, vim, tmux, nodejs, and npm
RUN apt-get update && apt-get install -y curl git vim tmux nodejs npm && rm -rf /var/lib/apt/lists/*

# This allows git to use the GITHUB_TOKEN environment variable for authentication. fine grained token
# humans reviews and merge due to branch protections
RUN git config --global credential.helper store

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN curl -fsSL https://opencode.ai/install | bash && \
    ln -s /root/.opencode/bin/opencode /usr/local/bin/opencode

RUN npm install -g @earendil-works/pi-coding-agent

WORKDIR /app

COPY .pi /app/.pi

COPY docker-entrypoint.sh /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]

COPY . /app

RUN ln -s /app/.pi /root/.pi

CMD ["/bin/sh"]
