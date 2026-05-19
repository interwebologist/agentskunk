"""File Tool Module - read_file tool."""

import json
from pathlib import Path
from tools.registry import registry


def read_file(path: str) -> str:
    """Read a file."""
    try:
        p = Path(path).expanduser()
        with open(p, "r") as f:
            content = f.read()
        return json.dumps({"path": str(p), "content": content})
    except Exception as e:
        return json.dumps({"error": str(e)})


READ_FILE_SCHEMA = {
    "name": "read_file",
    "description": "Read a text file. Returns the file contents as JSON with path and content fields.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to read (absolute or relative)",
            }
        },
        "required": ["path"],
    },
}

registry.register(
    name="read_file",
    toolset="file",
    schema=READ_FILE_SCHEMA,
    handler=lambda args, **kw: read_file(path=args.get("path", "")),
    check_fn=None,
    emoji="📖",
)
