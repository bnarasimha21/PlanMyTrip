#!/usr/bin/env python3
"""
Fast alternatives to CrewAI agents using Langchain Gradient
for 3-5x performance improvement
"""

import json
import os
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_gradient import ChatGradient
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from serp_utils import search_travel_info, search_places, search_restaurants, search_attractions, search_activities

load_dotenv()

# Define Pydantic models for structured output
class Place(BaseModel):
    name: str = Field(description="Name of the place")
    neighborhood: str = Field(description="Neighborhood or area", default=None)
    category: str = Field(description="Category: food/art/culture/shopping/sightseeing")
    address: str = Field(description="Full address", default=None)
    latitude: float = Field(description="Latitude coordinate", default=None)
    longitude: float = Field(description="Longitude coordinate", default=None)
    notes: str = Field(description="Brief description or notes")

class ItineraryResponse(BaseModel):
    places: List[Place] = Field(description="List of places for the itinerary")

class ClassificationResponse(BaseModel):
    classification: str = Field(description="Either 'question' or 'modification'")

class QuestionResponse(BaseModel):
    response: str = Field(description="Answer to the travel question")

class ModificationResponse(BaseModel):
    type: str = Field(description="Type of response", default="modification")
    response: str = Field(description="Description of changes made")
    places: List[Place] = Field(description="Updated list of places")

class TripExtractionResponse(BaseModel):
    city: str = Field(description="City name")
    interests: str = Field(description="Comma-separated interests")
    days: int = Field(description="Number of days")

# Initialize Gradient LLM
gradient_llm = ChatGradient(
    model="llama3.3-70b-instruct",
    api_key=os.getenv("DIGITALOCEAN_INFERENCE_KEY")
)

MAPBOX_TOKEN = os.getenv("MAPBOX_API_KEY") or os.getenv("MAPBOX_ACCESS_TOKEN")

def fast_get_itinerary(city: str, interests: str, days: int):
    """Fast itinerary generation using direct OpenAI call with SERP API enhancement"""
    
    print(f"[SERP] Generating itinerary for {city} with interests: {interests}")
    
    # Get current information about attractions and places
    serp_places = []
    interest_list = [i.strip() for i in interests.lower().split(',')]
    
    for interest in interest_list[:3]:  # Limit to first 3 interests for API efficiency
        print(f"[SERP] Searching for {interest} places in {city}")
        if 'food' in interest or 'restaurant' in interest or 'dining' in interest:
            places = search_restaurants(city, interest, 3)
        elif 'art' in interest or 'museum' in interest or 'culture' in interest:
            places = search_attractions(city, f"{interest} museum gallery", 3)
        elif 'shop' in interest or 'market' in interest:
            places = search_activities(city, f"{interest} shopping market", 3)
        else:
            places = search_attractions(city, interest, 3)
        
        serp_places.extend(places)
    
    # Also get general attractions for the city
    general_attractions = search_attractions(city, "top attractions must visit", 4)
    serp_places.extend(general_attractions)
    
    print(f"[SERP] Found {len(serp_places)} places from search")
    
    # Format SERP results for the prompt
    serp_context = ""
    if serp_places:
        serp_context = "CURRENT SEARCH RESULTS FROM SERP API:\n"
        for i, place in enumerate(serp_places[:10], 1):  # Limit to top 10
            place_info = f"{i}. {place.get('name', 'Unknown')}"
            if place.get('address'):
                place_info += f" - {place.get('address')}"
            if place.get('description'):
                place_info += f" - {place.get('description')[:100]}..."
            if place.get('rating'):
                place_info += f" (Rating: {place.get('rating')})"
            serp_context += place_info + "\n"
        serp_context += "\n"
    
    prompt = f"""Create a {days}-day travel itinerary for {city} focusing on {interests}.

{serp_context}Use the search results above as a reference for current, popular places to include in the itinerary. Prioritize places with good ratings and detailed information.

Return ONLY a valid JSON object with this structure:
{{"places":[{{"name":"Name","neighborhood":"Area","category":"food/art/culture/shopping/sightseeing","address":"Address","latitude":null,"longitude":null,"notes":"Brief note"}}]}}

Requirements:
- Include {max(5, days * 2)} diverse places that match the interests
- Prioritize places from the search results when they match the interests
- Mix of popular attractions and local gems
- Include specific addresses where possible
- Categorize each place appropriately (food, art, culture, shopping, sightseeing)
- Provide helpful notes for each place
- Focus on places that are currently open and accessible
- Real places only, NO markdown formatting, just pure JSON"""

    try:
        # Set up structured output parser
        parser = JsonOutputParser(pydantic_object=ItineraryResponse)

        prompt_template = PromptTemplate(
            template="You are a travel expert. {format_instructions}\n\n{query}",
            input_variables=["query"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )

        chain = prompt_template | gradient_llm | parser

        try:
            result = chain.invoke({"query": prompt})
            places = result.get('places', [])
        except Exception as e:
            print(f"[STRUCTURED] Structured output failed, using fallback: {e}")
            # Fallback to regular call
            messages = [
                SystemMessage(content="You are a travel expert. Return only valid JSON with real, current places."),
                HumanMessage(content=prompt)
            ]

            llm_result = gradient_llm.invoke(messages, temperature=0.5, max_tokens=800)
            response = llm_result.content.strip()

            # Clean markdown if present
            if response.startswith('```json'):
                response = response[7:]
            elif response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()

            # Parse JSON
            try:
                data = json.loads(response)
                places = data.get('places', [])
            except json.JSONDecodeError:
                places = []
            
        # Geocode missing coordinates so markers render on the map
        print(f"[GEOCODING] Starting geocoding. MAPBOX_TOKEN exists: {bool(MAPBOX_TOKEN)}, MAPBOX_TOKEN value: {MAPBOX_TOKEN[:10] if MAPBOX_TOKEN else 'None'}..., Places count: {len(places)}")
        if MAPBOX_TOKEN and places:
            for place in places:
                if place.get("latitude") is not None and place.get("longitude") is not None:
                    print(f"[GEOCODING] Skipping {place.get('name')} - already has coordinates")
                    continue
                place_name = place.get("name")
                
                address = place.get("address")
                query_parts = [place_name, address, city]
                query = ", ".join([q for q in query_parts if q])
                print(f"[GEOCODING] Geocoding '{place_name}' with query: '{query}'")
                try:
                    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{requests.utils.quote(query)}.json"
                    print(f"[GEOCODING] Making request to: {url[:100]}...")
                    resp = requests.get(url, params={"access_token": MAPBOX_TOKEN, "limit": 1}, timeout=10)
                    print(f"[GEOCODING] Response status: {resp.status_code}")
                    if resp.ok:
                        features = resp.json().get("features", [])
                        print(f"[GEOCODING] Found {len(features)} features")
                        if features:
                            longitude, latitude = features[0]["center"]
                            place["latitude"] = latitude
                            place["longitude"] = longitude
                            print(f"[GEOCODING] ✅ Set coordinates for {place_name}: {latitude}, {longitude}")
                            if not place.get("address"):
                                place["address"] = features[0].get("place_name")
                        else:
                            print(f"[GEOCODING] ❌ No features found for {place_name}")
                            place["latitude"] = None
                            place["longitude"] = None
                    else:
                        print(f"[GEOCODING] ❌ Request failed for {place_name}: {resp.text[:200]}")
                        place["latitude"] = None
                        place["longitude"] = None
                except Exception as e:
                    print(f"[GEOCODING] ❌ Exception for {place_name}: {e}")
                    place["latitude"] = None
                    place["longitude"] = None
        else:
            print(f"[GEOCODING] Skipping geocoding - MAPBOX_TOKEN: {bool(MAPBOX_TOKEN)}, places: {len(places) if places else 0}")
        
        return {
            "city": city,
            "interests": interests,
            "days": days,
            "places": places[:6],  # Limit for speed
            "raw_research_text": str(result) if 'result' in locals() else None
        }
        
    except Exception as e:
        print(f"Fast itinerary error: {e}")
        return {
            "city": city,
            "interests": interests,
            "days": days,
            "places": [],
            "raw_research_text": None
        }

def classify_user_intent(user_input: str, context: str = None) -> str:
    """
    Use OpenAI to classify whether user input is a question or modification request
    Returns: 'question' or 'modification'
    """
    
    prompt = f"""Classify the following user input as either a "question" or a "modification" request for a travel itinerary.

USER INPUT: "{user_input}"

CONTEXT: {context or "User is planning a trip and has an existing itinerary."}

CLASSIFICATION RULES:
- "question": User is asking for information, advice, recommendations, explanations, or seeking help. This includes questions about availability, possibilities, or general inquiries.
  Examples: "What's the best time to visit?", "How far is X from Y?", "Which place is better?", "What should I know about X?", "Can I get a scooter rental?", "Is there a good restaurant nearby?", "Where can I find X?"
  
- "modification": User is giving a direct command or explicit request to change, add, remove, or replace something in their itinerary. Look for imperative verbs and direct instructions.
  Examples: "Add a restaurant", "Remove the museum", "Replace X with Y", "Include more shopping places", "Put in a scooter rental", "Take out expensive places"

Respond with ONLY one word: "question" or "modification"."""

    try:
        # Set up structured output parser
        parser = JsonOutputParser(pydantic_object=ClassificationResponse)

        prompt_template = PromptTemplate(
            template="You are a precise intent classifier for travel planning. 'question' = asking for information/availability. 'modification' = direct command to change itinerary. Questions about 'can I', 'where can I', 'is there' are ALWAYS questions, not modifications.\n\n{format_instructions}\n\n{query}",
            input_variables=["query"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )

        chain = prompt_template | gradient_llm | parser

        try:
            result = chain.invoke({"query": prompt})
            classification = result.get('classification', '').lower()
        except Exception as e:
            print(f"[STRUCTURED] Classification structured output failed, using fallback: {e}")
            # Fallback to regular call
            messages = [
                SystemMessage(content="You are a precise intent classifier for travel planning. 'question' = asking for information/availability. 'modification' = direct command to change itinerary. Questions about 'can I', 'where can I', 'is there' are ALWAYS questions, not modifications. Respond with only 'question' or 'modification'."),
                HumanMessage(content=prompt)
            ]

            response = gradient_llm.invoke(messages, temperature=0.1, max_tokens=10)
            classification = response.content.strip().lower()

        result = classification
        
        # Debug logging
        print(f"[CLASSIFIER] Input: '{user_input}' -> Raw response: '{result}'")
        
        # Ensure we only get valid responses
        if result in ['question', 'modification']:
            print(f"[CLASSIFIER] Final classification: {result}")
            return result
        else:
            # Default to question if unclear
            print(f"[CLASSIFIER] Invalid response '{result}', defaulting to 'question'")
            return 'question'
            
    except Exception as e:
        print(f"Classification error: {e}")
        # Default to question on error
        return 'question'

def test_classifier():
    """Test function to verify classifier works correctly"""
    test_cases = [
        ("can I get a scooter rental in hanoi", "question"),
        ("add a scooter rental", "modification"),
        ("where can I find good pho", "question"),
        ("include a pho restaurant", "modification"),
        ("is there a night market", "question"),
        ("put in a night market", "modification"),
        ("what's the best route", "question"),
        ("remove the museum", "modification")
    ]
    
    print("\n=== TESTING CLASSIFIER ===")
    for input_text, expected in test_cases:
        result = classify_user_intent(input_text, "User planning trip to Hanoi")
        status = "✓" if result == expected else "✗"
        print(f"{status} '{input_text}' -> {result} (expected: {expected})")
    print("=== END TEST ===\n")

def fast_handle_question(city: str, interests: str, days: int, user_question: str, 
                        original_request: str = None, current_places: list = None, 
                        chat_history: list = None):
    """Enhanced question handling with brief responses using SERP API"""
    
    print(f"[DEBUG] Question function called: {user_question}")
    
    if not user_question or not user_question.strip():
        return {
            "type": "answer",
            "response": "Please ask me a question about your travel plans."
        }
    
    # Get brief info from SERP API (first 100 chars only)
    serp_info = search_travel_info(user_question, city)[:100]
    
    # Create very short context
    context = f"Trip: {city}, {interests}"
    if current_places and len(current_places) > 0:
        context += f", Current places: {len(current_places)}"
    
    prompt = f"""{context}

Question: {user_question}

Context: {serp_info}

Give a direct 1-sentence answer (max 20 words):"""

    try:
        # Set up structured output parser
        parser = JsonOutputParser(pydantic_object=QuestionResponse)

        prompt_template = PromptTemplate(
            template="Answer travel questions in exactly 1 sentence. Maximum 20 words. Be direct and helpful.\n\n{format_instructions}\n\n{query}",
            input_variables=["query"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )

        chain = prompt_template | gradient_llm | parser

        try:
            result = chain.invoke({"query": prompt})
            response = result.get('response', '')
        except Exception as e:
            print(f"[STRUCTURED] Question structured output failed, using fallback: {e}")
            # Fallback to regular call
            messages = [
                SystemMessage(content="Answer travel questions in exactly 1 sentence. Maximum 20 words. Be direct and helpful."),
                HumanMessage(content=prompt)
            ]

            llm_result = gradient_llm.invoke(messages, temperature=0.1, max_tokens=40)
            response = llm_result.content.strip()
        
        # Ensure response ends with period if it doesn't
        if response and not response.endswith('.'):
            response += '.'
        
        return {
            "type": "answer",
            "response": response
        }
        
    except Exception as e:
        print(f"[ERROR] Question error: {type(e).__name__}: {e}")
        # Try a simple fallback response
        try:
            simple_response = f"Check {city} travel guides for {user_question.replace('?', '').lower()}."
            return {
                "type": "answer", 
                "response": simple_response
            }
        except:
            return {
                "type": "answer",
                "response": f"You can find that in {city}. Check local recommendations."
            }

def fast_handle_modification(city: str, interests: str, days: int, existing_places: list, modification_request: str):
    """Fast modification handling using direct OpenAI call with SERP API enhancement"""
    
    if not modification_request or not modification_request.strip():
        return {
            "city": city,
            "interests": interests,
            "days": days,
            "places": existing_places or [],
            "type": "modification",
            "response": "No changes requested."
        }
    
    # Check if this is an "add" request vs other modifications
    is_add_request = any(word in modification_request.lower() for word in ['add', 'include', 'put in', 'insert', 'append'])
    
    # Get relevant places from SERP API with location priority
    if is_add_request:
        print(f"[SERP] Searching for ADD request: {modification_request} specifically in {city}")
        # Simple approach: let SERP API and prompt handle location filtering
        
        # For add requests, be very specific about location
        search_query = f"{modification_request} in {city}"
        serp_places = search_places(search_query, city, 5)
        
        # Enhanced targeted searches with city enforcement
        if any(word in modification_request.lower() for word in ['restaurant', 'food', 'eat', 'dining']):
            serp_places.extend(search_restaurants(city, modification_request, 3))
        elif any(word in modification_request.lower() for word in ['museum', 'art', 'culture', 'gallery']):
            serp_places.extend(search_attractions(city, f"{modification_request} museum gallery", 3))
        elif any(word in modification_request.lower() for word in ['shop', 'market', 'mall']):
            serp_places.extend(search_activities(city, f"{modification_request} shopping market", 3))
        else:
            serp_places.extend(search_attractions(city, modification_request, 3))
    else:
        print(f"[SERP] Searching for MODIFY request: {modification_request} in {city}")
        # For other modifications (remove, replace), less strict location filtering
        search_query = modification_request
        serp_places = search_places(search_query, city, 3)
    
    print(f"[SERP] Found {len(serp_places)} relevant places for modification")
    
    # Format SERP results for the prompt with location emphasis
    serp_context = ""
    if serp_places:
        if is_add_request:
            serp_context = f"CURRENT SEARCH RESULTS FOR NEW PLACES IN {city.upper()}:\n"
        else:
            serp_context = "CURRENT SEARCH RESULTS FOR MODIFICATION:\n"
        
        for i, place in enumerate(serp_places[:8], 1):  # Limit to top 8
            place_info = f"{i}. {place.get('name', 'Unknown')}"
            if place.get('address'):
                place_info += f" - {place.get('address')}"
            if place.get('description'):
                place_info += f" - {place.get('description')[:80]}..."
            if place.get('rating'):
                place_info += f" (Rating: {place.get('rating')})"
            serp_context += place_info + "\n"
        serp_context += "\n"
    
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

{serp_context}User Request: "{modification_request}"
{location_constraint}

Use ONLY the search results above when adding new places. Prioritize places with good ratings that are clearly located in {city}.

CRITICAL INSTRUCTIONS - READ CAREFULLY:"""
    else:
        prompt = f"""You are modifying a travel itinerary. Here's the current situation:

City: {city}
Current Places: {places_json}

{serp_context}User Request: "{modification_request}"

Use the search results above when modifying places. Prioritize places with good ratings and detailed information.

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

    try:
        # Set up structured output parser
        parser = JsonOutputParser(pydantic_object=ModificationResponse)

        prompt_template = PromptTemplate(
            template="You are a travel assistant. Return valid JSON for itinerary modifications.\n\n{format_instructions}\n\n{query}",
            input_variables=["query"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )

        chain = prompt_template | gradient_llm | parser

        try:
            result = chain.invoke({"query": prompt})
            updated_places = result.get('places', existing_places or [])
            response_text = result.get('response', 'I\'ve processed your modification request.')
        except Exception as e:
            print(f"[STRUCTURED] Modification structured output failed, using fallback: {e}")
            # Fallback to regular call
            messages = [
                SystemMessage(content="You are a travel assistant. Return only valid JSON for itinerary modifications."),
                HumanMessage(content=prompt)
            ]

            llm_result = gradient_llm.invoke(messages, temperature=0.7, max_tokens=800)
            response = llm_result.content.strip()

            # Clean markdown if present
            if response.startswith('```json'):
                response = response[7:]
            elif response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()

            # Parse JSON
            try:
                data = json.loads(response)
                updated_places = data.get('places', existing_places or [])
                response_text = data.get('response', 'I\'ve processed your modification request.')
            except json.JSONDecodeError:
                # Ultimate fallback
                updated_places = existing_places or []
                response_text = "I've processed your request."
            
            # Geocode missing coordinates for new places
            if MAPBOX_TOKEN and updated_places:
                for place in updated_places:
                    if place.get("latitude") is not None and place.get("longitude") is not None:
                        continue
                    
                    # Build search query with city, country for better accuracy
                    place_name = place.get("name")
                    address = place.get("address")
                    
                    # Add "India" to help disambiguate Indian cities from other countries
                    query_parts = [place_name, address, f"{city}, India"]
                    query = ", ".join([q for q in query_parts if q])
                    
                    try:
                        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{requests.utils.quote(query)}.json"
                        resp = requests.get(url, params={"access_token": MAPBOX_TOKEN, "limit": 1}, timeout=10)
                        if resp.ok:
                            features = resp.json().get("features", [])
                            if features:
                                longitude, latitude = features[0]["center"]
                                place["latitude"] = latitude
                                place["longitude"] = longitude
                                if not place.get("address"):
                                    place["address"] = features[0].get("place_name")
                    except Exception:
                        # If geocoding fails, set to None (will be skipped in frontend)
                        place["latitude"] = None
                        place["longitude"] = None

        return {
            "city": city,
            "interests": interests,
            "days": days,
            "places": updated_places,
            "type": "modification",
            "response": response_text
        }
        
    except Exception as e:
        print(f"Fast modification error: {e}")
        return {
            "city": city,
            "interests": interests,
            "days": days,
            "places": existing_places or [],
            "type": "modification",
            "response": "I'm having trouble processing that request right now."
        }

def fast_extract_trip_request(trip_request_text: str):
    """Fast trip request extraction using direct OpenAI call"""
    
    if not trip_request_text or not trip_request_text.strip():
        return {"city": "Bangalore", "interests": "art, food", "days": 1}
    
    prompt = f"""Extract travel details from this request: "{trip_request_text}"

Return ONLY a JSON object with these exact keys:
{{
  "city": "City Name",
  "interests": "comma, separated, interests",
  "days": number
}}

If any information is missing, use reasonable defaults."""

    try:
        # Set up structured output parser
        parser = JsonOutputParser(pydantic_object=TripExtractionResponse)

        prompt_template = PromptTemplate(
            template="Extract travel information from the request.\n\n{format_instructions}\n\n{query}",
            input_variables=["query"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )

        chain = prompt_template | gradient_llm | parser

        try:
            result = chain.invoke({"query": prompt})
            if all(k in result for k in ["city", "interests", "days"]):
                return result
        except Exception as e:
            print(f"[STRUCTURED] Extraction structured output failed, using fallback: {e}")
            # Fallback to regular call
            messages = [
                SystemMessage(content="Extract travel information. Return only valid JSON."),
                HumanMessage(content=prompt)
            ]

            llm_result = gradient_llm.invoke(messages, temperature=0.3, max_tokens=150)
            response = llm_result.content.strip()

            # Clean markdown if present
            if response.startswith('```json'):
                response = response[7:]
            elif response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()

            try:
                data = json.loads(response)
                if all(k in data for k in ["city", "interests", "days"]):
                    return data
            except:
                pass
            
    except Exception as e:
        print(f"Fast extraction error: {e}")
    
    # Fallback
    return {"city": "Bangalore", "interests": "art, food", "days": 1}
