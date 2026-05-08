#!/bin/sh
set -e

# Set up git user and email for opencode agent (hardcoded)
echo "Setting up git user name: opencode-agent"
git config --global user.name "opencode-agent"

echo "Setting up git user email: agent@opencode.local"
git config --global user.email "agent@opencode.local"

# Set up git credentials if GITHUB_TOKEN is provided
if [ -n "$GITHUB_TOKEN" ]; then
    echo "Setting up git credentials for GitHub"
    git config --global credential.helper store
    # Extract token value from env to avoid expansion issues
    echo "https://x-access-token:${GITHUB_TOKEN}@github.com" > /root/.git-credentials
    chmod 600 /root/.git-credentials
fi

# Execute the command passed to docker run
exec "$@"
