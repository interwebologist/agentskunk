#!/usr/bin/env python3
"""Bash Tool - Run bash commands."""

import json
import subprocess
from tools.registry import registry


def run_bash(command: str) -> str:
    """Run a bash command."""
    try:
        r = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=300
        )
        status = "SUCCESS" if r.returncode == 0 else "ERROR"
        output = r.stdout + r.stderr

        result = {
            "status": status,
            "exit_code": r.returncode,
            "output": output[:1000] if len(output) > 1000 else output,
        }

        if len(output) > 1000:
            import os
            import uuid

            os.makedirs("outputs", exist_ok=True)
            path = f"outputs/{uuid.uuid4().hex[:8]}.log"
            with open(path, "w") as f:
                f.write(output)
            result["full_log_saved"] = path

        return json.dumps(result)
    except subprocess.TimeoutExpired:
        return json.dumps(
            {"status": "ERROR", "error": "Command timed out after 300 seconds"}
        )
    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})


RUN_BASH_SCHEMA = {
    "name": "run_bash",
    "description": "Run a bash command. Returns output and exit code.",
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The bash command to execute",
            }
        },
        "required": ["command"],
    },
}

registry.register(
    name="run_bash",
    toolset="system",
    schema=RUN_BASH_SCHEMA,
    handler=lambda args, **kw: run_bash(command=args.get("command", "")),
    check_fn=None,
    emoji="⚙️",
)
