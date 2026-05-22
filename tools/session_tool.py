"""Session Tool - Clear conversation history."""

import json
from tools.registry import registry


def clear_topic(new_topic: str = "") -> str:
    """Clears the conversation history (except system prompt) and starts a new topic if provided."""
    import agent

    sys_prompt = None
    if agent.CHAT_HISTORY and agent.CHAT_HISTORY[0].get("role") == "system":
        sys_prompt = agent.CHAT_HISTORY[0]

    agent.CHAT_HISTORY = []
    if sys_prompt:
        agent.CHAT_HISTORY.append(sys_prompt)

    result = {"topic_cleared": True}
    if new_topic:
        result["new_topic"] = new_topic
        result["message"] = (
            f"Topic cleared. New topic: {new_topic}. Please start the conversation based on this."
        )
    else:
        result["message"] = (
            "Topic cleared. Conversation history has been reset. Waiting for next user input."
        )

    return json.dumps(result)


CLEAR_TOPIC_SCHEMA = {
    "name": "clear_topic",
    "description": "Clear the conversation history and start a new topic. Updates global CHAT_HISTORY state.",
    "parameters": {
        "type": "object",
        "properties": {
            "new_topic": {
                "type": "string",
                "description": "Optional: The new topic or query to start the conversation with after clearing.",
            }
        },
        "required": [],
    },
}

registry.register(
    name="clear_topic",
    toolset="session",
    schema=CLEAR_TOPIC_SCHEMA,
    handler=lambda args, **kw: clear_topic(new_topic=args.get("new_topic", "")),
    check_fn=None,
    emoji="🗑️",
)
