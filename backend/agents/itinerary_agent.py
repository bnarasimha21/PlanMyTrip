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

        {search_context}
        Use the search results above as a reference for current, popular places to include in the itinerary. 
        Prioritize places with good ratings and detailed information.

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
                        search_context: str = "", original_request: str = "", chat_history: List[dict] = []) -> dict:
        """Modify existing itinerary based on user request"""

        prompt = f"""
        Here is the original request of user planning for a trip: {original_request}

        Here is the Itinerary suggested by us for the trip: {existing_places}

        Here is the chat history of the conversation between user and us: {chat_history}

        Based on users request, make necessary modification to the itinerary 
        based on the chat history and the original request.

        Here is the user query: {modification_request}

        1. If user is asking to add a new place to itinerary:        

            ADD/INCLUDE OPERATIONS:
                - You MUST keep itinerary intact and add the new one(s) to it.
                - Example: If current itinerary has [A, B, C] and user says "add D", result should be [A, B, C, D]
                - Do not remove any existing places from the itinerary.
                - Do not replace any existing places with the new one(s).
                - Do not change the order of the existing places.
                - Do not replace any existing places with the new one(s).

                CRITICAL LOCATION REQUIREMENT:
                - ALL places (new or existing) MUST be located specifically in {city}
                - DO NOT include places from other cities (including Ho Chi Minh City, Bangkok, etc.)
                - Verify each place is actually in {city} before including it

        2. If user is asking to remove a place from itinerary:
            REMOVE/DELETE OPERATIONS:
                - Only remove places when explicitly told to "remove", "delete", "take out"
                - Keep all other existing places    


        3. If user is asking to replace a place in itinerary:
            REPLACE OPERATIONS:
                - Only replace when explicitly told to "replace X with Y"

        EXAMPLES:
        - "Add UB City to the list" -> Keep ALL existing places + add UB City
        - "Include Central Mall" -> Keep ALL existing places + add Central Mall
        - "Remove Place A" -> Keep all places except Place A
        - "Replace Place A with Place B" -> Keep all places but change Place A to Place B                

        
        Return ONLY a JSON object with this structure:
        {{
        "type": "modification",
        "response": "Description of what changes were made",
        "places": [
            {{
            "name": "Place Name",
            "neighborhood": "Area Name",
            "category": "Food/Art/Culture/Shopping/Sightseeing",
            "address": "Full Address",
            "latitude": <latitude of the place>,
            "longitude": <longitude of the place>,
            "notes": "Brief description"
            }}
        ]
        }}
        """


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
            print(f"Updated places: {updated_places}")
            response_text = result.get('response', 'I\'ve processed your modification request.')

            # Convert to dict format if they're Pydantic models
            if updated_places and hasattr(updated_places[0], 'model_dump'):
                updated_places = [p.model_dump() for p in updated_places]

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
                search_context,
                state.metadata.get('original_request', ''),
                state.metadata.get('chat_history', [])
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