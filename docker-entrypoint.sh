#!/bin/sh
set -e

# Set up git credentials if GITHUB_TOKEN is provided
if [ -n "$GITHUB_TOKEN" ]; then
    echo "Setting up git credentials for GitHub"
    git config --global credential.helper store
    # Extract token value from env to avoid expansion issues
    TOKEN_VALUE=$(env | grep GITHUB_TOKEN | cut -d= -f2-)
    echo "https://${TOKEN_VALUE}@github.com" > /root/.git-credentials
    chmod 600 /root/.git-credentials
fi

# Execute the command passed to docker run
exec "$@"
