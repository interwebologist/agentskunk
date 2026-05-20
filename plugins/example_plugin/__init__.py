"""Example plugin demonstrating tool registration via ctx.register_tool()."""

import json
from tools.registry import registry


def register(ctx) -> None:
    """Register the example plugin's tools."""

    def example_plugin_tool(**kwargs) -> str:
        """Example plugin tool."""
        return json.dumps({"result": "plugin tool works"})

    registry.register(
        name="example_plugin_tool",
        toolset="example",
        schema={
            "name": "example_plugin_tool",
            "description": "Example plugin tool demonstrating the plugin pattern",
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "Optional input parameter",
                    }
                },
                "required": [],
            },
        },
        handler=lambda args, **kw: example_plugin_tool(**args),
        check_fn=None,
    )
