"""
Tools for LangGraph agents using SERP API
"""

import os
import requests
from typing import List, Dict, Any, Optional
from serpapi import GoogleSearch
from agents.models import SearchResults

# Set the API key
SERP_API_KEY = "57ac64b9ae4022e145b68dea1e2ff26c1fe5819d8a43da8b4297497fb8bcc56b"
MAPBOX_TOKEN = os.getenv("MAPBOX_API_KEY") or os.getenv("MAPBOX_ACCESS_TOKEN")

def get_country_for_city(city: str) -> str:
    """Get the country for a given city to improve geocoding accuracy"""
    city_lower = city.lower()

    # City to country mapping
    city_country_map = {
        # Vietnam
        'hanoi': 'Vietnam',
        'ho chi minh city': 'Vietnam',
        'saigon': 'Vietnam',
        'da nang': 'Vietnam',
        'hue': 'Vietnam',
        'nha trang': 'Vietnam',
        'hoi an': 'Vietnam',

        # Thailand
        'bangkok': 'Thailand',
        'chiang mai': 'Thailand',
        'phuket': 'Thailand',
        'pattaya': 'Thailand',

        # India
        'mumbai': 'India',
        'delhi': 'India',
        'bangalore': 'India',
        'kolkata': 'India',
        'chennai': 'India',
        'hyderabad': 'India',
        'pune': 'India',
        'goa': 'India',
        'jaipur': 'India',
        'agra': 'India',

        # Malaysia
        'kuala lumpur': 'Malaysia',
        'penang': 'Malaysia',
        'johor bahru': 'Malaysia',

        # Singapore
        'singapore': 'Singapore',

        # Indonesia
        'jakarta': 'Indonesia',
        'bali': 'Indonesia',
        'yogyakarta': 'Indonesia',

        # Philippines
        'manila': 'Philippines',
        'cebu': 'Philippines',

        # Europe
        'paris': 'France',
        'london': 'United Kingdom',
        'rome': 'Italy',
        'madrid': 'Spain',
        'berlin': 'Germany',
        'amsterdam': 'Netherlands',

        # USA
        'new york': 'United States',
        'los angeles': 'United States',
        'chicago': 'United States',
        'san francisco': 'United States',
        'miami': 'United States',

        # Other popular destinations
        'tokyo': 'Japan',
        'seoul': 'South Korea',
        'beijing': 'China',
        'shanghai': 'China',
        'sydney': 'Australia',
        'melbourne': 'Australia',
    }

    return city_country_map.get(city_lower, '')

def search_places_tool(query: str, location: str = "", num_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search for places using SERP API

    Args:
        query: Search query (e.g., "best restaurants", "tourist attractions")
        location: Location to search in (e.g., "New York", "Paris")
        num_results: Number of results to return

    Returns:
        List of place information dictionaries
    """
    try:
        search_query = f"{query} in {location}" if location else query

        search = GoogleSearch({
            "q": search_query,
            "api_key": SERP_API_KEY,
            "num": num_results,
            "hl": "en",
            "gl": "us"
        })

        results = search.get_dict()
        places = []

        if not isinstance(results, dict):
            return []

        # Extract organic results
        if "organic_results" in results:
            for result in results["organic_results"]:
                if isinstance(result, dict):
                    place_info = {
                        "name": result.get("title", ""),
                        "description": result.get("snippet", ""),
                        "url": result.get("link", ""),
                        "source": "serp_organic"
                    }
                    places.append(place_info)

        # Extract local results if available
        if "local_results" in results:
            for result in results["local_results"]:
                if isinstance(result, dict):
                    gps_coords = result.get("gps_coordinates", {})
                    place_info = {
                        "name": result.get("title", ""),
                        "address": result.get("address", ""),
                        "rating": result.get("rating", 0),
                        "reviews": result.get("reviews", 0),
                        "type": result.get("type", ""),
                        "phone": result.get("phone", ""),
                        "website": result.get("website", ""),
                        "latitude": gps_coords.get("latitude") if isinstance(gps_coords, dict) else None,
                        "longitude": gps_coords.get("longitude") if isinstance(gps_coords, dict) else None,
                        "source": "serp_local"
                    }
                    places.append(place_info)

        # Extract knowledge graph results if available
        if "knowledge_graph" in results:
            kg = results["knowledge_graph"]
            if "title" in kg:
                place_info = {
                    "name": kg.get("title", ""),
                    "description": kg.get("description", ""),
                    "type": kg.get("type", ""),
                    "website": kg.get("website", ""),
                    "source": "serp_knowledge_graph"
                }
                places.append(place_info)

        return places[:num_results]

    except Exception as e:
        print(f"SERP search error: {e}")
        return []

def search_travel_info_tool(query: str, location: str = "") -> str:
    """
    Search for travel-related information using SERP API

    Args:
        query: Travel question or topic
        location: Location context if relevant

    Returns:
        Formatted search results as text
    """
    try:
        search_query = f"{query} {location}".strip()

        search = GoogleSearch({
            "q": search_query,
            "api_key": SERP_API_KEY,
            "num": 5,
            "hl": "en",
            "gl": "us"
        })

        results = search.get_dict()
        info_text = []

        # Extract answer box if available
        if "answer_box" in results:
            answer = results["answer_box"]
            if "answer" in answer:
                info_text.append(f"Quick Answer: {answer['answer']}")
            elif "snippet" in answer:
                info_text.append(f"Quick Answer: {answer['snippet']}")

        # Extract featured snippet
        if "featured_snippet" in results:
            snippet = results["featured_snippet"]
            info_text.append(f"Featured Info: {snippet.get('snippet', '')}")

        # Extract organic results (shortened)
        if "organic_results" in results:
            for i, result in enumerate(results["organic_results"][:2], 1):
                title = result.get("title", "")
                snippet = result.get("snippet", "")[:80]  # Limit snippet length
                if title and snippet:
                    info_text.append(f"{i}. {title}: {snippet}...")

        return "\n\n".join(info_text) if info_text else "No relevant information found."

    except Exception as e:
        print(f"SERP travel info search error: {e}")
        return "Unable to fetch current information at this time."

def search_restaurants_tool(location: str, cuisine_type: str = "", num_results: int = 5) -> List[Dict[str, Any]]:
    """Search for restaurants in a specific location"""
    query = f"best {cuisine_type} restaurants" if cuisine_type else "best restaurants"
    return search_places_tool(query, location, num_results)

def search_attractions_tool(location: str, interest_type: str = "", num_results: int = 5) -> List[Dict[str, Any]]:
    """Search for tourist attractions in a specific location"""
    query = f"{interest_type} attractions tourist places" if interest_type else "tourist attractions places to visit"
    return search_places_tool(query, location, num_results)

def search_activities_tool(location: str, activity_type: str = "", num_results: int = 5) -> List[Dict[str, Any]]:
    """Search for activities in a specific location"""
    query = f"{activity_type} activities things to do" if activity_type else "things to do activities"
    return search_places_tool(query, location, num_results)

def geocode_place_tool(place_name: str, address: str = "", city: str = "") -> Dict[str, Optional[float]]:
    """
    Geocode a place using Mapbox API

    Returns:
        Dictionary with latitude and longitude
    """
    if not MAPBOX_TOKEN:
        return {"latitude": None, "longitude": None}

    try:
        # Get the correct country for the city
        country = get_country_for_city(city)
        city_country = f"{city}, {country}" if country else city
        query_parts = [place_name, address, city_country]
        query = ", ".join([q for q in query_parts if q])

        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{requests.utils.quote(query)}.json"
        resp = requests.get(url, params={"access_token": MAPBOX_TOKEN, "limit": 1}, timeout=10)

        if resp.ok:
            features = resp.json().get("features", [])
            if features:
                longitude, latitude = features[0]["center"]
                return {"latitude": latitude, "longitude": longitude}

        return {"latitude": None, "longitude": None}

    except Exception as e:
        print(f"Geocoding error: {e}")
        return {"latitude": None, "longitude": None}

def format_search_context(places: List[Dict[str, Any]], search_type: str = "general") -> str:
    """Format search results into context for agents"""
    if not places:
        return "No search results available."

    context = f"CURRENT SEARCH RESULTS ({search_type.upper()}):\n"
    for i, place in enumerate(places[:10], 1):  # Limit to top 10
        place_info = f"{i}. {place.get('name', 'Unknown')}"
        if place.get('address'):
            place_info += f" - {place.get('address')}"
        if place.get('description'):
            place_info += f" - {place.get('description')[:100]}..."
        if place.get('rating'):
            place_info += f" (Rating: {place.get('rating')})"
        context += place_info + "\n"

    return context