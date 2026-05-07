#!/bin/bash
# Usage: ./.loop.sh <iterations>
set -e
iterations=${1:-40}  # Default to 40 iterations if not provided

# Initialize variables for loop detection
prev_result=""
prev_prev_result=""

for ((i=1; i<=iterations; i++)); do
  # Build the prompt, adding loop detection message if needed
  prompt="@.plan.md @.stat.txt \
    1. Read the .plan.md and .stat.txt file \
    2. Id the next highest-priority task. \
    3. Implement it, run tests/linting, and commit changes. \
    4. Update .stat.txt. \
    ONLY DO ONE TASK. If all tasks are done, output <promise>COMPLETE</promise>."
    
  # Add loop detection warning if last two results were the same
  if [[ "$prev_result" == "$prev_prev_result" && "$prev_result" != "" ]]; then
    prompt="$prompt
    
    IMPORTANT: You tried the exact same thing twice in the last two iterations. You must now try something different to make progress."
  fi
  
  result=$(opencode run --dangerously-skip-permissions "$prompt")
  
  echo "$result"
   
  # Check for completion
  if [[ "$result" == *"<promise>COMPLETE</promise>"* ]]; then
    echo "Task fully completed after $i loops."
    exit 0
  fi
  
  # Shift results for loop detection (keep track of last two results)
  prev_prev_result="$prev_result"
  prev_result="$result"
done
