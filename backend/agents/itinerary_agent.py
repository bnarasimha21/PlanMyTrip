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
        clean_places = []
        for place in places:
            if not isinstance(place, dict):
                continue
            if place.get("latitude") is not None and place.get("longitude") is not None:
                clean_places.append(place)
                continue
            place_name = place.get("name")
            address = place.get("address")
            coords = geocode_place_tool(place_name, address, city)
            place["latitude"] = coords["latitude"]
            place["longitude"] = coords["longitude"]
            clean_places.append(place)
        return clean_places

    def generate_itinerary(self, city: str, interests: str, days: int, search_context: str = "") -> dict:
        """Generate initial itinerary using search results"""

        prompt = f"""
                    Create a {days}-day travel itinerary for destination "{city}" focusing on: {interests}.

                    INPUT CONTEXT (Search results for destination "{city}"):
                    {search_context}

                    STRICT OUTPUT FORMAT:
                    Return ONLY a valid JSON object:
                    {{"places":[{{"name":"Name","neighborhood":"Area","category":"food|art|culture|shopping|sightseeing","address":"Address","latitude":null,"longitude":null,"notes":"Brief note"}}]]}}

                    HARD LOCATION CONSTRAINTS (MANDATORY):
                    - Every place MUST be inside the administrative boundary of "{city}" only (if this destination is a city).
                    - DO NOT include places from any other city, province, island, or country.
                    - Do not include similarly named places from other locations.
                    - If a place appears in search results but is outside "{city}", EXCLUDE it.
                    - If location cannot be verified from the context, EXCLUDE it.

                    VERIFICATION CHECK (BEFORE OUTPUT):
                    For each place:
                    - Confirm the address explicitly contains "{city}" (and correct sub-localities if applicable) when applicable.
                    - If ambiguous, search context must clearly tie it to the destination. Otherwise, exclude.

                    SELECTION RULES:
                    - Include {max(5, days * 2)} diverse, real, currently open/accessible places aligned with the interests.
                    - Prioritize items from INPUT CONTEXT that explicitly mention the destination in their address/metadata.
                    - Mix must-see and local gems.
                    - Provide specific addresses (street + locality + city) when destination is a city.
                    - Properly categorize each place.

                    OUTPUT:
                    - Only pure JSON. No markdown, no comments, no trailing commas.
                    """

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
                """
                You are a meticulous travel expert. You must ONLY return valid JSON. 
                You MUST exclude any place not verifiably located inside the target city. 
                If you cannot find enough valid places in the city, return fewer places rather than guessing. 
                Do NOT include similarly named places in other regions.
                """
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

    def _should_use_search(self, modification_request: str, existing_places: list) -> bool:
        """Heuristic to decide if modification needs search."""
        q = (modification_request or "").lower()
        # If modification references existing place, and is just remove/replace/add known place, do not search
        try:
            place_names = [p.get('name', '') for p in existing_places or [] if isinstance(p, dict)]
            for name in place_names:
                if name and name.lower() in q:
                    return False
        except Exception:
            pass
        search_keywords = [
            'add', 'new', 'local gem', 'what else', 'find', 'suggest', 'recommend', 'famous', 'must see', 'top', 'hidden',
            'tickets', 'opening', 'price', 'cost', 'address', 'current', 'latest', 'up to date', 'good', 'best', 'nice', 'restaurant', 'hotel', 'book', 'booking', 'reservation'
        ]
        if any(k in q for k in search_keywords):
            return True
        return False

    def modify_itinerary(self, city: str, interests: str, days: int,
                        existing_places: List[dict], modification_request: str,
                        search_context: str = "", original_request: str = "", chat_history: List[dict] = []) -> dict:
        """Modify existing itinerary based on user request, preserving context and performing search only if required."""
        # Build system instructions
        system_message = (
            f"You are PlanMyTrip, a helpful travel assistant. "
            f"All modifications should keep the itinerary consistent, answer in context, and "
            f'ONLY include places in {city}. '
            f"When adding or suggesting places, they MUST actually be in {city}, not from any other city or country. "
            f"Use ONLY modifications that make sense given the original request, user interests, current itinerary, and chat history. "
            f"If the user refers to an unnamed place by description or position or 'this/that/it', infer based on current itinerary. "
            f"Don't duplicate or remove places unless the user asks. Describe your action clearly."
        )
        # Prepare itinerary context
        itinerary_summaries = []
        for place in existing_places[:10]:
            if not isinstance(place, dict):
                continue
            name = place.get('name') or 'Unknown'
            category = place.get('category') or ''
            neighborhood = place.get('neighborhood') or ''
            notes = (place.get('notes') or '')[:60]
            address = (place.get('address') or '')
            summary = f"- {name} ({category}) {neighborhood}, {address}. {notes}"
            itinerary_summaries.append(summary)
        itinerary_block = '\n'.join(itinerary_summaries) or '(none)'

        # Prepare message list
        messages = [("system", system_message)]
        # Replay succinct recent chat history
        if chat_history and isinstance(chat_history, list):
            for msg in chat_history[-6:]:
                role = (msg.get('type') or '').lower()
                content = msg.get('message') or ''
                if not content:
                    continue
                if role == 'user':
                    messages.append(("user", content))
                elif role == 'bot':
                    messages.append(("assistant", content))
        messages.append(("user", f"Context: City: {city}, Interests: {interests}, Days: {days}\n"
                                   f"Current Itinerary (up to 10):\n{itinerary_block}\n"
                                   f"Original trip request: {original_request}\n"
                                   f"User's new modification request: {modification_request}"))

        import json as _json
        from langchain_core.messages import SystemMessage, HumanMessage
        use_search = self._should_use_search(modification_request, existing_places)
        print(f"[ITINERARY MODIFY] Use search tools: {use_search}")
        try:
            if not use_search:
                # Use LLM only, no search/tools
                llm_msgs = [SystemMessage(content=system_message)]
                if chat_history and isinstance(chat_history, list):
                    for msg in chat_history[-6:]:
                        role = (msg.get('type') or '').lower()
                        content = msg.get('message') or ''
                        if not content:
                            continue
                        if role == 'user':
                            llm_msgs.append(HumanMessage(content=content))
                        elif role == 'bot':
                            llm_msgs.append(SystemMessage(content=f"Assistant previously said: {content}"))
                llm_msgs.append(HumanMessage(content=messages[-1][1]))
                # Ask for only the required JSON structure
                llm_msgs.append(HumanMessage(content='Return only a valid JSON for the modified itinerary, nothing else.'))
                llm_result = self.llm.invoke(llm_msgs)
                resp_text = getattr(llm_result, 'content', None) or ''
                print(f"[ITINERARY MODIFY] LLM response: {resp_text[:140]}")
                try:
                    mod_json = _json.loads(resp_text)
                    updated_places = mod_json.get('places', existing_places or [])
                    response_text = mod_json.get('response', 'I have updated your itinerary as requested.')
                except Exception as inner_e:
                    print(f"[ITINERARY MODIFY] LLM parse error, falling back to chain+tools: {inner_e}")
                    use_search = True
            if use_search:
                # Use chain with proper structure and activate tools/search
                prompt = '\n'.join([
                    system_message,
                    f'City: {city}',
                    f'Interests: {interests}',
                    f'Days: {days}',
                    f'Current itinerary (as JSON): {existing_places}',
                    f'Original trip request: {original_request}',
                    f'Recent chat history: {chat_history}',
                    f'User modification request: {modification_request}',
                    f"Be sure all added places are in {city} and output strictly matches the required modification JSON schema!"
                ])
                chain = self.create_structured_chain(
                    system_message,
                    ModificationResponse
                )
                result = self.execute_with_fallback(
                    chain,
                    prompt,
                    ModificationResponse,
                    system_message + " Return valid modification JSON only."
                )
                updated_places = result.get('places')
                if updated_places is None:
                    updated_places = existing_places or []
                updated_places = [p for p in updated_places if isinstance(p, dict)]
                response_text = result.get('response', 'I have updated your itinerary as requested.')
            # Geocode as before, convert Pydantic if needed
            if updated_places is None:
                updated_places = []
            updated_places = [p for p in updated_places if isinstance(p, dict)]
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