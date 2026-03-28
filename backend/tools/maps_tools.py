"""
Maps Tools — Google Maps Places API.
"""
import os
import requests

GCP_API_KEY = os.environ.get("GCP_API_KEY", "")

def search_places(query: str, location: str = "", radius_km: int = 10) -> dict:
    """Search for places using Google Maps.
    
    Args:
        query: What to search for (e.g., 'best restaurants', 'historical monuments').
        location: City or area name (e.g., 'Kolkata', 'Mumbai').
        radius_km: Search radius in kilometers.
    
    Returns:
        A dict with a list of places including name, address, rating.
    """
    try:
        full_query = f"{query} in {location}" if location else query
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {"key": GCP_API_KEY, "query": full_query}
        response = requests.get(url, params=params, timeout=10)
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
            })
        return {"status": "success", "query": full_query, "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_place_details(place_id: str) -> dict:
    """Get detailed information about a specific place.
    
    Args:
        place_id: The Google Place ID.
    
    Returns:
        A dict with details including phone, website, hours.
    """
    try:
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "key": GCP_API_KEY,
            "place_id": place_id,
            "fields": "name,formatted_address,formatted_phone_number,website,rating,opening_hours,url",
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        result = data.get("result", {})
        return {
            "status": "success",
            "name": result.get("name", ""),
            "address": result.get("formatted_address", ""),
            "phone": result.get("formatted_phone_number", "N/A"),
            "website": result.get("website", "N/A"),
            "rating": result.get("rating", "N/A"),
            "hours": result.get("opening_hours", {}).get("weekday_text", []),
            "google_maps_url": result.get("url", ""),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}