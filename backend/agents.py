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

# Optional modifier agent to adjust existing plans based on user instructions
modify_agent = Agent(
    name="ModifyAgent",
    role="Itinerary Refiner",
    goal="Update the existing itinerary and places based on a specific user modification request",
    backstory="Carefully integrates user-specified additions or changes into an existing plan while preserving coherence.",
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

# Define tasks
def get_itinerary(city, interests, days):
    research_task = Task(
        description=f"Find the best {interests} places in {city}.",
        agent=research_agent,
        expected_output=(
            "Return STRICT JSON only with key 'places' as a list of objects: "
            "[{ 'name': str, 'neighborhood': str | null, 'category': str, 'address': str | null, "
            "'latitude': float | null, 'longitude': float | null, 'notes': str }]."
        )
    )
    # itinerary_task = Task(
    #     description=f"Create a {days}-day itinerary in {city} focusing on {interests} using the research.",
    #     agent=itinerary_agent,
    #     expected_output="A structured day-by-day itinerary (morning/afternoon/evening) covering the requested number of days, referencing items from the research and including short logistics tips (distance/area clustering).",
    #     depends_on=[research_task]
    # )
    crew = Crew(tasks=[research_task])
    result = crew.kickoff()

    raw_research_output = None
    if isinstance(result, dict):
        raw_research_output = result.get(research_task) or result.get("final_output")
    else:
        raw_research_output = result

    places = []
    if isinstance(raw_research_output, str):
        # Try JSON first
        try:
            parsed = json.loads(raw_research_output)
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
    elif isinstance(raw_research_output, dict) and isinstance(raw_research_output.get("places"), list):
        places = raw_research_output.get("places")

    # Fallback: if we still have no places, ask OpenAI directly for JSON
    if not places:
        try:
            completion = openai.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a travel research assistant. Return only valid JSON."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"List top art/food places in {city} for interests: {interests}. "
                            "Return JSON with key 'places' as a list of objects: "
                            "[{ 'name': str, 'neighborhood': str | null, 'category': str, 'address': str | null, "
                            "'latitude': float | null, 'longitude': float | null, 'notes': str }]."
                        ),
                    },
                ],
                temperature=0.2,
            )
            content = completion.choices[0].message.content
            raw_research_output = content
            parsed = json.loads(content)
            if isinstance(parsed, dict) and isinstance(parsed.get("places"), list):
                places = parsed.get("places")
        except Exception:
            places = []

    # Geocode with Mapbox for missing coordinates
    mapbox_token = os.getenv("MAPBOX_API_KEY") or os.getenv("MAPBOX_ACCESS_TOKEN")
    if mapbox_token and places:
        for p in places:
            lat = p.get("latitude")
            lon = p.get("longitude")
            if lat and lon:
                continue
            query_parts = [p.get("name"), p.get("address"), city]
            query = ", ".join([q for q in query_parts if q])
            try:
                url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{requests.utils.quote(query)}.json"
                resp = requests.get(url, params={"access_token": mapbox_token, "limit": 1}, timeout=10)
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
        "places": places,
        "raw_research_text": raw_research_output if isinstance(raw_research_output, str) else None,
    }


def extract_trip_request(trip_request_text: str):
    """Use ExtractorAgent to parse trip request into {city, interests, days}.

    Returns defaults when not confidently extracted.
    """
    if not trip_request_text or not trip_request_text.strip():
        return {"city": "Bangalore", "interests": "art, food", "days": 1}

    task = Task(
        description=(
            "Extract structured fields from the following user request.\n"
            f"Request: {trip_request_text}\n"
            "Return STRICT JSON with keys: city (str), interests (str, comma-separated), days (int).\n"
            "If multiple cities are mentioned, choose the primary one. If days not given, infer a reasonable default between 1 and 7."
        ),
        agent=extractor_agent,
        expected_output="{ 'city': str, 'interests': str, 'days': int }",
    )
    crew = Crew(tasks=[task])
    result = crew.kickoff()
    payload = None
    if isinstance(result, dict):
        output = result.get(task) or result.get("final_output") or next(iter(result.values()), None)
        try:
            payload = json.loads(output) if isinstance(output, str) else output
        except Exception:
            payload = None
    if isinstance(payload, dict):
        city = payload.get("city") or "Bangalore"
        interests = payload.get("interests") or "art, food"
        try:
            days = int(payload.get("days", 1))
        except Exception:
            days = 1
        days = max(1, min(7, days))
        return {"city": city, "interests": interests, "days": days}
    # Fallback
    return {"city": "Bangalore", "interests": "art, food", "days": 1}


def apply_modification(city: str, interests: str, days: int, existing_places: list, instruction: str):
    """Apply a user-specified modification to the itinerary using CrewAI conditionally.

    If no instruction is provided, returns the existing data unchanged.
    """
    if not instruction or not instruction.strip():
        return {
            "city": city,
            "interests": interests,
            "days": days,
            "places": existing_places or [],
        }

    # Build a conditional modify task only when there is an instruction
    modify_task = Task(
        description=(
            "Given the existing places (JSON below) and the user instruction, update the list.\n"
            f"City: {city}\nInterests: {interests}\nDays: {days}\n"
            f"Instruction: {instruction}\n"
            f"Existing places JSON: {json.dumps(existing_places or [], ensure_ascii=False)}\n"
            "Return STRICT JSON with key 'places' as a list of objects: "
            "[{ 'name': str, 'neighborhood': str | null, 'category': str | null, 'address': str | null, "
            "'latitude': float | null, 'longitude': float | null, 'notes': str | null }].\n"
            "Always preserve existing entries unless the instruction requires changing them."
        ),
        agent=modify_agent,
        expected_output=(
            "{ 'places': [ { 'name': str, 'neighborhood': str | null, 'category': str | null, 'address': str | null, "
            "'latitude': float | null, 'longitude': float | null, 'notes': str | null } ] }"
        ),
    )

    crew = Crew(tasks=[modify_task])
    result = crew.kickoff()

    modified_places = existing_places or []
    parsed_payload = None
    if isinstance(result, dict):
        output = None
        if modify_task in result:
            output = result.get(modify_task)
        elif "final_output" in result:
            output = result.get("final_output")
        elif len(result.values()) > 0:
            try:
                output = next(iter(result.values()))
            except Exception:
                output = result
        try:
            parsed_payload = json.loads(output) if isinstance(output, str) else output
        except Exception:
            parsed_payload = None
    elif isinstance(result, str):
        try:
            parsed_payload = json.loads(result)
        except Exception:
            parsed_payload = None

    if isinstance(parsed_payload, dict) and isinstance(parsed_payload.get("places"), list):
        modified_places = parsed_payload.get("places")
    else:
        # Fallback to direct LLM if Crew output is not parseable
        try:
            completion = openai.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "Return ONLY valid JSON with a 'places' array."},
                    {
                        "role": "user",
                        "content": (
                            f"City: {city}. Interests: {interests}. Existing places: {json.dumps(existing_places or [])}. "
                            f"Instruction: {instruction}. Return JSON with key 'places' as described."
                        ),
                    },
                ],
                temperature=0.2,
            )
            content = completion.choices[0].message.content
            payload = json.loads(content)
            if isinstance(payload, dict) and isinstance(payload.get("places"), list):
                modified_places = payload.get("places")
        except Exception:
            modified_places = existing_places or []

    # Geocode missing coordinates using Mapbox for modified list
    mapbox_token = os.getenv("MAPBOX_API_KEY") or os.getenv("MAPBOX_ACCESS_TOKEN")
    if mapbox_token and modified_places:
        for p in modified_places:
            if p.get("latitude") is not None and p.get("longitude") is not None:
                continue
            query_parts = [p.get("name"), p.get("address"), city]
            query = ", ".join([q for q in query_parts if q])
            try:
                url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{requests.utils.quote(query)}.json"
                resp = requests.get(url, params={"access_token": mapbox_token, "limit": 1}, timeout=10)
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
        "places": modified_places,
    }