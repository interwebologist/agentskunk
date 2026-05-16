import requests
import os
import json
import subprocess
import uuid
import re
from dotenv import load_dotenv
from openai import OpenAI
from ddgs import DDGS
from bs4 import BeautifulSoup
from markdownify import markdownify as md

load_dotenv()

client = OpenAI(
    base_url=os.getenv("OPENAI_API_BASE", "http://192.168.1.33:8080/v1"),
    api_key=os.getenv("OPENAI_API_KEY", "not-needed")
)
model = os.getenv("MODEL_NAME", "NVIDIA-Nemotron-3-Super-120B-A12B-UD-Q4_K_XL.gguf")

def process_result(output: str, exit_code: int, limit: int = 1000) -> str:
    status = "SUCCESS" if exit_code == 0 else "ERROR"
    
    if len(output) > limit:
        os.makedirs("outputs", exist_ok=True)
        path = f"outputs/{uuid.uuid4().hex[:8]}.log"
        with open(path, "w") as f: f.write(output)
        return f"{status}: {output[:limit]}... [FULL LOG SAVED TO {path}]"
    
    return f"{status}: {output}" if output else status

def run_bash(command: str) -> str:
    """Run a bash command."""
    r = subprocess.run(command, shell=True, capture_output=True, text=True)
    return process_result(r.stdout + r.stderr, r.returncode)

def read_file(path: str) -> str:
    """Read a file."""
    try:
        with open(path, "r") as f: return f.read()
    except Exception as e: return f("[ERROR] {str(e)}")


def weather(loc: str):
    """Get weather for location."""
    geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={loc}&count=1").json()
    if not geo.get("results"): return f"{loc} not found."
    res = geo["results"][0]
    w = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={res['latitude']}&longitude={res['longitude']}&current_weather=true&hourly=temperature_2m&forecast_hours=25&temperature_unit=fahrenheit&timezone=auto").json()
    now = w["current_weather"]["temperature"]
    future = w["hourly"]["temperature_2m"][-1]
    return f"{res['name']}: Now {now}F, 24h {future}F."

def web_search(query: str, max_results: int = 3) -> str:
    """Searches the web using DuckDuckGo and returns the top results."""
    with DDGS() as ddgs:
        results = [r for r in ddgs.text(query, max_results=max_results)]
        if not results:
            return "No results found."
        
        formatted_results = []
        for r in results:
            formatted_results.append(f"Title: {r['title']}\nSnippet: {r['body']}\nSource: {r['href']}")
        
        return "\n\n".join(formatted_results)

def google_search(q: str, num: int = 10) -> str:
    """Official Serpbase.dev (Serper) Google Search tool."""
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": q, "num": num})
    headers = {
        'X-API-KEY': os.getenv("SERPBASE_API_KEY"),
        'Content-Type': 'application/json'
    }
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status()
        data = response.json()
        results = data.get("organic", [])
        if not results: return "No organic results found."
        output = [f"Title: {r.get('title')}\nLink: {r.get('link')}\nSnippet: {r.get('snippet')}" for r in results]
        return "\n\n".join(output)
    except Exception as e:
        return f"Serpbase Error: {str(e)}"

def web_fetch(url: str) -> str:
    """Fetches a URL, converts GitHub links to raw, cleans HTML, and returns Markdown."""
    github_pattern = r"https?://(?:www\.)?github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.*)"
    
    if "github.com" in url and "/blob/" in url:
        match = re.match(github_pattern, url)
        if match:
            user, repo, branch, filepath = match.groups()
            raw_url = f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{filepath}"
            try:
                response = requests.get(raw_url, headers={"User-Agent": "Claude-User"}, timeout=10)
                if response.status_code == 200:
                    ext = filepath.split('.')[-1] if '.' in filepath else ''
                    return f"```{ext}\n{response.text}\n```"
            except Exception: pass

    try:
        response = requests.get(url, headers={
            "User-Agent": "Claude-User",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }, timeout=10)
        if response.status_code != 200: return f"Error: {response.status_code}"
        
        soup = BeautifulSoup(response.text, "html.parser")
        for el in soup(["script", "style", "nav", "footer", "header", "aside", "svg", "form"]):
            el.decompose()
            
        return md(str(soup), strip=['img', 'button'], heading_style="atx").strip()
    except Exception as e:
        return f"Error: {str(e)}"

# Tool Registry
TOOL_REGISTRY = {
    "run_bash": {
        "func": run_bash,
        "description": "Run a bash command",
        "parameters": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"]
        }
    },
    "read_file": {
        "func": read_file,
        "description": "Read a file",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"]
        }
    },
    "weather": {
        "func": weather,
        "description": "Get weather for a location",
        "parameters": {
            "type": "object",
            "properties": {"loc": {"type": "string"}},
            "required": ["loc"]
        }
    },
    "web_search": {
        "func": web_search,
        "description": "Search the web with DuckDuckGo",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_results": {"type": "integer", "default": 3}
            },
            "required": ["query"]
        }
    },
    "google_search": {
        "func": google_search,
        "description": "Search Google using Serpbase.dev",
        "parameters": {
            "type": "object",
            "properties": {
                "q": {"type": "string", "description": "The search query"},
                "num": {"type": "integer", "description": "Number of results", "default": 5}
            },
            "required": ["q"]
        }
    },
    "web_fetch": {
        "func": web_fetch,
        "description": "Fetch a URL and return clean Markdown content. Detects GitHub links and gets raw code.",
        "parameters": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"]
        }
    }
}

# Generate OpenAI tools list
tools = [
    {
        "type": "function",
        "function": {
            "name": name,
            "description": cfg["description"],
            "parameters": cfg["parameters"]
        }
    }
    for name, cfg in TOOL_REGISTRY.items()
]

def run(prompt: str):
    msgs = [{"role": "user", "content": prompt}]
    while True:
        res = client.chat.completions.create(model=model, messages=msgs, tools=tools)
        msg = res.choices[0].message
        msgs.append(msg)

        if not msg.tool_calls:
            return msg.content

        for call in msg.tool_calls:
            func_name = call.function.name
            if func_name in TOOL_REGISTRY:
                args = json.loads(call.function.arguments)
                out = TOOL_REGISTRY[func_name]["func"](**args)
                msgs.append({"role": "tool", "tool_call_id": call.id, "content": out})

if __name__ == "__main__":
    print(run("Run a bash command that fails and outputs a lot of text."))
