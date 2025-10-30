from fastapi import FastAPI, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, List, Optional, Dict
import io
import tempfile
import os
import json
from datetime import datetime, timedelta

# Import the new simplified workflow
from agents.simple_workflow import trip_workflow

# Import payment service
from payment_service import payment_service

# Import database manager
from database import db_manager

# Import GTTS for text-to-speech
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    print("GTTS not available. Install with: pip install gtts")

app = FastAPI(title="TripXplorer API (LangGraph)", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Admin stats endpoint
@app.get("/admin/stats")
def admin_stats() -> Dict[str, Any]:
    """Return aggregate stats for admin dashboard"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Total users
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]

            # Admin users
            try:
                cursor.execute("SELECT COUNT(*) FROM users WHERE IsAdmin = 1")
                admin_users = cursor.fetchone()[0]
            except Exception:
                admin_users = 0

            # Total trips
            cursor.execute("SELECT COUNT(*) FROM trip_history")
            total_trips = cursor.fetchone()[0]

            # Trips this month
            cursor.execute("SELECT COUNT(*) FROM trip_history WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')")
            monthly_trips = cursor.fetchone()[0]

            # Subscription breakdown
            cursor.execute("SELECT plan, COUNT(*) FROM subscriptions WHERE status='active' GROUP BY plan")
            subs = {row[0]: row[1] for row in cursor.fetchall()}

            # Top 10 freemium users by total trips
            cursor.execute(
                """
                SELECT u.name, u.email, u.user_id, COUNT(t.id) as trips
                FROM users u
                JOIN subscriptions s ON s.user_id = u.user_id AND s.status='active'
                LEFT JOIN trip_history t ON t.user_id = u.user_id
                WHERE s.plan = 'freemium'
                GROUP BY u.user_id
                ORDER BY trips DESC
                LIMIT 10
                """
            )
            top_freemium = [
                {"name": r[0] or "-", "email": r[1] or "-", "user_id": r[2], "trips": r[3] or 0}
                for r in cursor.fetchall()
            ]

            # Top 10 premium users by total trips
            cursor.execute(
                """
                SELECT u.name, u.email, u.user_id, COUNT(t.id) as trips
                FROM users u
                JOIN subscriptions s ON s.user_id = u.user_id AND s.status='active'
                LEFT JOIN trip_history t ON t.user_id = u.user_id
                WHERE s.plan = 'premium'
                GROUP BY u.user_id
                ORDER BY trips DESC
                LIMIT 10
                """
            )
            top_premium = [
                {"name": r[0] or "-", "email": r[1] or "-", "user_id": r[2], "trips": r[3] or 0}
                for r in cursor.fetchall()
            ]

            # Recent activity: last 10 trips
            cursor.execute(
                """
                SELECT t.id, t.user_id, u.name, u.email, t.city, t.created_at
                FROM trip_history t
                LEFT JOIN users u ON u.user_id = t.user_id
                ORDER BY t.created_at DESC
                LIMIT 10
                """
            )
            recent_trips = [
                {
                    "id": r[0],
                    "user_id": r[1],
                    "name": r[2] or "-",
                    "email": r[3] or "-",
                    "city": r[4] or "-",
                    "created_at": r[5]
                }
                for r in cursor.fetchall()
            ]

            # Power users this month (top 10)
            cursor.execute(
                """
                SELECT u.name, u.email, u.user_id, COUNT(t.id) as trips
                FROM users u
                LEFT JOIN trip_history t ON t.user_id = u.user_id
                WHERE strftime('%Y-%m', t.created_at) = strftime('%Y-%m', 'now')
                GROUP BY u.user_id
                ORDER BY trips DESC
                LIMIT 10
                """
            )
            power_users_month = [
                {"name": r[0] or "-", "email": r[1] or "-", "user_id": r[2], "trips": r[3] or 0}
                for r in cursor.fetchall()
            ]

            # Top cities this month (top 10)
            cursor.execute(
                """
                SELECT city, COUNT(*) as trips
                FROM trip_history
                WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now') AND city IS NOT NULL AND city <> ''
                GROUP BY city
                ORDER BY trips DESC
                LIMIT 10
                """
            )
            top_cities_month = [
                {"city": r[0], "trips": r[1]}
                for r in cursor.fetchall()
            ]

            # Trips per day for last 14 days
            cursor.execute(
                """
                SELECT strftime('%Y-%m-%d', created_at) as d, COUNT(*) as count
                FROM trip_history
                WHERE date(created_at) >= date('now', '-13 days')
                GROUP BY d
                ORDER BY d ASC
                """
            )
            trips_per_day_rows = cursor.fetchall()
            trips_per_day = {row[0]: row[1] for row in trips_per_day_rows}

            return {
                "success": True,
                "stats": {
                    "total_users": total_users,
                    "admin_users": admin_users,
                    "total_trips": total_trips,
                    "monthly_trips": monthly_trips,
                    "subscriptions": {
                        "freemium": subs.get("freemium", 0),
                        "premium": subs.get("premium", 0)
                    },
                    "top_users": {
                        "freemium": top_freemium,
                        "premium": top_premium
                    },
                    "recent_trips": recent_trips,
                    "power_users_month": power_users_month,
                    "top_cities_month": top_cities_month,
                    "trips_per_day_14": trips_per_day
                }
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


# Subscription plan limits
SUBSCRIPTION_LIMITS = {
    "freemium": {
        "max_trips_per_month": 3,
        "max_days_per_trip": 1,
        "features": ["basic_ai", "interactive_maps", "basic_voice", "community_support"]
    },
    "premium": {
        "max_trips_per_month": -1,  # -1 means unlimited
        "max_days_per_trip": 30,
        "features": ["unlimited_trips", "advanced_ai", "route_optimization", "multi_day", "advanced_voice", "priority_support", "export", "offline_maps", "weather", "budget_tracking", "group_planning"]
    }
}

def get_user_subscription_plan(user_id: str = "default") -> str:
    """Get user's subscription plan from database."""
    try:
        user_data = db_manager.get_user(user_id)
        if user_data and user_data.get('plan'):
            return user_data['plan']
        return "freemium"  # Default to freemium
    except Exception as e:
        print(f"Error getting user subscription plan: {e}")
        return "freemium"

def check_usage_limit(user_id: str, plan: str, current_month: str) -> Dict[str, Any]:
    """Check if user has exceeded their usage limits."""
    if plan not in SUBSCRIPTION_LIMITS:
        plan = "freemium"
    
    limits = SUBSCRIPTION_LIMITS[plan]
    
    try:
        # Get usage from database
        usage_data = db_manager.get_usage(user_id, current_month)
        trips_used = usage_data.get('trips_used', 0)
        max_trips = limits["max_trips_per_month"]
        
        # Check trip limit
        if max_trips != -1 and trips_used >= max_trips:
            return {
                "allowed": False,
                "reason": "trip_limit_exceeded",
                "message": f"You've reached your monthly limit of {max_trips} trip plans. Upgrade to Premium for unlimited trips!",
                "usage": {"trips_used": trips_used, "max_trips": max_trips}
            }
        
        return {
            "allowed": True,
            "usage": {"trips_used": trips_used, "max_trips": max_trips}
        }
    except Exception as e:
        print(f"Error checking usage limit: {e}")
        return {
            "allowed": False,
            "reason": "error",
            "message": "Error checking usage limits. Please try again.",
            "usage": {"trips_used": 0, "max_trips": 3}
        }

def check_days_limit(plan: str, days: int) -> Dict[str, Any]:
    """Check if the requested trip duration is allowed for the plan."""
    if plan not in SUBSCRIPTION_LIMITS:
        plan = "freemium"
    
    limits = SUBSCRIPTION_LIMITS[plan]
    max_days = limits["max_days_per_trip"]
    
    if days > max_days:
        return {
            "allowed": False,
            "reason": "days_limit_exceeded",
            "message": f"Your {plan} plan allows up to {max_days} day{'s' if max_days != 1 else ''} per trip. Upgrade to Premium for up to 30 days!",
            "usage": {"requested_days": days, "max_days": max_days}
        }
    
    return {"allowed": True}

def increment_usage(user_id: str, current_month: str):
    """Increment user's monthly trip usage in database."""
    try:
        db_manager.increment_usage(user_id, current_month)
    except Exception as e:
        print(f"Error incrementing usage: {e}")

class ExtractRequest(BaseModel):
    text: str

class ItineraryRequest(BaseModel):
    # New generic destination fields (preferred)
    destination: Optional[str] = None
    destination_type: Optional[str] = None  # e.g., "city" | "country"
    # Backward compatibility
    city: Optional[str] = None
    interests: Optional[str] = None
    days: Optional[int] = None
    trip_request: Optional[str] = None
    user_id: Optional[str] = "default"
    subscription_plan: Optional[str] = None

class Place(BaseModel):
    name: str
    neighborhood: Optional[str] = None
    category: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None

class ModifyRequest(BaseModel):
    # New generic destination fields (preferred)
    destination: Optional[str] = None
    destination_type: Optional[str] = None  # e.g., "city" | "country"
    # Backward compatibility
    city: Optional[str] = None
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

class SubscriptionCheckRequest(BaseModel):
    user_id: Optional[str] = "default"
    subscription_plan: Optional[str] = None

class UsageRequest(BaseModel):
    user_id: Optional[str] = "default"
    subscription_plan: Optional[str] = None
    days: Optional[int] = None

class UserRequest(BaseModel):
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    google_id: Optional[str] = None

class PaymentVerificationRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    user_id: Optional[str] = "default"

@app.get("/")
def home() -> Dict[str, Any]:
    return {"status": "ok", "message": "TripXplorer API (LangGraph) is running"}

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
        # --- TEMP MOCK: Return static Paris data for testing ---
        text = (req.trip_request or "").lower()
        dest_raw = (req.destination or req.city or "").lower()
        if "paris" in text or "paris" in dest_raw:
            destination = req.destination or req.city or "Paris"
            destination_type = req.destination_type or "city"
            interests = req.interests or "art, food"
            days = req.days or 2
            mock_places = [
                {"name": "Eiffel Tower", "category": "landmark", "latitude": 48.8584, "longitude": 2.2945},
                {"name": "Louvre Museum", "category": "museum", "latitude": 48.8606, "longitude": 2.3376},
                {"name": "Notre-Dame Cathedral", "category": "landmark", "latitude": 48.8530, "longitude": 2.3499},
                {"name": "Montmartre", "category": "neighborhood", "latitude": 48.8867, "longitude": 2.3431},
                {"name": "Musée d'Orsay", "category": "museum", "latitude": 48.8600, "longitude": 2.3266},
            ]
        return {
            "destination": destination,
            "destination_type": destination_type,
            "city": destination,
            "interests": interests,
            "days": days,
            "places": mock_places,
            "subscription_info": {
                "plan": req.subscription_plan or get_user_subscription_plan(req.user_id or "default"),
                "usage": {"trips_used": 0, "max_trips": SUBSCRIPTION_LIMITS.get("premium", {}).get("max_trips_per_month", -1)},
                "features": SUBSCRIPTION_LIMITS.get("premium", {}).get("features", [])
            }
        }
        #--- END TEMP MOCK ---
        # Get user subscription plan
        user_id = req.user_id or "default"
        subscription_plan = req.subscription_plan or get_user_subscription_plan(user_id)

        if req.trip_request and not ((req.destination or req.city) and req.interests and req.days):
            # Extract details first if needed
            extracted = trip_workflow.extract_trip_request(req.trip_request)
            destination = extracted.get("destination") or extracted.get("city")
            destination_type = extracted.get("destination_type") or "city"
            interests = extracted["interests"]
            days = extracted["days"]
        else:
            destination = req.destination or req.city or "Bangalore"
            destination_type = req.destination_type or "city"
            interests = req.interests or "art, food"
            days = req.days or 1

        # Check days limit
        days_check = check_days_limit(subscription_plan, days)

        if not days_check["allowed"]:
            return {
                "error": True,
                "type": "subscription_limit",
                "message": days_check["message"],
                "details": days_check,
                "destination": destination,
                "destination_type": destination_type,
                "city": destination,  # deprecated mirror
                "interests": interests,
                "days": days,
                "places": []
            }

        # Check monthly usage limit
        current_month = datetime.now().strftime("%Y-%m")
        usage_check = check_usage_limit(user_id, subscription_plan, current_month)
        if not usage_check["allowed"]:
            return {
                "error": True,
                "type": "subscription_limit",
                "message": usage_check["message"],
                "details": usage_check,
                "destination": destination,
                "destination_type": destination_type,
                "city": destination,  # deprecated mirror
                "interests": interests,
                "days": days,
                "places": []
            }

        # Generate itinerary
        # For now, workflow still expects a city parameter; pass destination string
        result = trip_workflow.generate_itinerary(city=destination, interests=interests, days=days)

        print(result)
        # Increment usage counter
        increment_usage(user_id, current_month)
        
        # Get updated usage after increment
        updated_usage_data = db_manager.get_usage(user_id, current_month)
        updated_trips_used = updated_usage_data.get('trips_used', 0)
        
        # Record trip in database for analytics
        places_count = len(result.get("places", []))
        # Record using destination string in the legacy city field for now
        db_manager.record_trip(user_id, destination, interests, days, places_count)
        
        # Add subscription info to result with updated usage
        limits = SUBSCRIPTION_LIMITS[subscription_plan]
        result["subscription_info"] = {
            "plan": subscription_plan,
            "usage": {
                "trips_used": updated_trips_used,
                "max_trips": limits["max_trips_per_month"]
            },
            "features": limits["features"]
        }

        # Include destination fields in response for clients
        result["destination"] = destination
        result["destination_type"] = destination_type
        # Deprecated mirror for backward compatibility
        result["city"] = destination
        
        return result

    except Exception as e:
        print(f"Itinerary error: {e}")
        return {
            "destination": destination if 'destination' in locals() else "Bangalore",
            "destination_type": destination_type if 'destination_type' in locals() else "city",
            "city": (destination if 'destination' in locals() else "Bangalore"),
            "interests": interests if 'interests' in locals() else "art, food",
            "days": days if 'days' in locals() else 1,
            "places": [],
            "raw_research_text": None,
            "error": True,
            "message": "Error generating itinerary"
        }

@app.post("/modify")
def modify(req: ModifyRequest) -> Dict[str, Any]:
    """Handle modifications using LangGraph agents"""
    try:
        print(f"\n=== /modify endpoint called (LangGraph) ===")
        print(f"Instruction: '{req.instruction}'")
        dest = req.destination or req.city
        dest_type = req.destination_type or "city"
        print(f"Destination: {dest} ({dest_type}), Days: {req.days}")

        places_dicts = [p.model_dump() for p in req.places]
        print(f"Number of existing places: {len(places_dicts)}")

        result = trip_workflow.handle_modification(
            city=dest,
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
            "destination": dest,
            "destination_type": dest_type,
            "city": dest,  # deprecated mirror
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
def verify_payment(req: PaymentVerificationRequest) -> Dict[str, Any]:
    """Verify Razorpay payment signature and upgrade subscription"""
    try:
        # Verify payment with Razorpay
        result = payment_service.verify_payment(
            razorpay_order_id=req.razorpay_order_id,
            razorpay_payment_id=req.razorpay_payment_id,
            razorpay_signature=req.razorpay_signature
        )
        
        if result.get("success") and result.get("verified"):
            # Payment verified, upgrade user to premium
            upgrade_success = db_manager.update_subscription(
                user_id=req.user_id,
                plan="premium",
                payment_id=req.razorpay_payment_id,
                amount_paid=1.00,
                currency="INR"
            )
            
            if upgrade_success:
                result["message"] = "Payment successful! Welcome to Premium! You now have unlimited trip plans and up to 30-day itineraries."
                result["subscription_upgraded"] = True
            else:
                result["message"] = "Payment verified but subscription upgrade failed. Please contact support."
                result["subscription_upgraded"] = False
        
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

@app.post("/subscription/check")
def check_subscription(req: SubscriptionCheckRequest) -> Dict[str, Any]:
    """Check user's subscription status and limits"""
    try:
        user_id = req.user_id or "default"
        subscription_plan = req.subscription_plan or get_user_subscription_plan(user_id)
        current_month = datetime.now().strftime("%Y-%m")
        
        usage_check = check_usage_limit(user_id, subscription_plan, current_month)
        limits = SUBSCRIPTION_LIMITS.get(subscription_plan, SUBSCRIPTION_LIMITS["freemium"])
        
        return {
            "success": True,
            "subscription_plan": subscription_plan,
            "limits": limits,
            "usage": usage_check.get("usage", {}),
            "can_create_trip": usage_check["allowed"]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/subscription/usage")
def check_usage(req: UsageRequest) -> Dict[str, Any]:
    """Check if user can create a trip with given parameters"""
    try:
        user_id = req.user_id or "default"
        subscription_plan = req.subscription_plan or get_user_subscription_plan(user_id)
        current_month = datetime.now().strftime("%Y-%m")
        
        # Check trip count limit
        usage_check = check_usage_limit(user_id, subscription_plan, current_month)
        if not usage_check["allowed"]:
            return {
                "success": True,
                "allowed": False,
                "reason": "trip_limit_exceeded",
                "message": usage_check["message"],
                "details": usage_check
            }
        
        # Check days limit if provided
        if req.days:
            days_check = check_days_limit(subscription_plan, req.days)
            if not days_check["allowed"]:
                return {
                    "success": True,
                    "allowed": False,
                    "reason": "days_limit_exceeded",
                    "message": days_check["message"],
                    "details": days_check
                }
        
        return {
            "success": True,
            "allowed": True,
            "subscription_plan": subscription_plan,
            "usage": usage_check.get("usage", {}),
            "limits": SUBSCRIPTION_LIMITS.get(subscription_plan, SUBSCRIPTION_LIMITS["freemium"])
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/subscription/upgrade")
def upgrade_subscription(req: SubscriptionCheckRequest) -> Dict[str, Any]:
    """Upgrade user subscription"""
    try:
        user_id = req.user_id or "default"
        subscription_plan = req.subscription_plan or "premium"
        
        # Update subscription in database
        success = db_manager.update_subscription(
            user_id=user_id,
            plan=subscription_plan,
            payment_id=f"upgrade_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            amount_paid=1.00,
            currency="INR"
        )
        
        if success:
            return {
                "success": True,
                "message": f"Successfully upgraded to {subscription_plan} plan!",
                "subscription_plan": subscription_plan
            }
        else:
            return {
                "success": False,
                "error": "Failed to upgrade subscription. Please try again."
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/subscription/update")
def update_subscription(req: SubscriptionCheckRequest) -> Dict[str, Any]:
    """Update user subscription plan (upgrade or downgrade)"""
    try:
        user_id = req.user_id or "default"
        subscription_plan = req.subscription_plan
        
        if not subscription_plan:
            return {
                "success": False,
                "error": "Subscription plan is required"
            }
        
        if subscription_plan not in ["freemium", "premium"]:
            return {
                "success": False,
                "error": "Invalid subscription plan. Must be 'freemium' or 'premium'"
            }
        
        # Get current plan
        current_plan = get_user_subscription_plan(user_id)
        
        # Update subscription in database
        payment_id = None
        amount_paid = None
        if subscription_plan == "premium" and current_plan != "premium":
            payment_id = f"upgrade_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            amount_paid = 1.00
        elif subscription_plan == "freemium" and current_plan == "premium":
            payment_id = f"downgrade_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            amount_paid = 0.00
        
        success = db_manager.update_subscription(
            user_id=user_id,
            plan=subscription_plan,
            payment_id=payment_id,
            amount_paid=amount_paid,
            currency="INR"
        )
        
        if success:
            return {
                "success": True,
                "message": f"Successfully updated to {subscription_plan} plan!",
                "subscription_plan": subscription_plan
            }
        else:
            return {
                "success": False,
                "error": "Failed to update subscription. Please try again."
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/user/create")
def create_user(req: UserRequest) -> Dict[str, Any]:
    """Create a new user"""
    try:
        success = db_manager.create_user(
            user_id=req.user_id,
            email=req.email,
            name=req.name,
            google_id=req.google_id
        )
        
        if success:
            return {
                "success": True,
                "message": "User created successfully",
                "user_id": req.user_id
            }
        else:
            return {
                "success": False,
                "error": "Failed to create user"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/user/{user_id}")
def get_user(user_id: str) -> Dict[str, Any]:
    """Get user information and subscription details"""
    try:
        user_data = db_manager.get_user(user_id)
        
        if user_data:
            # Get user statistics
            stats = db_manager.get_user_stats(user_id)
            
            return {
                "success": True,
                "user": user_data,
                "stats": stats
            }
        else:
            return {
                "success": False,
                "error": "User not found"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/user/{user_id}/stats")
def get_user_stats(user_id: str) -> Dict[str, Any]:
    """Get user statistics"""
    try:
        stats = db_manager.get_user_stats(user_id)
        return {
            "success": True,
            "stats": stats
        }
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