from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, List, Optional, Dict

from agents import extract_trip_request, get_itinerary, apply_modification


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
    parsed = extract_trip_request(req.text)
    return parsed


@app.post("/itinerary")
def itinerary(req: ItineraryRequest) -> Dict[str, Any]:
    if req.trip_request and not (req.city and req.interests and req.days):
        parsed = extract_trip_request(req.trip_request)
        city = parsed["city"]
        interests = parsed["interests"]
        days = parsed["days"]
    else:
        city = req.city or "Bangalore"
        interests = req.interests or "art, food"
        days = req.days or 1
    data = get_itinerary(city=city, interests=interests, days=days)
    return data  # {city, interests, days, places, raw_research_text}


@app.post("/modify")
def modify(req: ModifyRequest) -> Dict[str, Any]:
    places_dicts = [p.model_dump() for p in req.places]
    updated = apply_modification(
        city=req.city,
        interests=req.interests,
        days=req.days,
        existing_places=places_dicts,
        instruction=req.instruction,
    )
    return updated  # {city, interests, days, places}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
