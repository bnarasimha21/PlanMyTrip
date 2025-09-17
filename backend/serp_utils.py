"""
SERP API utilities for enhanced search capabilities
"""

import os
from serpapi import GoogleSearch
from typing import List, Dict, Any, Optional
import json

# Set the API key
SERP_API_KEY = "57ac64b9ae4022e145b68dea1e2ff26c1fe5819d8a43da8b4297497fb8bcc56b"

def search_places(query: str, location: str = "", num_results: int = 10) -> List[Dict[str, Any]]:
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

def search_travel_info(query: str, location: str = "") -> str:
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
        
        # Skip people also ask for brevity
        
        return "\n\n".join(info_text) if info_text else "No relevant information found."
        
    except Exception as e:
        print(f"SERP travel info search error: {e}")
        return "Unable to fetch current information at this time."

def search_restaurants(location: str, cuisine_type: str = "", num_results: int = 5) -> List[Dict[str, Any]]:
    """Search for restaurants in a specific location"""
    query = f"best {cuisine_type} restaurants" if cuisine_type else "best restaurants"
    return search_places(query, location, num_results)

def search_attractions(location: str, interest_type: str = "", num_results: int = 5) -> List[Dict[str, Any]]:
    """Search for tourist attractions in a specific location"""
    query = f"{interest_type} attractions tourist places" if interest_type else "tourist attractions places to visit"
    return search_places(query, location, num_results)

def search_activities(location: str, activity_type: str = "", num_results: int = 5) -> List[Dict[str, Any]]:
    """Search for activities in a specific location"""
    query = f"{activity_type} activities things to do" if activity_type else "things to do activities"
    return search_places(query, location, num_results)

def get_current_travel_tips(location: str) -> str:
    """Get current travel tips and information for a location"""
    query = f"travel tips current information visiting {location} 2024"
    return search_travel_info(query, location)

def get_transportation_info(location: str, transport_type: str = "") -> str:
    """Get transportation information for a location"""
    query = f"{transport_type} transportation getting around" if transport_type else "transportation getting around"
    return search_travel_info(query, location)

# Test function
def test_serp_api():
    """Test SERP API functionality"""
    print("Testing SERP API...")
    
    # Test place search
    places = search_places("best restaurants", "Paris", 3)
    print(f"Found {len(places)} restaurant results for Paris")
    
    # Test travel info
    info = search_travel_info("best time to visit", "Japan")
    print(f"Travel info length: {len(info)} characters")
    
    # Test specific searches
    restaurants = search_restaurants("Tokyo", "sushi", 2)
    print(f"Found {len(restaurants)} sushi restaurants in Tokyo")
    
    print("SERP API test completed!")

if __name__ == "__main__":
    test_serp_api()
