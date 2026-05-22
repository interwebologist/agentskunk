"""Google Search Tool - Serpbase.dev search."""

import json
import os
import requests
from tools.registry import registry


def google_search(q: str, num: int = 10) -> str:
    """Official Serpbase.dev (Serper) Google Search tool."""
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": q, "num": num})
    headers = {
        "X-API-KEY": os.getenv("SERPBASE_API_KEY"),
        "Content-Type": "application/json",
    }
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status()
        data = response.json()
        results = data.get("organic", [])
        if not results:
            return json.dumps({"error": "No organic results found."})
        output = []
        for r in results:
            output.append(
                {
                    "title": r.get("title", ""),
                    "link": r.get("link", ""),
                    "snippet": r.get("snippet", ""),
                }
            )
        return json.dumps({"query": q, "results": output})
    except Exception as e:
        return json.dumps({"error": f"Serpbase Error: {str(e)}"})


GOOGLE_SEARCH_SCHEMA = {
    "name": "google_search",
    "description": "Search Google using Serpbase.dev (Serper). Requires SERPBASE_API_KEY environment variable.",
    "parameters": {
        "type": "object",
        "properties": {
            "q": {"type": "string", "description": "The search query"},
            "num": {
                "type": "integer",
                "description": "Number of results",
                "default": 10,
            },
        },
        "required": ["q"],
    },
}

registry.register(
    name="google_search",
    toolset="web",
    schema=GOOGLE_SEARCH_SCHEMA,
    handler=lambda args, **kw: google_search(
        q=args.get("q", ""), num=args.get("num", 10)
    ),
    check_fn=None,
    emoji="🔍",
)
