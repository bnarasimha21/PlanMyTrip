"""
Agent for generating and modifying itineraries
"""

import json
from typing import List
from agents.base_agent import BaseAgent
from agents.models import ItineraryResponse, ModificationResponse, Place, AgentState
from agents.tools import geocode_place_tool

class ItineraryAgent(BaseAgent):
    """Agent responsible for generating and modifying itineraries"""

    def filter_places_by_city(self, places: List[dict], target_city: str) -> List[dict]:
        """Filter out places that might be in wrong city"""
        filtered_places = []
        wrong_city_keywords = [
            'ho chi minh', 'saigon', 'bangkok', 'kuala lumpur', 'singapore',
            'jakarta', 'manila', 'phnom penh', 'vientiane'
        ]
        target_city_lower = target_city.lower()

        for place in places:
            place_name = (place.get('name') or '').lower()
            place_address = (place.get('address') or '').lower()
            place_notes = (place.get('notes') or '').lower()

            # Check if place contains wrong city keywords
            contains_wrong_city = any(
                keyword in place_name or keyword in place_address or keyword in place_notes
                for keyword in wrong_city_keywords if keyword != target_city_lower
            )

            if not contains_wrong_city:
                filtered_places.append(place)
            else:
                print(f"[FILTER] Removed {place.get('name')} - appears to be in wrong city")

        return filtered_places

    def geocode_places(self, places: List[dict], city: str) -> List[dict]:
        """Add geocoding to places that don't have coordinates"""
        for place in places:
            if place.get("latitude") is not None and place.get("longitude") is not None:
                continue

            place_name = place.get("name")
            address = place.get("address")

            coords = geocode_place_tool(place_name, address, city)
            place["latitude"] = coords["latitude"]
            place["longitude"] = coords["longitude"]

        return places

    def generate_itinerary(self, city: str, interests: str, days: int, search_context: str = "") -> dict:
        """Generate initial itinerary using search results"""

        prompt = f"""Create a {days}-day travel itinerary for {city} focusing on {interests}.

{search_context}Use the search results above as a reference for current, popular places to include in the itinerary. Prioritize places with good ratings and detailed information.

Return ONLY a valid JSON object with this structure:
{{"places":[{{"name":"Name","neighborhood":"Area","category":"food/art/culture/shopping/sightseeing","address":"Address","latitude":null,"longitude":null,"notes":"Brief note"}}]}}

CRITICAL LOCATION REQUIREMENT:
- ALL places MUST be located specifically in {city}
- DO NOT include places from other cities
- Verify each place is actually in {city} before including it
- If unsure about location, do not include the place

Requirements:
- Include {max(5, days * 2)} diverse places that match the interests
- Prioritize places from the search results when they match the interests
- Mix of popular attractions and local gems
- Include specific addresses where possible
- Categorize each place appropriately (food, art, culture, shopping, sightseeing)
- Provide helpful notes for each place
- Focus on places that are currently open and accessible
- Real places only, NO markdown formatting, just pure JSON
- ONLY places located in {city}"""

        # Create structured chain
        chain = self.create_structured_chain(
            "You are a travel expert. Return valid JSON with real, current places.",
            ItineraryResponse
        )

        try:
            result = self.execute_with_fallback(
                chain,
                prompt,
                ItineraryResponse,
                "You are a travel expert. Return only valid JSON with real, current places."
            )

            places = result.get('places', [])

            # Convert to dict format if they're Pydantic models
            if places and hasattr(places[0], 'model_dump'):
                places = [p.model_dump() for p in places]

            # Filter places by city
            places = self.filter_places_by_city(places, city)

            # Geocode places
            places = self.geocode_places(places, city)

            return {
                "city": city,
                "interests": interests,
                "days": days,
                "places": places[:6],  # Limit for speed
                "raw_research_text": str(result)
            }

        except Exception as e:
            print(f"Itinerary generation error: {e}")
            return {
                "city": city,
                "interests": interests,
                "days": days,
                "places": [],
                "raw_research_text": None
            }

    def modify_itinerary(self, city: str, interests: str, days: int,
                        existing_places: List[dict], modification_request: str,
                        search_context: str = "") -> dict:
        """Modify existing itinerary based on user request"""

        # Check if this is an "add" request vs other modifications
        is_add_request = any(word in modification_request.lower()
                           for word in ['add', 'include', 'put in', 'insert', 'append'])

        places_json = json.dumps(existing_places or [], indent=2)

        # Enhanced prompt based on request type
        if is_add_request:
            location_constraint = f"""
LOCATION CONSTRAINT - EXTREMELY IMPORTANT:
- You are planning a trip to {city}
- ALL new places MUST be located in {city} specifically
- DO NOT add places from other cities, even if they seem relevant
- If the search results don't show places clearly in {city}, respond with an error
- Verify each place is actually in {city} before adding it"""

            prompt = f"""You are modifying a travel itinerary for {city}. Here's the current situation:

City: {city}
Current Places: {places_json}

{search_context}User Request: "{modification_request}"
{location_constraint}

Use ONLY the search results above when adding new places. Prioritize places with good ratings that are clearly located in {city}.

CRITICAL INSTRUCTIONS - READ CAREFULLY:"""
        else:
            prompt = f"""You are modifying a travel itinerary. Here's the current situation:

City: {city}
Current Places: {places_json}

{search_context}User Request: "{modification_request}"

Use the search results above when modifying places. Prioritize places with good ratings and detailed information.

CRITICAL LOCATION REQUIREMENT:
- ALL places (new or existing) MUST be located specifically in {city}
- DO NOT include places from other cities (including Ho Chi Minh City, Bangkok, etc.)
- Verify each place is actually in {city} before including it

CRITICAL INSTRUCTIONS - READ CAREFULLY:

1. PRESERVATION RULE: The "places" array in your response MUST contain ALL places that should exist in the final itinerary.

2. ADD/INCLUDE OPERATIONS:
   - Words like "add", "include", "put in", "to the list", "to the itinerary" mean ADD TO EXISTING
   - You MUST include ALL current places PLUS the new one(s)
   - Example: If current has [A, B, C] and user says "add D", result should be [A, B, C, D]

3. REMOVE/DELETE OPERATIONS:
   - Only remove places when explicitly told to "remove", "delete", "take out"
   - Keep all other existing places

4. REPLACE OPERATIONS:
   - Only replace when explicitly told to "replace X with Y"

5. EXAMPLES:
   - "Add UB City to the list" -> Keep ALL existing places + add UB City
   - "Include Central Mall" -> Keep ALL existing places + add Central Mall
   - "Remove Place A" -> Keep all places except Place A
   - "Replace Place A with Place B" -> Keep all places but change Place A to Place B

Current places count: {len(existing_places or [])}
You must return AT LEAST this many places unless explicitly asked to remove some.

Return ONLY a JSON object:
{{
  "type": "modification",
  "response": "Description of what changes were made",
  "places": [
    {{
      "name": "Place Name",
      "neighborhood": "Area Name",
      "category": "Food/Art/Culture",
      "address": "Full Address",
      "latitude": null,
      "longitude": null,
      "notes": "Brief description"
    }}
  ]
}}"""

        # Create structured chain
        chain = self.create_structured_chain(
            "You are a travel assistant. Return valid JSON for itinerary modifications.",
            ModificationResponse
        )

        try:
            result = self.execute_with_fallback(
                chain,
                prompt,
                ModificationResponse,
                "You are a travel assistant. Return only valid JSON for itinerary modifications."
            )

            updated_places = result.get('places', existing_places or [])
            response_text = result.get('response', 'I\'ve processed your modification request.')

            # Convert to dict format if they're Pydantic models
            if updated_places and hasattr(updated_places[0], 'model_dump'):
                updated_places = [p.model_dump() for p in updated_places]

            # Filter places by city
            updated_places = self.filter_places_by_city(updated_places, city)

            # Geocode new places
            updated_places = self.geocode_places(updated_places, city)

            return {
                "city": city,
                "interests": interests,
                "days": days,
                "places": updated_places,
                "type": "modification",
                "response": response_text
            }

        except Exception as e:
            print(f"Modification error: {e}")
            return {
                "city": city,
                "interests": interests,
                "days": days,
                "places": existing_places or [],
                "type": "modification",
                "response": "I'm having trouble processing that request right now."
            }

    def run(self, state: AgentState) -> AgentState:
        """Run the itinerary agent"""

        search_context = state.search_results.context if state.search_results else ""

        if state.intent == "modification":
            # Modify existing itinerary
            modification_request = state.metadata.get('instruction', '')
            existing_places = [p.model_dump() if hasattr(p, 'model_dump') else p for p in state.places]

            result = self.modify_itinerary(
                state.city,
                state.interests,
                state.days,
                existing_places,
                modification_request,
                search_context
            )

            # Update state with modified places
            state.places = [Place(**p) for p in result.get('places', [])]
            state.response = result.get('response', '')
            state.metadata['result_type'] = 'modification'

        else:
            # Generate new itinerary
            result = self.generate_itinerary(
                state.city,
                state.interests,
                state.days,
                search_context
            )

            # Update state with new places
            state.places = [Place(**p) for p in result.get('places', [])]
            state.metadata['result_type'] = 'itinerary'

        return state