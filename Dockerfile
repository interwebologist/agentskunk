FROM python:3.13-slim

# Install uv, curl, git, vim, and tmux
RUN apt-get update && apt-get install -y curl git vim tmux && rm -rf /var/lib/apt/lists/*

# Configure git to use GitHub token for HTTP endpoints automatically
# This allows git to use the GITHUB_TOKEN environment variable for authentication
# We'll set this up at runtime instead of build time since GITHUB_TOKEN isn't available during build
RUN git config --global credential.helper store

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install opencode CLI
RUN curl -fsSL https://opencode.ai/install | bash && \
    ln -s /root/.opencode/bin/opencode /usr/local/bin/opencode

# Set working directory
WORKDIR /app

# Copy current directory contents into the container at /app
ADD . /app

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh

# Default command to start shell
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["/bin/sh"]
