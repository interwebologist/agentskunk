import time
import uuid
import json
import os
from typing import List, Optional, Union
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import agent
from agent import run, guardrails, TOOL_REGISTRY
from state import SimpleSessionDB
from tools.registry import registry, discover_builtin_tools

# Trigger auto-discovery of tools
discover_builtin_tools()

app = FastAPI(title="OpenAI-Compatible Agent API")

session_db = SimpleSessionDB()


# --- HITL Request Schemas ---
class HITLApprovalRequest(BaseModel):
    tool_name: str
    tool_args: dict
    session_id: str
    user_id: Optional[str] = None


class HITLApprovalResponse(BaseModel):
    approved: bool
    tool_name: str
    timestamp: int


hitl_approvals: dict[str, dict] = {}


@app.post("/v1/hitl/approve")
async def hitl_approve(request: HITLApprovalRequest):
    """HITL approval endpoint for API calls."""
    if os.getenv("HITL_ENABLED", "true").lower() not in ("true", "1", "yes"):
        raise HTTPException(status_code=403, detail="HITL is disabled")

    tool_cfg = TOOL_REGISTRY.get(request.tool_name, {})
    if tool_cfg.get("risk") != "high":
        raise HTTPException(status_code=400, detail="Tool does not require approval")

    key = f"{request.session_id}:{request.tool_name}"
    if key not in hitl_approvals:
        raise HTTPException(status_code=404, detail="Approval request not found")

    approval_data = hitl_approvals.pop(key)
    if approval_data["tool_args"] != request.tool_args:
        raise HTTPException(status_code=400, detail="Tool arguments mismatch")

    return HITLApprovalResponse(
        approved=True, tool_name=request.tool_name, timestamp=int(time.time())
    )


@app.get("/v1/hitl/pending")
async def hitl_pending(session_id: str, user_id: Optional[str] = None):
    """Get pending HITL approvals for a session."""
    if os.getenv("HITL_ENABLED", "true").lower() not in ("true", "1", "yes"):
        return {"pending": []}

    pending = [
        {"session_id": k.split(":")[0], "tool_name": k.split(":")[1], **v}
        for k, v in hitl_approvals.items()
        if k.startswith(f"{session_id}:")
    ]
    return {"pending": pending}


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


def check_tool_approvals(
    messages: List[ChatMessage], session_id: str
) -> Optional[dict]:
    """Check if any tool calls require approval and store for later approval."""
    if os.getenv("HITL_ENABLED", "true").lower() not in ("true", "1", "yes"):
        return None

    last_msg = messages[-1]
    if not last_msg.content:
        return None

    try:
        data = json.loads(last_msg.content)
        if isinstance(data, dict) and "tool_calls" in data:
            for call in data["tool_calls"]:
                if call.get("type") == "function":
                    func_name = call["function"]["name"]
                    tool_cfg = TOOL_REGISTRY.get(func_name, {})
                    if tool_cfg.get("risk") == "high":
                        args = json.loads(call["function"]["arguments"])
                        key = f"{session_id}:{func_name}"
                        hitl_approvals[key] = {
                            "tool_args": args,
                            "tool_call_id": call.get("id"),
                            "timestamp": int(time.time()),
                        }
                        return {
                            "tool_name": func_name,
                            "tool_args": args,
                            "tool_call_id": call.get("id"),
                            "session_id": session_id,
                        }
    except (json.JSONDecodeError, KeyError):
        pass

    return None
@app.get("/v1/tools", response_model=List[dict])
async def list_tools():
    """List all available tools in OpenAI format."""
    tool_names = set(registry.get_all_tool_names())
    return registry.get_definitions(tool_names=tool_names)


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
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

        approval_info = check_tool_approvals(request.messages, session_id)
        if approval_info:
            raise HTTPException(
                status_code=202,
                detail={
                    "message": "Tool requires human approval",
                    "approval_endpoint": "/v1/hitl/approve",
                    "pending_approval": approval_info,
                },
            )

        def api_approval_func(func_name: str, args: dict) -> bool:
            key = f"{session_id}:{func_name}"
            return key not in hitl_approvals

        response_text = run(user_prompt, require_approval=api_approval_func)

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
