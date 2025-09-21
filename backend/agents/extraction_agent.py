"""
Agent for extracting trip details from user requests
"""

from agents.base_agent import BaseAgent
from agents.models import TripExtractionResponse, AgentState

class ExtractionAgent(BaseAgent):
    """Agent responsible for extracting trip details from user text"""

    def extract_trip_details(self, trip_request_text: str) -> dict:
        """Extract city, interests, and days from trip request"""

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

            if all(k in result for k in ["city", "interests", "days"]):
                return result

        except Exception as e:
            print(f"Extraction error: {e}")

        # Fallback
        return {"city": "Bangalore", "interests": "art, food", "days": 1}

    def run(self, state: AgentState) -> AgentState:
        """Run the extraction agent"""
        result = self.extract_trip_details(state.query)

        state.city = result.get("city")
        state.interests = result.get("interests")
        state.days = result.get("days")

        return state