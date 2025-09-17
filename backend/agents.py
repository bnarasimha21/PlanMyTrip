from crewai import Agent, Crew, Task
import os
import json
import requests
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
MAPBOX_TOKEN = os.getenv("MAPBOX_API_KEY") or os.getenv("MAPBOX_ACCESS_TOKEN")

# Define agents
research_agent = Agent(
    name="ResearchAgent",
    role="Travel Researcher",
    goal="Find must see places in the city based on user interests",
    backstory="Expert in travel and local recommendations.",
    llm="gpt-4o-mini"
)

itinerary_agent = Agent(
    name="ItineraryAgent",
    role="Itinerary Planner",
    goal="Create a itinerary based on user interests and research",
    backstory="Specialist in optimizing travel plans based on user interests and research.",
    llm="gpt-4o-mini"
)

# Question handler agent to answer travel-related questions
question_agent = Agent(
    name="QuestionAgent",
    role="Travel Information Assistant",
    goal="Answer user questions about travel, routes, recommendations, and general travel advice",
    backstory="Expert travel consultant who provides helpful answers about destinations, routes, travel tips, and recommendations without modifying any itineraries.",
    llm="gpt-4o-mini"
)

# Modification handler agent to update itineraries
modification_agent = Agent(
    name="ModificationAgent", 
    role="Itinerary Modifier",
    goal="Update and modify travel itineraries based on user requests",
    backstory="Specialist in adjusting travel plans, adding/removing places, and updating itineraries based on user preferences while maintaining trip coherence.",
    llm="gpt-4o-mini"
)

# ExtractorAgent to parse free-form trip requests
extractor_agent = Agent(
    name="ExtractorAgent",
    role="Request Extractor",
    goal="Extract city (or cities), interests list, and number of days from a free-form trip request",
    backstory="Expert at understanding natural language requests and producing clean structured JSON fields for downstream agents.",
    llm="gpt-4o-mini"
)

def get_itinerary(city: str, interests: str, days: int):
    research_task = Task(
        description=f"Find the best {interests} places in {city}.",
        agent=research_agent,
        expected_output=(
            "Return STRICT JSON only with key 'places' as a list of objects: "
            "[{ 'name': str, 'neighborhood': str | null, 'category': str, 'address': str | null, "
            "'latitude': float | null, 'longitude': float | null, 'notes': str }]."
        )
    )
    
    crew = Crew(tasks=[research_task])
    result = crew.kickoff()

    # Extract the actual content from CrewOutput (same fix as in question/modification functions)
    raw_research_output = None
    if hasattr(result, 'raw'):
        raw_research_output = str(result.raw).strip()
    elif hasattr(result, '__str__'):
        raw_research_output = str(result).strip()
    elif isinstance(result, str):
        raw_research_output = result.strip()
    elif isinstance(result, dict):
        raw_research_output = result.get(research_task) or result.get("final_output")

    places = []
    if raw_research_output:
        # Clean the output by removing markdown code blocks if present
        cleaned_output = raw_research_output
        if cleaned_output.startswith('```json'):
            cleaned_output = cleaned_output[7:]  # Remove ```json
        elif cleaned_output.startswith('```'):
            cleaned_output = cleaned_output[3:]   # Remove ```
        if cleaned_output.endswith('```'):
            cleaned_output = cleaned_output[:-3]  # Remove trailing ```
        cleaned_output = cleaned_output.strip()
        
        # Try to parse as JSON first
        try:
            parsed = json.loads(cleaned_output)
            if isinstance(parsed, dict) and isinstance(parsed.get("places"), list):
                places = parsed.get("places")
        except Exception:
            # Fallback: naive line-based extraction of place names
            lines = [l.strip(" -•*\t") for l in raw_research_output.splitlines() if l.strip()]
            candidate_lines = [l for l in lines if len(l.split()) <= 12 or any(ch.isdigit() for ch in l[:3])]
            unique_names = []
            for line in candidate_lines:
                name = line.split(" - ")[0].split(" – ")[0].split(":")[0].split("(")[0].strip()
                if name and name not in unique_names:
                    unique_names.append(name)
            places = [{"name": n, "neighborhood": None, "category": None, "address": None, "latitude": None, "longitude": None, "notes": None} for n in unique_names[:15]]

    # Fallback: if we still have no places, ask OpenAI directly for JSON
    if not places:
        try:
            completion = openai.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "Return ONLY valid JSON with a 'places' array of travel destinations."},
                    {"role": "user", "content": f"Find the best {interests} places in {city}. Return JSON with key 'places' containing an array of place objects with name, neighborhood, category, address, latitude, longitude, notes."},
                ],
                temperature=0.7,
            )
            fallback_response = completion.choices[0].message.content.strip()
            fallback_payload = json.loads(fallback_response)
            if isinstance(fallback_payload, dict) and isinstance(fallback_payload.get("places"), list):
                places = fallback_payload.get("places")
        except Exception:
            pass

    # Geocode missing coordinates using Mapbox
    if MAPBOX_TOKEN and places:
        for place in places:
            if place.get("latitude") is not None and place.get("longitude") is not None:
                continue
            query_parts = [place.get("name"), place.get("address"), city]
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
                continue

    return {
        "city": city,
        "interests": interests,
        "days": days,
        "places": places,
        "raw_research_text": str(raw_research_output) if raw_research_output else None,
    }

def extract_trip_request(trip_request_text: str):
    extract_task = Task(
        description=(
            f"Extract key information from this trip request: '{trip_request_text}'\n"
            "Return STRICT JSON with keys: 'city' (string), 'interests' (string), 'days' (integer).\n"
            "Examples:\n"
            "- 'Plan a 3-day art and food tour in Paris' → {'city': 'Paris', 'interests': 'art, food', 'days': 3}\n"
            "- 'I want to visit Tokyo for 5 days focusing on culture' → {'city': 'Tokyo', 'interests': 'culture', 'days': 5}"
        ),
        agent=extractor_agent,
        expected_output="{ 'city': str, 'interests': str, 'days': int }"
    )
    
    crew = Crew(tasks=[extract_task])
    result = crew.kickoff()
    
    if isinstance(result, dict):
        output = result.get(extract_task) or result.get("final_output")
    else:
        output = result
    
    try:
        if isinstance(output, str):
            parsed = json.loads(output)
        else:
            parsed = output
        
        if isinstance(parsed, dict) and all(k in parsed for k in ["city", "interests", "days"]):
            return parsed
    except Exception:
        pass
    
    return {"city": "Bangalore", "interests": "art, food", "days": 1}

def handle_question(city: str, interests: str, days: int, user_question: str):
    """Handle user questions about travel without modifying any itinerary."""
    if not user_question or not user_question.strip():
        return {
            "type": "answer",
            "response": "Please ask me a question about your travel plans."
        }

    question_task = Task(
        description=(
            f"Answer the user's travel question based on the trip context:\n"
            f"City: {city}\n"
            f"Interests: {interests}\n"
            f"Trip Duration: {days} days\n"
            f"User Question: {user_question}\n\n"
            f"Provide a helpful, informative answer about travel, routes, recommendations, "
            f"or general advice related to their trip. Do not modify any itinerary."
        ),
        agent=question_agent,
        expected_output="A helpful text response answering the user's travel question"
    )

    crew = Crew(tasks=[question_task])
    result = crew.kickoff()

    # Extract response text from CrewOutput
    response_text = "I'm here to help with your travel questions."
    
    # Handle CrewOutput object (newer CrewAI versions)
    if hasattr(result, 'raw'):
        response_text = str(result.raw).strip()
    elif hasattr(result, '__str__'):
        # CrewOutput can be converted to string directly
        response_text = str(result).strip()
    elif isinstance(result, str) and result.strip():
        # Direct string response from CrewAI
        response_text = result.strip()
    elif isinstance(result, dict):
        # Try multiple ways to extract the response from dict
        output = None
        if question_task in result:
            output = result.get(question_task)
        elif "final_output" in result:
            output = result.get("final_output")
        elif len(result.values()) > 0:
            # Get first value from the result dict
            output = list(result.values())[0]
        
        if isinstance(output, str) and output.strip():
            response_text = output.strip()
        elif isinstance(output, dict) and output.get("response"):
            response_text = str(output.get("response"))

    return {
        "type": "answer",
        "response": response_text
    }

def handle_modification(city: str, interests: str, days: int, existing_places: list, modification_request: str):
    """Handle user requests to modify their itinerary."""
    if not modification_request or not modification_request.strip():
        return {
            "city": city,
            "interests": interests,
            "days": days,
            "places": existing_places or [],
            "type": "modification",
            "response": "No changes requested."
        }

    modification_task = Task(
        description=(
            f"Update the itinerary based on the user's modification request:\n"
            f"City: {city}\n"
            f"Interests: {interests}\n"
            f"Days: {days}\n"
            f"Modification Request: {modification_request}\n"
            f"Current places JSON: {json.dumps(existing_places or [], ensure_ascii=False)}\n\n"
            f"IMPORTANT RULES:\n"
            f"- If user says 'add', 'include', or mentions 'to the list/itinerary': KEEP all existing places AND add the new one(s)\n"
            f"- If user says 'remove' or 'delete': Remove only the specified place(s)\n"
            f"- If user says 'replace': Replace only the specified place(s)\n"
            f"- NEVER remove existing places unless explicitly asked to remove them\n"
            f"- The final 'places' array should contain ALL places that should be in the itinerary\n"
            f"- Return STRICT JSON with: {{'type': 'modification', 'response': 'description of changes', 'places': [...updated places...]}}\n"
            f"Place objects: {{'name': str, 'neighborhood': str|null, 'category': str|null, 'address': str|null, "
            f"'latitude': float|null, 'longitude': float|null, 'notes': str|null}}"
        ),
        agent=modification_agent,
        expected_output="JSON object with 'type': 'modification', 'response': description of changes, and 'places': updated array"
    )

    crew = Crew(tasks=[modification_task])
    result = crew.kickoff()

    # Process the result - handle CrewOutput object
    response_text = "I've processed your modification request."
    updated_places = existing_places or []
    
    # Extract the actual content from CrewOutput
    raw_output = None
    if hasattr(result, 'raw'):
        raw_output = str(result.raw).strip()
    elif hasattr(result, '__str__'):
        raw_output = str(result).strip()
    elif isinstance(result, str):
        raw_output = result.strip()
    elif isinstance(result, dict):
        raw_output = result.get(modification_task) or result.get("final_output") or next(iter(result.values()), result)
    
    # Try to parse as JSON (with markdown cleanup)
    parsed_payload = None
    if raw_output:
        # Clean the output by removing markdown code blocks if present
        cleaned_output = raw_output
        if cleaned_output.startswith('```json'):
            cleaned_output = cleaned_output[7:]  # Remove ```json
        elif cleaned_output.startswith('```'):
            cleaned_output = cleaned_output[3:]   # Remove ```
        if cleaned_output.endswith('```'):
            cleaned_output = cleaned_output[:-3]  # Remove trailing ```
        cleaned_output = cleaned_output.strip()
        
        try:
            parsed_payload = json.loads(cleaned_output)
        except Exception:
            parsed_payload = None

    if isinstance(parsed_payload, dict):
        response_text = parsed_payload.get("response", response_text)
        if isinstance(parsed_payload.get("places"), list):
            updated_places = parsed_payload.get("places")
    else:
        # Fallback to direct LLM
        try:
            completion = openai.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "Return JSON with 'type': 'modification', 'response': description, and 'places': updated array."},
                    {"role": "user", "content": f"City: {city}. Interests: {interests}. Days: {days}. Existing places: {json.dumps(existing_places or [])}. Modification request: {modification_request}. Update the places based on the request."},
                ],
                temperature=0.2,
            )
            fallback_response = completion.choices[0].message.content.strip()
            fallback_payload = json.loads(fallback_response)
            if isinstance(fallback_payload, dict):
                response_text = fallback_payload.get("response", response_text)
                if isinstance(fallback_payload.get("places"), list):
                    updated_places = fallback_payload.get("places")
        except Exception:
            pass

    # Geocode missing coordinates for new places
    if MAPBOX_TOKEN and updated_places:
        for p in updated_places:
            if p.get("latitude") is not None and p.get("longitude") is not None:
                continue
            query_parts = [p.get("name"), p.get("address"), city]
            query = ", ".join([q for q in query_parts if q])
            try:
                url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{requests.utils.quote(query)}.json"
                resp = requests.get(url, params={"access_token": MAPBOX_TOKEN, "limit": 1}, timeout=10)
                if resp.ok:
                    feats = resp.json().get("features", [])
                    if feats:
                        lon, lat = feats[0]["center"]
                        p["latitude"] = lat
                        p["longitude"] = lon
                        if not p.get("address"):
                            p["address"] = feats[0].get("place_name")
            except Exception:
                continue

    return {
        "city": city,
        "interests": interests,
        "days": days,
        "places": updated_places,
        "type": "modification",
        "response": response_text,
    }
