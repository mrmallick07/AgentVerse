"""
Search Tools — Google Custom Search + Wikipedia.
MCP tools for the ResearchAgent.
"""

import requests
from backend.tools.google_auth import GCP_API_KEY, SEARCH_ENGINE_ID


def web_search(query: str, num_results: int = 5) -> dict:
    """Search the web using Google Custom Search API.
    
    Args:
        query: The search query string.
        num_results: Number of results to return (max 10).
    
    Returns:
        A dict with a list of search results containing title, link, and snippet.
    """
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GCP_API_KEY,
            "cx": SEARCH_ENGINE_ID,
            "q": query,
            "num": min(num_results, 10),
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("items", []):
            results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
            })

        return {"status": "success", "query": query, "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def wikipedia_search(topic: str) -> dict:
    """Search Wikipedia for articles matching a topic.
    
    Args:
        topic: The topic to search for on Wikipedia.
    
    Returns:
        A dict with matching article titles and summaries.
    """
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": topic,
            "srlimit": 5,
            "format": "json",
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("query", {}).get("search", []):
            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", ""),
                "page_id": item.get("pageid"),
            })

        return {"status": "success", "topic": topic, "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def wikipedia_summary(title: str) -> dict:
    """Get a detailed summary of a specific Wikipedia article.
    
    Args:
        title: The exact title of the Wikipedia article.
    
    Returns:
        A dict containing the article title, summary text, and URL.
    """
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        return {
            "status": "success",
            "title": data.get("title", ""),
            "summary": data.get("extract", ""),
            "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
