"""Web Search Tool - DuckDuckGo search."""

import json
from tools.registry import registry


def web_search(query: str, max_results: int = 3) -> str:
    """Searches the web using DuckDuckGo and returns the top results."""
    try:
        from ddgs import DDGS

        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=max_results)]
            if not results:
                return json.dumps({"error": "No results found."})

            formatted_results = []
            for r in results:
                formatted_results.append(
                    {
                        "title": r.get("title", ""),
                        "snippet": r.get("body", ""),
                        "url": r.get("href", ""),
                    }
                )

            return json.dumps({"query": query, "results": formatted_results})
    except ImportError:
        return json.dumps(
            {"error": "ddgs package not installed. Install with: pip install ddgs"}
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


def check_web_search_requirements() -> bool:
    """Check if ddgs package is installed."""
    try:
        import importlib.util

        return importlib.util.find_spec("ddgs") is not None
    except ImportError:
        return False


WEB_SEARCH_SCHEMA = {
    "name": "web_search",
    "description": "Search the web using DuckDuckGo. Returns search results with title, snippet, and URL.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query"},
            "max_results": {
                "type": "integer",
                "description": "Number of results to return",
                "default": 3,
            },
        },
        "required": ["query"],
    },
}

registry.register(
    name="web_search",
    toolset="web",
    schema=WEB_SEARCH_SCHEMA,
    handler=lambda args, **kw: web_search(
        query=args.get("query", ""), max_results=args.get("max_results", 3)
    ),
    check_fn=check_web_search_requirements,
    emoji="🌐",
)
