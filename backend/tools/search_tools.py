"""
Search Tools — Wikipedia only.
Custom Search replaced by Gemini Search Grounding in ResearchAgent.
"""
import requests


def wikipedia_search(topic: str) -> dict:
    """Search Wikipedia for articles matching a topic."""
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {"action": "query", "list": "search", "srsearch": topic, "srlimit": 5, "format": "json"}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        results = []
        for item in data.get("query", {}).get("search", []):
            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", ""),
            })
        return {"status": "success", "topic": topic, "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def wikipedia_summary(title: str) -> dict:
    """Get summary of a specific Wikipedia article."""
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
        response = requests.get(url, timeout=10)
        data = response.json()
        return {
            "status": "success",
            "title": data.get("title", ""),
            "summary": data.get("extract", ""),
            "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}