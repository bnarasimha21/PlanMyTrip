from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, List, Optional, Dict

from fast_agents import fast_extract_trip_request, fast_get_itinerary, fast_handle_question, fast_handle_modification, classify_user_intent, test_classifier


app = FastAPI(title="LetMePlanMyTrip API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExtractRequest(BaseModel):
    text: str


class ItineraryRequest(BaseModel):
    city: Optional[str] = None
    interests: Optional[str] = None
    days: Optional[int] = None
    trip_request: Optional[str] = None


class Place(BaseModel):
    name: str
    neighborhood: Optional[str] = None
    category: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None


class ModifyRequest(BaseModel):
    city: str
    interests: str
    days: int
    places: List[Place]
    instruction: str
    original_request: Optional[str] = None
    chat_history: Optional[List[Dict[str, Any]]] = None

@app.get("/")
def home() -> Dict[str, Any]:
    return {"status": "ok", "message": "LetMePlanMyTrip API is running"}

@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok"}


@app.post("/extract")
def extract(req: ExtractRequest) -> Dict[str, Any]:
    parsed = fast_extract_trip_request(req.text)  # Use fast version
    return parsed


@app.post("/itinerary")
def itinerary(req: ItineraryRequest) -> Dict[str, Any]:
    if req.trip_request and not (req.city and req.interests and req.days):
        parsed = fast_extract_trip_request(req.trip_request)  # Use fast version
        city = parsed["city"]
        interests = parsed["interests"]
        days = parsed["days"]
    else:
        city = req.city or "Bangalore"
        interests = req.interests or "art, food"
        days = req.days or 1
    data = fast_get_itinerary(city=city, interests=interests, days=days)  # Use fast version
    return data  # {city, interests, days, places, raw_research_text}


@app.post("/modify")
def modify(req: ModifyRequest) -> Dict[str, Any]:
    print(f"\n=== /modify endpoint called ===")
    print(f"Instruction: '{req.instruction}'")
    print(f"City: {req.city}, Days: {req.days}")
    
    places_dicts = [p.model_dump() for p in req.places]
    print(f"Number of existing places: {len(places_dicts)}")
    
    # Use AI to intelligently classify the user's intent
    context = f"User is planning a {req.days}-day trip to {req.city} with interests in {req.interests}. "
    if places_dicts:
        place_names = [p.get('name', 'Unknown') for p in places_dicts[:5]]  # First 5 places for context
        context += f"Current itinerary includes: {', '.join(place_names)}."
    else:
        context += "No places in itinerary yet."
    
    print(f"About to call classify_user_intent...")
    user_intent = classify_user_intent(req.instruction, context)
    print(f"classify_user_intent returned: '{user_intent}'")
    is_question = (user_intent == 'question')
    
    # Log classification for debugging
    print(f"User input: '{req.instruction}' -> Classified as: '{user_intent}'")
    
    if is_question:
        # Handle as question - no places modification
        response = fast_handle_question(  # Use fast version
            city=req.city,
            interests=req.interests,
            days=req.days,
            user_question=req.instruction,
            original_request=req.original_request,
            current_places=places_dicts,
            chat_history=req.chat_history,
        )
        
        # Log the response for debugging
        print(f"[API DEBUG] Response received: {response.get('response', 'NO RESPONSE')[:100]}...")
        
        # Add places for consistency with frontend expectations
        response["city"] = req.city
        response["interests"] = req.interests
        response["days"] = req.days
        response["places"] = places_dicts  # Keep existing places unchanged
    else:
        # Handle as modification request
        response = fast_handle_modification(  # Use fast version
            city=req.city,
            interests=req.interests,
            days=req.days,
            existing_places=places_dicts,
            modification_request=req.instruction,
        )
    
    return response


@app.get("/test-classifier")
def test_classification() -> Dict[str, Any]:
    """Test endpoint to verify classifier is working correctly"""
    try:
        test_classifier()
        return {"status": "success", "message": "Check console output for test results"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
