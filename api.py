import time
import uuid
import json
import os
from typing import List, Optional, Union
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import agent
from agent import run, guardrails
from state import SimpleSessionDB
from tools.registry import registry, discover_builtin_tools

# Trigger auto-discovery of tools
discover_builtin_tools()

app = FastAPI(title="OpenAI-Compatible Agent API")

session_db = SimpleSessionDB()


# --- OpenAI Request Schemas ---
class ChatMessage(BaseModel):
    role: str
    content: str
    name: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    user: Optional[str] = None


# --- OpenAI Response Schemas ---
class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = "stop"


class ChatCompletionResponseUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:12]}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChatCompletionResponseChoice]
    usage: ChatCompletionResponseUsage


class ModelObject(BaseModel):
    id: str
    object: str = "model"
    created: int = Field(default_factory=lambda: int(time.time()))
    owned_by: str = "agent"


class ModelList(BaseModel):
    object: str = "list"
    data: List[ModelObject]


@app.get("/v1/models", response_model=ModelList)
async def list_models():
    models_data = []
    try:
        if os.path.exists("models.json"):
            with open("models.json", "r") as f:
                data = json.load(f)
                for provider in data.get("providers", {}).values():
                    for m in provider.get("models", []):
                        models_data.append(ModelObject(id=m.get("id")))
    except Exception:
        pass

    if not models_data:
        models_data.append(ModelObject(id=getattr(agent, "model", "default-model")))

    return ModelList(data=models_data)


@app.get("/v1/tools", response_model=List[dict])
async def list_tools():
    """List all available tools in OpenAI format."""
    tool_names = set(registry.get_all_tool_names())
    return registry.get_definitions(tool_names=tool_names)


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest) -> ChatCompletionResponse:
    try:
        session_id = request.user or "default"

        if guardrails.is_kill_switch_triggered():
            kill_result = guardrails.trigger_kill_switch()
            raise HTTPException(
                status_code=503,
                detail=f"Service unavailable: Kill switch activated. {kill_result}",
            )

        db_messages = session_db.get_messages(session_id)
        agent.CHAT_HISTORY = db_messages

        if not request.messages:
            raise HTTPException(
                status_code=400, detail="Messages array cannot be empty"
            )

        for msg in request.messages[:-1]:
            session_db.append_message(session_id, msg.role, msg.content)

        user_prompt = request.messages[-1].content

        is_blocked, block_msg, block_type = guardrails.validate_input(user_prompt)
        if is_blocked:
            guardrails.trigger_kill_switch()
            raise HTTPException(
                status_code=403, detail=f"Input blocked [{block_type}]: {block_msg}"
            )

        response_text = run(user_prompt)

        session_db.append_message(session_id, "user", user_prompt)
        session_db.append_message(session_id, "assistant", response_text)

        prompt_tokens = sum(len(m.content) for m in request.messages) // 4
        completion_tokens = len(response_text) // 4

        return ChatCompletionResponse(
            model=request.model,
            choices=[
                ChatCompletionResponseChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=response_text),
                    finish_reason="stop",
                )
            ],
            usage=ChatCompletionResponseUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
