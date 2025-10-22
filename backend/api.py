from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, List, Optional, Dict
import io
import tempfile
import os

# Import the new simplified workflow
from agents.simple_workflow import trip_workflow

# Import payment service
from payment_service import payment_service

# Import GTTS for text-to-speech
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    print("GTTS not available. Install with: pip install gtts")

app = FastAPI(title="LetMePlanMyTrip API (LangGraph)", version="2.0.0")

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

class TTSRequest(BaseModel):
    text: str
    lang: Optional[str] = "en"

class CreateOrderRequest(BaseModel):
    amount: int
    currency: Optional[str] = "INR"
    receipt: Optional[str] = None

class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

@app.get("/")
def home() -> Dict[str, Any]:
    return {"status": "ok", "message": "LetMePlanMyTrip API (LangGraph) is running"}

@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "version": "2.0.0", "backend": "LangGraph"}

@app.post("/extract")
def extract(req: ExtractRequest) -> Dict[str, Any]:
    """Extract trip details using LangGraph agents"""
    try:
        result = trip_workflow.extract_trip_request(req.text)
        return result
    except Exception as e:
        print(f"Extract error: {e}")
        return {"city": "Bangalore", "interests": "art, food", "days": 1}

@app.post("/itinerary")
def itinerary(req: ItineraryRequest) -> Dict[str, Any]:
    """Generate itinerary using LangGraph agents"""
    try:
        if req.trip_request and not (req.city and req.interests and req.days):
            # Extract details first if needed
            extracted = trip_workflow.extract_trip_request(req.trip_request)
            city = extracted["city"]
            interests = extracted["interests"]
            days = extracted["days"]
        else:
            city = req.city or "Bangalore"
            interests = req.interests or "art, food"
            days = req.days or 1

        result = trip_workflow.generate_itinerary(city=city, interests=interests, days=days)
        return result

    except Exception as e:
        print(f"Itinerary error: {e}")
        return {
            "city": city if 'city' in locals() else "Bangalore",
            "interests": interests if 'interests' in locals() else "art, food",
            "days": days if 'days' in locals() else 1,
            "places": [],
            "raw_research_text": None
        }

@app.post("/modify")
def modify(req: ModifyRequest) -> Dict[str, Any]:
    """Handle modifications using LangGraph agents"""
    try:
        print(f"\n=== /modify endpoint called (LangGraph) ===")
        print(f"Instruction: '{req.instruction}'")
        print(f"City: {req.city}, Days: {req.days}")

        places_dicts = [p.model_dump() for p in req.places]
        print(f"Number of existing places: {len(places_dicts)}")

        result = trip_workflow.handle_modification(
            city=req.city,
            interests=req.interests,
            days=req.days,
            existing_places=places_dicts,
            instruction=req.instruction,
            original_request=req.original_request,
            chat_history=req.chat_history
        )

        return result

    except Exception as e:
        print(f"Modify error: {e}")
        return {
            "city": req.city,
            "interests": req.interests,
            "days": req.days,
            "places": [p.model_dump() for p in req.places],
            "type": "modification",
            "response": "I'm having trouble processing that request right now."
        }

@app.post("/tts")
def text_to_speech(req: TTSRequest):
    """Generate audio from text using GTTS"""
    if not GTTS_AVAILABLE:
        return {"error": "GTTS not available"}

    try:
        # Create GTTS object
        tts = gTTS(text=req.text, lang=req.lang, slow=False)

        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            tts.save(temp_file.name)

            # Read the audio file
            with open(temp_file.name, "rb") as audio_file:
                audio_data = audio_file.read()

            # Clean up temp file
            os.unlink(temp_file.name)

            # Return audio file
            return Response(
                content=audio_data,
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": "inline; filename=speech.mp3"
                }
            )

    except Exception as e:
        return {"error": str(e)}

@app.post("/payment/create-order")
def create_payment_order(req: CreateOrderRequest) -> Dict[str, Any]:
    """Create a Razorpay order for payment"""
    try:
        result = payment_service.create_order(
            amount=req.amount,
            currency=req.currency,
            receipt=req.receipt
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/payment/verify")
def verify_payment(req: VerifyPaymentRequest) -> Dict[str, Any]:
    """Verify Razorpay payment signature"""
    try:
        result = payment_service.verify_payment(
            razorpay_order_id=req.razorpay_order_id,
            razorpay_payment_id=req.razorpay_payment_id,
            razorpay_signature=req.razorpay_signature
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/payment/details/{payment_id}")
def get_payment_details(payment_id: str) -> Dict[str, Any]:
    """Get payment details from Razorpay"""
    try:
        result = payment_service.get_payment_details(payment_id)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

# Test endpoint for the new workflow
@app.get("/test-workflow")
def test_workflow() -> Dict[str, Any]:
    """Test endpoint to verify LangGraph workflow is working"""
    try:
        # Test extraction
        extraction_result = trip_workflow.extract_trip_request("Plan a 2-day food tour in Tokyo")

        # Test itinerary generation
        itinerary_result = trip_workflow.generate_itinerary("Tokyo", "food", 2)

        return {
            "status": "success",
            "extraction_test": extraction_result,
            "itinerary_places_count": len(itinerary_result.get("places", [])),
            "message": "LangGraph workflow is functioning correctly"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)