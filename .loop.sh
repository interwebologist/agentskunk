#!/bin/bash
# Usage: ./.loop.sh <iterations>
set -e
for ((i=1; i<=$1; i++)); do
  result=$(opencode --yes -p 
    "@.plan.md @.stat.txt \
    1. Read the .plan.md and .stat.txt file \
    2. Id the next highest-priority task. \
    3. Implement it, run tests/linting, and commit changes. \
    4. Update .stat.txt. \
    ONLY DO ONE TASK. If all tasks are done, output <promise>COMPLETE</promise>.")

  echo "$result"
  
  if [[ "$result" == *"<promise>COMPLETE</promise>"* ]]; then
    echo "Task fully completed after $i loops."
    exit 0
  fi
done
