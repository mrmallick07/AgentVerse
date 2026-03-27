"""
YouTube Tools — YouTube Data API v3.
MCP tools for the ResearchAgent.
"""

import requests
from backend.tools.google_auth import GCP_API_KEY


def search_youtube_videos(query: str, max_results: int = 5) -> dict:
    """Search YouTube for videos matching a query.
    
    Args:
        query: The search query for YouTube videos.
        max_results: Maximum number of results to return (max 10).
    
    Returns:
        A dict with a list of video results containing title, channel, view count, and URL.
    """
    try:
        # Step 1: Search for videos
        search_url = "https://www.googleapis.com/youtube/v3/search"
        search_params = {
            "key": GCP_API_KEY,
            "q": query,
            "part": "snippet",
            "type": "video",
            "maxResults": min(max_results, 10),
            "order": "relevance",
        }
        response = requests.get(search_url, params=search_params, timeout=10)
        response.raise_for_status()
        search_data = response.json()

        video_ids = []
        snippets = {}
        for item in search_data.get("items", []):
            vid_id = item["id"]["videoId"]
            video_ids.append(vid_id)
            snippets[vid_id] = item["snippet"]

        if not video_ids:
            return {"status": "success", "query": query, "results": []}

        # Step 2: Get video statistics
        stats_url = "https://www.googleapis.com/youtube/v3/videos"
        stats_params = {
            "key": GCP_API_KEY,
            "id": ",".join(video_ids),
            "part": "statistics",
        }
        stats_response = requests.get(stats_url, params=stats_params, timeout=10)
        stats_response.raise_for_status()
        stats_data = stats_response.json()

        stats_map = {}
        for item in stats_data.get("items", []):
            stats_map[item["id"]] = item.get("statistics", {})

        # Step 3: Combine results
        results = []
        for vid_id in video_ids:
            snippet = snippets.get(vid_id, {})
            stats = stats_map.get(vid_id, {})
            results.append({
                "title": snippet.get("title", ""),
                "channel": snippet.get("channelTitle", ""),
                "description": snippet.get("description", "")[:200],
                "published_at": snippet.get("publishedAt", ""),
                "view_count": stats.get("viewCount", "N/A"),
                "like_count": stats.get("likeCount", "N/A"),
                "url": f"https://www.youtube.com/watch?v={vid_id}",
            })

        return {"status": "success", "query": query, "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_trending_videos(category: str = "science & technology", max_results: int = 5) -> dict:
    """Get trending/popular YouTube videos in a specific category.
    
    Args:
        category: The category to search trending videos for (e.g., 'science & technology', 'education', 'entertainment', 'travel', 'food').
        max_results: Maximum number of results to return.
    
    Returns:
        A dict with a list of popular/trending videos in that category.
    """
    try:
        # Use search with sorting by view count for the category
        search_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "key": GCP_API_KEY,
            "q": f"trending {category} 2025 2026",
            "part": "snippet",
            "type": "video",
            "maxResults": min(max_results, 10),
            "order": "viewCount",
            "publishedAfter": "2025-01-01T00:00:00Z",
        }
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("items", []):
            snippet = item["snippet"]
            vid_id = item["id"]["videoId"]
            results.append({
                "title": snippet.get("title", ""),
                "channel": snippet.get("channelTitle", ""),
                "description": snippet.get("description", "")[:200],
                "url": f"https://www.youtube.com/watch?v={vid_id}",
            })

        return {"status": "success", "category": category, "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}
