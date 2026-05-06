#!/bin/bash
# shuru-template.sh - Generates dynamic Shuru configuration based on agent number

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/shuru.json"

# Check if agent number is provided
if [ -z "$1" ]; then
  echo "Error: Agent number required"
  echo "Usage: $0 <agent-number>"
  exit 1
fi

AGENT_NUMBER=$1
TOKEN_VAR="GITHUB_AGENT${AGENT_NUMBER}_TOKEN"

# Generate the shuru.json configuration
cat > "$CONFIG_FILE" << EOF
{
  "allow_net": true,
  "allow_host_writes": true,
  "cpus": 4,
  "memory": 4096,
  "disk_size": 8192,
  "mounts": [
    "./:/workspace:rw"
  ],
  "ports": [
    "8000:8000",
    "5173:5173"
  ],
  "secrets": {
    "GITHUB_TOKEN": {
      "from": "${TOKEN_VAR}",
      "hosts": ["api.github.com"]
    }
  }
}
EOF

echo "Generated Shuru configuration for agent $AGENT_NUMBER"
echo "Using token variable: $TOKEN_VAR"
echo "Configuration saved to: $CONFIG_FILE"