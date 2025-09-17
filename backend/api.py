from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, List, Optional, Dict

from fast_agents import fast_extract_trip_request, fast_get_itinerary, fast_handle_question, fast_handle_modification


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
    places_dicts = [p.model_dump() for p in req.places]
    
    # Determine if this is a question or modification request
    instruction = req.instruction.lower().strip()
    
    # Question indicators
    question_words = ['what', 'how', 'where', 'when', 'why', 'which', 'who']
    question_phrases = ['best route', 'how far', 'distance', 'recommend', 'suggest', 'advice']
    
    is_question = (
        instruction.endswith('?') or
        any(instruction.startswith(word) for word in question_words) or
        any(phrase in instruction for phrase in question_phrases)
    )
    
    if is_question:
        # Handle as question - no places modification
        response = fast_handle_question(  # Use fast version
            city=req.city,
            interests=req.interests,
            days=req.days,
            user_question=req.instruction,
        )
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
