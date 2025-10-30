"""
Agent for extracting trip details from user requests
"""

from agents.base_agent import BaseAgent
from agents.models import TripExtractionResponse, AgentState

class ExtractionAgent(BaseAgent):
    """Agent responsible for extracting trip details from user text"""

    def extract_trip_details(self, trip_request_text: str) -> dict:
        """Extract destination (city or country), interests, and days from trip request"""

        if not trip_request_text or not trip_request_text.strip():
            return {"city": "Bangalore", "interests": "art, food", "days": 1}

        prompt = f"""Extract travel details from this request: "{trip_request_text}"

        Return ONLY a JSON object with these exact keys (prefer destination fields):
        {{
        "destination": "Destination Name",  
        "destination_type": "city" | "country",
        "city": "City Name (deprecated, mirror of destination when type=city)",
        "interests": "comma, separated, interests",
        "days": number
        }}

        Rules:
        - If the user mentions a country (e.g., Vietnam), set destination_type="country" and destination to the country name.
        - If the user mentions a city (e.g., Paris), set destination_type="city" and destination to the city name, and also set city to the same value for compatibility.
        - If ambiguous, assume city.
        - If any information is missing, use reasonable defaults."""

        # Create structured chain
        chain = self.create_structured_chain(
            "Extract travel information from the request.",
            TripExtractionResponse
        )

        try:
            result = self.execute_with_fallback(
                chain,
                prompt,
                TripExtractionResponse,
                "Extract travel information. Return only valid JSON."
            )

            # Ensure destination fields exist for compatibility
            if all(k in result for k in ["interests", "days"]) and (result.get("destination") or result.get("city")):
                if not result.get("destination"):
                    result["destination"] = result.get("city")
                if not result.get("destination_type"):
                    result["destination_type"] = "city"
                # Keep legacy mirror
                if not result.get("city") and result.get("destination"):
                    result["city"] = result["destination"]
                return result

        except Exception as e:
            print(f"Extraction error: {e}")

        # Fallback
        return {"destination": "Bangalore", "destination_type": "city", "city": "Bangalore", "interests": "art, food", "days": 1}

    def run(self, state: AgentState) -> AgentState:
        """Run the extraction agent"""
        result = self.extract_trip_details(state.query)

        # Populate new destination fields and keep legacy city
        state.destination = result.get("destination") or result.get("city")
        state.destination_type = result.get("destination_type") or "city"
        state.city = state.destination
        state.interests = result.get("interests")
        state.days = result.get("days")

        return state