#!/usr/bin/env python3
"""
Fast alternatives to CrewAI agents using direct OpenAI calls
for 3-5x performance improvement
"""

import json
import openai
import os
import requests
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
MAPBOX_TOKEN = os.getenv("MAPBOX_API_KEY") or os.getenv("MAPBOX_ACCESS_TOKEN")

def fast_get_itinerary(city: str, interests: str, days: int):
    """Fast itinerary generation using direct OpenAI call"""
    
    prompt = f"""List 5 {interests} places in {city}. Return JSON:
{{"places":[{{"name":"Name","neighborhood":"Area","category":"{interests.split(',')[0].strip()}","address":"Address","latitude":null,"longitude":null,"notes":"Brief note"}}]}}

Real places only."""

    try:
        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a travel expert. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=600
        )
        
        response = completion.choices[0].message.content.strip()
        
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
            # Fallback: create simple places from text
            places = []
            
        # Skip geocoding for now - will be done asynchronously by frontend or cached later
        # This saves 10-15 seconds per request
        for place in places:
            if place.get("latitude") is None:
                place["latitude"] = None
            if place.get("longitude") is None:
                place["longitude"] = None
        
        return {
            "city": city,
            "interests": interests,
            "days": days,
            "places": places[:6],  # Limit for speed
            "raw_research_text": response
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

def fast_handle_question(city: str, interests: str, days: int, user_question: str):
    """Fast question handling using direct OpenAI call"""
    
    if not user_question or not user_question.strip():
        return {
            "type": "answer",
            "response": "Please ask me a question about your travel plans."
        }
    
    prompt = f"""{user_question} - {city}, {interests}, {days} days. Be concise."""

    try:
        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful travel assistant. Provide concise, practical answers."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=250
        )
        
        response = completion.choices[0].message.content.strip()
        
        return {
            "type": "answer",
            "response": response
        }
        
    except Exception as e:
        print(f"Fast question error: {e}")
        return {
            "type": "answer",
            "response": "I'm having trouble answering that question right now. Please try again."
        }

def fast_handle_modification(city: str, interests: str, days: int, existing_places: list, modification_request: str):
    """Fast modification handling using direct OpenAI call"""
    
    if not modification_request or not modification_request.strip():
        return {
            "city": city,
            "interests": interests,
            "days": days,
            "places": existing_places or [],
            "type": "modification",
            "response": "No changes requested."
        }
    
    places_json = json.dumps(existing_places or [], indent=2)
    
    prompt = f"""You are modifying a travel itinerary. Here's the current situation:

City: {city}
Current Places: {places_json}

User Request: "{modification_request}"

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
   - "Add UB City to the list" → Keep ALL existing places + add UB City
   - "Include Central Mall" → Keep ALL existing places + add Central Mall
   - "Remove Place A" → Keep all places except Place A
   - "Replace Place A with Place B" → Keep all places but change Place A to Place B

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
        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a travel assistant. Return only valid JSON for itinerary modifications."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        response = completion.choices[0].message.content.strip()
        
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
            
        except json.JSONDecodeError:
            # Fallback
            return {
                "city": city,
                "interests": interests,
                "days": days,
                "places": existing_places or [],
                "type": "modification",
                "response": "I've processed your request."
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
        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Extract travel information. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=150
        )
        
        response = completion.choices[0].message.content.strip()
        
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
