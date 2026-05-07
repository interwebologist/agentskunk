#!/bin/bash
# Usage: ./taskloop.sh <iterations>
set -e

for ((i=1; i<=$1; i++)); do
  # We run inside the docker sandbox for safety
  result=$(opencode --permission-mode acceptEdits -p \
    "@spec.md @status.txt \
    1. Read the spec.md and status file. \
    2. Identify the next highest-priority task. \
    3. Implement it, run tests/linting, and commit changes. \
    4. Update progress.txt. \
    ONLY DO ONE TASK. If all tasks are done, output <promise>COMPLETE</promise>.")

  echo "$result"
  
  if [[ "$result" == *"<promise>COMPLETE</promise>"* ]]; then
    echo "Task fully completed after $i loops."
    exit 0
  fi
done
