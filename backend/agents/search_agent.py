"""
Agent for searching places using SERP API
"""

from typing import List
from agents.base_agent import BaseAgent
from agents.models import AgentState, SearchResults
from agents.tools import (
    search_places_tool,
    search_restaurants_tool,
    search_attractions_tool,
    search_activities_tool,
    format_search_context
)

class SearchAgent(BaseAgent):
    """Agent responsible for searching places using SERP API"""

    def search_for_interests(self, city: str, interests: str, days: int) -> SearchResults:
        """Search for places based on user interests"""

        print(f"[SEARCH] Searching for {interests} in {city}")

        serp_places = []
        interest_list = [i.strip() for i in interests.lower().split(',')]

        for interest in interest_list[:3]:  # Limit to first 3 interests for API efficiency
            print(f"[SEARCH] Searching for {interest} places in {city}")

            if 'food' in interest or 'restaurant' in interest or 'dining' in interest:
                places = search_restaurants_tool(city, interest, 3)
            elif 'art' in interest or 'museum' in interest or 'culture' in interest:
                places = search_attractions_tool(city, f"{interest} museum gallery", 3)
            elif 'shop' in interest or 'market' in interest:
                places = search_activities_tool(city, f"{interest} shopping market", 3)
            else:
                places = search_attractions_tool(city, interest, 3)

            serp_places.extend(places)

        # Also get general attractions for the city
        general_attractions = search_attractions_tool(city, "top attractions must visit", 4)
        serp_places.extend(general_attractions)

        print(f"[SEARCH] Found {len(serp_places)} places from search")

        # Format context
        context = format_search_context(serp_places, "itinerary generation")

        return SearchResults(places=serp_places, context=context)

    def search_for_modification(self, city: str, modification_request: str) -> SearchResults:
        """Search for places for modification requests"""

        print(f"[SEARCH] Searching for modification: {modification_request} in {city}")

        # Check if this is an "add" request vs other modifications
        is_add_request = any(word in modification_request.lower()
                           for word in ['add', 'include', 'put in', 'insert', 'append'])

        serp_places = []

        if is_add_request:
            # For add requests, be very specific about location
            search_query = f"{modification_request} in {city}"
            serp_places = search_places_tool(search_query, city, 5)

            # Enhanced targeted searches with city enforcement
            if any(word in modification_request.lower()
                   for word in ['restaurant', 'food', 'eat', 'dining']):
                serp_places.extend(search_restaurants_tool(city, modification_request, 3))
            elif any(word in modification_request.lower()
                     for word in ['museum', 'art', 'culture', 'gallery']):
                serp_places.extend(search_attractions_tool(city, f"{modification_request} museum gallery", 3))
            elif any(word in modification_request.lower()
                     for word in ['shop', 'market', 'mall']):
                serp_places.extend(search_activities_tool(city, f"{modification_request} shopping market", 3))
            else:
                serp_places.extend(search_attractions_tool(city, modification_request, 3))
        else:
            # For other modifications (remove, replace), less strict location filtering
            serp_places = search_places_tool(modification_request, city, 3)

        print(f"[SEARCH] Found {len(serp_places)} relevant places for modification")

        # Format context
        search_type = "ADD request" if is_add_request else "modification"
        context = format_search_context(serp_places, search_type)

        return SearchResults(places=serp_places, context=context)

    def run(self, state: AgentState) -> AgentState:
        """Run the search agent"""

        if state.intent == "modification" and hasattr(state, 'modification_request'):
            # Search for modification
            search_results = self.search_for_modification(
                state.city,
                state.metadata.get('modification_request', '')
            )
        else:
            # Search for initial itinerary
            search_results = self.search_for_interests(
                state.city,
                state.interests,
                state.days
            )

        state.search_results = search_results
        return state