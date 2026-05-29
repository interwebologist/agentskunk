import os
import json
import logging
from typing import Any
from dotenv import load_dotenv
from openai import OpenAI, InternalServerError
from tools.registry import registry, discover_builtin_tools

from guardrails import create_guardrails, Guardrails

from tools.memory.store import MemoryStore

logger = logging.getLogger(__name__)

discover_builtin_tools()
load_dotenv()

guardrails: Guardrails = create_guardrails()

client = OpenAI(
    base_url=os.getenv("OPENAI_API_BASE", "http://192.168.1.33:8080/v1"),
    api_key=os.getenv("OPENAI_API_KEY", "not-needed"),
)
model = os.getenv("MODEL_NAME", "NVIDIA-Nemotron-3-Super-120B-A12B-UD-Q4_K_XL.gguf")

CHAT_HISTORY: list[dict[str, Any]] = []

MAX_ITERATIONS = 300


def load_system_prompt() -> str:
    """Load system prompt from environment variable or file."""
    env_prompt = os.getenv("SYSTEM_PROMPT")
    if env_prompt:
        return env_prompt.strip()

    path = "prompts/system_prompt.md"
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read().strip()
    return ""


def run(prompt: str, max_iterations: int = MAX_ITERATIONS) -> str:
    global CHAT_HISTORY

    if guardrails.is_kill_switch_triggered():
        kill_result = guardrails.trigger_kill_switch()
        return f"ERROR: Kill switch activated. {kill_result}"

    is_blocked, block_msg, block_type = guardrails.validate_input(prompt)
    if is_blocked:
        guardrails.trigger_kill_switch()
        return f"ERROR: Input blocked [{block_type}]: {block_msg}"

    if not CHAT_HISTORY:
        sys_p = load_system_prompt()
        if sys_p:
            CHAT_HISTORY.append({"role": "system", "content": sys_p})

    CHAT_HISTORY.append({"role": "user", "content": prompt})

    iterations = 0
    while iterations < max_iterations:
        if guardrails.is_kill_switch_triggered():
            kill_result = guardrails.trigger_kill_switch()
            return f"ERROR: Kill switch activated during execution. {kill_result}"

        iterations += 1
        tools = registry.get_definitions(set(registry.get_all_tool_names()), quiet=True)
        try:
            res = client.chat.completions.create(
                model=model, messages=CHAT_HISTORY, tools=tools
            )
        except InternalServerError as e:
            logger.error("OpenAI API error: %s", str(e), exc_info=True)
            if "Failed to parse tool call arguments as JSON" in str(e):
                error_msg = "JSON parsing error: The model returned malformed JSON for tool arguments. Please reformat your request."
                CHAT_HISTORY.append(
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "error_tool_call",
                                "type": "function",
                                "function": {
                                    "name": "error_handler",
                                    "arguments": "{}",
                                },
                            }
                        ],
                    }
                )
                CHAT_HISTORY.append(
                    {
                        "role": "tool",
                        "tool_call_id": "error_tool_call",
                        "content": json.dumps({"error": error_msg}),
                    }
                )
                return error_msg
            raise
        msg = res.choices[0].message

        CHAT_HISTORY.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            return str(msg.content)

        for call in msg.tool_calls:
            if call.type == "function":
                func_name = call.function.name
                try:
                    args = json.loads(call.function.arguments)
                    out = registry.dispatch(func_name, args)
                    CHAT_HISTORY.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.id,
                            "content": out,
                        }
                    )
                except Exception as e:
                    CHAT_HISTORY.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.id,
                            "content": f"Error: {str(e)}",
                        }
                    )

    return "Error: Maximum iterations reached without final response."


def on_session_end() -> None:
    """Auto-extract facts from conversation at session end."""
    global CHAT_HISTORY
    try:
        store = MemoryStore(db_path="~/.skunk/state.db")
        extracted = store.auto_extract_facts(CHAT_HISTORY)
        if extracted > 0:
            print(f"Auto-extracted {extracted} facts from session")
    except Exception as e:
        print(f"Auto-extraction failed: {e}")


if __name__ == "__main__":
    print(run("Run a bash command that fails and outputs a lot of text."))
