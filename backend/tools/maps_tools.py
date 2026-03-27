"""
Maps Tools — Google Maps Places API.
MCP tools for the PlannerAgent.
"""

import requests
from backend.tools.google_auth import GCP_API_KEY


def search_places(query: str, location: str = "", radius_km: int = 10) -> dict:
    """Search for places (restaurants, attractions, hotels, etc.) using Google Maps.
    
    Args:
        query: What to search for (e.g., 'best street food', 'historical monuments', 'coffee shops').
        location: City or area name to search in (e.g., 'Jaipur', 'New York', 'Tokyo').
        radius_km: Search radius in kilometers.
    
    Returns:
        A dict with a list of places including name, address, rating, and type.
    """
    try:
        full_query = f"{query} in {location}" if location else query
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "key": GCP_API_KEY,
            "query": full_query,
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for place in data.get("results", [])[:10]:
            results.append({
                "name": place.get("name", ""),
                "address": place.get("formatted_address", ""),
                "rating": place.get("rating", "N/A"),
                "total_ratings": place.get("user_ratings_total", 0),
                "types": place.get("types", [])[:3],
                "place_id": place.get("place_id", ""),
                "open_now": place.get("opening_hours", {}).get("open_now", "Unknown"),
            })

        return {"status": "success", "query": full_query, "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_place_details(place_id: str) -> dict:
    """Get detailed information about a specific place using its place_id.
    
    Args:
        place_id: The Google Place ID for the location.
    
    Returns:
        A dict with detailed information including phone, website, hours, and reviews.
    """
    try:
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "key": GCP_API_KEY,
            "place_id": place_id,
            "fields": "name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,opening_hours,reviews,price_level,url",
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        result = data.get("result", {})

        # Get top reviews
        reviews = []
        for review in result.get("reviews", [])[:3]:
            reviews.append({
                "author": review.get("author_name", ""),
                "rating": review.get("rating", ""),
                "text": review.get("text", "")[:200],
            })

        return {
            "status": "success",
            "name": result.get("name", ""),
            "address": result.get("formatted_address", ""),
            "phone": result.get("formatted_phone_number", "N/A"),
            "website": result.get("website", "N/A"),
            "rating": result.get("rating", "N/A"),
            "total_ratings": result.get("user_ratings_total", 0),
            "price_level": result.get("price_level", "N/A"),
            "hours": result.get("opening_hours", {}).get("weekday_text", []),
            "google_maps_url": result.get("url", ""),
            "reviews": reviews,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
