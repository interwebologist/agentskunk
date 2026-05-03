from typing import Annotated, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# 1. Define the State
class AgentState(TypedDict):
    """
    The state of our agent. 
    'messages' uses add_messages to append new messages rather than overwriting.
    """
    messages: Annotated[list[BaseMessage], add_messages]

# 2. Define the Tools
@tool
def get_weather(location: str):
    """Returns current weather and 24h forecast for a given location."""
    geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1").json()
    if not geo.get("results"): return f"Location {location} not found."
    res = geo["results"][0]
    w = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={res['latitude']}&longitude={res['longitude']}&current_weather=true&hourly=temperature_2m&forecast_hours=25&temperature_unit=fahrenheit&timezone=auto").json()
    now = w["current_weather"]["temperature"]
    future = w["hourly"]["temperature_2m"][-1]
    return f"Weather in {res['name']}: Now {now}°F, 24h forecast {future}°F."

tools = [get_weather]
tool_node = ToolNode(tools)

# 3. Define the Agent (LLM) logic
# Note: In a real scenario, you'd need an API key set in your environment.
model = ChatOpenAI(
    model=os.getenv("MODEL_NAME", "NVIDIA-Nemotron-3-Super-120B-A12B-UD-Q4_K_XL.gguf"),
    openai_api_base=os.getenv("OPENAI_API_BASE", "http://192.168.1.33:8080/v1"),
    openai_api_key=os.getenv("OPENAI_API_KEY", "not-needed")
).bind_tools(tools)

def call_model(state: AgentState):
    """Calls the LLM with the current list of messages."""
    messages = state["messages"]
    response = model.invoke(messages)
    return {"messages": [response]}

# 4. Define the Routing logic
def should_continue(state: AgentState):
    """
    Determines whether to continue to the tool node or end.
    Checks if the last message contains tool calls.
    """
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END

# 5. Build the Graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

# Set entry point
workflow.add_edge(START, "agent")

# Add conditional edges
workflow.add_conditional_edges(
    "agent",
    should_continue,
)

# Add edge from tools back to agent to allow for observation/reaction
workflow.add_edge("tools", "agent")

# Compile the graph
app = workflow.compile()

# 6. Execution Example
if __name__ == "__main__":
    inputs = {"messages": [("user", "What is the weather in New York?")]}
    for output in app.stream(inputs):
        for key, value in output.items():
            print(f"Output from node '{key}':")
            print(value)
            print("---")
