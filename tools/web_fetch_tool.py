"""Web Fetch Tool - Fetch URLs and return Markdown content."""

import json
import re
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from tools.registry import registry


def web_fetch(url: str) -> str:
    """Fetches a URL, converts GitHub links to raw, cleans HTML, and returns Markdown."""
    github_pattern = r"https?://(?:www\.)?github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.*)"

    if "github.com" in url and "/blob/" in url:
        match = re.match(github_pattern, url)
        if match:
            user, repo, branch, filepath = match.groups()
            raw_url = (
                f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{filepath}"
            )
            try:
                response = requests.get(
                    raw_url, headers={"User-Agent": "Claude-User"}, timeout=10
                )
                if response.status_code == 200:
                    ext = filepath.split(".")[-1] if "." in filepath else ""
                    return json.dumps(
                        {
                            "url": url,
                            "raw_url": raw_url,
                            "content": f"```{ext}\n{response.text}\n```",
                        }
                    )
            except Exception:
                pass

    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": "Claude-User",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            timeout=10,
        )
        if response.status_code != 200:
            return json.dumps({"error": f"Error: {response.status_code}"})

        soup = BeautifulSoup(response.text, "html.parser")
        for el in soup(
            ["script", "style", "nav", "footer", "header", "aside", "svg", "form"]
        ):
            el.decompose()

        markdown = md(str(soup), strip=["img", "button"], heading_style="atx").strip()
        return json.dumps({"url": url, "content": markdown})
    except Exception as e:
        return json.dumps({"error": f"Error: {str(e)}"})


WEB_FETCH_SCHEMA = {
    "name": "web_fetch",
    "description": "Fetch a URL and return clean Markdown content. Detects GitHub links and gets raw code.",
    "parameters": {
        "type": "object",
        "properties": {"url": {"type": "string", "description": "The URL to fetch"}},
        "required": ["url"],
    },
}

registry.register(
    name="web_fetch",
    toolset="web",
    schema=WEB_FETCH_SCHEMA,
    handler=lambda args, **kw: web_fetch(url=args.get("url", "")),
    check_fn=None,
    emoji="📄",
)
