"""
Tools for LangGraph agents using Tavily Search
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain_tavily import TavilySearch
from agents.models import SearchResults

load_dotenv()
MAPBOX_TOKEN = os.getenv("MAPBOX_API_KEY") or os.getenv("MAPBOX_ACCESS_TOKEN")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Initialize a single Tavily search tool instance; we will override per-call max_results
_tavily_search_tool = TavilySearch(max_results=5, topic="general")

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
    Search for places using Tavily Search

    Args:
        query: Search query (e.g., "best restaurants", "tourist attractions")
        location: Location to search in (e.g., "New York", "Paris")
        num_results: Number of results to return

    Returns:
        List of place information dictionaries
    """
    try:
        search_query = f"{query} in {location}" if location else query

        # Configure per-call max results by creating a transient tool
        if TAVILY_API_KEY:
            tavily_tool = TavilySearch(max_results=max(1, int(num_results)), topic="general", tavily_api_key=TAVILY_API_KEY)
        else:
            tavily_tool = TavilySearch(max_results=max(1, int(num_results)), topic="general")

        tool_msg = tavily_tool.invoke({"query": search_query})

        # tool_msg.content may be a JSON string; normalize to dict
        content = tool_msg if isinstance(tool_msg, dict) else None
        if content is None:
            try:
                content = json.loads(getattr(tool_msg, "content", "") or "{}")
            except Exception:
                content = {}

        results = content.get("results", []) if isinstance(content, dict) else []
        places: List[Dict[str, Any]] = []

        for result in results:
            if isinstance(result, dict):
                place_info: Dict[str, Any] = {
                    "name": result.get("title", ""),
                    "description": result.get("content", ""),
                    "url": result.get("url", ""),
                    "source": "tavily"
                }
                places.append(place_info)

        return places[:num_results]

    except Exception as e:
        print(f"Tavily search error: {e}")
        return []

def search_travel_info_tool(query: str, location: str = "") -> str:
    """
    Search for travel-related information using Tavily Search

    Args:
        query: Travel question or topic
        location: Location context if relevant

    Returns:
        Formatted search results as text
    """
    try:
        search_query = f"{query} {location}".strip()

        # Up to 5 concise results
        if TAVILY_API_KEY:
            tavily_tool = TavilySearch(max_results=5, topic="general", tavily_api_key=TAVILY_API_KEY)
        else:
            tavily_tool = TavilySearch(max_results=5, topic="general")

        tool_msg = tavily_tool.invoke({"query": search_query})
        try:
            content = tool_msg if isinstance(tool_msg, dict) else json.loads(getattr(tool_msg, "content", "") or "{}")
        except Exception:
            content = {}

        results = content.get("results", []) if isinstance(content, dict) else []
        if not results:
            return "No relevant information found."

        info_lines: List[str] = []
        for i, result in enumerate(results[:3], 1):
            title = result.get("title", "")
            snippet = (result.get("content", "") or "")[:120]
            url = result.get("url", "")
            if title and snippet:
                info_lines.append(f"{i}. {title}: {snippet}... ({url})")

        return "\n\n".join(info_lines) if info_lines else "No relevant information found."

    except Exception as e:
        print(f"Tavily travel info search error: {e}")
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