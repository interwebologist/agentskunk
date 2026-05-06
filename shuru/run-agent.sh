#!/bin/bash
# run-agent.sh
# Usage: ./run-agent.sh [--help] [--force-worktree] feature-branch-name

# Show help message
show_help() {
    echo "Usage: $0 [--help] [--force-worktree] feature-branch-name"
    echo ""
    echo "Options:"
    echo "  --help           Show this help message"
    echo "  --force-worktree Force creation of new worktree even if already in one"
    echo ""
    echo "Environment Variables:"
    echo "  GITHUB_AGENT{number}_TOKEN  GitHub fine-grained token for agent {number}"
    echo ""
    echo "Required Token Permissions:"
    echo "  - Contents: read/write"
    echo "  - Pull requests: read/write"
    echo ""
    echo "To set up your token:"
    echo "  1. Create a fine-grained token with the above permissions"
    echo "  2. Add to your ~/.zshrc or ~/.bashrc:"
    echo "     export GITHUB_AGENT1_TOKEN='your_token_here'"
    echo "  3. Source your shell config: source ~/.zshrc"
    echo ""
    echo "Notes:"
    echo "  - Tokens must be exported in shell rc files so they're available to child processes"
    echo "  - The worktree will be created at ../<branch-name> relative to current directory"
    echo "  - After creation, you'll be left in the new worktree directory"
    echo "  - Cleanup: git worktree remove ../<branch-name> || git worktree prune"
    exit 0
}

# Parse arguments
FORCE_WORKTREE=false
AGENT_NUM_PROVIDED=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            show_help
            ;;
        --force-worktree)
            FORCE_WORKTREE=true
            shift
            ;;
        *)  # First non-option argument
            if [ -z "$BRANCH_NAME" ]; then
                BRANCH_NAME=$1
            elif [ -z "$AGENT_NUMBER" ] && [ "$AGENT_NUM_PROVIDED" = false ]; then
                AGENT_NUMBER=$1
                AGENT_NUM_PROVIDED=true
            else
                echo "Error: Too many arguments"
                show_help
            fi
            shift
            ;;
    esac
done

# Check if branch name was provided
if [[ -z "$BRANCH_NAME" ]]; then
    echo "Error: Branch name is required"
    show_help
fi

# Source shell rc files to get environment variables
if [[ -f "$HOME/.zshrc" ]]; then
    source "$HOME/.zshrc"
fi
if [[ -f "$HOME/.bashrc" ]]; then
    source "$HOME/.bashrc"
fi

# Ask for agent number (default to 1 if empty)
# Check if agent number was provided as argument or environment variable
if [ -n "$AGENT_NUM" ]; then
    AGENT_NUMBER=$AGENT_NUM
elif [ -n "$1" ] && [[ ! "$1" =~ ^-- ]]; then
    # First non-option argument is agent number
    AGENT_NUMBER=$1
    shift
else
    echo "Which agent number are you using? (e.g., 1 for GITHUB_AGENT1_TOKEN, default: 1)"
    read AGENT_INPUT
    if [[ -z "$AGENT_INPUT" ]]; then
        AGENT_NUMBER=1
        echo "No agent number chosen: defaulting to agent 1"
    else
        AGENT_NUMBER=$AGENT_INPUT
    fi
fi

# Generate dynamic Shuru configuration based on agent number
"$PWD/shuru-template.sh" "$AGENT_NUMBER"

# Use the generated config for autonomous operation
export OPENCODE_CONFIG="$PWD/opencode.auto.json"

# Validate agent number is a positive integer
if ! [[ "$AGENT_NUMBER" =~ ^[0-9]+$ ]] || [ "$AGENT_NUMBER" -lt 1 ]; then
    echo "Error: Agent number must be a positive integer"
    exit 1
fi

# Construct the token variable name
TOKEN_VAR="GITHUB_AGENT${AGENT_NUMBER}_TOKEN"

# Check if the token variable is set
if [[ -z "${!TOKEN_VAR}" ]]; then
    echo "Error: $TOKEN_VAR is not set"
    echo ""
    echo "To fix this:"
    echo "  1. Create a fine-grained token with:"
    echo "     - Contents: read/write"
    echo "     - Pull requests: read/write"
    echo "  2. Add to your ~/.zshrc or ~/.bashrc:"
    echo "     export $TOKEN_VAR='your_token_here'"
    echo "  3. Source your shell config: source ~/.zshrc"
    exit 1
fi

# Check if we're already in a git worktree
# More reliable way to check if we're in a linked worktree
if [[ "$(git rev-parse --is-inside-work-tree 2>/dev/null)" == "true" && 
      "$(git rev-parse --is-inside-git-dir 2>/dev/null)" != "true" ]]; then
    # Check if it's a linked worktree (not the main working tree)
    if git rev-parse --show-superproject-working-tree >/dev/null 2>&1; then
        IN_WORKTREE=true
    else
        IN_WORKTREE=false
    fi
else
    IN_WORKTREE=false
fi

if [[ "$IN_WORKTREE" == "true" && "$FORCE_WORKTREE" == "false" ]]; then
    echo "Warning: You are currently in a git worktree."
    echo "Creating a new worktree will not affect your current worktree."
    echo ""
    echo "Your current work will remain intact in your existing worktree."
    echo ""
    read -p "Do you want to continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
        echo "Operation cancelled."
        exit 0
    fi
fi

# Get the token value
TOKEN_VALUE="${!TOKEN_VAR}"

# 1. Make the work tree
echo "Creating worktree for branch: $BRANCH_NAME"
git worktree add ../$BRANCH_NAME -b $BRANCH_NAME

# 2. Change to the new worktree directory
cd ../$BRANCH_NAME

# 3. Set local git rule for the token
git config --local url."https://${TOKEN_VALUE}@github.com/".insteadOf "git@github.com:"

# 4. Start the Shuru microVM with the specific token
echo "Starting Shuru microVM with agent ${AGENT_NUMBER} token..."
shuru run

# Inform user of their location
echo ""
echo "Switched to new worktree at: $(pwd)"
echo "To return to the main repository later, use: cd -"
echo ""
echo "Shuru configuration has been set up for agent $AGENT_NUMBER"
echo "You can now run 'shuru' directly in this workspace"
echo "A marker file 'shuru.sh' has been created to indicate the setup is complete"
echo "To update the configuration for a different agent, re-run: ../skunkagent/run-agent.sh $BRANCH_NAME"

# Create marker file to indicate Shuru is configured
touch shuru.sh
chmod +x shuru.sh