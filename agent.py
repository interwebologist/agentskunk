import os
import json
import uuid
from typing import List, Any
from dotenv import load_dotenv
from openai import OpenAI
from tools.registry import registry, discover_builtin_tools

# Trigger auto-discovery of tools
discover_builtin_tools()

load_dotenv()

client = OpenAI(
    base_url=os.getenv("OPENAI_API_BASE", "http://192.168.1.33:8080/v1"),
    api_key=os.getenv("OPENAI_API_KEY", "not-needed"),
)
model = os.getenv("MODEL_NAME", "NVIDIA-Nemotron-3-Super-120B-A12B-UD-Q4_K_XL.gguf")


def process_result(output: str, exit_code: int, limit: int = 1000) -> str:
    status = "SUCCESS" if exit_code == 0 else "ERROR"

    if len(output) > limit:
        os.makedirs("outputs", exist_ok=True)
        path = f"outputs/{uuid.uuid4().hex[:8]}.log"
        with open(path, "w") as f:
            f.write(output)
        return f"{status}: {output[:limit]}... [FULL LOG SAVED TO {path}]"

    return f"{status}: {output}" if output else status


# Global Configuration & State
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "90"))
CHAT_HISTORY: List[Any] = []


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

    # Initialize history with system prompt if empty
    if not CHAT_HISTORY:
        sys_p = load_system_prompt()
        if sys_p:
            CHAT_HISTORY.append({"role": "system", "content": sys_p})

    CHAT_HISTORY.append({"role": "user", "content": prompt})

    iterations = 0
    while iterations < max_iterations:
        iterations += 1

        # Get tool definitions from registry
        tool_names = set(registry.get_all_tool_names())
        tools = registry.get_definitions(tool_names=tool_names)

        res = client.chat.completions.create(
            model=model, messages=CHAT_HISTORY, tools=tools
        )  # type: ignore
        msg = res.choices[0].message

        # Convert message to dict to keep history consistent and avoid mypy errors
        CHAT_HISTORY.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            return str(msg.content)

        for call in msg.tool_calls:
            if call.type == "function":
                func_name = call.function.name
                try:
                    args = json.loads(call.function.arguments)
                    # Use registry.dispatch() instead of TOOL_REGISTRY lookup
                    out = registry.dispatch(func_name, args)
                    CHAT_HISTORY.append(
                        {"role": "tool", "tool_call_id": call.id, "content": out}
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
