import time
import uuid
import json
import os
from typing import List, Optional, Union
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import agent
from agent import run

app = FastAPI(title="OpenAI-Compatible Agent API")


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


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    try:
        # OpenAI API is stateless, but our agent has a global history.
        # We sync the global history with what's provided in the request.
        # We set CHAT_HISTORY to all messages except the last one,
        # because run() will append the prompt.
        agent.CHAT_HISTORY = [
            m.model_dump(exclude_none=True) for m in request.messages[:-1]
        ]

        user_prompt = request.messages[-1].content
        response_text = run(user_prompt)

        # Simple token estimation
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
